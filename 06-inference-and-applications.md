# Inference & Applications — Putting the Model to Work

> *Foundations of Modern AI* — Chapter 6
> Builds on: [Chapter 5 — Alignment](05-alignment.md) (we now have a trained, aligned assistant)
> Scope: how a finished model is actually *used* — the generation loop, sampling, the context window, prompting, retrieval (RAG), tools, and agents. The layer where most application developers work.

---

## 0. From "a trained model" to "a useful product"

Chapters 2–5 built a model. This chapter is about everything that happens *afterward*, every time you press enter. Two reframes set the scene:

- **Inference** is the act of running the finished model to generate output. Unlike training, the parameters no longer change — they're frozen. Inference is what you pay for per use, and it's *cheap per query* compared to the one-time training cost (Chapter 4).
- **The model is a component, not the product** (the closing idea of Chapter 1). What users experience is the model *plus* a system around it: prompting, memory, retrieval, tools, guardrails. This chapter builds that system up, layer by layer, motivated each time by something the bare model *can't* do.

---

## 1. The generation loop

Recall the Transformer's one trick (Chapter 3): given the tokens so far, output a probability for every possible next token. Generation just runs that trick in a loop:

```
   prompt: "The capital of France is"
        │
        ▼
   ┌─────────────────────────────────────────────┐
   │ 1. run the model over all tokens so far       │
   │ 2. get probabilities for the next token       │
   │ 3. pick one token  →  " Paris"                 │
   │ 4. append it to the sequence                   │
   │ 5. go back to step 1                           │
   └─────────────────────────────────────────────┘
        │  (stop at an end-of-text token or a length limit)
        ▼
   "The capital of France is Paris."
```

This is **autoregressive** generation: each token is produced using all the tokens before it, then fed back in. Two practical notes you'll hear:

- **Prefill vs. decode.** Processing your whole prompt at once (fast, parallel) is *prefill*; generating new tokens one-at-a-time (sequential, slower) is *decode*. This is why a long answer streams out gradually while the prompt is digested almost instantly.
- **The KV cache.** To avoid re-computing attention over the whole history at every step, the model caches its intermediate results for past tokens. This cache is the main consumer of memory during inference and a major target of optimization.

---

## 2. Sampling: how the next token is *chosen*

Step 3 above — "pick one token" — hides a real choice. The model gives a *probability distribution*; how we draw from it shapes the output's character.

| Strategy | How it picks | Feels like |
|----------|--------------|------------|
| **Greedy** | Always take the single highest-probability token | Deterministic, safe, can be repetitive/flat |
| **Sampling** | Draw randomly, weighted by the probabilities | Varied, creative, occasionally off |

Two dials control sampling:

- **Temperature** (the setting promised back in Chapter 3). Low temperature sharpens the distribution toward the top choices (focused, predictable); high temperature flattens it (diverse, riskier). ~0 ≈ greedy; ~0.7 is a common balance; high values get wild.
- **Top-p / top-k** ("nucleus" sampling). Only consider the most probable tokens — the top *k* of them, or the smallest set whose probabilities sum to *p* — then sample within that. This trims the long tail of bizarre options while keeping useful variety.

```
   next-token probabilities:  mat ████████ floor ███ sofa █ rug ▌ ... (tail)
   low temperature  →  almost always "mat"
   high temperature →  "mat" usually, but "floor"/"sofa" get real chances
   top-p            →  discard the tail entirely, sample among {mat, floor, sofa}
```

> Why deliberately add randomness? Because pure greedy decoding tends to produce dull, looping text, and because variety is often *wanted* (brainstorming, writing). The same model can be tuned factual-and-steady or loose-and-creative purely by these settings — no retraining.

---

## 3. The context window: the model's entire world

Here is the single most important concept for *using* models. **A model has no memory between calls.** It is a pure function: tokens in → next token out. Everything it "knows" about your conversation must be present in its input *right now*.

That input is the **context window** — a fixed maximum number of tokens (Chapter 2) the model can attend to at once, today ranging from thousands to millions.

```
   ┌──────────────────── CONTEXT WINDOW (e.g. 200,000 tokens) ───────────────────┐
   │ [system prompt]  the hidden instructions: "You are a helpful assistant…"      │
   │ [user]    earlier message                                                     │
   │ [assistant] earlier reply        ← the whole conversation history is re-sent   │
   │ [user]    your latest message                                                 │
   │ [retrieved documents, if any]                                                 │
   └──────────────────────────────────────────────────────────────────────────────┘
                         everything the model can "see" this turn
```

Consequences worth internalizing:

- **A chatbot feels like it remembers only because the app re-sends the history every turn.** The model itself is stateless. Run out of window and the oldest turns must be dropped or summarized — the model genuinely "forgets" them.
- **The system prompt** is just text placed at the front of the window — the chat-role markers from Chapter 2 telling the model who it is and the rules. It's powerful precisely because it sits in every turn's context.
- **Cost and latency scale with context** (Chapter 2: everything is tokens). A huge window is useful but not free.

This statelessness is exactly what motivates the next three layers — they're all techniques for *getting the right tokens into the window.*

---

## 4. Prompting: programming in plain language

Since the context window is all the model sees, **how you fill it is the primary control surface.** This is *prompting*, and a few reliable ideas:

- **Instructions.** Clear, specific asks beat vague ones. Stating the role, format, and constraints up front steers the output a lot.
- **Few-shot examples.** Putting a handful of input→output examples *in the prompt* teaches the model the pattern on the spot. This is **in-context learning** — a remarkable property that emerged from pretraining: the model adapts to a task from examples *without any parameter change*, purely by pattern-matching within the window.
- **Reasoning prompts.** Asking the model to "think step by step" (chain-of-thought) often improves hard reasoning, because it generates intermediate tokens to build on rather than leaping to an answer. Newer "reasoning models" bake this habit in.

