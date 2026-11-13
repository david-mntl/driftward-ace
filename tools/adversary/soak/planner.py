"""Lookahead survival bot: plans on the pure step function, plays mortal (or immortal for coverage)."""

from __future__ import annotations

import math

import paths  # noqa: F401  (puts game/ on sys.path)
from core.drifters.base import Phase, TouchEffect
from core.run import add_drifters, step_run
from core.ship import Thrust
from core.world import SCREEN_W
from geom import shape_bbox
from simkit import load_kit
from bots import Hover

ACTIONS = [
    Thrust(up=u, down=d, left=left, right=right)
    for left, right in ((True, False), (False, False), (False, True))
    for u, d in ((True, False), (False, False), (False, True))
]
LOST = -10000.0


def _hz_bbox(d):
    hb = d.current_hitbox()
    if not hb:
        return None
    bbs = [shape_bbox(s) for s in hb]
    return (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs))


def clearance(run, cap=80.0):
    """Smallest gap (px, bbox to bbox) between the ship and any hazard that can hurt, capped."""
    s = run.ship
    sl, st, sr, sb = s.x - 16, s.y - 16, s.x + 16, s.y + 16
    best = cap
    for d in run.drifters:
        if d.phase is not Phase.ACTIVE or d.effect_on_touch() is not TouchEffect.HIT:
            continue
        b = _hz_bbox(d)
        if b is None:
            continue
        dx = max(b[0] - sr, sl - b[2], 0.0)
        dy = max(b[1] - sb, st - b[3], 0.0)
        g = math.hypot(dx, dy)
        if g < best:
            best = g
    return best


def threat_near(run, radius=190.0):
    s = run.ship
    for d in run.drifters:
        if d.effect_on_touch() is not TouchEffect.HIT:
            continue
        if d.phase is Phase.GONE:
            continue
        if abs(d.x - s.x) < radius + d.width / 2 and abs(d.y - s.y) < radius + d.height / 2:
            return True
    return False


def position_value(run):
    s = run.ship
    v = 0.0
    v -= max(0.0, s.y - 390) * 1.5
    v -= max(0.0, 150 - s.y) * 0.4
    v -= max(0.0, 60 - min(s.x, SCREEN_W - s.x)) * 0.5
    v -= max(0.0, abs(s.vy) - 4) * 3
    return v


