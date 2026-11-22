#!/bin/bash
# Reference solution: take the line marked FAILED and drop the marker.
set -uo pipefail
/app/run_tests.sh | grep -m1 ' FAILED$' | sed 's/ FAILED$//' > /app/answer.txt
