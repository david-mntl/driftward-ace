"""Fireball tests, the base rules it relies on, and fireballs inside the run.

Contract: docs/contracts/systems/drifters.md, Rules: Fireball, The base (Drawn parts, Entering,
Leaving, Warning place, Warning tilt, Warning copy, Re-hit cooldown, Birth, Start), Spawner (steps
4, 7 and 8), Diagram (the start table and the Fireball timeline); docs/contracts/systems/run.md,
Rules (steps 3, 7, 8, 9) and Logging. Task: docs/contracts/DRA-56/tasks/DRA-56-04-qa-engineer.md.
One test per behavior it lists. The tuning records are built here from the GDD values below,
never read from game/tuning/, and no expected number is imported from the code under test.
"""

import logging
import math
from dataclasses import dataclass, replace

import pytest

from core.collision import Box, Circle, Hitbox, hitboxes_overlap, place_hitbox
from core.drifters.base import (
    Drifter,
    DrifterType,
    DrifterTypeExtra,
    Phase,
    TickContext,
    TouchEffect,
)
from core.drifters.fireball import Fireball, FireballTypeExtra
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox, spawn

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

SPEED_RATIO: float = 0.47
"""Level 1 speed as a multiple of the top sideways speed. Source: drifters/06-fireball.md,
speed_ratio (guess)."""

LEVEL_ONE_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""px/tick along the path, about 3.0926. Source: drifters/06-fireball.md, speed."""

ANGLE_DEGREES: float = 35.0
"""Path angle from straight down. Source: drifters/06-fireball.md, angle (guess)."""

TAIL_RATIO: float = 0.5
"""Tail radius as a share of the head's. Source: drifters/06-fireball.md, hitbox (guess)."""

HEAD_WIDTHS: dict[str, float] = {"small": 21.0, "big": 32.0}
"""Head widths by variant, px. Source: drifters/06-fireball.md, variants (guess)."""

DRAW_MARGIN: float = 1.5
"""Px added to each circle's radius in the drawn parts. Source: drifters.md, Rules, The base
(Drawn parts) and Rationale (DRA-56)."""

WARNING_TICKS: int = 60
"""ticks. Source: 07-drifters.md, entry_warning_ticks (guess)."""

SCREEN_W: int = 640
SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

WARNING_HALF: float = 12.0
"""Half of the 24 px entry warning. Source: 07-drifters.md, entry_warning_size (guess)."""

HAZARD_SPEED: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
"""Hazard speed × for Levels 1 to 8. Source: 08-difficulty.md, level table."""

REHIT_COOLDOWN: int = 180
REHIT_DIM: float = 0.75
"""Source: 05-lives-and-damage.md, rehit_cooldown, rehit_dim (guess)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

NO_KEY = Thrust()

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

FIREBALL_EXTRA: FireballTypeExtra = FireballTypeExtra(
    angle_degrees=ANGLE_DEGREES, tail_ratio=TAIL_RATIO
)


def expected_tail(head_width: float, invert: bool) -> tuple[float, float, float]:
    """The tail circle as (cx, cy, r), an offset from the head's center, worked out here.

    The tail touches the head from behind along the path: up and to the left, or up and to the
    right with `invert`. Source: drifters.md, Rules, Fireball (Hitbox).
    """
    radius = head_width / 2
    distance = (1 + TAIL_RATIO) * radius
    theta = math.radians(ANGLE_DEGREES)
    side = 1.0 if invert else -1.0
    return side * distance * math.sin(theta), -distance * math.cos(theta), TAIL_RATIO * radius


def expected_velocity(speed: float, invert: bool) -> tuple[float, float]:
    """The per-tick velocity along the path at `speed`, worked out here."""
    theta = math.radians(ANGLE_DEGREES)
    side = -1.0 if invert else 1.0
    return side * speed * math.sin(theta), speed * math.cos(theta)


def expected_hitbox(head_width: float, invert: bool) -> Hitbox:
    """Head first, then tail, as offsets from the head's center."""
    tail_x, tail_y, tail_r = expected_tail(head_width, invert)
    return (Circle(0.0, 0.0, head_width / 2), Circle(tail_x, tail_y, tail_r))


def make_tuning(
    *,
    hazards: HazardRules | None = None,
    switches: PlaytestSwitches | None = None,
    extra: DrifterTypeExtra | None = FIREBALL_EXTRA,
) -> DrifterTuning:
    """Build the fireball and meteorite tuning from the GDD values above.

    Each fireball variant holds the un-inverted hitbox, as `app.tuning` builds it.
    """
    fireball_variants: dict[str, VariantTuning] = {
        name: VariantTuning(
            width=width, height=width, hitbox=expected_hitbox(width, False), extra=None
        )
        for name, width in HEAD_WIDTHS.items()
    }
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.FIREBALL: DrifterTypeTuning(
                variants=fireball_variants,
                default_variant="small",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=extra,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )
    return tuning if hazards is None else replace(tuning, hazards=hazards)


