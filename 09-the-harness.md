# The Harness — How an Agent Is Actually Wired Together

> *Foundations of Modern AI* — Chapter 9 (extension)
> Builds on: [Chapter 6 — Inference & Applications](06-inference-and-applications.md) (tools & agents) and [Chapter 8 — Reasoning Models](08-reasoning-models.md)
> Scope: what a *harness* is, why an agent needs one, and how to build a simple one yourself — the agentic loop, how a language model "uses" tools, the system prompt, and why cache management matters. No prior math assumed.
> Inspired by Mario Zechner's ["Building pi, a minimal coding agent"](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/) — a great companion read.

---

## 0. What a harness is, and why you need one

By Chapter 6 we had the pieces of an agent — a model, some tools, a loop. This chapter zooms all the way in on the **program that holds those pieces together**: the *harness*.

Start from the constraint we keep returning to (Chapter 6): **the model is a stateless function.** Tokens in → tokens out. It has no memory, can't run code, can't read a file, can't loop. On its own it can only *say* things.

A **harness** is the ordinary program wrapped around that function to turn "says things" into "does things." It:

- holds the **system prompt** (who the assistant is, what tools exist),
- runs the **loop** (call model → act → feed results back → repeat),
- **executes the tools** the model asks for,
- manages the **context** (the growing transcript) and its **cost** (caching).

Tools like Claude Code, Cursor, and Zechner's minimal "pi" are all harnesses. The model is the engine; the harness is the rest of the car. And the encouraging news: **a basic harness is small** — a loop, a few tool functions, and a short prompt. By the end of this chapter you could write one.

> A theme worth borrowing from pi: a good harness is *legible*. Heavier agents "inject stuff behind your back that isn't surfaced in the UI." The whole value of understanding the harness is that nothing about an agent has to be magic — it's a loop you can read.

---

## 1. The mental unlock: how a model "uses" a tool

This is the part that confuses almost everyone, so let's kill the confusion directly.

> **A language model never runs a tool. It only ever emits text.**

It cannot open a file or execute a command — it's a next-token predictor (Chapter 3). So how does an AI "search the web" or "edit your code"? Through a **protocol**, in four beats:

```
  1. DECLARE   The harness tells the model (up front): "You have a tool called
               `read`. It takes {path}. Here's what it does."
  2. REQUEST   When the model wants the file, it doesn't read it — it emits a
               structured message: call `read` with {path: "main.py"} … then STOPS.
  3. EXECUTE   The HARNESS (plain code) sees that request, runs the real
               read_file("main.py"), and gets the contents.
  4. RETURN    The harness pastes the contents back into the conversation as a
               new message, and asks the model to continue.
```

The model "used a tool" the way you "use a calculator" by *writing down* `47 × 92 =` and handing the paper to someone else to compute. The model produces a **request**; your code does the work; the **answer comes back as more conversation.** That's the entire mechanism.

A concrete exchange (simplified):

```
  user      → "How many lines are in main.py?"

  assistant → [tool call] read(path="main.py")          ← model emits this and pauses
                                                            (it did NOT read anything)

  harness   → runs read_file("main.py") → "import sys\n..."
              appends a tool-result message with that text

  assistant → "main.py has 42 lines."                   ← model continues, now that
                                                            the result is in its context
```

Two things make this work, both supplied by the harness:

- The model was **told the tool exists** (step 1) — so emitting a call is a learned, in-distribution behavior (alignment + post-training taught it the format, Chapter 5).
- The model's request is **structured**, not freeform prose — so the harness can reliably parse it. That structure is the tool *definition*, next.

---

## 2. Tool definitions: name, description, schema

A tool, from the model's point of view, is just three things the harness declares:

| Field | Purpose |
|-------|---------|
| **name** | What to call it — e.g. `read`, `bash`. |
| **description** | *When and why* to use it, in plain language. The model picks tools based on this — write it well. |
| **input schema** | The arguments and their types, as **JSON Schema**, so the harness can validate the model's request. |

A minimal definition (the shape is near-identical across providers):

```json
{
  "name": "read",
  "description": "Read a file from disk. Use when you need to see file contents before editing.",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "Path to the file" }
    },
    "required": ["path"]
  }
}
```

A capable coding agent needs surprisingly few tools. Pi ships **four**:

| Tool | Does |
|------|------|
| `read` | Read a file (with offset/limit for big ones) |
| `write` | Create or overwrite a file |
| `edit` | Replace an exact string in a file (surgical edits) |
| `bash` | Run a shell command |

With just those, a model can explore a repo, run tests, and make changes — because `bash` alone is enormously general. (Why have dedicated `read`/`edit` at all, when `bash` could `cat` and `sed`? Because dedicated tools give the *harness* a typed hook it can validate, gate behind approval, or render nicely — a point we return to in §8.)

---

## 3. The agentic loop

Now the heart of the harness. Everything above plugs into one loop:

