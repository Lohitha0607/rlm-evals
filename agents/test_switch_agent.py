"""Unit tests for the switch agent's output handling (no model, no Docker)."""

import asyncio
import shutil
from pathlib import Path

import pytest

import switch_agent
from harbor.environments.base import ExecResult
from switch_agent import SwitchAgent


class LocalEnvironment:
    """Runs commands on this machine instead of in a Harbor box."""

    async def exec(self, command, cwd=None, env=None, timeout_sec=None, user=None):
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            executable="/bin/bash",
        )
        stdout, _ = await process.communicate()
        return ExecResult(stdout=stdout.decode(), return_code=process.returncode)


BIG = "for i in $(seq 1 40000); do echo line-$i; done"


@pytest.fixture(autouse=True)
def clean_out_dir():
    shutil.rmtree(switch_agent.OUT_DIR, ignore_errors=True)
    yield
    shutil.rmtree(switch_agent.OUT_DIR, ignore_errors=True)


def make_agent(mode, filter="on"):
    return SwitchAgent(
        logs_dir=Path("/tmp"), model_name="openrouter/x", mode=mode, filter=filter
    )


@pytest.mark.parametrize("mode", ["A", "B", "C"])
def test_small_output_is_shown_in_full(mode):
    text, truncated = asyncio.run(
        make_agent(mode)._shell(LocalEnvironment(), "echo hello")
    )
    assert "hello" in text
    assert not truncated


def test_mode_a_shows_only_the_tail():
    text, truncated = asyncio.run(make_agent("A")._shell(LocalEnvironment(), BIG))
    assert truncated
    assert "line-40000" in text
    assert "line-1\n" not in text
    assert "saved to /tmp/rlm_out/out_1.txt" in text


def test_mode_b_shows_head_gap_and_tail():
    text, truncated = asyncio.run(make_agent("B")._shell(LocalEnvironment(), BIG))
    assert truncated
    assert "line-1\n" in text
    assert "line-40000" in text
    assert "line-20000\n" not in text
    assert "lines omitted" in text
    assert "grep" in text


def test_mode_c_hides_the_text_and_python_can_read_it():
    agent = make_agent("C")
    environment = LocalEnvironment()
    text, truncated = asyncio.run(agent._shell(environment, BIG))
    assert truncated
    assert "line-" not in text
    assert "out[1]" in text
    result = asyncio.run(
        agent._python(environment, "print(out[1].splitlines()[19999])")
    )
    assert result.strip() == "line-20000"


def test_invalid_mode_is_rejected():
    with pytest.raises(ValueError):
        make_agent("D")


@pytest.mark.parametrize(
    "command", ["cat log | grep x", "cat log > f", "a; b", "a && b", "echo $(id)"]
)
def test_no_filter_refuses_pipes_and_redirects(command):
    text, truncated = asyncio.run(
        make_agent("A", filter="off")._run_unfiltered(LocalEnvironment(), command)
    )
    assert text.startswith("[refused")
    assert not truncated


def test_no_filter_runs_plain_commands_through_the_mode():
    text, truncated = asyncio.run(
        make_agent("B", filter="off")._run_unfiltered(LocalEnvironment(), "seq 1 40000")
    )
    assert truncated
    assert "lines omitted" in text


def test_write_file(tmp_path):
    target = tmp_path / "answer.txt"
    result = asyncio.run(
        make_agent("A", filter="off")._write_file(
            LocalEnvironment(), str(target), "E1042\n"
        )
    )
    assert result == "[written]"
    assert target.read_text() == "E1042\n"


def test_invalid_filter_is_rejected():
    with pytest.raises(ValueError):
        make_agent("A", filter="maybe")
