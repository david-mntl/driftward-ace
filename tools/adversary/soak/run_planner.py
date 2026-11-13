"""Run the lookahead survival bot (the planner) and print what it chose and where it died.

usage: python run_planner.py <seed> <immortal|mortal> <ticks>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from runner import MODES, finish, print_planner_report, run_one, summary_line


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("seed", type=int)
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("ticks", type=int)
    a = ap.parse_args()
    result = run_one("planner", a.seed, a.mode, a.ticks, record=False)
    finish(result, determinism=False)
    print(summary_line(result))
    print_planner_report(result)
    deaths_by_wave = {}
    for death in result["deaths"]:
        deaths_by_wave[death["wave"]] = deaths_by_wave.get(death["wave"], 0) + 1
    print("deaths by wave", deaths_by_wave)


if __name__ == "__main__":
    main()
