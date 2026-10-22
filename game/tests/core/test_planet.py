"""The planet, the base rules it relies on, and planets inside the run.

Contract: docs/contracts/systems/drifters.md, Diagram (the planet, its timeline and the inner field
rings table), Interface (`core/drifters/base.py`: `gravity_well`, `start_size`;
`core/drifters/planet.py`), Rules (The base: Start size, Gravity field, Re-hit cooldown; Spawner,
steps 4 Parked and 7; Planet); docs/contracts/systems/run.md, Interface (`gravity_wells`), Rules
(steps 4, 7 and 8, Other rules: Planets) and Logging; docs/contracts/systems/waves.md (the
unknown-type message, tested in test_wave_files.py). Task:
docs/contracts/DRA-96/tasks/DRA-96-07-qa-engineer.md. One test per behavior it lists.

The tuning records are built here from the GDD values below, never read from game/tuning/, and no
expected number is imported from the code under test. The pull formula and the ship against the
body alone are in test_ship_pull.py and test_collision.py.
"""

import logging
from dataclasses import replace
from fractions import Fraction

import pytest

from core.collision import Box, Circle, Hitbox, hitboxes_overlap
from core.drifters.base import (
    Drifter,
    DrifterType,
    DrifterTypeExtra,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
)
from core.drifters.floating_island import IslandShape, IslandVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.planet import Planet, PlanetTypeExtra, PlanetVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, gravity_wells, start_run, step_run
from core.scroll import Scroll
from core.ship import NO_GROUND, GravityWell, Ship, Thrust, ship_hitbox, spawn, step

SIZE: float = 64.0
"""px, a circle. Source: drifters/08-planet.md, size (guess)."""

SURFACE: float = 32.0
"""The body's radius, px. Source: same, hitbox."""

PULL_RADIUS: float = 150.0
"""px from the center. Source: same, pull_radius (guess)."""

PULL_MAX: float = 0.2
"""px/tick². Source: same, pull_max (guess)."""

WARNING_TICKS: int = 60
"""Source: 07-drifters.md, entry_warning_ticks (the shared value, guess)."""

RING_TRIP: int = 120
RING_GAP: int = 60
RING_FADE: float = 50.0
RING_COUNT: int = 2
"""Source: drifters/08-planet.md, field_ring_trip, field_ring_gap, field_ring_fade,
field_ring_count (guess)."""

FIELD_BOX: float = 302.0
"""2 x (pull_radius 150 + FIELD_DRAW_MARGIN 1). Source: drifters.md, Diagram (the planet): drawn
parts Box(0, 0, 302, 302)."""

START_Y: float = -151.0
"""Half the field box above the top edge. Source: drifters.md, Diagram (the planet timeline)."""

SCROLL_SPEED: float = 1.1
"""px/tick at Level 1. Source: 03-world-and-camera.md, scroll_base (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks. Source: 03-world-and-camera.md, scroll_start_delay (guess)."""

SCREEN_W: float = 640.0
SCREEN_H: float = 480.0
"""px. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

REHIT_COOLDOWN: int = 180
"""Ticks. Source: 05-lives-and-damage.md, rehit_cooldown (guess)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

NO_KEY = Thrust()

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: the next step moves the world 1.1 px."""

STILL: Scroll = Scroll()
"""A scroll at tick 0: the next 30 steps leave the world standing still."""

FAR_LEFT: Ship = Ship(x=40.0, y=240.0, vx=0.0, vy=0.0)
"""A resting ship more than 150 px from a planet centered at x 320 whatever its y."""

ROCK_HITBOX: Hitbox = (Circle(0.0, 0.0, 14.0),)
"""The medium meteorite. Source: drifters/01-meteorite.md, variants (guess)."""

PLANET_EXTRA: PlanetVariantExtra = PlanetVariantExtra(pull_radius=PULL_RADIUS, pull_max=PULL_MAX)
PLANET_TYPE_EXTRA: PlanetTypeExtra = PlanetTypeExtra(
    field_ring_trip=RING_TRIP,
    field_ring_gap=RING_GAP,
    field_ring_fade=RING_FADE,
    field_ring_count=RING_COUNT,
)


def make_tuning(
    *,
    switches: PlaytestSwitches | None = None,
    variant_extra: VariantExtra | None = PLANET_EXTRA,
    type_extra: DrifterTypeExtra | None = PLANET_TYPE_EXTRA,
) -> DrifterTuning:
    """Build the planet and meteorite tuning from the GDD values above.

    The planet's records are built the way the contract says `app.tuning` builds them: one
    circle of the file's size, `speed_ratio` 0.0 and the file's warning length. `variant_extra`
    and `type_extra` can be swapped for a wrong one to test the refusals.
    """
    return DrifterTuning(
        drifters={
            DrifterType.PLANET: DrifterTypeTuning(
                variants={
                    "standard": VariantTuning(
                        width=SIZE,
                        height=SIZE,
                        hitbox=(Circle(0.0, 0.0, SIZE / 2),),
                        extra=variant_extra,
                    )
                },
                default_variant="standard",
                speed_ratio=0.0,
                entry_warning_ticks=WARNING_TICKS,
                extra=type_extra,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=ROCK_HITBOX)},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )


TUNING: DrifterTuning = make_tuning()
NO_SCALING: DrifterTuning = make_tuning(
    switches=PlaytestSwitches(hazard_speed_scaling=False, timer_scaling=False)
)


def planet(
    x: float | None = 320.0,
    y: float | None = None,
    *,
    as_level: int | None = None,
    level: int = 1,
    tuning: DrifterTuning = TUNING,
) -> Planet:
    """Spawn a planet through the spawner. y None: its field ring's box on the top edge."""
    placement = Placement(DrifterType.PLANET, x, y, as_level=as_level)
    spawned: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(spawned, Planet)
    return spawned