TUNING: DrifterTuning = make_tuning()
CTX: TickContext = TickContext(ship=spawn())
VARIANTS: tuple[str, ...] = tuple(HEAD_WIDTHS)
INVERTS: tuple[bool, ...] = (False, True)


def place(
    variant: str | None = None,
    x: float | None = None,
    y: float | None = None,
    *,
    invert: bool = False,
    level: int = 1,
    as_level: int | None = None,
    specialty_enabled: bool | None = None,
    speed: float | None = None,
    tuning: DrifterTuning = TUNING,
) -> Fireball:
    """Spawn a fireball through the spawner. No x and no y: the top corner."""
    placement: Placement = Placement(
        DrifterType.FIREBALL,
        x,
        y,
        variant=variant,
        as_level=as_level,
        specialty_enabled=specialty_enabled,
        invert=invert,
        speed=speed,
    )
    drifter: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(drifter, Fireball)
    return drifter


def advance[T: Drifter](drifter: T, ticks: int, ctx: TickContext = CTX) -> T:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(ctx)
    return drifter


def active(
    variant: str | None = None,
    x: float | None = None,
    y: float | None = None,
    *,
    invert: bool = False,
    level: int = 1,
    speed: float | None = None,
    tuning: DrifterTuning = TUNING,
) -> Fireball:
    """A fireball that has just turned ACTIVE, on its first state."""
    fireball = advance(
        place(variant, x, y, invert=invert, level=level, speed=speed, tuning=tuning), WARNING_TICKS
    )
    assert fireball.phase is Phase.ACTIVE
    assert fireball.ticks_in_phase == 0
    return fireball


def parts_of(
    x: float, y: float, head_width: float, invert: bool
) -> list[tuple[float, float, float]]:
    """The two drawn boxes as (cx, cy, side) for a head at (x, y), worked out here."""
    tail_x, tail_y, tail_r = expected_tail(head_width, invert)
    return [
        (x, y, 2 * (head_width / 2 + DRAW_MARGIN)),
        (x + tail_x, y + tail_y, 2 * (tail_r + DRAW_MARGIN)),
    ]


def part_on_screen(cx: float, cy: float, side: float) -> bool:
    """Whether a box shares area with the screen, strict, worked out here."""
    half = side / 2
    return cx - half < SCREEN_W and cx + half > 0 and cy - half < SCREEN_H and cy + half > 0


def part_past_edge(cx: float, cy: float, side: float) -> bool:
    """Whether a box is fully past a side wall or the floor, never the top, worked out here."""
    half = side / 2
    return cx + half <= 0 or cx - half >= SCREEN_W or cy - half >= SCREEN_H


def assert_circles(actual: Hitbox, expected: Hitbox) -> None:
    """The same circles in the same order, numbers equal within 1e-9."""
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected, strict=True):
        assert isinstance(got, Circle)
        assert isinstance(want, Circle)
        assert (got.cx, got.cy, got.r) == pytest.approx((want.cx, want.cy, want.r), abs=1e-9)


def assert_boxes(actual: tuple[Box, ...], expected: list[tuple[float, float, float]]) -> None:
    """The same square boxes in the same order, numbers equal within 1e-9."""
    assert len(actual) == len(expected)
    for got, (cx, cy, side) in zip(actual, expected, strict=True):
        assert (got.cx, got.cy, got.w, got.h) == pytest.approx((cx, cy, side, side), abs=1e-9)


@dataclass(frozen=True)
class Entry:
    """One way to place a fireball: the placement's x and y, and what the start table says."""

    name: str
    x: float | None
    y: float | None


ENTRIES: tuple[Entry, ...] = (
    Entry("corner", None, None),
    Entry("along the top", 200.0, None),
    Entry("side", None, 120.0),
    Entry("both", 200.0, 120.0),
)
"""no x and no y, x alone, y alone, both. Source: drifters.md, Diagram (the start table)."""


def expected_start(entry: Entry, head_width: float, invert: bool) -> tuple[float, float]:
    """The start center the table gives, worked out here. R is the head's radius."""
    radius = head_width / 2
    if entry.y is not None:
        if entry.x is not None:
            return entry.x, entry.y
        return (SCREEN_W + radius if invert else -radius), entry.y
    corner_x = float(SCREEN_W) if invert else 0.0
    return (corner_x if entry.x is None else entry.x), -radius


