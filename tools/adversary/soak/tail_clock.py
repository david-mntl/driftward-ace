"""Cheap endgame study: the real step_run for 135,000 ticks with the wave spawns dropped (an empty field).

The wave clock, level, scroll, score and banner logic run through the whole endless tail at 1000+ ticks a
second. Full drifter play over the tail is endgame_chunks.py.

usage: python tail_clock.py <seed> [ticks]
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from simkit import load_kit
from core.scroll import scroll_speed
from bots import Hover
from oracle import Checker
from paths import out_dir
from stepper import advance

DEFAULT_TICKS = 135000  # past the end of Level 8's playlist, into the endless tail


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("seed", type=int)
    ap.add_argument("ticks", type=int, nargs="?", default=DEFAULT_TICKS)
    a = ap.parse_args()
    seed, n = a.seed, a.ticks
    kit = load_kit()
    run = kit.new_run(seed)
    bot = Hover(seed)
    chk = Checker(dict(bot="tail_clock_hover", seed=seed, mode="immortal"), kit.last_life_rules.delay_ticks)
    seg = []
    last = None
    rose = []
    banner_ticks = 0
    win = []
    t = 0
    for t in range(1, n + 1):
        run, _ = advance(kit, run, bot(run), checker=chk, immortal=True, spawn=False)
        w = run.waves
        key = (w.level, w.wave_id, w.resting, w.start_px)
        if key != last:
            last = key
            seg.append((t, w.level, w.wave_id, w.resting))
        if w.level_rose:
            rose.append((t, w.level))
        if run.level_up is not None:
            banner_ticks += 1
        if t % 6000 == 0:
            win.append(
                dict(
                    t=t,
                    level=run.level,
                    score=run.score,
                    meters=run.scroll.meters,
                    speed=scroll_speed(run.level),
                    banner=run.level_up is not None,
                    wave=w.wave_id,
                )
            )
        if run.game_over:
            break
    play = [(t, lvl, wid) for t, lvl, wid, rest in seg if not rest]
    lvl8 = [s for s in play if s[1] == 8]
    tail_counts = Counter(wid for _, _, wid in lvl8[7:])
    res = dict(
        seed=seed,
        ticks=t,
        level8_start=next((t for t, lvl, _ in play if lvl == 8), None),
        level8_playlist=lvl8[:7],
        first_tail_wave=lvl8[7] if len(lvl8) > 7 else None,
        tail_waves=len(lvl8) - 7,
        tail_counts=dict(tail_counts),
        tail_sequence_head=[w for _, _, w in lvl8[7:37]],
        level_rose_ticks=rose,
        banner_ticks=banner_ticks,
        windows=win,
        final_score=run.score,
        final_meters=run.scroll.meters,
        level_start=chk.level_start,
        findings=chk.findings,
        stats=chk.stats,
        level_by_start={lvl: min(t for t, ll, _ in play if ll == lvl) for lvl in sorted({lvl for _, lvl, _ in play})},
    )
    (out_dir("soak") / f"tail_clock_{seed}.json").write_text(json.dumps(res, default=str))
    print(
        seed,
        "ticks",
        t,
        "level8 at",
        res["level8_start"],
        "tail waves",
        res["tail_waves"],
        res["tail_counts"],
        "banner ticks",
        banner_ticks,
        "rose",
        rose[-2:],
        "findings",
        {k: v["count"] for k, v in chk.findings.items()},
        "score",
        run.score,
    )


if __name__ == "__main__":
    main()
