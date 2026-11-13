"""Advance a pickled long run by N ticks in a fresh process, so a busy machine schedules it fairly.

The state file is created and driven by endgame_chunks.py.

usage: python chunk_worker.py <state.pkl> <ticks>
"""

import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from simkit import load_kit
import oracle  # noqa: F401  (installs the capture hook)
from stepper import advance, record_crash


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("state", type=Path, help="the pickled state written by endgame_chunks.py")
    ap.add_argument("ticks", type=int)
    a = ap.parse_args()
    path, ticks = a.state, a.ticks
    state = pickle.loads(path.read_bytes())
    kit = load_kit()
    run, checker, bot, progress = state["run"], state["checker"], state["bot"], state["progress"]
    started = time.time()
    end = progress.ticks + ticks
    while progress.ticks < end and not state.get("done"):
        try:
            run, lives_lost = advance(kit, run, bot(run), checker=checker, tick=progress.ticks, immortal=True)
        except Exception:
            record_crash(checker, run, progress.ticks)
            state["done"] = "exception"
            break
        progress.observe(run, lives_lost)
        if run.game_over:
            state["done"] = "game_over"
    state["run"] = run
    state["secs"] = state.get("secs", 0) + time.time() - started
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(pickle.dumps(state))
    tmp.replace(path)
    print(f"{path.name} t={progress.ticks} level={run.level} {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
