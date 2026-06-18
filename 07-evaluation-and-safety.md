# Evaluation & Safety — Knowing if It's Any Good, and Whether It's Safe

> *Foundations of Modern AI* — Chapter 7
> Builds on: [Chapter 6 — Inference & Applications](06-inference-and-applications.md) (the model — and agents built on it — can now *do* things)
> Scope: how we measure capability and safety — benchmarks, human/LLM judging, red-teaming — and why "good" is a moving target. The discipline that runs *throughout* the lifecycle, not just at the end.

---

## 0. Why this is its own chapter

We've built a capable, aligned model (Chapters 2–5) and wrapped it in a system that can retrieve, compute, and act (Chapter 6). Two questions remain, and they're the whole job of this chapter:

> **Is it actually good?** And **is it safe?**

These resist a clean answer in a way that ordinary software does not. A traditional program either passes its tests or fails them. A language model produces **open-ended** output with no single correct answer, draws on effectively unbounded knowledge, and is used in ways its builders never anticipated. You cannot test it exhaustively. So evaluation becomes its own engineering discipline — and, as we'll see, a permanently unfinished one.

This is **step 6** of the Chapter 1 loop, but it bookends everything: you evaluate a base model, evaluate after alignment, evaluate before release, and **keep** evaluating in production (step 8).

---

## 1. Capability evaluation: benchmarks

The first instinct is to give the model a standardized exam. A **benchmark** is a fixed set of questions with known answers, so scoring can be automatic and models compared on a common yardstick. Familiar examples by flavour:

| Benchmark (example) | Tests | Format |
|---------------------|-------|--------|
| **MMLU** | Broad knowledge across 57 subjects | Multiple choice |
| **GSM8K** | Grade-school math word problems | Numeric answer |
| **HumanEval** | Code generation | Run the code against unit tests |
| **GPQA** | Hard graduate-level science | Multiple choice, "Google-proof" |

Benchmarks are indispensable: cheap, repeatable, objective, and they let the whole field track progress. But they have deep limitations.

### The three ways benchmarks lie

1. **Contamination (leakage).** If the test questions appeared in the training data, a high score measures *memorization*, not skill. This is exactly why the **decontamination** step from Chapter 2 exists — and why scores from a lab that skips it should be distrusted.
2. **Saturation.** Once models score ~95%+, the benchmark stops discriminating; everyone "passes," and it tells you nothing about the frontier. The field constantly has to invent *harder* tests (MMLU → GPQA → beyond).
3. **Gaming / narrowness.** A benchmark measures one narrow proxy. Optimizing to *the test* (tuning, prompt tricks, even training on similar data) can lift the number without lifting real capability — an instance of the law in Section 4.

> A benchmark score is **evidence, not proof.** A model that aces MMLU may still be useless at *your* task, because your task isn't on the test.

---

## 2. Capability evaluation: human and model judgment

Because benchmarks can't capture open-ended quality — "which assistant is more *helpful*?" — the field leans on judgment.

- **Human preference / arenas.** Show people two anonymous responses to the same prompt and ask which is better; aggregate millions of these into an **Elo-style ranking** (as in public "chatbot arenas"). This captures real-world helpfulness that multiple-choice can't, and it's the same *preference* signal that powers RLHF (Chapter 5) — here used to *judge* rather than to *train*.
- **LLM-as-judge.** Human rating is slow and costly, so a strong model is often used to *grade* another model's answers against a rubric. Fast and scalable — but circular and bias-prone (judges can favour their own style, longer answers, or confident tone), so it must be validated against humans.

The honest summary: **no single method suffices.** Serious evaluation triangulates — benchmarks for objective skills, human preference for quality, LLM-judges for scale — and treats any one number with suspicion.

---

## 3. Safety evaluation: red-teaming

Capability asks "can it do good things?" Safety asks "can it be made to do bad things — and what happens when it fails?" The central technique is **red-teaming**: deliberately adversarial testing, by humans and automated systems, trying to make the model misbehave.

What red-teamers probe for:

- **Jailbreaks** — prompts crafted to bypass the model's safety training (Chapter 5), coaxing out content it's meant to refuse.
- **Prompt injection** — malicious instructions hidden in *data the model reads* (a web page, a document, a tool result). This is the sharp risk for the **agents** of Chapter 6: an agent that browses or reads files can be hijacked by text it ingests, then act on the attacker's behalf.
- **Harmful content, bias, and toxicity** — does it produce dangerous instructions, or systematically skewed/unfair outputs (reflecting biases from its training data, Chapter 2)?
- **Dangerous capabilities** — for frontier models, structured evaluations of whether the model could meaningfully uplift a bad actor (e.g. cyber, bio). These "frontier safety" evals increasingly gate whether and how a model is released.

