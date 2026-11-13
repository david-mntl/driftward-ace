"""Random fuzz of the screen flow with the invariant checker.

usage: python a1_flow_fuzz.py [n_runs] [ticks]
"""

import json, random, sys, traceback
from collections import Counter
from multiprocessing import Pool

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT, Checker, th, tick, with_lives
from core.game_flow import Screen, TickInput, start_flow
from core.saves import Saves, ScoreEntry
from paths import out_dir


def make_saves(kind, rng):
    if kind == "none":
        return None
    if kind == "empty":
        return Saves()
    if kind == "empty_nick":
        return Saves(last_nickname="ACE")
    entries = []
    if kind == "full_low":  # 10 entries all high: small scores are off the list
        entries = [ScoreEntry(nickname=f"TOP{i}", score=5000 - i * 100, level_reached=3) for i in range(10)]
    elif kind == "full_tiny":  # 10 entries with score 0..: ties at low scores
        entries = [ScoreEntry(nickname=f"T{i}", score=30 - i * 3, level_reached=1 + (i % 2 == 0)) for i in range(10)]
        entries.sort(key=lambda e: (-e.score, -e.level_reached))
    elif kind == "half":
        entries = [ScoreEntry(nickname=f"H{i}", score=200 - i * 40, level_reached=1) for i in range(5)]
    return Saves(entries=tuple(entries), last_nickname=rng.choice([None, "ZED", "A B", "0123456789"]))


def fuzz_one(args):
    seed, ticks, kind = args
    rng = random.Random(seed)
    saves = make_saves(kind, rng)
    flow = start_flow(KIT.new_run(seed), saves)
    chk = Checker(f"seed={seed} saves={kind}")
    keys = th()
    conf_p = rng.choice([0.01, 0.05, 0.2, 0.5])
    arrow_flip = rng.choice([0.02, 0.1, 0.4])
    focus_p = rng.choice([0.0, 0.002, 0.02])
    down_bias = rng.choice([0.0, 0.3, 0.6])
    confirm_hold = 0
    seen = Counter()
    exc = None
    for _t in range(ticks):
        # sticky arrows
        a = [keys.up, keys.down, keys.left, keys.right]
        for i in range(4):
            if rng.random() < arrow_flip:
                a[i] = not a[i]
        if rng.random() < down_bias * 0.1:
            a[1] = True
            a[0] = False
        keys = th(*a)
        if confirm_hold > 0:
            confirm = True
            confirm_hold -= 1
        else:
            confirm = rng.random() < conf_p
            if confirm and rng.random() < 0.3:
                confirm_hold = rng.randint(1, 120)
        focus = rng.random() < focus_p
        # speed up deaths sometimes
        if flow.screen == Screen.PLAYING and rng.random() < 0.002 and flow.run.lives > 1 and not flow.run.game_over:
            flow = with_lives(flow, 1)
        ti = TickInput(thrust=keys, confirm=confirm, focus_lost=focus)
        try:
            new = tick(flow, keys, confirm, focus)
        except Exception:
            exc = traceback.format_exc()
            chk.bad("crash", exc.splitlines()[-1] + " | " + " ".join(exc.splitlines()[-4:-1]).strip()[:300])
            break
        chk.check(flow, ti, new)
        seen[new.screen.value] += 1
        flow = new
        if len(chk.viol) > 20:
            break
    return seed, kind, chk.viol, dict(seen), chk.run_id, chk.saves_written


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("n_runs", type=int, nargs="?", default=80)
    ap.add_argument("ticks", type=int, nargs="?", default=6000)
    a = ap.parse_args()
    n, ticks = a.n_runs, a.ticks
    kinds = ["none", "empty", "empty_nick", "full_low", "full_tiny", "half"]
    jobs = [(s, ticks, kinds[s % len(kinds)]) for s in range(1000, 1000 + n)]
    with Pool(7) as p:
        res = p.map(fuzz_one, jobs, chunksize=1)
    viols = Counter()
    first = {}
    tot_seen = Counter()
    runs = saved = 0
    for _seed, _kind, v, seen, rid, sw in res:
        runs += rid
        saved += sw
        tot_seen.update(seen)
        for k, m in v:
            key = (k, m.split("] ", 1)[-1][:80])
            viols[key] += 1
            first.setdefault(key, m)
    (out_dir("flow_collision") / "a1_fuzz.json").write_text(
        json.dumps(
            {
                "viol": [[list(k), c, first[k]] for k, c in viols.items()],
                "seen": tot_seen,
                "runs": runs,
                "saved": saved,
            },
            indent=1,
        )
    )
    print(f"jobs={n} ticks={ticks} screens={dict(tot_seen)} new_runs={runs} saved_entries={saved}")
    print(f"distinct violations: {len(viols)}")
    for k, c in list(viols.items())[:15]:
        print(c, k, first[k][:200])


if __name__ == "__main__":
    main()