class Planner:
    name = "planner"

    def __init__(self, seed, hold=8, depth=2, replan=6, immortal=False, topk=2, radius=120.0):
        self.topk = topk
        self.radius = radius
        self.kit = load_kit()
        self.hold = hold
        self.depth = depth
        self.replan = replan
        self.fallback = Hover(seed)
        self.plan_left = 0
        self.cur = Thrust()
        self.immortal = immortal
        self.decisions = 0
        self.fast = 0
        self.refines = 0
        self.candidates: list[dict] = []
        self.escapes_by_refine = 0
        self.sim_ticks = 0
        self.n_lost_first_layer = 0

    # ---- simulation
    def sim(self, run, th, n):
        """Hold `th` for n ticks. Returns (run, ticks_to_loss or None, min_clearance)."""
        tuning = self.kit.tuning
        lives0 = run.lives
        mc = 80.0
        for i in range(n):
            nxt = step_run(run, th)
            nxt = add_drifters(nxt, nxt.wave_spawns_due, tuning)
            self.sim_ticks += 1
            if nxt.lives < lives0:
                return nxt, i + 1, 0.0
            run = nxt
            if run.game_over:
                break
            if i % 2 == 1 or i == n - 1:
                c = clearance(run)
                if c < mc:
                    mc = c
        return run, None, mc

    def search(self, run, hold, depth):
        """Best (value, first_action) over action sequences; value LOST-ish when every path loses a life."""
        best_val = None
        best_first = None
        order = []
        for a in ACTIONS:
            r, lost, mc = self.sim(run, a, hold)
            if lost is not None:
                order.append((LOST + lost, a, None, 0.0))
            else:
                order.append((min(mc, 45.0) * 3 + position_value(r), a, r, mc))
        order.sort(key=lambda x: -x[0])
        expanded = 0
        for val1, a, r, _mc in order:
            if r is not None and depth >= 2:
                if expanded >= self.topk:
                    continue
                expanded += 1
            if r is None:
                if best_val is None or val1 > best_val:
                    best_val, best_first = val1, a
                continue
            if depth <= 1:
                v = val1
            else:
                v, _ = self.search(r, hold, depth - 1)
                v = min(v, val1 + 0.0) if v > LOST / 2 else v
            if best_val is None or v > best_val:
                best_val, best_first = v, a
            if v > 100.0 and depth >= 2:
                break  # comfortable path found: stop expanding
        return best_val, best_first

    def candidate(self, run, first_res):
        s = run.ship
        near = []
        for d in run.drifters:
            if d.effect_on_touch() is not TouchEffect.HIT:
                continue
            b = (
                _hz_bbox(d)
                if d.phase is Phase.ACTIVE
                else (d.x - d.width / 2, d.y - d.height / 2, d.x + d.width / 2, d.y + d.height / 2)
            )
            if b is None:
                continue
            dx = max(b[0] - (s.x + 16), (s.x - 16) - b[2], 0.0)
            dy = max(b[1] - (s.y + 16), (s.y - 16) - b[3], 0.0)
            g = math.hypot(dx, dy)
            if g < 200:
                near.append(
                    (
                        round(g, 1),
                        d.drifter_type.value,
                        d.variant,
                        d.phase.value,
                        round(d.x, 1),
                        round(d.y, 1),
                        d.uid,
                        d.has_entered,
                    )
                )
        near.sort()
        return dict(
            tick=run.scroll.ticks,
            wave=run.waves.wave_id,
            level=run.level,
            lives=run.lives,
            ship=(round(s.x, 1), round(s.y, 1), round(s.vx, 2), round(s.vy, 2)),
            waiting=run.waiting,
            invuln=run.invuln_ticks_left,
            near=near[:8],
            info=first_res,
        )

    def __call__(self, run):
        if self.plan_left > 0:
            self.plan_left -= 1
            return self.cur
        # decision point
        if run.game_over or run.burst is not None:
            return Thrust()
        self.decisions += 1
        if not threat_near(run, self.radius) and not run.waiting:
            self.fast += 1
            self.cur = self.fallback(run)
            self.plan_left = 2
            return self.cur
        val, first = self.search(run, self.hold, self.depth)
        if val is not None and val <= LOST / 2 and run.invuln_ticks_left == 0:
            # every explored 16-tick path loses a life: refine with shorter holds, deeper
            self.refines += 1
            val2, first2 = self.search_dfs(run, 4, 3)
            if val2 is not None:
                self.escapes_by_refine += 1
                first = first2
            elif len(self.candidates) < 80:
                self.candidates.append(self.candidate(run, dict(refine="none escaped", coarse_val=val)))
        elif val is not None and val <= LOST / 2:
            pass  # protected: hits cost nothing yet
        self.cur = first or Thrust()
        self.plan_left = self.replan - 1
        return self.cur

    def search_dfs(self, run, hold, depth):
        """Depth-first search for any action sequence that survives hold*depth ticks. Returns (1.0, first) or (None, None)."""

        def rec(r, d):
            for a in sorted(ACTIONS, key=lambda a: 0):
                r2, lost, _ = self.sim(r, a, hold)
                if lost is not None:
                    continue
                if d <= 1 or rec(r2, d - 1) is not None:
                    return a
            return None

        for a in ACTIONS:
            r2, lost, _ = self.sim(run, a, hold)
            if lost is not None:
                continue
            if depth <= 1 or rec(r2, depth - 1) is not None:
                return 1.0, a
        return None, None

    def report(self):
        return dict(
            decisions=self.decisions,
            fast=self.fast,
            refines=self.refines,
            escapes_by_refine=self.escapes_by_refine,
            candidates=self.candidates,
            sim_ticks=self.sim_ticks,
        )
