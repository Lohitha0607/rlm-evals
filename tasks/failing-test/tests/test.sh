#!/bin/bash
# Hidden grader: reward 1 if /app/answer.txt names the failing test, else 0.
mkdir -p /logs/verifier
answer=$(tr -d '[:space:]' < /app/answer.txt 2>/dev/null)
if [ "$answer" = "tests/billing/test_invoice.py::test_rounds_half_cent_up" ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
echo "answer: '${answer}'"
