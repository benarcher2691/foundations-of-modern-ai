# Reasoning Models — Teaching a Model to Think Before It Answers

> *Foundations of Modern AI* — Chapter 8 (extension)
> Builds on: [Chapter 4 — Pretraining](04-pretraining-mechanics.md) (scaling), [Chapter 5 — Alignment](05-alignment.md) (reinforcement learning), and [Chapter 6 — Inference](06-inference-and-applications.md) (chain-of-thought prompting)
> Scope: the 2024–2025 shift to models that generate a long internal reasoning process before answering — what they are, how they're trained, and the new "think longer" scaling axis. No prior math assumed.

---

## 0. Where this fits

Chapters 1–7 covered the core lifecycle. This chapter is an **extension** about one of the most important recent developments: **reasoning models** (the "o-series," "extended thinking," "R1," and similar).

Start from a limitation. A standard model (Chapter 3) emits its answer **immediately** — the first answer token is produced right after your prompt, with no scratch space. For lookup or fluency that's fine. For a hard math problem or a subtle bug, it's like demanding a person blurt the answer with no chance to work it out. Reasoning models remove that constraint: they **think first, then answer.**

> The cognitive analogy people reach for: fast, intuitive "System 1" (blurting) vs. slow, deliberate "System 2" (working it out). A reasoning model is a language model trained to *use* System 2 when the problem warrants it.

---

## 1. The core idea: a chain of thought, trained in

Chapter 6 introduced **chain-of-thought** prompting: telling a model to "think step by step" makes it generate intermediate reasoning, which improves hard problems because the model builds on its own partial work instead of leaping to a conclusion.

Reasoning models take that from a *prompting trick* to a *trained-in habit* — and push it much further:

```
   Standard model:
     prompt ─────────────────────────────► answer        (think? none)

   Reasoning model:
     prompt ─► [ long internal reasoning: try, check, backtrack, retry ] ─► answer
               └──────────── hundreds to thousands of "thinking" tokens ──┘
```

The model produces an extended stream of **reasoning tokens** — exploring approaches, doing sub-calculations, catching its own mistakes — *before* committing to a final answer. Crucially this isn't hand-scripted; the model learned the *behaviour* of reasoning. Which raises the real question: how do you train that?

---

## 2. How they're trained: reinforcement learning on checkable answers

Recall two kinds of training so far: **next-token imitation** (Chapter 4) and **RLHF**, where the reward came from *human preference* (Chapter 5). Reasoning models add a third, with a different reward source:

> **Reinforcement learning from verifiable rewards (RLVR):** train on problems whose answers can be **automatically checked** — math (is the final number right?), code (do the unit tests pass?), logic puzzles. The reward is simply *correct or not*.

The loop:

```
   1. give the model a problem with a known-checkable answer
   2. let it generate a long reasoning attempt + a final answer
   3. CHECK the final answer automatically (no human needed)
   4. reinforce the reasoning paths that led to correct answers; discourage the rest
   5. repeat over millions of problems
```

The difference from RLHF matters. RLHF optimizes "what humans *prefer*" — subjective, and vulnerable to sycophancy (Chapter 5). RLVR optimizes "what is *correct*" — objective and hard to fake, because a wrong proof doesn't suddenly pass the checker. This grounding is *why* reasoning training produces such large gains on math and coding.

### The striking part: reasoning behaviours *emerge*

Nobody tells the model *how* to reason. Yet, optimized only on "get the right answer," models spontaneously develop recognizable strategies:

- **breaking problems into steps**, and exploring more than one approach;
- **self-correction** — noticing an error mid-stream ("wait, that's wrong — let me redo it");
- **verification** — checking their own answer before committing.

