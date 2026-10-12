Feature: DRA-19
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/DRA-6/DRA-6-ship.md#interface
Status: done
Linear: DRA-20

## Do
Bring the three core modules in line with the Python standards and document the ship's fields. No behavior, value, name, signature or log line changes.
- `game/core/ship.py`, per `docs/contracts/DRA-6/DRA-6-ship.md`, Interface:
  - Document each `Ship` field with the contract's comment for it: `x` center x, `y` center y (screen px, y down); `vx` px/tick, + is right; `vy` px/tick, + is down (falling); `wall` the wall the ship was clamped against this tick; `at_top_line` the top line (ceiling) clamped the ship this tick. Use a docstring under each field, the style `core/scroll.py` already uses. Don't mark `at_top_line` TEMPORARY: the top line has been a permanent ceiling since DRA-13. Source: scope report DRA-19, item 1; review DRA-6-01-gameplay-implementer, finding 1.
  - Mark the ten constants `Final[int]` or `Final[float]`, keeping each one's current type. `Wall` is a type alias and stays as it is.
  - `slots=True` on `Thrust` and `Ship`, next to `frozen=True`.
- `game/core/scroll.py`, per `docs/contracts/DRA-13/DRA-13-scroll.md`, Interface: the six constants `Final[...]` with their current types, including the computed `SCROLL_PER_TICK`. `slots=True` on `Scroll`.
- `game/core/world.py`, per `docs/contracts/DRA-6/DRA-6-world.md`, Interface and Rules: the four constants `Final[...]` with their current types, including the computed `TOP_LINE_Y`. Add `from typing import Final`, the module's only import. Reword the module docstring's "Constants only, no imports." to match. Still no logger.
- `Final` comes from `typing`. Mark only module-level constants, never dataclass fields or `log`.
- Source for `Final` and `slots`: scope report DRA-19, item 5; reviews DRA-6-01-gameplay-implementer, finding 3, and DRA-13-01-gameplay-implementer, finding 1.
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint` and `game/tests/check.sh core` before handoff. The existing tests must pass unchanged.

## Acceptance check
From `game/`, run:
`python -c "import core.ship as s, core.scroll as c, core.world as w; print(s.__annotations__['GRAVITY'], c.__annotations__['SCROLL_PER_TICK'], w.__annotations__['TOP_LINE_Y']); print(s.Ship.__slots__, s.Thrust.__slots__, c.Scroll.__slots__); print(s.step(s.spawn(), s.Thrust()))"`
It prints `typing.Final[float] typing.Final[float] typing.Final[int]`, then `('x', 'y', 'vx', 'vy', 'wall', 'at_top_line') ('up', 'down', 'left', 'right') ('ticks', 'scrolled_ticks')`, then one ship one tick after spawn with `x=320.0` and `vy=0.16`, the same as before the change. Put the command and output in the implementation report.

## Out of scope
- The contract's Logging wording (scope item 2). That is a contract-only fix, already done. No code change for it.
- Any change to physics, scroll steps, values, log lines or signatures.
- `game/app/settings.py` constants. Not core, and not in DRA-19.
- Removing module loggers, any other refactor.
- Any change to `game/ui/`, `game/app/`, `game/main.py`.
- Tests.
