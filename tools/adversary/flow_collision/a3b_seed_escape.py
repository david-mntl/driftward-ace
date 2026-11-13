"""Single-seed version of a3_bfs_softlock: from the states sampled for one seed, reach the menu.

The pooled a3 run hung on a worker once, so its result comes from 24 of these.

usage: python a3b_seed_escape.py <seed>
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from a3_bfs_softlock import bfs, bot, sample_states
from flowlib import S


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("seed", type=int)
    seed = ap.parse_args().seed
    started = time.time()
    states, _kind = sample_states(seed)
    print(seed, "sampled", round(time.time() - started, 1), flush=True)
    for i, flow in enumerate(states):
        state_started = time.time()
        if flow.screen in (S.PLAYING, S.PAUSED):
            result = bot(flow)
        else:
            result = bfs(flow)[0]
        print(
            seed,
            i,
            flow.screen.value,
            "->",
            (result if result is None or isinstance(result, int) else len(result)),
            round(time.time() - state_started, 1),
            flush=True,
        )


if __name__ == "__main__":
    main()
