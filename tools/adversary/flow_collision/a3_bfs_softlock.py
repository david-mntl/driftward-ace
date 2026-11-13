"""Bounded BFS over abstract key macros from sampled states: is the MENU always reachable?

usage: python a3_bfs_softlock.py [seeds]
"""

import random, sys, json
from collections import deque
from multiprocessing import Pool

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT, S, th, tick, with_lives
from core.game_flow import start_flow
from paths import out_dir
from a1_flow_fuzz import make_saves

IDLE = (th(), False, False)
MACROS = {
    "C": [(th(), True, False), IDLE],
    "U": [(th(u=1), False, False), IDLE],
    "D": [(th(d=1), False, False), IDLE],
    "L": [(th(l=1), False, False), IDLE],
    "R": [(th(r=1), False, False), IDLE],
    "F": [(th(), False, True), IDLE],
    "W20": [IDLE] * 20,
    "DIVE": [IDLE] + [(th(d=1), False, False)] * 120,
    "BURN": [IDLE] * 130,
}


def sig(f):
    r = f.run
    return (
        f.screen,
        f.menu_selection,
        f.game_over_selection,
        f.picking,
        f.picker,
        r.lives,
        r.last_life,
        r.waiting,
        r.game_over,
        len(f.saves.entries) if f.saves else -1,
        f.confirm_held,
        f.arrows_held,
    )


def apply(f, macro):
    for t, c, fo in MACROS[macro]:
        f = tick(f, t, c, fo)
    return f


def bfs(f, max_nodes=250, max_depth=14):
    if f.screen == S.MENU:
        return [], 0
    seen = {sig(f)}
    q = deque([(f, [])])
    n = 0
    while q and n < max_nodes:
        cur, path = q.popleft()
        if len(path) >= max_depth:
            continue
        for name in MACROS:
            nxt = apply(cur, name)
            n += 1
            if nxt.screen == S.MENU:
                return path + [name], n
            s = sig(nxt)
            if s in seen:
                continue
            seen.add(s)
            q.append((nxt, path + [name]))
    return None, n


def sample_states(seed, count=12, ticks=6000):
    rng = random.Random(seed)
    kind = ["none", "empty", "empty_nick", "full_low", "full_tiny", "half"][seed % 6]
    saves = make_saves(kind, rng)
    f = start_flow(KIT.new_run(seed), saves)
    f = tick(f)
    out = []
    keys = th()
    conf_p = rng.choice([0.02, 0.1, 0.3])
    for t in range(ticks):
        a = [keys.up, keys.down, keys.left, keys.right]
        for i in range(4):
            if rng.random() < 0.08:
                a[i] = not a[i]
        keys = th(*a)
        c = rng.random() < conf_p
        fo = rng.random() < 0.01
        if f.screen == S.PLAYING and rng.random() < 0.003 and f.run.lives > 1:
            f = with_lives(f, rng.choice([1, 2]))
        f = tick(f, keys, c, fo)
        if t % (ticks // count) == 0:
            out.append(f)
    return out, kind


def bot(f, limit=30000):
    """Constructive escape policy: dive until out of lives, confirm the name, pick MENU."""
    prev_down = False
    for t in range(limit):
        if f.screen == S.MENU:
            return t
        keys, conf = th(), False
        if f.screen in (S.INSTRUCTIONS, S.LEADERBOARD, S.CREDITS, S.PAUSED):
            conf = not f.confirm_held
        elif f.screen == S.PLAYING:
            if f.run.last_life:
                pass
            elif f.run.waiting:
                keys = th(u=1) if not f.arrows_held.up and not prev_down else th()
                if f.arrows_held.down:
                    keys = th()
            else:
                keys = th(d=1)
        elif f.screen == S.GAME_OVER:
            if f.picking:
                conf = not f.confirm_held
            elif f.game_over_selection.value == "retry":
                keys = th(d=1) if not f.arrows_held.down else th()
            else:
                conf = not f.confirm_held
        prev_down = keys.down
        f = tick(f, keys, conf)
    return None


def job(seed):
    states, kind = sample_states(seed)
    res = []
    for f in states:
        if f.screen in (S.PLAYING, S.PAUSED):
            path = None
            tb = bot(f)
            res.append(
                (
                    f.screen.value,
                    f.run.lives,
                    f.run.waiting,
                    f.run.last_life,
                    f.picking,
                    ["bot", tb] if tb is not None else None,
                    0,
                )
            )
            continue
        path, n = bfs(f)
        res.append((f.screen.value, f.run.lives, f.run.waiting, f.run.last_life, f.picking, path, n))
    return seed, kind, res


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("seeds", type=int, nargs="?", default=24, help="how many seeds to sample, from 500")
    nseeds = ap.parse_args().seeds
    with Pool(7) as p:
        allres = p.map(job, range(500, 500 + nseeds))
    fails = []
    total = 0
    depth = {}
    for seed, kind, res in allres:
        for scr, lives, waiting, ll, picking, path, n in res:
            total += 1
            if path is None:
                fails.append((seed, kind, scr, lives, waiting, ll, picking, n))
            else:
                depth[scr] = max(depth.get(scr, 0), len(path))
    print(f"states={total} no-path-found={len(fails)} max path len by screen={depth}")
    for x in fails[:10]:
        print("FAIL", x)
    (out_dir("flow_collision") / "a3_bfs.json").write_text(
        json.dumps({"total": total, "fails": fails, "depth": depth}, indent=1)
    )


if __name__ == "__main__":
    main()
