"""Scripted rehit-cooldown and graze scenarios on core.run.step_run (no waves, hand-placed drifters)."""

from dataclasses import replace

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT, th
from scenarios import Suite
from simkit import drifter_type
from core.collision import Circle, hitboxes_overlap
from core.drifters.base import GrazeState, Phase
from core.drifters.spawner import Placement, spawn_drifter
from core.run import start_run, step_run
from core.ship import SPAWN_X, SPAWN_Y, ship_hitbox

UP = th(u=1)
METEORITE = drifter_type("meteorite")
COIN = drifter_type("coin")
SUITE = Suite("b2_rehit_graze.txt")
case = SUITE.case


def base_run():
    return start_run(waves=None, graze_rules=KIT.graze_rules, last_life_rules=KIT.last_life_rules)


def hazard(x, y, r=1000.0, dtype=METEORITE, variant="small", **kw):
    d = spawn_drifter(Placement(dtype, x=x, y=y, variant=variant), 1, KIT.tuning)
    return replace(d, x=x, y=y, speed=0.0, phase=Phase.ACTIVE, has_entered=True, hitbox=(Circle(0, 0, r),), **kw)


def add(run, *ds):
    n = run.next_uid
    ds = [replace(d, uid=n + i) for i, d in enumerate(ds)]
    return replace(run, drifters=run.drifters + tuple(ds), next_uid=n + len(ds))


def go(run, n, thrust=UP):
    for _ in range(n):
        run = step_run(run, thrust)
    return run


@case("rehit: A cannot re-hit for exactly rehit_cooldown ticks; hits again at N+181; B hits at N+61")
def _():
    m = []
    cd = 180
    run = add(base_run(), hazard(320, 240, rehit_cooldown_ticks=cd))
    # prime: held up so no fall; first step hits
    lives_log = []
    r = run
    for k in range(1, 400):
        r2 = step_run(r, UP)
        if r2.lives != r.lives:
            lives_log.append(k)
        r = r2
        if r.lives <= 1:
            break
    if lives_log[:2] != [1, 1 + cd + 1]:
        m.append(f"A hit ticks {lives_log[:3]} expected [1, {cd + 2}] (cooldown {cd} ticks)")
    # invulnerability length with a second hazard B (cooldown irrelevant)
    run = add(base_run(), hazard(320, 240, r=1000, rehit_cooldown_ticks=cd))
    run = step_run(run, UP)  # tick N: A hits
    if run.lives != 4 or run.invuln_ticks_left != 60:
        m.append(f"after hit lives={run.lives} invuln={run.invuln_ticks_left}")
    run = add(run, hazard(320, 240, r=1000, rehit_cooldown_ticks=cd))  # B joins, overlapping
    t = 0
    while run.lives == 4 and t < 200:
        run = step_run(run, UP)
        t += 1
    if t != 61:
        m.append(f"B hit on step {t} after A's hit (expected 61: 60 protected ticks)")
    # two hazards in the same tick: one life, both cooldowns
    run = add(base_run(), hazard(320, 240), hazard(330, 240))
    run = step_run(run, UP)
    if run.lives != 4:
        m.append(f"two touching: lives {run.lives}")
    if [d.rehit_ticks_left for d in run.drifters] != [180, 180]:
        m.append(f"cooldowns {[d.rehit_ticks_left for d in run.drifters]}")
    # cooldown does not scale with level: level 8 spawn
    d8 = spawn_drifter(Placement(METEORITE, x=100, variant="small"), 8, KIT.tuning)
    if d8.rehit_cooldown_ticks != 180:
        m.append(f"cooldown at L8 = {d8.rehit_cooldown_ticks}")
    # during cooldown brightness dim
    if run.drifters[0].brightness() != run.drifters[0].rehit_dim:
        m.append("not dimmed in cooldown")
    # no hit when protected, and still protected cooldown not started
    run = start_run(waves=None, graze_rules=KIT.graze_rules, last_life_rules=KIT.last_life_rules)
    run = add(replace(run, invuln_ticks_left=10), hazard(320, 240))
    run = go(run, 5)
    if run.lives != 5 or run.drifters[0].rehit_ticks_left != 0:
        m.append("protected ship got hit / cooldown started")
    return m


@case("hit while waiting after invulnerability (rule 2.7/1): standing ship can be hit")
def _():
    m = []
    run = replace(base_run(), waiting=True, invuln_ticks_left=0)
    run = add(run, hazard(320, 240))
    run = step_run(run, th())
    if run.lives != 4:
        m.append(f"waiting unprotected ship not hit: lives={run.lives}")
    return m


def pos_run(ship_xy, invuln=0, waiting=False):
    run = base_run()
    sh = replace(run.ship, x=ship_xy[0], y=ship_xy[1], vx=0.0, vy=0.0)
    return replace(run, ship=sh, invuln_ticks_left=invuln, waiting=waiting)


def with_ship(run, xy):
    return replace(run, ship=replace(run.ship, x=xy[0], y=xy[1], vx=0.0, vy=0.0))


def shiphb_dist_ok():
    pass


