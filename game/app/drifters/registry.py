"""The tuning loader registry: one loader per drifter type that has a tuning file of its own.

A drifter type with no loader here follows drifter-tuning.schema.json and is checked by
`app.drifters.checks.load_generic`. Each drifter's own module registers its loader by type, so the
app names no drifter. Filled once at import. Not a startup module: only `app.tuning` imports it,
inside the guard.

Source: docs/contracts/systems/app.md, Rules, Tuning loader.
"""

from collections.abc import Callable

from core.drifters.base import DrifterType
from core.drifters.tuning import DrifterTypeTuning

type TuningLoader = Callable[[str, object], DrifterTypeTuning]
"""Checks one drifter's tuning file and builds its record.

Called with (the file's name from the game folder down, its parsed JSON). Raises ValueError
naming the file and the field.
"""

_LOADERS: dict[DrifterType, TuningLoader] = {}
"""The registered loaders. Filled once at import by `register_tuning`."""


def register_tuning(drifter_type: DrifterType) -> Callable[[TuningLoader], TuningLoader]:
    """Register the decorated loader under `drifter_type`. Function decorator.

    Raises ValueError when the type already has a loader.
    """

    def decorator(loader: TuningLoader) -> TuningLoader:
        if drifter_type in _LOADERS:
            raise ValueError(f"drifter type '{drifter_type.value}' already has a tuning loader")
        _LOADERS[drifter_type] = loader
        return loader

    return decorator


def tuning_loader(drifter_type: DrifterType) -> TuningLoader | None:
    """Return the loader registered for `drifter_type`, or None for the shared schema."""
    return _LOADERS.get(drifter_type)
