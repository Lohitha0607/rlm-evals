"""Print a deterministic ~40,000-line test run with exactly one failure.

The failing test sits in the middle of the output, and the final summary only
reports the count, so neither the head nor the tail names the failure.
"""

import random

TOTAL_TESTS = 40_000
FAILING_INDEX = 20_517
FAILING_TEST = "tests/billing/test_invoice.py::test_rounds_half_cent_up"

MODULES = ["auth", "billing", "cache", "cli", "net", "parser", "storage", "search"]
VERBS = ["handles", "rejects", "parses", "retries", "caches", "formats", "validates"]
NOUNS = ["empty_input", "unicode", "large_payload", "timeout", "nulls", "duplicates"]


def main() -> None:
    rng = random.Random(20517)
    print("============================= test session starts ==============================")
    print(f"collected {TOTAL_TESTS} items")
    for index in range(1, TOTAL_TESTS + 1):
        if index == FAILING_INDEX:
            print(f"{FAILING_TEST} FAILED")
            continue
        module = rng.choice(MODULES)
        name = f"test_{rng.choice(VERBS)}_{rng.choice(NOUNS)}_{index}"
        print(f"tests/{module}/test_{module}_{index % 97}.py::{name} PASSED")
    print(f"=================== 1 failed, {TOTAL_TESTS - 1} passed in 812.44s ===================")


if __name__ == "__main__":
    main()
