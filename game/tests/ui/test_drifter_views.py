"""Drifter sprite views: frames, picks, placement over the hitbox, charge and fire looks, caches.

Direct-edit feature `drifter-sprites` (no contract, no task file). The spec is the implementation
report docs/reports/implementation/ui/drifter-sprites-ui-developer.md plus the Director's strip
table and game/tuning/drifter_looks.json. GDD: 12-art-and-audio.md, rules 3, 9, 10 and 13; drifters
03 chain lightning, 04 coin, 05 floating islands, 06 fireball, 07 UFO, 08 planet, 10 electric ball.

Two stores are used. The real one is `install_drifter_looks` on the real tuning (the strips in
game/assets/sprites/). The synthetic one is built here: every strip is a solid color that says
which strip (red channel = 11 x id) and which frame (green channel = 10 x frame + 5) it is, so a
pixel read from a draw says which look and frame the view chose, whatever the art is.

Pixels are read from drawn surfaces (`pygame.image.tobytes`). Placement tests count a hitbox pixel
as covered when its four corners lie inside the shape and its alpha is at least 128 (half), the
test's own reading of "opaque".
"""

import math
import random
import time
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from itertools import pairwise
from pathlib import Path

import pygame
import pytest

from app.drifter_looks_tuning import install_drifter_looks
from app.tuning import load_tuning
from core.collision import Box, Circle, Line, Shape
from core.drifters.base import Drifter, DrifterType, Phase, TouchEffect
from core.drifters.chain_lightning import ChainLightning
from core.drifters.electric_ball import ElectricBall
from core.drifters.floating_island import INVERTIBLE_SHAPES, IslandVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import (
    ChainLightningLooks,
    CoinLooks,
    DrifterLooks,
    ElectricBallLooks,
    FireballLooks,
    FloatingIslandLooks,
    MeteoriteLooks,
    PlanetLooks,
    StripOrder,
    StripRule,
    UfoLooks,
)
from ui.drifters.registry import render_drifter
from ui.drifters.sprites import (
    Sprites,
    eased_frame,
    install_sprites,
    installed_sprites,
    pick,
    sprites_folder,
    strip_frame,
)

TUNING: DrifterTuning = load_tuning()

UFO_SEED = 5
"""Any seed: a UFO needs one to be born. The look does not depend on it."""

ALPHA_COVERED = 128
"""A pixel at half alpha or more counts as drawn solid."""

SQRT_HALF = math.sqrt(2) / 2
"""Half the diagonal of a pixel: how far a whole-pixel draw may sit from a float center."""

UFO_STILL_COVERAGE: dict[str, int] = {"ufo_broken.png": 379, "ufo_clean.png": 424}
"""Hitbox pixels (disc box 40 x 10 and dome circle r9, a pixel counts when its four corners are
inside, alpha >= 128, the two shapes together) that the picked stills cover, measured by QA on
staging/assets/sprites/ufo-d2-r2.png (the broken look) and ufo-d3-r3.png (the clean look) at the
anchor the spec gives (frame bottom is the disc bottom, middle column the disc middle). The report
states no number; a frame of the strip may not cover less than its still."""

HIT_TYPES: tuple[DrifterType, ...] = (
    DrifterType.UFO,
    DrifterType.PLANET,
    DrifterType.FIREBALL,
    DrifterType.ELECTRIC_BALL,
    DrifterType.CHAIN_LIGHTNING,
    DrifterType.METEORITE,
)
"""Drifters whose touch is a hit, so the run dims them in the re-hit cooldown."""


# --- fixtures and small helpers ----------------------------------------------------------------


@pytest.fixture(scope="module")
def display() -> None:
    pygame.init()
    pygame.display.set_mode((640, 480))


SALT_SEED = 20261105
"""Seeds the global `random` while a store is built. `Sprites` draws its salt from it, and the
salt picks every look, so a test that needs all the skins of a pool in a few uids would pass for
nearly every salt and fail for a few. A fixed seed makes every run the same."""


@contextmanager
def _fixed_salt() -> Iterator[None]:
    state = random.getstate()
    random.seed(SALT_SEED)
    try:
        yield
    finally:
        random.setstate(state)


@pytest.fixture(scope="module")
def real_store(display: None) -> Sprites:
    with _fixed_salt():
        return install_drifter_looks(TUNING)


@pytest.fixture
def real(real_store: Sprites) -> Sprites:
    """The real strips, installed for the views."""
    install_sprites(real_store)
    return real_store


def _drifter(
    kind: DrifterType,
    variant: str | None = None,
    *,
    invert: bool = False,
    uid: int = 1,
    x: float = 320.0,
    y: float = 240.0,
    ticks: int = 0,
    rehit_ticks_left: int = 0,
) -> Drifter:
    """A drifter of the real tuning, ACTIVE, `ticks` into its phase, at (x, y)."""
    placement = Placement(
        kind,
        x=320.0,
        y=240.0,
        variant=variant,
        invert=invert,
        seed=UFO_SEED if kind is DrifterType.UFO else None,
    )
    born = spawn_drifter(placement, 1, TUNING)
    return replace(
        born,
        uid=uid,
        x=x,
        y=y,
        phase=Phase.ACTIVE,
        ticks_in_phase=ticks,
        rehit_ticks_left=rehit_ticks_left,
    )


def _ball(*, uid: int = 1, x: float = 320.0, y: float = 240.0, ticks: int = 0) -> ElectricBall:
    found = _drifter(DrifterType.ELECTRIC_BALL, uid=uid, x=x, y=y, ticks=ticks)
    assert isinstance(found, ElectricBall)
    return found


def _chain(
    variant: str = "pair_flat",
    *,
    invert: bool = False,
    uid: int = 1,
    x: float = 320.0,
    y: float = 240.0,
    ticks: int = 0,
) -> ChainLightning:
    found = _drifter(
        DrifterType.CHAIN_LIGHTNING, variant, invert=invert, uid=uid, x=x, y=y, ticks=ticks
    )
    assert isinstance(found, ChainLightning)
    return found


class Shot:
    """A drawn surface read back as RGBA bytes."""

    def __init__(self, surface: pygame.Surface) -> None:
        self.w, self.h = surface.get_size()
        self.data: bytes = pygame.image.tobytes(surface, "RGBA")

    def alpha(self, x: int, y: int) -> int:
        if not (0 <= x < self.w and 0 <= y < self.h):
            return 0
        return self.data[(y * self.w + x) * 4 + 3]

    def rgb(self, x: int, y: int) -> tuple[int, int, int]:
        start = (y * self.w + x) * 4
        return (self.data[start], self.data[start + 1], self.data[start + 2])


def _transparent(width: int = 640, height: int = 480) -> pygame.Surface:
    return pygame.Surface((width, height), pygame.SRCALPHA)


def _black(width: int, height: int) -> pygame.Surface:
    surface = pygame.Surface((width, height))
    surface.fill((0, 0, 0))
    return surface


def _alpha_shot(
    drifter: Drifter,
    size: tuple[int, int] = (240, 240),
    center: tuple[float, float] | None = None,
) -> tuple[Shot, Drifter]:
    """Draw the drifter, moved to `center` (the middle of the surface by default), on a clear
    surface: alpha says what the view drew. Returns the picture and the moved drifter."""
    at = center if center is not None else (size[0] / 2, size[1] / 2)
    placed = replace(drifter, x=at[0], y=at[1])
    surface = _transparent(*size)
    render_drifter(surface, placed)
    return Shot(surface), placed


