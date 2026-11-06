"""Level-up motion tests. Contract: docs/contracts/systems/level-up/view.md, Interface
(`ui/level_up_motion.py`) and Presentation (the banner, the flight, the bump, the HUD pop).

The functions are pure: an age in, a share, an offset or a scale out. The looks below are written
here, to the shape of docs/contracts/schemas/level-up.schema.json, and none is read from
tuning/level_up.json. Every expected number is an end point the contract names (0, 1, a field of
the look) or a straight consequence of one.
"""

import dataclasses
from itertools import pairwise

import pytest

from ui.level_up_motion import (
    band_shares,
    bump_offset,
    fall_offset,
    fly_position,
    fly_share,
    pop_scale,
    pose_scales,
)
from ui.level_up_rules import BandLook, BumpLook, FlyLook, NumberLook, PopLook

BAND = BandLook(
    height=100,
    alpha=100,
    center_offset_y=0,
    open_start=3,
    open_end=13,
    close_start=90,
    close_end=120,
    close_glass_share=0.6,
    hairline_width=1,
    corner_tick_length=6,
)
"""Test-local values that obey the schema: open_start < open_end <= close_start < close_end."""

NUMBER = NumberLook(
    font_size=80,
    outline_width=2,
    center_offset_y=0,
    fall_start=4,
    fall_end=20,
    fall_overshoot_px=8.0,
    fall_peak_share=0.7,
    fall_stretch_x=0.9,
    fall_stretch_y=1.1,
    squash_ticks=6,
    squash_x=1.25,
    squash_y=0.8,
    pose_steps=4,
)

BUMP = BumpLook(pixels=4, ticks=12, peak_share=0.3)

FLY = FlyLook(start=90, arc_px=30.0, steps=8)

POP = PopLook(
    ticks=20,
    start_scale=1.4,
    undershoot_scale=0.9,
    undershoot_share=0.5,
    flash_ticks=12,
    steps=10,
    bar_flash_ticks=16,
    box_flash_ticks=18,
    box_flash_width=1,
    box_corner_cut=8,
)

ARRIVAL: int = 110
"""The arrival age used with `FLY`. Above `FLY.start`."""

EPS: float = 1e-9


# ----- the bump -----


BUMPS = [
    BUMP,
    dataclasses.replace(BUMP, pixels=1),
    dataclasses.replace(BUMP, pixels=10, ticks=30, peak_share=0.1),
    dataclasses.replace(BUMP, pixels=7, ticks=9, peak_share=0.9),
    dataclasses.replace(BUMP, pixels=3, ticks=14, peak_share=0.25),
]
NUMBERS = [
    NUMBER,
    dataclasses.replace(NUMBER, fall_start=0, fall_end=2),
    dataclasses.replace(NUMBER, fall_start=10, fall_end=40),
]


@pytest.mark.parametrize("bump", BUMPS)
@pytest.mark.parametrize("number", NUMBERS)
def test_the_bump_is_zero_before_the_landing_and_after_it_and_reaches_its_pixels(
    number: NumberLook, bump: BumpLook
) -> None:
    last_age = number.fall_end + bump.ticks + 20
    offsets = [bump_offset(age, number, bump) for age in range(last_age)]
    for age in range(number.fall_end):
        assert offsets[age] == 0, age
    for age in range(number.fall_end + bump.ticks, last_age):
        assert offsets[age] == 0, age
    assert all(isinstance(offset, int) and offset >= 0 for offset in offsets)
    assert max(offsets) == bump.pixels
    assert max(offsets) == max(offsets[number.fall_end : number.fall_end + bump.ticks])


@pytest.mark.parametrize("bump", BUMPS)
def test_a_bump_of_zero_pixels_never_moves_the_picture(bump: BumpLook) -> None:
    none = dataclasses.replace(bump, pixels=0)
    for age in range(NUMBER.fall_end + none.ticks + 20):
        assert bump_offset(age, NUMBER, none) == 0, age


def test_the_bump_depends_on_the_age_alone() -> None:
    first = [bump_offset(age, NUMBER, BUMP) for age in range(60)]
    second = [bump_offset(age, NUMBER, BUMP) for age in range(60)]
    assert first == second


