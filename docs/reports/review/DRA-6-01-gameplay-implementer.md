Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/gameplay/DRA-6-01-gameplay-implementer.md` (Gameplay Implementer, task `docs/contracts/DRA-6/tasks/DRA-6-01-gameplay-implementer.md`) against `docs/contracts/DRA-6/DRA-6-ship.md` and `docs/contracts/DRA-6/DRA-6-world.md`. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-6-01-gameplay-implementer.md` (this file). Reviewed: `game/core/world.py`, `game/core/ship.py`.
3. **Checks:** by reading only. Nothing run.
   - Interface: every name, type, default and signature in both contracts checked line by line against the code. All match.
   - Step order and arithmetic traced by hand against contract Rules 1 to 8. The reported numbers were recomputed by hand and agree: the acceptance output `184.0 0.0`, 60 ticks of free fall to y 478.2, the wall+floor tick to (16.0, 496.5) then a respawn, and the all-keys result vx 0.0, vy 0.16.
   - Read against `game/CONTEXT.md` (logging, errors, run modes, layout), `game/ruff.toml` (line length 100, ANN), and the gameplay-implementer standards.
   - 0 must-fix, 1 should-fix, 3 notes.
4. **Assumptions:**
   - I read "Implementers' standards" as the Python standards in `.claude/agents/gameplay-implementer.md`.
   - Where the standards ask for `pygame.Vector2`/`FRect` but the contract forbids pygame in core, I treat the contract as the rule.
5. **Documentation differences:** None. The wording gap in the contract's Logging rules (finding 2) is internal to the contract. It does not conflict with the GDD or `CLAUDE.md`. It goes to the Architect as a note, not as a block.
6. **Next:**
   - QA Engineer: run the checks for `docs/reports/implementation/gameplay/DRA-6-01-gameplay-implementer.md` (task DRA-6-03). Must-fix count: 0.
   - Architect (through the Director): optional rewording of DRA-6-ship.md, Rules, Logging, per finding 2.
   - Integration Engineer: `game/app/settings.py:9` still holds `SCREEN_SIZE` (finding 4). The DRA-5 contract's Impact table owns that change.
7. **Status:** done.

## Findings
1. **should-fix** `game/core/ship.py:63-72`: the `Ship` fields carry no units or sign convention, and `at_top_line` is not marked TEMPORARY. The contract's Interface gives each field a comment: `vx` px/tick, + is right; `vy` px/tick, + is down (falling); `wall` is the wall clamped against this tick; `at_top_line` is TEMPORARY, DRA-6. The class docstring only says "Screen px, y down. x and y are the ship's center." Rule: docstrings state units, and the temporary DRA-6 stand-ins are marked as such. Source: gameplay-implementer Python standards ("Docstrings say what a function guarantees, its units"); task DRA-6-01, Do (mark the temporary parts); DRA-6-ship.md, Interface. Change: carry the contract's per-field comments into the class docstring or onto the fields, and mark `at_top_line` TEMPORARY (DRA-6, replaced by the camera).
2. **note** `game/core/ship.py:95-99`: contact logging reads `moved`, the ship after the clamps and before the respawn reset, not the returned ship. The contract's Logging rules say "when the returned ship has `wall` set" (DRA-6-ship.md, Rules, Logging, line 135). They also say that on a wall hit plus a respawn in one tick, the wall line comes first and the respawn line follows (line 139). After a respawn the returned ship has `wall=None`, so both sentences hold only for the pre-reset ship. The implementer flagged this under Assumptions, and the code satisfies the ordering rule. Source: DRA-6-ship.md, Rules, Logging. Change: none in code. Suggest the Architect replace "the returned ship" with "the ship after the clamps, before any respawn" in the wall and top-line lines.
3. **note** `game/core/ship.py:18-48, 53, 63`: the constants are not `Final`, and the dataclasses are `frozen=True` without `slots=True`. The standards ask for `Final` constants and `slots=True` where it fits. Decisions explains the `Final` choice: it matches the Interface text and `app/settings.py`. It does not mention `slots`. Both are allowed under the contract. Adding `slots=True` would not change the Interface. Source: gameplay-implementer Python standards. Change: optional. Consider `slots=True` on `Thrust` and `Ship` in a later task that touches the file.
4. **note** `game/app/settings.py:9`: `SCREEN_SIZE = (640, 480)` is still in place, so the screen size now lives in two files: here and in `core/world.py:9,12`. This task correctly left it alone, since `game/app/` is not its lane. Source: DRA-6-world.md, Rationale; DRA-5-app.md, Impact (`game/app/settings.py`: remove `SCREEN_SIZE`). Change: the Integration Engineer removes it under the DRA-5 Impact list. Until then, the two values must not drift.

