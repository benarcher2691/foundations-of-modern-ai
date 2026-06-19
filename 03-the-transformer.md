# The Transformer — How a Model Reads Tokens and Predicts the Next One

> *Foundations of Modern AI* — Chapter 3
> Builds on: [Chapter 2 — Data & Tokenization](02-data-and-tokenization.md) (we now have a clean stream of tokens)
> Scope: the architecture that consumes tokens — built up from scratch, with **no prior math assumed**. The one idea to master is *attention*.

---

## 0. The job we're designing a machine to do

By the end of Chapter 2 we have a stream of integer **tokens**. The Transformer's entire job is embarrassingly narrow:

> **Given the tokens so far, predict a probability for every possible next token.**

That's it. "Write me a poem," "debug this code," "explain photosynthesis" — all of it is this one operation, run over and over (we'll see how in Chapter 6). So the whole of this chapter answers: *what kind of machine can look at a sequence of tokens and produce a good guess at the next one?*

The 2017 answer — the **Transformer** ("Attention Is All You Need") — now underlies essentially every frontier model. We'll build it up piece by piece: **embeddings → attention → multiple heads → the full block → stacking**.

---

## 1. Tokens become vectors (embeddings)

An integer like `1257` carries no meaning — `1258` isn't "one more" in any useful sense. So the first thing the model does is replace each token ID with a long list of numbers called an **embedding vector** (think: a few thousand numbers per token).

The trick is that **meaning becomes direction in space.** During training the model arranges these vectors so that related tokens sit near each other and relationships become consistent directions:

```
        cat • • kitten
           •
        dog • • puppy
                              • king
                                 \  (roughly the same step:
                              • queen   "add femaleness")
        • man ──────────────► • woman
```

The famous illustration: `king − man + woman ≈ queen`. You don't program this; it *emerges* because vectors that help predict the next token well end up geometrically sensible. 

> **Key reframe:** inside the model, every token is a point in a high-dimensional "meaning space." Everything that follows is about *moving those points around* until they encode not just each word, but each word *in this particular context*.

---

## 2. The core problem: meaning depends on neighbours

A word's embedding starts out **context-free** — the token `bank` gets the same starting vector in both:

- "I sat on the river **bank**."
- "I deposited cash at the **bank**."

But the *right* meaning depends on the other words. So the machine needs a way for each token to **look at the other tokens and update itself** accordingly. "river" should pull `bank` toward the geography meaning; "cash" toward the finance meaning.

That mechanism is **attention**. It is the heart of the Transformer, and the next section is the most important page in this series so far.

---

## 3. Attention — letting tokens look at each other

Here is the idea without any equations. Every token produces three things from its current vector:

| Role | Plain-English meaning | Library analogy |
|------|-----------------------|-----------------|
| **Query** | "Here's what I'm looking for." | The search request you type. |
| **Key** | "Here's what I'm about." | The label on the spine of each book. |
| **Value** | "Here's what I actually offer." | The content inside that book. |

Attention is then a three-step dance, performed for **every token at once**:

1. **Match.** A token's *Query* is compared against the *Key* of every other token. Good matches score high. (For `bank`, its query "what disambiguates me?" matches the key of `cash` strongly.)
2. **Weight.** Those match scores are turned into percentages that add to 100% (via a function called *softmax*) — the token's "attention weights."
3. **Blend.** The token pulls in a weighted mix of everyone's *Values*, according to those percentages, and adds it to itself.

```
   "cash"   "at"   "the"   "bank" ← this token is updating itself
     │        │      │       │
   Key      Key    Key     Query  "what should I pay attention to?"
     \________\______\______/
                  match → weights:   cash 0.7  the 0.1  at 0.1  bank 0.1
                  blend their Values by those weights
                            │
                            ▼
              "bank" is now nudged toward the *finance* meaning
```

After this step, `bank`'s vector is no longer context-free — it has literally absorbed a bit of `cash`. **Attention is how context gets mixed into each token.** Because every token does this simultaneously against every other token, the model captures relationships across the whole sequence in one shot — short-range *and* long-range alike.

> Why "Attention Is All You Need": earlier models (RNNs) read left-to-right one step at a time, so distant words were hard to connect and training couldn't be parallelized. Attention compares all positions directly and in parallel — which is exactly what made models scalable to today's sizes.

### One wrinkle for generation: no peeking ahead

When the model is learning to predict the *next* token, it must not look at tokens that come *after* the one it's predicting (that would be cheating). So during this process a **causal mask** hides future positions: each token may attend only to itself and the tokens *before* it. This is why generation is called **autoregressive** — it builds the sequence strictly left to right.

---

## 4. Many heads, many kinds of relationship

One attention operation learns *one kind* of relationship. But language has many simultaneously: grammatical subject↔verb, pronoun↔referent, adjective↔noun, topic↔topic.

So Transformers run several attention operations in parallel — **multi-head attention**. Each "head" gets its own Queries/Keys/Values and specializes:

