"""Stutter probe (scratch only). Patches app.frame from outside; pushes one record per frame to JS.

URL options: audio=0 (no mixer), gc=freeze (gc.freeze after load), auto=0 (no autopilot).
Record: t,interval,sleep,ticks,tick_ms,draw_ms,flip_ms,gc_ms,drifters,cues,screen
"""

import gc
import random
import sys
import time

import platform
import pygame

import app.frame as fr
import core.game_flow as gf
import core.run as cr
from core.ship import Thrust

window = platform.window
query = str(window.location.search)
OPTS = dict(p.split("=", 1) for p in query.lstrip("?").split("&") if "=" in p)
window.eval("window.__probe = []; window.__probe_meta = {}")
window.__probe_meta.opts = query
window.__probe_meta.py = sys.version

if "snap" in OPTS:
    fr.TICK_SNAP_SECONDS = float(OPTS["snap"])

if OPTS.get("nofreeze") == "1":
    fr._freeze_startup_heap = lambda: None

if "cap" in OPTS:
    fr.MAX_TICKS_PER_FRAME = int(OPTS["cap"])

if OPTS.get("lite") == "1":
    import ui.background_view as _bv

    def _plain(surface, art, ticks):
        frames = art.sway
        position = ticks / art.rules.sway_loop_ticks % 1.0 * len(frames)
        f = frames[int(position) % len(frames)]
        f.set_alpha(None)
        surface.blit(f, (0, 0))

    _bv._draw_painting = _plain

if OPTS.get("audio") == "0":
    fr.load_audio = lambda levels: None

_real_step_run = cr.step_run


def _immortal(run, thrust):
    out = _real_step_run(run, thrust)
    if 0 < out.lives < 3:
        out = cr.replace(out, lives=5)
    return out


gf.step_run = _immortal

st = {
    "flow": None,
    "frame": 0,
    "loop_t": None,
    "flip_end": None,
    "ticks": 0,
    "tick_ms": 0.0,
    "draw_ms": 0.0,
    "gc_ms": 0.0,
    "gc_t": 0.0,
    "steer": 0,
    "t0": time.perf_counter(),
    "froze": False,
}
rng = random.Random(7)


def _gc_cb(phase, info):
    if phase == "start":
        st["gc_t"] = time.perf_counter()
    else:
        st["gc_ms"] += (time.perf_counter() - st["gc_t"]) * 1000


gc.callbacks.append(_gc_cb)

_real_read = fr._read_events


def _read(*a, **k):
    now = time.perf_counter()
    st["sleep"] = (now - st["flip_end"]) * 1000 if st["flip_end"] else 0.0
    st["interval"] = (now - st["loop_t"]) * 1000 if st["loop_t"] else 0.0
    st["loop_t"] = now
    return _real_read(*a, **k)


fr._read_events = _read

from app.tuning import load_tuning as _lt
from app.waves import load_wave_book as _lwb

L8_SLOTS = len(_lwb(_lt()).level_slots(8))
_real_step_flow = fr.step_flow
_JUMPED = [False]


def _jump(flow):
    """URL jump=4 | 8 | tail: start the run's waves at that level (tail = past Level 8's slots)."""
    from dataclasses import replace as _rep

    j = OPTS.get("jump")
    if not j or _JUMPED[0] or flow.screen.name != "PLAYING" or flow.run.waves is None:
        return flow
    _JUMPED[0] = True
    level = 8 if j == "tail" else int(j)
    w = flow.run.waves
    slot = len(w.book.level_slots(level)) if j == "tail" else 0
    if j == "tail":
        _WS["l8"] = L8_SLOTS
    nw = _rep(w, level=level, next_slot=slot, resting=True, rest_ticks_left=30)
    return _rep(flow, run=_rep(flow.run, waves=nw))


def _step_flow(*a, **k):
    st["ticks"] += 1
    if OPTS.get("jump"):
        a = (_jump(a[0]),) + tuple(a[1:])
    return _real_step_flow(*a, **k)


fr.step_flow = _step_flow

_real_run_ticks = fr._run_ticks


def _run_ticks(*a, **k):
    t = time.perf_counter()
    r = _real_run_ticks(*a, **k)
    st["tick_ms"] = (time.perf_counter() - t) * 1000
    return r


fr._run_ticks = _run_ticks

_real_draw = fr._draw


def _draw(*a, **k):
    st["flow"] = a[8]
    t = time.perf_counter()
    _real_draw(*a, **k)
    st["draw_ms"] = (time.perf_counter() - t) * 1000


