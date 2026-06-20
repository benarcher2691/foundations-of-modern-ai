# Appendix B — Build a Minimal Coding Agent (in Python, with an open model)

> *Foundations of Modern AI* — Appendix B
> Builds on: [Chapter 9 — The Harness](09-the-harness.md) (this is that chapter, made runnable)
> Scope: a complete, working terminal coding agent in ~150 lines of Python — an LLM, a loop, and four tools — running against an **open** model (GLM via Z.ai, or MiniMax) through an OpenAI-compatible endpoint.
> Inspired by Thorsten Ball's ["How to Build an Agent"](https://ampcode.com/notes/how-to-build-an-agent). The runnable code lives in [`agent/agent.py`](agent/agent.py).

---

## 0. What we're building, and why it's small

Chapter 9 argued that a harness is just *call the model → run the tools it asks for → feed results back → repeat*. This appendix proves it by building one you can actually run. The whole agent is **about 150 lines**: a system prompt, four tools, and the loop.

The thesis, borrowed from the article that inspired this: a coding agent is **"an LLM, a loop, and enough tokens."** There is no hidden cleverness — the model is doing the reasoning (Chapters 3–5, 8); our code just gives it hands (Chapter 9). With four tools — read a file, list files, edit a file, run a shell command — a capable model can explore a project, write code, run it, and fix its own mistakes.

Two deliberate choices for this build:

- **Python**, because it's the lingua franca of the field (Chapter 2's training data is full of it).
- An **open model** — GLM-5.2 (Z.ai) or MiniMax-M2.7 — instead of a closed API, because you asked for one, and because it shows the harness is genuinely model-agnostic.

---

## 1. The trick that makes it provider-agnostic

Chapter 9 said the *only* provider-specific part of a harness is the wire format, hidden behind one `complete()` function. Here we get that almost for free, because both open providers expose an **OpenAI-compatible** API. So we use the standard `openai` Python client and just *repoint* it:

| Provider | `base_url` | `model` |
|----------|------------|---------|
| **GLM (Z.ai)** — our default | `https://api.z.ai/api/openai/v1` | `glm-5.2` |
| **MiniMax** | `https://api.minimax.io/v1` | `MiniMax-M2.7` |
| Local (Ollama, etc.) | `http://localhost:11434/v1` | e.g. `qwen2.5-coder` |

```python
from openai import OpenAI
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)   # swap BASE_URL/MODEL to switch
```

That's the entire "agnostic" story: one client speaking the OpenAI Chat Completions dialect, three lines of config to change models. (Endpoints and model names drift — confirm the current ones in your provider's dashboard.)

### Setup

```bash
pip install openai
export AI_API_KEY=...        # a key from Z.ai or MiniMax
```

---

## 2. A tool is a function plus a schema

Recall Chapter 9: the model never runs anything — it *requests* a tool by emitting a structured call, and our code executes it. So every tool is two things: a **Python function** that does the work, and a **schema** that tells the model the tool exists and what arguments it takes.

Here are the four functions — short and unremarkable, which is the point:

```python
def read_file(path):                      # read a file
    return Path(path).read_text()

def list_files(path="."):                 # list a directory (dirs get a trailing /)
    items = [p.name + ("/" if p.is_dir() else "") for p in sorted(Path(path).iterdir())]
    return json.dumps(items)

def edit_file(path, old_str, new_str):    # replace text; empty old_str → create file
    p = Path(path)
    if old_str == "":
        p.write_text(new_str); return f"wrote {path}"
    text = p.read_text()
    if old_str not in text: return "ERROR: old_str not found in file"
    p.write_text(text.replace(old_str, new_str, 1)); return "OK"

def bash(cmd):                            # run a shell command
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return (r.stdout + r.stderr).strip() or "(no output)"
```

The `edit_file` design is worth noting: instead of "rewrite the whole file," the model supplies an **exact `old_str` to find and a `new_str` to replace it with** — a surgical edit. (Empty `old_str` means "create the file.") This is easier for the model to get right and safer than regenerating whole files.