```
   Head 1: tracks subject ↔ verb agreement
   Head 2: links pronouns ("it") ↔ what they refer to
   Head 3: connects adjectives ↔ their nouns
   Head 4: follows long-range topic threads
   ...   (dozens of heads, learned automatically)
        │
        └─► their results are combined back into each token's vector
```

Nobody assigns these jobs; the heads differentiate on their own during training because diverse "viewpoints" predict the next token better than one. (Researchers later probe a trained model to discover what each head learned.)

---

## 5. The full Transformer block

Attention mixes information *between* tokens. But each token also needs to *think* about what it just absorbed. So a Transformer **block** pairs attention with a second component:

| Sub-layer | What it does | One-liner |
|-----------|--------------|-----------|
| **Multi-head attention** | Mixes context between tokens | "Gather relevant info from the sequence." |
| **Feed-forward network (MLP)** | Processes each token on its own | "Now think hard about what I gathered." |

Two structural tricks make deep stacks of these blocks trainable — worth naming because you'll hear them constantly:

- **Residual connections** — each sub-layer *adds* its result to its input instead of replacing it (`output = input + change`). Information can flow straight through, so signals (and learning) don't get lost in a deep stack.
- **Layer normalization** — re-scales the numbers at each step to keep them in a stable range, preventing them from exploding or vanishing.

```
   token vectors in
        │
   ┌────▼─────────────────┐
   │  Multi-head attention │  ── add back to input (residual) + normalize
   └────┬─────────────────┘
   ┌────▼─────────────────┐
   │  Feed-forward (MLP)   │  ── add back to input (residual) + normalize
   └────┬─────────────────┘
        ▼
   token vectors out  (same shape, richer meaning)
```

A block takes in token vectors and hands back token vectors of the same shape — just *more contextually informed*. Which means you can stack them.

---

## 6. Stack the blocks — depth builds abstraction

A real model stacks **dozens to hundreds** of these identical blocks. Each layer refines the representation a little further, and a rough hierarchy emerges:

```
   Layer 1–3    surface: spelling, word boundaries, simple syntax
   Layer 4–10   phrases, grammar, who-did-what-to-whom
   Layer 11–30  meaning, references, factual associations
   Deeper       abstract reasoning, task structure, "intent"
        │
        ▼
   a final vector for each position, rich with context
```

This mirrors the embedding intuition from Section 1: low layers handle form, high layers handle meaning. Depth is *why* large models reason in ways small ones can't.

### One more ingredient: position

Attention, by itself, is **order-blind** — it sees a *set* of tokens, not a sequence, so "dog bites man" and "man bites dog" would look identical. Transformers fix this by adding **positional information** to each token (a "position 1, position 2…" signal baked into the vectors). Now order is part of the meaning.

---

## 7. From the top of the stack to an actual next token

After the final block, each position has a context-rich vector. To turn the *last* position's vector into a prediction:

1. **Project to vocabulary scores (logits).** Multiply by the vocabulary to get one raw score per possible token — say 100,000 numbers, one per token in the vocabulary.
2. **Softmax to probabilities.** Convert those scores into percentages that sum to 100%.
3. **Sample.** Pick the next token from that distribution (greedily, or with controlled randomness — the *temperature* setting from Chapter 6).

```
   final vector ──► [logits: one score per token] ──► softmax ──► probabilities
                                                                      │
        " The cat sat on the ___ "                                    ▼
                                          mat   0.41  ┐
                                          floor 0.18  │  ← sample one
                                          sofa  0.07  │
                                          ...         ┘
```

Append the chosen token to the input and **run the whole machine again** for the next one. That loop — covered in Chapter 6 — is how a next-token predictor writes essays, code, and proofs.

---

## 8. Why the Transformer won

| Property | Why it mattered |
|----------|-----------------|
| **Parallelism** | All positions processed at once → trains efficiently on huge GPU clusters (RNNs couldn't). |
| **Long-range links** | Any token can attend to any other directly → no "forgetting" across long text. |
| **Scales cleanly** | Just add more blocks, wider vectors, more data → predictably better (the *scaling laws* of Chapter 4). |
| **General-purpose** | The same architecture handles text, code, images, audio — only the tokenizer changes. |

That combination is why one 2017 design now underlies essentially every frontier AI system.

---

## 9. Recap

- The Transformer does one thing: **read the tokens so far, output a probability for each possible next token.**
- **Embeddings** turn tokens into vectors where *meaning is direction*.
- **Attention** lets every token look at every other (Query matches Key, blend the Values) so context is mixed into each token. A **causal mask** stops it peeking ahead, making generation left-to-right.
- **Multi-head** attention learns many relationship types at once; **stacking** blocks builds abstraction from spelling up to reasoning. **Residuals + layer-norm** keep deep stacks trainable; **positional** signals restore word order.
- The top of the stack becomes **logits → softmax → a sampled next token**, then the loop repeats.

---

## Next up

**Chapter 4 — Pretraining mechanics:** we have the machine; how does it actually *learn*? We'll cover the loss function, gradient descent, what "training" physically does to those billions of parameters, and the **scaling laws** that predict how much smarter a model gets with more data and compute.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`.*
