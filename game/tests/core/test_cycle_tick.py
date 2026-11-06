"""`cycle_tick()` of the electric ball and the chain lightning: the public name of the old
private `_cycle_tick`, with the same values and the same charge and fire boundaries.

Direct-edit feature `drifter-sprites` (no contract): the views call `cycle_tick()` for the charge
animation instead of copying the formula. Expected values are the old method's, written out here:
the tick within the cycle is `ticks_in_phase % (charge_ticks + fire_ticks)`; a drifter charges
while that is under `charge_ticks`, fires from `charge_ticks` on; the charge rays are
1 + cycle_tick x charge_rays // charge_ticks. Values: drifters/10-electric-ball.md (charge 120,
fire 120, 4 rays, pulse 64, ball 16), game/tuning/drifters/chain_lightning.json (charge 90, fire
80, 4 rays; the file's own values, so the two lengths differ and a swapped formula shows),
08-difficulty.md (Timer x 0.70 at Level 8: 120 x 0.70 = 84).

The tuning is built here and no file under game/tuning/ is read.
"""

from dataclasses import replace

import pytest

from core.collision import Circle, Line
from core.drifters.base import Drifter, DrifterType, Phase
from core.drifters.chain_lightning import (
    ChainLayout,
    ChainLightning,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    InvertMirror,
)
from core.drifters.electric_ball import (
    ElectricBall,
    ElectricBallTypeExtra,
    ElectricBallVariantExtra,
)
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)

BALL_CHARGE = 120
BALL_FIRE = 120
BALL_CHARGE_LEVEL_8 = 84
CHAIN_CHARGE = 90
CHAIN_FIRE = 80
RAYS = 4
WARNING_TICKS = 60

PAIR_FLAT = ChainLayout(
    nodes=((-64.0, 0.0), (64.0, 0.0)), arcs=((0, 1),), invert_mirror=InvertMirror.LEFT_RIGHT
)


def _tuning() -> DrifterTuning:
    return DrifterTuning(
        drifters={
            DrifterType.ELECTRIC_BALL: DrifterTypeTuning(
                variants={
                    "standard": VariantTuning(
                        width=16.0,
                        height=16.0,
                        hitbox=(Circle(0.0, 0.0, 64.0),),
                        extra=ElectricBallVariantExtra(pulse_radius=64.0),
                    )
                },
                default_variant="standard",
                speed_ratio=0.375,
                entry_warning_ticks=WARNING_TICKS,
                extra=ElectricBallTypeExtra(
                    charge_ticks=BALL_CHARGE,
                    fire_ticks=BALL_FIRE,
                    charge_rays=RAYS,
                    ray_length=6.0,
                    ray_width=1.0,
                    outline_width=1.0,
                    rim_width=2.0,
                    fill_opacity=0.35,
                ),
            ),
            DrifterType.CHAIN_LIGHTNING: DrifterTypeTuning(
                variants={
                    "pair_flat": VariantTuning(
                        width=140.0,
                        height=12.0,
                        hitbox=(
                            Line(-64.0, 0.0, 64.0, 0.0, 6),
                            Circle(-64.0, 0.0, 6.0),
                            Circle(64.0, 0.0, 6.0),
                        ),
                        extra=ChainLightningVariantExtra(layout=PAIR_FLAT),
                    )
                },
                default_variant="pair_flat",
                speed_ratio=0.09,
                entry_warning_ticks=WARNING_TICKS,
                extra=ChainLightningTypeExtra(
                    node_size=12.0,
                    arc_width=6.0,
                    charge_ticks=CHAIN_CHARGE,
                    fire_ticks=CHAIN_FIRE,
                    charge_rays=RAYS,
                    ray_length=6.0,
                    ray_width=1.0,
                    warning_layout=PAIR_FLAT,
                ),
            ),
        },
        switches=PlaytestSwitches(),
    )


TUNING: DrifterTuning = _tuning()


def _active(kind: DrifterType, level: int, ticks: int) -> Drifter:
    """The drifter, ACTIVE and on screen, `ticks` into its phase."""
    born = spawn_drifter(Placement(kind, x=320.0, y=240.0), level, TUNING)
    return replace(born, phase=Phase.ACTIVE, ticks_in_phase=ticks)


def _check_cycle(kind: DrifterType, level: int, charge: int, fire: int) -> None:
    cycle = charge + fire
    seen: set[int] = set()
    for ticks in range(3 * cycle + 7):
        drifter = _active(kind, level, ticks)
        assert isinstance(drifter, ElectricBall | ChainLightning)
        assert drifter.charge_ticks == charge
        assert drifter.fire_ticks == fire
        inside = ticks % cycle
        seen.add(inside)
        assert drifter.cycle_tick() == inside, ticks
        assert drifter.is_charging() == (inside < charge), ticks
        assert drifter.is_firing() == (inside >= charge), ticks
        rays = 1 + inside * RAYS // charge if inside < charge else 0
        assert drifter.charge_ray_count() == rays, ticks
    assert seen == set(range(cycle))


@pytest.mark.parametrize(("level", "charge"), [(1, BALL_CHARGE), (8, BALL_CHARGE_LEVEL_8)])
def test_the_electric_ball_cycle_tick_counts_through_charge_then_fire_and_wraps(
    level: int, charge: int
) -> None:
    _check_cycle(DrifterType.ELECTRIC_BALL, level, charge, BALL_FIRE)


def test_the_chain_lightning_cycle_tick_counts_through_charge_then_fire_and_wraps() -> None:
    _check_cycle(DrifterType.CHAIN_LIGHTNING, 1, CHAIN_CHARGE, CHAIN_FIRE)


@pytest.mark.parametrize(
    ("kind", "charge", "fire"),
    [
        (DrifterType.ELECTRIC_BALL, BALL_CHARGE, BALL_FIRE),
        (DrifterType.CHAIN_LIGHTNING, CHAIN_CHARGE, CHAIN_FIRE),
    ],
)
def test_the_charge_and_fire_boundaries_sit_on_the_tick_the_cycle_says(
    kind: DrifterType, charge: int, fire: int
) -> None:
    cycle = charge + fire
    cases = [
        (0, True),
        (charge - 1, True),
        (charge, False),
        (cycle - 1, False),
        (cycle, True),
        (cycle + charge - 1, True),
        (cycle + charge, False),
        (2 * cycle - 1, False),
        (2 * cycle, True),
    ]
    for ticks, charging in cases:
        drifter = _active(kind, 1, ticks)
        assert isinstance(drifter, ElectricBall | ChainLightning)
        assert drifter.is_charging() is charging, ticks
        assert drifter.is_firing() is (not charging), ticks
        assert drifter.cycle_tick() == ticks % cycle


@pytest.mark.parametrize("kind", [DrifterType.ELECTRIC_BALL, DrifterType.CHAIN_LIGHTNING])
def test_a_drifter_in_its_warning_neither_charges_nor_fires(kind: DrifterType) -> None:
    for ticks in (0, 10, 119, 120, 200):
        born = spawn_drifter(Placement(kind, x=320.0, y=240.0), 1, TUNING)
        waiting = replace(born, phase=Phase.WARNING, ticks_in_phase=ticks)
        assert isinstance(waiting, ElectricBall | ChainLightning)
        assert not waiting.is_charging()
        assert not waiting.is_firing()
        assert waiting.charge_ray_count() == 0