def _corners(px: int, py: int) -> tuple[tuple[int, int], ...]:
    return ((px, py), (px + 1, py), (px, py + 1), (px + 1, py + 1))


def _seg_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    length = vx * vx + vy * vy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / length))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _holds(shape: Shape, x: float, y: float, px: int, py: int) -> bool:
    """True when the pixel (px, py) lies wholly inside `shape` placed at (x, y)."""
    if isinstance(shape, Circle):
        return all(
            math.hypot(cx - (x + shape.cx), cy - (y + shape.cy)) <= shape.r
            for cx, cy in _corners(px, py)
        )
    if isinstance(shape, Box):
        return all(
            abs(cx - (x + shape.cx)) <= shape.w / 2 and abs(cy - (y + shape.cy)) <= shape.h / 2
            for cx, cy in _corners(px, py)
        )
    if isinstance(shape, Line):
        return all(
            _seg_dist(cx, cy, x + shape.ax, y + shape.ay, x + shape.bx, y + shape.by)
            <= shape.thickness / 2
            for cx, cy in _corners(px, py)
        )
    raise TypeError(f"no pixel rule for {shape!r}")


def _box_of(shape: Shape, x: float, y: float) -> tuple[int, int, int, int]:
    """A pixel box (x0, y0, x1, y1) that holds the shape."""
    if isinstance(shape, Circle):
        near, far = x + shape.cx - shape.r, x + shape.cx + shape.r
        top, bottom = y + shape.cy - shape.r, y + shape.cy + shape.r
    elif isinstance(shape, Box):
        near, far = x + shape.cx - shape.w / 2, x + shape.cx + shape.w / 2
        top, bottom = y + shape.cy - shape.h / 2, y + shape.cy + shape.h / 2
    elif isinstance(shape, Line):
        reach = shape.thickness / 2
        near, far = min(x + shape.ax, x + shape.bx) - reach, max(x + shape.ax, x + shape.bx) + reach
        top, bottom = (
            min(y + shape.ay, y + shape.by) - reach,
            max(y + shape.ay, y + shape.by) + reach,
        )
    else:
        raise TypeError(f"no pixel rule for {shape!r}")
    return (math.floor(near) - 1, math.floor(top) - 1, math.ceil(far) + 1, math.ceil(bottom) + 1)


def _held_pixels(shape: Shape, x: float, y: float) -> list[tuple[int, int]]:
    x0, y0, x1, y1 = _box_of(shape, x, y)
    return [
        (px, py)
        for py in range(y0, y1 + 1)
        for px in range(x0, x1 + 1)
        if _holds(shape, x, y, px, py)
    ]


def _uncovered(
    shot: Shot, shape: Shape, x: float, y: float, minimum: int
) -> list[tuple[int, int, int]]:
    """Pixels wholly inside `shape` whose alpha is under `minimum`, with their alpha."""
    return [
        (px, py, shot.alpha(px, py))
        for px, py in _held_pixels(shape, x, y)
        if shot.alpha(px, py) < minimum
    ]