def test_each_entry_starts_where_the_start_table_says() -> None:
    for variant in VARIANTS:
        width = HEAD_WIDTHS[variant]
        for invert in INVERTS:
            for entry in ENTRIES:
                where = (variant, invert, entry.name)
                start = place(variant, entry.x, entry.y, invert=invert)
                assert (start.x, start.y) == pytest.approx(
                    expected_start(entry, width, invert), abs=1e-9
                ), where
                assert start.phase is Phase.WARNING
                assert start.ticks_in_phase == 0
                assert start.current_hitbox() == ()
                assert not start.has_entered
                assert start.invert is invert
                assert start.angle_degrees == ANGLE_DEGREES
                assert start.tail_ratio == TAIL_RATIO
                assert (start.width, start.height) == (width, width)
    # The numbers the contract's start table and examples spell out.
    assert (place("small").x, place("small").y) == (0.0, -10.5)
    assert (place("small", invert=True).x, place("small", invert=True).y) == (640.0, -10.5)
    assert (place("big").x, place("big").y) == (0.0, -16.0)
    assert (place("big", invert=True).x, place("big", invert=True).y) == (640.0, -16.0)
    assert (place("small", y=120.0).x, place("small", y=120.0).y) == (-10.5, 120.0)
    assert (place("small", y=120.0, invert=True).x, place("small", y=120.0, invert=True).y) == (
        650.5,
        120.0,
    )
    assert (place("big", y=120.0).x, place("big", y=120.0, invert=True).x) == (-16.0, 656.0)
    # No variant given: small, the default. Nothing is required: it never raises.
    assert place().variant == "small"
    assert place(x=300.0, y=300.0).x == 300.0


def test_the_warning_shows_where_the_start_table_says() -> None:
    far_right: float = SCREEN_W - WARNING_HALF
    far_bottom: float = SCREEN_H - WARNING_HALF
    for variant in VARIANTS:
        for invert in INVERTS:
            corner = place(variant, invert=invert)
            expected = (far_right if invert else WARNING_HALF, WARNING_HALF)
            assert corner.warning_center() == pytest.approx(expected), (variant, invert)
            # Along the top: at its x against the top edge, x kept 12 px from each wall.
            for x, wanted in ((200.0, 200.0), (3.0, 12.0), (12.0, 12.0), (637.0, 628.0)):
                top = place(variant, x, invert=invert)
                assert top.warning_center() == pytest.approx((wanted, WARNING_HALF)), (x, invert)
            # A side: at its y against the wall it enters from.
            for y, wanted in ((120.0, 120.0), (5.0, 12.0), (475.0, far_bottom)):
                side = place(variant, y=y, invert=invert)
                side_x = far_right if invert else WARNING_HALF
                assert side.warning_center() == pytest.approx((side_x, wanted)), (y, invert)
            # Both set and on the screen: where it is.
            both = place(variant, 200.0, 300.0, invert=invert)
            assert both.warning_center() == pytest.approx((200.0, 300.0))
            # The warning stays put on every WARNING state.
            waiting = place(variant, invert=invert)
            shown = waiting.warning_center()
            for _ in range(WARNING_TICKS - 1):
                waiting = waiting.update(CTX)
                assert waiting.phase is Phase.WARNING
                assert waiting.warning_center() == shown
    # The contract's table, by name.
    assert place("small").warning_center() == (12.0, 12.0)
    assert place("small", invert=True).warning_center() == (628.0, 12.0)


def test_it_flies_a_straight_line_at_its_angle_and_speed_mirrored_by_invert() -> None:
    for variant in VARIANTS:
        for invert in INVERTS:
            for level in range(1, 9):
                speed = LEVEL_ONE_SPEED * HAZARD_SPEED[level - 1]
                vx, vy = expected_velocity(speed, invert)
                fireball = place(variant, invert=invert, level=level)
                where = (variant, invert, level)
                assert fireball.speed == pytest.approx(speed), where
                assert (fireball.velocity_x, fireball.velocity_y) == pytest.approx((vx, vy)), where
                # In WARNING it doesn't move: 59 updates, then it turns ACTIVE on the 60th.
                start = (fireball.x, fireball.y)
                for _ in range(WARNING_TICKS - 1):
                    fireball = fireball.update(CTX)
                    assert (fireball.x, fireball.y) == start
                    assert fireball.phase is Phase.WARNING
                fireball = fireball.update(CTX)
                assert fireball.phase is Phase.ACTIVE
                assert fireball.ticks_in_phase == 0
                assert (fireball.x, fireball.y) == start
                # Then it moves by the same step on every tick, in a straight line.
                for n in range(1, 41):
                    before = (fireball.x, fireball.y)
                    fireball = fireball.update(CTX)
                    assert fireball.ticks_in_phase == n
                    assert (fireball.x - before[0], fireball.y - before[1]) == pytest.approx(
                        (vx, vy), abs=1e-9
                    ), where
                    assert (fireball.x, fireball.y) == pytest.approx(
                        (start[0] + n * vx, start[1] + n * vy), abs=1e-9
                    )
                # Along the path it covers `speed` per tick, 35 degrees from straight down, and
                # the angle never changes with the level.
                assert math.hypot(vx, vy) == pytest.approx(speed)
                assert math.degrees(math.atan2(abs(vx), vy)) == pytest.approx(ANGLE_DEGREES)
                assert (vx < 0) is invert
                assert vy > 0
    # The numbers the contract spells out.
    small = place("small")
    assert (small.velocity_x, small.velocity_y) == pytest.approx((1.7738, 2.5333), abs=1e-4)
    assert small.speed == pytest.approx(3.0926, abs=1e-4)
    level_eight = place("small", level=8)
    assert (level_eight.velocity_x, level_eight.velocity_y) == pytest.approx(
        (2.5189, 3.5973), abs=1e-4
    )
    assert level_eight.speed == pytest.approx(4.3915, abs=1e-4)
    # The state after 198 active ticks from the corner is the contract's: x 351.22, y 491.10.
    far = advance(active("small"), 198)
    assert (far.x, far.y) == pytest.approx((351.22, 491.10), abs=0.01)


