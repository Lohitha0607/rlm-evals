"""Summarise Experiment 1: success, tokens and turns per task × mode × condition.

Usage: python3 analyze.py [jobs-dir] [--exp2]
Reads jobs/exp1-filter-<on|off>-<A|B|C>-<task>/<trial>/ (Harbor result.json for the
reward, agent/switch_agent_stats.json for tokens and turns) and prints Markdown
tables plus a paired "real or luck?" comparison of C against A and B.
"""

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

JOB_NAME = re.compile(r"^exp1-filter-(on|off)-([ABC])-(.+)$")
EXP2_JOB_NAME = re.compile(r"^exp2-(goose|pi|prime-agent)-(.+)$")
AGENTS = ["goose", "pi", "prime-agent"]
EXP2_TRIES = 3
TASKS = ["first-error", "failing-test", "final-deploy", "count-500s"]


def load(jobs_dir: Path) -> dict:
    """Return {(filter, mode, task): [trial dicts]}."""
    runs: dict = defaultdict(list)
    for job in sorted(jobs_dir.iterdir()):
        match = JOB_NAME.match(job.name)
        if not match or not job.is_dir():
            continue
        key = match.groups()
        for trial in sorted(p for p in job.iterdir() if p.is_dir()):
            result_path = trial / "result.json"
            if not result_path.exists():
                continue
            result = json.loads(result_path.read_text())
            rewards = (result.get("verifier_result") or {}).get("rewards") or {}
            stats_path = trial / "agent" / "switch_agent_stats.json"
            stats = json.loads(stats_path.read_text()) if stats_path.exists() else {}
            runs[key].append(
                {
                    "reward": float(rewards.get("reward", 0.0)),
                    "errored": bool(result.get("exception_info")),
                    "input_tokens": stats.get("input_tokens"),
                    "turns": stats.get("turns"),
                    "truncated": stats.get("truncated_outputs", 0),
                }
            )
    return runs


def wilson(successes: int, total: int) -> tuple[float, float]:
    """95% Wilson interval for a success rate."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.96
    p = successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (
        1 + z * z / total
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def fmt_tokens(values: list) -> str:
    values = [v for v in values if v is not None]
    return f"{round(mean(values)):,}" if values else "-"


def table(runs: dict, filter_: str) -> str:
    lines = [
        f"### Condition: filter={filter_}",
        "",
        "| Task | Mode | Solved | 95% CI | Mean input tokens | Mean turns | Truncated outputs | Errors |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for task in TASKS:
        for mode in "ABC":
            trials = runs.get((filter_, mode, task), [])
            if not trials:
                continue
            solved = sum(t["reward"] >= 1.0 for t in trials)
            low, high = wilson(solved, len(trials))
            lines.append(
                f"| {task} | {mode} | {solved}/{len(trials)} | {low:.2f}–{high:.2f} | "
                f"{fmt_tokens([t['input_tokens'] for t in trials])} | "
                f"{fmt_tokens([t['turns'] for t in trials])} | "
                f"{sum(t['truncated'] for t in trials)} | "
                f"{sum(t['errored'] for t in trials)} |"
            )
    return "\n".join(lines)


def token_ratio(runs: dict, filter_: str, mode: str) -> str:
    """Mean input tokens of `mode` divided by C's, over tasks where both ran."""
    ratios = []
    for task in TASKS:
        c = [t["input_tokens"] for t in runs.get((filter_, "C", task), []) if t["input_tokens"]]
        other = [t["input_tokens"] for t in runs.get((filter_, mode, task), []) if t["input_tokens"]]
        if c and other:
            ratios.append(mean(other) / mean(c))
    return f"{mean(ratios):.1f}×" if ratios else "-"


def load_exp2(jobs_dir: Path) -> dict:
    """Return {(agent, task): [trial dicts]} using Harbor's own token accounting."""
    runs: dict = defaultdict(list)
    for job in sorted(jobs_dir.iterdir()):
        match = EXP2_JOB_NAME.match(job.name)
        if not match or not job.is_dir():
            continue
        for trial in sorted(p for p in job.iterdir() if p.is_dir()):
            result_path = trial / "result.json"
            if not result_path.exists():
                continue
            result = json.loads(result_path.read_text())
            rewards = (result.get("verifier_result") or {}).get("rewards") or {}
            agent_result = result.get("agent_result") or {}
            runs[match.groups()].append(
                {
                    "reward": float(rewards.get("reward", 0.0)),
                    "errored": bool(result.get("exception_info")),
                    "input_tokens": agent_result.get("n_input_tokens"),
                    "output_tokens": agent_result.get("n_output_tokens"),
                }
            )
    # Experiment 2 uses 3 tries per cell; keep cells comparable if a job had more.
    return {key: trials[:EXP2_TRIES] for key, trials in runs.items()}


def exp2_table(runs: dict) -> str:
    lines = [
        "| Task | Agent | Solved | 95% CI | Mean input tokens | Mean output tokens | Errors |",
        "|---|---|---|---|---|---|---|",
    ]
    for task in TASKS:
        for agent in AGENTS:
            trials = runs.get((agent, task), [])
            if not trials:
                continue
            solved = sum(t["reward"] >= 1.0 for t in trials)
            low, high = wilson(solved, len(trials))
            lines.append(
                f"| {task} | {agent} | {solved}/{len(trials)} | {low:.2f}–{high:.2f} | "
                f"{fmt_tokens([t['input_tokens'] for t in trials])} | "
                f"{fmt_tokens([t['output_tokens'] for t in trials])} | "
                f"{sum(t['errored'] for t in trials)} |"
            )
    return "\n".join(lines)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jobs_dir = Path(args[0] if args else "jobs")
    runs = load(jobs_dir)
    exp2 = load_exp2(jobs_dir)
    if exp2 and "--exp2" in sys.argv:
        total = sum(len(v) for v in exp2.values())
        print(f"# Experiment 2 results ({total} trials)\n")
        print(exp2_table(exp2))
        return
    if not runs:
        print("No exp1 jobs found.")
        return
    total = sum(len(v) for v in runs.values())
    print(f"# Experiment 1 results ({total} trials)\n")
    for filter_ in ("off", "on"):
        if any(key[0] == filter_ for key in runs):
            print(table(runs, filter_))
            print()
            print(
                f"Input tokens vs C (mean over tasks): "
                f"A = {token_ratio(runs, filter_, 'A')}, B = {token_ratio(runs, filter_, 'B')}\n"
            )


if __name__ == "__main__":
    main()
