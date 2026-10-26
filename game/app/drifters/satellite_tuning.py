"""The satellite's tuning file: its one own field, and the loader that checks it.

The file follows drifter-tuning.schema.json and adds `angle_degrees` to every variant, with exactly
two boxes (the body, then the panel bar). The loader registers itself by type, so the app names no
drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (A drifter's own fields);
docs/contracts/schemas/satellite-tuning.schema.json.
"""

from app.drifters.checks import OwnFields, is_number, load_generic
from app.drifters.registry import register_tuning
from core.collision import Box, Hitbox
from core.drifters.base import DrifterType
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.tuning import DrifterTypeTuning


def _satellite_extra(
    name: str, path: str, fields: dict[str, object], hitbox: Hitbox
) -> SatelliteVariantExtra:
    """Check a satellite variant: exactly two boxes (body, then panel bar) and its angle.

    Source: satellite-tuning.schema.json; drifters/02-satellite.md, variants.
    """
    if len(hitbox) != 2 or not all(isinstance(shape, Box) for shape in hitbox):
        raise ValueError(f"{name}: {path}.hitbox must be exactly two boxes")
    angle: object = fields["angle_degrees"]
    if not is_number(angle) or not 0 <= angle < 90:
        raise ValueError(f"{name}: {path}.angle_degrees must be a number >= 0 and < 90")
    return SatelliteVariantExtra(angle_degrees=angle)


_OWN: OwnFields = (frozenset({"angle_degrees"}), _satellite_extra)
"""The satellite's own variant field and its checker. Source: satellite-tuning.schema.json."""


@register_tuning(DrifterType.SATELLITE)
def _load_satellite(name: str, data: object) -> DrifterTypeTuning:
    """Check the satellite's file: the shared schema, plus its angle on every variant."""
    return load_generic(name, data, _OWN)
