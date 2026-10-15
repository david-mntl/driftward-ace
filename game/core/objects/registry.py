"""The object registry: one class per object type, and nothing else.

Source: docs/contracts/systems/objects.md, Interface and Rules, Registry.
"""

import inspect
import logging

from core.objects.base import GameObject, ObjectType

log = logging.getLogger(__name__)

_CLASSES: dict[ObjectType, type[GameObject]] = {}
"""The registered classes. Filled once at import by `register_object`."""


def register_object[G: GameObject](cls: type[G]) -> type[G]:
    """Register `cls` under its `object_type`. Class decorator.

    Raises TypeError for an abstract class or one with no `object_type`, and ValueError
    when the type already has a class.
    """
    if inspect.isabstract(cls):
        raise TypeError(f"{cls.__name__} is abstract and can't be registered")
    object_type: ObjectType | None = getattr(cls, "object_type", None)
    if object_type is None:
        raise TypeError(f"{cls.__name__} has no object_type")
    if object_type in _CLASSES:
        raise ValueError(f"object type '{object_type.value}' is already registered")
    _CLASSES[object_type] = cls
    return cls


def available_objects() -> frozenset[ObjectType]:
    """Return every registered object type."""
    return frozenset(_CLASSES)


def object_class(object_type: ObjectType) -> type[GameObject]:
    """Return the class registered for `object_type`. Raises ValueError when none is."""
    if object_type not in _CLASSES:
        raise ValueError(f"no class registered for object type '{object_type.value}'")
    return _CLASSES[object_type]
