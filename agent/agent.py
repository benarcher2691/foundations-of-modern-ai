#!/usr/bin/env python3
"""
A minimal terminal coding agent — Foundations of Modern AI, Appendix B.

The whole thing is "an LLM, a loop, and four tools." It speaks the OpenAI
Chat Completions format, so it runs against any OpenAI-compatible endpoint —
here, an open model: GLM (Z.ai) or MiniMax. Switch providers by changing
two values (base_url + model), nothing else.

    pip install -r requirements.txt
    export AI_API_KEY=...          # your provider key (required)
    # defaults to GLM-5.2 via Z.ai; override to switch providers:
    #   export AI_BASE_URL=https://api.minimax.io/v1
    #   export AI_MODEL=MiniMax-M2.7
    python agent.py

⚠ The `bash` tool runs arbitrary shell commands with your privileges and the
  agent decides what to run. Use it in a throwaway directory, not on anything
  you care about. (A real harness would gate this behind approval — see Ch.7/9.)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

# --- Provider config (the only provider-specific part) ---------------------
# GLM (Z.ai):  base_url = https://api.z.ai/api/openai/v1   model = glm-5.2
# MiniMax:     base_url = https://api.minimax.io/v1        model = MiniMax-M2.7
# Endpoints/model names evolve — confirm the current ones in your dashboard.
BASE_URL = os.environ.get("AI_BASE_URL", "https://api.z.ai/api/openai/v1")
MODEL = os.environ.get("AI_MODEL", "glm-5.2")
API_KEY = os.environ.get("AI_API_KEY")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = (
    "You are a coding assistant working in a terminal, in the user's current "
    "directory. Use the tools to read, list, and edit files and run shell "
    "commands. Read a file before editing it. Keep replies short."
)

# --- Tools: each is a plain function + an OpenAI-style schema ---------------


def read_file(path: str) -> str:
    """Return the contents of a file at a relative path."""
    return Path(path).read_text()


def list_files(path: str = ".") -> str:
    """List files/directories under path; directories get a trailing slash."""
    items = [p.name + ("/" if p.is_dir() else "") for p in sorted(Path(path).iterdir())]
    return json.dumps(items)


def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Replace old_str with new_str. If old_str is empty, create/overwrite the file."""
    p = Path(path)
    if old_str == "":
        p.write_text(new_str)
        return f"wrote {path}"
    text = p.read_text()
    if old_str not in text:
        return "ERROR: old_str not found in file"
    p.write_text(text.replace(old_str, new_str, 1))
    return "OK"


def bash(cmd: str) -> str:
    """Run a shell command and return its combined stdout+stderr."""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return (r.stdout + r.stderr).strip() or "(no output)"


# Registry: tool name -> (python function, OpenAI tool schema)
def _schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


TOOLS = {
    "read_file": (read_file, _schema(
        "read_file", "Read the contents of a file at a relative path.",
        {"path": {"type": "string"}}, ["path"])),
    "list_files": (list_files, _schema(
        "list_files", "List files and directories under a path (default: current dir).",
        {"path": {"type": "string", "description": "Directory; defaults to '.'"}}, [])),
    "edit_file": (edit_file, _schema(
        "edit_file",
        "Replace old_str with new_str in a file. If old_str is empty, create or "
        "overwrite the file with new_str.",
        {"path": {"type": "string"},
         "old_str": {"type": "string"},
         "new_str": {"type": "string"}},
        ["path", "old_str", "new_str"])),
    "bash": (bash, _schema(
        "bash", "Run a shell command in the current directory and return its output.",
        {"cmd": {"type": "string"}}, ["cmd"])),
}

TOOL_SCHEMAS = [schema for _fn, schema in TOOLS.values()]


def run_tool(name: str, args: dict) -> str:
    fn, _schema = TOOLS[name]
    try:
        return str(fn(**args))
    except Exception as e:
        return f"ERROR: {e}"


def main() -> None:
    if not API_KEY:
        sys.exit("Set AI_API_KEY (and optionally AI_BASE_URL / AI_MODEL).")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"minimal agent — {MODEL} @ {BASE_URL}   (ctrl-c to quit)\n")

    while True:  # outer loop: one turn of conversation per user message
        try:
            user = input("\033[94myou>\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not user:
            continue
        messages.append({"role": "user", "content": user})

        while True:  # inner loop: model thinks + uses tools until it replies
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOL_SCHEMAS,
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))  # keep full history

            if not msg.tool_calls:  # no tool calls => the model answered
                print(f"\033[92mai>\033[0m {msg.content}\n")
                break

            for tc in msg.tool_calls:  # run each requested tool, feed results back
                args = json.loads(tc.function.arguments or "{}")
                result = run_tool(tc.function.name, args)
                preview = result.replace("\n", " ")[:80]
                print(f"  \033[90m[tool] {tc.function.name}({args}) -> {preview}\033[0m")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            # loop again: the model now sees the tool results and decides next step


if __name__ == "__main__":
    main()
