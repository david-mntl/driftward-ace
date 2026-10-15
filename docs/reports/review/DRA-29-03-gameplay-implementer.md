Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the implementation report `docs/reports/implementation/gameplay/DRA-29-03-gameplay-implementer.md` (objects in `core/run.py`: `objects`, `next_uid`, `level`, `add_objects`, steps 3, 7 and 8, the lifecycle log lines). The `/implement` skill sent it.
2. **Delivered:** `docs/reports/review/DRA-29-03-gameplay-implementer.md` (this file).
3. **Checks:** I only read the code. I ran nothing.
   - I compared `game/core/run.py` line by line with `docs/contracts/systems/run.md` (Interface, Rules steps 1 to 9, game-over tick, `add_objects`, Logging, Impact, Rationale), the task's Do list and Acceptance check, the `base.py`, `spawner.py` and `collision.py` parts of `docs/contracts/systems/objects.md`, `05-lives-and-damage.md`, `game/CONTEXT.md` and `game/ruff.toml`. The contract agrees with `05-lives-and-damage.md`, rules 1, 2, 4 and 5 and Edge cases. Life-lost feedback is out of scope for DRA-29, as the contract says.
   - I traced the acceptance script by hand. Up from (320, 240) reaches the top line (y 184) in about 21 ticks. 29 updates leave the meteorite in WARNING with `ticks_in_phase` 29 and no hitbox. On tick 30, step 3 turns it ACTIVE at (320, 184) before the ship steps. Its r 14 circle overlaps the ship hitbox, so the ship is hit: lives 2, `invuln_ticks_left` 30, `hit_ship` True, ship unmoved. Then `may_hit_ship()` is False. The meteorite falls 4.935 px/tick and is dropped at ACTIVE tick 63 (y ≈ 494.9), which is inside the 200 ticks. `next_uid` 2. All three claimed lines, and the claimed `object gone ... y=494.91`, follow from the code.
   - The log order in `_step_playing` (`run.py:177-197`) matches Logging: active, wait end, ship, scroll, invulnerable end, fall or touch/life lost/game over, gone.
   - Bans: the code has no pygame, `ui` or `app` import, no randomness, frame time, sleep, thread, `await` or `print`.
4. **Assumptions:** I can't confirm the "35 passed", ruff and mypy results by reading. QA runs them. I took the implementer's word that the `core/ship.py` working-tree change is from before this task.
5. **Documentation differences:** None. No contract or locked-decision break found.
6. **Next:** Gameplay Implementer, Review fix mode, on this file. Open: 0 must-fix, 1 should-fix, 2 notes.
7. **Status:** done.

## Findings
1. **should-fix** `game/core/run.py:225`: the `_apply_fall` docstring cites "systems/run.md, Rules, step 5" for the fall. DRA-29 renumbered the steps, and the fall is now step 6. Step 5 is the scroll. The function was edited in this task, and `_end_run` in the same file (`run.py:244`) already uses the new numbers ("steps 6.3 and 7.5"). Rule: a docstring's source points to the right place. Sources: `docs/contracts/systems/run.md`, Rules ("Step numbers changed in DRA-29: ... 5 (fall) ... are now ... 6"); `game/CONTEXT.md`, Docstrings. Change: cite "step 6" in the `_apply_fall` docstring.
2. **note** `game/core/run.py:124`: the `object spawn` line works out its level (`placement.as_level`, else `run.level`) on its own, alongside the spawner's step 3. The two rules match today, and the contract's Logging asks for exactly this value. If the spawner's choice ever changes, the log could drift from the level that was actually used. Rule: the log shows the level used. Source: `docs/contracts/systems/run.md`, Logging, `object spawn`; `docs/contracts/systems/objects.md`, Rules, Spawner, step 3. Change: none.
3. **note** `game/core/run.py:278-281`: `_apply_hit` runs the overlap test on every object before it checks `protected`, so it does the work even on ticks that can't hit. Behavior is correct: a protected tick marks and logs nothing. Rule: none broken. Source: `docs/contracts/systems/run.md`, Rules, step 7.2. Change: none.

