# Experiment 1 results (120 trials)

### Condition: filter=off

| Task | Mode | Solved | 95% CI | Mean input tokens | Mean turns | Truncated outputs | Errors |
|---|---|---|---|---|---|---|---|
| first-error | A | 4/5 | 0.38–0.96 | 82,302 | 7 | 5 | 0 |
| first-error | B | 5/5 | 0.57–1.00 | 81,522 | 7 | 5 | 0 |
| first-error | C | 5/5 | 0.57–1.00 | 6,013 | 6 | 5 | 0 |
| failing-test | A | 5/5 | 0.57–1.00 | 77,491 | 6 | 5 | 0 |
| failing-test | B | 5/5 | 0.57–1.00 | 72,012 | 6 | 5 | 0 |
| failing-test | C | 5/5 | 0.57–1.00 | 9,148 | 8 | 5 | 0 |
| final-deploy | A | 5/5 | 0.57–1.00 | 134,927 | 8 | 5 | 0 |
| final-deploy | B | 5/5 | 0.57–1.00 | 102,529 | 6 | 5 | 0 |
| final-deploy | C | 5/5 | 0.57–1.00 | 7,996 | 7 | 5 | 0 |
| count-500s | A | 5/5 | 0.57–1.00 | 388,152 | 11 | 5 | 0 |
| count-500s | B | 5/5 | 0.57–1.00 | 353,014 | 11 | 6 | 0 |
| count-500s | C | 5/5 | 0.57–1.00 | 8,755 | 7 | 5 | 0 |

Input tokens vs C (mean over tasks): A = 20.8×, B = 18.6×

### Condition: filter=on

| Task | Mode | Solved | 95% CI | Mean input tokens | Mean turns | Truncated outputs | Errors |
|---|---|---|---|---|---|---|---|
| first-error | A | 5/5 | 0.57–1.00 | 24,036 | 5 | 1 | 0 |
| first-error | B | 5/5 | 0.57–1.00 | 19,874 | 5 | 1 | 0 |
| first-error | C | 5/5 | 0.57–1.00 | 9,414 | 4 | 1 | 0 |
| failing-test | A | 5/5 | 0.57–1.00 | 26,165 | 4 | 2 | 0 |
| failing-test | B | 5/5 | 0.57–1.00 | 28,495 | 4 | 2 | 0 |
| failing-test | C | 5/5 | 0.57–1.00 | 6,023 | 5 | 2 | 0 |
| final-deploy | A | 5/5 | 0.57–1.00 | 78,339 | 5 | 5 | 0 |
| final-deploy | B | 5/5 | 0.57–1.00 | 74,431 | 5 | 5 | 0 |
| final-deploy | C | 5/5 | 0.57–1.00 | 5,636 | 6 | 5 | 0 |
| count-500s | A | 5/5 | 0.57–1.00 | 161,690 | 6 | 5 | 0 |
| count-500s | B | 5/5 | 0.57–1.00 | 102,109 | 5 | 3 | 0 |
| count-500s | C | 5/5 | 0.57–1.00 | 4,703 | 4 | 4 | 0 |

Input tokens vs C (mean over tasks): A = 13.8×, B = 10.4×

