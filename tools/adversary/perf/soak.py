"""Desktop full-loop soak: the real frame loop with real drawing, fake clock, 1 tick per frame.

Immortal autopilot (lives reset to 5), dummy SDL drivers. Records per frame: tick ms, draw ms,
draw split per part, drifter counts by type and phase, level, wave id, GC time. Nothing here
edits game/: everything is monkeypatched at runtime.

Usage: python soak.py --label NAME [--seed N] [--tail-minutes M] [--lean] [--tracemalloc]
         [--profile-levels N] [--profile-waves ID,ID --profile-frames N] [--nodraw-until-profile]
         [--shots DIR] [--max-frames N]
"""

import argparse
import asyncio
import cProfile
import contextlib
import dataclasses
import gc
import json
import os
import random
import sys
import time
import types
from array import array
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: paths
from paths import GAME_DIR, out_dir

sys.path.insert(0, str(GAME_DIR))

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--tail-minutes", type=float, default=21.0)
ap.add_argument("--lean", action="store_true", help="no per-frame arrays, periodic samples only")
ap.add_argument("--tracemalloc", action="store_true")
ap.add_argument("--profile-levels", type=int, default=0, help="cProfile the first N frames of each level (and tail)")
ap.add_argument("--profile-waves", default="", help="comma list of wave ids to cProfile (all their frames)")
ap.add_argument("--profile-frames", type=int, default=3000, help="max frames profiled per wave id")
ap.add_argument("--nodraw-until-profile", action="store_true", help="skip drawing outside profile windows")
ap.add_argument("--shots", default="")
ap.add_argument("--max-frames", type=int, default=0)
ap.add_argument("--jump", default="", help="start the waves at level N, or tail (past Level 8 slots)")
ap.add_argument("--jump-slot", type=int, default=0)
ap.add_argument("--stop-level", type=int, default=0, help="stop 150 frames after the level exceeds N")
ap.add_argument(
    "--nodraw-tail-minutes", type=float, default=0.0, help="skip drawing for the first M minutes of the tail"
)
ap.add_argument(
    "--sweep", type=int, default=0, help="profile N frames at each level 1..8 and the tail, jumping between them"
)
ap.add_argument("--checkpoint", type=int, default=0, help="write the npz every N frames")
ARGS = ap.parse_args()

OUT = out_dir("perf")

import pygame

import core.game_flow as gf
import core.run as cr
from core.drifters.base import DrifterType
from core.levels import LEVEL_COUNT

random.seed(ARGS.seed)
real_step_run = cr.step_run
hits = [0]


def immortal_step_run(run, thrust):
    out = real_step_run(run, thrust)
    if 0 < out.lives < 3:
        hits[0] += 1
        out = cr.replace(out, lives=5)
    return out


gf.step_run = immortal_step_run

fake_t = [0.0]


def fake_clock():
    fake_t[0] += 1 / 60
    return fake_t[0]


import app.frame as fr
import ui.background_view as bv
import ui.hud as hud_mod
import ui.level_up_view as luv
import ui.mute_icon as mi

real_perf = time.thread_time  # CPU time of this thread: robust to the box being oversubscribed
wall_clock = time.perf_counter
fr.time = types.SimpleNamespace(perf_counter=fake_clock)
fr.FOCUS_LOST_EVENTS = frozenset()

frame_no = [0]
rng = random.Random(ARGS.seed + 100)
flow_ref = [None]
steer = [0]


class Pressed:
    def __init__(self, keys):
        self.keys = keys

    def __getitem__(self, k):
        return k in self.keys


def fake_get_pressed():
    n = frame_no[0]
    keys = set()
    fl = flow_ref[0]
    if fl is None or fl.screen.name != "PLAYING":
        if n % 20 < 3:
            keys.add(pygame.K_RETURN)
        return Pressed(keys)
    if n % 90 == 0:
        steer[0] = rng.choice([-1, 0, 1])
    ship = fl.run.ship
    if ship.y > 330 or (ship.y > 250 and n % 4 != 0):
        keys.add(pygame.K_UP)
    if ship.x < 120:
        steer[0] = 1
    elif ship.x > 520:
        steer[0] = -1
    if steer[0] == 1:
        keys.add(pygame.K_RIGHT)
    elif steer[0] == -1:
        keys.add(pygame.K_LEFT)
    return Pressed(keys)