def active(x: float, y: float) -> Planet:
    """A planet already ACTIVE at (x, y), at the start of its ACTIVE phase."""
    return replace(planet(x, y), phase=Phase.ACTIVE, ticks_in_phase=0)


def rock(x: float, y: float) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, x, y), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0)


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def run_of(
    ship: Ship,
    *drifters: Drifter,
    scroll: Scroll = STILL,
    lives: int = LIVES_START,
    waiting: bool = False,
    invuln_ticks_left: int = 0,
) -> Run:
    """A run with the drifters numbered from 1, in order, and the ship where given."""
    numbered = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return Run(
        ship=ship,
        scroll=scroll,
        lives=lives,
        waiting=waiting,
        invuln_ticks_left=invuln_ticks_left,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def run_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every line the run logged, in order."""
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def planets_of(run: Run) -> list[Planet]:
    """The planets on the field, in order."""
    return [d for d in run.drifters if isinstance(d, Planet)]


def well_at(x: float, y: float) -> GravityWell:
    """The field the contract says a planet at (x, y) pulls with."""
    return GravityWell(x=x, y=y, surface_radius=SURFACE, pull_radius=PULL_RADIUS, pull_max=PULL_MAX)


def test_a_planet_is_born_in_warning_with_speed_0_at_every_level() -> None:
    base = planet(320.0, None)
    assert base.phase is Phase.WARNING
    assert base.ticks_in_phase == 0
    assert base.warning_ticks == WARNING_TICKS
    assert base.speed == 0.0
    assert (base.x, base.y) == (320.0, START_Y)
    assert (base.width, base.height) == (SIZE, SIZE)
    assert base.variant == "standard"
    assert base.hitbox == (Circle(0.0, 0.0, SURFACE),)
    assert base.current_hitbox() == ()
    assert base.pull_radius == PULL_RADIUS
    assert base.pull_max == PULL_MAX
    assert (base.field_ring_trip, base.field_ring_gap) == (RING_TRIP, RING_GAP)
    assert (base.field_ring_fade, base.field_ring_count) == (RING_FADE, RING_COUNT)
    assert base.surface_radius() == SURFACE
    assert base.uid == 0
    assert not base.has_entered
    assert base.specialty is None
    assert base.rehit_ticks_left == 0
    assert base.parked
    assert base.effect_on_touch() is TouchEffect.HIT
    # Every level, every as_level and both switch sets give the very same planet.
    for tuning in (TUNING, NO_SCALING):
        for level in range(1, 9):
            assert planet(320.0, None, level=level, tuning=tuning) == base, level
            assert planet(320.0, None, as_level=level, tuning=tuning) == base, level
    # Added to a run it is in WARNING with its uid, and nothing else about the run changes.
    added = add_drifters(start_run(), [Placement(DrifterType.PLANET, x=320.0)], TUNING)
    assert len(added.drifters) == 1
    assert added.drifters[0].phase is Phase.WARNING
    assert added.drifters[0].uid == 1
    assert added.drifters[0].current_hitbox() == ()
    assert gravity_wells(added.drifters) == ()


def test_a_planet_starts_at_its_x_and_the_y_given_or_its_field_ring_above_the_top_edge() -> None:
    top = planet(320.0, None)
    assert (top.x, top.y) == (320.0, START_Y)
    # The field ring's box has its bottom edge on the top edge: nothing drawn is on screen.
    (box,) = top.drawn_parts()
    assert box.cy + box.h / 2 == 0.0
    assert not top.is_partly_on_screen()
    spot = planet(440.0, 210.0)
    assert (spot.x, spot.y) == (440.0, 210.0)
    assert spot.phase is Phase.WARNING
    zero = planet(0.0, 0.0)
    assert (zero.x, zero.y) == (0.0, 0.0)
    # The start size is the field ring's box, and the base's for a tuning with no pull.
    assert Planet.start_size(SIZE, SIZE, PLANET_EXTRA) == (FIELD_BOX, FIELD_BOX)
    assert Planet.start_size(SIZE, SIZE, None) == (SIZE, SIZE)
    assert Planet.start_position(55.0, None, FIELD_BOX, FIELD_BOX, False) == (55.0, START_Y)
    assert Planet.start_position(55.0, 7.0, FIELD_BOX, FIELD_BOX, False) == (55.0, 7.0)
    # Its warning shows at (x, 12) for a top start, kept 12 px inside each side, and at the placed
    # spot when that is on screen.
    assert top.warning_center() == (320.0, 12.0)
    assert planet(0.0, None).warning_center() == (12.0, 12.0)
    assert planet(640.0, None).warning_center() == (628.0, 12.0)
    assert spot.warning_center() == (440.0, 210.0)
    # A meteorite still starts where it did before DRA-96: its bottom edge on the top edge.
    for x in (320.0, 5.0):
        flier = spawn_drifter(Placement(DrifterType.METEORITE, x=x), 1, TUNING)
        assert (flier.x, flier.y) == (x, -14.0)
        assert flier.warning_center() == (min(max(x, 12.0), 628.0), 12.0)
    placed = spawn_drifter(Placement(DrifterType.METEORITE, x=100.0, y=50.0), 1, TUNING)
    assert (placed.x, placed.y) == (100.0, 50.0)
    # A placement without x is refused, with or without y; the run is left as it was.
    for placement in (Placement(DrifterType.PLANET), Placement(DrifterType.PLANET, y=100.0)):
        with pytest.raises(ValueError, match="planet placement needs x"):
            spawn_drifter(placement, 1, TUNING)
        run = start_run()
        with pytest.raises(ValueError, match="planet placement needs x"):
            add_drifters(run, [placement], TUNING)
        assert run.drifters == ()
    with pytest.raises(ValueError, match="planet placement needs x"):
        Planet.start_position(None, 10.0, FIELD_BOX, FIELD_BOX, False)


def test_a_planet_stays_put_while_warning_then_moves_only_by_the_scroll_step() -> None:
    steps = [0.0, 0.0, 1.1, 1.1, 3.7, 0.0, 1.87, 1.1]
    ships = [spawn(), resting(0.0, 0.0), resting(500.0, 400.0), resting(318.0, 100.0)]
    for tuning in (TUNING, NO_SCALING):
        for level in (1, 8):
            where = (tuning is NO_SCALING, level)
            moving = planet(123.0, 50.0, as_level=level, tuning=tuning)
            # WARNING: the scroll never moves it, 59 states, then it turns ACTIVE in place.
            for index in range(WARNING_TICKS - 1):
                ship = ships[index % len(ships)]
                moving = moving.update(
                    TickContext(ship=ship, scroll_step_px=steps[index % len(steps)])
                )
                assert moving.phase is Phase.WARNING, (where, index)
                assert moving.ticks_in_phase == index + 1
                assert (moving.x, moving.y) == (123.0, 50.0)
            moving = moving.update(TickContext(ship=spawn(), scroll_step_px=1.1))
            assert moving.phase is Phase.ACTIVE
            assert moving.ticks_in_phase == 0
            assert (moving.x, moving.y) == (123.0, 50.0)
            # ACTIVE: down by the scroll step and nothing else, whatever the ship does.
            y = 50.0
            for index, step_px in enumerate(steps * 3):
                moving = moving.update(
                    TickContext(ship=ships[index % len(ships)], scroll_step_px=step_px)
                )
                y += step_px
                assert moving.y == pytest.approx(y, abs=1e-9), (where, index)
                assert moving.x == 123.0
                assert moving.ticks_in_phase == index + 1
                assert moving.phase is Phase.ACTIVE
            # A TickContext built with the ship alone is a world standing still.
            still = moving.update(TickContext(ship=spawn()))
            assert still.y == moving.y
            assert still.x == moving.x
    # GONE is left as it is, whatever the step.
    gone = replace(planet(123.0, 50.0), phase=Phase.GONE)
    assert gone.update(TickContext(ship=spawn(), scroll_step_px=1.1)) == gone
    # In a run, added at the end of tick T: still through T+59, ACTIVE at T+60 where it was
    # placed, then 1.1 a tick, as the starfield moves.
    run = add_drifters(
        replace(start_run(), scroll=SCROLLING), [Placement(DrifterType.PLANET, x=100.0)], TUNING
    )
    for tick in range(1, 80):
        run = step_run(replace(run, ship=FAR_LEFT), NO_KEY)
        (only,) = planets_of(run)
        assert only.x == 100.0
        assert only.speed == 0.0
        if tick < WARNING_TICKS:
            assert only.phase is Phase.WARNING
            assert only.y == START_Y
        else:
            assert only.phase is Phase.ACTIVE
            expected = START_Y + (tick - WARNING_TICKS) * SCROLL_SPEED
            assert only.y == pytest.approx(expected, abs=1e-9), tick
    # An ACTIVE planet before the scroll starts stands still for 30 ticks, then moves 1.1 a tick.
    run = run_of(FAR_LEFT, active(320.0, 100.0), scroll=STILL)
    for tick in range(1, 60):
        run = step_run(replace(run, ship=FAR_LEFT), NO_KEY)
        (only,) = planets_of(run)
        assert only.x == 320.0
        if tick <= SCROLL_START_DELAY:
            assert only.y == 100.0, tick
        else:
            expected = 100.0 + (tick - SCROLL_START_DELAY) * SCROLL_SPEED
            assert only.y == pytest.approx(expected, abs=1e-9), tick


def test_a_planet_refuses_invert_a_specialty_a_speed_a_missing_x_and_the_wrong_extras() -> None:
    placement = Placement(DrifterType.PLANET, x=320.0, invert=True)
    with pytest.raises(ValueError, match="planet has no invert"):
        spawn_drifter(placement, 1, TUNING)
    run = start_run()
    with pytest.raises(ValueError, match="planet has no invert"):
        add_drifters(run, [placement], TUNING)
    assert run.drifters == ()
    placement = Placement(DrifterType.PLANET, x=320.0, specialty_enabled=True)
    with pytest.raises(ValueError, match="planet has no specialty"):
        spawn_drifter(placement, 1, TUNING)
    with pytest.raises(ValueError, match="planet has no specialty"):
        add_drifters(run, [placement], TUNING)
    # A specialty switched off, or not given, is fine.
    assert planet().phase is Phase.WARNING
    off = Placement(DrifterType.PLANET, x=320.0, specialty_enabled=False)
    assert spawn_drifter(off, 1, TUNING).phase is Phase.WARNING
    # A speed is refused whatever it is, at any level.
    for speed in (0.0, 1.0, 4.5):
        for level in (1, 8):
            placement = Placement(DrifterType.PLANET, x=320.0, speed=speed)
            with pytest.raises(ValueError, match="planet has no speed"):
                spawn_drifter(placement, level, TUNING)
            with pytest.raises(ValueError, match="planet has no speed"):
                add_drifters(run, [placement], TUNING)
    # A missing x is a refusal of its own (see the start test); here it is also refused at a level.
    with pytest.raises(ValueError, match="planet placement needs x"):
        spawn_drifter(Placement(DrifterType.PLANET, as_level=5), 1, TUNING)
    # Tuning with no variant values or the wrong kind of them, and with no type values or the
    # wrong kind of them.
    wrong_variant = IslandVariantExtra(shape=IslandShape.RECTANGLE)
    for bad_variant in (None, wrong_variant):
        tuning = make_tuning(variant_extra=bad_variant)
        with pytest.raises(ValueError, match="planet variant 'standard' has no pull"):
            spawn_drifter(Placement(DrifterType.PLANET, x=320.0), 1, tuning)
        with pytest.raises(ValueError, match="planet variant 'standard' has no pull"):
            add_drifters(run, [Placement(DrifterType.PLANET, x=320.0)], tuning)
    for bad_type in (None, DrifterTypeExtra()):
        tuning = make_tuning(type_extra=bad_type)
        with pytest.raises(ValueError, match="planet tuning has no type values"):
            spawn_drifter(Placement(DrifterType.PLANET, x=320.0), 1, tuning)
        with pytest.raises(ValueError, match="planet tuning has no type values"):
            add_drifters(run, [Placement(DrifterType.PLANET, x=320.0)], tuning)
    assert run.drifters == ()


def test_gravity_well_is_none_in_warning_and_gone_and_the_field_at_the_center_while_active() -> (
    None
):
    waiting = planet(320.0, 100.0)
    assert waiting.phase is Phase.WARNING
    assert waiting.gravity_well() is None
    ready = active(320.0, 100.0)
    assert ready.gravity_well() == well_at(320.0, 100.0)
    assert ready.gravity_well() == GravityWell(320.0, 100.0, 32.0, 150.0, 0.2)
    # It follows the planet, wherever it is, even above the screen or below the floor.
    for x, y in ((0.0, 0.0), (640.0, 480.0), (123.5, -151.0), (50.0, 700.0)):
        assert active(x, y).gravity_well() == well_at(x, y)
    # The state that turns ACTIVE gives the field at once, and the last ACTIVE state still does.
    moving = planet(320.0, 100.0)
    for _ in range(WARNING_TICKS - 1):
        moving = moving.update(TickContext(ship=spawn()))
        assert moving.gravity_well() is None
    moving = moving.update(TickContext(ship=spawn()))
    assert moving.phase is Phase.ACTIVE
    assert moving.gravity_well() == well_at(320.0, 100.0)
    gone = replace(moving, phase=Phase.GONE)
    assert gone.gravity_well() is None
    # Every level and both switch sets give the same field.
    for tuning in (TUNING, NO_SCALING):
        for level in (1, 8):
            spawned = replace(
                planet(320.0, 100.0, as_level=level, tuning=tuning),
                phase=Phase.ACTIVE,
                ticks_in_phase=0,
            )
            assert spawned.gravity_well() == well_at(320.0, 100.0)
    # A meteorite has no field.
    assert rock(320.0, 100.0).gravity_well() is None


INNER_RING_TABLE: tuple[tuple[int, tuple[float, float], tuple[float, float]], ...] = (
    # t, ring 0 (radius, opacity), ring 1 (radius, opacity). Source: drifters.md, Diagram (the
    # inner field rings table): radius 150 - 118 k / 120, opacity 0.5 (1 - k / 120), the radius
    # to 2 decimals and the opacity to 4.
    (0, (150.00, 0.5000), (91.00, 0.2500)),
    (30, (120.50, 0.3750), (61.50, 0.1250)),
    (60, (91.00, 0.2500), (150.00, 0.5000)),
    (119, (32.98, 0.0042), (91.98, 0.2542)),
    (120, (150.00, 0.5000), (91.00, 0.2500)),
)


def exact_ring(t: int, index: int) -> tuple[Fraction, Fraction]:
    """Ring `index` on tick `t` of the ACTIVE phase, exact, from the file's values."""
    k = (t - index * RING_GAP) % RING_TRIP
    radius = Fraction(150) - Fraction(118) * k / RING_TRIP
    opacity = Fraction(1, 2) * (1 - Fraction(k, RING_TRIP))
    return radius, opacity


def test_inner_rings_give_the_tables_radii_and_opacities_and_nothing_outside_active() -> None:
    for t, ring_0, ring_1 in INNER_RING_TABLE:
        rings = replace(active(320.0, 100.0), ticks_in_phase=t).inner_rings()
        assert len(rings) == 2, t
        for ring, (radius, opacity) in zip(rings, (ring_0, ring_1), strict=True):
            assert ring.radius == pytest.approx(radius, abs=0.005), t
            assert ring.opacity == pytest.approx(opacity, abs=0.00005), t
    # The formula on many ticks, over three cycles, exact: both rings, and never outside
    # the surface and the field's edge or beyond half opacity.
    for t in range(3 * RING_TRIP + 1):
        rings = replace(active(320.0, 100.0), ticks_in_phase=t).inner_rings()
        for index, ring in enumerate(rings):
            exact_radius, exact_opacity = exact_ring(t, index)
            assert ring.radius == pytest.approx(float(exact_radius), abs=1e-9), (t, index)
            assert ring.opacity == pytest.approx(float(exact_opacity), abs=1e-12), (t, index)
            assert SURFACE < ring.radius <= PULL_RADIUS, (t, index)
            assert 0.0 < ring.opacity <= 0.5, (t, index)
    # The same through the clock: a planet turned ACTIVE and updated t times.
    moving = active(320.0, 100.0)
    for t in range(1, 125):
        moving = moving.update(TickContext(ship=spawn()))
        assert moving.ticks_in_phase == t
        for index, ring in enumerate(moving.inner_rings()):
            exact_radius, exact_opacity = exact_ring(t, index)
            assert ring.radius == pytest.approx(float(exact_radius), abs=1e-9), (t, index)
            assert ring.opacity == pytest.approx(float(exact_opacity), abs=1e-12), (t, index)
    # Outside ACTIVE there are none, whatever the tick.
    for phase in (Phase.WARNING, Phase.GONE):
        for t in (0, 30, 60, 119, 120):
            assert replace(active(320.0, 100.0), phase=phase, ticks_in_phase=t).inner_rings() == ()
    assert planet(320.0, 100.0).inner_rings() == ()
    # The rings never change with level or switches.
    for tuning in (TUNING, NO_SCALING):
        for level in (1, 8):
            leveled = replace(
                planet(320.0, 100.0, as_level=level, tuning=tuning),
                phase=Phase.ACTIVE,
                ticks_in_phase=30,
            )
            first, second = leveled.inner_rings()
            assert first.radius == pytest.approx(120.5)
            assert second.radius == pytest.approx(61.5)


def test_the_drawn_box_and_the_timeline_enter_keep_and_drop_the_planet_as_the_diagram_says(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    ctx = TickContext(ship=spawn(), scroll_step_px=SCROLL_SPEED)
    # The drawn box is the field ring's box, centered on the planet, in every phase.
    for phase in (Phase.WARNING, Phase.ACTIVE, Phase.GONE):
        shown = replace(planet(200.0, 300.0), phase=phase)
        assert shown.drawn_parts() == (Box(200.0, 300.0, FIELD_BOX, FIELD_BOX),)
    # The drifter alone. At T its box's bottom edge is on the top edge: not on screen.
    moving = replace(planet(320.0, None), phase=Phase.ACTIVE, ticks_in_phase=0)
    assert moving.y == START_Y
    assert not moving.is_partly_on_screen()
    assert not moving.mark_entered().has_entered
    assert not moving.is_off_screen()
    for n in range(1, 712):
        moving = moving.update(ctx).mark_entered()
        assert moving.has_entered, n
        assert moving.y == pytest.approx(START_Y + n * SCROLL_SPEED, abs=1e-9)
        # Its box's top edge is at 479.00 on n = 710 (kept) and 480.10 on n = 711 (dropped).
        assert moving.is_off_screen() == (n >= 711), n
    # In a run, with the world scrolling: the Diagram's timeline, state after state.
    run = replace(start_run(), scroll=SCROLLING)
    run = add_drifters(run, [Placement(DrifterType.PLANET, x=320.0)], TUNING)
    caplog.clear()
    for n in range(1, WARNING_TICKS + 712):
        run = step_run(replace(run, ship=FAR_LEFT), NO_KEY)
        if n < WARNING_TICKS:
            (only,) = planets_of(run)
            assert only.phase is Phase.WARNING, n
            assert only.ticks_in_phase == n
            assert not only.has_entered
            assert only.gravity_well() is None
            assert only.current_hitbox() == ()
        elif n == WARNING_TICKS:
            # T+60: ACTIVE, still above the screen, not entered, and the field already on.
            (only,) = planets_of(run)
            assert only.phase is Phase.ACTIVE
            assert only.ticks_in_phase == 0
            assert only.y == START_Y
            assert not only.has_entered
            assert only.gravity_well() == well_at(320.0, START_Y)
            assert only.current_hitbox() == (Circle(320.0, START_Y, SURFACE),)
        elif n < WARNING_TICKS + 711:
            # T+61 on: entered. T+770 (m = 710): kept, its box's top edge at 479.00.
            (only,) = planets_of(run)
            m = n - WARNING_TICKS
            assert only.phase is Phase.ACTIVE
            assert only.ticks_in_phase == m
            assert only.has_entered, n
            assert only.y == pytest.approx(START_Y + m * SCROLL_SPEED, abs=1e-9), n
        else:
            # T+771: dropped, with its field.
            assert run.drifters == ()
            assert gravity_wells(run.drifters) == ()
    assert [line for line in run_lines(caplog) if "gone" in line] == [
        "drifter gone id=1 type=planet x=320.00 y=631.10"
    ]
    # Placed on screen it shows there at once, and enters on its first ACTIVE update.
    spot = active(320.0, 240.0)
    assert spot.is_partly_on_screen()
    assert spot.update(ctx).mark_entered().has_entered
    # Placed half past a side wall it never leaves by the side: it never moves sideways. It goes
    # only below the floor, once its box's top edge is at or below it (y >= 631).
    for x in (0.0, 640.0):
        edge = active(x, 240.0)
        for n in range(1, 450):
            edge = edge.update(ctx).mark_entered()
            assert edge.x == x
            assert edge.has_entered
            assert edge.is_off_screen() == (edge.y - FIELD_BOX / 2 >= SCREEN_H), (x, n)
    # Never before it has entered: fully past a side from the start, or already below the floor,
    # it is not off screen on any state and the run never drops it.
    for x, y in ((-1000.0, 240.0), (1640.0, 240.0), (320.0, 800.0)):
        outside = active(x, y)
        for n in range(1, 300):
            outside = outside.update(ctx).mark_entered()
            assert not outside.has_entered, (x, y, n)
            assert not outside.is_off_screen(), (x, y, n)
        parked = add_drifters(
            replace(start_run(), scroll=SCROLLING),
            [Placement(DrifterType.PLANET, x=x, y=y)],
            TUNING,
        )
        for _ in range(WARNING_TICKS + 300):
            parked = step_run(replace(parked, ship=FAR_LEFT), NO_KEY)
        assert len(parked.drifters) == 1


def test_a_flying_ship_in_a_field_is_pulled_a_waiting_one_is_not_and_the_press_starts_it() -> None:
    # A planet at (320, 300) standing still (STILL), the ship level with it 100 px to the right
    # (inside the field, clear of the body), so the pull is straight left.
    well = well_at(320.0, 300.0)
    flying = Ship(x=420.0, y=300.0, vx=0.0, vy=0.0)
    wells = (well,)
    without = step(flying, NO_KEY, NO_GROUND)
    pulled = step(flying, NO_KEY, NO_GROUND, wells)
    assert pulled.vx < without.vx
    # Strength at 100 px: 0.2 (150 - 100) / 118, then drag 0.94 on x. Gravity is the same.
    assert pulled.vx == pytest.approx(-PULL_MAX * 50 / 118 * 0.94, abs=1e-12)
    assert pulled.vy == without.vy
    for protected in (False, True):
        run = run_of(
            flying, active(320.0, 300.0), invuln_ticks_left=INVULN_TICKS if protected else 0
        )
        after = step_run(run, NO_KEY)
        assert after.ship == pulled, protected
        assert after.ship != without
        assert after.lives == LIVES_START
    # Outside the field there is no pull.
    far = resting(320.0 + PULL_RADIUS + 1, 300.0)
    assert step_run(run_of(far, active(320.0, 300.0)), NO_KEY).ship == step(far, NO_KEY)
    # The field is where the planet has moved to on this tick: 1.1 px lower, with the world moving.
    scrolling = run_of(flying, active(320.0, 300.0), scroll=SCROLLING)
    moved = step_run(scrolling, NO_KEY)
    assert moved.ship == step(flying, NO_KEY, NO_GROUND, (well_at(320.0, 301.1),))
    assert moved.ship != step(flying, NO_KEY, NO_GROUND, wells)
    # A planet still in WARNING pulls nothing.
    held = run_of(flying, replace(planet(320.0, 300.0)), scroll=STILL)
    assert step_run(held, NO_KEY).ship == without
    # A ship standing in the respawn wait inside a field is not pulled: 60 ticks, still the
    # respawn spot, still waiting, no life lost, protected or not.
    for protected in (False, True):
        standing = run_of(
            spawn(),
            active(320.0, 330.0),
            waiting=True,
            invuln_ticks_left=1000 if protected else 0,
        )
        for tick in range(60):
            standing = step_run(replace(standing, scroll=STILL), NO_KEY)
            assert standing.waiting, tick
            assert standing.ship == spawn(), tick
            assert standing.lives == LIVES_START
        # The press that ends the wait steps the ship, with the pull and gravity on that tick.
        pressed = step_run(replace(standing, scroll=STILL), Thrust(up=True))
        assert not pressed.waiting
        expected = step(spawn(), Thrust(up=True), NO_GROUND, (well_at(320.0, 330.0),))
        assert pressed.ship == expected
        assert pressed.ship != step(spawn(), Thrust(up=True), NO_GROUND)
        # It keeps being pulled on the next ticks.
        after_press = step_run(replace(pressed, ship=resting(420.0, 330.0), scroll=STILL), NO_KEY)
        assert after_press.ship == step(
            resting(420.0, 330.0), NO_KEY, NO_GROUND, (well_at(320.0, 330.0),)
        )


def test_touching_the_body_is_one_hit_then_the_cooldown_holds_even_with_the_pull_on_the_ship() -> (
    None
):
    # Inside the field but clear of the body (100 px away): never a hit, no cooldown. The ship
    # is put back each tick so it stays there.
    clear = run_of(resting(420.0, 300.0), active(320.0, 300.0))
    for _ in range(10):
        clear = step_run(replace(clear, ship=resting(420.0, 300.0)), NO_KEY)
        assert clear.lives == LIVES_START
        assert planets_of(clear)[0].rehit_ticks_left == 0
        assert clear.invuln_ticks_left == 0
    # Touching the body: one hit on the first tick, one life, the cooldown starts, the invulnerable
    # blink starts, the planet stays. The ship sits 10 px below the center, inside the body, and
    # the pull (0.2 at the surface) and gravity (0.16) keep it moving inside the body. The scroll
    # is put back to still each tick so the planet stands where it is.
    run = run_of(resting(320.0, 310.0), active(320.0, 300.0))
    run = step_run(run, NO_KEY)
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    (hit,) = planets_of(run)
    assert hit.rehit_ticks_left == REHIT_COOLDOWN
    assert hit.phase is Phase.ACTIVE
    assert not run.game_over
    # Ticks 2 to 181: the planet can't hit again, protected for the first 30, then not. The pull
    # holds the ship against the body the whole time.
    for tick in range(2, REHIT_COOLDOWN + 2):
        run = step_run(replace(run, scroll=STILL), NO_KEY)
        assert hitboxes_overlap(ship_hitbox(run.ship), planets_of(run)[0].current_hitbox()), tick
        assert run.lives == LIVES_START - 1, tick
        assert not run.game_over
        expected_left = REHIT_COOLDOWN - (tick - 1)
        assert planets_of(run)[0].rehit_ticks_left == expected_left, tick
    assert run.invuln_ticks_left == 0
    # Tick 182: the cooldown is over and the ship is still on the body: a second hit.
    run = step_run(replace(run, scroll=STILL), NO_KEY)
    assert run.lives == LIVES_START - 2
    assert planets_of(run)[0].rehit_ticks_left == REHIT_COOLDOWN
    assert run.invuln_ticks_left == INVULN_TICKS


def test_gravity_wells_holds_every_active_planets_field_in_drifter_order() -> None:
    first = replace(active(100.0, 200.0), uid=1)
    warning = replace(planet(250.0, 150.0), uid=2)
    flier = replace(rock(200.0, 200.0), uid=3)
    gone = replace(active(300.0, 300.0), uid=4, phase=Phase.GONE)
    second = replace(active(500.0, 300.0), uid=5)
    drifters: tuple[Drifter, ...] = (first, warning, flier, gone, second)
    expected = (well_at(100.0, 200.0), well_at(500.0, 300.0))
    assert gravity_wells(drifters) == expected
    assert isinstance(gravity_wells(drifters), tuple)
    # The order is the drifters' order.
    assert gravity_wells(tuple(reversed(drifters))) == (expected[1], expected[0])
    # A moved planet moves its field.
    moved = replace(second, y=310.0)
    assert gravity_wells((moved,)) == (well_at(500.0, 310.0),)
    # With none, or none ACTIVE, there are no wells.
    assert gravity_wells(()) == ()
    assert gravity_wells((flier,)) == ()
    assert gravity_wells((warning, gone, flier)) == ()
    # Two planets on the field give two wells to the step, and the ship feels the sum.
    pair = run_of(resting(320.0, 300.0), active(220.0, 300.0), active(420.0, 300.0))
    both = step_run(pair, NO_KEY)
    wells = (well_at(220.0, 300.0), well_at(420.0, 300.0))
    assert both.ship == step(resting(320.0, 300.0), NO_KEY, NO_GROUND, wells)


def test_a_planet_logs_spawn_active_each_hit_and_gone_and_nothing_for_its_pull(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    run = replace(start_run(), scroll=SCROLLING)
    run = add_drifters(run, [Placement(DrifterType.PLANET, x=320.0)], TUNING)
    # The ship is put back at (320, 240) every tick, so the planet falls onto it, pulls it from
    # T+280, hits it once (the body passes in about 87 ticks, less than the cooldown), and is
    # dropped at T+771.
    for _ in range(WARNING_TICKS + 711):
        run = step_run(replace(run, ship=resting(320.0, 240.0)), NO_KEY)
    assert run.drifters == ()
    assert run.lives == LIVES_START - 1
    assert run_lines(caplog) == [
        "drifter spawn id=1 type=planet variant=standard x=320.00 y=-151.00 speed=0.00 level=1",
        "drifter active id=1 type=planet x=320.00 y=-151.00",
        "drifter touch id=1 type=planet effect=hit",
        "life lost lives=2",
        "invulnerable end",
        "drifter gone id=1 type=planet x=320.00 y=631.10",
    ]
    # Nothing under core.drifters, core.ship, core.collision or core.popup logs: the pull and
    # the field are silent.
    assert {r.name for r in caplog.records} == {RUN_LOGGER}