```
  messages = [ first user message ]

  loop forever:
      reply = call_model(system_prompt, tools, messages)   # the LLM call
      append reply to messages                             # keep the transcript

      if reply has no tool calls:
          return reply                                     # model is done → answer the user

      for each tool_call in reply:
          result = run_tool(tool_call.name, tool_call.args) # the harness does the work
          append a tool-result message (linked to tool_call) to messages

      # loop again — model now sees the results and decides the next step
```

That's it. The whole "agent" is: **call the model; if it asked for tools, run them and feed the results back; otherwise you're done.** Each turn the model sees the entire growing transcript and decides the next action — read another file, run the tests, or stop and reply.

```
        ┌───────────────────────────────────────────────┐
        │                                                │
        ▼                                                │
   call model ──► tool calls? ──no──► reply to user (done)
        ▲              │ yes
        │              ▼
        │        run each tool
        │              │
        └──── append results ◄┘
```

The loop's exit condition is simply **"the model replied with text and no tool calls"** — it decided it's finished. (Anthropic's API signals this with `stop_reason: "end_turn"` vs. `"tool_use"`; other providers have an equivalent flag.)

Pair this with Chapter 8 and you see why reasoning models make better agents: a stronger *"decide the next step"* makes a smarter loop.

---

## 4. Keeping it LLM-agnostic

Here's the reassuring part: **the loop above is identical for every model provider.** The only thing that differs is the *wire format* of one message — how a tool call and its result are represented. Two concrete dialects:

| Concept | Anthropic (Claude) | OpenAI (GPT) |
|---------|--------------------|--------------|
| Model requests a tool | a `tool_use` content block: `{id, name, input}` | a `tool_calls` entry: `{id, function:{name, arguments}}` |
| Harness returns a result | a `tool_result` block keyed by `tool_use_id` | a message with `role: "tool"` keyed by `tool_call_id` |
| "I'm done" signal | `stop_reason: "end_turn"` | `finish_reason: "stop"` |

Same idea — *request, then result-linked-by-id* — different field names. So you isolate the difference behind **one function**:

```
  complete(system, tools, messages) -> { text, tool_calls, done }
      # internally: translate to this provider's format, call its API,
      # translate the response back into a normalized shape
```

Write a `complete()` for Anthropic, another for OpenAI (or a local model via Ollama, etc.), and **your loop, tools, and prompt never change.** This is exactly how real harnesses stay multi-provider — pi supports Anthropic, OpenAI, Google, and any OpenAI-compatible endpoint behind one such seam. *Agnostic by abstraction:* the loop is universal; only the adapter is provider-specific.

---

## 5. The system prompt

The **system prompt** is the standing instruction block placed at the very front of the context every turn (Chapter 6). In a harness it carries:

- **identity & intent** — "You are an expert coding assistant operating in a terminal";
- **tool guidance** — when to prefer `edit` over `write`, to read before editing, to run tests after changes;
- **conventions** — output format, how to ask for clarification, safety rules.

The instinct is to write a giant prompt. Resist it. Pi's entire system prompt is **under 1,000 tokens** — it names the assistant, lists the four tools with a line of guidance each, and stops, where some other harnesses run to many thousands of tokens. Two reasons less is more:

1. **Every token is sent every turn** (the model is stateless), so a bloated prompt is a tax on the whole session.
2. Modern models already *know how to code and use tools* (Chapters 4–5). The prompt's job is to set role and conventions, not to re-teach the model its job. Over-instruction also backfires — aggressive "you MUST" language makes capable models overtrigger.

> Rule of thumb: the system prompt should say what's *specific to your harness* (its tools, its conventions, its guardrails) — not everything you wish were true about good engineering.

---

## 6. Cache management — the part beginners skip and regret

Here is the most important *efficiency* idea in the whole chapter, and it falls straight out of statelessness.

The model has no memory, so **every turn you resend the entire transcript** — system prompt + tool definitions + the full back-and-forth so far. As an agent works, that transcript grows: turn 1 might be 2,000 tokens; turn 20, after reading files and running commands, might be 50,000. And you re-send all of it *every step*.

Naively, the model re-processes that whole growing prefix each turn. Over a session that's roughly **quadratic** cost — the early context gets re-read again and again. For a long agent run, this is the difference between cheap and unaffordable.

**Prompt caching** fixes it. The provider can cache the result of processing a prefix of the input; on the next request, the unchanged prefix is served from cache instead of recomputed. The economics (Anthropic's numbers, others are similar):

- a **cache read** costs about **0.1×** the normal input price — a 90% discount on the repeated part;
- a **cache write** costs about **1.25×** (for the default 5-minute lifetime; ~2× for a 1-hour lifetime) — a small premium paid once.

So a long agent session goes from re-paying full price for the whole history every turn to paying ~10% for everything it has already seen. That's the lever that makes agents economical.

### The one rule that makes caching work

> **Caching is a prefix match. Any change to the cached prefix invalidates it from the change-point onward.**

The provider caches *up to a point* in your input, keyed on the exact bytes. Change anything before that point and the cache is void from there. Two consequences drive how you structure a harness:

1. **Keep the front of the context frozen.** The render order is **tools → system prompt → conversation**. Tool definitions and the system prompt should be byte-for-byte identical every turn — so *don't* interpolate a timestamp, a random ID, or "current file: X" into the system prompt. That single changing byte busts the cache for the entire session.
2. **Only ever append.** Add new turns to the *end* of the transcript; never edit or reorder earlier messages. An append-only conversation means the long stable prefix keeps hitting the cache, and only the new tail is processed fresh.

Concretely, you mark a **cache breakpoint** at the end of the stable prefix (in the Anthropic API, `cache_control: {type: "ephemeral"}`; default 5-minute lifetime, or `"1h"`), and another at the end of the latest turn so the conversation prefix is reused too. Then verify it's working: the response reports how many tokens were served from cache (`cache_read_input_tokens`) — if that's stuck at zero across turns, something in your prefix is changing every request, and you have a silent cache-buster to hunt down.

```
   ┌──────────── frozen, cached prefix (cheap to re-send) ─────────────┐  ┌ new ┐
   [ tool defs ] [ system prompt ] [ turn1 ][ result1 ][ turn2 ]...      [ turnN ]
                                 ▲                          ▲
                          breakpoint                  breakpoint
                       (tools+system cached)     (conversation cached)
```

Get this right and a 50-turn coding session stays cheap. Get it wrong — a clock in the system prompt — and you pay full freight every single turn without realizing it.

---

## 7. A complete minimal harness

Putting every piece together, here is a whole agent in pseudocode — short enough to read in one sitting:

```python
SYSTEM = "You are a coding assistant in a terminal. Read before you edit. " \
         "Run tests after changes. Use the tools; keep replies short."

TOOLS = [ read_def, write_def, edit_def, bash_def ]   # name + description + schema each

def run_tool(name, args):
    if name == "read":  return open(args["path"]).read()
    if name == "write": open(args["path"], "w").write(args["content"]); return "ok"
    if name == "edit":  return apply_edit(args["path"], args["old"], args["new"])
    if name == "bash":  return shell(args["cmd"], timeout=args.get("timeout", 60))

def agent(user_message):
    messages = [ user(user_message) ]
    while True:
        reply = complete(SYSTEM, TOOLS, messages)   # provider adapter + caching live here
        messages.append(reply)
        if reply.done:                               # no tool calls → finished
            return reply.text
        for call in reply.tool_calls:
            result = run_tool(call.name, call.args)
            messages.append(tool_result(call.id, result))   # link by id, append only
```

Everything in this chapter is in those ~15 lines: the **loop** (§3), **tool execution** (§1–2), the **system prompt** (§5), the provider-agnostic **`complete()`** seam (§4), and the **append-only** discipline that keeps caching healthy (§6). A real harness adds polish, but this *is* an agent.

---

## 8. What real harnesses add

The skeleton works; production harnesses layer on safety and ergonomics, each tying back to earlier ideas:

- **Permissions / approval.** Before a destructive `bash` or `write`, pause and ask the user. Dedicated tools (vs. raw `bash`) exist partly so the harness can *gate* specific actions — this is the safety boundary from Chapter 7 made concrete, and why agent autonomy raises risk.
- **Streaming.** Show tokens as they generate, and parse tool calls progressively, so the UI feels live.
- **Parallel & safe tool use.** Run independent read-only tools (search, list) concurrently; serialize anything that mutates state.
- **Context management.** When the transcript nears the context window (Chapter 6), **compact** it — summarize old turns — or prune stale tool output, so long sessions don't overflow.
- **Sub-agents.** Spawn a fresh harness with its own context for a sub-task. Powerful, but (per pi's caution) it's "a black box within a black box" — you lose visibility, so use it deliberately.

None of these change the core: they wrap more judgment around the same **call → act → feed back** loop.

---

## 9. Recap

- A **harness** is the ordinary program that turns a stateless model into an agent: it holds the system prompt and tools, runs the loop, executes tool calls, and manages context and cost.
- **A model never runs a tool — it only emits text.** "Tool use" is a protocol: the harness *declares* tools, the model *requests* one (structured text) and pauses, the harness *executes* the real code, and the result is *returned* as more conversation.
- A **tool** is a name + description + JSON-schema; a handful (read/write/edit/bash) goes a long way because `bash` is so general.
- The **agentic loop** is tiny: call model → if it asked for tools, run them and append results → else reply. It's **LLM-agnostic** — only a thin `complete()` adapter differs per provider (Anthropic `tool_use`/`tool_result` vs OpenAI `tool_calls`/`role:tool`).
- Keep the **system prompt minimal** — every token is re-sent each turn, and modern models already know how to work.
- **Cache management** is the key to affordable agents: the transcript grows and is re-sent every turn, so cache the **frozen prefix** (tools → system → history), keep it byte-stable, and **only append**. Cache reads cost ~0.1×; a changing byte in the prefix silently busts everything.

---

## What's next

- **Appendix — [Landmark Papers](appendix-landmark-papers.md):** the foundational works behind everything in this series.
- *Planned — Multimodality:* extending these ideas to images, audio, and video (still parked; the series leans text and code).

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
