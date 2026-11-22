"""A small Harbor agent whose only variable is how it handles huge tool outputs.

Run with:  harbor run --agent switch_agent:SwitchAgent --ak mode=A|B|C -m openrouter/<model>

Every mode gets the same model, prompt, `shell` tool and turn budget. When a
command's output is larger than the limits, the model sees:
  A: the tail only, plus the path of the saved full output (goose today)
  B: head + an explicit gap marker + tail, plus a hint on how to narrow it
  C: none of the text, only a handle (`out[n]`) to explore with a `python` tool
"""

import asyncio
import base64
import json
import os
import shlex
import time
from pathlib import Path
from typing import Any

from openai import APIStatusError, AsyncOpenAI

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

LIMIT_LINES = 2_000
LIMIT_BYTES = 50_000
PYTHON_OUTPUT_BYTES = 10_000
COMMAND_TIMEOUT_SEC = 180
OUT_DIR = "/tmp/rlm_out"

SYSTEM_PROMPT = (
    "You are a coding agent working in a Linux container. Use the tools to run "
    "commands and inspect results. When the task is complete, reply with a short "
    "final message and no tool call."
)

SHELL_TOOL = {
    "type": "function",
    "function": {
        "name": "shell",
        "description": "Run a bash command in the container and return its output.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}

PYTHON_TOOL = {
    "type": "function",
    "function": {
        "name": "python",
        "description": (
            "Run Python 3 code in the container. `out` maps a number to the full "
            "text of each stored command output (out[3] is a str). Only `out` "
            "persists between calls. Printed output is capped at 10 KB, so print "
            "focused results (slices, matches, counts), not whole outputs."
        ),
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
}

RUN_TOOL = {
    "type": "function",
    "function": {
        "name": "run",
        "description": (
            "Run one command in the container and return its output. Pipes, "
            "redirects and command chaining (| > < ; & ` $( ) are not allowed."
        ),
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}

WRITE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write text to a file in the container (overwrites it).",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
}

# Characters that would let a command filter or redirect its own output.
FORBIDDEN_IN_NO_FILTER = ("|", ">", "<", ";", "&", "`", "$(")

PYTHON_PRELUDE = f"""
import glob as _glob, os as _os
out = {{}}
for _path in _glob.glob("{OUT_DIR}/out_*.txt"):
    _n = int(_os.path.basename(_path)[4:-4])
    with open(_path, errors="replace") as _f:
        out[_n] = _f.read()
"""


def _model_route(model_name: str) -> tuple[str, str]:
    """Return (model id, base URL) for an `openrouter/<model>` name."""
    prefix = "openrouter/"
    if not model_name.startswith(prefix):
        raise ValueError("switch_agent expects a model name like openrouter/<model>")
    return model_name[len(prefix) :], "https://openrouter.ai/api/v1"


class SwitchAgent(BaseAgent):
    def __init__(
        self,
        *args,
        mode: str = "A",
        filter: str = "on",
        max_turns: int = 25,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        mode = str(mode).upper()
        if mode not in ("A", "B", "C"):
            raise ValueError("mode must be A, B or C")
        filter = str(filter).lower()
        if filter not in ("on", "off"):
            raise ValueError("filter must be on or off")
        self.mode = mode
        # filter=off: the agent cannot pipe or redirect, so a huge output always
        # comes back through the mode's handler (like a tool returning a big blob).
        self.allow_filter = filter == "on"
        self.max_turns = int(max_turns)
        self._outputs = 0

    @staticmethod
    def name() -> str:
        return "switch-agent"

    def version(self) -> str | None:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        await environment.exec(f"mkdir -p {OUT_DIR} && chmod 1777 {OUT_DIR}")

    # ---- output handling: the only thing that differs between modes ----

    async def _show_output(
        self, environment: BaseEnvironment, n: int, path: str, exit_code: str
    ) -> tuple[str, bool]:
        """Return (text for the model, whether the output was over the limits)."""
        stats = await environment.exec(f"wc -l < {path}; wc -c < {path}")
        numbers = [int(v) for v in (stats.stdout or "").split() if v.isdigit()]
        lines, size = (numbers + [0, 0])[:2]
        header = f"[exit code {exit_code}]\n"
        if lines <= LIMIT_LINES and size <= LIMIT_BYTES:
            full = await environment.exec(f"cat {path}")
            return header + (full.stdout or ""), False

        if self.mode == "A":
            tail = await environment.exec(
                f"tail -n {LIMIT_LINES} {path} | tail -c {LIMIT_BYTES}"
            )
            return (
                header
                + (tail.stdout or "")
                + f"\n[output truncated: showing the end only. Full output "
                f"({lines} lines, {size} bytes) saved to {path}]"
            ), True

        if self.mode == "B":
            half_lines, half_bytes = LIMIT_LINES // 2, LIMIT_BYTES // 2
            head = await environment.exec(
                f"head -n {half_lines} {path} | head -c {half_bytes}"
            )
            tail = await environment.exec(
                f"tail -n {half_lines} {path} | tail -c {half_bytes}"
            )
            omitted = max(lines - LIMIT_LINES, 0)
            return (
                header
                + (head.stdout or "")
                + f"\n[... {omitted} lines omitted ...]\n"
                + (tail.stdout or "")
                + f"\n[output truncated: showing the start and end. Full output "
                f"({lines} lines, {size} bytes) saved to {path}. To see more, "
                "narrow it with grep, redirect it to a file, or rerun with a "
                "filter.]"
            ), True

        return (
            header
            + f"[output stored as out[{n}]: {lines} lines, {size} bytes; not shown. "
            f"Explore it with the python tool, for example print(out[{n}][:500]) "
            f"or [l for l in out[{n}].splitlines() if 'error' in l][:20]]"
        ), True

    # ---- tools ----

    async def _shell(
        self, environment: BaseEnvironment, command: str
    ) -> tuple[str, bool]:
        self._outputs += 1
        n = self._outputs
        path = f"{OUT_DIR}/out_{n}.txt"
        try:
            result = await environment.exec(
                f"mkdir -p {OUT_DIR}; ( {command} ) > {path} 2>&1; echo $?",
                timeout_sec=COMMAND_TIMEOUT_SEC,
            )
        except Exception as error:  # e.g. the command hung past the timeout
            return f"[command failed: {error}]", False
        exit_code = (result.stdout or "").strip().splitlines()[-1:] or ["?"]
        return await self._show_output(environment, n, path, exit_code[0])

    async def _run_unfiltered(
        self, environment: BaseEnvironment, command: str
    ) -> tuple[str, bool]:
        if any(token in command for token in FORBIDDEN_IN_NO_FILTER):
            return (
                "[refused: pipes, redirects and command chaining are not allowed; "
                "run one plain command]"
            ), False
        return await self._shell(environment, command)

    async def _write_file(
        self, environment: BaseEnvironment, path: str, content: str
    ) -> str:
        encoded = base64.b64encode(content.encode()).decode()
        result = await environment.exec(
            f"echo {encoded} | base64 -d > {shlex.quote(path)}"
        )
        return "[written]" if result.return_code == 0 else f"[failed: {result.stdout}]"

    async def _python(self, environment: BaseEnvironment, code: str) -> str:
        script = base64.b64encode((PYTHON_PRELUDE + "\n" + code).encode()).decode()
        try:
            result = await environment.exec(
                f"echo {script} | base64 -d > {OUT_DIR}/cell.py && "
                f"python3 {OUT_DIR}/cell.py 2>&1 | head -c {PYTHON_OUTPUT_BYTES}",
                timeout_sec=COMMAND_TIMEOUT_SEC,
            )
        except Exception as error:
            return f"[python failed: {error}]"
        return result.stdout or ""

    # ---- the loop ----

    async def _complete(self, client: AsyncOpenAI, **request) -> Any:
        for attempt in range(6):
            try:
                return await client.chat.completions.create(**request)
            except APIStatusError as error:
                if error.status_code not in (429, 500, 502, 503) or attempt == 5:
                    raise
                await asyncio.sleep(min(60, 5 * 2**attempt))

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        model_id, base_url = _model_route(self.model_name or "")
        client = AsyncOpenAI(
            base_url=base_url,
            api_key=self._extra_env.get("OPENROUTER_API_KEY")
            or os.environ["OPENROUTER_API_KEY"],
        )
        tools = [SHELL_TOOL] if self.allow_filter else [RUN_TOOL, WRITE_FILE_TOOL]
        if self.mode == "C":
            tools.append(PYTHON_TOOL)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": instruction},
        ]
        log_path = Path(self.logs_dir) / "switch_agent.jsonl"
        stats = {
            "turns": 0,
            "tool_calls": 0,
            "truncated_outputs": 0,
            "filtered_reruns": 0,
        }
        input_tokens = output_tokens = 0

        with log_path.open("w") as log:
            for turn in range(1, self.max_turns + 1):
                stats["turns"] = turn
                response = await self._complete(
                    client, model=model_id, messages=messages, tools=tools
                )
                if response.usage:
                    input_tokens += response.usage.prompt_tokens or 0
                    output_tokens += response.usage.completion_tokens or 0
                message = response.choices[0].message
                messages.append(message.model_dump(exclude_none=True))
                calls = message.tool_calls or []
                log.write(
                    json.dumps(
                        {
                            "turn": turn,
                            "text": message.content,
                            "tool_calls": len(calls),
                        }
                    )
                    + "\n"
                )
                if not calls:
                    break

                for call in calls:
                    stats["tool_calls"] += 1
                    started = time.monotonic()
                    try:
                        args = json.loads(call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    truncated = False
                    if (
                        call.function.name == "shell"
                        and self.allow_filter
                        and "command" in args
                    ):
                        command = args["command"]
                        if any(
                            word in command
                            for word in ("grep", "awk", "sed -n", "| head", "| tail")
                        ):
                            stats["filtered_reruns"] += 1
                        result, truncated = await self._shell(environment, command)
                    elif (
                        call.function.name == "run"
                        and not self.allow_filter
                        and "command" in args
                    ):
                        result, truncated = await self._run_unfiltered(
                            environment, args["command"]
                        )
                    elif (
                        call.function.name == "write_file"
                        and not self.allow_filter
                        and "path" in args
                    ):
                        result = await self._write_file(
                            environment, args["path"], args.get("content", "")
                        )
                    elif (
                        call.function.name == "python"
                        and self.mode == "C"
                        and "code" in args
                    ):
                        result = await self._python(environment, args["code"])
                    else:
                        result = (
                            f"Unknown tool or missing arguments: {call.function.name}"
                        )
                    stats["truncated_outputs"] += int(truncated)
                    messages.append(
                        {"role": "tool", "tool_call_id": call.id, "content": result}
                    )
                    log.write(
                        json.dumps(
                            {
                                "turn": turn,
                                "tool": call.function.name,
                                "args": args,
                                "truncated": truncated,
                                "result_chars": len(result),
                                "seconds": round(time.monotonic() - started, 2),
                            }
                        )
                        + "\n"
                    )
                context.n_input_tokens = input_tokens
                context.n_output_tokens = output_tokens

        context.n_input_tokens = input_tokens
        context.n_output_tokens = output_tokens
        context.metadata = {
            **(context.metadata or {}),
            "mode": self.mode,
            "filter": "on" if self.allow_filter else "off",
            **stats,
        }
        (Path(self.logs_dir) / "switch_agent_stats.json").write_text(
            json.dumps(
                {
                    "mode": self.mode,
                    "filter": "on" if self.allow_filter else "off",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    **stats,
                },
                indent=2,
            )
        )