def test_a_placements_speed_replaces_the_level_one_speed_along_the_path() -> None:
    for invert in INVERTS:
        for level in (1, 8):
            fireball = place("small", invert=invert, level=level, speed=2.0)
            wanted = 2.0 * HAZARD_SPEED[level - 1]
            vx, vy = expected_velocity(wanted, invert)
            assert fireball.speed == pytest.approx(wanted)
            assert (fireball.velocity_x, fireball.velocity_y) == pytest.approx((vx, vy))
            assert math.hypot(fireball.velocity_x, fireball.velocity_y) == pytest.approx(wanted)
            assert math.degrees(
                math.atan2(abs(fireball.velocity_x), fireball.velocity_y)
            ) == pytest.approx(ANGLE_DEGREES)
        # as_level sets the Level 8 speed multiplier at Level 1 the same way.
        as_eight = place("big", invert=invert, level=1, as_level=8, speed=2.0)
        assert as_eight.speed == pytest.approx(2.0 * 1.42)
        # Without a placement speed the default holds.
        assert place("big", invert=invert).speed == pytest.approx(LEVEL_ONE_SPEED)


def test_the_hitbox_is_the_head_on_its_center_and_the_tail_touching_from_behind() -> None:
    for variant in VARIANTS:
        width = HEAD_WIDTHS[variant]
        for invert in INVERTS:
            fireball = place(variant, invert=invert)
            where = (variant, invert)
            assert_circles(fireball.hitbox, expected_hitbox(width, invert))
            head, tail = fireball.hitbox
            assert isinstance(head, Circle)
            assert isinstance(tail, Circle)
            assert (head.cx, head.cy, head.r) == (0.0, 0.0, width / 2)
            assert tail.r == pytest.approx(TAIL_RATIO * width / 2)
            # The tail touches the head: centers are exactly the two radii apart.
            assert math.hypot(tail.cx, tail.cy) == pytest.approx(head.r + tail.r), where
            # It is behind along the path: the head-to-tail vector is the path turned around.
            vx, vy = fireball.velocity_x, fireball.velocity_y
            cross = tail.cx * vy - tail.cy * vx
            dot = tail.cx * vx + tail.cy * vy
            assert cross == pytest.approx(0.0, abs=1e-9), where
            assert dot < 0, where
            # Up and to the left; up and to the right with invert.
            assert tail.cy < 0
            assert (tail.cx > 0) is invert
            # Nothing in WARNING; placed at (x, y) once ACTIVE, moving with it.
            assert fireball.current_hitbox() == ()
            live = advance(fireball, WARNING_TICKS + 7)
            assert live.phase is Phase.ACTIVE
            placed = place_hitbox(expected_hitbox(width, invert), live.x, live.y)
            assert_circles(live.current_hitbox(), placed)
            assert live.hitbox == fireball.hitbox
            assert live.effect_on_touch() is TouchEffect.HIT
    # The numbers the contract spells out: small tail at (-9.03, -12.90) r 5.25; big, invert,
    # tail at (+13.77, -19.66) r 8.
    _, small_tail = place("small").hitbox
    assert isinstance(small_tail, Circle)
    assert (small_tail.cx, small_tail.cy, small_tail.r) == pytest.approx(
        (-9.03, -12.90, 5.25), abs=0.01
    )
    _, big_tail = place("big", invert=True).hitbox
    assert isinstance(big_tail, Circle)
    assert (big_tail.cx, big_tail.cy, big_tail.r) == pytest.approx((13.77, -19.66, 8.0), abs=0.01)


def test_the_drawn_parts_are_one_box_per_circle_and_a_meteorites_is_its_footprint() -> None:
    for variant in VARIANTS:
        width = HEAD_WIDTHS[variant]
        for invert in INVERTS:
            fireball = advance(active(variant, 300.0, 100.0, invert=invert), 5)
            assert_boxes(fireball.drawn_parts(), parts_of(fireball.x, fireball.y, width, invert))
    # The sizes the contract spells out: 24 and 13.5 small, 35 and 19 big.
    small_head, small_tail = active("small", 300.0, 100.0).drawn_parts()
    assert (small_head.w, small_head.h, small_tail.w, small_tail.h) == (24.0, 24.0, 13.5, 13.5)
    big_head, big_tail = active("big", 300.0, 100.0, invert=True).drawn_parts()
    assert (big_head.w, big_head.h, big_tail.w, big_tail.h) == (35.0, 35.0, 19.0, 19.0)
    # A meteorite draws its footprint alone: one box, its center and its size.
    rock = spawn_drifter(Placement(DrifterType.METEORITE, 300.0, 100.0), 1, TUNING)
    assert isinstance(rock, Meteorite)
    rock = advance(rock, WARNING_TICKS + 3)
    assert rock.drawn_parts() == (Box(rock.x, rock.y, 28.0, 28.0),)
    assert rock.drawn_parts() == (Box(300.0, rock.y, 28.0, 28.0),)


