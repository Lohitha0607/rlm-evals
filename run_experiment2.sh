#!/bin/bash
# Experiment 2: real agents on every task, 5 tries each.
# Usage: ./run_experiment2.sh <agent> [model]   agent = goose | pi | prime-agent
# Needs OPENROUTER_API_KEY in the environment. Runs Harbor from ~/Desktop/harbor
# (the branch with the prime-agent adapter), so every agent uses the same Harbor.
set -uo pipefail
cd "$(dirname "$0")"

AGENT="${1:?usage: ./run_experiment2.sh <goose|pi|prime-agent> [model]}"
MODEL="${2:-openrouter/nvidia/nemotron-3.5-super-vl:free}"
TRIES="${TRIES:-3}"
CONCURRENCY="${CONCURRENCY:-2}"
HARBOR_DIR="$HOME/Desktop/harbor"
JOBS_DIR="$PWD/jobs"

for task in first-error failing-test final-deploy count-500s; do
  job="exp2-$AGENT-$task"
  if [ -f "$JOBS_DIR/$job/result.json" ]; then
    echo "skip $job (done)"
    continue
  fi
  rm -rf "$JOBS_DIR/$job"
  echo "$(date +%H:%M:%S) start $job"
  (cd "$HARBOR_DIR" && NO_COLOR=1 uv run harbor run -p "$OLDPWD/tasks/$task" \
    -a "$AGENT" -m "$MODEL" -k "$TRIES" -n "$CONCURRENCY" \
    -o "$JOBS_DIR" --job-name "$job") > "$JOBS_DIR/$job.log" 2>&1
  echo "$(date +%H:%M:%S) done  $job (exit $?)"
done
echo "ALL DONE ($AGENT)"
