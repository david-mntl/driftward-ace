"""The meteorite's drawn box and rule 12 (leaving): a rock stays until nothing of it is drawn.

Direct-edit feature `drifter-sprites` (no contract): `Meteorite.drawn_parts()` returns one box
centered on the rock, `drawn_width` square (at least the footprint), so the rock stays on screen
until its drawn art has left, not only its footprint. Source: 07-drifters.md, rule 12 (fully off
screen means nothing drawn is still on screen; at a side or the floor, never the top); the
implementation report, `## Meteorite`.

The tuning is built here, never read from game/tuning/. Sizes: small 20, medium 28, big 40 wide
(drifters/01-meteorite.md, size); drawn widths 26, 36, 52 (the report: width x 36 / 28, rounded up).
The screen is 640 x 480 (03-world-and-camera.md, screen_w, screen_h). A box that only touches the
floor or a side from the inside counts as past it (the base class's rule, 07-drifters.md rule 12).
"""

from dataclasses import replace

import pytest

from core.collision import Box, Circle
from core.drifters.base import DrifterType, Phase, TickContext
from core.drifters.meteorite import Meteorite, MeteoriteVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.ship import spawn

SCREEN_W = 640.0
SCREEN_H = 480.0
SIZES: dict[str, tuple[float, float]] = {
    "small": (20.0, 26.0),
    "medium": (28.0, 36.0),
    "big": (40.0, 52.0),
}
"""variant: (width, drawn width)."""
CTX = TickContext(ship=spawn())


def _tuning(*, extra: bool = True, drawn_scale: float = 1.0) -> DrifterTuning:
    variants = {
        name: VariantTuning(
            width=width,
            height=width,
            hitbox=(Circle(0.0, 0.0, width / 2),),
            extra=MeteoriteVariantExtra(drawn_width=drawn * drawn_scale) if extra else None,
        )
        for name, (width, drawn) in SIZES.items()
    }
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants=variants,
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            )
        },
        switches=PlaytestSwitches(),
    )


TUNING = _tuning()


def _rock(
    variant: str, x: float, y: float, *, tuning: DrifterTuning = TUNING, entered: bool = True
) -> Meteorite:
    """The rock, ACTIVE at (x, y), and entered unless told otherwise."""
    born = spawn_drifter(Placement(DrifterType.METEORITE, x=x, y=y, variant=variant), 1, tuning)
    assert isinstance(born, Meteorite)
    return replace(born, phase=Phase.ACTIVE, has_entered=entered)


@pytest.mark.parametrize("variant", list(SIZES))
def test_the_drawn_box_is_one_box_drawn_width_square_centered_on_the_rock(variant: str) -> None:
    width, drawn = SIZES[variant]
    for x, y in ((320.0, 240.0), (12.5, -30.0), (600.25, 470.75)):
        rock = _rock(variant, x, y)
        assert rock.drawn_parts() == (Box(x, y, drawn, drawn),)
        assert rock.width == width


def test_the_drawn_box_is_never_smaller_than_the_footprint() -> None:
    for variant, (width, _) in SIZES.items():
        for tuning in (_tuning(extra=False), _tuning(drawn_scale=0.1)):
            rock = _rock(variant, 100.0, 100.0, tuning=tuning)
            assert rock.drawn_parts() == (Box(100.0, 100.0, width, width),), variant


@pytest.mark.parametrize("variant", list(SIZES))
def test_a_rock_whose_footprint_is_below_the_floor_stays_while_its_drawn_box_is_on_screen(
    variant: str,
) -> None:
    width, drawn = SIZES[variant]
    footprint_clear = SCREEN_H + width / 2
    drawn_clear = SCREEN_H + drawn / 2
    # Footprint fully below the floor (touching counts), drawn box still over it.
    for y in (footprint_clear, footprint_clear + 0.5, drawn_clear - 0.5, drawn_clear - 0.01):
        rock = _rock(variant, 320.0, y)
        assert rock.y - width / 2 >= SCREEN_H, "the footprint is fully below the floor"
        assert rock.is_partly_on_screen(), y
        assert not rock.is_off_screen(), y
    # The drawn box has left: touching the floor counts as left, and so does anything below.
    for y in (drawn_clear, drawn_clear + 0.01, drawn_clear + 40.0):
        assert _rock(variant, 320.0, y).is_off_screen(), y


