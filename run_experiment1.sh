#!/bin/bash
# Experiment 1: the switch agent on every task × mode × condition, 5 tries each.
# Usage: ./run_experiment1.sh [model]   (needs OPENROUTER_API_KEY in the environment)
set -uo pipefail
cd "$(dirname "$0")"

MODEL="${1:-openrouter/nvidia/nemotron-3.5-super-vl:free}"
TRIES=5
CONCURRENCY=3
export PYTHONPATH="$PWD/agents"

for filter in off on; do
  for mode in A B C; do
    for task in first-error failing-test final-deploy count-500s; do
      job="exp1-filter-$filter-$mode-$task"
      if [ -f "jobs/$job/result.json" ]; then
        echo "skip $job (done)"
        continue
      fi
      rm -rf "jobs/$job"
      echo "$(date +%H:%M:%S) start $job"
      NO_COLOR=1 harbor run -p "tasks/$task" \
        --agent switch_agent:SwitchAgent --ak "mode=$mode" --ak "filter=$filter" \
        -m "$MODEL" -k "$TRIES" -n "$CONCURRENCY" \
        -o jobs --job-name "$job" > "jobs/$job.log" 2>&1
      echo "$(date +%H:%M:%S) done  $job (exit $?)"
    done
  done
done
echo "ALL DONE"