def entered_and_off(fireball: Fireball) -> tuple[bool, bool]:
    """Whether the contract's rules say it has entered, and is off screen, worked out here."""
    width = fireball.width
    parts = parts_of(fireball.x, fireball.y, width, fireball.invert)
    entered = fireball.phase is Phase.ACTIVE and any(part_on_screen(*p) for p in parts)
    off = all(part_past_edge(*p) for p in parts)
    return entered, off


def test_it_leaves_only_when_head_and_tail_are_both_off_and_never_before_it_entered() -> None:
    # Each state of a flight from every kind of entry: has_entered and is_off_screen follow the
    # contract's boxes on every tick, and it does leave.
    entries: tuple[Entry, ...] = (
        Entry("corner", None, None),
        Entry("along the top", 200.0, None),
        Entry("side", None, 120.0),
    )
    first_off: dict[tuple[str, bool, str], int] = {}
    for variant in VARIANTS:
        for invert in INVERTS:
            for entry in entries:
                fireball = place(variant, entry.x, entry.y, invert=invert)
                entered = False
                found: int | None = None
                for step in range(1, 1000):
                    fireball = fireball.update(CTX).mark_entered()
                    if fireball.phase is not Phase.ACTIVE:
                        assert not fireball.has_entered
                        assert not fireball.is_off_screen()
                        continue
                    seen, off = entered_and_off(fireball)
                    entered = entered or seen
                    assert fireball.has_entered is entered, (variant, invert, entry.name, step)
                    assert fireball.is_off_screen() is (entered and off), (
                        variant,
                        invert,
                        entry.name,
                        step,
                    )
                    if fireball.is_off_screen():
                        found = fireball.ticks_in_phase
                        break
                assert found is not None, (variant, invert, entry.name)
                first_off[(variant, invert, entry.name)] = found
    # The three drop points the contract spells out, in active ticks.
    assert first_off[("small", False, "corner")] == 202
    assert first_off[("big", True, "corner")] == 208
    assert first_off[("small", False, "side")] == 150


def test_it_stays_while_either_drawn_box_is_on_screen_and_goes_by_each_boxs_own_edge() -> None:
    head_half = 10.5 + DRAW_MARGIN
    tail_x, tail_y, tail_r = expected_tail(21.0, False)
    tail_half = tail_r + DRAW_MARGIN

    def at(x: float, y: float, *, invert: bool = False, entered: bool = True) -> Fireball:
        base = active("small", invert=invert)
        return replace(base, x=x, y=y, has_entered=entered)

    # The head is fully below the floor and the tail's box is still on screen: it stays.
    head_off_y = SCREEN_H + head_half + 1.0
    lone_tail = at(320.0, head_off_y)
    assert part_past_edge(*parts_of(320.0, head_off_y, 21.0, False)[0])
    assert not part_past_edge(*parts_of(320.0, head_off_y, 21.0, False)[1])
    assert lone_tail.is_partly_on_screen()
    assert not lone_tail.is_off_screen()
    # Just before the tail's box top reaches the floor it stays; on the first state it has, it goes.
    boundary_y = SCREEN_H - tail_y + tail_half
    assert not at(320.0, boundary_y - 0.01).is_off_screen()
    assert at(320.0, boundary_y).is_off_screen() is part_past_edge(
        320.0 + tail_x, boundary_y + tail_y, 2 * tail_half
    )
    assert at(320.0, boundary_y + 0.01).is_off_screen()
    # Each box by its own edge: the head under the floor, the tail past the left wall.
    assert at(-8.0, 500.0).is_off_screen()
    assert part_past_edge(*parts_of(-8.0, 500.0, 21.0, False)[0])
    assert part_past_edge(*parts_of(-8.0, 500.0, 21.0, False)[1])
    # The head past the right wall, the tail's box still across the wall line: it stays.
    head_side_x = SCREEN_W + head_half
    assert not at(head_side_x, 100.0).is_off_screen()
    assert at(head_side_x + 9.03 + tail_half - head_half + 0.01, 100.0).is_off_screen()
    # The same, mirrored, at the left wall with invert: the tail trails to the right.
    assert not at(-head_half, 100.0, invert=True).is_off_screen()
    assert at(-(9.03 + tail_half) - 0.05, 100.0, invert=True).is_off_screen()
    # Never at the top, however far above it is.
    assert not at(320.0, -300.0).is_off_screen()
    assert not at(320.0, -head_half - 0.5).is_off_screen()
    # Never before it has entered, wherever it is.
    unentered = at(320.0, 900.0, entered=False)
    assert unentered.phase is Phase.ACTIVE
    assert not unentered.is_partly_on_screen()
    assert not unentered.is_off_screen()
    assert not unentered.mark_entered().has_entered
    assert not advance(unentered, 50).mark_entered().is_off_screen()
    # Entering is strict: a head box that only touches the top edge is not on screen.
    touching = at(320.0, -head_half, entered=False)
    assert not touching.is_partly_on_screen()
    assert touching.mark_entered() == touching
    inside = at(320.0, -head_half + 0.01, entered=False)
    assert inside.is_partly_on_screen()
    assert inside.mark_entered().has_entered
    # The tail's box alone on screen counts as partly on screen.
    assert lone_tail.is_partly_on_screen()
    # In WARNING it is never off screen, even with has_entered forced on.
    warning = replace(place("small"), x=320.0, y=900.0, has_entered=True)
    assert warning.phase is Phase.WARNING
    assert not warning.is_off_screen()


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def run_with_ship(ship: Ship, *placements: Placement, tuning: DrifterTuning = TUNING) -> Run:
    """A fresh run with the ship put where the test wants it, and the placements added."""
    return add_drifters(replace(start_run(), ship=ship), list(placements), tuning)