pygame.key.get_pressed = fake_get_pressed

# ---- per-part timers -------------------------------------------------------------------------
PARTS: dict[str, float] = {}
PART_NAMES = [
    "bg",
    "bg_paint",
    "bg_river",
    "bg_swirl",
    "bg_planets",
    "star",
    "drift",
    "ship",
    "pop",
    "ring",
    "burst",
    "hud",
    "lub",
    "luf",
    "mute",
    "dim",
    "step_flow",
    "add_drifters",
]
TYPE_NAMES = [t.value for t in DrifterType]
for t in TYPE_NAMES:
    PART_NAMES.append("d:" + t)


def timed(name, fn):
    def w(*a, **k):
        c = real_perf()
        r = fn(*a, **k)
        PARTS[name] = PARTS.get(name, 0.0) + (real_perf() - c) * 1000
        return r

    return w


fr.draw_background = timed("bg", fr.draw_background)
for nm, part in (
    ("_draw_painting", "bg_paint"),
    ("_draw_river", "bg_river"),
    ("_draw_swirl", "bg_swirl"),
    ("_draw_planets", "bg_planets"),
):
    setattr(bv, nm, timed(part, getattr(bv, nm)))
fr.draw_starfield = timed("star", fr.draw_starfield)
fr.draw_ship = timed("ship", fr.draw_ship)
fr.draw_points_popup = timed("pop", fr.draw_points_popup)
fr.draw_graze_ring = timed("ring", fr.draw_graze_ring)
fr.draw_burst = timed("burst", fr.draw_burst)
hud_mod.HudView.draw = timed("hud", hud_mod.HudView.draw)
hud_mod.HudView.dim = timed("dim", hud_mod.HudView.dim)
luv.LevelUpView.draw_banner = timed("lub", luv.LevelUpView.draw_banner)
luv.LevelUpView.draw_flight = timed("luf", luv.LevelUpView.draw_flight)
mi.MuteIconView.draw = timed("mute", mi.MuteIconView.draw)
PENDING = [ARGS.jump] if ARGS.jump else []
SWEPT: set = set()
_sf = fr.step_flow


def jumping_step_flow(flow, inp):
    if PENDING and flow.screen.name == "PLAYING" and flow.run.waves is not None:
        from dataclasses import replace as _rep

        j = PENDING.pop(0)
        lvl = 8 if j == "tail" else int(j)
        w = flow.run.waves
        slot = len(w.book.level_slots(lvl)) if j == "tail" else (ARGS.jump_slot if j == ARGS.jump else 0)
        if j == "tail":
            S.l8_wave_count = L8_SLOTS
        flow = _rep(
            flow, run=_rep(flow.run, waves=_rep(w, level=lvl, next_slot=slot, resting=True, rest_ticks_left=30))
        )
    return _sf(flow, inp)


fr.step_flow = timed("step_flow", jumping_step_flow)
fr.add_flow_drifters = timed("add_drifters", fr.add_flow_drifters)

_real_render = fr.render_drifter


def render_timed(surface, drifter):
    c = real_perf()
    _real_render(surface, drifter)
    ms = (real_perf() - c) * 1000
    PARTS["drift"] = PARTS.get("drift", 0.0) + ms
    k = "d:" + drifter.drifter_type.value
    PARTS[k] = PARTS.get(k, 0.0) + ms


fr.render_drifter = render_timed

# ---- state tracking --------------------------------------------------------------------------
from app.waves import load_wave_book
from app.tuning import load_tuning

BOOK = load_wave_book(load_tuning())
L8_SLOTS = len(BOOK.level_slots(LEVEL_COUNT))
WAVE_IDS: dict[str, int] = {}
LEVEL_FRAME0: dict[int, int] = {}