Each function is paired with an **OpenAI tool schema** — `name`, `description`, and a JSON-Schema for the arguments:

```python
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read the contents of a file at a relative path.",
    "parameters": {
      "type": "object",
      "properties": {"path": {"type": "string"}},
      "required": ["path"],
    },
  },
}
```

The **description** is the model's only guide to *when* to use a tool — so it earns its keep. We keep a registry mapping each name to `(function, schema)`, and send the list of schemas on every request.

---

## 3. The loop

Everything comes together in two nested loops — the heart of the agent:

```python
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:                                   # OUTER: one user message per turn
    user = input("you> ")
    messages.append({"role": "user", "content": user})

    while True:                               # INNER: think + use tools until it replies
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOL_SCHEMAS,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))   # keep the full history

        if not msg.tool_calls:                # no tool calls → the model answered
            print("ai>", msg.content)
            break

        for tc in msg.tool_calls:             # run each requested tool, feed results back
            args = json.loads(tc.function.arguments or "{}")
            result = run_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,         # link the result to the request
                "content": result,
            })
        # loop again — the model now sees the results and decides the next step
```

Trace one turn against Chapter 9's protocol:

```
  you> create fizzbuzz.py and run it
        │
        ▼  model emits a tool call (it did NOT write anything yet):
   tool_call → edit_file(path="fizzbuzz.py", old_str="", new_str="for i in range(1,21): ...")
        │   we run it; append a role:"tool" result ("wrote fizzbuzz.py")
        ▼  model emits another:
   tool_call → bash(cmd="python fizzbuzz.py")
        │   we run it; append the program's output
        ▼  no more tool calls:
   ai> Done — created fizzbuzz.py and it prints 1, 2, Fizz, 4, Buzz, …
```

Two details that make it correct:

- **The conversation is the memory.** The model is stateless (Chapter 6), so we append *every* message — user, assistant, and each `tool` result — and resend the whole list each call. The growing `messages` list *is* the agent's working memory.
- **Tool results link back by id.** Each `tool_call` has an `id`; the result we send back carries the matching `tool_call_id`. That's how the model knows which request this answers (the OpenAI dialect of Chapter 9's `tool_use`/`tool_result` pairing).

The inner loop exits exactly when the model **replies with text and no tool calls** — its way of saying "I'm done; here's the answer."

---

## 4. The whole program

Putting it together — system prompt, tools, registry, loop — this is the complete agent (also in [`agent/agent.py`](agent/agent.py), with a couple of niceties like coloured output):

```python
import json, os, subprocess, sys
from pathlib import Path
from openai import OpenAI

BASE_URL = os.environ.get("AI_BASE_URL", "https://api.z.ai/api/openai/v1")
MODEL    = os.environ.get("AI_MODEL", "glm-5.2")
client   = OpenAI(base_url=BASE_URL, api_key=os.environ["AI_API_KEY"])

SYSTEM_PROMPT = ("You are a coding assistant working in a terminal, in the user's "
    "current directory. Use the tools to read, list, and edit files and run shell "
    "commands. Read a file before editing it. Keep replies short.")

def read_file(path): return Path(path).read_text()
def list_files(path="."):
    return json.dumps([p.name + ("/" if p.is_dir() else "")
                       for p in sorted(Path(path).iterdir())])
def edit_file(path, old_str, new_str):
    p = Path(path)
    if old_str == "": p.write_text(new_str); return f"wrote {path}"
    t = p.read_text()
    if old_str not in t: return "ERROR: old_str not found in file"
    p.write_text(t.replace(old_str, new_str, 1)); return "OK"
def bash(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return (r.stdout + r.stderr).strip() or "(no output)"

def tool(name, desc, props, required):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required}}}

TOOLS = {
    "read_file":  (read_file,  tool("read_file",  "Read a file at a relative path.",
                   {"path": {"type": "string"}}, ["path"])),
    "list_files": (list_files, tool("list_files", "List files/dirs under a path.",
                   {"path": {"type": "string"}}, [])),
    "edit_file":  (edit_file,  tool("edit_file",  "Replace old_str with new_str; "
                   "empty old_str creates the file.",
                   {"path": {"type": "string"}, "old_str": {"type": "string"},
                    "new_str": {"type": "string"}}, ["path", "old_str", "new_str"])),
    "bash":       (bash,       tool("bash", "Run a shell command, return its output.",
                   {"cmd": {"type": "string"}}, ["cmd"])),
}
SCHEMAS = [s for _f, s in TOOLS.values()]

def run_tool(name, args):
    try:    return str(TOOLS[name][0](**args))
    except Exception as e: return f"ERROR: {e}"

messages = [{"role": "system", "content": SYSTEM_PROMPT}]
while True:
    try: user = input("you> ").strip()
    except (EOFError, KeyboardInterrupt): break
    if not user: continue
    messages.append({"role": "user", "content": user})
    while True:
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=SCHEMAS).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            print("ai>", msg.content); break
        for tc in msg.tool_calls:
            result = run_tool(tc.function.name, json.loads(tc.function.arguments or "{}"))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
```