def sweep(run, path, thrust=UP):
    """Place the ship at each point of `path` before each tick (physics moves it < 1px per tick)."""
    log = []
    for xy in path:
        run = step_run(with_ship(run, xy), thrust)
        log.append((run.grazes, run.lives, run.drifters[0].graze_state if run.drifters else None))
    return run, log


def in_out_path(cx=320, cy=240, start=-100, near=-4, steps=5):
    pass


@case("graze: pays once on exit; not again on re-entry; popup/score/cue")
def _():
    m = []
    d = hazard(320, 100, r=20)
    run = add(pos_run((320, 300)), d)  # ship far below

    # hitbox ship box ~ 32 tall: ship center at y=100+20+16+8 -> within zone 14 of the circle, not touching
    # find y distances by oracle on the code itself
    def zone_state(y):
        sh = ship_hitbox(replace(run.ship, x=320, y=y))
        dd = run.drifters[0]
        from core.collision import grow_hitbox

        return hitboxes_overlap(dd.current_hitbox(), sh), hitboxes_overlap(grow_hitbox(dd.current_hitbox(), 14), sh)

    ys = {y: zone_state(y) for y in range(100, 400, 1)}
    inzone_ys = [y for y, (t, z) in ys.items() if z and not t]
    zone_y = inzone_ys[0]
    far_y = max(y for y, (t, z) in ys.items() if not z)
    path = [(320, far_y)] * 3 + [(320, zone_y)] * 5 + [(320, far_y)] * 3
    run2, log = sweep(run, path, thrust=th())
    if run2.grazes != 1:
        m.append(f"first in/out grazes={run2.grazes} log={log}")
    if run2.score != run2.scroll.meters + 25:
        m.append(f"score {run2.score} meters {run2.scroll.meters}")
    # re-enter and exit
    run3, log = sweep(run2, path, thrust=th())
    if run3.grazes != 1:
        m.append(f"re-entry grazes={run3.grazes}")
    # popup & ring exist on the pay tick
    r = run
    for i, xy in enumerate(path):
        r = step_run(with_ship(r, xy), th())
        if i == len(path) - 3:
            if len(r.graze_rings) != 1:
                m.append(f"ring count at pay tick {len(r.graze_rings)}")
            if not any(p for p in r.popups):
                m.append("no popup at pay tick")
    # hovering in zone for a long time then leaving still pays once
    path2 = [(320, far_y)] * 2 + [(320, zone_y)] * 300 + [(320, far_y)] * 2
    run4, _ = sweep(run, path2, thrust=th())
    if run4.grazes != 1:
        m.append(f"hover graze={run4.grazes}")
    return m


@case(
    "graze: not paid when exit happens while invulnerable; pays after protection ends; enters protected leaves unprotected pays"
)
def _():
    m = []
    d = hazard(320, 100, r=20)
    base = add(pos_run((320, 300), invuln=0), d)
    from core.collision import grow_hitbox

    def st(y):
        sh = ship_hitbox(replace(base.ship, x=320, y=y))
        dd = base.drifters[0]
        return hitboxes_overlap(dd.current_hitbox(), sh), hitboxes_overlap(grow_hitbox(dd.current_hitbox(), 14), sh)

    zone_y = next(y for y in range(100, 400) if st(y)[1] and not st(y)[0])
    far_y = max(y for y in range(100, 400) if not st(y)[1])
    # exit while invulnerable
    run = replace(base, invuln_ticks_left=30)
    run, log = sweep(run, [(320, far_y)] * 2 + [(320, zone_y)] * 3 + [(320, far_y)] * 3, th())
    if run.grazes != 0:
        m.append(f"paid while invulnerable: {run.grazes}")
    if run.drifters[0].graze_state != GrazeState.OUTSIDE:
        m.append(f"state after protected exit {run.drifters[0].graze_state}")
    # protected enter, unprotected exit: pays
    run = replace(base, invuln_ticks_left=4)
    run, log = sweep(run, [(320, far_y)] * 1 + [(320, zone_y)] * 8 + [(320, far_y)] * 2, th())
    if run.grazes != 1:
        m.append(f"enter protected exit unprotected grazes={run.grazes} log={log}")
    # then re-enter after unprotected exit: no more
    # exit tick exactly when protection ends: protected judged by state going into the tick
    for inv in range(1, 12):
        run = replace(base, invuln_ticks_left=inv)
        run, log = sweep(run, [(320, zone_y)] * 5 + [(320, far_y)] * 2 + [(320, zone_y)] * 3 + [(320, far_y)] * 2, th())
        # invuln = inv -> exit at tick 6: protected until tick `inv`; inv<6 -> pays first exit
        exp = 1 if inv < 11 else 0  # first exit at tick 6, second at tick 11, protected while inv >= tick
        if run.grazes != exp:
            m.append(f"inv={inv} grazes={run.grazes} (expected 1)")
    return m