@pytest.mark.parametrize("variant", list(SIZES))
def test_a_rock_past_a_side_stays_until_its_drawn_box_is_past_it(variant: str) -> None:
    width, drawn = SIZES[variant]
    # Left: x + w / 2 <= 0 is past. Right: x - w / 2 >= 640 is past. `inward` points to the screen.
    for edge, outward in ((0.0, -1.0), (SCREEN_W, 1.0)):
        x_foot = edge + outward * width / 2
        x_drawn = edge + outward * drawn / 2
        inward = -outward
        for x in (x_foot, x_foot + inward * 0.5, x_drawn + inward * 0.5, x_drawn + inward * 0.01):
            assert not _rock(variant, x, 240.0).is_off_screen(), (variant, x)
        for x in (x_drawn, x_drawn + outward * 0.01, x_drawn + outward * 30.0):
            assert _rock(variant, x, 240.0).is_off_screen(), (variant, x)


@pytest.mark.parametrize("variant", list(SIZES))
def test_a_rock_is_never_removed_at_the_top_or_before_it_has_entered(variant: str) -> None:
    for y in (-500.0, -SIZES[variant][1], -SIZES[variant][1] / 2):
        assert not _rock(variant, 320.0, y).is_off_screen()
    for x, y in ((-500.0, 240.0), (900.0, 240.0), (320.0, 900.0)):
        assert not _rock(variant, x, y, entered=False).is_off_screen()


@pytest.mark.parametrize("variant", list(SIZES))
def test_a_falling_rock_is_dropped_the_tick_its_drawn_box_clears_the_floor(variant: str) -> None:
    """Falls 2 px a tick from just above the floor: the footprint clears the floor
    (y - w / 2 >= 480) some ticks before the drawn box does (y - drawn / 2 >= 480)."""
    width, drawn = SIZES[variant]
    speed = 2.0
    born = spawn_drifter(
        Placement(DrifterType.METEORITE, x=320.0, y=440.0, variant=variant, speed=speed), 1, TUNING
    )
    assert isinstance(born, Meteorite)
    rock = replace(born, phase=Phase.ACTIVE)
    assert rock.speed == speed
    footprint_tick = drawn_tick = None
    for tick in range(1, 100):
        rock = rock.update(CTX).mark_entered()
        if footprint_tick is None and rock.y - width / 2 >= SCREEN_H:
            footprint_tick = tick
        if rock.is_off_screen():
            drawn_tick = tick
            break
    assert footprint_tick is not None
    assert drawn_tick is not None
    expected_foot = -(-(SCREEN_H + width / 2 - 440.0) // speed)
    expected_drawn = -(-(SCREEN_H + drawn / 2 - 440.0) // speed)
    assert footprint_tick == expected_foot
    assert drawn_tick == expected_drawn
    assert drawn_tick > footprint_tick, "the drawn box outlasts the footprint"


@pytest.mark.parametrize("level", [1, 4, 8])
@pytest.mark.parametrize("variant", list(SIZES))
def test_a_rock_with_no_y_starts_with_its_whole_drawn_box_just_above_the_top_edge(
    variant: str, level: int
) -> None:
    """Rule 14 (07-drifters.md): starts fully off screen, touching the edge, by what is drawn."""
    width, drawn = SIZES[variant]
    born = spawn_drifter(Placement(DrifterType.METEORITE, x=100.0, variant=variant), level, TUNING)
    assert isinstance(born, Meteorite)
    assert (born.x, born.y) == (100.0, -drawn / 2)
    (box,) = born.drawn_parts()
    assert box.cy + box.h / 2 == 0.0, "the drawn box's bottom edge is on the top edge"
    assert not born.is_partly_on_screen()
    assert born.width == width, "the footprint is not changed"
    active = replace(born, phase=Phase.ACTIVE).mark_entered()
    assert not active.is_partly_on_screen()
    assert not active.has_entered
    # One px of fall puts the drawn box on screen.
    moved = replace(active, y=active.y + 1.0).mark_entered()
    assert moved.is_partly_on_screen()
    assert moved.has_entered


@pytest.mark.parametrize("variant", list(SIZES))
def test_a_rock_with_no_drawn_width_starts_by_its_footprint_and_a_placed_y_is_kept(
    variant: str,
) -> None:
    width, _ = SIZES[variant]
    plain = spawn_drifter(
        Placement(DrifterType.METEORITE, x=100.0, variant=variant), 1, _tuning(extra=False)
    )
    assert plain.y == -width / 2
    for y in (50.0, 0.0, -100.0, 479.5):
        placed = spawn_drifter(
            Placement(DrifterType.METEORITE, x=100.0, y=y, variant=variant), 1, TUNING
        )
        assert (placed.x, placed.y) == (100.0, y)
