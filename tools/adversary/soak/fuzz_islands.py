"""Synthetic island fuzz: random island layouts (pairs, stacks, wall corners) at Level 8 scroll speed.

Not shipped content: anything found here is reachable only by a future wave.

usage: python fuzz_islands.py <seed> <ticks> [bot]
"""

from __future__ import annotations

import random
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from simkit import drifter_type, load_kit
from core.drifters.spawner import Placement
from core.waves import Wave, WaveBook, WaveKind, start_waves
from core.run import start_run
from core.world import SCREEN_W
from runner import run_one, finish, summary_line
from bots import BOT_NAMES, make_bot

ISLAND = drifter_type("floating_island")

VARIANTS = {
    "rectangle": (320, 120),
    "box": (120, 120),
    "l_shape": (320, 120),
    "t_shape": (320, 120),
    "triangle": (320, 120),
}
INVERTIBLE = {"l_shape", "t_shape", "triangle"}


def layout(rng):
    out = []
    kind = rng.choice(["single", "pair_side", "stack", "corner", "trio", "stack_tight"])

    def one(x_frac_mode, y=None, variant=None):
        v = variant or rng.choice(list(VARIANTS))
        w, h = VARIANTS[v]
        if x_frac_mode == "left":
            x = w / 2
        elif x_frac_mode == "right":
            x = SCREEN_W - w / 2
        else:
            x = rng.uniform(w / 2, SCREEN_W - w / 2)
        inv = v in INVERTIBLE and rng.random() < 0.5
        return Placement(drifter_type=ISLAND, x=x, y=y, variant=v, invert=inv), h

    if kind == "single":
        out.append(one(rng.choice(["left", "right", "any"]))[0])
    elif kind == "pair_side":
        a, _ = one("left", variant=rng.choice(["box", "rectangle", "l_shape", "t_shape"]))
        b, _ = one("right", variant=rng.choice(["box", "rectangle", "l_shape", "t_shape"]))
        out += [a, b]
    elif kind in ("stack", "stack_tight"):
        gap = rng.uniform(0, 50) if kind == "stack_tight" else rng.uniform(0, 140)
        a, ha = one("any")
        b0, hb = one("any")
        y_a = -ha / 2
        y_b = y_a - ha / 2 - gap - hb / 2
        out += [replace(a, y=y_a), replace(b0, y=y_b)]
    elif kind == "corner":
        a, ha = one(rng.choice(["left", "right"]), variant=rng.choice(["l_shape", "t_shape", "box"]))
        out.append(a)
    else:
        out += [one("any")[0] for _ in range(3)]
        out = [replace(p, y=-60 - 150 * i) for i, p in enumerate(out)]
    return out


class Injector:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.next_t = 40

    def __call__(self, run, t):
        if t >= self.next_t:
            self.next_t = t + self.rng.randint(200, 420)
            return layout(self.rng)
        return ()


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("seed", type=int)
    ap.add_argument("ticks", type=int)
    ap.add_argument("bot", nargs="?", default="island_seeker", choices=BOT_NAMES)
    a = ap.parse_args()
    seed, ticks, botname = a.seed, a.ticks, a.bot
    kit = load_kit()
    book = kit.book
    zero = Wave(wave_id="fuzz0", length_px=10**9, kind=WaveKind.FIXED, min_level=None, placements=())
    fbook = WaveBook(waves={"fuzz0": zero}, wave_zero_id="fuzz0", playlists=book.playlists)
    waves = replace(start_waves(fbook, seed, kit.level_up_rules), level=8)
    run0 = start_run(waves=waves, graze_rules=kit.graze_rules, last_life_rules=kit.last_life_rules)
    bot = make_bot(botname, seed * 101 + 3)
    res = run_one("fuzz_" + botname, seed, "immortal", ticks, bot=bot, run0=run0, inject=Injector(seed), record=True)
    finish(res, run0=run0, make_inject=lambda: Injector(seed))  # replay from the same start and the same islands
    print(summary_line(res))
    for k, f in res["findings"].items():
        print("  ", k, f["count"], str(f["examples"][0])[:260])
    print("  stats", res["stats"])


if __name__ == "__main__":
    main()
