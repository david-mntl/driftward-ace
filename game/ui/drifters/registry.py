"""The view registry and `render_drifter`: which look draws which drifter, and in which phase.

Source: docs/contracts/systems/drifters.md, game/ui/drifters/ and Presentation. It only draws.
It never fills the background, never flips the display, never logs per frame and never
catches an error.
"""

import logging
from collections.abc import Callable

import pygame

from core.drifters.base import Drifter, DrifterType, Phase
from ui.drifters.entry_warning import draw_entry_warning, drop_entry_warning

log = logging.getLogger(__name__)

type DrifterView = Callable[[pygame.Surface, Drifter, tuple[float, float], float], None]
"""view(surface, drifter, center, scale): draw the drifter's look centered at `center` (screen px),
scaled by `scale` (1.0 full size, 0.5 half size)."""

_VIEWS: dict[DrifterType, DrifterView] = {}
"""The registered views. Filled once at import by `register_view`."""


def register_view(drifter_type: DrifterType) -> Callable[[DrifterView], DrifterView]:
    """Return a decorator that registers a view for `drifter_type`.

    Raises ValueError when the type already has a view.
    """

    def decorate(view: DrifterView) -> DrifterView:
        if drifter_type in _VIEWS:
            raise ValueError(f"view for drifter type '{drifter_type.value}' is already registered")
        _VIEWS[drifter_type] = view
        return view

    return decorate


def registered_views() -> frozenset[DrifterType]:
    """Return every drifter type that has a view."""
    return frozenset(_VIEWS)


def render_drifter(surface: pygame.Surface, drifter: Drifter) -> None:
    """Draw `drifter` for its phase: the entry warning in WARNING, its view at (x, y) in ACTIVE.

    GONE draws nothing. Raises ValueError when no view is registered for the drifter's type.
    """
    view: DrifterView = _view_for(drifter.drifter_type)
    if drifter.phase is Phase.WARNING:
        draw_entry_warning(surface, drifter, view)
    elif drifter.phase is Phase.ACTIVE:
        drop_entry_warning(drifter)
        view(surface, drifter, (drifter.x, drifter.y), 1.0)


def _view_for(drifter_type: DrifterType) -> DrifterView:
    """Return the view registered for `drifter_type`, or raise ValueError."""
    if drifter_type not in _VIEWS:
        raise ValueError(f"no view registered for drifter type '{drifter_type.value}'")
    return _VIEWS[drifter_type]
