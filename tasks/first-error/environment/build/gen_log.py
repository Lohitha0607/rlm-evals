"""Print a deterministic ~40,000-line failed build log.

The first real error is near the top; a second, misleading error sits near
the end, so an agent that only sees the tail of the output answers wrong.
"""

import random

TOTAL_LINES = 40_000
FIRST_ERROR_LINE = 120
LATE_ERROR_LINE = 39_600

CRATES = ["core", "parser", "net", "storage", "auth", "cli", "metrics", "cache"]
FILES = ["lib.rs", "mod.rs", "config.rs", "handler.rs", "utils.rs", "types.rs"]
WARNINGS = [
    "unused variable `{name}`",
    "unused import: `std::{name}`",
    "field `{name}` is never read",
    "function `{name}` is never used",
    "variable `{name}` does not need to be mutable",
]
NAMES = ["buf", "idx", "ctx", "tmp", "cfg", "len", "conn", "rows", "item", "key"]


def main() -> None:
    rng = random.Random(1042)
    line = 0
    while line < TOTAL_LINES:
        line += 1
        if line == FIRST_ERROR_LINE:
            print("error[E1042]: cannot find function `parse_config` in module `core::config`")
            continue
        if line == LATE_ERROR_LINE:
            print("error[E2077]: build script for `metrics` exited with status 1")
            continue
        crate = rng.choice(CRATES)
        kind = rng.random()
        if kind < 0.15:
            print(f"   Compiling {crate} v0.{rng.randint(1, 9)}.{rng.randint(0, 20)}")
        elif kind < 0.85:
            name = rng.choice(NAMES)
            message = rng.choice(WARNINGS).format(name=name)
            print(
                f"warning: {message}  --> src/{crate}/{rng.choice(FILES)}:"
                f"{rng.randint(1, 900)}:{rng.randint(1, 80)}"
            )
        else:
            print(f"    = note: `#[warn(dead_code)]` on by default in `{crate}`")
    print("error: could not compile `app` due to previous errors")


if __name__ == "__main__":
    main()
