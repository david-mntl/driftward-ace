"""The drifter sprite store: strips loaded once, and every derived image built once and kept.

A view asks for a frame in the size, mirror, angle and brightness it needs. The first ask builds
it (flip, smoothscale, rotozoom, a dimmed copy) and the next asks get the same surface, so a draw
after warm-up is a dictionary lookup and a blit. The views' `warm` functions ask for everything the
game will need while the screen is still loading, so no spawn builds an image mid-run.

Every cache key is built from whole numbers that take few values: a file, a frame index, a size in
px, an angle in whole degrees, a brightness step. Nothing is keyed by a float that moves each frame.

Brightness is rounded to one of `dim_steps` levels. Level `dim_steps` is full brightness; a lower
level multiplies the RGB of an image and leaves its alpha alone.

The frame helpers (`strip_frame`, `eased_frame`) turn the game's tick count into a frame index.
They count ticks, never wall time, so a pause freezes them. `mix` offsets every drifter's loop by
its uid so a group never animates in lockstep.

A drifter's `seed` is its uid plus a salt drawn once from `random` when the sprites are built, so
the looks a wave gets (`look_pick` is random) differ from run to run and never change mid-run.

Source: 12-art-and-audio.md, rules 3, 9, 10 and 13. It only loads and draws.
"""

import logging
import math
import random
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pygame

from ui.drifters.looks import DrifterLooks, StripOrder, StripRule

log = logging.getLogger(__name__)

type Size = tuple[int, int]
"""A width and a height, px."""

type _ImageKey = tuple[str, int, bool, int, int, int, int]
"""(file, frame, mirrored, width, height, angle, level). Width and height are 0 for the native size,
angle is 0 for no turn."""

_SALT_BITS: Final[int] = 32
"""Bits of the per-install salt."""

_MASK: Final[int] = 0xFFFFFFFF
"""Keeps `mix` in 32 bits."""

_MIX_ADD: Final[int] = 0x165667B1
_MIX_A: Final[int] = 0x9E3779B1
_MIX_B: Final[int] = 0x85EBCA6B
_MIX_C: Final[int] = 0x2C1B3C6D
_MIX_D: Final[int] = 0x297A2D39
"""Integer-hash constants (golden ratio and murmur3). Not game values: they only scatter bits."""

_LOOP_SALT: Final[int] = 1
"""Salt of the loop's starting frame, so it differs from the look pick for the same uid."""


def mix(first: int, second: int) -> int:
    """Return a 32-bit pseudo-random number from two whole numbers. Pure and fast."""
    value: int = (first * _MIX_A + second * _MIX_B + _MIX_ADD) & _MASK
    value ^= value >> 15
    value = (value * _MIX_C) & _MASK
    value ^= value >> 12
    value = (value * _MIX_D) & _MASK
    return value ^ (value >> 15)


def pick(seed: int, count: int) -> int:
    """Return which of `count` looks the drifter has, 0 .. count - 1. Stable for one `seed`."""
    return mix(seed, 0) % count


def loop_frame(uid: int, step: int, count: int) -> int:
    """Return frame `step` of a loop of `count` frames, started at a point set by `uid`."""
    return (step + mix(uid, _LOOP_SALT)) % count


def random_frame(uid: int, step: int, count: int) -> int:
    """Return a pseudo-random frame for `step`, never the frame of `step - 1`.

    Even and odd frames take turns (which parity comes first depends on `uid`), and each step picks
    at random inside its parity, so two steps in a row can never match.
    """
    if count < 2:
        return 0
    parity: int = (step + uid) % 2
    pool: int = (count - parity + 1) // 2
    return 2 * (mix(uid, step) % pool) + parity


def frame_for_step(rule: StripRule, uid: int, step: int, count: int) -> int:
    """Return the frame shown at `step` (`ticks_per_frame` ticks long) in the rule's order."""
    if rule.order is StripOrder.RANDOM:
        return random_frame(uid, step, count)
    return loop_frame(uid, step, count)


