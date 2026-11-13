"""Differential test: core.collision overlap vs an SDF grid oracle, over every drifter type/variant/level.

Usage: b1_collision_diff.py [samples_per_tick] [tick_stride]
Checks per sampled tick: (1) hitbox vs ship hitbox overlap, (2) graze zone vs ship overlap,
(3) hitboxes_near is True whenever the exact test is True (margins 0, 1, 14, 50), (4) boundary hunt by
bisection: the point where the code flips must be within ~0.6 px of the oracle's surface.
"""

import json, random, sys
from collections import defaultdict
from dataclasses import replace
from multiprocessing import Pool

import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT, spawn_first_valid
from paths import out_dir
from oracle import bounds, m_value
from core.collision import grow_hitbox, hitboxes_near, hitboxes_overlap
from core.drifters.base import Phase, TickContext
from core.drifters.registry import drifter_class
from core.ship import ship_hitbox, spawn
from core.world import SCREEN_H, SCREEN_W

MISS_T = -0.5  # code says no overlap, oracle depth >= 1 px
FALSE_T = 0.6  # code says overlap, oracle gap >= 1.2 px
MARGINS = (0.0, 1.0, 14.0, 50.0)
EDGE_MARGIN = 20  # the wandering test ship stays this far inside the screen


def kinds(hb):
    return "+".join(sorted({type(s).__name__ for s in hb}))


def ship_at(x, y):
    return replace(spawn(), x=x, y=y)


def pair_label(hb, shb):
    return kinds(hb) + " vs ship(Box+Box)"


def check_pair(hb, shb, grow, label, rec, ctx, stats, key):
    """Compare code vs oracle for one placed hitbox pair."""
    zone = grow_hitbox(hb, grow) if grow else hb
    code = hitboxes_overlap(zone, shb)
    m = m_value(hb, shb, grow_a=grow)
    stats[key + ":n"] += 1
    if code and m > FALSE_T:
        rec.append(("false_hit", label, m, ctx))
    elif (not code) and m < MISS_T:
        rec.append(("miss", label, m, ctx))
    for mg in MARGINS:
        if code and not hitboxes_near(hb, shb, mg if grow == 0 else max(mg, grow)) and (grow == 0 or mg >= grow):
            rec.append(("near_skip", label, mg, ctx))
    return code, m


def hunt(hb, shb_fn, grow, rng, cx, cy, ext):
    """Bisect along a random ray from far outside to the drifter center; return (lo, hi) flip points."""
    ang = rng.uniform(0, 6.2832)
    dx, dy = np.cos(ang), np.sin(ang)
    far = ext + 40
    ox, oy = cx - dx * far, cy - dy * far
    zone = grow_hitbox(hb, grow) if grow else hb

    def f(t):
        return hitboxes_overlap(zone, shb_fn(ox + dx * far * t, oy + dy * far * t))

    # find first True along the ray with fine steps
    n = 60
    for i in range(n + 1):
        t = i / n
        if f(t):
            if i == 0:
                return None
            lo, hi = (i - 1) / n, t
            for _ in range(28):
                mid = (lo + hi) / 2
                if f(mid):
                    hi = mid
                else:
                    lo = mid
            return (ox + dx * far * lo, oy + dy * far * lo), (ox + dx * far * hi, oy + dy * far * hi)
    return None


