"""The drifter registry: one class per drifter type, and nothing else.

Source: docs/contracts/systems/drifters.md, Interface and Rules, Registry.
"""

import inspect
import logging

from core.drifters.base import Drifter, DrifterType

log = logging.getLogger(__name__)

_CLASSES: dict[DrifterType, type[Drifter]] = {}
"""The registered classes. Filled once at import by `register_drifter`."""


def register_drifter[G: Drifter](cls: type[G]) -> type[G]:
    """Register `cls` under its `drifter_type`. Class decorator.

    Raises TypeError for an abstract class or one with no `drifter_type`, and ValueError
    when the type already has a class.
    """
    if inspect.isabstract(cls):
        raise TypeError(f"{cls.__name__} is abstract and can't be registered")
    drifter_type: DrifterType | None = getattr(cls, "drifter_type", None)
    if drifter_type is None:
        raise TypeError(f"{cls.__name__} has no drifter_type")
    if drifter_type in _CLASSES:
        raise ValueError(f"drifter type '{drifter_type.value}' is already registered")
    _CLASSES[drifter_type] = cls
    return cls


def available_drifters() -> frozenset[DrifterType]:
    """Return every registered drifter type."""
    return frozenset(_CLASSES)


def drifter_class(drifter_type: DrifterType) -> type[Drifter]:
    """Return the class registered for `drifter_type`. Raises ValueError when none is."""
    if drifter_type not in _CLASSES:
        raise ValueError(f"no class registered for drifter type '{drifter_type.value}'")
    return _CLASSES[drifter_type]
