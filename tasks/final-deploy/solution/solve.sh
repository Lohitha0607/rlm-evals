#!/bin/bash
# Reference solution: take the id from the "(live)" deploy line.
set -uo pipefail
/app/deploy.sh | grep ' (live)$' | tail -1 | awk '{print $2}' > /app/answer.txt
