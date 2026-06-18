# Foundations of Modern AI

A plain-language study series on how modern AI systems — especially Large Language Models (LLMs) like the GPT / Claude / Gemini families — are actually built. Each chapter assumes no prior math and builds on the previous one.

Each chapter exists as a Markdown source of truth (`.md`) and a self-contained, styled HTML rendering (`.html`) built from it.

## Chapters

| # | Chapter | Source | Read |
|---|---------|--------|------|
| 1 | The Top-Level Map — the 8-step lifecycle of an AI system | [`.md`](01-ai-system-lifecycle.md) | [`.html`](01-ai-system-lifecycle.html) |
| 2 | Data & Tokenization — from the messy internet to clean integers | [`.md`](02-data-and-tokenization.md) | [`.html`](02-data-and-tokenization.html) |
| 3 | The Transformer — how a model reads tokens and predicts the next one | [`.md`](03-the-transformer.md) | [`.html`](03-the-transformer.html) |
| 4 | Pretraining Mechanics — loss, gradient descent, and scaling laws | [`.md`](04-pretraining-mechanics.md) | [`.html`](04-pretraining-mechanics.html) |

*Planned:* Chapter 5 — Alignment · Chapter 6 — Inference & Applications · Chapter 7 — Evaluation & Safety.

## Building the HTML

The HTML files are generated from the Markdown with [pandoc](https://pandoc.org/) and a shared stylesheet:

```bash
./build.sh              # rebuild every chapter
./build.sh 04-pretraining-mechanics.md   # rebuild one
```

Each `.html` is standalone (CSS embedded, no external dependencies) and opens correctly on its own.

## Repository layout

```
*.md         chapter sources (the source of truth)
*.html       generated, self-contained renderings
style.css    shared stylesheet (light/dark aware)
build.sh     pandoc build script
```