That's a coding agent. Everything from Chapter 9 is here: the **system prompt** (§5 there), **tool definitions** (§2), the **agentic loop** (§3), and the **append-only history** (§6) — concrete and runnable.

---

## 5. Running it

```bash
cd /a/throwaway/directory          # see the safety note below
export AI_API_KEY=...
python agent.py
```

A first session might look like:

```
you> write hello.py that prints hello, then run it
  [tool] edit_file({'path': 'hello.py', 'old_str': '', 'new_str': "print('hello')"}) -> wrote hello.py
  [tool] bash({'cmd': 'python hello.py'}) -> hello
ai> Done — hello.py prints "hello".

you> add a bug to it, then find and fix the bug
  [tool] edit_file(...) -> OK
  [tool] read_file({'path': 'hello.py'}) -> print('helo')
  [tool] edit_file({'path': 'hello.py', 'old_str': 'helo', 'new_str': 'hello'}) -> OK
ai> Fixed a typo (helo → hello); it prints "hello" again.
```

Notice nobody told the model *how* to do any of this — which tool, in what order. It read the file because it decided it needed to, then edited, then verified. The loop just keeps offering it tools until it stops asking. That autonomy is the model's (Chapters 5, 8); the harness only supplies the hands.

---

## 6. What this leaves out (on purpose)

This is a teaching skeleton, not Claude Code. To go from here to a real harness, add the things Chapters 6–9 described:

- **Safety / approval.** ⚠ The `bash` tool runs **any command the model chooses**, with your privileges. Run the agent in a scratch directory, and in anything real, **gate destructive tools behind a yes/no prompt** (Chapter 9, §8; the risk from Chapter 7).
- **Streaming.** Print tokens as they arrive instead of waiting for the full reply.
- **Context management.** The `messages` list grows forever; eventually it exceeds the **context window** (Chapter 6). Real harnesses **compact** old turns or prune stale tool output.
- **Prompt caching.** We resend the whole history every step — fine for a demo, expensive for long sessions. Chapter 9 (§6) is the fix: keep a stable prefix and let the provider cache it.
- **Robustness.** Retries, malformed-arguments handling, file-size limits, parallel read-only tools.

None of these change the core. They wrap more judgment around the same **call → act → feed back** loop.

---

## 7. Recap

- A working coding agent is **~150 lines**: a system prompt, four tools, and a loop — "an LLM, a loop, and enough tokens."
- Because open providers (GLM via Z.ai, MiniMax) speak the **OpenAI-compatible** format, the harness is genuinely model-agnostic: change `base_url` + `model` to switch, nothing else.
- A **tool is a function + a schema**; `read_file`, `list_files`, `edit_file` (surgical find/replace), and `bash` are enough to do real work.
- The **loop** appends every message (the stateless model's memory), runs each requested tool, links results back by id, and stops when the model replies with text.
- The model supplies the **autonomy**; the harness supplies the **hands**. Production extras (approval, streaming, compaction, caching) wrap the same loop.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`. Runnable code: [`agent/agent.py`](agent/agent.py).*