@case("graze: not paid in respawn wait (even after invulnerability ended)")
def _():
    m = []
    d = hazard(320, 100, r=20)
    from core.collision import grow_hitbox

    run = add(pos_run((320, 240), invuln=0, waiting=True), d)

    # drifter moves instead of ship: slide hazard from in-zone to far
    def st(dy):
        sh = ship_hitbox(run.ship)
        dd = replace(run.drifters[0], y=dy)
        return hitboxes_overlap(dd.current_hitbox(), sh), hitboxes_overlap(grow_hitbox(dd.current_hitbox(), 14), sh)

    zone_ys = [y for y in range(-200, 500) if st(y)[1] and not st(y)[0]]
    far = [y for y in range(-200, 500) if not st(y)[1]]
    zone_y = zone_ys[0]
    far_y = min(far, key=lambda y: abs(y - zone_y))
    r = run
    for dy in [far_y] * 2 + [zone_y] * 4 + [far_y] * 3:
        r = replace(r, drifters=(replace(r.drifters[0], y=dy),))
        r = step_run(r, th())
    if r.grazes != 0:
        m.append(f"graze paid in wait: {r.grazes}")
    if not r.waiting:
        m.append("wait ended without press")
    return m


@case("graze: touching (even while invulnerable/in cooldown) spends the graze; hit hazard pays none")
def _():
    m = []
    from core.collision import grow_hitbox

    d = hazard(320, 100, r=20)
    base = add(pos_run((320, 300)), d)

    def st(y):
        sh = ship_hitbox(replace(base.ship, x=320, y=y))
        dd = base.drifters[0]
        return hitboxes_overlap(dd.current_hitbox(), sh), hitboxes_overlap(grow_hitbox(dd.current_hitbox(), 14), sh)

    touch_y = min(y for y in range(400) if st(y)[0])
    far_y = max(y for y in range(100, 400) if not st(y)[1])
    # touch while invulnerable then leave unprotected -> no graze
    run = replace(base, invuln_ticks_left=3)
    run, _log = sweep(run, [(320, far_y)] + [(320, touch_y + 6)] * 1 + [(320, far_y)] * 3, th())
    if run.grazes != 0:
        m.append(f"graze after touching while protected: {run.grazes}")
    # real hit then leave and come back after cooldown: no graze
    run = replace(base)
    run, _log = sweep(run, [(320, far_y)] + [(320, touch_y + 6)] + [(320, far_y)] * 3, th())
    if run.grazes != 0 or run.lives != 4:
        m.append(f"hit hazard paid graze or no hit: grazes={run.grazes} lives={run.lives}")
    return m


@case("graze: hazard leaves screen with ship in zone pays (not touched)")
def _():
    m = []
    run = pos_run((620, 240))
    run = replace(run, ship=replace(run.ship, x=620.0))
    sh = ship_hitbox(run.ship)
    d0 = replace(hazard(620, 240, r=8), width=10, height=10)
    cand_on = cand_off = None
    for dy in range(150, 330, 2):
        on = [
            dx
            for dx in range(580, 700)
            if (
                lambda dd: (
                    (not dd.is_off_screen())
                    and hitboxes_overlap(dd.graze_zone(), sh)
                    and not hitboxes_overlap(dd.current_hitbox(), sh)
                )
            )(replace(d0, x=float(dx), y=float(dy)))
        ]
        off = [
            dx
            for dx in range(580, 700)
            if (
                lambda dd: (
                    dd.is_off_screen()
                    and hitboxes_overlap(dd.graze_zone(), sh)
                    and not hitboxes_overlap(dd.current_hitbox(), sh)
                )
            )(replace(d0, x=float(dx), y=float(dy)))
        ]
        if on and off:
            cand_on, cand_off = (on[-1], dy), (off[0], dy)
            break
    if cand_off is None:
        return ["INFO: could not build off-screen-in-zone geometry"]
    r = add(run, replace(d0, x=float(cand_on[0]), y=float(cand_on[1])))
    r = step_run(with_ship(r, (620, 240)), th())
    if r.drifters[0].graze_state != GrazeState.INSIDE:
        m.append(f"not INSIDE: {r.drifters[0].graze_state}")
    r = replace(r, drifters=(replace(r.drifters[0], x=float(cand_off[0]), y=float(cand_off[1])),))
    r = step_run(with_ship(r, (620, 240)), th())
    if r.grazes != 1:
        m.append(
            f"off-screen exit with ship in zone paid {r.grazes} (state {r.drifters[0].graze_state if r.drifters else 'dropped'})"
        )
    return m


@case("coin / island: no graze, collect pays points; overlapping coin collected even while invulnerable")
def _():
    m = []
    run = pos_run((SPAWN_X, SPAWN_Y), invuln=20)
    c = spawn_drifter(Placement(COIN, x=SPAWN_X, y=SPAWN_Y, variant="common"), 1, KIT.tuning)
    c = replace(c, x=SPAWN_X, y=SPAWN_Y)
    run = add(run, c)
    r = step_run(run, UP)
    if r.coin_points != 50:
        m.append(f"coin points {r.coin_points}")
    if r.grazes != 0:
        m.append("graze from coin")
    return m


if __name__ == "__main__":
    SUITE.main(__doc__)