## Checklist
1. Interface matches exactly: **pass**. World: `SCREEN_W`, `SCREEN_H`, `TOP_LINE_RATIO`, `TOP_LINE_Y` with the contract's types and values. Ship: ten constants, `Wall`, `Thrust`, `Ship` (fields, order, defaults, `frozen=True`), `spawn() -> Ship`, `step(ship, thrust) -> Ship`. Nothing renamed, added or dropped. Private helpers are not part of the Interface.
2. UI/core split: **pass**. Core imports only stdlib and `core.world` (`ship.py:10-14`). `world.py` has no imports. No `ui` or `app` import.
3. Fixed 60 Hz tick: **pass**. No frame time, dt or clock anywhere. One call is one tick.
4. Randomness only from a passed-in `random.Random`: **pass** (n/a in substance). No randomness. Nothing iterates over sets or dicts.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, audio or file path.
6. Every number traces to the GDD: **pass**. Each constant matches 04-ship.md, 03-world-and-camera.md or 05-lives-and-damage.md Values, and each docstring names its source. `TOP_LINE_Y` is computed from the ratio (`world.py:21`). The `0.0` speeds on clamp and spawn are contract rules ("vx = 0", "vy = 0", "at rest"), not tuning values. No fallback defaults.
7. Pillars and locked decisions: **pass**. No weapons. Input only changes acceleration (`ship.py:109-116`). Walls clamp with vx 0 and no bounce (`ship.py:128-133`). The top-line vy 0 and the floor respawn are the Director-approved temporary stand-ins (scope report DRA-6, Limits). Hazard rules: n/a.
8. Smells: **finding** (should-fix 1 on missing field units; note 3). No god class, no long parameter lists, no nesting deeper than one `if`, no duplicated blocks, no magic numbers, no dead or commented-out code. The only module-level state is `log` plus the constants. Every function is type-hinted.
9. Decisions present and matching the code: **pass**. All ten bullets checked. Update order, the four helpers plus the log helper, literal per-key thrust, plain floats, plain annotations, the wall clamp, the strict `<` top-line trigger, the `>=` floor test returning `spawn()`, and `round(...)` for `TOP_LINE_Y` all match the code.
10. Report claims match the files: **pass**. Hand traces of the acceptance check and the smoke figures agree with the code. The grep claim holds: the only `random` text is the docstring at `ship.py:5`. A `.gitkeep` was kept, as stated. Nothing was run.

## For QA
- Wall and floor in the same tick (e.g. `Ship(10.0, 491.0, -3.0, 5.5)`): the wall line, then the respawn line, then a ship at (320, 240) at rest with `wall=None`.
- Hold Left at the wall for many ticks: exactly one `wall hit` line. Release, then press again: a second line, because a ship resting at x 16 with vx 0 reads `wall=None`.
- Boundary checks: top edge exactly 480 (y 496.0) respawns, just above it does not. A ship resting exactly on the top line (y 184.0, vy 0) with no Up is not clamped and starts to fall.
- `step` never mutates its input (frozen), and the same ship and thrust always give the same result.
- Opposite keys: Left+Right gives vx unchanged apart from drag. Up+Down gives vy + 0.16 only.