def gone_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """The `drifter gone` lines the run logged."""
    return lines_starting(caplog, "drifter gone")


def touch_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """The `drifter touch` lines the run logged."""
    return lines_starting(caplog, "drifter touch")


def lines_starting(caplog: pytest.LogCaptureFixture, prefix: str) -> list[str]:
    """The lines the run logged that start with `prefix`."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == RUN_LOGGER and r.getMessage().startswith(prefix)
    ]


def test_the_corner_timeline_holds_in_the_run_and_it_is_dropped_only_when_every_part_is_off(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    parked = resting(HOME_X, 20.0)
    run = run_with_ship(parked, Placement(DrifterType.FIREBALL))
    vx, vy = expected_velocity(LEVEL_ONE_SPEED, False)
    assert len(run.drifters) == 1
    for state in range(1, 262):
        run = step_run(replace(run, ship=parked), NO_KEY)
        assert len(run.drifters) == 1, state
        fireball = run.drifters[0]
        assert isinstance(fireball, Fireball)
        if state < WARNING_TICKS:
            assert fireball.phase is Phase.WARNING
            assert not fireball.has_entered
            assert (fireball.x, fireball.y) == (0.0, -10.5)
            continue
        n = state - WARNING_TICKS
        assert fireball.phase is Phase.ACTIVE
        assert fireball.ticks_in_phase == n
        assert fireball.has_entered, state
        assert (fireball.x, fireball.y) == pytest.approx((n * vx, -10.5 + n * vy), abs=1e-9)
        if state == WARNING_TICKS:
            assert len(fireball.current_hitbox()) == 2
        if state == 258:
            # The head's own circle is fully below the floor; the tail's box top is on screen.
            assert (fireball.x, fireball.y) == pytest.approx((351.22, 491.10), abs=0.01)
            head_circle = fireball.current_hitbox()[0]
            assert isinstance(head_circle, Circle)
            assert head_circle.cy - head_circle.r >= SCREEN_H
            tail_box = fireball.drawn_parts()[1]
            assert tail_box.cy - tail_box.h / 2 == pytest.approx(471.44, abs=0.01)
            assert not part_past_edge(tail_box.cx, tail_box.cy, tail_box.w)
        if state == 261:
            tail_box = fireball.drawn_parts()[1]
            assert (fireball.x, fireball.y) == pytest.approx((356.54, 498.70), abs=0.01)
            assert tail_box.cy - tail_box.h / 2 == pytest.approx(479.04, abs=0.01)
        assert gone_lines(caplog) == [], state
    # Tick T+262: the tail's box top is at 481.58 and the head's at 489.23: every part is off.
    run = step_run(replace(run, ship=parked), NO_KEY)
    assert run.drifters == ()
    assert run.lives == LIVES_START
    last = 262 - WARNING_TICKS
    assert gone_lines(caplog) == [
        f"drifter gone id=1 type=fireball x={last * vx:.2f} y={-10.5 + last * vy:.2f}"
    ]
    assert gone_lines(caplog) == ["drifter gone id=1 type=fireball x=358.32 y=501.23"]
    assert touch_lines(caplog) == []
    # Its life is exactly: spawn, active, gone.
    assert len(lines_starting(caplog, "drifter spawn")) == 1
    assert len(lines_starting(caplog, "drifter active")) == 1


def test_big_invert_and_side_fireballs_are_dropped_on_the_contracts_ticks() -> None:
    parked = resting(HOME_X, 20.0)
    cases: tuple[tuple[Placement, int], ...] = (
        (Placement(DrifterType.FIREBALL, variant="big", invert=True), 208),
        (Placement(DrifterType.FIREBALL, y=120.0), 150),
    )
    for placement, active_ticks in cases:
        run = run_with_ship(parked, placement)
        for step in range(1, WARNING_TICKS + active_ticks):
            run = step_run(replace(run, ship=parked), NO_KEY)
            assert len(run.drifters) == 1, (placement, step)
        run = step_run(replace(run, ship=parked), NO_KEY)
        assert run.drifters == (), placement
        assert run.lives == LIVES_START
    # The contract's last positions: big invert x 271.04, y 510.93; side x 255.58, y 500.00.
    big = advance(active("big", invert=True), 208)
    assert (big.x, big.y) == pytest.approx((271.04, 510.93), abs=0.01)
    side = advance(active("small", y=120.0), 150)
    assert (side.x, side.y) == pytest.approx((255.58, 500.00), abs=0.01)


def test_its_warning_copy_is_tilted_along_its_path_with_the_tail_back() -> None:
    for variant in VARIANTS:
        width = HEAD_WIDTHS[variant]
        radius = width / 2
        for invert in INVERTS:
            fireball = place(variant, invert=invert)
            where = (variant, invert)
            # The tilt is +35 counterclockwise flying down to the right, -35 with invert.
            tilt = fireball.warning_tilt_degrees()
            assert tilt == (-ANGLE_DEGREES if invert else ANGLE_DEGREES), where
            copy = fireball.warning_copy()
            # The comet laid straight down, sized on head plus tail, still in WARNING.
            assert isinstance(copy, Fireball)
            assert copy.phase is Phase.WARNING
            assert copy.width == pytest.approx(width)
            assert copy.height == pytest.approx((1 + TAIL_RATIO) * width)
            assert_circles(
                copy.hitbox,
                (
                    Circle(0.0, TAIL_RATIO * radius, radius),
                    Circle(0.0, -radius, TAIL_RATIO * radius),
                ),
            )
            # Never mirrored: the copy is the same whatever `invert` says.
            assert_circles(copy.hitbox, place(variant).warning_copy().hitbox)
            # The copy's head is below its tail and they touch.
            copy_head, copy_tail = copy.hitbox
            assert isinstance(copy_head, Circle)
            assert isinstance(copy_tail, Circle)
            assert copy_head.cy > copy_tail.cy
            assert math.hypot(copy_head.cx - copy_tail.cx, copy_head.cy - copy_tail.cy) == (
                pytest.approx(copy_head.r + copy_tail.r)
            )
            # The whole comet fits the copy's box.
            assert copy_head.cy + copy_head.r == pytest.approx(copy.height / 2)
            assert copy_tail.cy - copy_tail.r == pytest.approx(-copy.height / 2)
            # Turning the copy counterclockwise on screen by the tilt (y down: up goes to the
            # left) puts the tail back along the path, where the hitbox has it.
            behind_x = copy_tail.cx - copy_head.cx
            behind_y = copy_tail.cy - copy_head.cy
            turn = math.radians(tilt)
            turned = (
                behind_x * math.cos(turn) + behind_y * math.sin(turn),
                -behind_x * math.sin(turn) + behind_y * math.cos(turn),
            )
            _, tail = fireball.hitbox
            assert isinstance(tail, Circle)
            assert turned == pytest.approx((tail.cx, tail.cy), abs=1e-9), where
            # The original is untouched.
            assert fireball.width == width
            assert_circles(fireball.hitbox, expected_hitbox(width, invert))
    # The numbers the contract spells out: head plus tail is 31.5 small and 48 big.
    assert place("small").warning_copy().height == pytest.approx(31.5)
    assert place("big").warning_copy().height == pytest.approx(48.0)
    assert place("small").warning_copy().width == pytest.approx(21.0)
    # A meteorite's copy is itself and its tilt is 0.
    rock = spawn_drifter(Placement(DrifterType.METEORITE, 300.0), 1, TUNING)
    assert rock.warning_copy() == rock
    assert rock.warning_tilt_degrees() == 0.0


def test_it_refuses_a_specialty_and_a_tuning_without_its_type_values() -> None:
    with pytest.raises(ValueError, match="fireball has no specialty"):
        place("small", specialty_enabled=True)
    # Off and left out are fine, and so are invert, a variant, a side, a speed and as_level.
    assert place("small", specialty_enabled=False).specialty is None
    assert place("big", invert=True, y=100.0, speed=2.0, as_level=3).invert
    for broken in (None, DrifterTypeExtra()):
        with pytest.raises(ValueError, match="fireball tuning has no type values"):
            place("small", tuning=make_tuning(extra=broken))
    with pytest.raises(ValueError, match="fireball tuning has no type values"):
        place("big", invert=True, tuning=make_tuning(extra=None))


def fireball_run(fireball: Fireball, ship: Ship, *, invuln: int = 0) -> Run:
    """A run with one ACTIVE fireball, uid 1, that has entered, and the ship where given."""
    return Run(
        ship=ship,
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        invuln_ticks_left=invuln,
        drifters=(replace(fireball, uid=1, has_entered=True),),
        next_uid=2,
    )


def fireball_of(run: Run) -> Fireball:
    """The single fireball on the field."""
    assert len(run.drifters) == 1
    fireball = run.drifters[0]
    assert isinstance(fireball, Fireball)
    return fireball


def tick(run: Run, ship: Ship, *, clear_invuln: bool = True) -> Run:
    """One tick with the ship put back first, and invulnerability cleared so only the cooldown
    can stop a hit."""
    run = replace(run, ship=ship)
    return step_run(replace(run, invuln_ticks_left=0) if clear_invuln else run, NO_KEY)


def test_in_the_run_a_hit_costs_a_life_and_the_fireball_keeps_flying_dim_and_cannot_hit_again(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    ship = resting(HOME_X, HOME_Y)
    # A very slow fireball keeps the ship in it for the whole cooldown.
    crawl = 0.02
    vx, vy = expected_velocity(crawl, False)
    fireball = replace(active("small", HOME_X, HOME_Y - 6.0, speed=crawl), x=HOME_X, y=HOME_Y)
    run = fireball_run(fireball, ship)
    assert hitboxes_overlap(fireball_of(run).current_hitbox(), ship_hitbox(ship))
    run = tick(run, ship)
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert not run.game_over
    assert touch_lines(caplog) == ["drifter touch id=1 type=fireball effect=hit"]
    # It keeps flying: it is still there, still ACTIVE, and moved by its velocity.
    flying = fireball_of(run)
    assert flying.phase is Phase.ACTIVE
    assert (flying.x, flying.y) == pytest.approx((HOME_X + vx, HOME_Y + vy), abs=1e-9)
    assert flying.rehit_ticks_left == REHIT_COOLDOWN
    assert flying.brightness() == REHIT_DIM
    # The next 180 ticks: no hit, with the ship still in it and invulnerability cleared. It dims
    # on exactly 180 states and keeps moving.
    for after in range(1, REHIT_COOLDOWN + 1):
        run = tick(run, ship)
        current = fireball_of(run)
        assert run.lives == LIVES_START - 1, after
        assert hitboxes_overlap(current.current_hitbox(), ship_hitbox(ship)), after
        assert current.ticks_in_phase == flying.ticks_in_phase + after
        assert current.x == pytest.approx(flying.x + after * vx, abs=1e-9)
        assert current.rehit_ticks_left == REHIT_COOLDOWN - after
        assert current.brightness() == (REHIT_DIM if after < REHIT_COOLDOWN else 1.0), after
    assert len(touch_lines(caplog)) == 1
    # The tick after: it hits again, and its cooldown starts again.
    run = tick(run, ship)
    assert run.lives == LIVES_START - 2
    assert run.invuln_ticks_left == INVULN_TICKS
    assert fireball_of(run).rehit_ticks_left == REHIT_COOLDOWN
    assert fireball_of(run).brightness() == REHIT_DIM
    assert len(touch_lines(caplog)) == 2
    # A touch while invulnerable is no hit and starts no cooldown.
    protected = fireball_run(fireball, ship, invuln=INVULN_TICKS)
    for left in range(INVULN_TICKS - 1, -1, -1):
        protected = tick(protected, ship, clear_invuln=False)
        assert protected.lives == LIVES_START
        assert protected.invuln_ticks_left == left
        assert fireball_of(protected).rehit_ticks_left == 0
        assert fireball_of(protected).brightness() == 1.0


def test_in_the_run_touching_the_tail_alone_is_a_hit(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    ship_box_foot = ship_hitbox(resting(HOME_X, HOME_Y))[1]
    assert isinstance(ship_box_foot, Box)
    foot_bottom = ship_box_foot.cy + ship_box_foot.h / 2
    for variant in VARIANTS:
        width = HEAD_WIDTHS[variant]
        for invert in INVERTS:
            tail_x, tail_y, tail_r = expected_tail(width, invert)
            # The tail's center 0.5 px inside the foot's bottom edge; the head is then below it.
            tail_center = (HOME_X, foot_bottom - 0.5)
            head_x, head_y = tail_center[0] - tail_x, tail_center[1] - tail_y
            fireball = replace(
                active(variant, invert=invert),
                x=head_x,
                y=head_y,
                velocity_x=0.0,
                velocity_y=0.0,
            )
            ship = resting(HOME_X, HOME_Y)
            run = fireball_run(fireball, ship)
            head, tail = fireball_of(run).current_hitbox()
            ship_shapes = ship_hitbox(ship)
            where = (variant, invert)
            assert hitboxes_overlap((tail,), ship_shapes), where
            assert not hitboxes_overlap((head,), ship_shapes), where
            caplog.clear()
            run = tick(run, ship)
            assert run.lives == LIVES_START - 1, where
            assert run.invuln_ticks_left == INVULN_TICKS
            assert fireball_of(run).rehit_ticks_left == REHIT_COOLDOWN
            assert touch_lines(caplog) == ["drifter touch id=1 type=fireball effect=hit"], where
            # Just clear: the tail 0.5 px below the foot's bottom edge plus its radius, no hit.
            clear_y = foot_bottom + tail_r + 0.5
            apart = replace(fireball, x=head_x, y=clear_y - tail_y)
            assert not hitboxes_overlap(apart.current_hitbox(), ship_shapes), where
            quiet = tick(fireball_run(apart, ship), ship)
            assert quiet.lives == LIVES_START, where
            assert fireball_of(quiet).rehit_ticks_left == 0
