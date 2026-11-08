"""Frame loop constants. Constants only, no imports.

From DRA-6 the screen size lives in core/world.py (SCREEN_W, SCREEN_H).
Source: docs/contracts/systems/app.md, Interface, game/app/settings.py, and Impact.
"""

TICK_RATE: int = 60
"""Ticks per second. Source: 15-tech-constraints.md, tick_rate."""

MAX_TICKS_PER_FRAME: int = 2
"""Most ticks one frame may run; owed time beyond that is dropped.

Each catch-up tick makes its frame slower, so a high cap turns one late frame into a chain of
them. Source: 15-tech-constraints.md, max_ticks_per_frame (guess); 91-decision-log.md, rows 21
and 149.
"""

TICK_SNAP_SECONDS: float = 0.002
"""A frame this close to a whole tick, s, still runs that tick; the next frame pays it back.

Browser frames come a little early or late. Without the snap a frame 0.1 ms short of a tick runs
none and the next runs two: the picture holds, then jumps. Game speed stays 60 ticks/s.
Source: 15-tech-constraints.md, tick_snap (guess); 91-decision-log.md, row 149.
"""
