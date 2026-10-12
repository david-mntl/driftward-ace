Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-19-01 (Architect): `Final` constants, `slots=True`, documented Ship fields in core.
2. **Delivered:** `game/core/ship.py`, `game/core/scroll.py`, `game/core/world.py`.
3. **Checks:** Run from `game/`:
   `python -c "import core.ship as s, core.scroll as c, core.world as w; print(s.__annotations__['GRAVITY'], c.__annotations__['SCROLL_PER_TICK'], w.__annotations__['TOP_LINE_Y']); print(s.Ship.__slots__, s.Thrust.__slots__, c.Scroll.__slots__); print(s.step(s.spawn(), s.Thrust()))"`
   Output:
   `typing.Final[float] typing.Final[float] typing.Final[int]`
   `('x', 'y', 'vx', 'vy', 'wall', 'at_top_line') ('up', 'down', 'left', 'right') ('ticks', 'scrolled_ticks')`
   `Ship(x=320.0, y=240.16, vx=0.0, vy=0.16, wall=None, at_top_line=False)`
   `game/tests/check.sh lint`: PASS lint, PASS format. `check.sh core`: 18 passed, tests unchanged. Grep of core for sleep, threading, asyncio, pygame, random.random(: no hits. The step is pure and deterministic, so repeat runs match.
4. **Assumptions:** Field docstrings are short and follow the contract's comments. The "TEMPORARY" mention of the floor respawn in the ship module docstring is left, since only `at_top_line` was to lose it.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-19/tasks/DRA-19-01-gameplay-implementer.md`. Left alone: `game/app/settings.py`, module loggers, tests.
7. **Status:** done.

## Decisions
- `Final[int]` or `Final[float]` keeps each constant's current type. `Wall` alias unchanged.
- `slots=True` added next to `frozen=True` on `Thrust`, `Ship`, `Scroll`. No field has a mutable default, so slots is safe.
- World docstring now reads "Constants only." since it imports `Final`. No logger added.
- Source: scope report DRA-19 items 1 and 5.