@dataclasses.dataclass
class St:
    """Where the run is, for the frame spy. One instance, `S`."""

    prev_resting: bool = True
    prev_wave: str | None = None
    wave_seq: int = 0
    l8_wave_count: int = 0
    tail: bool = False
    tail_start_frame: int | None = None
    shots: set[str] = dataclasses.field(default_factory=set)
    l4_max: int = 0
    l8_shot_at: int | None = None
    stop_at: int | None = None


S = St()

# per-frame arrays
A = {}
if not ARGS.lean:
    for k in ("tick", "draw", "wall", "gc", "canary"):
        A[k] = array("f")
    for k in PART_NAMES:
        A["p:" + k] = array("f")
    for k in ("level", "wave", "seq", "nd", "nwarn", "nactive", "pop", "ring", "flags", "tail"):
        A[k] = array("i")
    for t in TYPE_NAMES:
        A["n:" + t] = array("H")
TICK = [0.0]
DRAW = [0.0]
GC_MS = [0.0]
_gc_t = [0.0]
gc_events = []


def gc_cb(phase, d):
    if phase == "start":
        _gc_t[0] = real_perf()
    else:
        ms = (real_perf() - _gc_t[0]) * 1000
        GC_MS[0] += ms
        gc_events.append((frame_no[0], d["generation"], ms, d["collected"]))


gc.callbacks.append(gc_cb)

# ---- profile control -------------------------------------------------------------------------
prof = [None]
prof_stats: dict[str, cProfile.Profile] = {}
prof_frames: dict[str, int] = {}
PROFILE_WAVES = [w for w in ARGS.profile_waves.split(",") if w]


def want_profile_key(flow):
    """The profile bucket this frame belongs to, or None."""
    if flow is None:
        return None
    w = flow.run.waves
    if w is None:
        return None
    if ARGS.sweep:
        key = "tail" if S.tail else f"L{w.level}"
        if prof_frames.get(key, 0) < ARGS.sweep and not w.resting:
            return key
    if ARGS.profile_levels:
        key = "tail" if S.tail else f"L{w.level}"
        if prof_frames.get(key, 0) < ARGS.profile_levels and not w.resting:
            return key
    if PROFILE_WAVES and w.wave_id in PROFILE_WAVES and not w.resting:
        key = "W:" + w.wave_id
        if prof_frames.get(key, 0) < ARGS.profile_frames:
            return key
    return None


def set_profile(key):
    cur = prof[0]
    if cur is not None and cur[0] == key:
        return
    if cur is not None:
        cur[1].disable()
    if key is None:
        prof[0] = None
        return
    p = prof_stats.setdefault(key, cProfile.Profile())
    p.enable()
    prof[0] = (key, p)


# ---- frame loop patches ----------------------------------------------------------------------
real_draw = fr._draw
real_run_ticks = fr._run_ticks
window_ref = [None]


def canary():
    c = real_perf()
    x = 0
    for i in range(3000):
        x += i * i
    return (real_perf() - c) * 1000


def spy_run_ticks(*a, **k):
    flow = a[0]
    if ARGS.profile_levels or PROFILE_WAVES or ARGS.sweep:
        set_profile(want_profile_key(flow))
    PARTS.clear()
    t0 = real_perf()
    r = real_run_ticks(*a, **k)
    TICK[0] = (real_perf() - t0) * 1000
    return r


def profiling():
    return prof[0] is not None


def spy_draw(window, field, backdrop, hud, look, background, bt, ship_look, flow, *a, **k):
    window_ref[0] = window
    flow_ref[0] = flow
    if (ARGS.nodraw_until_profile and not profiling()) or (
        ARGS.nodraw_tail_minutes and (not S.tail or frame_no[0] - S.tail_start_frame < ARGS.nodraw_tail_minutes * 3600)
    ):
        DRAW[0] = 0.0
        return
    t0 = real_perf()
    real_draw(window, field, backdrop, hud, look, background, bt, ship_look, flow, *a, **k)
    DRAW[0] = (real_perf() - t0) * 1000
    maybe_shot(window, flow)