def run_combo(args):
    dt, vn, level, seed, nsamp, stride = args
    rng = random.Random(f"{dt.value}|{vn}|{level}|{seed}")  # text seeds are stable across runs; hash() of text is not
    d = spawn_first_valid(dt, vn, level, seed)
    if d is None:
        return (dt.value, vn, level, "SPAWN_FAIL", [], {})
    rec = []
    stats = defaultdict(int)
    ticks = 0
    shape_kinds = set()
    while d.phase is not Phase.GONE and ticks < 1500:
        # wandering ship near the drifter to exercise followers
        if ticks % 15 == 0:
            tx = d.x + rng.uniform(-60, 60)
            ty = d.y + rng.uniform(-60, 60)
            ship = ship_at(
                min(max(tx, EDGE_MARGIN), SCREEN_W - EDGE_MARGIN), min(max(ty, EDGE_MARGIN), SCREEN_H - EDGE_MARGIN)
            )
        d = d.update(TickContext(ship=ship, scroll_step_px=1.3)).mark_entered()
        ticks += 1
        if d.is_off_screen():
            break
        if d.phase is not Phase.ACTIVE or ticks % stride:
            continue
        hb = d.current_hitbox()
        if not hb:
            continue
        shape_kinds.add(kinds(hb))
        stats["ticks"] += 1
        b = [bounds(s) for s in hb]
        L = min(x[0] for x in b)
        T = min(x[1] for x in b)
        R = max(x[2] for x in b)
        B = max(x[3] for x in b)
        cx, cy = d.x, d.y
        ext = max(R - L, B - T)
        for grow in (0.0, d.graze_margin):
            for _ in range(nsamp):
                sx = rng.uniform(L - 22 - grow, R + 22 + grow)
                sy = rng.uniform(T - 22 - grow, B + 22 + grow)
                if rng.random() < 0.5:  # snap closer to a shape edge region
                    s0 = rng.choice(hb)
                    bb = bounds(s0)
                    sx = rng.choice([bb[0], bb[2], (bb[0] + bb[2]) / 2]) + rng.uniform(-10, 10)
                    sy = rng.choice([bb[1], bb[3], (bb[1] + bb[3]) / 2]) + rng.uniform(-10, 10)
                shb = ship_hitbox(ship_at(sx, sy))
                ctx = dict(
                    type=dt.value,
                    variant=vn,
                    level=level,
                    tick=ticks,
                    dx=round(d.x, 3),
                    dy=round(d.y, 3),
                    ship=(round(sx, 3), round(sy, 3)),
                    grow=grow,
                    seed=seed,
                )
                check_pair(
                    hb,
                    shb,
                    grow,
                    f"{'zone' if grow else 'hit'} {kinds(hb)} vs ship",
                    rec,
                    ctx,
                    stats,
                    "zone" if grow else "hit",
                )
            for _ in range(max(2, nsamp)):
                r = hunt(hb, lambda x, y: ship_hitbox(ship_at(x, y)), grow, rng, cx, cy, ext)
                if r is None:
                    continue
                lo, hi = r
                for tag, (x, y) in (("lo", lo), ("hi", hi)):
                    shb = ship_hitbox(ship_at(x, y))
                    m = m_value(hb, shb, grow_a=grow)
                    stats["hunt:n"] += 1
                    # at the flip the oracle must be within ~0.6 of zero
                    if abs(m) > 0.6:
                        ctx = dict(
                            type=dt.value,
                            variant=vn,
                            level=level,
                            tick=ticks,
                            dx=round(d.x, 3),
                            dy=round(d.y, 3),
                            ship=(round(x, 3), round(y, 3)),
                            grow=grow,
                            side=tag,
                            seed=seed,
                        )
                        rec.append(("flip_off_surface", f"{'zone' if grow else 'hit'} {kinds(hb)} vs ship", m, ctx))
    return (dt.value, vn, level, "ok", rec[:40], dict(stats) | {"shapes": sorted(shape_kinds), "ticks_life": ticks})


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("samples_per_tick", type=int, nargs="?", default=6)
    ap.add_argument("tick_stride", type=int, nargs="?", default=5)
    a = ap.parse_args()
    nsamp, stride = a.samples_per_tick, a.tick_stride
    jobs = []
    for dt, tt in KIT.tuning.drifters.items():
        c = drifter_class(dt)
        for vn in tt.variants:
            for level in (1, 4, 8):
                for seed in (11, 222, 3333) if c.seeded else (None,):
                    jobs.append((dt, vn, level, seed, nsamp, stride))
    with Pool(7) as p:
        res = p.map(run_combo, jobs, chunksize=1)
    summary = defaultdict(lambda: defaultdict(int))
    worst = {}
    n_total = 0
    for t, v, _l, st, rec, stats in res:
        if st != "ok":
            print("SPAWN FAIL", t, v)
            continue
        n_total += stats.get("hit:n", 0) + stats.get("zone:n", 0)
        for kind, label, m, ctx in rec:
            key = (kind, label)
            summary[key]["count"] += 1
            if key not in worst or abs(m) > abs(worst[key][0]):
                worst[key] = (m, ctx)
    out = {
        "samples": n_total,
        "findings": [
            {"kind": k[0], "label": k[1], "count": v["count"], "worst_m": worst[k][0], "ctx": worst[k][1]}
            for k, v in summary.items()
        ],
    }
    (out_dir("flow_collision") / "b1_collision_diff.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"combos={len(res)} oracle comparisons={n_total}")
    print("shapes seen:", sorted({s for r in res if r[3] == "ok" for s in r[5].get("shapes", [])}))
    for f in out["findings"]:
        print(f["kind"], f["label"], "count", f["count"], "worst", round(f["worst_m"], 3), f["ctx"])
    if not out["findings"]:
        print("no disagreements")


if __name__ == "__main__":
    main()
