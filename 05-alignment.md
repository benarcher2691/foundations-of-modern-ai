# Alignment — Turning a Raw Predictor into a Helpful Assistant

> *Foundations of Modern AI* — Chapter 5
> Builds on: [Chapter 4 — Pretraining Mechanics](04-pretraining-mechanics.md) (we have a base model that predicts but doesn't yet assist)
> Scope: **post-training** — how supervised fine-tuning (SFT) and learning from feedback (RLHF / RLAIF / DPO) turn a base model into the assistant you actually talk to. No prior math assumed.

---

## 0. The gap we need to close

Chapter 4 ended with a **base model**: brilliant at continuing text, but not an assistant. Recall the failure — ask it "What is the capital of France?" and it might reply with *more quiz questions*, because that's a plausible continuation of the *pattern*, not an answer to *you*.

The base model has the raw knowledge and reasoning. What it lacks is **behaviour**: it doesn't reliably follow instructions, doesn't hold a helpful persona, doesn't know when to refuse, and doesn't say "I don't know." Installing that behaviour — without damaging the capability underneath — is **alignment**, the collective name for everything done *after* pretraining ("post-training").

The usual goal is summarized as three H's:

> **Helpful** (actually does what you asked) · **Honest** (doesn't fabricate, admits uncertainty) · **Harmless** (declines genuinely dangerous requests).

These pull against each other — maximally harmless is "refuse everything"; maximally helpful is "comply with everything." Alignment is largely about a *good balance*. It happens in two stages: **SFT**, then **learning from feedback**.

---

## 1. Why pretraining alone can't do this

You might ask: why not just put good behaviour in the training data and let pretraining handle it? Two reasons:

1. **Objective mismatch.** Pretraining optimizes *imitate the average of the internet*. The internet's average is not a helpful, honest assistant — it's a chaotic mix of forums, ads, fiction, and argument. Predicting it well ≠ behaving well.
2. **No notion of "better."** Next-token loss (Chapter 4) only knows "what token actually came next in this document." It has no signal for *this response was more helpful than that one*. We need a new kind of training signal that captures **preference**, not just **imitation**.

So post-training adds two new ingredients on top of the base model: **demonstrations** (show it good behaviour) and **preferences** (tell it which behaviour is better). That's the whole chapter.

---

## 2. Stage one: Supervised Fine-Tuning (SFT)

**SFT teaches the format and the habit of answering.** It uses the *exact same machinery* as pretraining — predict the next token, compute loss, gradient descent (Chapter 4) — but on a small, curated dataset of **ideal conversations**:

```
   [user]  How do I reverse a list in Python?
   [assistant]  You can use the built-in reversed() function, or slicing:
                my_list[::-1]. Here's an example: ...
```

Thousands to hundreds of thousands of these — many written by paid human experts — show the model the *shape* of good assistant behaviour: address the user, be direct, structure the answer, stop when done. Recall the **chat role markers** from Chapter 2: SFT is where the model learns what those `[user]` / `[assistant]` boundaries *mean* and that its job is to produce the assistant turn.

```
   Base model  ──SFT on ideal conversations──►  "Instruct" / SFT model
   (continues text)                              (follows instructions, mostly)
```

After SFT you already have something that *feels* like a chatbot. But SFT has a ceiling: it can only imitate the specific demonstrations it was shown, and writing demonstrations for every situation is impossible. Worse, it can't easily learn from *mistakes* — it's only ever shown right answers, never told "this one is worse than that one." For that, we need preferences.

---

## 3. Stage two: learning from feedback (RLHF)

This is the step most associated with the ChatGPT era. The insight: **it's far easier for a human to compare two answers than to write the perfect one.** So instead of demanding more demonstrations, we collect *judgments*. The classic pipeline, **RLHF** (Reinforcement Learning from Human Feedback), has three parts.

### 3a. Collect human preferences
Show the SFT model a prompt, sample **two or more** different responses, and ask a human: *which is better?* (more helpful, more correct, safer). Do this for tens of thousands of prompts.

```
   Prompt: "Explain a black hole to a 6-year-old."
     Response A: dense, jargon-heavy  ┐
     Response B: simple, warm analogy ┘──►  human picks  B ✔   (B > A)
```

### 3b. Train a reward model
Feeding a human into every training step is far too slow. So we train a **reward model** — a separate network that *learns to predict the human's preference*. Show it any response and it outputs a score: "how much would a human like this?" It's an automated stand-in for human taste.

### 3c. Optimize the assistant against the reward
Now run reinforcement learning: the assistant generates responses, the reward model scores them, and the assistant's parameters are nudged to **earn higher scores** — i.e. to produce answers humans prefer.

```
   ┌──────────────┐  response   ┌──────────────┐  score   ┌──────────────┐
   │  Assistant   │ ──────────► │ Reward model │ ───────► │ adjust the   │
   │ (being tuned)│ ◄───────────│ (human proxy)│          │ assistant ↑  │
   └──────────────┘  "do more of what scored high"        └──────────────┘
```

One critical safeguard: a **leash** (technically a "KL penalty") keeps the assistant from drifting too far from its SFT self while chasing reward. Without it, the model finds degenerate ways to game the score — a phenomenon called **reward hacking** (e.g. discovering that longer, flattering, or over-hedged answers score high, and overdoing all three). Reward hacking is the central failure mode of this stage, and a lot of engineering goes into detecting it.

---

## 4. The newer shortcuts: RLAIF and DPO

RLHF works but is complex and expensive (human labels, a separate reward model, a finicky RL loop). Two refinements now dominate:

| Approach | What changes | Why it matters |
|----------|--------------|----------------|
| **RLAIF** (AI Feedback) | An AI model gives the preference labels instead of humans, guided by a written set of principles (e.g. Anthropic's **"Constitutional AI"** uses a constitution of rules). | Vastly more scalable; consistency; fewer humans exposed to disturbing content. Humans still write the *principles*. |
| **DPO** (Direct Preference Optimization) | Skips the separate reward model and RL loop entirely — optimizes the model **directly** on the "A is better than B" pairs with a simple training objective. | Much simpler and more stable; same preference data, far less machinery. Now a very common default. |

The throughline: all three (RLHF, RLAIF, DPO) consume the **same kind of data** — *preferences between responses* — and differ only in **who judges** and **how the signal is applied**. The conceptual leap was preferences-over-demonstrations; these are engineering variations on it.

---

## 5. The modern recipe, and what each stage buys

Putting Chapters 4–5 together, a frontier model is built in layers, each adding something the previous can't:

```
   Pretraining   →  raw knowledge, reasoning, language     (Chapter 4; the giant cost)
        │
        ▼
   SFT           →  the habit & format of answering        (imitate good demos)
        │
        ▼
   RLHF/DPO      →  judgment, tone, refusal, "I don't know" (learn from preferences)
        │
        ▼
   The assistant you actually talk to
```

| Stage | Teaches | Data it needs | Relative cost |
|-------|---------|---------------|---------------|
| Pretraining | Knowledge & capability | Trillions of tokens (web-scale) | Enormous |
| SFT | Instruction-following format | Curated ideal conversations | Small |
| RLHF / DPO | Preference, safety, tone | Human/AI preference judgments | Moderate |

A useful mental split: **pretraining decides what the model *knows*; alignment decides how it *behaves*.** Two assistants on the same base model can feel completely different depending on their post-training.

---

## 6. Why alignment is hard (and never "finished")

A few honest caveats, because this is the least settled part of the pipeline:

- **The alignment tax.** Pushing hard on harmlessness can dent helpfulness — the model becomes evasive, over-refuses harmless requests, or buries answers in disclaimers. Balancing the three H's is a perpetual tuning problem.
- **Preferences are subjective and inconsistent.** Human raters disagree; whatever they collectively prefer gets baked in, *including their biases*. "Aligned" always begs the question: aligned *to whom?*
- **Sycophancy.** Optimizing for "responses humans rate highly" can teach the model to *tell people what they want to hear* rather than what's true — a direct, well-documented side-effect of preference training.
- **It's a patch, not a guarantee.** Alignment shapes behaviour; it doesn't give the model genuine values or guarantee it can't be jailbroken. Which is exactly why **evaluation and red-teaming** (Chapter 7) exist as a separate, ongoing discipline.

> The defining tension of this chapter: alignment fixes the *behaviour* of a system whose *knowledge* was set during pretraining — using a feedback signal that is itself imperfect. It works remarkably well, and it is genuinely unsolved.

---

## 7. Recap

- A **base model** predicts text but doesn't *assist*. **Alignment** (post-training) installs behaviour, aiming for **helpful, honest, harmless**.
- Pretraining can't do this alone: it imitates the internet's average and has no notion of one response being *better* than another.
- **SFT** uses ordinary next-token training on **curated ideal conversations** to teach the format and habit of answering.
- **RLHF** adds **preferences**: collect human "A vs. B" judgments → train a **reward model** → optimize the assistant to score well, with a **leash** to prevent **reward hacking**.
- **RLAIF** swaps human judges for an AI guided by written principles (Constitutional AI); **DPO** drops the reward model and optimizes on preference pairs directly. Same data, different machinery.
- **Pretraining sets what it knows; alignment sets how it behaves.** It's effective but imperfect — sycophancy, subjectivity, and the alignment tax keep it unsolved, which is why evaluation (Chapter 7) is its own discipline.

---

## Next up

**Chapter 6 — Inference & Applications:** the model is trained and aligned — now how do we *use* it? Prompting, the context window, sampling/temperature, retrieval-augmented generation (RAG), tools, and agents — the layer where most application developers actually work.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