fr._run_ticks = spy_run_ticks
fr._draw = spy_draw

last_flip = [None]
real_flip = pygame.display.flip


def maybe_shot(window, flow):
    if not ARGS.shots or flow.screen.name != "PLAYING":
        return
    w = flow.run.waves
    if w is None:
        return
    d = Path(ARGS.shots)
    d.mkdir(parents=True, exist_ok=True)
    n = len(flow.run.drifters)
    if w.level == 4 and not w.resting and n > S.l4_max:
        S.l4_max = n
        pygame.image.save(window, str(d / "1_level4_peak.png"))
        S.shots.add("l4")
    if w.level == 8 and "l8" not in S.shots and 7 in LEVEL_FRAME0:
        S.l8_shot_at = S.l8_shot_at or frame_no[0] + 25
    if "l8" not in S.shots and S.l8_shot_at is not None and frame_no[0] >= S.l8_shot_at:
        pygame.image.save(window, str(d / "2_level8_start.png"))
        S.shots.add("l8")
    if S.tail and "tail1" not in S.shots and not w.resting and frame_no[0] - (S.tail_start_frame or 0) > 120:
        pygame.image.save(window, str(d / "3_first_endless_wave.png"))
        S.shots.add("tail1")
    if S.tail and "tail10" not in S.shots and frame_no[0] - S.tail_start_frame > 10 * 3600 and not w.resting:
        pygame.image.save(window, str(d / "4_endless_plus_10min.png"))
        S.shots.add("tail10")
    if (
        S.tail
        and "tail10b" not in S.shots
        and frame_no[0] - S.tail_start_frame > 10 * 3600
        and n >= 8
        and not w.resting
    ):
        pygame.image.save(window, str(d / "4b_endless_plus_10min_busy.png"))
        S.shots.add("tail10b")


# ---- samples ---------------------------------------------------------------------------------
samples = []
WATCH = []  # (label, container)


