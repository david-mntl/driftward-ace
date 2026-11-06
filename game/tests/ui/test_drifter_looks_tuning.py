"""Drifter looks tests: the loader, and the strips and ground images the file names.

Direct-edit feature `drifter-sprites` (no contract, no task file). The spec is the implementation
report docs/reports/implementation/ui/drifter-sprites-ui-developer.md, the Director's strip table
(frame count, size, ticks a frame, order) and game/tuning/drifter_looks.json. GDD:
12-art-and-audio.md, rules 9, 10 and 13.

The loader (`load_drifter_looks`) reads the file in `app.drifter_looks_tuning.TUNING_DIR`, so each
bad-file test writes a copy into `tmp_path` and points that name at it, the way `test_hud_tuning`
does. Every bad value must raise ValueError naming `tuning/drifter_looks.json` and the field.
"""

import copy
import json
import re
import shutil
from collections.abc import Iterator
from pathlib import Path

import pygame
import pytest

import app.drifter_looks_tuning as looks_tuning
import app.tuning as drifter_tuning
from app.drifter_looks_tuning import LOOKS_FILE, load_drifter_looks
from app.tuning import load_tuning
from core.drifters.base import DrifterType
from core.drifters.floating_island import IslandVariantExtra
from core.drifters.meteorite import MeteoriteVariantExtra
from ui.drifters.looks import DrifterLooks, StripOrder, StripRule
from ui.drifters.sprites import Sprites, sprites_folder

MESSAGE_START = r"^tuning/drifter_looks\.json: "
"""Every loader error starts with the file's name."""

FILE_NAME = "tuning/drifter_looks.json"
"""The name every error starts with. Source: the loader's docstring and the implementation
report (ValueError names the file and the field)."""

SHIPPED: Path = Path(looks_tuning.__file__).resolve().parent.parent / "tuning" / LOOKS_FILE

SPEC: dict[str, tuple[int, int, int, int, str]] = {
    "ufo_broken.png": (8, 40, 20, 3, "random"),
    "ufo_clean.png": (8, 40, 20, 5, "loop"),
    "planet_marble.png": (24, 64, 64, 8, "loop"),
    "fireball.png": (6, 64, 64, 4, "loop"),
    "coin_common.png": (8, 24, 24, 6, "loop"),
    "coin_rare.png": (8, 24, 24, 6, "loop"),
    "electric_ball_charge.png": (8, 24, 24, 6, "loop"),
    "electric_ball_fire.png": (6, 24, 24, 3, "random"),
    "electric_ball_ring.png": (6, 128, 128, 3, "random"),
    "chain_node_charge.png": (8, 18, 18, 6, "loop"),
    "chain_node_fire.png": (6, 18, 18, 3, "random"),
    "chain_arc.png": (6, 181, 16, 3, "random"),
    "meteorite_rock_a.png": (32, 36, 36, 3, "loop"),
    "meteorite_rock_b.png": (32, 36, 36, 3, "loop"),
    "meteorite_rock_c.png": (32, 36, 36, 3, "loop"),
    "meteorite_rock_d.png": (32, 36, 36, 3, "loop"),
}
"""file: (frames, frame width, frame height, ticks a frame, order). Source: the Director's strip
table for the drifter sprites (frames, frame size, ticks a frame, order), 2026-11-05; the four
meteorite skins from drifters/01-meteorite.md, look_frames (32 frames, the variant size square: the
medium rock 28 plus the art past the circle = 36) and look_ticks_per_frame (3), and the report's
`## Meteorite` section."""

GROUND_SIZE: tuple[int, int] = (320, 120)
"""Source: drifters/05-floating-islands.md, art_canvas (320 x 120, the 120 x 120 box its crop)."""


def _shipped() -> dict[str, object]:
    data: dict[str, object] = json.loads(SHIPPED.read_text(encoding="utf-8"))
    return data


def _walk(node: object, prefix: tuple[object, ...] = ()) -> Iterator[tuple[object, ...]]:
    """Every object key and every list-of-objects entry as a path of keys and indexes."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield (*prefix, key)
            yield from _walk(value, (*prefix, key))
    elif isinstance(node, list) and node and all(isinstance(item, dict) for item in node):
        for index, item in enumerate(node):
            yield from _walk(item, (*prefix, index))


def _field(path: tuple[object, ...]) -> str:
    """The loader's wording of a path: `ufo.looks[0].file`."""
    text = ""
    for part in path:
        text += f"[{part}]" if isinstance(part, int) else f"{'.' if text else ''}{part}"
    return text


def _at(data: object, path: tuple[object, ...]) -> object:
    for part in path:
        data = data[part]  # type: ignore[index]
    return data