```
   Red team ──► crafts adversarial inputs ──► model ──► did it break?
        ▲                                                   │
        └──────────── findings patch guardrails ◄───────────┘
        (and feed the next alignment round — Chapter 5)
```

Red-teaming is never "done." It's an arms race: every new defense invites a new attack, so it runs continuously, before and after release.

---

## 4. The core difficulty: Goodhart's Law

One idea explains why both capability and safety evaluation stay hard:

> **"When a measure becomes a target, it ceases to be a good measure."** — Goodhart's Law

Every metric here is a *proxy* for something we actually care about (true capability, genuine safety). The moment we optimize hard against the proxy — train to the benchmark, maximize the reward model (Chapter 5's *reward hacking*), please the human raters (*sycophancy*) — the proxy and the real goal drift apart. The number goes up; the thing you wanted may not.

This is why:
- benchmarks must keep changing,
- evaluations are kept **private/held-out** so they can't be trained against,
- and "how good is this model, really?" never reduces to a single dashboard figure.

Evaluation is fundamentally an attempt to measure something open-ended with closed-ended tools, against a system that — directly or indirectly — gets optimized toward whatever you measure.

---

## 5. Honesty, calibration, and the hallucination problem

A capability *and* safety concern in one: does the model say true things, and does it know what it doesn't know?

- **Hallucination** (Chapter 6) is evaluated with factuality benchmarks and grounded-answer checks — but it can't be fully eliminated, because the model generates *plausible* tokens, not *verified* ones.
- **Calibration** asks whether the model's confidence matches its accuracy: a well-calibrated model is unsure exactly when it should be. Alignment (Chapter 5) can accidentally *hurt* calibration — a model trained to sound helpful and confident may state guesses as facts.
- The practical mitigations live in Chapter 6: **RAG** to ground answers in sources, **tools** to compute/verify, and prompting the model to **express uncertainty** rather than bluff.

---

## 6. Evaluation never stops: monitoring in production

Pre-release testing can't anticipate real users. So **step 8** of the lifecycle (Chapter 1) is continuous evaluation in the wild:

- **Monitoring** — track failures, drift, latency, cost, and abuse on live traffic.
- **Feedback** — collect user signals (thumbs, reports, corrections).
- **Incident response** — patch guardrails quickly when something slips through.
- **Closing the loop** — feed everything learned back into the **next** data and alignment cycle (Chapters 2 & 5). The findings become training signal.

This is what makes the lifecycle a *loop*, not a line: evaluation in production is the bridge from one model generation to the next.

---

## 7. So what does "good" mean?

There is no universal answer — and that's the real lesson. "Good" is **relative to a purpose**:

- a coding assistant is judged on correct, runnable code;
- a medical tool on safety, calibration, and citable sources;
- a creative writing aid on fluency and variety;
- a high-autonomy agent on whether it completes tasks *without* harmful actions.

A responsible evaluation picks the dimensions that matter for *its* use case, measures each with the best available (imperfect) tool, weighs **capability against safety** for that context, and stays humble about what the numbers don't capture.

> The throughline of the whole series: a modern AI system is a chain of imperfect-but-powerful steps — curated data, self-supervised pretraining, human-guided alignment, a system of tools around the model — and evaluation is the discipline that keeps the chain honest. It is never finished, and that is the point.

---

## 8. Recap

- Models produce **open-ended** output, so they can't be tested like ordinary software; evaluation is its own discipline that runs **throughout** the lifecycle.
- **Benchmarks** (MMLU, GSM8K, HumanEval…) are cheap and comparable but lie via **contamination**, **saturation**, and **gaming** — evidence, not proof.
- **Human preference** (Elo arenas) and **LLM-as-judge** capture open-ended quality; serious evaluation **triangulates** and trusts no single number.
- **Red-teaming** is adversarial safety testing — jailbreaks, **prompt injection** (especially dangerous for agents), bias, and frontier "dangerous capability" evals. It's a continuous arms race.
- **Goodhart's Law** explains the core difficulty: optimize a proxy and it stops measuring the real thing — hence held-out evals and ever-changing benchmarks.
- **Honesty/calibration** and **hallucination** are measured but not solved; grounding and tools mitigate them.
- Evaluation **never stops**: production monitoring closes the loop back to data and alignment. "**Good**" is always relative to the use case.

---

## What's next

That completes the **core lifecycle** — from raw data all the way to a monitored, evaluated product, and back around the loop. Two further pieces extend the story:

**Chapter 8 — [Reasoning Models](08-reasoning-models.md):** a deeper look at the recent shift to models that *think* before they answer — generating long internal reasoning, trained by reinforcement on problems with checkable answers.

**Appendix — [Landmark Papers](appendix-landmark-papers.md):** a short library of the foundational works this whole story rests on — from Turing's 1936 definition of computation to the 2017 Transformer and the 2020 demonstration that scale brings few-shot learning — each with a summary and why it mattered.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