def rss_kb():
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * (os.sysconf("SC_PAGE_SIZE") // 1024)


def build_watch():
    """Find every cache-like container owned by game modules, once, right before the freeze."""
    seen = set()
    for name, mod in list(sys.modules.items()):
        if not name.startswith(("ui", "app", "core")) or mod is None:
            continue
        for attr, obj in list(vars(mod).items()):
            if hasattr(obj, "cache_info") and hasattr(obj, "cache_clear"):
                WATCH.append((f"lru:{name}.{attr}", obj))
            elif isinstance(obj, (dict, list, set)) and id(obj) not in seen and not attr.startswith("__"):
                seen.add(id(obj))
                WATCH.append((f"mod:{name}.{attr}", obj))
    for o in gc.get_objects():
        m = getattr(type(o), "__module__", "") or ""
        if m.startswith(("ui", "app", "core")) and not isinstance(o, (type, types.FunctionType)):
            d = getattr(o, "__dict__", None)
            items = list(d.items()) if isinstance(d, dict) else []
            for slot in (
                getattr(type(o), "__slots__", ()) if isinstance(getattr(type(o), "__slots__", ()), tuple) else ()
            ):
                if hasattr(o, slot):
                    items.append((slot, getattr(o, slot)))
            for attr, v in items:
                if isinstance(v, (dict, list, set)) and id(v) not in seen:
                    seen.add(id(v))
                    WATCH.append((f"obj:{type(o).__name__}.{attr}", v))


def census():
    out = {}
    for label, c in WATCH:
        n = c.cache_info().currsize if hasattr(c, "cache_info") else len(c)
        out[label] = n
    return out


def sample(tag=""):
    flow = flow_ref[0]
    w = flow.run.waves if flow else None
    s = {
        "frame": frame_no[0],
        "tag": tag,
        "level": w.level if w else 0,
        "tail": S.tail,
        "rss_kb": rss_kb(),
        "blocks": sys.getallocatedblocks(),
        "gc_count": gc.get_count(),
        "arrays_kb": sum(a.itemsize * len(a) for a in A.values()) // 1024,
        "census": census(),
        "hits": hits[0],
    }
    if tag or frame_no[0] % 3000 == 0:
        s["gc_objects"] = len(gc.get_objects())
    samples.append(s)


real_freeze = fr._freeze_startup_heap


def freeze_with_watch():
    gc.collect()
    build_watch()
    real_freeze()


fr._freeze_startup_heap = freeze_with_watch

if ARGS.tracemalloc:
    import tracemalloc

    tracemalloc.start(8)
    snaps = {}


def tm_snap(name):
    if ARGS.tracemalloc:
        gc.collect()
        snaps[name] = tracemalloc.take_snapshot()


class Done(Exception):
    pass


import signal

STOP = [False]
signal.signal(signal.SIGUSR1, lambda *_: STOP.__setitem__(0, True))


def save_arrays(suffix=""):
    if A:
        import numpy as np

        np.savez_compressed(
            OUT / f"soak_{ARGS.label}{suffix}.npz", **{k: np.frombuffer(v, dtype=v.typecode) for k, v in A.items()}
        )
        (OUT / f"soak_{ARGS.label}{suffix}_meta.json").write_text(
            json.dumps(
                {
                    "meta": {
                        "wave_ids": WAVE_IDS,
                        "level_frame0": LEVEL_FRAME0,
                        "tail_start_frame": S.tail_start_frame,
                        "type_names": TYPE_NAMES,
                        "part_names": PART_NAMES,
                        "frames": frame_no[0],
                        "hits": hits[0],
                        "l8_slots": L8_SLOTS,
                        "label": ARGS.label,
                        "args": vars(ARGS),
                    },
                    "samples": samples,
                    "gc": gc_events,
                }
            )
        )


def spy_flip():
    real_flip()
    now = wall_clock()
    wall = (now - last_flip[0]) * 1000 if last_flip[0] is not None else 0.0
    last_flip[0] = now
    frame_no[0] += 1
    n = frame_no[0]
    flow = flow_ref[0]
    run = flow.run if flow else None
    w = run.waves if run else None
    playing = flow is not None and flow.screen.name == "PLAYING" and w is not None
    if playing:
        if w.level not in LEVEL_FRAME0:
            LEVEL_FRAME0[w.level] = n
            if w.level in (1, 8) and ARGS.tracemalloc:
                tm_snap(f"L{w.level}")
            sample(f"level{w.level}_start")
        started = (not w.resting) and (S.prev_resting or w.wave_id != S.prev_wave)
        if started:
            S.wave_seq += 1
            if w.level == LEVEL_COUNT:
                S.l8_wave_count += 1
                if S.l8_wave_count > L8_SLOTS and not S.tail:
                    S.tail = True
                    S.tail_start_frame = n
                    sample("tail_start")
                    if ARGS.tracemalloc:
                        tm_snap("tail_start")
        S.prev_resting = w.resting
        S.prev_wave = w.wave_id
    if not ARGS.lean and flow is not None:
        A["tick"].append(TICK[0])
        A["draw"].append(DRAW[0])
        A["wall"].append(wall)
        A["gc"].append(GC_MS[0])
        A["canary"].append(canary())
        for k in PART_NAMES:
            A["p:" + k].append(PARTS.get(k, 0.0))
        ds = run.drifters
        A["level"].append(w.level if w else 0)
        wid = WAVE_IDS.setdefault(w.wave_id if w else "", len(WAVE_IDS))
        A["wave"].append(wid)
        A["seq"].append(S.wave_seq if playing else -1)
        A["nd"].append(len(ds))
        nwarn = sum(1 for d in ds if d.phase.name == "WARNING")
        A["nwarn"].append(nwarn)
        A["nactive"].append(len(ds) - nwarn)
        A["pop"].append(len(run.popups))
        A["ring"].append(len(run.graze_rings))
        A["flags"].append(
            (1 if w and w.resting else 0)
            | (2 if run.level_up is not None else 0)
            | (4 if run.invuln_ticks_left > 0 else 0)
            | (8 if flow.screen.name == "PLAYING" else 0)
        )
        A["tail"].append(1 if S.tail else 0)
        cnt = {}
        for d in ds:
            cnt[d.drifter_type.value] = cnt.get(d.drifter_type.value, 0) + 1
        for t in TYPE_NAMES:
            A["n:" + t].append(cnt.get(t, 0))
    GC_MS[0] = 0.0
    if n % 600 == 0 and n > 10:
        sample()
    if n % 1800 == 0:
        print(
            f"frame {n} level {w.level if w else '-'} tail {S.tail} wave {w.wave_id if w else '-'} "
            f"nd {len(run.drifters) if run else 0} rss {rss_kb() // 1024} MB scr {flow.screen.name if flow else ''} "
            f"rest {w.resting if w else ''} wait {run.waiting if run else ''} lives {run.lives if run else ''} "
            f"slot {w.next_slot if w else ''}",
            flush=True,
        )
    stop = (ARGS.max_frames and n >= ARGS.max_frames) or STOP[0]
    if ARGS.checkpoint and n % ARGS.checkpoint == 0:
        save_arrays("_ckpt")
    if S.tail and n - S.tail_start_frame >= ARGS.tail_minutes * 3600:
        stop = True
    if ARGS.stop_level and w is not None and w.level > ARGS.stop_level:
        S.stop_at = S.stop_at or n + 150
        if n >= S.stop_at:
            stop = True
    if profiling():
        prof_frames[prof[0][0]] = prof_frames.get(prof[0][0], 0) + 1
    if ARGS.sweep and not PENDING and w is not None and not stop:
        cur = "tail" if S.tail else f"L{w.level}"
        if prof_frames.get(cur, 0) >= ARGS.sweep and cur not in SWEPT:
            SWEPT.add(cur)
            order = [f"L{i}" for i in range(1, 9)] + ["tail"]
            nxt = order.index(cur) + 1
            if nxt < len(order):
                PENDING.append(order[nxt][1:] if order[nxt] != "tail" else "tail")
            else:
                stop = True
    if stop:
        raise Done


pygame.display.flip = spy_flip

t_start = wall_clock()
with contextlib.suppress(Done):
    asyncio.run(fr.frame_loop(fr.RunMode.NORMAL))
set_profile(None)
elapsed = wall_clock() - t_start
sample("end")
if ARGS.tracemalloc:
    tm_snap("end")
print(f"done {frame_no[0]} frames in {elapsed:.0f}s, tail_start {S.tail_start_frame}, hits {hits[0]}", flush=True)

lab = ARGS.label
meta = {
    "label": lab,
    "args": vars(ARGS),
    "wave_ids": WAVE_IDS,
    "level_frame0": LEVEL_FRAME0,
    "tail_start_frame": S.tail_start_frame,
    "l8_slots": L8_SLOTS,
    "type_names": TYPE_NAMES,
    "part_names": PART_NAMES,
    "elapsed_s": elapsed,
    "hits": hits[0],
    "frames": frame_no[0],
}
(OUT / f"soak_{lab}_meta.json").write_text(json.dumps({"meta": meta, "samples": samples, "gc": gc_events}))
if A:
    import numpy as np

    np.savez_compressed(OUT / f"soak_{lab}.npz", **{k: np.frombuffer(v, dtype=v.typecode) for k, v in A.items()})
if ARGS.tracemalloc:

    def top(a, b, n=25):
        st = snaps[b].compare_to(snaps[a], "lineno")
        return [(str(s.traceback[0]), s.size_diff, s.count_diff) for s in st[:n]]

    res = {}
    keys = list(snaps)
    for i in range(len(keys) - 1):
        res[f"{keys[i]}->{keys[i + 1]}"] = top(keys[i], keys[i + 1])
    (OUT / f"soak_{lab}_tracemalloc.json").write_text(json.dumps(res, indent=1))
if prof_stats:
    pdir = OUT / f"prof_{lab}"
    pdir.mkdir(exist_ok=True)
    for k, p in prof_stats.items():
        p.dump_stats(str(pdir / (k.replace(":", "_") + ".prof")))
    print("profiles:", {k: prof_frames.get(k) for k in prof_stats})
