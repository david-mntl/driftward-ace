"""Frame loop constants. Constants only, no imports.

From DRA-6 the screen size lives in core/world.py (SCREEN_W, SCREEN_H).
Source: docs/contracts/systems/app.md, Interface, game/app/settings.py, and Impact.
"""

TICK_RATE: int = 60
"""Ticks per second. Source: 15-tech-constraints.md, tick_rate."""

MAX_TICKS_PER_FRAME: int = 5
"""Most ticks one frame may run; owed time beyond that is dropped.

Source: 15-tech-constraints.md, max_ticks_per_frame (guess); 91-decision-log.md, row 21.
"""