> Prompting is best understood as *soft programming*: you're not changing the model, you're arranging its context so the next-token machine is overwhelmingly likely to produce what you want. It's the cheapest, fastest lever — try it before anything heavier.

---

## 5. What prompting alone can't fix

Even a perfectly prompted model has hard limits, all stemming from *what's in the window* and *how it was trained*:

| Limitation | Why it happens |
|------------|----------------|
| **Knowledge cutoff** | It only knows what was in its training data, frozen at a past date. It can't know today's news. |
| **No private/live data** | Your company's docs, a user's account, a live price — none of it was in training. |
| **Hallucination** | It generates *plausible* tokens, not *verified* ones. Asked something it doesn't know, it may fabricate confidently. |
| **Can't act** | It outputs text. By itself it can't run code, search, send email, or change anything in the world. |

The last three layers of the chapter each remove one of these walls.

---

## 6. Retrieval-Augmented Generation (RAG): giving it the right facts

**RAG fixes the knowledge limits** by fetching relevant text at query time and placing it in the context window *before* the model answers. The model then answers *from the provided documents* rather than from memory.

The key enabling idea is **embeddings** (Chapter 3: meaning as direction in space). Documents are pre-converted to vectors and stored; at query time your question is embedded too, and a **vector search** finds the documents whose meaning is nearest.

```
   knowledge base ──► chunk & embed ──► [vector database]
                                              ▲  nearest-meaning search
   user question ──► embed ──────────────────┘
        │
        ▼
   retrieved chunks + question  ──►  stuffed into the context window  ──►  model answers,
                                                                          grounded & citable
```

Why it matters: RAG lets a frozen model use **current** and **private** data, **grounds** answers in real sources (reducing hallucination), and supports **citations** — without any retraining. It's the workhorse pattern behind most "chat with your documents / company knowledge" products.

---

## 7. Tools (function calling): giving it hands

**Tools fix the "can't act" limit.** The model is told, in its context, about a set of functions it may call — a calculator, a web search, a database query, code execution, any API. When useful, instead of answering in prose it emits a **structured call** (which function, which arguments). The surrounding system runs it and feeds the result back into the context.

```
   user: "What's 4,317 × 89, and is it bigger than last quarter's revenue?"
        │
        ▼
   model emits →  calculator(4317 * 89)         ┐  the *system* executes these,
   model emits →  db.query("Q3 revenue")         ┘  not the model
        │  results returned into context: 384213, and 350000
        ▼
   model: "It's 384,213 — yes, about 10% above last quarter's 350,000."
```

This turns a text generator into something that can *compute exactly* (covering for the arithmetic weakness from Chapter 2), *look things up live*, and *interact with real systems* — while the model's job stays the same: predict the next token, where the next token might be "call this tool."

---

## 8. Agents: giving it autonomy

An **agent** chains tools and reasoning into a *loop* aimed at a goal, deciding its own next step each time rather than answering in one shot:

```
   GOAL: "Find the cheapest flight next Friday and draft an email about it."
   ┌──► THINK   what should I do next?
   │    ACT     call a tool (search flights / read calendar / draft text)
   │    OBSERVE read the tool's result
   └────┘  repeat until the goal is met, then respond
```

This **think → act → observe** loop lets a model tackle multi-step tasks: research, writing and running code, operating software, orchestrating many tools. Each pass, the growing transcript (plan, actions, results) lives in the context window, so the agent "remembers" within the task.

> Agents are where capability and **risk** rise together. A system that can take real actions can take *wrong* ones — bad tool calls, runaway loops, acting on a hallucination or a malicious instruction hidden in retrieved data ("prompt injection"). This is precisely why guardrails and **evaluation/safety** (Chapter 7) become non-negotiable once a model can *do* things, not just *say* things.

---

## 9. How the layers stack

Each layer adds a capability the one below lacks — and you adopt only as much as the task needs:

```
   Base capability    a trained, aligned model                 (Chapters 2–5)
        +  Prompting   shape the context in plain language       → steer behaviour
        +  RAG         inject current / private facts            → ground & cite
        +  Tools       let it compute and act                    → exact & connected
        +  Agents      loop tools toward a goal                  → autonomous multi-step
        ─────────────────────────────────────────────────────────────────────────
        =  the AI product the user actually touches
```

**Reach for the lightest layer that works.** Most needs are met by good prompting; add RAG when facts must be current or private; add tools when the model must compute or act; add agency only when a task genuinely needs multiple self-directed steps.

---

## 10. Recap

- **Inference** runs the frozen model in an **autoregressive loop**: predict → pick → append → repeat. *Prefill* digests the prompt; *decode* streams the answer; the *KV cache* makes it efficient.
- **Sampling** chooses each token: **temperature** and **top-p/top-k** trade focus against variety — tunable without retraining.
- The **context window** is the model's whole world; it is **stateless**, so the app re-sends history, system prompt, and any retrieved text every turn. Cost scales with tokens.
- **Prompting** is soft programming — instructions, **few-shot in-context learning**, step-by-step reasoning — the cheapest lever.
- Bare models hit walls (knowledge cutoff, no private/live data, hallucination, can't act). **RAG** injects the right facts via embeddings + vector search; **tools** let it compute and act via structured calls; **agents** loop tools toward a goal.
- The product is the model **plus** these layers. Use the lightest one that works — and note that as autonomy rises, so does risk.

---

## Next up

**Chapter 7 — Evaluation & Safety:** if a model (and the agents built on it) can now *do* things, how do we know it's any good — and that it's safe? Benchmarks, human/LLM judging, red-teaming, and what "good" even means.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
