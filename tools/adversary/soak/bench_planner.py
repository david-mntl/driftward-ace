"""Time the planner on one mortal run (seed 1, planner seed 5) and print the result.

usage: python bench_planner.py <ticks>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from planner import Planner
from runner import print_planner_report, run_one


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("ticks", type=int)
    a = ap.parse_args()
    result = run_one("planner", 1, "mortal", a.ticks, bot=Planner(5), check=True, record=False)
    print(
        result["result"],
        result["ticks"],
        result["secs"],
        result["final_score"],
        result["lives_lost"],
        result["furthest_level"],
    )
    print_planner_report(result, show_candidates=0)
    print(result["deaths"][:5])


if __name__ == "__main__":
    main()
