"""Run a batch of bots in parallel and print one line per run.

usage: python run_matrix.py <immortal|mortal|planner|endgame|all> [--seeds 1,2,3] [--ticks N] [--bots a,b] [--procs 8]

immortal  every bot with the lives refilled, to reach Level 8 and beyond
mortal    every bot on the real life flow, until game over
planner   the lookahead bot, mortal and immortal
endgame   three long immortal runs (125,000 ticks) into the endless tail, without recording
all       immortal + mortal + planner
"""

from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from bots import BOT_NAMES
from paths import out_dir
from runner import finish, run_one, summary_line

MAX_REPLAY_TICKS = 60000  # the determinism replay doubles the cost of a run, so skip it for longer ones
DEFAULT_TICKS = dict(immortal=22000, mortal=40000, planner_mortal=30000, planner_immortal=22000, endgame=125000)
ENDGAME_RUNS = (("hover", 11), ("sticky", 12), ("hazard_seeker", 13))  # (bot, seed)
KINDS = ("immortal", "mortal", "planner", "endgame", "all")


def job(args):
    """Run one (bot, seed, mode, ticks, record) job; return its summary line."""
    bot_name, seed, mode, ticks, record = args
    result = run_one(bot_name, seed, mode, ticks, record=record)
    finish(result, determinism=ticks <= MAX_REPLAY_TICKS)
    return summary_line(result) + f" det={result.get('determinism_ok')}"


def build_jobs(kind, seeds, ticks, bots):
    """The list of jobs for `kind`. `ticks` overrides the default length of every job when given."""
    names = bots or list(BOT_NAMES)
    jobs = []
    if kind in ("immortal", "all"):
        jobs += [(b, s, "immortal", ticks or DEFAULT_TICKS["immortal"], True) for b in names for s in seeds]
    if kind in ("mortal", "all"):
        jobs += [(b, s, "mortal", ticks or DEFAULT_TICKS["mortal"], True) for b in names for s in seeds]
    if kind in ("planner", "all"):
        for s in seeds:
            jobs.append(("planner", s, "mortal", ticks or DEFAULT_TICKS["planner_mortal"], True))
            jobs.append(("planner", s, "immortal", ticks or DEFAULT_TICKS["planner_immortal"], True))
    if kind == "endgame":
        runs = [(b, 11 + i) for i, b in enumerate(bots)] if bots else ENDGAME_RUNS
        jobs += [(b, s, "immortal", ticks or DEFAULT_TICKS["endgame"], False) for b, s in runs]
    return jobs


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("kind", choices=KINDS)
    ap.add_argument("--seeds", default="1,2,3", help="comma list")
    ap.add_argument("--ticks", type=int, default=None, help="ticks per run; default depends on the kind")
    ap.add_argument("--bots", default=None, help="comma list; default every bot")
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    seeds = [int(x) for x in a.seeds.split(",")]
    jobs = build_jobs(a.kind, seeds, a.ticks, a.bots.split(",") if a.bots else None)
    log = out_dir("soak") / f"matrix_{a.kind}.log"
    with Pool(a.procs, maxtasksperchild=1) as pool, open(log, "a") as fh:
        for line in pool.imap_unordered(job, jobs):
            print(line, flush=True)
            fh.write(line + "\n")
            fh.flush()


if __name__ == "__main__":
    main()
