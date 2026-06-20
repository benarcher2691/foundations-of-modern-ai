# minimal coding agent

The runnable companion to **[Appendix B — Build a Minimal Coding Agent](../appendix-build-a-coding-agent.html)** of *Foundations of Modern AI*.

About 150 lines: an LLM, a loop, and four tools (`read_file`, `list_files`, `edit_file`, `bash`). It speaks the OpenAI Chat Completions format, so it runs against any OpenAI-compatible endpoint — here, an **open model**.

## Run it

```bash
pip install -r requirements.txt
export AI_API_KEY=...        # your provider key (required)
python agent.py
```

It defaults to **GLM-5.2 via Z.ai**. To use a different OpenAI-compatible provider, set two env vars:

| Provider | `AI_BASE_URL` | `AI_MODEL` |
|----------|---------------|------------|
| GLM (Z.ai) — default | `https://api.z.ai/api/openai/v1` | `glm-5.2` |
| MiniMax | `https://api.minimax.io/v1` | `MiniMax-M2.7` |
| Local (Ollama, etc.) | `http://localhost:11434/v1` | e.g. `qwen2.5-coder` |

> Endpoints and model names change — confirm the current ones in your provider's dashboard. MiniMax's host is `api.minimax.io` or `api.minimaxi.com` depending on region.

## ⚠ Safety

The `bash` tool runs **arbitrary shell commands** with your privileges, and the model decides what to run. Use it in a **throwaway directory**, never on anything you care about. A production harness gates this behind user approval (see Chapters 7 and 9).

## Try

```
you> create fizzbuzz.py that prints fizzbuzz for 1..20, then run it
you> what files are in this directory?
you> there's a bug in utils.py, find and fix it
```
