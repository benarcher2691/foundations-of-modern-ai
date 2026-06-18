# Appendix — Landmark Papers

> *Foundations of Modern AI* — Appendix
> Builds on: the whole series ([Chapter 1](01-ai-system-lifecycle.md) … [Chapter 7](07-evaluation-and-safety.md))
> Scope: ten foundational works the modern story rests on — each with a summary and why it mattered. The PDFs live in [`papers/`](papers/); each entry also links to its original online **source**.

---

## How to read this list

The chapters explained *how* a modern AI system works. This appendix traces *where the ideas came from* — an eight-decade arc:

```
  WHAT IS COMPUTATION?        Turing 1936
  WHAT IS INFORMATION?        Shannon 1948
  CAN A MACHINE LEARN?        Rosenblatt 1958  →  Minsky & Papert 1969 (the limits)
  HOW DOES IT LEARN (DEEPLY)? Rumelhart–Hinton–Williams 1986
  THE INFRASTRUCTURE          Lamport 1978 (distributed) · Brin & Page 1998 (web-scale data)
  THE MODERN ERA              AlexNet 2012  →  Transformer 2017  →  GPT-3 2020
```

Each entry below links the paper to the chapter it underpins.

---

## 1. On Computable Numbers, with an Application to the Entscheidungsproblem
**Alan Turing, 1936** · [📄 PDF](papers/01-turing-1936.pdf) · [source ↗](https://www.cs.virginia.edu/~robins/Turing_Paper_1936.pdf)

**Summary.** To settle a question in mathematical logic (Hilbert's *Entscheidungsproblem* — is there a mechanical procedure to decide any mathematical statement?), Turing invented an abstract machine: an infinite tape, a read/write head, and a table of rules. He showed this simple device captures *everything* that can be mechanically computed, defined the **universal machine** that can simulate any other by reading its description as data, and proved some problems (the **halting problem**) are *undecidable* — no algorithm can solve them. The answer to Hilbert was therefore *no*.

**Why it matters.** This is the theoretical bedrock of computer science. The universal machine is the idea that *one* general-purpose computer, fed different programs, can do anything computable — which is exactly what a neural network running on a GPU is. Every chapter in this series ultimately runs on Turing's insight that computation is substrate-independent and programmable.

---

## 2. A Mathematical Theory of Communication
**Claude Shannon, 1948** · [📄 PDF](papers/02-shannon-1948.pdf) · [source ↗](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf)

**Summary.** Shannon founded **information theory** in a single paper. He defined the **bit** as the unit of information, introduced **entropy** as the measure of uncertainty in a source, and proved the limits of compression (source coding) and of reliable transmission over a noisy channel (channel capacity). He also modeled English as a statistical process — using n-gram approximations to *predict the next letter/word* — strikingly prefiguring language models.

**Why it matters.** Entropy is the direct ancestor of the **cross-entropy loss** that trains every model ([Chapter 4](04-pretraining-mechanics.md)): "how surprised was the model by the true next token" *is* Shannon's surprise. Tokenization-as-compression ([Chapter 2](02-data-and-tokenization.md)) and the very framing of language modeling as next-token prediction ([Chapter 3](03-the-transformer.md)) are Shannon's legacy. Prediction and compression are two sides of one coin — his coin.

---

## 3. The Perceptron: A Probabilistic Model for Information Storage and Organization in the Brain
**Frank Rosenblatt, 1958** · [📄 PDF](papers/03-rosenblatt-1958.pdf) · [source ↗](https://www.ling.upenn.edu/courses/cogs501/Rosenblatt1958.pdf)

**Summary.** Rosenblatt proposed the **perceptron**: an artificial neuron that takes weighted inputs, sums them, and fires if the sum crosses a threshold — *and* a learning rule that adjusts the weights from examples until the outputs are correct. Crucially, the machine *learns from data* rather than being hand-programmed.

**Why it matters.** This is the ancestor of every artificial neural network. The single weighted-sum-and-activation unit is still the atom inside the Transformer ([Chapter 3](03-the-transformer.md)), and "adjust weights from examples" is the seed of all training ([Chapter 4](04-pretraining-mechanics.md)). Modern models are, in a sense, perceptrons stacked billions deep.

---

## 4. Perceptrons
**Marvin Minsky & Seymour Papert, 1969** · *book — no free full PDF; see [MIT Press](https://mitpress.mit.edu/9780262630221/perceptrons/) / [Internet Archive](https://archive.org/details/perceptronsintro0000mins)*

**Summary.** A rigorous mathematical analysis of what single-layer perceptrons *cannot* do. Most famously, they proved a one-layer perceptron cannot learn the **XOR** function (and, more generally, anything not linearly separable). They noted that multi-layer networks might overcome this, but no method to *train* such networks existed at the time.

**Why it matters.** The book's pessimism helped trigger the first **"AI winter,"** drying up neural-network funding for years. But it also framed the central challenge precisely: we need *deep* (multi-layer) networks, and we need a way to train them. That challenge stood open until backpropagation (next entry) answered it — making this the indispensable "problem statement" of deep learning. *(This is why it's a book and not a downloadable paper; the summary stands in for the text.)*

---

## 5. Time, Clocks, and the Ordering of Events in a Distributed System
**Leslie Lamport, 1978** · [📄 PDF](papers/05-lamport-1978.pdf) · [source ↗](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)

**Summary.** In a system of computers with no shared clock, what does "happened before" even mean? Lamport defined a **partial ordering** of events via the *happened-before* relation, introduced **logical clocks** to timestamp events consistently, and showed how to build a **total order** — enabling distributed machines to agree on the sequence of events (the basis of *state-machine replication*).

**Why it matters.** This is foundational to distributed computing — the substrate that makes large-scale AI *physically possible*. Pretraining a frontier model spreads one computation across tens of thousands of coordinated machines ([Chapter 4](04-pretraining-mechanics.md)), and serving it at scale ([Chapter 6](06-inference-and-applications.md)) is a distributed-systems problem. The algorithms are different from ML, but without reliable distributed coordination there is no training run and no deployment.

---

## 6. Learning Representations by Back-Propagating Errors
**David Rumelhart, Geoffrey Hinton, Ronald Williams, 1986** · [📄 PDF](papers/06-rumelhart-hinton-williams-1986.pdf) · [source ↗](https://www.cs.toronto.edu/~hinton/absps/naturebp.pdf)

**Summary.** This paper popularized **backpropagation**: an efficient way to compute, for every weight in a multi-layer network, how much it contributed to the output error — by propagating the error backward through the layers via the chain rule. With it, networks with **hidden layers** could finally be trained, and the authors showed those hidden units learn useful internal **representations** of the data on their own.

**Why it matters.** This is the answer to the challenge Minsky & Papert posed — the algorithm that made deep learning trainable. It is *exactly* the mechanism behind [Chapter 4](04-pretraining-mechanics.md): backpropagation computes the gradients, gradient descent takes the step. Every model in this series learns by the method this paper made practical.

---

## 7. The Anatomy of a Large-Scale Hypertextual Web Search Engine
**Sergey Brin & Larry Page, 1998** · [📄 PDF](papers/07-brin-page-1998.pdf) · [source ↗](http://infolab.stanford.edu/pub/papers/google.pdf)

**Summary.** The paper that introduced **Google**. It described **PageRank** — ranking web pages by the link structure of the web, treating a link as a vote weighted by the voter's own importance — and, just as importantly, the engineering of **crawling, indexing, and serving** the entire web at a scale no one had managed before.

**Why it matters.** Two legacies feed straight into modern AI. First, the discipline of **harvesting and organizing web-scale text** is the direct ancestor of the data pipelines in [Chapter 2](02-data-and-tokenization.md) (the very web crawls that became training corpora). Second, PageRank's idea of *importance from structure* echoes in how models weigh relevance — and Google's later research lab produced the Transformer itself (next entries).

---

## 8. ImageNet Classification with Deep Convolutional Neural Networks (AlexNet)
**Alex Krizhevsky, Ilya Sutskever, Geoffrey Hinton, 2012** · [📄 PDF](papers/08-alexnet-2012.pdf) · [source ↗](https://proceedings.neurips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf)

**Summary.** A deep **convolutional neural network** that won the 2012 ImageNet competition by a stunning margin, roughly halving the previous error rate. Its winning combination: a deep architecture trained on **GPUs**, the **ReLU** activation for faster training, **dropout** to curb overfitting, and heavy **data augmentation** — all fed by a massive labeled dataset.

**Why it matters.** This is the empirical "big bang" of the deep-learning era. It proved that **depth + big data + GPU compute** decisively beats hand-crafted features, and it set off the wave of investment and research that everything since rides on. The recipe it validated — scale the network, scale the data, scale the hardware — is precisely the scaling thesis formalized in [Chapter 4](04-pretraining-mechanics.md).

---

## 9. Attention Is All You Need
**Ashish Vaswani et al. (Google), 2017** · [📄 PDF](papers/09-attention-2017.pdf) · [source ↗](https://arxiv.org/abs/1706.03762)

**Summary.** Introduced the **Transformer**, an architecture built entirely on **self-attention** — letting every token directly attend to every other — with **multi-head attention** and **positional encodings**, and *no recurrence*. Removing the sequential bottleneck of earlier models made training massively **parallelizable** and long-range dependencies easy to capture.

**Why it matters.** This is the architecture of [Chapter 3](03-the-transformer.md) and the direct foundation of essentially every modern LLM (the "T" in GPT). Its parallelism is *what made models scalable* to the sizes [Chapter 4](04-pretraining-mechanics.md) describes. If one paper is the hinge between "old" and "modern" AI, it's this one.

---

## 10. Language Models are Few-Shot Learners (GPT-3)
**Tom Brown et al. (OpenAI), 2020** · [📄 PDF](papers/10-gpt3-2020.pdf) · [source ↗](https://arxiv.org/abs/2005.14165)

**Summary.** OpenAI scaled a Transformer language model to **175 billion parameters** and showed that, at that scale, the model performs new tasks from just a few examples *in the prompt* — **in-context (few-shot) learning** — with **no gradient updates or fine-tuning**. Capability emerged from scale plus a plain next-token objective.

**Why it matters.** GPT-3 demonstrated the payoff of the **scaling laws** ([Chapter 4](04-pretraining-mechanics.md)) and put **in-context learning / prompting** ([Chapter 6](06-inference-and-applications.md)) at the center of how we use models. It turned language models from research curiosities into a general-purpose technology and launched the era this entire series describes.

---

## The arc in one sentence

Turing made computation universal, Shannon made information measurable, Rosenblatt made a machine that learns, Minsky & Papert exposed its limits, backpropagation broke through them, distributed systems and web-scale data made the scaling physically possible, AlexNet proved deep learning works, the Transformer gave it the right shape, and GPT-3 showed that scale alone unlocks general capability — which is where [Chapter 1](01-ai-system-lifecycle.md) begins.

---

*Generated as part of the Foundations of Modern AI study series. Source of truth: this `.md` file; the `.html` is built from it via `./build.sh`. The PDFs in [`papers/`](papers/) remain the property of their respective authors/publishers and are included for educational reference; each entry also links to its original source.*
