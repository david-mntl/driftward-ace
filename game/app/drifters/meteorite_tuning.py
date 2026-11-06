"""The meteorite's tuning file: the shared schema, plus `drawn_width` on every variant.

The file follows drifter-tuning.schema.json. Each variant adds `drawn_width`, the side of the
square its drawn rock fits in (the art is wider than the hit circle). The loader registers itself
by type, so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (A drifter's own fields);
drifters/01-meteorite.md, looks.
"""

from app.drifters.checks import OwnFields, check_positive, load_generic
from app.drifters.registry import register_tuning
from core.collision import Hitbox
from core.drifters.base import DrifterType, VariantExtra
from core.drifters.meteorite import MeteoriteVariantExtra
from core.drifters.tuning import DrifterTypeTuning


def _meteorite_extra(
    name: str, path: str, fields: dict[str, object], hitbox: Hitbox
) -> VariantExtra:
    """Check the variant's `drawn_width` (a number > 0, at least its width) and build its extra."""
    drawn: float = check_positive(name, f"{path}.drawn_width", fields["drawn_width"])
    width: object = fields["width"]
    if isinstance(width, int | float) and drawn < width:
        raise ValueError(f"{name}: {path}.drawn_width must be at least width")
    return MeteoriteVariantExtra(drawn_width=drawn)


_OWN: OwnFields = (frozenset({"drawn_width"}), _meteorite_extra)
"""The meteorite's own variant field and its checker."""


@register_tuning(DrifterType.METEORITE)
def _load_meteorite(name: str, data: object) -> DrifterTypeTuning:
    """Check the meteorite's file: the shared schema, plus `drawn_width` on every variant."""
    return load_generic(name, data, _OWN)