def _edited(path: tuple[object, ...], value: object, *, drop: bool = False) -> dict[str, object]:
    """The shipped file with the field at `path` set to `value`, or taken out."""
    data = copy.deepcopy(_shipped())
    parent = _at(data, path[:-1])
    if drop:
        del parent[path[-1]]  # type: ignore[attr-defined]
    else:
        parent[path[-1]] = value  # type: ignore[index]
    return data


def _load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: object) -> DrifterLooks:
    (tmp_path / LOOKS_FILE).write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(looks_tuning, "TUNING_DIR", tmp_path)
    return load_drifter_looks()


FIELDS: list[tuple[object, ...]] = [path for path in _walk(_shipped()) if isinstance(path[-1], str)]
"""Every field the file has, at every depth: each one is required."""

LEAVES: list[tuple[object, ...]] = [
    path for path in FIELDS if not isinstance(_at(_shipped(), path), dict)
]
"""Every field that holds a value (a number, a text, a color or a list of file names)."""


def _ids(paths: list[tuple[object, ...]]) -> list[str]:
    return [_field(path) for path in paths]


def test_the_shipped_file_loads_and_holds_every_strip_of_the_spec() -> None:
    looks = load_drifter_looks()
    raw = _shipped()
    assert looks.dim_steps == raw["dim_steps"]
    found = {
        rule.file: (rule.frame_w, rule.frame_h, rule.ticks_per_frame, rule.order.value)
        for rule in looks.strips()
    }
    assert found == {name: spec[1:] for name, spec in SPEC.items()}
    assert len(looks.strips()) == len(SPEC)
    assert set(looks.floating_island.looks) == {
        "island_ground_1.png",
        "island_ground_2.png",
        "island_ground_3.png",
    }
    assert [rule.file for rule in looks.meteorite.looks] == [
        "meteorite_rock_a.png",
        "meteorite_rock_b.png",
        "meteorite_rock_c.png",
        "meteorite_rock_d.png",
    ]
    assert looks.meteorite.art_hitbox_width == 28
    assert looks.planet.field_ring_radius_step >= 1
    assert looks.chain_lightning.charge_ticks_per_frame_end >= 1
    assert looks.electric_ball.charge_ticks_per_frame_end >= 1


