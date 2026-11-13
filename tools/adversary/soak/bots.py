"""Bot policies. Each is a callable bot(run) -> Thrust, with its own random.Random."""

from __future__ import annotations

import math
import random

import paths  # noqa: F401  (puts game/ on sys.path)
from core.drifters.base import Phase, TouchEffect
from core.ship import SHIP_H, SHIP_W, SPAWN_X, Thrust
from core.world import SCREEN_W, TOP_LINE_Y

TOP_EDGE = TOP_LINE_Y + SHIP_H // 2  # ship center y when on the top line
CENTER_X = SCREEN_W / 2


def T(u=False, d=False, l=False, r=False):
    return Thrust(up=u, down=d, left=l, right=r)


def islands(run):
    return [d for d in run.drifters if d.effect_on_touch() is TouchEffect.BLOCK and d.phase is Phase.ACTIVE]


def hazards(run):
    return [
        d
        for d in run.drifters
        if d.phase is Phase.ACTIVE and d.effect_on_touch() is TouchEffect.HIT and d.may_hit_ship()
    ]


def hold_y(ship, target, band=0):
    """True when thrust-up is wanted to hold height `target` (center y)."""
    return ship.y + 9.0 * ship.vy > target + band


class Idle:
    name = "idle"

    def __init__(self, seed):
        pass

    def __call__(self, run):
        return T()


class Sticky:
    name = "sticky"

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.left = 0
        self.cur = T()

    def __call__(self, run):
        if self.left <= 0:
            m = self.rng.randrange(16)
            self.cur = T(bool(m & 1), bool(m & 2), bool(m & 4), bool(m & 8))
            self.left = self.rng.randint(5, 60)
        self.left -= 1
        return self.cur


class Hover:
    name = "hover"

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.tx = SPAWN_X
        self.left = 0
        self.ty = 300.0

    def __call__(self, run):
        s = run.ship
        if self.left <= 0:
            self.tx = self.rng.uniform(60, 580)
            self.ty = self.rng.uniform(200, 380)
            self.left = self.rng.randint(60, 240)
        self.left -= 1
        l = r = False
        if s.x < 50:
            r = True
        elif s.x > 590:
            l = True
        else:
            dx = self.tx - s.x - 12 * s.vx
            l, r = dx < -8, dx > 8
        return T(u=hold_y(s, self.ty), l=l, r=r)


class WallHug:
    def __init__(self, seed, side):
        self.rng = random.Random(seed)
        self.side = side
        self.name = f"wall_{side}"

    def __call__(self, run):
        s = run.ship
        return T(
            u=hold_y(s, 300 + 40 * math.sin(run.scroll.ticks / 90.0)), l=self.side == "left", r=self.side == "right"
        )


class TopHug:
    name = "top_hug"

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.left = 0
        self.cur = (False, False)

    def __call__(self, run):
        if self.left <= 0:
            self.cur = self.rng.choice([(False, False), (True, False), (False, True), (False, False)])
            self.left = self.rng.randint(10, 120)
        self.left -= 1
        return T(u=True, l=self.cur[0], r=self.cur[1])


class FloorSkim:
    name = "floor_skim"

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.left = 0
        self.cur = (False, False)
        self.target = 440.0

    def __call__(self, run):
        if self.left <= 0:
            self.cur = self.rng.choice([(False, False), (True, False), (False, True)])
            self.left = self.rng.randint(15, 100)
            self.target = self.rng.uniform(425, 470)  # includes dipping to the floor line
        self.left -= 1
        s = run.ship
        return T(u=hold_y(s, self.target), l=self.cur[0], r=self.cur[1])


