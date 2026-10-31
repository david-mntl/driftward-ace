"""The satellite's tuning file: its own fields, and the loader that checks them.

The file follows drifter-tuning.schema.json and adds the angle, the panel swing, the field speed
and `swing_hitbox` (the panel boxes that turn with the swing) to every variant. `hitbox` holds the
body, which stays still. The loader registers itself by type, so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (A drifter's own fields);
docs/contracts/schemas/satellite-tuning.schema.json.
"""

import math

from app.drifters.checks import OwnFields, check_positive, check_shape, is_number, load_generic
from app.drifters.registry import register_tuning
from core.collision import Box, Hitbox
from core.drifters.base import DrifterType
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.tuning import DrifterTypeTuning

_EDGE_TOLERANCE: float = 1e-9
"""px. Absorbs floating point error when a turned corner sits exactly on the footprint's edge."""


def _whole(name: str, path: str, value: object) -> int:
    """Return value if it is an int >= 1 (never a bool), else raise."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name}: {path} must be a whole number >= 1")
    return value


def _swing_boxes(name: str, path: str, value: object) -> tuple[Box, ...]:
    """Check `swing_hitbox`: a list of one or more boxes. Returns them."""
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name}: {path} must be a list of one or more boxes")
    boxes: list[Box] = []
    for index, item in enumerate(value):
        shape = check_shape(name, f"{path}[{index}]", item)
        if not isinstance(shape, Box):
            raise ValueError(f"{name}: {path}[{index}] must be a box")
        boxes.append(shape)
    return tuple(boxes)


def _check_swing_inside(
    name: str,
    path: str,
    boxes: tuple[Box, ...],
    degrees: float,
    frames: int,
    width: float,
    height: float,
) -> None:
    """Raise unless every panel box, turned to every swing step, lies inside the footprint.

    Source: 07-drifters.md, rule 8 (a hitbox is never bigger than what the player sees).
    """
    half_w: float = width / 2
    half_h: float = height / 2
    for step in range(frames):
        turn: float = math.radians(degrees * math.sin(2 * math.pi * step / frames))
        cos_t, sin_t = math.cos(turn), math.sin(turn)
        for index, box in enumerate(boxes):
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                px: float = box.cx + sx * box.w / 2
                py: float = box.cy + sy * box.h / 2
                x: float = px * cos_t + py * sin_t
                y: float = -px * sin_t + py * cos_t
                if abs(x) > half_w + _EDGE_TOLERANCE or abs(y) > half_h + _EDGE_TOLERANCE:
                    raise ValueError(
                        f"{name}: {path}.swing_hitbox[{index}] leaves the "
                        f"{width:g} x {height:g} footprint at swing step {step}"
                    )


def _satellite_extra(
    name: str, path: str, fields: dict[str, object], hitbox: Hitbox
) -> SatelliteVariantExtra:
    """Check a satellite variant's own fields and build its extra.

    Source: satellite-tuning.schema.json; drifters/02-satellite.md, variants.
    """
    angle: object = fields["angle_degrees"]
    if not is_number(angle) or not 0 <= angle < 90:
        raise ValueError(f"{name}: {path}.angle_degrees must be a number >= 0 and < 90")
    degrees: object = fields["swing_degrees"]
    if not is_number(degrees) or not 0 <= degrees < 90:
        raise ValueError(f"{name}: {path}.swing_degrees must be a number >= 0 and < 90")
    frames: int = _whole(name, f"{path}.swing_frames", fields["swing_frames"])
    ticks: int = _whole(name, f"{path}.swing_ticks_per_frame", fields["swing_ticks_per_frame"])
    field_ticks: int = _whole(
        name, f"{path}.field_ticks_per_frame", fields["field_ticks_per_frame"]
    )
    panels: tuple[Box, ...] = _swing_boxes(name, f"{path}.swing_hitbox", fields["swing_hitbox"])
    width: float = check_positive(name, f"{path}.width", fields["width"])
    height: float = check_positive(name, f"{path}.height", fields["height"])
    _check_swing_inside(name, path, panels, degrees, frames, width, height)
    return SatelliteVariantExtra(
        angle_degrees=angle,
        swing_degrees=degrees,
        swing_frames=frames,
        swing_ticks_per_frame=ticks,
        field_ticks_per_frame=field_ticks,
        swing_hitbox=panels,
    )


_OWN: OwnFields = (
    frozenset(
        {
            "angle_degrees",
            "swing_degrees",
            "swing_frames",
            "swing_ticks_per_frame",
            "field_ticks_per_frame",
            "swing_hitbox",
        }
    ),
    _satellite_extra,
)
"""The satellite's own variant fields and their checker. Source: satellite-tuning.schema.json."""


@register_tuning(DrifterType.SATELLITE)
def _load_satellite(name: str, data: object) -> DrifterTypeTuning:
    """Check the satellite's file: the shared schema, plus its own fields on every variant."""
    return load_generic(name, data, _OWN)
