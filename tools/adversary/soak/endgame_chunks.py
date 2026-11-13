"""Long immortal run in fresh-process chunks, writing out/soak/runs/endgame_<bot>_<seed>.json.

usage: python endgame_chunks.py <bot> <seed> <total_ticks> [chunk]
"""

import json
import pickle
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from simkit import load_kit
from oracle import Checker
from paths import out_dir
from runner import BOT_AND_PLANNER_NAMES, bot_for_run
from stepper import Progress

DEATHS_KEPT = 200
DEFAULT_CHUNK_TICKS = 4000


def summarize(state, bot_name, seed, total):
    """The result record for the run so far, in the shape runner.run_one writes."""
    checker, run, progress = state["checker"], state["run"], state["progress"]
    report = checker.report()
    report["deaths"] = checker.deaths[-DEATHS_KEPT:]  # a 125,000-tick run dies many times: keep the latest
    return dict(
        bot="endgame_" + bot_name,
        seed=seed,
        mode="immortal",
        ticks=progress.ticks,
        max_ticks=total,
        result=state.get("done") or "cap",
        furthest_level=progress.furthest_level,
        level8_tick=progress.level8_tick,
        final_score=run.score,
        meters=run.scroll.meters,
        lives_lost=progress.lives_lost,
        lives_left=run.lives,
        grazes=run.grazes,
        secs=round(state.get("secs", 0), 1),
        windows=progress.windows,
        death_count=len(checker.deaths),
        exception=None,
        **report,
    )


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("bot", choices=BOT_AND_PLANNER_NAMES)
    ap.add_argument("seed", type=int)
    ap.add_argument("total_ticks", type=int)
    ap.add_argument("chunk", type=int, nargs="?", default=DEFAULT_CHUNK_TICKS, help="ticks per worker process")
    a = ap.parse_args()
    bot_name, seed, total, chunk = a.bot, a.seed, a.total_ticks, a.chunk
    kit = load_kit()
    out = out_dir("soak")
    runs = out_dir("soak", "runs")
    summary_path = runs / f"endgame_{bot_name}_{seed}.json"

    def write_summary(state):
        summary_path.write_text(json.dumps(summarize(state, bot_name, seed, total), default=str))

    sp = out / f"state_{bot_name}_{seed}.pkl"
    if not sp.exists():
        state = dict(
            run=kit.new_run(seed),
            checker=Checker(
                dict(bot="endgame_" + bot_name, seed=seed, mode="immortal"), kit.last_life_rules.delay_ticks
            ),
            bot=bot_for_run(bot_name, seed),
            progress=Progress(),
        )
        sp.write_bytes(pickle.dumps(state))
    while True:
        state = pickle.loads(sp.read_bytes())
        done = state["progress"].ticks
        if done >= total or state.get("done"):
            break
        step = min(chunk, total - done)
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "chunk_worker.py"), str(sp), str(step)],
            capture_output=True,
            text=True,
            check=False,
        )
        print(r.stdout.strip()[-200:], r.stderr.strip()[-300:], flush=True)
        if r.returncode != 0:
            # The state file did not advance, so looping again would repeat the same failure forever.
            sys.exit(f"chunk_worker failed with exit code {r.returncode}")
        state = pickle.loads(sp.read_bytes())
        write_summary(state)
    write_summary(state)
    print("done", bot_name, seed, state["progress"].ticks, flush=True)


if __name__ == "__main__":
    main()