fr._draw = _draw

_real_held = fr._held_keys


def _held():
    if OPTS.get("auto") == "0":
        return _real_held()
    flow = st["flow"]
    n = st["frame"]
    if flow is None or flow.screen.name != "PLAYING":
        return Thrust(), n % 20 < 3
    if n % 90 == 0:
        st["steer"] = rng.choice([-1, 0, 1])
    ship = flow.run.ship
    up = ship.y > 330 or (ship.y > 250 and n % 4 != 0)
    if ship.x < 120:
        st["steer"] = 1
    elif ship.x > 520:
        st["steer"] = -1
    return Thrust(up=up, left=st["steer"] == -1, right=st["steer"] == 1), False


fr._held_keys = _held

PARTS = {}


def _timed(name, fn):
    def w(*a, **k):
        c = time.perf_counter()
        r = fn(*a, **k)
        PARTS[name] = PARTS.get(name, 0.0) + (time.perf_counter() - c) * 1000
        return r

    return w


import ui.hud as _hud
import ui.level_up_view as _luv
import ui.mute_icon as _mi

fr.draw_background = _timed("bg", fr.draw_background)
fr.draw_starfield = _timed("star", fr.draw_starfield)
fr.render_drifter = _timed("drift", fr.render_drifter)
fr.draw_ship = _timed("ship", fr.draw_ship)
fr.draw_points_popup = _timed("pop", fr.draw_points_popup)
fr.draw_graze_ring = _timed("ring", fr.draw_graze_ring)
_hud.HudView.draw = _timed("hud", _hud.HudView.draw)
_luv.LevelUpView.draw_banner = _timed("lub", _luv.LevelUpView.draw_banner)
_luv.LevelUpView.draw_flight = _timed("luf", _luv.LevelUpView.draw_flight)
_mi.MuteIconView.draw = _timed("mute", _mi.MuteIconView.draw)

_real_flip = pygame.display.flip


def _canary():
    c = time.perf_counter()
    x = 0
    for i in range(3000):
        x += i * i
    return (time.perf_counter() - c) * 1000


_WS = {"prev_rest": True, "prev_wave": None, "seq": 0, "l8": 0, "tail": 0}


def _wave_ctx(flow):
    """level|wave id|seq|resting|tail, tracked per flip (endless tail = after Level 8's slots)."""
    if flow is None or flow.run.waves is None or flow.screen.name != "PLAYING":
        return "0|-|0|0|0"
    w = flow.run.waves
    if not w.resting and (_WS["prev_rest"] or w.wave_id != _WS["prev_wave"]):
        _WS["seq"] += 1
        if w.level == 8:
            _WS["l8"] += 1
            if _WS["l8"] > L8_SLOTS:
                _WS["tail"] = 1
    _WS["prev_rest"] = w.resting
    _WS["prev_wave"] = w.wave_id
    return f"{w.level}|{w.wave_id}|{_WS['seq']}|{int(w.resting)}|{_WS['tail']}"


def _flip():
    can = _canary()
    t = time.perf_counter()
    _real_flip()
    end = time.perf_counter()
    st["frame"] += 1
    flow = st["flow"]
    nd = len(flow.run.drifters) if flow is not None else 0
    cues = len(flow.run.sound_cues) if flow is not None else 0
    scr = flow.screen.name[:2] if flow is not None else "--"
    if OPTS.get("gc") == "freeze" and not st["froze"] and st["frame"] == 120:
        gc.collect()
        gc.freeze()
        st["froze"] = True
    if OPTS.get("rec") != "0":
        window.__probe.push(
            f"{(t - st['t0']) * 1000:.1f},{st.get('interval', 0):.2f},{st.get('sleep', 0):.2f},"
            f"{st['ticks']},{st['tick_ms']:.2f},{st['draw_ms']:.2f},{(end - t) * 1000:.2f},"
            f"{st['gc_ms']:.2f},{nd},{cues},{scr},{can:.3f},"
            + ";".join(f"{k}={v:.1f}" for k, v in PARTS.items() if v >= 0.05)
            + f",{int(flow is not None and flow.run.level_up is not None)}"
            + f",{_wave_ctx(flow)}"
        )
    st["ticks"] = 0
    st["gc_ms"] = 0.0
    PARTS.clear()
    st["flip_end"] = time.perf_counter()


pygame.display.flip = _flip