def strip_frame(rule: StripRule, uid: int, ticks: int, count: int) -> int:
    """Return the frame shown after `ticks` game ticks at the rule's steady speed."""
    return frame_for_step(rule, uid, ticks // rule.ticks_per_frame, count)


def eased_frame(
    rule: StripRule, end_ticks_per_frame: int, uid: int, ticks: int, span: int, count: int
) -> int:
    """Return the frame `ticks` into a `span`-tick charge whose speed eases up as it fills.

    Ticks per frame moves in a straight line from `rule.ticks_per_frame` to
    `end_ticks_per_frame` over the span. The frames shown so far are the integral of
    1 / ticks_per_frame, worked out in closed form, so the loop never jumps when the speed changes.
    """
    start: int = rule.ticks_per_frame
    done: int = min(max(ticks, 0), span)
    if start == end_ticks_per_frame:
        shown: float = done / start
    else:
        slope: float = (end_ticks_per_frame - start) / span
        shown = math.log((start + slope * done) / start) / slope
    return frame_for_step(rule, uid, math.floor(shown), count)


def scaled_size(rule: StripRule, factor: float) -> Size | None:
    """Return the frame size times `factor` in whole px, or None when that is the native size."""
    size: Size = (max(1, round(rule.frame_w * factor)), max(1, round(rule.frame_h * factor)))
    return None if size == (rule.frame_w, rule.frame_h) else size


class Sprites:
    """The loaded strips and ground images, and the caches of images built from them."""

    def __init__(
        self, looks: DrifterLooks, folder: Path, warm_levels: tuple[int, ...] | None = None
    ) -> None:
        """Load every strip and ground image in `looks` from `folder`. Needs the display open.

        `warm_levels` are the brightness levels the views warm, besides full brightness (None:
        none). Raises FileNotFoundError for a missing file (from pygame) and ValueError when a
        strip's size is not a whole number of its frames.
        """
        self.looks: DrifterLooks = looks
        """The rules the strips were loaded by."""

        self.steps: int = looks.dim_steps
        """Brightness levels; level `steps` is full brightness."""

        self.warm_levels: tuple[int, ...] = tuple(dict.fromkeys((self.steps, *(warm_levels or ()))))
        """Brightness levels `warm` functions build, full brightness first."""

        self._frames: dict[str, tuple[pygame.Surface, ...]] = {
            rule.file: _load_strip(folder, rule) for rule in looks.strips()
        }
        self._grounds: tuple[pygame.Surface, ...] = tuple(
            _load_image(folder / name) for name in looks.floating_island.looks
        )
        self.salt: int = random.getrandbits(_SALT_BITS)
        """Drawn once per install. Mixed into every uid, so which look a drifter has and where its
        frames start differ from run to run (look_pick is random) but never change mid-run."""

        self._images: dict[_ImageKey, pygame.Surface] = {}
        self._built: dict[tuple[object, ...], pygame.Surface] = {}

    def count(self, rule: StripRule) -> int:
        """Return how many frames the rule's strip has."""
        return len(self._frames[rule.file])

    def seed(self, uid: int) -> int:
        """Return `uid` mixed with this install's salt: the number the frame helpers take as the
        drifter's uid. Stable for one run, different between runs."""
        return (uid + self.salt) & _MASK

    def level(self, brightness: float) -> int:
        """Return `brightness` (0..1) rounded to a level, 0 .. `steps`."""
        return min(self.steps, max(0, round(brightness * self.steps)))

    def shade(self, color: tuple[int, int, int], level: int) -> tuple[int, int, int]:
        """Return `color` with each channel times `level / steps`, rounded half up."""
        share: float = level / self.steps
        red, green, blue = color
        return (
            math.floor(red * share + 0.5),
            math.floor(green * share + 0.5),
            math.floor(blue * share + 0.5),
        )

    def image(
        self,
        rule: StripRule,
        index: int,
        level: int,
        *,
        mirror: bool = False,
        size: Size | None = None,
        angle: int = 0,
    ) -> pygame.Surface:
        """Return frame `index` of the rule's strip, mirrored, scaled to `size`, turned `angle`
        whole degrees counterclockwise, and dimmed to `level`. Built the first time it is asked.
        """
        width, height = size or (0, 0)
        return self._get((rule.file, index, mirror, width, height, angle, level))

    def ground(self, index: int) -> pygame.Surface:
        """Return the island ground image `index`, as loaded."""
        return self._grounds[index]

    def ground_count(self) -> int:
        """Return how many ground images there are."""
        return len(self._grounds)

    def built(self, key: tuple[object, ...], build: Callable[[], pygame.Surface]) -> pygame.Surface:
        """Return the image kept under `key`, calling `build` the first time. `key` must hold
        everything the image depends on: it is never rebuilt."""
        image: pygame.Surface | None = self._built.get(key)
        if image is None:
            image = build()
            self._built[key] = image
        return image

    def _get(self, key: _ImageKey) -> pygame.Surface:
        """Return the image for `key`, building it the first time."""
        image: pygame.Surface | None = self._images.get(key)
        if image is None:
            image = self._derive(key)
            self._images[key] = image
        return image

    def _derive(self, key: _ImageKey) -> pygame.Surface:
        """Build the image for `key`: a dimmed copy of the full-brightness one, or the base."""
        file, index, mirror, width, height, angle, level = key
        if level != self.steps:
            full: _ImageKey = (file, index, mirror, width, height, angle, self.steps)
            return _dimmed(self._get(full), level, self.steps)
        image: pygame.Surface = self._frames[file][index]
        if mirror:
            image = pygame.transform.flip(image, True, False)
        if width:
            image = pygame.transform.smoothscale(image, (width, height))
        if angle:
            image = pygame.transform.rotozoom(image, angle, 1.0)
        return image


_installed: list[Sprites] = []
"""The sprites the views draw from: empty until `install_sprites`, then one entry."""


def install_sprites(sprites: Sprites) -> None:
    """Make `sprites` the store every drifter view draws from."""
    _installed[:] = [sprites]


def installed_sprites() -> Sprites:
    """Return the installed store. Raises RuntimeError when none was installed yet."""
    if not _installed:
        raise RuntimeError(
            "drifter sprites are not installed: call app.drifter_looks_tuning."
            "install_drifter_looks once the display is open"
        )
    return _installed[0]


def sprites_folder() -> Path:
    """Return the folder the game's sprite files live in, `game/assets/sprites`."""
    return Path(__file__).resolve().parents[2] / "assets" / "sprites"


def _load_image(path: Path) -> pygame.Surface:
    """Read one PNG and convert it to the display format with alpha."""
    return pygame.image.load(str(path)).convert_alpha()


def _load_strip(folder: Path, rule: StripRule) -> tuple[pygame.Surface, ...]:
    """Load the rule's strip and cut it into frames.

    Raises ValueError when its height is not `frame_h` or its width is not a whole number of
    `frame_w` px frames.
    """
    strip: pygame.Surface = _load_image(folder / rule.file)
    width, height = strip.get_size()
    if height != rule.frame_h or width % rule.frame_w != 0:
        raise ValueError(
            f"assets/sprites/{rule.file}: size {width}x{height} is not a whole number of "
            f"{rule.frame_w}x{rule.frame_h} px frames (tuning/drifter_looks.json)"
        )
    frames: tuple[pygame.Surface, ...] = tuple(
        strip.subsurface((i * rule.frame_w, 0, rule.frame_w, rule.frame_h)).copy()
        for i in range(width // rule.frame_w)
    )
    log.info("%s loaded: %d frames of %dx%d px", rule.file, len(frames), rule.frame_w, rule.frame_h)
    return frames


def _dimmed(image: pygame.Surface, level: int, steps: int) -> pygame.Surface:
    """Return a copy of `image` with its RGB times `level / steps`. Alpha is unchanged."""
    result: pygame.Surface = image.copy()
    value: int = round(255 * level / steps)
    result.fill((value, value, value, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return result
