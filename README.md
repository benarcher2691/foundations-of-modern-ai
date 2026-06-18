# Foundations of Modern AI

A plain-language study series on how modern AI systems — especially Large Language Models (LLMs) like the GPT / Claude / Gemini families — are actually built. Each chapter assumes no prior math and builds on the previous one.

Each chapter exists as a Markdown source of truth (`.md`) and a self-contained, styled HTML rendering (`.html`) built from it.

**Start here:** open [`index.html`](index.html) — a landing page linking every chapter, with a light/dark mode toggle.

## Chapters

| # | Chapter | Source | Read |
|---|---------|--------|------|
| 1 | The Top-Level Map — the 8-step lifecycle of an AI system | [`.md`](01-ai-system-lifecycle.md) | [`.html`](01-ai-system-lifecycle.html) |
| 2 | Data & Tokenization — from the messy internet to clean integers | [`.md`](02-data-and-tokenization.md) | [`.html`](02-data-and-tokenization.html) |
| 3 | The Transformer — how a model reads tokens and predicts the next one | [`.md`](03-the-transformer.md) | [`.html`](03-the-transformer.html) |
| 4 | Pretraining Mechanics — loss, gradient descent, and scaling laws | [`.md`](04-pretraining-mechanics.md) | [`.html`](04-pretraining-mechanics.html) |
| 5 | Alignment — turning a raw predictor into a helpful, honest, harmless assistant | [`.md`](05-alignment.md) | [`.html`](05-alignment.html) |
| 6 | Inference & Applications — generation, prompting, RAG, tools, and agents | [`.md`](06-inference-and-applications.md) | [`.html`](06-inference-and-applications.html) |

*Planned:* Chapter 7 — Evaluation & Safety.

## Building the HTML

The HTML files are generated from the Markdown with [pandoc](https://pandoc.org/) and a shared stylesheet:

```bash
./build.sh              # rebuild every chapter
./build.sh 04-pretraining-mechanics.md   # rebuild one
```

Each `.html` is standalone (CSS embedded, no external dependencies) and opens correctly on its own.

## Repository layout

```
index.html   landing page (links + light/dark toggle); hand-authored, not generated
*.md         chapter sources (the source of truth)
*.html       generated, self-contained chapter renderings
style.css    shared stylesheet (light/dark aware)
build.sh     pandoc build script
```