def _strip_alphas(file: str, frame_w: int, frame_h: int, mirrored: bool) -> list[tuple[int, ...]]:
    """The alpha of every frame of a strip file, row by row, each frame as one tuple."""
    image = pygame.image.load(str(sprites_folder() / file))
    width, height = image.get_size()
    data = pygame.image.tobytes(image, "RGBA")
    frames: list[tuple[int, ...]] = []
    for index in range(width // frame_w):
        rows: list[int] = []
        for row in range(height):
            start = (row * width + index * frame_w) * 4 + 3
            line = list(data[start : start + frame_w * 4 : 4])
            rows.extend(reversed(line) if mirrored else line)
        frames.append(tuple(rows))
    assert height == frame_h
    return frames


# --- the synthetic store ------------------------------------------------------------------------

GROUND_FILES = ("ground_a.png", "ground_b.png", "ground_c.png")


def _write_strip(folder: Path, name: str, ident: int, frames: int, w: int, h: int) -> None:
    """Write a strip whose frame i is one solid color (11 x ident, 10 x i + 5, 0)."""
    strip = pygame.Surface((frames * w, h), pygame.SRCALPHA)
    for index in range(frames):
        strip.fill((11 * ident, 10 * index + 5, 0, 255), (index * w, 0, w, h))
    pygame.image.save(strip, str(folder / name))


@pytest.fixture(scope="module")
def synthetic_folder(display: None, tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("synthetic_sprites")
    for ident, (name, frames, w, h) in SYNTHETIC.items():
        _write_strip(folder, name, ident, frames, w, h)
    for offset, name in enumerate(GROUND_FILES):
        ground = pygame.Surface((320, 120), pygame.SRCALPHA)
        ground.fill((11 * (16 + offset), 0, 0, 255))
        pygame.image.save(ground, str(folder / name))
    return folder


SYNTHETIC: dict[int, tuple[str, int, int, int]] = {
    1: ("ufo_a.png", 8, 40, 20),
    2: ("ufo_b.png", 5, 40, 20),
    3: ("ufo_c.png", 6, 40, 20),
    4: ("planet_a.png", 4, 64, 64),
    5: ("planet_b.png", 6, 64, 64),
    6: ("planet_c.png", 5, 64, 64),
    7: ("fireball.png", 6, 64, 64),
    8: ("coin_common.png", 8, 24, 24),
    9: ("coin_rare.png", 8, 24, 24),
    10: ("ball_charge.png", 8, 24, 24),
    11: ("ball_fire.png", 6, 24, 24),
    12: ("ball_ring.png", 6, 128, 128),
    13: ("node_charge.png", 8, 18, 18),
    14: ("node_fire.png", 6, 18, 18),
    15: ("arc.png", 6, 181, 16),
    19: ("rock_a.png", 8, 36, 36),
    20: ("rock_b.png", 8, 36, 36),
    21: ("rock_c.png", 8, 36, 36),
    22: ("rock_d.png", 8, 36, 36),
}
"""id: (file, frames, frame width, frame height). The id is the strip's color code."""

SYNTHETIC_RULES: dict[int, tuple[int, StripOrder]] = {
    1: (3, StripOrder.RANDOM),
    2: (5, StripOrder.LOOP),
    3: (4, StripOrder.LOOP),
    4: (8, StripOrder.LOOP),
    5: (3, StripOrder.LOOP),
    6: (4, StripOrder.RANDOM),
    7: (4, StripOrder.LOOP),
    8: (6, StripOrder.LOOP),
    9: (6, StripOrder.LOOP),
    10: (6, StripOrder.LOOP),
    11: (3, StripOrder.RANDOM),
    12: (3, StripOrder.RANDOM),
    13: (6, StripOrder.LOOP),
    14: (3, StripOrder.RANDOM),
    15: (3, StripOrder.RANDOM),
    19: (5, StripOrder.LOOP),
    20: (5, StripOrder.LOOP),
    21: (5, StripOrder.LOOP),
    22: (5, StripOrder.LOOP),
}
"""id: (ticks a frame, order)."""

ART_HITBOX_WIDTH = 28
"""Width of the hit circle the meteorite art was drawn for (the real file's value)."""

RAY_COLOR = (255, 255, 255)
OUTLINE_COLOR = (0, 255, 255)
CHARGE_END = 2
"""The eased charge ends at this many ticks a frame (the real file's value)."""


def _rule(ident: int) -> StripRule:
    name, frames, w, h = SYNTHETIC[ident]
    ticks, order = SYNTHETIC_RULES[ident]
    assert frames > 0
    return StripRule(name=name, file=name, frame_w=w, frame_h=h, ticks_per_frame=ticks, order=order)


def _synthetic_looks() -> DrifterLooks:
    return DrifterLooks(
        dim_steps=8,
        ufo=UfoLooks(looks=(_rule(1), _rule(2), _rule(3))),
        planet=PlanetLooks(
            looks=(_rule(4), _rule(5), _rule(6)),
            field_ring_color=(180, 120, 255),
            field_ring_width=1,
            field_ring_radius_step=2,
        ),
        fireball=FireballLooks(strip=_rule(7), art_head_width=32, art_head_center=(44, 44)),
        coin=CoinLooks(common=_rule(8), rare=_rule(9)),
        electric_ball=ElectricBallLooks(
            charge=_rule(10),
            charge_ticks_per_frame_end=CHARGE_END,
            fire=_rule(11),
            ring=_rule(12),
            ray_color=RAY_COLOR,
            outline_color=OUTLINE_COLOR,
        ),
        chain_lightning=ChainLightningLooks(
            node_charge=_rule(13),
            charge_ticks_per_frame_end=CHARGE_END,
            node_fire=_rule(14),
            arc=_rule(15),
            ray_color=RAY_COLOR,
        ),
        floating_island=FloatingIslandLooks(looks=GROUND_FILES),
        meteorite=MeteoriteLooks(
            looks=(_rule(19), _rule(20), _rule(21), _rule(22)), art_hitbox_width=ART_HITBOX_WIDTH
        ),
    )


@pytest.fixture
def synthetic(synthetic_folder: Path) -> Sprites:
    """The solid-color strips, installed for the views."""
    with _fixed_salt():
        store = Sprites(_synthetic_looks(), synthetic_folder)
    install_sprites(store)
    return store


def _id_at(shot: Shot, x: int, y: int) -> tuple[int, int] | None:
    """(strip id, frame) of a pixel drawn from a synthetic strip, else None."""
    red, green, blue = shot.rgb(x, y)
    if blue != 0 or red == 0:
        return None
    return (round(red / 11), round((green - 5) / 10))


def _census(shot: Shot, x0: int, y0: int, x1: int, y1: int) -> Counter[int]:
    """Count the pixels in a box by strip id. Pixels of any other color (rays, outline) are -1."""
    found: Counter[int] = Counter()
    for py in range(max(0, y0), min(shot.h, y1)):
        for px in range(max(0, x0), min(shot.w, x1)):
            red, _, blue = shot.rgb(px, py)
            if blue != 0:
                found[-1] += 1
            elif red != 0:
                found[round(red / 11)] += 1
    return found


def _shown(drifter: Drifter) -> tuple[int, int]:
    """(strip id, frame) the view drew at the drifter's center, on a small clear canvas."""
    side = 140
    placed = replace(drifter, x=70.0, y=70.0)
    surface = _black(side, side)
    render_drifter(surface, placed)
    found = _id_at(Shot(surface), 70, 70)
    assert found is not None, "nothing drawn at the drifter's center"
    return found


# --- 3. frame selection --------------------------------------------------------------------------


@pytest.mark.parametrize("uid", [1, 2, 3, 17, 4096])
def test_every_real_strip_steps_every_ticks_per_frame_in_its_order(real: Sprites, uid: int) -> None:
    for rule in real.looks.strips():
        count = real.count(rule)
        shown = [
            strip_frame(rule, real.seed(uid), t, count)
            for t in range(3 * count * rule.ticks_per_frame)
        ]
        steps = [
            shown[i : i + rule.ticks_per_frame] for i in range(0, len(shown), rule.ticks_per_frame)
        ]
        assert all(len(set(step)) == 1 for step in steps), rule.file
        frames = [step[0] for step in steps]
        assert all(0 <= frame < count for frame in frames)
        pairs = list(pairwise(frames))
        if rule.order is StripOrder.LOOP:
            assert all(after == (before + 1) % count for before, after in pairs), rule.file
            assert set(frames) == set(range(count)), rule.file
        else:
            assert all(before != after for before, after in pairs), rule.file


def test_a_random_strip_shows_every_frame_and_never_the_same_one_twice_in_a_row(
    real: Sprites,
) -> None:
    for rule in real.looks.strips():
        if rule.order is not StripOrder.RANDOM:
            continue
        count = real.count(rule)
        for uid in range(1, 40):
            frames = [
                strip_frame(rule, real.seed(uid), t * rule.ticks_per_frame, count)
                for t in range(600)
            ]
            assert all(a != b for a, b in pairwise(frames)), (rule.file, uid)
        seen = {
            strip_frame(rule, real.seed(uid), t * rule.ticks_per_frame, count)
            for uid in range(1, 40)
            for t in range(60)
        }
        assert seen == set(range(count)), rule.file


@pytest.mark.parametrize("kind", [DrifterType.UFO, DrifterType.PLANET, DrifterType.METEORITE])
def test_the_views_follow_each_strips_order_and_speed_in_game_ticks(
    synthetic: Sprites, kind: DrifterType
) -> None:
    pools = {
        DrifterType.UFO: synthetic.looks.ufo.looks,
        DrifterType.PLANET: synthetic.looks.planet.looks,
        DrifterType.METEORITE: synthetic.looks.meteorite.looks,
    }
    pool = pools[kind]
    seen_ids: set[int] = set()
    for uid in range(1, 31):
        sequence = [_shown(_drifter(kind, uid=uid, ticks=t)) for t in range(130)]
        idents = {ident for ident, _ in sequence}
        assert len(idents) == 1, "a drifter never changes look"
        (ident,) = idents
        seen_ids.add(ident)
        rule = _rule(ident)
        count = SYNTHETIC[ident][1]
        step = rule.ticks_per_frame
        frames = [frame for _, frame in sequence]
        for start in range(0, 130 - step + 1, step):
            assert len(set(frames[start : start + step])) == 1, (uid, ident, start)
        per_step = [frames[start] for start in range(0, 130 - step + 1, step)]
        pairs = list(pairwise(per_step))
        if rule.order is StripOrder.LOOP:
            assert all(after == (before + 1) % count for before, after in pairs), (uid, ident)
            assert any(after == 0 for _, after in pairs), "a loop wraps"
        else:
            assert all(before != after for before, after in pairs), (uid, ident)
    assert len(seen_ids) == len(pool)


def test_animation_depends_on_ticks_and_not_on_the_wall_clock(
    synthetic: Sprites, monkeypatch: pytest.MonkeyPatch
) -> None:
    drifters = [
        _drifter(DrifterType.UFO, uid=3, ticks=40),
        _drifter(DrifterType.PLANET, uid=4, ticks=77),
        _drifter(DrifterType.COIN, "rare", uid=5, ticks=31),
        _ball(uid=6, ticks=50),
        _chain(uid=7, ticks=100),
    ]
    first = [_shown(d) for d in drifters]
    wall = {"now": 1000.0}

    def jumping_clock() -> float:
        wall["now"] += 977.31
        return wall["now"]

    with monkeypatch.context() as patched:
        patched.setattr(time, "time", jumping_clock)
        patched.setattr(time, "monotonic", jumping_clock)
        patched.setattr(time, "perf_counter", jumping_clock)
        patched.setattr(pygame.time, "get_ticks", lambda: int(jumping_clock()))
        second = [_shown(d) for d in drifters]
        third = [_shown(d) for d in drifters]
    assert first == second == third
    moving = {_shown(_drifter(DrifterType.PLANET, uid=4, ticks=t)) for t in range(60)}
    assert len(moving) > 1, "the frames never change as the ticks pass"


def _numeric_frames(start: int, end: int, span: int, tick: int) -> float:
    """Frames shown after `tick` ticks of a charge whose ticks a frame go linearly start to end,
    summed in small steps (1 / ticks-a-frame is the frames a tick)."""
    steps = 200
    total = 0.0
    for index in range(tick * steps):
        moment = (index + 0.5) / steps
        total += 1 / (start + (end - start) * moment / span) / steps
    return total


@pytest.mark.parametrize("uid", [1, 2, 3, 9, 4000])
def test_the_charge_easing_never_steps_a_frame_back_and_speeds_up(real: Sprites, uid: int) -> None:
    looks = real.looks
    cases = (
        (
            looks.electric_ball.charge,
            looks.electric_ball.charge_ticks_per_frame_end,
            _ball(uid=uid).charge_ticks,
        ),
        (
            looks.chain_lightning.node_charge,
            looks.chain_lightning.charge_ticks_per_frame_end,
            _chain(uid=uid).charge_ticks,
        ),
    )
    for rule, end, span in cases:
        count = real.count(rule)
        assert rule.order is StripOrder.LOOP
        frames = [eased_frame(rule, end, real.seed(uid), t, span, count) for t in range(span)]
        steps = [(after - before) % count for before, after in pairwise(frames)]
        assert set(steps) <= {0, 1}, (rule.file, steps)
        moved = [sum(steps[i : i + span // 3]) for i in range(0, 3 * (span // 3), span // 3)]
        assert moved[0] < moved[1] < moved[2], (rule.file, moved)
        advanced = sum(steps)
        expected = _numeric_frames(rule.ticks_per_frame, end, span, span - 1)
        assert abs(advanced - expected) <= 1, (rule.file, advanced, expected)


def test_the_electric_ball_view_eases_its_charge_frames_through_the_cycle(
    synthetic: Sprites,
) -> None:
    for uid in (1, 2, 5, 11):
        span = _ball(uid=uid).charge_ticks
        frames = [_shown(_ball(uid=uid, ticks=t)) for t in range(span)]
        assert {ident for ident, _ in frames} == {10}
        index = [frame for _, frame in frames]
        count = SYNTHETIC[10][1]
        steps = [(after - before) % count for before, after in pairwise(index)]
        assert set(steps) <= {0, 1}, (uid, steps)
        third = span // 3
        moved = [sum(steps[i : i + third]) for i in range(0, 3 * third, third)]
        assert moved[0] < moved[2], (uid, moved)
        again = [_shown(_ball(uid=uid, ticks=t + _cycle(uid))) for t in range(span)]
        assert again == frames, "the next charge plays the same frames"


def _cycle(uid: int) -> int:
    ball = _ball(uid=uid)
    return ball.charge_ticks + ball.fire_ticks


def test_the_chain_node_view_eases_its_charge_frames_through_the_cycle(
    synthetic: Sprites,
) -> None:
    for uid in (1, 2, 5, 11):
        probe = _chain(uid=uid)
        span = probe.charge_ticks
        frames = [_shown_node(_chain(uid=uid, ticks=t)) for t in range(span)]
        assert {ident for ident, _ in frames} == {13}
        index = [frame for _, frame in frames]
        count = SYNTHETIC[13][1]
        steps = [(after - before) % count for before, after in pairwise(index)]
        assert set(steps) <= {0, 1}, (uid, steps)
        third = span // 3
        moved = [sum(steps[i : i + third]) for i in range(0, 3 * third, third)]
        assert moved[0] < moved[2], (uid, moved)


def _shown_node(chain: ChainLightning) -> tuple[int, int]:
    """(strip id, frame) at the middle of the first node of a chain drawn at (320, 240)."""
    surface = _black(640, 480)
    render_drifter(surface, chain)
    first = chain.node_centers()[0]
    found = _id_at(Shot(surface), round(first[0]), round(first[1]))
    assert found is not None
    return found


# --- 4. look pick --------------------------------------------------------------------------------


def _look_read(drifter: Drifter) -> int:
    """The id of the synthetic strip (or ground) the view drew at the drifter's center.

    The drifter is moved to the middle of a small black surface first.
    """
    island = drifter.drifter_type is DrifterType.FLOATING_ISLAND
    size = (340, 160) if island else (140, 140)
    center = (size[0] // 2, size[1] // 2)
    surface = _black(*size)
    render_drifter(surface, replace(drifter, x=float(center[0]), y=float(center[1])))
    found = _id_at(Shot(surface), *center)
    assert found is not None
    return found[0]


def _look_of(kind: DrifterType, uid: int, variant: str | None = None) -> int:
    return _look_read(_drifter(kind, variant, uid=uid))


POOLS: tuple[tuple[DrifterType, str | None, set[int]], ...] = (
    (DrifterType.UFO, None, {1, 2, 3}),
    (DrifterType.PLANET, None, {4, 5, 6}),
    (DrifterType.FLOATING_ISLAND, "box", {16, 17, 18}),
    (DrifterType.METEORITE, "medium", {19, 20, 21, 22}),
)
"""Each drifter with a pool of looks, and the strip ids of its pool."""


@pytest.mark.parametrize(("kind", "variant", "pool"), POOLS, ids=lambda value: str(value)[:20])
def test_a_drifter_keeps_its_look_and_every_look_in_the_pool_is_reachable(
    synthetic: Sprites, kind: DrifterType, variant: str | None, pool: set[int]
) -> None:
    reached: set[int] = set()
    for uid in range(1, 91):
        first = _look_of(kind, uid, variant)
        assert first in pool
        reached.add(first)
        for ticks in (13, 200, 1000):
            moved = _drifter(kind, variant, uid=uid, ticks=ticks)
            assert _look_read(moved) == first, (kind, uid, ticks)
    assert reached == pool, f"{kind.value}: looks never picked {sorted(pool - reached)}"


def test_the_picks_follow_the_uid_so_a_group_gets_a_mix_of_looks(synthetic: Sprites) -> None:
    for kind, variant, pool in POOLS:
        picks = [_look_of(kind, uid, variant) for uid in range(1, 25)]
        assert len(set(picks)) > 1, kind
        assert set(picks) <= pool


def test_each_meteorite_starts_its_turn_at_its_own_frame(synthetic: Sprites) -> None:
    """GDD 01, look_ticks_per_frame: each rock starts at a random frame and then steps every
    `ticks_per_frame` ticks. The synthetic strips have 8 frames and 5 ticks a frame (not the real
    32 and 3), so the test reads no number from the real strips."""
    starts = [
        _shown(_drifter(DrifterType.METEORITE, "medium", uid=uid, ticks=0)) for uid in range(1, 41)
    ]
    frames = {frame for _, frame in starts}
    assert len(frames) >= 4, f"40 rocks started on only frames {sorted(frames)}"
    assert len({ident for ident, _ in starts}) == 4
    pairs = [
        (_shown(_drifter(DrifterType.METEORITE, "medium", uid=uid, ticks=0)), uid)
        for uid in range(1, 9)
    ]
    assert len({shown for shown, _ in pairs}) > 1
    for uid in (1, 2, 3):
        ident, first = starts[uid - 1]
        count = SYNTHETIC[ident][1]
        for ticks in range(90):
            _, frame = _shown(_drifter(DrifterType.METEORITE, "medium", uid=uid, ticks=ticks))
            assert frame == (first + ticks // 5) % count, (uid, ticks)


def test_a_new_install_can_give_other_picks(synthetic_folder: Path, synthetic: Sprites) -> None:
    """`look_pick` is random (12-art-and-audio.md, rule 10): runs differ, one run never changes."""
    state = random.getstate()
    random.seed(20261105)
    try:
        lists: list[tuple[int, ...]] = []
        salts: set[int] = set()
        for _ in range(12):
            store = Sprites(_synthetic_looks(), synthetic_folder)
            salts.add(store.salt)
            install_sprites(store)
            lists.append(tuple(_look_of(DrifterType.UFO, uid) for uid in range(1, 16)))
            again = tuple(_look_of(DrifterType.UFO, uid) for uid in range(1, 16))
            assert lists[-1] == again, "one install keeps its picks"
    finally:
        random.setstate(state)
    assert len(salts) > 1
    assert len(set(lists)) > 1, "twelve installs all picked the same looks"
    install_sprites(synthetic)


# --- 5. placement --------------------------------------------------------------------------------


def _region(shot: Shot, left: int, top: int, width: int, height: int) -> tuple[int, ...]:
    return tuple(shot.alpha(left + i, top + j) for j in range(height) for i in range(width))


def _union_coverage(shot: Shot, d: Drifter) -> int:
    held = {pixel for shape in d.hitbox for pixel in _held_pixels(shape, d.x, d.y)}
    return sum(1 for px, py in held if shot.alpha(px, py) >= ALPHA_COVERED)


@pytest.mark.parametrize("invert", [False, True])
def test_the_ufo_frame_sits_on_its_disc_and_covers_it_and_the_dome_as_well_as_the_still(
    real: Sprites, invert: bool
) -> None:
    rules = real.looks.ufo.looks
    candidates: list[tuple[StripRule, int, tuple[int, ...]]] = [
        (rule, index, alphas)
        for rule in rules
        for index, alphas in enumerate(_strip_alphas(rule.file, rule.frame_w, rule.frame_h, invert))
    ]
    used: set[str] = set()
    for uid in range(1, 17):
        for ticks in range(0, 60, 6):
            d = _drifter(DrifterType.UFO, invert=invert, uid=uid, ticks=ticks)
            shot, d = _alpha_shot(d, (120, 100))
            left, top = round(d.x) - 20, round(d.y) - 15
            drawn = _region(shot, left, top, 40, 20)
            matches = [(rule, index) for rule, index, alphas in candidates if alphas == drawn]
            assert matches, f"uid {uid} tick {ticks}: no frame of the strip is where the disc is"
            rule = matches[0][0]
            used.add(rule.file)
            assert _union_coverage(shot, d) >= UFO_STILL_COVERAGE[rule.file], (
                rule.file,
                matches[0][1],
            )
    assert used == {rule.file for rule in rules}


@pytest.mark.parametrize("variant", ["small", "big"])
@pytest.mark.parametrize("invert", [False, True])
def test_the_fireball_head_is_covered_and_the_tail_shows_in_both_directions_and_sizes(
    real: Sprites, variant: str, invert: bool
) -> None:
    for uid in range(1, 7):
        for ticks in range(0, 24, 2):
            d = _drifter(DrifterType.FIREBALL, variant, invert=invert, uid=uid, ticks=ticks)
            shot, d = _alpha_shot(d, (140, 140))
            head, tail = d.hitbox
            assert _uncovered(shot, head, d.x, d.y, ALPHA_COVERED) == [], (uid, ticks)
            assert _uncovered(shot, tail, d.x, d.y, 1) == [], (uid, ticks)


def test_the_planet_covers_its_whole_circle_on_every_frame(real: Sprites) -> None:
    rule = real.looks.planet.looks[0]
    for ticks in range(0, real.count(rule) * rule.ticks_per_frame, rule.ticks_per_frame):
        d = _drifter(DrifterType.PLANET, uid=1, ticks=ticks)
        shot, d = _alpha_shot(d, (140, 140))
        (circle,) = d.hitbox
        assert _uncovered(shot, circle, d.x, d.y, ALPHA_COVERED) == [], ticks


@pytest.mark.parametrize("variant", ["common", "rare"])
def test_the_coin_crystal_box_is_covered_on_every_frame(real: Sprites, variant: str) -> None:
    for uid in (1, 2, 3):
        for ticks in range(0, 8 * 6, 6):
            d = _drifter(DrifterType.COIN, variant, uid=uid, ticks=ticks)
            shot, d = _alpha_shot(d, (60, 60))
            (box,) = d.hitbox
            assert _uncovered(shot, box, d.x, d.y, ALPHA_COVERED) == [], (uid, ticks)


MEDIUM_WIDTH = 28.0
"""The width the Director's limits are given at. Small (20) and big (40) scale them with it."""

MIN_COVERED_SHARE = 0.88
FULLY_COVERED_RADIUS = 10.0
MAX_BITE_DEPTH = 3.0
VISIBLE_INK = 32
"""Director decision 2026-11-05 (to be written into the GDD): at the medium rock the art covers at
least 88% of the r14 hit circle, the center r10 fully, and no bite cuts deeper than 3 px.
Accepted by the main session on the Director's rule ("it does not matter that the look in a corner
is less than the hitbox, if the other side is maintaining the shape"): the 3 px applies to the
native medium art (read at alpha >= 128, as the coverage is); small and big are scaled art, so
their bites are read at visible ink (alpha >= 32) with the limit scaled by width / 28. Scaling
softens a bite's edge, which moves the half-alpha line inward and not the rock."""


def _circle_scan(
    shot: Shot, circle: Circle, x: float, y: float, bite_alpha: int = ALPHA_COVERED
) -> tuple[int, int, float, int, int]:
    """(pixels in the circle, covered, deepest uncovered px from the edge, center pixels, covered).

    A pixel is in the circle when its center is; covered means alpha >= 128; a bite is a pixel
    under `bite_alpha`. `circle.r` is the
    placed circle's radius; the center disc is `FULLY_COVERED_RADIUS` scaled to this rock.
    """
    inner = FULLY_COVERED_RADIUS * circle.r / (MEDIUM_WIDTH / 2)
    total = covered = center_total = center_covered = 0
    deepest = 0.0
    for py in range(math.floor(y - circle.r) - 1, math.ceil(y + circle.r) + 1):
        for px in range(math.floor(x - circle.r) - 1, math.ceil(x + circle.r) + 1):
            distance = math.hypot(px + 0.5 - x, py + 0.5 - y)
            if distance > circle.r:
                continue
            total += 1
            solid = shot.alpha(px, py) >= ALPHA_COVERED
            covered += solid
            if shot.alpha(px, py) < bite_alpha:
                deepest = max(deepest, circle.r - distance)
            if distance <= inner:
                center_total += 1
                center_covered += solid
    return total, covered, deepest, center_total, center_covered


FRAME_WALK_UIDS = 8
"""Rocks walked through a whole turn each (uids 1 to 8 reach all four skins under `SALT_SEED`)."""


@pytest.mark.parametrize("variant", ["small", "medium", "big"])
def test_the_meteorite_art_covers_the_hit_circle_to_the_directors_limits(
    real: Sprites, variant: str
) -> None:
    looks = real.looks.meteorite.looks
    skins: set[int] = set()
    shown: set[tuple[int, int]] = set()
    worst_share, worst_depth = 1.0, 0.0
    for uid in range(1, FRAME_WALK_UIDS + 1):
        skin = pick(real.seed(uid), len(looks))
        rule = looks[skin]
        count = real.count(rule)
        skins.add(skin)
        # One whole turn of the rock, a frame at a time, whatever its start frame, frame count
        # and ticks a frame are in the file.
        for step in range(count):
            ticks = step * rule.ticks_per_frame
            shown.add((skin, strip_frame(rule, real.seed(uid), ticks, count)))
            d = _drifter(DrifterType.METEORITE, variant, uid=uid, ticks=ticks)
            shot, placed = _alpha_shot(d, (120, 120), center=(60.0, 60.0))
            (circle,) = placed.hitbox
            assert isinstance(circle, Circle)
            bite_alpha = ALPHA_COVERED if placed.width == MEDIUM_WIDTH else VISIBLE_INK
            total, covered, deepest, center_total, center_covered = _circle_scan(
                shot, circle, placed.x, placed.y, bite_alpha
            )
            scale = placed.width / MEDIUM_WIDTH
            assert center_covered == center_total, (variant, uid, ticks, "center disc has a hole")
            worst_share = min(worst_share, covered / total)
            worst_depth = max(worst_depth, deepest / scale)
    every_frame = {(i, f) for i, rule in enumerate(looks) for f in range(real.count(rule))}
    assert shown == every_frame, f"frames never drawn: {sorted(every_frame - shown)[:10]}"
    assert skins == set(range(len(looks))), "the uids used never showed every skin"
    assert worst_share >= MIN_COVERED_SHARE, (variant, worst_share)
    assert worst_depth <= MAX_BITE_DEPTH, (variant, worst_depth, "px at the medium rock's scale")


@pytest.mark.parametrize("variant", ["small", "medium", "big"])
@pytest.mark.parametrize("center", [(60.0, 60.0), (60.4, 60.6), (59.5, 60.5)])
def test_every_pixel_the_meteorite_draws_is_inside_its_drawn_box(
    real: Sprites, variant: str, center: tuple[float, float]
) -> None:
    """Rule 12 (07-drifters.md): the drifter leaves once nothing drawn is on screen, so the drawn
    box must hold every drawn pixel (to the half pixel a whole-pixel blit moves it)."""
    looks = real.looks.meteorite.looks
    for uid in range(1, FRAME_WALK_UIDS + 1):
        rule = looks[pick(real.seed(uid), len(looks))]
        for step in range(real.count(rule)):
            ticks = step * rule.ticks_per_frame
            d = _drifter(DrifterType.METEORITE, variant, uid=uid, ticks=ticks)
            shot, placed = _alpha_shot(d, (120, 120), center=center)
            (box,) = placed.drawn_parts()
            for py in range(shot.h):
                for px in range(shot.w):
                    if shot.alpha(px, py) == 0:
                        continue
                    assert box.cx - box.w / 2 - 0.5 <= px, (variant, uid, ticks, px, py)
                    assert px + 1 <= box.cx + box.w / 2 + 0.5, (variant, uid, ticks, px, py)
                    assert box.cy - box.h / 2 - 0.5 <= py, (variant, uid, ticks, px, py)
                    assert py + 1 <= box.cy + box.h / 2 + 0.5, (variant, uid, ticks, px, py)


def _center_inside(shape: object, x: float, y: float) -> set[tuple[int, int]]:
    """Pixels whose center lies in a Box, or in a polygon (cross products, either way round)."""
    found: set[tuple[int, int]] = set()
    if isinstance(shape, Box):
        for py in range(
            math.floor(y + shape.cy - shape.h / 2), math.ceil(y + shape.cy + shape.h / 2)
        ):
            for px in range(
                math.floor(x + shape.cx - shape.w / 2), math.ceil(x + shape.cx + shape.w / 2)
            ):
                if (
                    abs(px + 0.5 - (x + shape.cx)) < shape.w / 2
                    and abs(py + 0.5 - (y + shape.cy)) < shape.h / 2
                ):
                    found.add((px, py))
        return found
    points = [(x + px, y + py) for px, py in shape.points]  # type: ignore[attr-defined]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    for py in range(math.floor(min(ys)), math.ceil(max(ys))):
        for px in range(math.floor(min(xs)), math.ceil(max(xs))):
            signs = []
            for index, (ax, ay) in enumerate(points):
                bx, by = points[(index + 1) % len(points)]
                signs.append((bx - ax) * (py + 0.5 - ay) - (by - ay) * (px + 0.5 - ax))
            if all(s >= 0 for s in signs) or all(s <= 0 for s in signs):
                found.add((px, py))
    return found


def _ground_crop(name: str, width: int, height: int) -> Callable[[int, int], tuple[int, int, int]]:
    """Pixel reader of the centered `width` x `height` crop of a ground image file."""
    image = pygame.image.load(str(sprites_folder() / name))
    ground = Shot(image)
    origin_x, origin_y = (ground.w - width) // 2, (ground.h - height) // 2

    def pixel(x: int, y: int) -> tuple[int, int, int]:
        return ground.rgb(origin_x + x, origin_y + y)

    return pixel


def _island_cases() -> list[tuple[str, bool]]:
    island = TUNING.drifters[DrifterType.FLOATING_ISLAND]
    cases: list[tuple[str, bool]] = []
    for name, variant in island.variants.items():
        assert isinstance(variant.extra, IslandVariantExtra)
        cases.append((name, False))
        if variant.extra.shape in INVERTIBLE_SHAPES:
            cases.append((name, True))
    return cases


@pytest.mark.parametrize(("variant", "invert"), _island_cases(), ids=lambda v: str(v))
def test_the_island_draws_exactly_its_hitbox_and_nothing_else(
    real: Sprites, variant: str, invert: bool
) -> None:
    """GDD 05: the island's art fills its shape exactly (12-art rule 9)."""
    for uid in range(1, 7):
        d = _drifter(DrifterType.FLOATING_ISLAND, variant, invert=invert, uid=uid)
        shot, d = _alpha_shot(d, (400, 200))
        expected: set[tuple[int, int]] = set()
        for shape in d.hitbox:
            expected |= _center_inside(shape, d.x, d.y)
        drawn = {
            (index % shot.w, index // shot.w)
            for index, alpha in enumerate(shot.data[3::4])
            if alpha > 0
        }
        assert drawn == expected, (variant, invert, uid, len(drawn), len(expected))
        assert all(shot.alpha(px, py) == 255 for px, py in drawn), (variant, invert, uid)
        left, top = round(d.x - d.width / 2), round(d.y - d.height / 2)
        crops = [
            _ground_crop(name, round(d.width), round(d.height))
            for name in real.looks.floating_island.looks
        ]
        matching = [
            crop
            for crop in crops
            if all(shot.rgb(px, py) == crop(px - left, py - top) for px, py in drawn)
        ]
        assert matching, f"{variant} {invert} {uid}: the pixels are not a centered crop of a ground"


def _stray_pixels(
    shot: Shot, cx: float, cy: float, radius: float, slack: float, min_alpha: int = 1
) -> int:
    """Count pixels at `min_alpha` or more whose nearest point is farther than `radius` + `slack`
    from the center."""
    stray = 0
    reach = math.ceil(radius + slack) + 4
    for py in range(math.floor(cy) - reach, math.floor(cy) + reach):
        for px in range(math.floor(cx) - reach, math.floor(cx) + reach):
            if shot.alpha(px, py) < min_alpha:
                continue
            dx = max(px - cx, 0.0, cx - (px + 1))
            dy = max(py - cy, 0.0, cy - (py + 1))
            if math.hypot(dx, dy) > radius + slack:
                stray += 1
    return stray


def test_the_firing_ring_draws_nothing_outside_the_pulse_circle_and_fills_it(real: Sprites) -> None:
    """The ring strip is 128 px and is scaled to twice `pulse_radius` from the tuning. Scaling
    softens its edge by under a pixel, so outside the circle only solid ink counts as drawn
    (`ALPHA_COVERED`), as for the scaled meteorites."""
    for uid in (1, 2, 3):
        ball = _ball(uid=uid)
        radius = ball.pulse_radius
        for ticks in range(ball.charge_ticks, ball.charge_ticks + ball.fire_ticks, 13):
            d = _ball(uid=uid, ticks=ticks)
            assert d.pulse_fires()
            shot, placed = _alpha_shot(d, (200, 200))
            strays = _stray_pixels(shot, placed.x, placed.y, radius, 0.0, ALPHA_COVERED)
            assert strays == 0, (uid, ticks)
            (circle,) = placed.hitbox
            assert _uncovered(shot, circle, placed.x, placed.y, 1) == [], (uid, ticks)


@pytest.mark.parametrize(("x", "y"), [(320.4, 240.4), (320.5, 240.5), (200.49, 300.51)])
def test_the_firing_ring_stays_in_the_circle_to_the_half_pixel_a_whole_pixel_draw_allows(
    real: Sprites, x: float, y: float
) -> None:
    """Every firing tick of the tuning's cycle, read at solid ink like the test above."""
    ball = _ball(x=x, y=y)
    for ticks in range(ball.charge_ticks, ball.charge_ticks + ball.fire_ticks, 7):
        d = _ball(x=x, y=y, ticks=ticks)
        assert d.pulse_fires()
        shot, placed = _alpha_shot(d, (200, 200), center=(100 + x % 1, 100 + y % 1))
        strays = _stray_pixels(shot, placed.x, placed.y, d.pulse_radius, SQRT_HALF, ALPHA_COVERED)
        assert strays == 0, ticks


@pytest.mark.parametrize("variant", list(TUNING.drifters[DrifterType.CHAIN_LIGHTNING].variants))
@pytest.mark.parametrize("invert", [False, True])
def test_the_chain_arcs_and_nodes_cover_their_hitbox_while_they_fire(
    real: Sprites, variant: str, invert: bool
) -> None:
    for uid in (1, 2):
        probe = _chain(variant, invert=invert, uid=uid)
        for k in range(0, probe.fire_ticks, 9):
            d = _chain(variant, invert=invert, uid=uid, ticks=probe.charge_ticks + k)
            assert d.firing_arcs() == tuple(range(len(d.arcs)))
            shot, placed = _alpha_shot(d, (320, 260))
            for shape in placed.hitbox:
                assert _uncovered(shot, shape, placed.x, placed.y, ALPHA_COVERED) == [], (
                    variant,
                    invert,
                    uid,
                    k,
                    shape,
                )


# --- 6. charge and fire looks only when core says so ---------------------------------------


def _sample_ticks(charge: int, fire: int) -> list[int]:
    cycle = charge + fire
    ticks = set(range(0, 2 * cycle, 5))
    ticks |= {
        0,
        1,
        charge - 1,
        charge,
        charge + 1,
        cycle - 1,
        cycle,
        cycle + charge - 1,
        cycle + charge,
    }
    return sorted(ticks)


BALL_BOX = (320 - 90, 240 - 90, 320 + 90, 240 + 90)


def test_the_electric_ball_shows_its_charge_look_while_charging_and_the_fire_look_while_firing(
    synthetic: Sprites,
) -> None:
    charge_id, fire_id, ring_id = 10, 11, 12
    probe = _ball()
    for ticks in _sample_ticks(probe.charge_ticks, probe.fire_ticks):
        d = _ball(ticks=ticks)
        surface = _black(640, 480)
        render_drifter(surface, d)
        shot = Shot(surface)
        found = _census(shot, *BALL_BOX)
        if d.pulse_fires():
            assert ticks % (d.charge_ticks + d.fire_ticks) >= d.charge_ticks
            assert found[charge_id] == 0, ticks
            assert found[fire_id] > 0, ticks
            assert found[ring_id] > 0, ticks
            assert found[-1] == 0, f"a charge ray or outline shows while it fires ({ticks})"
            middle = _id_at(shot, 320, 240)
            assert middle is not None
            assert middle[0] == fire_id
        else:
            assert ticks % (d.charge_ticks + d.fire_ticks) < d.charge_ticks
            assert found[fire_id] == 0, f"fire look while charging ({ticks})"
            assert found[ring_id] == 0, f"ring while charging ({ticks})"
            assert found[charge_id] > 0, ticks
            rays = d.charge_ray_count()
            assert (found[-1] > 0) == (rays > 0), ticks


@pytest.mark.parametrize("ticks_into_cycle", [0, 60, 119, 120, 180, 239])
def test_an_electric_ball_core_says_is_off_screen_draws_no_fire_or_charge_look(
    synthetic: Sprites, ticks_into_cycle: int
) -> None:
    for x in (700.0, 660.0):
        d = _ball(x=x, ticks=ticks_into_cycle)
        assert not d.ball_on_screen()
        assert not d.pulse_fires()
        assert d.charge_ray_count() == 0
        surface = _black(900, 480)
        render_drifter(surface, d)
        found = _census(Shot(surface), int(x) - 90, 150, int(x) + 90, 330)
        assert found[11] == 0, "fire look drawn off screen"
        assert found[12] == 0, "ring drawn off screen"
        assert found[-1] == 0, "a ray or an outline drawn off screen"
        assert set(found) <= {10}, found


def test_a_ball_with_its_box_on_the_screen_edge_fires_when_core_says_so(synthetic: Sprites) -> None:
    for x in (630.0, 640.0, 647.0, 648.0, 649.0):
        d = _ball(x=x, ticks=130)
        surface = _black(900, 480)
        render_drifter(surface, d)
        found = _census(Shot(surface), int(x) - 90, 150, int(x) + 90, 330)
        assert (found[11] > 0) == d.pulse_fires(), x
        assert (found[12] > 0) == d.pulse_fires(), x


def test_the_chain_draws_arcs_and_fire_nodes_only_while_core_says_they_fire(
    synthetic: Sprites,
) -> None:
    node_charge, node_fire, arc = 13, 14, 15
    for variant in ("pair_flat", "trio_line"):
        probe = _chain(variant)
        reach = 150
        for ticks in _sample_ticks(probe.charge_ticks, probe.fire_ticks):
            d = _chain(variant, ticks=ticks)
            surface = _black(640, 480)
            render_drifter(surface, d)
            shot = Shot(surface)
            firing = d.firing_arcs()
            in_cycle = ticks % (d.charge_ticks + d.fire_ticks)
            assert (firing != ()) == (in_cycle >= d.charge_ticks)
            found = _census(shot, 320 - reach, 240 - 40, 320 + reach, 240 + 40)
            lit = {node for index in firing for node in d.arcs[index]}
            for number, (nx, ny) in enumerate(d.node_centers()):
                middle = _id_at(shot, round(nx), round(ny))
                assert middle is not None
                assert middle[0] == (node_fire if number in lit else node_charge), (
                    variant,
                    ticks,
                    number,
                )
            if firing:
                assert found[arc] > 0
                assert found[node_fire] > 0
                assert found[-1] == 0, "rays while firing"
            else:
                assert found[arc] == 0, (variant, ticks)
                assert found[node_fire] == 0, (variant, ticks)
                assert found[node_charge] > 0


def test_a_chain_whose_arc_core_does_not_fire_shows_no_fire_look_for_it(synthetic: Sprites) -> None:
    node_charge, node_fire, arc = 13, 14, 15
    probe = _chain("pair_flat")
    firing_tick = probe.charge_ticks + 5
    off_screen = _chain("pair_flat", x=620.0, ticks=firing_tick)
    assert off_screen.firing_arcs() == ()
    surface = _black(900, 480)
    render_drifter(surface, off_screen)
    found = _census(Shot(surface), 460, 200, 800, 280)
    assert found[arc] == 0, found
    assert found[node_fire] == 0, found

    one_arc = _chain("trio_line", x=520.0, ticks=probe.charge_ticks + 5)
    assert one_arc.firing_arcs() == (0,)
    surface = _black(900, 480)
    render_drifter(surface, one_arc)
    shot = Shot(surface)
    third = _id_at(shot, round(one_arc.node_centers()[2][0]), round(one_arc.node_centers()[2][1]))
    first = _id_at(shot, round(one_arc.node_centers()[0][0]), round(one_arc.node_centers()[0][1]))
    assert third is not None
    assert first is not None
    assert third[0] == node_charge, "the node of an arc that does not fire shows the fire look"
    assert first[0] == node_fire


def test_the_rare_coin_draws_the_rare_strip_and_the_common_coin_the_common_one(
    synthetic: Sprites,
) -> None:
    for uid in range(1, 12):
        common = {
            _shown(_drifter(DrifterType.COIN, "common", uid=uid, ticks=t))[0] for t in range(60)
        }
        rare = {_shown(_drifter(DrifterType.COIN, "rare", uid=uid, ticks=t))[0] for t in range(60)}
        assert common == {8}, uid
        assert rare == {9}, uid


def test_a_draw_gives_the_same_pixels_before_and_after_other_draws(real: Sprites) -> None:
    """The store keeps images between draws (the planet's rings change their alpha at each blit):
    nothing one draw does may change another."""
    kinds = [
        (DrifterType.PLANET, None),
        (DrifterType.UFO, None),
        (DrifterType.FIREBALL, "big"),
        (DrifterType.COIN, "rare"),
        (DrifterType.ELECTRIC_BALL, None),
        (DrifterType.CHAIN_LIGHTNING, "trio_triangle"),
        (DrifterType.FLOATING_ISLAND, "l_shape"),
        (DrifterType.METEORITE, "big"),
    ]
    for rehit in (0, 30):
        cases = [
            _drifter(kind, name, uid=3 + number, ticks=10 + 37 * number, rehit_ticks_left=rehit)
            for number, (kind, name) in enumerate(kinds)
        ]
        first = [_alpha_shot(d, (400, 400))[0].data for d in cases]
        for other in (rehit, 30 - rehit):
            for extra in range(40):
                _alpha_shot(
                    _drifter(DrifterType.PLANET, ticks=7 * extra, rehit_ticks_left=other),
                    (400, 400),
                )
        again = [_alpha_shot(d, (400, 400))[0].data for d in cases]
        assert first == again
        assert again == [_alpha_shot(d, (400, 400))[0].data for d in cases]


# --- 7. caches -----------------------------------------------------------------------------------


def _sizes(store: Sprites) -> tuple[int, int]:
    """Entries in the store's two caches. It has no public count: this reads its two dicts."""
    return (len(store._images), len(store._built))


def _draw_everything(
    surface: pygame.Surface, kinds: Callable[[DrifterType], bool], rehit_ticks_left: int
) -> int:
    drawn = 0
    for kind, type_tuning in TUNING.drifters.items():
        if kind is DrifterType.SATELLITE or not kinds(kind):
            continue
        for name, variant in type_tuning.variants.items():
            inverts = [False]
            if kind in (DrifterType.UFO, DrifterType.FIREBALL, DrifterType.CHAIN_LIGHTNING):
                inverts = [False, True]
            if isinstance(variant.extra, IslandVariantExtra):
                inverts = [False, True] if variant.extra.shape in INVERTIBLE_SHAPES else [False]
            for invert in inverts:
                for uid in (1, 2, 3):
                    for step, ticks in enumerate(range(0, 520, 7)):
                        d = _drifter(
                            kind,
                            name,
                            invert=invert,
                            uid=uid,
                            x=100.3 + 7.1 * (step % 50),
                            y=80.7 + 3.3 * (step % 60),
                            ticks=ticks,
                            rehit_ticks_left=rehit_ticks_left,
                        )
                        render_drifter(surface, d)
                        drawn += 1
    return drawn


def test_drawing_many_frames_adds_no_cache_entries_after_the_install(real: Sprites) -> None:
    surface = _transparent()
    before = _sizes(real)
    assert before[0] > 0
    assert before[1] > 0
    drawn = _draw_everything(surface, lambda kind: True, 0)
    assert drawn > 3000
    assert _sizes(real) == before


def test_drawing_dimmed_drifters_adds_no_cache_entries_for_the_warmed_looks(real: Sprites) -> None:
    """The island is left out: its touch is a block, never a hit, so the run never dims it."""
    surface = _transparent()
    before = _sizes(real)
    drawn = _draw_everything(
        surface,
        lambda kind: kind is DrifterType.COIN or kind in HIT_TYPES,
        TUNING.hazards.rehit_cooldown_ticks,
    )
    assert drawn > 2000
    assert _sizes(real) == before


def test_a_dimmed_drifter_is_the_same_picture_darker(real: Sprites) -> None:
    for kind in HIT_TYPES:
        full = _drifter(kind, uid=2, ticks=130)
        dimmed = replace(full, rehit_ticks_left=5)
        assert dimmed.brightness() < 1.0 == full.brightness()
        bright, _ = _alpha_shot(full, (340, 340))
        dark, _ = _alpha_shot(dimmed, (340, 340))
        if kind is not DrifterType.PLANET:
            assert bright.data[3::4] == dark.data[3::4], kind
        lit = sum(bright.data[0::4]) + sum(bright.data[1::4]) + sum(bright.data[2::4])
        dim = sum(dark.data[0::4]) + sum(dark.data[1::4]) + sum(dark.data[2::4])
        assert dim < lit, kind


def test_every_hit_drifter_is_the_kind_the_cache_test_dims() -> None:
    for kind in HIT_TYPES:
        assert _drifter(kind).effect_on_touch() is TouchEffect.HIT
    assert _drifter(DrifterType.FLOATING_ISLAND).effect_on_touch() is TouchEffect.BLOCK


def test_the_installed_store_is_the_one_the_views_use(real: Sprites) -> None:
    assert installed_sprites() is real
