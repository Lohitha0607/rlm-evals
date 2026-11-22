# rlm-evals

How should a coding agent handle a **huge tool output** (a 40,000-line build log, a long test run, a big diff)?
This project compares three ways, as Harbor tasks with exact-answer graders.

| Mode | What the model sees when an output is huge |
|---|---|
| **A. Tail only** | the last ~2,000 lines + a path to the full output (goose today) |
| **B. Head + tail + hint** | the first and last ~1,000 lines + "narrow with grep, redirect to a file, or rerun with a higher limit" (goose #12704's agreed fix) |
| **C. RLM-style** | none of it directly: the output is stored as a variable that the model explores with code (peek / search / slice), as in Recursive Language Models |

## Conditions
- **natural** (`--ak filter=on`): a normal `shell` tool. Agents may filter at the source (`> file`, `| grep`), so huge outputs may never reach the model.
- **no-filter** (`--ak filter=off`): tools `run` (no pipes, redirects or chaining) and `write_file`, so a huge output always comes back through the mode's handler, like an MCP tool returning a big blob.

## Experiments
1. **Controlled:** one small agent with a switch for A / B / C. Same model, tools and prompt; only the output handling changes.
2. **Real agents:** goose (A today, B after #12704) vs pi vs Prime Agent (an RLM agent; Harbor adapter in harbor-framework/harbor#4419). pi vs Prime Agent is the fairest pair, since Prime Agent grew out of pi and adds the RLM REPL.

Experiment 1 ran each task × mode 5 times with free Nemotron 3.5 Super; Experiment 2 ran each task × agent 3 times with the paid version of the same model. Measured: success rate, tokens, cost, turns, split by where the answer sits (start / middle / end).

## Tasks
| Task | Answer sits | Expected |
|---|---|---|
| `first-error` | start (line 120 of 40,001; a misleading error near the end) | A fails, B and C succeed |
| `failing-test` | middle (line 20,519 of 40,003; the summary only gives the count) | A and B fail, C succeeds |
| `final-deploy` | end (the `(live)` line; earlier deploys were rolled back) | control: all succeed |
| `count-500s` | scattered (count status-500 requests in one hour across 40,000 lines) | needs every line: A and B fail unless the agent reruns with a filter; C can count with code |

Outputs are generated when the box is built and the generator is deleted, so the answer is only in the output itself.

Every task is validated before use: the reference solution (`-a oracle`) scores 1 and doing nothing (`-a nop`) scores 0.

## Layout
```
tasks/<name>/     Harbor tasks (instruction, environment, hidden tests, reference solution)
agents/           the small A/B/C agent (Experiment 1) and its tests
analyze.py        builds the results tables from jobs/
run_experiment*.sh  the exact runs behind each table
jobs/             Harbor run results (not committed)
```

## Run
```bash
harbor run -p tasks/first-error -a oracle -o jobs     # should score 1.0
harbor run -p tasks/first-error -a nop -o jobs        # should score 0.0
```

## First signal (dry run, 1 try each, free Nemotron, no-filter)
| Task | A tokens in | B tokens in | C tokens in | Solved |
|---|---|---|---|---|
| first-error | 55,712 | 38,475 | 4,623 | all |
| failing-test | 83,345 | 80,120 | 5,609 | all |

A and B recovered by grepping the saved copy of the output; C used the python tool. All solved, but C used roughly 10× fewer input tokens, because A and B keep up to 50 KB of truncated output in the context for every later turn. One try each, so this is a signal, not a result yet.

## Experiment 1 results (120 trials, free Nemotron 3.5 Super, 5 tries per cell)
Full tables: [`RESULTS-experiment1.md`](RESULTS-experiment1.md) (`python3 analyze.py`).

- **Success:** 119/120. Every mode solved every task in both conditions except one miss (A, first-error, no-filter: 4/5). With 5 tries per cell the 95% intervals overlap, so **success does not separate the modes** for this model.
- **Cost separates them clearly:** mean input tokens were **A 20.8× and B 18.6× those of C** with no filtering, and **A 13.8× and B 10.4×** in the natural condition. Example, count-500s with no filtering: A 388,152 · B 353,014 · C 8,755.
- **Why:** A and B keep up to 50 KB of truncated output in the context for every later turn and then grep the saved copy; C keeps only a handle (`out[n]`) and returns small results from code.
- **Natural condition:** the agent often filtered at the source itself, so fewer outputs were truncated (e.g. first-error: 1 of 5 runs per mode), but C was still cheapest on every task.
- **Limits:** one model, small synthetic tasks, 5 tries per cell, one agent.

## Experiment 2 results (36 trials, Nemotron 3.5 Super, 3 tries per cell)
Full table and trajectory notes: [`RESULTS-experiment2.md`](RESULTS-experiment2.md) (`python3 analyze.py --exp2`).

| Mean input tokens | first-error | failing-test | final-deploy | count-500s |
|---|---|---|---|---|
| goose | 23,204 | 20,861 | 22,481 | 26,740 |
| pi | 17,289 | 48,146 | 52,917 | 295,016 |
| Prime Agent | 97,501 | 133,692 | 161,940 | 197,678 |

- **All 36 trials solved;** cost is what differs. goose was cheapest on every task.
- **Prime Agent, the RLM-based agent, was not cheaper.** It often repeated each step in both its `bash` tool and its Python REPL, and in 4 of 12 runs the whole output still reached the model's context.
- **Takeaway with Experiment 1:** RLM-style handling cuts tokens about 20× when it is the default path for huge outputs, but not when it is an optional tool the model may skip.

## Takeaways for agent builders
1. Measure cost, not only success: every approach solved these tasks, but token use differed by up to 20×.
2. Put huge outputs behind a handle by default (store, then let the model query it) instead of pasting truncated text into the context.
3. An RLM tool next to a normal shell is not enough; the model may still pick the shell.

