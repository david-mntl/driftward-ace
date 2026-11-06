"""The level-up moment's motion: pure functions from an age to a share, an offset or a scale.

Source: docs/contracts/systems/level-up/view.md, Interface (``ui/level_up_motion.py``) and
Presentation. Ages and elapsed ticks are ints, every share is a float from 0 to 1. No state, no
pygame: the views call these once per frame with ``banner.age_ticks``.

Two curves, both exact at their end points (0 gives 0, 1 gives 1): ``_smooth`` is a smoothstep
(``3t^2 - 2t^3``, slow at both ends) and ``_ease_out`` a cubic ease-out (``1 - (1 - t)^3``, fast
first, then settling). The contract only says "eased" and names the end points; the choice of curve
is the Architect's call (task DRA-148-03, Not in the contract).
"""

import logging

from ui.level_up_rules import BandLook, BumpLook, FlyLook, NumberLook, PopLook

log = logging.getLogger(__name__)

type Point = tuple[float, float]


def _ramp(value: float, start: float, end: float) -> float:
    """Return 0 up to ``start``, a straight ramp to 1 at ``end``, 1 from ``end`` on."""
    if value <= start:
        return 0.0
    if value >= end:
        return 1.0
    return (value - start) / (end - start)


def _smooth(share: float) -> float:
    """Smoothstep of a share 0..1."""
    return share * share * (3.0 - 2.0 * share)


def _ease_out(share: float) -> float:
    """Cubic ease-out of a share 0..1."""
    return 1.0 - (1.0 - share) ** 3


def _mix(first: float, second: float, share: float) -> float:
    """Blend two values; share 0 gives ``first`` and share 1 gives ``second`` exactly."""
    return first * (1.0 - share) + second * share


def fade_share(age: int, start: int, end: int) -> float:
    """Return 0 up to ``start``, a straight ramp to 1 at ``end``, 1 after. Used for every fade."""
    return _ramp(age, start, end)


def band_shares(age: int, band: BandLook) -> tuple[float, float]:
    """Return (glass share, line share) of the band at ``age``, each 0..1, eased with smoothstep.

    Both rise from 0 at ``open_start`` to 1 at ``open_end`` and stay 1 until ``close_start``. In the
    closing window the glass falls to 0 over its first ``close_glass_share`` and the lines stay 1
    until then, then fall to 0 by ``close_end``. 0 before ``open_start`` and after ``close_end``.
    """
    opened: float = _smooth(_ramp(age, band.open_start, band.open_end))
    glass_end: float = (
        band.close_start + (band.close_end - band.close_start) * band.close_glass_share
    )
    glass_closed: float = _smooth(_ramp(age, band.close_start, glass_end))
    lines_closed: float = _smooth(_ramp(age, glass_end, band.close_end))
    return opened * (1.0 - glass_closed), opened * (1.0 - lines_closed)


def fall_offset(age: int, number: NumberLook, distance_px: float) -> float:
    """Return the number's y offset from its resting center, px, y down.

    -``distance_px`` up to ``fall_start``. Then a cubic ease-out to ``fall_overshoot_px`` past its
    place at ``fall_peak_share`` of the fall, a smoothstep back to 0 by ``fall_end``, 0 after.
    """
    if age >= number.fall_end:
        return 0.0
    share: float = _ramp(age, number.fall_start, number.fall_end)
    peak: float = number.fall_peak_share
    if share <= peak:
        return _mix(-distance_px, number.fall_overshoot_px, _ease_out(share / peak))
    return _mix(number.fall_overshoot_px, 0.0, _smooth((share - peak) / (1.0 - peak)))


def pose_scales(age: int, number: NumberLook) -> tuple[float, float]:
    """Return the number's (scale x, scale y): stretched while it falls, squashed on landing.

    Before ``fall_end``: (``fall_stretch_x``, ``fall_stretch_y``). On ``fall_end``: (``squash_x``,
    ``squash_y``), a cubic ease-out back to (1, 1) over ``squash_ticks``. (1, 1) after.
    """
    if age < number.fall_end:
        return number.fall_stretch_x, number.fall_stretch_y
    settled: float = _ease_out(_ramp(age - number.fall_end, 0, number.squash_ticks))
    return _mix(number.squash_x, 1.0, settled), _mix(number.squash_y, 1.0, settled)


def bump_offset(age: int, number: NumberLook, bump: BumpLook) -> int:
    """Return the whole px the play area's picture is moved down, never negative.

    0 before ``fall_end`` and from ``fall_end + bump.ticks`` on. Between, a cubic ease-out from 0 to
    ``bump.pixels`` by ``bump.peak_share`` of the bump, then a smoothstep back to 0. 0 always when
    ``bump.pixels`` is 0.
    """
    elapsed: int = age - number.fall_end
    if elapsed < 0 or elapsed >= bump.ticks:
        return 0
    share: float = elapsed / bump.ticks
    if share <= bump.peak_share:
        depth: float = _ease_out(share / bump.peak_share)
    else:
        depth = 1.0 - _smooth((share - bump.peak_share) / (1.0 - bump.peak_share))
    return max(0, round(bump.pixels * depth))


def fly_share(age: int, fly: FlyLook, arrival_ticks: int) -> float:
    """Return the flight's progress 0..1: 0 up to ``fly.start``, a smoothstep to 1 at arrival."""
    return _smooth(_ramp(age, fly.start, arrival_ticks))


def fly_position(share: float, start: Point, end: Point, arc_px: float) -> Point:
    """Return the point ``share`` along a quadratic curve from ``start`` to ``end``, px.

    The control point is the midpoint moved up by ``arc_px`` (y down). Share 0 is ``start`` and
    share 1 is ``end``, exactly.
    """
    control: Point = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0 - arc_px)
    first: float = (1.0 - share) ** 2
    second: float = 2.0 * (1.0 - share) * share
    third: float = share**2
    return (
        first * start[0] + second * control[0] + third * end[0],
        first * start[1] + second * control[1] + third * end[1],
    )


def pop_scale(elapsed: int, pop: PopLook) -> float:
    """Return the HUD number's size multiple ``elapsed`` ticks after arrival.

    ``start_scale`` at 0, a smoothstep down to ``undershoot_scale`` at ``undershoot_share`` of
    ``pop.ticks``, a smoothstep up to 1.0 at ``pop.ticks``, 1.0 from there on. Never above
    ``start_scale``.
    """
    if elapsed >= pop.ticks:
        return 1.0
    share: float = _ramp(elapsed, 0, pop.ticks)
    low: float = pop.undershoot_share
    if share <= low:
        return _mix(pop.start_scale, pop.undershoot_scale, _smooth(share / low))
    return _mix(pop.undershoot_scale, 1.0, _smooth((share - low) / (1.0 - low)))
