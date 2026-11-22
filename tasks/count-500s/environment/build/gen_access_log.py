"""Print a deterministic ~40,000-line access log for one day.

The answer (how many status-500 responses happened between 14:00:00 and
14:59:59) needs every line, so no head or tail preview is enough. Run with
--answer to print the expected count instead of the log.
"""

import random
import sys

TOTAL_LINES = 40_000
PATHS = ["/api/orders", "/api/users", "/login", "/api/search", "/health", "/api/cart"]
METHODS = ["GET", "GET", "GET", "POST", "PUT", "DELETE"]


def lines():
    rng = random.Random(500)
    seconds = sorted(rng.randint(0, 86_399) for _ in range(TOTAL_LINES))
    for second in seconds:
        hour, rest = divmod(second, 3600)
        minute, sec = divmod(rest, 60)
        roll = rng.random()
        status = 500 if roll < 0.02 else 404 if roll < 0.07 else 200
        yield hour, (
            f"2026-11-02T{hour:02d}:{minute:02d}:{sec:02d}Z {rng.choice(METHODS)} "
            f"{rng.choice(PATHS)} {status} {rng.randint(2, 1800)}ms"
        ), status


def main() -> None:
    if "--answer" in sys.argv:
        print(sum(1 for hour, _, status in lines() if hour == 14 and status == 500))
        return
    for _, text, _ in lines():
        print(text)


if __name__ == "__main__":
    main()
