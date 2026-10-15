"""The view registry and `render_object`: which look draws which object, and in which phase.

Source: docs/contracts/systems/objects.md, game/ui/objects/ and Presentation. It only draws.
It never fills the background, never flips the display, never logs per frame and never
catches an error.
"""

import logging
from collections.abc import Callable

import pygame

from core.objects.base import GameObject, ObjectType, Phase
from ui.objects.entry_warning import draw_entry_warning, drop_entry_warning

log = logging.getLogger(__name__)

type ObjectView = Callable[[pygame.Surface, GameObject, tuple[float, float], float], None]
"""view(surface, obj, center, scale): draw the object's look centered at `center` (screen px),
scaled by `scale` (1.0 full size, 0.5 half size)."""

_VIEWS: dict[ObjectType, ObjectView] = {}
"""The registered views. Filled once at import by `register_view`."""


def register_view(object_type: ObjectType) -> Callable[[ObjectView], ObjectView]:
    """Return a decorator that registers a view for `object_type`.

    Raises ValueError when the type already has a view.
    """

    def decorate(view: ObjectView) -> ObjectView:
        if object_type in _VIEWS:
            raise ValueError(f"view for object type '{object_type.value}' is already registered")
        _VIEWS[object_type] = view
        return view

    return decorate


def registered_views() -> frozenset[ObjectType]:
    """Return every object type that has a view."""
    return frozenset(_VIEWS)


def render_object(surface: pygame.Surface, obj: GameObject) -> None:
    """Draw `obj` for its phase: the entry warning in WARNING, its view at (x, y) in ACTIVE.

    GONE draws nothing. Raises ValueError when no view is registered for the object's type.
    """
    view: ObjectView = _view_for(obj.object_type)
    if obj.phase is Phase.WARNING:
        draw_entry_warning(surface, obj, view)
    elif obj.phase is Phase.ACTIVE:
        drop_entry_warning(obj)
        view(surface, obj, (obj.x, obj.y), 1.0)


def _view_for(object_type: ObjectType) -> ObjectView:
    """Return the view registered for `object_type`, or raise ValueError."""
    if object_type not in _VIEWS:
        raise ValueError(f"no view registered for object type '{object_type.value}'")
    return _VIEWS[object_type]