# ----- the band -----


BANDS = [
    BAND,
    dataclasses.replace(BAND, close_glass_share=0.2),
    dataclasses.replace(BAND, close_glass_share=0.9),
    dataclasses.replace(BAND, open_start=0, open_end=1, close_start=2, close_end=3),
    dataclasses.replace(BAND, open_start=0, open_end=10, close_start=100, close_end=124),
]


@pytest.mark.parametrize("band", BANDS)
def test_the_band_is_shut_before_opening_and_after_closing_and_open_between(
    band: BandLook,
) -> None:
    for age in range(band.open_start + 1):
        assert band_shares(age, band) == (0.0, 0.0), age
    for age in range(band.close_end, band.close_end + 20):
        assert band_shares(age, band) == (0.0, 0.0), age
    for age in range(band.open_end, band.close_start + 1):
        assert band_shares(age, band) == (1.0, 1.0), age
    for age in range(band.close_end + 20):
        glass, lines = band_shares(age, band)
        assert 0.0 <= glass <= 1.0, age
        assert 0.0 <= lines <= 1.0, age


@pytest.mark.parametrize("band", BANDS)
def test_the_band_rises_while_opening_and_the_glass_closes_before_the_lines(
    band: BandLook,
) -> None:
    opening = [band_shares(age, band) for age in range(band.open_start, band.open_end + 1)]
    for before, after in pairwise(opening):
        assert after[0] >= before[0]
        assert after[1] >= before[1]
        assert after[0] == after[1]
    closing = [band_shares(age, band) for age in range(band.close_start, band.close_end + 1)]
    for before, after in pairwise(closing):
        assert after[0] <= before[0]
        assert after[1] <= before[1]
    glass_end = band.close_start + (band.close_end - band.close_start) * band.close_glass_share
    for age in range(band.close_start, band.close_end + 1):
        glass, lines = closing[age - band.close_start]
        assert glass <= lines + EPS, age
        if age <= glass_end:
            assert lines == 1.0, age
        if age >= glass_end:
            assert glass == 0.0, age
    glass_gone = [
        age
        for age in range(band.close_start, band.close_end + 1)
        if closing[age - band.close_start][0] == 0.0
    ]
    lines_gone = [
        age
        for age in range(band.close_start, band.close_end + 1)
        if closing[age - band.close_start][1] == 0.0
    ]
    if band.close_end - band.close_start > 2:
        assert glass_gone[0] < lines_gone[0]
    assert lines_gone[0] <= band.close_end


# ----- the number's fall -----


DISTANCES = [100.0, 240.5, 1.0]


@pytest.mark.parametrize("distance", DISTANCES)
@pytest.mark.parametrize("number", NUMBERS)
def test_the_number_is_exactly_at_rest_from_the_landing_and_above_the_play_area_before_the_fall(
    number: NumberLook, distance: float
) -> None:
    for age in range(number.fall_end, number.fall_end + 40):
        assert fall_offset(age, number, distance) == 0.0, age
    for age in range(number.fall_start + 1):
        assert fall_offset(age, number, distance) == -distance, age


@pytest.mark.parametrize("distance", [100.0, 240.5])
def test_the_number_comes_down_from_above_and_overshoots_by_no_more_than_its_overshoot(
    distance: float,
) -> None:
    number = NUMBER
    offsets = [fall_offset(age, number, distance) for age in range(number.fall_end)]
    assert offsets[number.fall_start + 1] < 0.0
    assert max(offsets) <= number.fall_overshoot_px + EPS
    assert max(offsets) > 0.0
    peak = number.fall_start + (number.fall_end - number.fall_start) * number.fall_peak_share
    for age in range(number.fall_start, int(peak)):
        assert offsets[age + 1] >= offsets[age], age
    for age in range(int(peak) + 1, number.fall_end - 1):
        assert offsets[age + 1] <= offsets[age], age


