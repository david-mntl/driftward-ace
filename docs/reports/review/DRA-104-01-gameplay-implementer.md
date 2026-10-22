Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-104-01 (the UFO, the placement seed, the new `Birth` and `Placement` fields) against `docs/contracts/systems/drifters.md` v8. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-104-01-gameplay-implementer.md`.
3. **Checks:** Read the four delivered files, the task file, the contract's Interface (base, spawner, ufo, `__init__`), Rules (The base, Spawner, UFO, Tuning files, Logging), Impact and the DRA-104 Rationale, `drifters/07-ufo.md`, `game/CONTEXT.md` and `game/ruff.toml`. Traced by hand: the Level 1 and Level 8 birth values (1.974, 2.8031, 2.272, 0.142, 42 to 68), the first pick at n 21 (disc left edge 1.454, dome box left 10.95), `weave_brake_speed(12, 0.1)` = 1.5 (k 14) and `weave_stop_distance(2.272, 0.142)` = 19.312 (k 16). All match the task's expected lines. 10 checklist items; 3 findings: 0 must-fix, 1 should-fix, 2 notes.
4. **Assumptions:** I can't see the pre-DRA-104 spawner, so F1 doesn't say whether `_birth_speed` used to run before `start_position`. Attribute docstrings in place of the contract's line comments follow the existing house style (`base.py`, `spawner.py`). They are not a finding.
5. **Documentation differences:** None.
6. **Next:** Gameplay Implementer, Review fix mode, for F1. F2 and F3 ask for no change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-104-01-F1 | should-fix | game/core/drifters/spawner.py:131 | fixed |
| DRA-104-01-F2 | note | game/core/drifters/ufo.py:51 | no action |
| DRA-104-01-F3 | note | docs/reports/implementation/gameplay/DRA-104-01-gameplay-implementer.md:39 | no action |

### DRA-104-01-F1
The parked speed refusal now runs last. `_check_seed` runs at `spawner.py:131`, after `start_position` (`:130`). `_birth_speed`, which holds the step 4 refusal `<type> has no speed`, is called only inside the `Birth(...)` arguments at `:140`. The contract runs the steps in order: step 4 (speed, with the parked refusal), then step 7 (start), then step 8 (seed). A placement with two faults therefore gets the wrong message. One example is a coin row with both `speed` and `seed`: the contract gives `coin has no speed`, the code gives `coin has no seed`. A parked drifter with `speed` and a missing coordinate gets `placement needs x` first. No valid placement behaves differently, so this is a should-fix and not a contract break for the Director.
Rule: the spawner's step order. Source: `docs/contracts/systems/drifters.md`, Rules, Spawner, steps 4, 7 and 8 (lines 1834 to 1839).
Change: compute `speed = _birth_speed(cls, placement, type_tuning, speed_mult)` into a local right after `speed_mult` (line 128), before `start_size` and `start_position`, and pass that local to `Birth`.

### DRA-104-01-F2
`BRAKE_ROUND_DIGITS` (6) has the same value and purpose as `base.TIMER_ROUND_DIGITS`: round to 6 decimals before rounding up. Both are named, `Final` and disclosed, and the two rules may change apart. Change: none.

### DRA-104-01-F3
Assumptions say "Four module constants" but list three. Decisions call all three "draw constants", and `BRAKE_ROUND_DIGITS` is not one. The code matches the list. Only the count and the label are off. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F2
9. pass
10. F1, F3

## For QA
- Weave limits at Levels 1 and 8, both sides, many seeds: `|velocity_y|` never above `weave_speed_max`, never changing by more than `weave_turn` a tick, never passing `target_y`, and y always inside 188 to 440.
- A pick near a band edge (y within 40 px of `band_top` or `band_bottom`): it turns the other way. With room above 40 px but below the step, it stops exactly on the edge.
- Playtest `hazard_speed_scaling` off at Level 8: `weave_speed_max` 1.6 and `weave_turn` 0.1. A debug `speed` override changes only `velocity_x`, not the weave.
- A placement with an on-screen `x`: it weaves from its first ACTIVE tick. With `invert` it is dropped on n 345 (x −21.03).
- `placement_seed` and one seeded path give the same numbers in the browser build as on the desktop (Rationale, `random.Random` from a string).

## Re-check 2026-10-22
1. **Task:** Re-check the round 1 answers for DRA-104-01, against the implementation report's `## Review fix 2026-10-22` section. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-104-01-gameplay-implementer.md` (line 1, the F1 row, this section).
3. **Checks:** Read the `## Review fix` section and its answer, `game/core/drifters/spawner.py:78-154` (`_birth_speed` and `spawn_drifter`), and the contract's Spawner steps 4, 7 and 8 (`drifters.md` lines 1834 to 1839). 1 finding answered, 1 confirmed fixed; 0 new findings.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. 0 open findings.
7. **Status:** done.

- DRA-104-01-F1: fixed. `spawner.py:129` computes `speed` from `_birth_speed` right after `speed_mult`, before `start_size` (`:130`), `start_position` (`:131`) and `_check_seed` (`:132`). `Birth` takes the local at `:141`. The refusals now run in the contract's order: step 4, step 7, step 8.
