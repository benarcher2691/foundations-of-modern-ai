# Pretraining Mechanics — How Billions of Numbers Learn to Predict

> *Foundations of Modern AI* — Chapter 4
> Builds on: [Chapter 3 — The Transformer](03-the-transformer.md) (we have the machine; now it must learn)
> Scope: what "training" physically does — the **loss**, **gradient descent**, and the **scaling laws** that predict how good a model gets. No prior math assumed.

---

## 0. What's actually inside the machine

In Chapter 3 we built the Transformer's *structure* — embeddings, attention, blocks. But a freshly built Transformer is useless: its **parameters** (also called *weights* — the billions of numbers that fill the attention and feed-forward layers) start as **random noise**. Ask it to predict the next token and it produces gibberish, every token equally likely.

**Pretraining is the process of adjusting those billions of numbers until the predictions become good.** That's the whole game. This chapter is about *how* that adjustment happens, mechanically, and *how far* it can be pushed (scaling laws).

> Helpful frame: the architecture is the *shape* of the brain; the parameters are *what it has learned*. Two models with identical architecture but different parameters are as different as two people with the same kind of brain but different memories.

---

## 1. Measuring wrongness: the loss

You can't improve what you can't measure. So we need a single number that says *how wrong* the model currently is. That number is the **loss**.

The recipe, for next-token prediction:

1. Take real text from the corpus: `"The cat sat on the ___"`.
2. The model outputs a probability for every possible next token (Chapter 3, Section 7).
3. Look at the probability it gave to the token that *actually* came next (`mat`).
4. **High probability on the right answer → low loss. Low probability → high loss.** (Technically this is *cross-entropy*: the loss is large when the model was "surprised" by the true token.)

```
   model said:  mat 0.41, floor 0.18, sofa 0.07, ...
   truth was:   "mat"
   gave it 0.41 → "mildly surprised" → moderate loss

   if it had said mat 0.95 → low loss   (confident & correct)
   if it had said mat 0.01 → high loss  (confident & wrong = heavily penalized)
```

Average this over a huge amount of text and you get **the** number that training tries to push down. Lower loss = better next-token predictions = a more capable model. *Everything* in pretraining is in service of reducing this one quantity.

---

## 2. The learning step: gradient descent

Now the central question: given that the loss is too high, **which way should we nudge each of the billions of parameters to make it lower?**

The answer comes from the **gradient** — for every single parameter, a number saying "if you increase this weight a tiny bit, the loss goes *up* this much (or *down* this much)." The gradient is computed by an algorithm called **backpropagation**, which efficiently traces the loss backward through every layer to assign each parameter its share of the blame.

Then we take a small step in the direction that *reduces* loss. This is **gradient descent**, and the standard analogy is exact:

```
   You're on a foggy hillside (the "loss landscape") and want the valley floor.
   You can't see far, but you can feel the slope under your feet (the gradient).
   Rule: step a little in the steepest-downhill direction. Repeat.

        loss
         │   \                         . ← random start (high loss)
         │    \                      .'
         │     \                  .'   each step ↓ reduces loss
         │      '.            _.-'
         │        '._     _.-'
         │           '---'  ← lower loss (better model)
         └──────────────────────────────► (billions of parameter dimensions)
```

How big a step? The **learning rate** — too large and you overshoot the valley; too small and training takes forever. Tuning it is part of the craft.

### The training loop, in full

Pretraining is just this loop, repeated an astronomical number of times:

```
   repeat for trillions of tokens:
     1. FORWARD   — feed a batch of text through the model, get predictions
     2. LOSS      — measure how wrong they were
     3. BACKWARD  — backpropagation computes the gradient for every parameter
     4. UPDATE    — nudge every parameter a small step downhill (gradient descent)
```

A few terms you'll now recognize:
- **Batch** — we process many text chunks at once (thousands of tokens) per step, for stable, efficient updates.
- **Step** — one pass of the four-stage loop above; a big run is *millions* of steps.
- **Epoch** — one full pass over the dataset. Frontier LLMs often train for only ~1 epoch (or less) on deduplicated data — they're so data-hungry that seeing data once is typical, which is also why the *deduplication* from Chapter 2 matters so much.

That's it. There is no separate "understanding" module — grammar, facts, reasoning, and coding ability are **all** side-effects of relentlessly minimizing next-token loss over a vast, varied corpus.

---

## 3. The staggering scale

This loop is conceptually simple but physically enormous. The compute bill is governed by a rough rule:

> **Training compute ≈ 6 × (number of parameters) × (number of training tokens).**