@pytest.mark.parametrize("number", NUMBERS)
def test_the_number_is_stretched_while_falling_and_settles_to_one_after_the_squash(
    number: NumberLook,
) -> None:
    for age in range(number.fall_end):
        assert pose_scales(age, number) == (number.fall_stretch_x, number.fall_stretch_y), age
    assert pose_scales(number.fall_end, number) == (number.squash_x, number.squash_y)
    settled = number.fall_end + number.squash_ticks
    for age in range(settled, settled + 40):
        assert pose_scales(age, number) == (1.0, 1.0), age
    for age in range(number.fall_end, settled):
        scale_x, scale_y = pose_scales(age, number)
        assert min(number.squash_x, 1.0) <= scale_x <= max(number.squash_x, 1.0)
        assert min(number.squash_y, 1.0) <= scale_y <= max(number.squash_y, 1.0)


# ----- the flight -----


POINTS = [
    ((0.0, 0.0), (100.0, 50.0)),
    ((320.0, 240.5), (780.25, 140.0)),
    ((-30.5, 12.0), (-30.5, 400.0)),
    ((500.0, 500.0), (500.0, 500.0)),
]


@pytest.mark.parametrize(("start", "end"), POINTS)
@pytest.mark.parametrize("arc", [0.0, 40.0, 133.5])
def test_the_flight_is_exactly_at_its_start_at_share_0_and_at_its_end_at_share_1(
    start: tuple[float, float], end: tuple[float, float], arc: float
) -> None:
    assert fly_position(0.0, start, end, arc) == start
    assert fly_position(1.0, start, end, arc) == end
    middle = fly_position(0.5, start, end, arc)
    assert middle[0] == pytest.approx((start[0] + end[0]) / 2.0)
    assert middle[1] == pytest.approx((start[1] + end[1]) / 2.0 - arc / 2.0)


@pytest.mark.parametrize("arrival", [ARRIVAL, FLY.start + 1, FLY.start + 60])
def test_the_flight_share_is_0_up_to_its_start_and_1_from_the_arrival_tick(arrival: int) -> None:
    for age in range(FLY.start + 1):
        assert fly_share(age, FLY, arrival) == 0.0, age
    for age in range(arrival, arrival + 40):
        assert fly_share(age, FLY, arrival) == 1.0, age
    shares = [fly_share(age, FLY, arrival) for age in range(arrival + 1)]
    assert all(0.0 <= share <= 1.0 for share in shares)
    assert shares == sorted(shares)
    if arrival - FLY.start > 1:
        assert 0.0 < fly_share(arrival - 1, FLY, arrival) < 1.0


# ----- the HUD pop -----


POPS = [
    POP,
    dataclasses.replace(POP, ticks=1),
    dataclasses.replace(POP, ticks=60, start_scale=2.0, undershoot_scale=0.5),
    dataclasses.replace(POP, undershoot_scale=1.0, undershoot_share=0.9),
    dataclasses.replace(POP, start_scale=1.05, undershoot_share=0.1),
]


@pytest.mark.parametrize("pop", POPS)
def test_the_pop_starts_at_its_start_scale_never_goes_above_it_and_is_1_from_its_end_on(
    pop: PopLook,
) -> None:
    assert pop_scale(0, pop) == pop.start_scale
    scales = [pop_scale(elapsed, pop) for elapsed in range(pop.ticks + 40)]
    assert max(scales) == pop.start_scale
    assert all(scale <= pop.start_scale for scale in scales)
    for elapsed in range(pop.ticks, pop.ticks + 40):
        assert pop_scale(elapsed, pop) == 1.0, elapsed
    assert min(scales) >= min(pop.undershoot_scale, 1.0) - EPS


def test_the_pop_goes_down_through_its_undershoot_then_back_up_to_1() -> None:
    pop = POP
    low = round(pop.ticks * pop.undershoot_share)
    assert pop_scale(low, pop) == pytest.approx(pop.undershoot_scale)
    for elapsed in range(low):
        assert pop_scale(elapsed + 1, pop) <= pop_scale(elapsed, pop)
    for elapsed in range(low, pop.ticks):
        assert pop_scale(elapsed + 1, pop) >= pop_scale(elapsed, pop)
