#!/bin/bash
# Reference solution: take the first `error[CODE]` line from the build output.
set -uo pipefail
/app/build.sh 2>&1 | grep -m1 -oE '^error\[E[0-9]+\]' | sed -E 's/^error\[(E[0-9]+)\]$/\1/' > /app/answer.txt
