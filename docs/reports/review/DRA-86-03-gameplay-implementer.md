Status: reviewed
Created by: implementation-reviewer

1. **Task:** review the island block in the ship (`Ground`, `NO_GROUND`, `Ship.against_island`, `spawn_clear`, `block_ship`, the `ground` argument of `step`, the `island contact` log line), implementation report `docs/reports/implementation/gameplay/DRA-86-03-gameplay-implementer.md`, from the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-86-03-gameplay-implementer.md` (this file). Reviewed: `game/core/ship.py`.
3. **Checks:** by reading only. Compared `game/core/ship.py` with `docs/contracts/systems/ship.md` (Interface, Rules: step 6 Then islands, Islands 1 to 5, Respawn spot, Logging, Impact DRA-86, Rationale DRA-86), `docs/contracts/systems/drifters.md` (Push-out interface, DRA-86 Impact table), `docs/design/gdd/04-ship.md` rule 2 step 6, `docs/design/gdd/drifters/05-floating-islands.md` rules 4 to 6 and Edge cases, `game/CONTEXT.md` and `game/ruff.toml`. Hand-traced acceptance lines 1, 2, 4, 6 and 7 against the code: each matches the task's expected output. The failures the report names (`test_collision.py`, `test_wave_files.py`, `tests/ui/test_drifter_registry.py`) are the ones the drifters.md DRA-86 Impact table expects. Ran nothing.
4. **Assumptions:** read "Values are the new position after the clamp or the push" (ship.md, Logging) as each line logging the position after its own clamp or push. See F1.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no change asked.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-86-03-F1 | note | game/core/ship.py:202 | no action |

### DRA-86-03-F1
`wall hit` now logs the position after the wall clamp, before the island push and the top line. Before DRA-86 it logged the position at the end of the step, so its `y` differs on a tick with a wall hit and a top-line stop (or an island push) together. ship.md, Logging puts `island contact` (logged by `block_ship`) between `wall hit` and `top line stop`, so this order is the only one the contract allows without a second, unlogged block helper. It is disclosed in Decisions and no existing test reads the value. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. F1
10. pass

## For QA
- Wall hit and top-line stop on the same tick: one `wall hit` line with the post-wall-clamp `y`, then one `top line stop` line (F1).
- Ship clipping an island corner next to a side wall: the push through the wall is refused and the next shortest way is used; no ship ends up inside the island.
- Upward push that would cross the top line: refused, the ship goes down instead.
- `spawn_clear` with the up and down exits equal: the spot above wins; with the spot above past the top line: the spot below.
- Ride an island, lift off, land again: `island contact` logs once per landing, never per tick.