class IslandSeeker:
    name = "island_seeker"

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.mode = "center"
        self.target_uid = None
        self.fallback = Hover(seed + 1)
        self.left = 0

    def _go(self, s, tx, ty, push_into=None):
        dx = tx - s.x - 6 * s.vx
        l, r = dx < -4, dx > 4
        u = s.y + 7 * s.vy > ty + 2
        d = s.y + 7 * s.vy < ty - 12
        return T(u=u, d=d, l=l, r=r)

    def __call__(self, run):
        isl = islands(run)
        s = run.ship
        if not isl:
            self.target_uid = None
            return self.fallback(run)
        cand = [d for d in isl if d.y - d.height / 2 < 470]
        if not cand:
            return self.fallback(run)
        if self.target_uid is None or all(d.uid != self.target_uid for d in cand) or self.left <= 0:
            cand.sort(key=lambda d: math.hypot(d.x - s.x, d.y - s.y))
            pick = cand[0] if self.rng.random() < 0.7 else self.rng.choice(cand)
            self.target_uid = pick.uid
            self.mode = self.rng.choice(["center", "center", "top_line", "wall", "under", "side"])
            self.left = self.rng.randint(120, 400)
        self.left -= 1
        d = next(x for x in cand if x.uid == self.target_uid)
        if self.mode == "center":
            return self._go(s, d.x, d.y)
        if self.mode == "top_line":
            # park at the top line under the island's path, then press up (island descends onto the ship)
            if s.y > TOP_EDGE + 6 or abs(s.x - d.x) > 12:
                if abs(s.x - d.x) > 12:
                    return self._go(s, d.x, max(TOP_EDGE + 40, min(s.y, 300)))
                return T(u=True, l=False, r=False)
            return T(u=True, l=self.rng.random() < 0.2, r=self.rng.random() < 0.2)
        if self.mode == "wall":
            wall_x = SHIP_W // 2 if d.x < CENTER_X else SCREEN_W - SHIP_W // 2
            if abs(s.x - wall_x) > 10 and abs(s.x - d.x) > d.width / 2 + 40:
                return self._go(s, wall_x, d.y)
            return T(u=s.y > d.y, d=s.y < d.y - 10, l=wall_x < CENTER_X, r=wall_x > CENTER_X)
        if self.mode == "under":
            # sit under the island and push up into it
            return (
                self._go(s, d.x, d.y + d.height / 2 + 40)
                if s.y < d.y + d.height / 2 + 10
                else T(u=True, l=s.x > d.x + 6, r=s.x < d.x - 6)
            )
        # side: slide along the island flank pushing in
        side = -1 if s.x < d.x else 1
        return T(u=hold_y(s, d.y), l=side > 0, r=side < 0)


class HazardSeeker:
    name = "hazard_seeker"

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.fallback = Hover(seed + 7)

    def __call__(self, run):
        hz = hazards(run)
        s = run.ship
        hz = [d for d in hz if -50 < d.y < 520 and -50 < d.x < 700]
        if not hz:
            return self.fallback(run)
        d = min(hz, key=lambda d: math.hypot(d.x - s.x, d.y - s.y))
        dx = d.x - s.x - 5 * (s.vx)
        dy = d.y - s.y - 5 * (s.vy)
        return T(u=dy < -6 or (abs(dy) < 20 and s.vy > 1.0), d=dy > 6 and s.vy < 3.5, l=dx < -4, r=dx > 4)


_BOTS = {
    "idle": lambda seed: Idle(seed),
    "sticky": lambda seed: Sticky(seed),
    "hover": lambda seed: Hover(seed),
    "wall_left": lambda seed: WallHug(seed, "left"),
    "wall_right": lambda seed: WallHug(seed, "right"),
    "top_hug": lambda seed: TopHug(seed),
    "floor_skim": lambda seed: FloorSkim(seed),
    "island_seeker": lambda seed: IslandSeeker(seed),
    "hazard_seeker": lambda seed: HazardSeeker(seed),
}
BOT_NAMES = tuple(_BOTS)  # the nine bots with fixed habits. The planner is separate (planner.py)


def make_bot(name, seed):
    """The bot called `name`, with its own random stream from `seed`."""
    return _BOTS[name](seed)
