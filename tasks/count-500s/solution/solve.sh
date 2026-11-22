#!/bin/bash
# Reference solution: count 500s in the 14:00-14:59 hour.
set -uo pipefail
/app/access_log.sh | awk '$1 ~ /T14:/ && $4 == 500' | wc -l | tr -d ' ' > /app/answer.txt
