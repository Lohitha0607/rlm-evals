# Experiment 2: real agents (36 trials)

Same 4 tasks as Experiment 1, run with real agents through Harbor (natural condition: each agent's own tools).
Model: `openrouter/nvidia/nemotron-3.5-super-vl` (paid), 3 tries per cell. Prime Agent ran through the adapter in harbor-framework/harbor#4419.
Regenerate the table with `python3 analyze.py --exp2`.

| Task | Agent | Solved | 95% CI | Mean input tokens | Mean output tokens | Errors |
|---|---|---|---|---|---|---|
| first-error | goose | 3/3 | 0.44–1.00 | 23,204 | 438 | 0 |
| first-error | pi | 3/3 | 0.44–1.00 | 17,289 | 343 | 0 |
| first-error | prime-agent | 3/3 | 0.44–1.00 | 97,501 | 801 | 0 |
| failing-test | goose | 3/3 | 0.44–1.00 | 20,861 | 418 | 0 |
| failing-test | pi | 3/3 | 0.44–1.00 | 48,146 | 348 | 0 |
| failing-test | prime-agent | 3/3 | 0.44–1.00 | 133,692 | 880 | 0 |
| final-deploy | goose | 3/3 | 0.44–1.00 | 22,481 | 238 | 0 |
| final-deploy | pi | 3/3 | 0.44–1.00 | 52,917 | 477 | 0 |
| final-deploy | prime-agent | 3/3 | 0.44–1.00 | 161,940 | 906 | 0 |
| count-500s | goose | 3/3 | 0.44–1.00 | 26,740 | 757 | 0 |
| count-500s | pi | 3/3 | 0.44–1.00 | 295,016 | 1,535 | 0 |
| count-500s | prime-agent | 3/3 | 0.44–1.00 | 197,678 | 1,185 | 0 |

## Findings
- **Success does not separate the agents:** 36/36 solved.
- **Cost does:** goose used the fewest input tokens on every task (21k–27k). Prime Agent used 98k–198k, about 6× goose on average, and more than pi on 3 of 4 tasks. pi's cost jumped on `count-500s` (295k).
- **Having RLM tools is not the same as working the RLM way.** Reading the 12 Prime Agent trajectories:
  - it often ran each step twice, once with its `bash` tool and again inside `python_repl` (about 2 `bash` and 4 `python_repl` calls per run);
  - in 4 of 12 runs the whole 40,000-line output still reached the model's context (a plain `cat` of the output, or printing it in full from the REPL), which is what RLM is meant to avoid;
  - its first turn alone is about 9k input tokens of instructions, re-sent on every turn (about 14 assistant messages per run, mostly cache hits).
- **Together with Experiment 1:** when the output is stored as a variable *by design* (mode C), input tokens drop about 20×. When RLM is an optional tool next to a normal shell, the model does not reliably use it, and the saving disappears. The design point for agents such as goose: make the variable/handle path the default for huge outputs, rather than an extra tool.

## Limits
One model, 3 tries per cell, 4 synthetic tasks. Token counts include cache reads, which are billed at a lower rate. Agent versions are the ones Harbor installed on 2026-11-21/22. pi's first-error cell was re-run with one trial at a time after two setup timeouts caused by low memory on the host (the timed-out attempt is kept out of the table).
