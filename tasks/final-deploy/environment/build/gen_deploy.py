"""Print a deterministic ~40,000-line deploy log whose answer is at the end.

Earlier "Deployed" lines are rollbacks of older releases; only the final one is
the deployment that is live now. This is the control task: every mode sees the
end of the output.
"""

import random

TOTAL_LINES = 40_000
STALE_DEPLOYS = {8_000: "dep-3f19a2", 21_000: "dep-77c0e4", 33_000: "dep-a05b91"}
FINAL_DEPLOY = "dep-9e41c7"

SERVICES = ["api", "worker", "web", "scheduler", "gateway"]
STEPS = [
    "pulling image",
    "running health check",
    "draining connections",
    "warming cache",
    "syncing config",
    "rotating logs",
]


def main() -> None:
    rng = random.Random(9417)
    for line in range(1, TOTAL_LINES + 1):
        if line in STALE_DEPLOYS:
            print(f"Deployed {STALE_DEPLOYS[line]} (rolled back)")
            continue
        service = rng.choice(SERVICES)
        print(
            f"[{service}] {rng.choice(STEPS)} "
            f"({rng.randint(1, 64)}/{64}) took {rng.randint(3, 900)}ms"
        )
    print(f"Deployed {FINAL_DEPLOY} (live)")
    print("deploy finished")


if __name__ == "__main__":
    main()