Plug in frontier numbers — hundreds of billions of parameters, trillions of tokens — and you get figures like **10²⁵ floating-point operations**, which translates to:

| Resource | Frontier-scale ballpark |
|----------|-------------------------|
| Hardware | Tens of thousands of GPUs/TPUs in a cluster |
| Wall-clock time | Weeks to a few months of continuous running |
| Cost | Tens to hundreds of millions of dollars per run |
| Output | One set of trained parameters (a "base model") |

This is why pretraining happens **rarely** (a handful of times per model generation), is done by **few organizations**, and is checkpointed obsessively — a crash 80% through a two-month run is enormously expensive, so the parameters are saved to disk continually.

It also reframes everything downstream: post-training (Chapter 5) and inference (Chapter 6) are *cheap* by comparison. The giant, one-time cost is here.

---

## 4. Scaling laws: bigger is predictably better

The discovery that powered the last several years: **model quality improves smoothly and predictably as you add compute, data, and parameters.** Plot loss against scale and you get a clean, descending **power law** — no plateau in the ranges explored so far.

```
   loss
     │•
     │ ••                  Each 10× in compute buys a
     │   •••               reliable, measurable drop in loss.
     │      ••••           Smooth enough to *forecast* a big
     │          •••••      model's loss from small experiments.
     │               ••••••••••
     └────────────────────────────► compute / data / parameters  (log scale)
```

Why this matters: it turns model-building from alchemy into **planning**. Before spending $100M, labs run small models, fit the curve, and extrapolate what the big one will achieve. It's the closest thing the field has to an engineering law.

### Compute-optimal training (the "Chinchilla" insight)

Given a fixed compute budget, should you build a *bigger* model or train on *more data*? Early models were oversized and undertrained. The **Chinchilla** finding (2022) showed a balanced ratio is best — roughly **20 training tokens per parameter** — and that a smaller, well-fed model beats a larger, data-starved one. This is *why* token counts exploded into the trillions, and why the data-curation work of Chapter 2 became a frontier bottleneck: at some point you run out of high-quality tokens.

### Emergence: abilities that switch on

Scaling isn't only smooth. Some capabilities — multi-step arithmetic, certain kinds of reasoning, following novel instructions — are nearly absent in small models and then appear **relatively abruptly** past a size threshold. These **emergent abilities** are part of why scaling has been pursued so aggressively, and part of why each model generation surprises even its builders. (How sharp these jumps "really" are is an active research debate, but the practical effect — new skills arriving with scale — is not in dispute.)

---

## 5. What you get at the end: a base model

When the loop finally stops, you have a **base (pretrained) model**: parameters that encode a vast amount of the world's text. It is startlingly capable — and also not yet the assistant you talk to.

| A base model **can** | A base model **cannot (yet)** |
|----------------------|-------------------------------|
| Continue/complete any text plausibly | Reliably *follow an instruction* rather than just continue it |
| Reproduce grammar, facts, code, styles | Know when to refuse harmful or unsafe requests |
| Do in-context learning from examples in the prompt | Hold a helpful chat persona, or say "I don't know" |
| Serve as the raw substrate of intelligence | Behave safely and predictably out of the box |

Ask a base model "What is the capital of France?" and it might helpfully answer *Paris* — or it might continue with "What is the capital of Germany? What is the capital of Spain?" because that pattern (a quiz list) is also a plausible *continuation*. It predicts; it doesn't yet *assist*.

Closing that gap — turning a raw next-token predictor into a helpful, honest, harmless assistant — is **post-training and alignment**, the subject of Chapter 5.

---

## 6. Recap

- A model's **parameters** start random; **pretraining** adjusts them until next-token predictions are good.
- The **loss** measures wrongness (surprise at the true next token). All of training minimizes this one number.
- **Backpropagation** computes the **gradient** (which way to nudge each parameter); **gradient descent** takes a small downhill step. Repeat over **trillions of tokens** — that loop *is* learning.
- The scale is enormous (≈ `6 × params × tokens` operations → months, many GPUs, huge cost), which is why pretraining is rare and downstream steps are comparatively cheap.
- **Scaling laws** make quality a predictable function of compute/data/size; **Chinchilla** says balance parameters with ~20× tokens; some abilities **emerge** abruptly with scale.
- The result is a **base model** — broadly capable, but not yet an instruction-following, safe assistant. That's Chapter 5.

---

## Next up

**Chapter 5 — Alignment:** how supervised fine-tuning (SFT) and reinforcement learning from human (or AI) feedback (RLHF/RLAIF, DPO) turn a raw base model into the helpful, honest, and harmless assistant you actually interact with.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