These are emergent (echoing Chapter 4's emergence): they appear because they *help solve the problem*, not because they were programmed. A model rewarded purely for correctness discovers, on its own, that double-checking pays off.

---

## 3. A new scaling axis: thinking longer at inference

Chapter 4's scaling laws were about **training**: more data, parameters, and compute *during training* → a better model. Reasoning models opened a second, complementary axis:

> **Test-time (inference-time) compute:** for a *fixed* trained model, letting it generate **more reasoning tokens** at answer-time produces **better answers** on hard problems.

```
   accuracy
     │                        ___────  more thinking →
     │                ___────'           higher accuracy
     │           __──'                   (on hard problems)
     │       _──'
     └────────────────────────────────► thinking tokens spent per question
        (train-time scaling sets the curve; test-time scaling moves along it)
```

This is a genuine shift in how capability is bought. You can now trade **compute per query** for **quality per query**, decided at request time — no retraining. In practice this surfaces as a **thinking budget** or **effort** setting: spend more tokens (and time, and money) on a hard question; spend almost none on an easy one.

---

## 4. What it looks like in use

- **Thinking, then answering.** The model first emits its reasoning, then a clean final answer. The reasoning is sometimes hidden, sometimes shown verbatim, sometimes shown as a summary — a product/safety choice that varies by system.
- **Budgets / effort levels.** You (or the app) can dial how much the model thinks. Higher effort → better on hard tasks, but slower and costlier (more tokens, Chapter 2).
- **It's still one model.** A reasoning model is a normal Transformer (Chapter 3) doing next-token prediction (Chapter 4) — the *training* taught it to spend many of those tokens on reasoning before the answer. No new architecture is required.

---

## 5. When reasoning helps — and when it doesn't

More thinking is not always better. The skill is matching effort to the task:

| Reasoning models shine | Reasoning is wasteful / counterproductive |
|------------------------|-------------------------------------------|
| Multi-step math and science | Simple factual lookup ("capital of France") |
| Complex coding, debugging, refactoring | Short creative or conversational replies |
| Logical puzzles, planning, proofs | Latency-sensitive, high-volume simple calls |
| Tasks where a wrong step compounds | Tasks where the answer is immediate anyway |

For easy questions, a reasoning model can **overthink** — burning tokens and time, occasionally even talking itself *out* of a correct first instinct. The practical guidance mirrors Chapter 6's "lightest layer that works": reach for reasoning (or a higher thinking budget) when a task is genuinely hard, not by default.

---

## 6. Limits and caveats

Reasoning is a major advance, not a cure — and it raises its own issues, several tying straight back to Chapter 7:

- **Still fallible.** A long, confident chain of reasoning can still reach a wrong answer. More steps mean more *chances* to be right, not a guarantee.
- **Faithfulness.** The reasoning the model *shows* may not be the true cause of its answer — it can reach a conclusion one way and narrate a tidier story. This makes visible reasoning an unreliable audit trail, an active **safety/evaluation** concern (Chapter 7).
- **Cost and latency.** Thinking tokens are real tokens: reasoning answers are slower and more expensive. Test-time scaling buys quality *with* compute.
- **Reward hacking, again.** Even with verifiable rewards, models can find shortcuts that satisfy the *checker* without genuinely solving the problem (Goodhart's Law, Chapter 7) — so the checkers and training tasks must be designed carefully.

---

## 7. Reasoning + tools = stronger agents

The natural pairing is with the **agents** of Chapter 6. An agent's loop is *think → act → observe*; a reasoning model makes the **think** step far more capable. Interleave the two and you get a system that can reason about *what* to do, call a tool, reason about the result, and continue — the basis of the strongest current agentic systems (deep research, autonomous coding). Reasoning supplies the deliberation; tools supply the facts and actions.

---

## 8. Recap

- **Reasoning models** are trained to generate a long internal **chain of thought** before answering — turning Chapter 6's prompting trick into a trained-in habit.
- They're trained largely by **reinforcement learning on verifiable rewards (RLVR)** — problems with automatically checkable answers (math, code) — which is more objective than RLHF's human preference and grounds the gains.
- Useful reasoning **behaviours emerge** from optimizing only for correctness: decomposition, self-correction, verification.
- They add a new **test-time compute** scaling axis: think longer → better answers, tunable per query via a thinking budget — complementing Chapter 4's train-time scaling.
- They **shine on hard multi-step problems** and can **overthink** easy ones; match effort to difficulty.
- Caveats: still fallible, possibly **unfaithful** reasoning, higher cost/latency, and Goodhart-style reward hacking (Chapter 7). Paired with **tools**, reasoning powers today's strongest **agents**.

---

## What's next

- **Chapter 9 — [The Harness](09-the-harness.md):** how an agent is actually wired together — the loop, how a model "uses" tools, the system prompt, and cache management.
- **Appendix — [Landmark Papers](appendix-landmark-papers.md):** the foundational works the whole series rests on.
- *Planned — Multimodality:* how the same Transformer ideas extend to images, audio, and video (parked for now; this series leans text and code).

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
