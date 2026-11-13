"""Run one bot once and print the result and its findings.

usage: python smoke.py <bot> <seed> <immortal|mortal> <ticks>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from runner import BOT_AND_PLANNER_NAMES, MODES, finish, run_one, summary_line


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("bot", choices=BOT_AND_PLANNER_NAMES)
    ap.add_argument("seed", type=int)
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("ticks", type=int)
    a = ap.parse_args()
    result = finish(run_one(a.bot, a.seed, a.mode, a.ticks))
    print(summary_line(result))
    print(dict(result["stats"]), "determinism", result.get("determinism_ok"))
    for kind, finding in result["findings"].items():
        print(kind, finding["count"], str(finding["examples"][0])[:300])


if __name__ == "__main__":
    main()