## Checklist
1. Interface matches exactly: **pass**. `Run` has `objects: tuple[GameObject, ...] = ()` and `next_uid: int = 1`, both documented (`run.py:72-76`). The `level` property returns `level_at(self.scroll.meters)` (`run.py:96-99`). The `add_objects(run, placements: Sequence[Placement], tuning: ObjectTuning) -> Run` signature matches (`run.py:110`). The existing names, defaults and constants are unchanged.
2. UI/core split: **pass**. Imports are stdlib, `core.collision`, `core.levels`, `core.objects.*`, `core.scroll` and `core.ship` only.
3. Fixed 60 Hz tick: **pass**. Invulnerability counts ticks. Objects advance one `update` per playing tick, and nothing advances on a game-over tick (`run.py:329-340`).
4. Randomness: **pass**. None. Objects are updated, tested and dropped in tuple order. A hit costs one life whatever the number of touching objects, so the order decides no outcome.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, audio or path.
6. Numbers trace: **pass**. No new number. `INVULN_TICKS` is the existing locked constant. Speed and level come from `spawn_object` and `core.levels`.
7. Pillars and locked decisions: **pass**. A hit keeps the ship's position, speed and `waiting` (`run.py:296-298`): no stun, no instant stop. Only ACTIVE objects can touch (`run.py:263`), so every hazard warns first. Spawn-on-ship is not checked at runtime, as the contract's objects.md Rationale says.
8. Smells: **finding** (3). Short functions, nesting depth 2 at most, no duplicated blocks (game over is now shared in `_end_run`), no dead or commented-out code, no module-level state, full type hints.
9. Decisions: **finding** (1). All eight match the code: the step order, fall and hit as exclusive (`run.py:195-197`), the shared `_end_run`, `may_hit_ship()` asked and `hit_ship` never read, the wait kept on a hit, drops last returning the same `Run` when none drop (`run.py:319-320`), the game-over tick untouched, and no new numbers. Only the `_apply_fall` docstring's step number lags the renumbering.
10. Report claims match the files: **finding** (2). The acceptance output, the log order and the "no other file" claim match the code. Assumption 2 (the logged level) is as the contract asks; see note 2.

## For QA
- Two meteorites touching the ship on one tick: one `life lost`, two `object touch` lines, and both get `hit_ship` True.
- A fall and an overlap on the same tick: only the fall's lines appear, and no meteorite gets `hit_ship`.
- A meteorite overlapping the ship while it is invulnerable: no `object touch`, `hit_ship` stays False, and it can hit on the first unprotected tick if it still overlaps.
- A hit during the respawn wait: lives drop, `waiting` stays True, the ship stays at (320, 240), and invulnerability resets to 30.
- A hit on the last life: game over with the ship where it was hit and the objects frozen. `add_objects` then returns the same run, and retry gives no objects and `next_uid` 1.

## Re-check 2026-10-15
1. **Task:** Re-check finding 1 against the implementer's `## Review fix 2026-10-15` section in `docs/reports/implementation/gameplay/DRA-29-03-gameplay-implementer.md`. The `/implement` skill sent it.
2. **Delivered:** `docs/reports/review/DRA-29-03-gameplay-implementer.md` (line 1 updated, this section appended).
3. **Checks:** I only read the code. I ran nothing. `game/core/run.py:225` now reads "systems/run.md, Rules, step 6". `docs/contracts/systems/run.md:170` confirms the DRA-23 fall step is now step 6. The fix changes the docstring only. `_apply_fall` code (`run.py:227-238`) is unchanged.
4. **Assumptions:** I can't confirm the claimed lint, typecheck, core and smoke results by reading. QA runs them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on `docs/reports/implementation/gameplay/DRA-29-03-gameplay-implementer.md`. Open: 0 must-fix, 0 should-fix, 2 notes (change none).
7. **Status:** done.

1. closed. `game/core/run.py:225` cites "systems/run.md, Rules, step 6", matching the renumbered contract.
