"""Per-tick invariant oracle for the soak harness. Reads rules from the GDD, recomputes outcomes itself."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

import paths  # noqa: F401  (puts game/ on sys.path)
from core.drifters.base import Phase, TickContext, TouchEffect
from core.run import gravity_wells, island_ground
from core.scroll import scroll_step_px
from core.ship import NO_GROUND, block_ship, step
from gdd_rules import (
    INVULN_TICKS,
    LEVEL_COUNT,
    LIVES_START,
    SCREEN_H,
    SCREEN_W,
    SCROLL_BASE,
    SCROLL_MULT,
    SCROLL_START_DELAY_TICKS,
    SHIP_HALF,
    SPAWN_X,
    SPAWN_Y,
    TOP_LINE_Y,
)
from geom import hits_ship, island_depth

# Limits of the checks themselves. They are not design numbers; they are how strict or patient a check is.
OVERLAP_EPS = 1e-6  # a hit needs overlap beyond this; touching within it is "ambiguous", not a miss
MAX_SHIP_SPEED = 60  # px per tick: above this the ship's state is broken
FAR_PX = 2000  # a drifter this far from the screen centre has left the world without being removed
ISLAND_DEPTH_TOLERANCE_PX = 0.01  # the ship may sink this far into an island before it is a finding
PUSH_TELEPORT_PX = 14  # an island push-out larger than this in one tick is reported as a teleport
RESPAWN_SEARCH_STEP_PX = 0.25  # resolution of the search for the nearest clear respawn spot
RESPAWN_TOLERANCE_PX = 1.0  # the game's respawn y may differ from the search by this much
RESPAWN_SEARCH_LIMIT_Y = 2000  # the search for a clear spot below the spawn point gives up here
RESPAWN_TIE_PX = 0.3  # up and down spots this close count as equal: the game may take either
STUCK_WINDOW_TICKS = 120  # holding a direction for this long without moving needs an explanation
STUCK_REPORT_GAP_TICKS = 600  # report a stuck ship at most this often
STALL_SLACK_TICKS = 600  # how long past its length a wave may run before it counts as stalled
LEVEL_STUCK_TICKS = 12000  # a level before the last one must end within this
DRIFTER_MAX_AGE_TICKS = 3600  # a drifter alive longer than this is a leak
BANNER_DEDUPE_TICKS = 300  # a level-up banner seen again within this is the same banner
MAX_POPUPS = MAX_RINGS = 200  # more than this in flight is an unbounded collection
MAX_DRIFTERS = 400
FORGET_DEAD_EVERY_TICKS = 600  # how often the birth-tick table drops uids that left
EXAMPLES_KEPT = 3  # examples stored per finding kind
LOG_CAP = 40  # entries kept in the squeeze and jump logs

# `core.run._update_drifters` is wrapped to hand the oracle the drifters as the game updated them this tick.
import core.run as _core_run

CAPTURE: dict = {}
_orig_update = _core_run._update_drifters


def _capturing_update(run, scroll_px):
    out = _orig_update(run, scroll_px)
    CAPTURE["upd"] = out
    CAPTURE["for"] = run
    return out


_core_run._update_drifters = _capturing_update


def _press(thrust, held):
    return any(
        n and not b
        for n, b in zip(
            (thrust.up, thrust.down, thrust.left, thrust.right),
            (held.up, held.down, held.left, held.right),
            strict=True,
        )
    )


def _touching(upd, ship0):
    """The hazards that overlap the ship at `ship0`, and whether any only touches within the tolerance."""
    touching, ambiguous = [], False
    for d in upd:
        if d.phase is Phase.ACTIVE and d.effect_on_touch() is TouchEffect.HIT and d.may_hit_ship():
            hitbox = d.current_hitbox()
            if hits_ship(hitbox, ship0.x, ship0.y, OVERLAP_EPS):
                touching.append(d)
            elif hits_ship(hitbox, ship0.x, ship0.y, -OVERLAP_EPS):
                ambiguous = True
    return touching, ambiguous


def _active_islands(upd):
    """(variant, x, y, inverted) of each island in play, for the details of a finding."""
    return [
        (d.variant, round(d.x, 1), round(d.y, 1), d.invert)
        for d in upd
        if d.effect_on_touch() is TouchEffect.BLOCK and d.phase is Phase.ACTIVE
    ]


@dataclass
class _Facts:
    """What one playing tick should look like, worked out once and shared by the checks.

    `run` is the state before the tick and `new` the game's state after it. `ship0` is where the oracle's own
    step puts the ship, `touching` the hazards it overlaps there, `expected_loss` the lives the design says
    are lost, and `loss` the lives the game took.
    """

    run: object
    new: object
    thrust: object
    tick: int
    info: dict
    upd: tuple
    ground: object
    wells: object
    press: bool
    protected: bool
    stands: bool
    ship0: object
    fell: bool
    touching: list
    ambiguous: bool
    expected_loss: int
    loss: int


def _clear_spot_offsets(shapes):
    """Distance from the spawn point to the nearest island-free spot straight up and straight down.

    Up stops at the top line, down at RESPAWN_SEARCH_LIMIT_Y. A direction with no clear spot is None.
    """

    def clear(y):
        return island_depth(shapes, SPAWN_X, y) <= OVERLAP_EPS

    up = down = None
    y = SPAWN_Y
    while y > TOP_LINE_Y + SHIP_HALF - 1e-9:
        y -= RESPAWN_SEARCH_STEP_PX
        if clear(y):
            up = SPAWN_Y - y
            break
    y = SPAWN_Y
    while y < RESPAWN_SEARCH_LIMIT_Y:
        y += RESPAWN_SEARCH_STEP_PX
        if clear(y):
            down = y - SPAWN_Y
            break
    return up, down


class Checker:
    def __init__(self, meta: dict, last_life_delay: int = 120, keep_examples: int = EXAMPLES_KEPT):
        self.meta = meta
        self.t = 0
        self.delay = last_life_delay
        self.findings: dict[str, dict] = {}
        self.keep = keep_examples
        self.stats = dict(
            max_drifters=0,
            max_popups=0,
            max_rings=0,
            max_depth=0.0,
            max_push=0.0,
            squeezes=0,
            falls=0,
            protected_falls=0,
            hits=0,
            island_ticks=0,
            jumps=0,
            max_age=0,
        )
        self.max_drifters_by_wave: dict[str, int] = {}
        self.born: dict[int, int] = {}
        self.deaths: list[dict] = []
        self.waves_log: list[tuple] = []
        self.seg_key = None
        self.seg_start = 0
        self.seg_limit = 10**9
        self.seg_flagged = False
        self.level_start: dict[int, int] = {}
        self.death_t = None
        self.banners: list[tuple[int, int]] = []
        self.pos_hist: deque = deque(maxlen=STUCK_WINDOW_TICKS)
        self.stuck_last = -(10**9)
        self.squeeze_log: list[dict] = []
        self.jump_log: list[dict] = []
        self.uid_types: dict[int, str] = {}
        self.spawn_counts: dict[str, int] = {}
        self.fall_wait_log: list[dict] = []

    def report(self):
        """What a run result keeps from the oracle: the findings, the stats and the logs."""
        return dict(
            findings=self.findings,
            stats=self.stats,
            max_drifters_by_wave=self.max_drifters_by_wave,
            waves_log=self.waves_log,
            level_start=self.level_start,
            banners=self.banners,
            deaths=self.deaths,
            spawn_counts=self.spawn_counts,
            squeeze_log=self.squeeze_log,
            jump_log=self.jump_log,
        )

    # ---- helpers
    def add(self, kind, key=None, **details):
        k = kind if key is None else f"{kind}|{key}"
        f = self.findings.get(k)
        d = dict(tick=self.t, **self.meta, **details)
        if f is None:
            self.findings[k] = dict(kind=kind, key=key, count=1, examples=[d])
        else:
            f["count"] += 1
            if len(f["examples"]) < self.keep:
                f["examples"].append(d)

    def ctx(self, run):
        w = run.waves
        return dict(
            wave=w.wave_id if w else None,
            level=run.level,
            lives=run.lives,
            ship=(round(run.ship.x, 3), round(run.ship.y, 3), round(run.ship.vx, 3), round(run.ship.vy, 3)),
        )

    # ---- main
    def check(self, run, thrust, new):
        """Compare one tick of the game (`run` before, `new` after, the keys `thrust`) with the design rules."""
        t = self.t
        self.t += 1
        if run.game_over:
            if new.score != run.score or new.lives != run.lives:
                self.add("game_over_not_frozen", **self.ctx(run))
            return
        self._check_monotonic_and_ranges(run, new)
        self._check_scroll_and_ship_values(run, new)
        self._track_banner(run, new, t)
        self._wave_progress(run, new, t)
        self._leaks(run, new, t)
        if run.burst is not None:
            self._last_life(run, new, t)
            return
        self._playing(run, thrust, new, t)

    def _check_monotonic_and_ranges(self, run, new):
        """Lives, score, scroll and level only move the allowed way, and stay in range."""
        if new.lives > run.lives:
            self.add("lives_increase", **self.ctx(run), new_lives=new.lives)
        if not 0 <= new.lives <= LIVES_START:
            self.add("lives_range", **self.ctx(run), new_lives=new.lives)
        if new.score < run.score:
            self.add("score_decrease", **self.ctx(run), old=run.score, new=new.score)
        if new.scroll.distance_px < run.scroll.distance_px:
            self.add("scroll_decrease", **self.ctx(run))
        if new.level < run.level:
            self.add("level_decrease", **self.ctx(run), new_level=new.level)
        if not 1 <= new.level <= LEVEL_COUNT:
            self.add("level_range", **self.ctx(run), new_level=new.level)

    def _check_scroll_and_ship_values(self, run, new):
        """The world scrolls at the GDD speed for the level, and the ship's numbers are sane."""
        expected = 0.0 if run.scroll.ticks + 1 <= SCROLL_START_DELAY_TICKS else SCROLL_BASE * SCROLL_MULT[run.level - 1]
        got = new.scroll.distance_px - run.scroll.distance_px
        if abs(got - expected) > OVERLAP_EPS:
            self.add("scroll_speed", **self.ctx(run), expected=expected, got=got)
        s = new.ship
        if not all(math.isfinite(v) for v in (s.x, s.y, s.vx, s.vy)):
            self.add("ship_not_finite", **self.ctx(run), now=repr(s))
        elif abs(s.vx) > MAX_SHIP_SPEED or abs(s.vy) > MAX_SHIP_SPEED:
            self.add("ship_speed_huge", **self.ctx(run), now=repr(s))

    def _track_banner(self, run, new, t):
        """Note the tick a level-up banner first shows, once per banner."""
        is_new_banner = (
            not self.banners or self.banners[-1][1] != new.level or self.banners[-1][0] < t - BANNER_DEDUPE_TICKS
        )
        if new.level_up is not None and is_new_banner and run.level_up is None:
            self.banners.append((t, new.level))

    def _last_life(self, run, new, t):
        if new.score != run.score:
            self.add("score_moved_in_last_life", **self.ctx(run), old=run.score, new=new.score)
        if new.lives != 0 or new.ship != run.ship:
            self.add("last_life_state_changed", **self.ctx(run))
        if new.game_over:
            took = t - self.death_t if self.death_t is not None else None
            self.stats["game_over_after"] = took
            if took != self.delay:
                self.add("game_over_delay", **self.ctx(run), took=took, expected=self.delay)

    # ---- one playing tick
    def _playing(self, run, thrust, new, t):
        """Work out what the design says should have happened, then compare each part with `new`."""
        f = self._expected(run, thrust, new, t)
        self._check_life_loss(f)
        self._check_after_hit(f)
        self._check_waiting(f)
        self._check_grazes(f)
        if new.burst is None:  # in the last-life burst the ship stays where it died
            self._check_ship(f)
        self._stuck(run, thrust, new, t)

    def _expected(self, run, thrust, new, t):
        """The facts about this tick that the checks share: where the ship should be, what it touches."""
        press = _press(thrust, run.held)
        scroll_px = scroll_step_px(run.scroll, run.level)
        upd = CAPTURE.get("upd")
        if upd is None or CAPTURE.get("for") is not run:
            upd = tuple(
                d.update(TickContext(ship=run.ship, scroll_step_px=scroll_px)).mark_entered() for d in run.drifters
            )
        ground = island_ground(upd, scroll_px)
        wells = gravity_wells(upd)
        stands = run.waiting and not press
        ship0 = block_ship(run.ship, ground) if stands else step(run.ship, thrust, ground, wells)
        fell = ship0.y - SHIP_HALF >= SCREEN_H
        touching, ambiguous = ([], False) if fell else _touching(upd, ship0)
        protected = run.invuln_ticks_left > 0
        if fell:
            expected_loss = 0 if protected else 1
        else:
            expected_loss = 1 if (touching and not protected) else 0
        return _Facts(
            run=run,
            new=new,
            thrust=thrust,
            tick=t,
            info=self.ctx(run),
            upd=upd,
            ground=ground,
            wells=wells,
            press=press,
            protected=protected,
            stands=stands,
            ship0=ship0,
            fell=fell,
            touching=touching,
            ambiguous=ambiguous,
            expected_loss=expected_loss,
            loss=run.lives - new.lives,
        )

    def _check_life_loss(self, f):
        """A life is lost exactly when the ship is unprotected and touches a hazard or falls off the bottom."""
        run = f.run
        if f.loss != f.expected_loss and not (f.ambiguous and f.loss in (0, 1) and f.expected_loss == 0):
            kind = "missed_hit" if f.loss < f.expected_loss else "unexplained_life_loss"
            self.add(
                kind,
                key=(run.waves.wave_id if run.waves else None),
                **f.info,
                loss=f.loss,
                expected=f.expected_loss,
                fell=f.fell,
                protected=f.protected,
                waiting=run.waiting,
                stands=f.stands,
                touching=[(d.drifter_type.value, d.variant, round(d.x, 1), round(d.y, 1)) for d in f.touching],
                ship0=(round(f.ship0.x, 3), round(f.ship0.y, 3)),
            )
        if f.fell:
            self.stats["protected_falls" if f.protected else "falls"] += 1

    def _check_after_hit(self, f):
        """After a real life loss: log the death, the invulnerability reset and the re-hit cooldown.
        With no loss: the invulnerability timer counts down by one."""
        run, new = f.run, f.new
        if f.loss == 1 and f.expected_loss == 1:
            if not f.fell:
                self.stats["hits"] += 1
            self.deaths.append(
                dict(
                    tick=f.tick,
                    wave=f.info["wave"],
                    level=run.level,
                    cause="fall" if f.fell else "hit",
                    ship=f.info["ship"],
                    touching=[(d.drifter_type.value, d.variant) for d in f.touching],
                    left_after=new.lives,
                )
            )
            if new.lives == 0:
                self.death_t = f.tick
            elif new.invuln_ticks_left != INVULN_TICKS:
                self.add("invuln_not_reset", **f.info, got=new.invuln_ticks_left)
            for d in f.touching:
                after = next((x for x in new.drifters if x.uid == d.uid), None)
                if after is not None and after.rehit_ticks_left != d.rehit_cooldown_ticks:
                    self.add(
                        "rehit_cooldown_wrong", **f.info, got=after.rehit_ticks_left, expected=d.rehit_cooldown_ticks
                    )
        elif f.loss == 0:
            expected = max(run.invuln_ticks_left - 1, 0)
            if new.invuln_ticks_left != expected:
                self.add("invuln_timer", **f.info, got=new.invuln_ticks_left, expected=expected)

    def _check_waiting(self, f):
        """The ship waits at rest after a respawn until a key is pressed; a fall puts it back to waiting."""
        run, new = f.run, f.new
        if new.lives > 0 or f.loss == 0:
            if f.fell and f.protected:
                expected_wait = False
            elif f.fell:
                expected_wait = True
            else:
                expected_wait = f.stands
            if new.waiting != expected_wait:
                self.add(
                    "waiting_wrong",
                    **f.info,
                    got=new.waiting,
                    expected=expected_wait,
                    press=f.press,
                    fell=f.fell,
                    protected=f.protected,
                )
        if run.waiting and not f.press and not f.fell and not new.waiting and new.lives > 0:
            self.add("wait_ended_without_press", **f.info)
        if run.waiting and f.press and new.waiting and not f.fell:
            self.add("wait_not_ended_by_press", **f.info)
        if f.fell and not f.protected and new.lives > 0 and new.invuln_ticks_left != INVULN_TICKS:
            self.add("fall_invuln", **f.info)

    def _check_grazes(self, f):
        """No graze is paid while protected or waiting, and the count never goes down."""
        run, new = f.run, f.new
        if (f.protected or f.stands) and new.grazes > run.grazes:
            self.add(
                "graze_while_protected", **f.info, protected=f.protected, stands=f.stands, paid=new.grazes - run.grazes
            )
        if new.grazes < run.grazes:
            self.add("graze_decrease", **f.info)

    def _check_ship(self, f):
        """Where the ship ended up: inside the walls, below the top line, matching the oracle's own step,
        out of every island, and (after a fall or an island push) at the right place."""
        run, new, info = f.run, f.new, f.info
        s = new.ship
        islands = f.ground.hitbox
        if s.x - SHIP_HALF < -OVERLAP_EPS or s.x + SHIP_HALF > SCREEN_W + OVERLAP_EPS:
            self.add("ship_outside_wall", **info, now=(s.x, s.y), against_island=s.against_island)
        if s.y - SHIP_HALF < TOP_LINE_Y - OVERLAP_EPS:
            self.add("ship_above_top_line", **info, now=(s.x, s.y), against_island=s.against_island)
        if s.y - SHIP_HALF >= SCREEN_H:
            self.add("ship_below_floor_after_tick", **info, now=(s.x, s.y))
        if not f.fell and new.ship != f.ship0:
            self.add("ship_mismatch", **info, got=repr(new.ship), expected=repr(f.ship0))
        depth = island_depth(islands, s.x, s.y) if islands else 0.0
        if islands:
            self.stats["island_ticks"] += 1
        if depth > self.stats["max_depth"]:
            self.stats["max_depth"] = depth
        if depth > ISLAND_DEPTH_TOLERANCE_PX:
            self.add(
                "ship_in_island",
                key=("fall" if f.fell else "step"),
                **info,
                depth=depth,
                now=(round(s.x, 3), round(s.y, 3)),
                wall=s.wall,
                top=s.at_top_line,
                islands=_active_islands(f.upd),
            )
        if f.fell:
            self._respawn_check(run, new, f.upd, islands, f.protected, info)
        elif islands and not f.stands:
            self._push_check(run, f.thrust, f.ship0, f.wells, new, f.upd, info, f.tick)

    def _respawn_check(self, run, new, upd, shapes, protected, info):
        s = new.ship
        if s.x != SPAWN_X or s.vx != 0.0 or s.vy != 0.0:
            self.add("respawn_not_at_rest_center_x", **info, now=repr(s))
        free = (not shapes) or island_depth(shapes, SPAWN_X, SPAWN_Y) <= OVERLAP_EPS
        if free:
            if s.y != SPAWN_Y:
                self.add("respawn_moved_without_island", **info, now=repr(s))
            return
        du, dd = _clear_spot_offsets(shapes)
        # the nearest clear spot straight up, or straight down when up has none or is clearly farther
        if du is not None and (dd is None or du <= dd + RESPAWN_TIE_PX):
            exp = SPAWN_Y - du
        else:
            exp = SPAWN_Y + dd
        self.fall_wait_log.append(dict(tick=self.t - 1, y=s.y, exp=exp, du=du, dd=dd))
        if abs(s.y - exp) > RESPAWN_TOLERANCE_PX:
            self.add("respawn_spot_not_nearest", **info, got=s.y, expected=exp, du=du, dd=dd)

    def _push_check(self, run, thrust, ship0, wells, new, upd, info, t):
        free = step(run.ship, thrust, NO_GROUND, wells)
        disp = math.hypot(ship0.x - free.x, ship0.y - free.y)
        if disp > self.stats["max_push"]:
            self.stats["max_push"] = disp
        s = new.ship
        if s.against_island and (s.wall is not None or s.at_top_line):
            self.stats["squeezes"] += 1
            if len(self.squeeze_log) < LOG_CAP:
                self.squeeze_log.append(
                    dict(
                        tick=t,
                        **info,
                        now=(round(s.x, 2), round(s.y, 2)),
                        wall=s.wall,
                        top=s.at_top_line,
                        push=round(disp, 2),
                        islands=_active_islands(upd),
                    )
                )
        if disp > PUSH_TELEPORT_PX:
            self.stats["jumps"] += 1
            if len(self.jump_log) < LOG_CAP:
                self.jump_log.append(
                    dict(
                        tick=t,
                        **info,
                        push=round(disp, 2),
                        now=(round(s.x, 2), round(s.y, 2)),
                        islands=_active_islands(upd),
                    )
                )
            self.add("push_teleport", key=f"{int(disp // 10) * 10}+", **info, push=disp, now=(s.x, s.y))

    def _stuck(self, run, thrust, new, t):
        s = new.ship
        self.pos_hist.append(
            (
                s.x,
                s.y,
                thrust.up,
                thrust.down,
                thrust.left,
                thrust.right,
                s.wall,
                s.at_top_line,
                s.against_island,
                new.waiting,
                new.invulnerable,
            )
        )
        if (
            len(self.pos_hist) < STUCK_WINDOW_TICKS
            or t - self.stuck_last < STUCK_REPORT_GAP_TICKS
            or new.burst is not None
        ):
            return
        h = self.pos_hist
        x0, y0 = h[0][0], h[0][1]
        if math.hypot(s.x - x0, s.y - y0) >= 1.0:
            return
        if any(e[9] for e in h):
            return
        ups = {e[2] for e in h}, {e[3] for e in h}, {e[4] for e in h}, {e[5] for e in h}
        up_c, dn_c, l_c, r_c = (next(iter(u)) if len(u) == 1 else None for u in ups)
        if up_c is None and dn_c is None and l_c is None and r_c is None:
            return
        if not any(v for v in (up_c, dn_c, l_c, r_c)):
            return  # holding nothing: gravity must move it; only flag below
        explained = False
        hor = (l_c and not r_c) or (r_c and not l_c)
        ver = (up_c and not dn_c) or (dn_c and not up_c)
        walled = s.x <= SHIP_HALF + OVERLAP_EPS or s.x >= SCREEN_W - SHIP_HALF - OVERLAP_EPS
        top = s.y - SHIP_HALF <= TOP_LINE_Y + OVERLAP_EPS
        if hor and not ver and walled:
            explained = True
        if ver and up_c and not hor and top:
            explained = True
        if hor and ver and walled and top:
            explained = True
        if hor and ver and ((walled and top) or (walled and dn_c is False) or (top and up_c)):
            explained = True
        if explained:
            return
        self.stuck_last = t
        isl = any(e[8] for e in h)
        near = [
            (d.drifter_type.value, d.variant, round(d.x, 1), round(d.y, 1))
            for d in new.drifters
            if abs(d.x - s.x) < 150 and abs(d.y - s.y) < 150
        ]
        self.add(
            "stuck_120",
            key=("island" if isl else "free"),
            **self.ctx(new),
            held=(up_c, dn_c, l_c, r_c),
            against_island=isl,
            wall=s.wall,
            top=s.at_top_line,
            near=near[:8],
        )

    def _wave_progress(self, run, new, t):
        w = new.waves
        if w is None:
            return
        key = (w.wave_id, w.start_px, w.resting, w.level)
        if key != self.seg_key:
            self.seg_key = key
            self.seg_start = t
            self.seg_flagged = False
            if w.level not in self.level_start:
                self.level_start[w.level] = t
            if not w.resting:
                self.waves_log.append((t, w.level, w.wave_id))
                wv = w.book.waves[w.wave_id]
                self.seg_limit = (
                    wv.length_px / (SCROLL_BASE * SCROLL_MULT[w.level - 1])
                    + SCROLL_START_DELAY_TICKS
                    + STALL_SLACK_TICKS
                )
            else:
                self.seg_limit = w.rest_ticks_left + STALL_SLACK_TICKS
        elif not self.seg_flagged and t - self.seg_start > self.seg_limit:
            self.seg_flagged = True
            self.add("wave_stalled", **self.ctx(run), segment=str(key), ticks=t - self.seg_start, limit=self.seg_limit)
        # level stuck before 8
        if w.level < 8:
            ls = self.level_start.get(w.level, 0)
            if t - ls > LEVEL_STUCK_TICKS:
                if not self.findings.get(f"level_stuck|{w.level}"):
                    self.add("level_stuck", key=w.level, **self.ctx(run), since=ls)

    def _leaks(self, run, new, t):
        n = len(new.drifters)
        st = self.stats
        if n > st["max_drifters"]:
            st["max_drifters"] = n
        wid = new.waves.wave_id if new.waves else None
        if n > self.max_drifters_by_wave.get(wid, 0):
            self.max_drifters_by_wave[wid] = n
        if len(new.popups) > st["max_popups"]:
            st["max_popups"] = len(new.popups)
        if len(new.graze_rings) > st["max_rings"]:
            st["max_rings"] = len(new.graze_rings)
        if len(new.popups) > MAX_POPUPS or len(new.graze_rings) > MAX_RINGS or n > MAX_DRIFTERS:
            self.add(
                "unbounded_collections", **self.ctx(run), drifters=n, popups=len(new.popups), rings=len(new.graze_rings)
            )
        uids = set()
        for d in new.drifters:
            if d.uid in uids:
                self.add("duplicate_uid", **self.ctx(run), uid=d.uid)
            uids.add(d.uid)
            b = self.born.get(d.uid)
            if b is None:
                self.born[d.uid] = t
                tname = d.drifter_type.value
                self.uid_types[d.uid] = tname
                self.spawn_counts[tname] = self.spawn_counts.get(tname, 0) + 1
            else:
                age = t - b
                if age > st["max_age"]:
                    st["max_age"] = age
                if age > DRIFTER_MAX_AGE_TICKS:
                    self.add(
                        "drifter_long_lived",
                        key=f"{d.drifter_type.value}/{d.variant}",
                        **self.ctx(run),
                        uid=d.uid,
                        age=age,
                        pos=(round(d.x, 1), round(d.y, 1)),
                        phase=d.phase.value,
                    )
            if not (math.isfinite(d.x) and math.isfinite(d.y)):
                self.add("drifter_not_finite", **self.ctx(run), uid=d.uid, type=d.drifter_type.value)
            elif abs(d.x) > FAR_PX or abs(d.y) > FAR_PX:
                self.add(
                    "drifter_far_outside",
                    key=f"{d.drifter_type.value}/{d.variant}",
                    **self.ctx(run),
                    uid=d.uid,
                    pos=(round(d.x, 1), round(d.y, 1)),
                    phase=d.phase.value,
                )
        # forget dead uids to keep the dict small
        if t % FORGET_DEAD_EVERY_TICKS == 0:
            alive = {d.uid for d in new.drifters}
            self.born = {u: b for u, b in self.born.items() if u in alive}