@pytest.mark.parametrize("path", FIELDS, ids=_ids(FIELDS))
def test_a_missing_field_raises_naming_the_file_and_the_field(
    path: tuple[object, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="is missing") as caught:
        _load(tmp_path, monkeypatch, _edited(path, None, drop=True))
    assert str(caught.value).startswith(f"{FILE_NAME}: ")
    assert str(caught.value).split(": ", 1)[1].startswith(_field(path))


def _wrong_values(value: object) -> list[object]:
    """Values of the wrong type for a field that holds `value`."""
    if isinstance(value, bool):
        return [1, "true"]
    if isinstance(value, int):
        return ["3", 2.5, True, None, [1]]
    if isinstance(value, str):
        return [5, None, ["a"], True]
    return ["red", 5, None, {}]


@pytest.mark.parametrize("path", LEAVES, ids=_ids(LEAVES))
def test_a_value_of_the_wrong_type_raises_naming_the_file_and_the_field(
    path: tuple[object, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for wrong in _wrong_values(_at(_shipped(), path)):
        with pytest.raises(ValueError, match=MESSAGE_START) as caught:
            _load(tmp_path, monkeypatch, _edited(path, wrong))
        message = str(caught.value)
        assert message.startswith(f"{FILE_NAME}: "), (wrong, message)
        assert _field(path) in message, (wrong, message)


def test_a_wrong_object_where_an_object_belongs_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for path in [path for path in FIELDS if isinstance(_at(_shipped(), path), dict)]:
        with pytest.raises(ValueError, match=MESSAGE_START) as caught:
            _load(tmp_path, monkeypatch, _edited(path, 5))
        assert str(caught.value).startswith(f"{FILE_NAME}: {_field(path)}")
    with pytest.raises(ValueError, match="must be an object"):
        _load(tmp_path, monkeypatch, [])


def test_an_unknown_order_raises_naming_the_file_the_field_and_the_choices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    orders = [path for path in FIELDS if path[-1] == "order"]
    assert len(orders) >= 8
    for path in orders:
        for bad in ("shuffle", "", "LOOP", 3, None):
            with pytest.raises(ValueError, match=MESSAGE_START) as caught:
                _load(tmp_path, monkeypatch, _edited(path, bad))
            message = str(caught.value)
            assert message.startswith(f"{FILE_NAME}: {_field(path)}"), message
            assert all(order.value in message for order in StripOrder), message


def test_an_unknown_field_and_a_broken_file_raise_naming_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    extra = _edited(("ufo", "looks", 0, "speed"), 1)
    with pytest.raises(ValueError, match=r"ufo\.looks.*not a known field") as caught:
        _load(tmp_path, monkeypatch, extra)
    assert str(caught.value).startswith(f"{FILE_NAME}: ")
    (tmp_path / LOOKS_FILE).write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(looks_tuning, "TUNING_DIR", tmp_path)
    with pytest.raises(ValueError, match="not valid JSON") as broken:
        load_drifter_looks()
    assert str(broken.value).startswith(f"{FILE_NAME}: ")


@pytest.mark.parametrize(
    "path",
    [
        path
        for path in LEAVES
        if path[-1] in ("ticks_per_frame", "frame_w", "frame_h", "dim_steps", "art_hitbox_width")
    ],
    ids=_ids(
        [
            path
            for path in LEAVES
            if path[-1]
            in ("ticks_per_frame", "frame_w", "frame_h", "dim_steps", "art_hitbox_width")
        ]
    ),
)
def test_a_count_or_size_below_one_raises(
    path: tuple[object, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for bad in (0, -1):
        with pytest.raises(ValueError, match="integer >= 1") as caught:
            _load(tmp_path, monkeypatch, _edited(path, bad))
        assert _field(path) in str(caught.value)


@pytest.mark.parametrize("value", [[0, 0, 0], [0, 120, 255], [255, 0, 255]])
def test_a_color_channel_of_zero_loads(
    value: list[int], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A color is RGB 0..255 (looks.py: `field_ring_color`, `ray_color`, `outline_color`)."""
    colors = [path for path in LEAVES if str(path[-1]).endswith("color")]
    assert len(colors) == 4
    for path in colors:
        looks = _load(tmp_path, monkeypatch, _edited(path, value))
        assert looks.dim_steps >= 1


def test_a_head_center_of_zero_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader lists `fireball.art_head_center` among the integers that may be 0."""
    path = ("fireball", "art_head_center")
    looks = _load(tmp_path, monkeypatch, _edited(path, [0, 0]))
    assert looks.fireball.art_head_center == (0, 0)


def test_a_color_channel_above_255_or_a_short_color_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    colors = [path for path in LEAVES if str(path[-1]).endswith("color")]
    for path in colors:
        for bad in ([1, 2, 256], [1, 2], [1, 2, 3, 4]):
            with pytest.raises(ValueError, match=MESSAGE_START) as caught:
                _load(tmp_path, monkeypatch, _edited(path, bad))
            assert str(caught.value).startswith(f"{FILE_NAME}: {_field(path)}")


@pytest.fixture(scope="module")
def display() -> None:
    pygame.init()
    pygame.display.set_mode((640, 480))


def _copy_sprites(tmp_path: Path) -> Path:
    folder = tmp_path / "sprites"
    shutil.copytree(sprites_folder(), folder)
    return folder


def test_a_strip_that_is_not_a_whole_number_of_frames_raises_naming_the_file(
    display: None, tmp_path: Path
) -> None:
    looks = load_drifter_looks()
    folder = _copy_sprites(tmp_path)
    for rule in looks.strips():
        for width, height in (
            (rule.frame_w * 3 + 1, rule.frame_h),
            (rule.frame_w * 3, rule.frame_h + 1),
        ):
            shutil.copy(sprites_folder() / rule.file, folder / rule.file)
            image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.image.save(image, str(folder / rule.file))
            with pytest.raises(ValueError, match=re.escape(rule.file)) as caught:
                Sprites(looks, folder)
            message = str(caught.value)
            assert rule.file in message, message
            assert "drifter_looks.json" in message, message
            assert f"{width}x{height}" in message, message
        shutil.copy(sprites_folder() / rule.file, folder / rule.file)
    Sprites(looks, folder)


def test_a_missing_strip_file_raises(display: None, tmp_path: Path) -> None:
    looks = load_drifter_looks()
    folder = _copy_sprites(tmp_path)
    (folder / "fireball.png").unlink()
    with pytest.raises(FileNotFoundError, match=r"fireball\.png"):
        Sprites(looks, folder)


@pytest.mark.parametrize("rule", load_drifter_looks().strips(), ids=lambda rule: rule.file)
def test_every_strip_is_there_with_the_tuned_frame_size_and_a_whole_frame_count(
    rule: StripRule,
) -> None:
    frames, frame_w, frame_h, ticks, order = SPEC[rule.file]
    path = sprites_folder() / rule.file
    assert path.is_file(), f"{path} is missing"
    image = pygame.image.load(str(path))
    width, height = image.get_size()
    assert (rule.frame_w, rule.frame_h) == (frame_w, frame_h)
    assert height == rule.frame_h
    assert width % rule.frame_w == 0
    assert width // rule.frame_w == frames
    assert (rule.ticks_per_frame, rule.order.value) == (ticks, order)
    data = pygame.image.tobytes(image, "RGBA")
    for index in range(frames):
        ink = 0
        for row in range(height):
            start = (row * width + index * frame_w) * 4
            ink += sum(1 for alpha in data[start + 3 : start + frame_w * 4 : 4] if alpha)
        assert ink > 0, f"{rule.file} frame {index} is empty"


def test_every_island_ground_is_there_and_big_enough_for_every_island() -> None:
    looks = load_drifter_looks()
    tuning = load_tuning()
    island = tuning.drifters[DrifterType.FLOATING_ISLAND]
    widths = {
        variant.width
        for variant in island.variants.values()
        if isinstance(variant.extra, IslandVariantExtra)
    }
    heights = {variant.height for variant in island.variants.values()}
    assert widths
    assert heights
    for name in looks.floating_island.looks:
        path = sprites_folder() / name
        assert path.is_file(), f"{path} is missing"
        width, height = pygame.image.load(str(path)).get_size()
        assert (width, height) == GROUND_SIZE
        assert width >= max(widths)
        assert height >= max(heights)


def test_the_meteorite_needs_at_least_one_skin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match=MESSAGE_START) as caught:
        _load(tmp_path, monkeypatch, _edited(("meteorite", "looks"), []))
    assert "meteorite.looks" in str(caught.value)


# --- the meteorite's tuning file: `drawn_width` on every variant --------------------------------

METEORITE_FILE = "tuning/drifters/meteorite.json"
DRAWN_WIDTHS = {"small": 26, "medium": 36, "big": 52}
"""Source: the report's `## Meteorite` section: width x 36 / 28, rounded up (20, 28, 40 px wide)."""


def _meteorite_tuning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, edit: object = None
) -> dict[str, object]:
    """`load_tuning()` on a copy of the tuning folder whose meteorite file `edit` changed."""
    folder = tmp_path / "tuning"
    shutil.copytree(drifter_tuning.TUNING_DIR, folder)
    path = folder / "drifters" / "meteorite.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if callable(edit):
        edit(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(drifter_tuning, "TUNING_DIR", folder)
    loaded: dict[str, object] = {"tuning": drifter_tuning.load_tuning()}
    return loaded


def test_the_shipped_meteorite_file_gives_every_variant_its_drawn_width(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tuning = _meteorite_tuning(tmp_path, monkeypatch)["tuning"]
    variants = tuning.drifters[DrifterType.METEORITE].variants  # type: ignore[attr-defined]
    assert set(variants) == set(DRAWN_WIDTHS)
    for name, variant in variants.items():
        assert isinstance(variant.extra, MeteoriteVariantExtra)
        assert variant.extra.drawn_width == DRAWN_WIDTHS[name]
        assert variant.extra.drawn_width >= variant.width


@pytest.mark.parametrize("variant", list(DRAWN_WIDTHS))
def test_a_meteorite_variant_without_drawn_width_raises_naming_the_file_and_field(
    variant: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="is missing") as caught:
        _meteorite_tuning(
            tmp_path, monkeypatch, lambda data: data["variants"][variant].pop("drawn_width")
        )
    assert str(caught.value) == f"{METEORITE_FILE}: variants.{variant}.drawn_width is missing"


@pytest.mark.parametrize("bad", ["36", True, None, [36], {"w": 36}, 0, -5, 0.0])
def test_a_meteorite_drawn_width_that_is_not_a_positive_number_raises(
    bad: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="drawn_width") as caught:
        _meteorite_tuning(
            tmp_path, monkeypatch, lambda data: data["variants"]["medium"].update(drawn_width=bad)
        )
    assert str(caught.value).startswith(f"{METEORITE_FILE}: variants.medium.drawn_width must be")


@pytest.mark.parametrize("narrow", [27, 27.99, 19.5, 1])
def test_a_drawn_width_below_the_variant_width_raises(
    narrow: float, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The loader enforces drawn_width >= width, so the drawn box is never under the footprint."""
    with pytest.raises(ValueError, match="drawn_width must be at least width") as caught:
        _meteorite_tuning(
            tmp_path,
            monkeypatch,
            lambda data: data["variants"]["medium"].update(drawn_width=narrow),
        )
    assert str(caught.value).startswith(f"{METEORITE_FILE}: variants.medium.drawn_width")


@pytest.mark.parametrize("wide", [28, 28.0, 36.5, 100])
def test_a_drawn_width_of_at_least_the_width_loads(
    wide: float, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tuning = _meteorite_tuning(
        tmp_path, monkeypatch, lambda data: data["variants"]["medium"].update(drawn_width=wide)
    )["tuning"]
    extra = tuning.drifters[DrifterType.METEORITE].variants["medium"].extra  # type: ignore[attr-defined]
    assert isinstance(extra, MeteoriteVariantExtra)
    assert extra.drawn_width == wide


def test_the_meteorite_file_refuses_an_unknown_variant_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="not a known field"):
        _meteorite_tuning(
            tmp_path, monkeypatch, lambda data: data["variants"]["small"].update(foo=1)
        )
