Status: reviewed
Created by: implementation-reviewer

1. **Task:** review DRA-111-01, the electric ball's core (`ELECTRIC_BALL`, `core/drifters/electric_ball.py`, the import line), against `systems/drifters/electric-ball/core.md` and the shared base parts the task names. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-111-01-gameplay-implementer.md` (this file).
3. **Checks:** read the implementation report, the task file, `impact.md`, `electric-ball/core.md` and `rationale.md`, the named parts of `shared/base-interface.md`, `shared/base.md` and `shared/spawner-registry-tuning.md`, `drifters/10-electric-ball.md`, `game/CONTEXT.md`, `game/ruff.toml`, and the three delivered files. Followed the acceptance output against the Diagram's timeline and the Cycle, Charge rays and Leaving rules by hand: the tick numbers in all four runs match. Nothing was run.
4. **Assumptions:** the test failure counts in **Checks** (6 core, 1 ui) match `impact.md`'s DRA-111-01 rows: the 5 in `test_wave_files.py` are the parametrized type-list case (`test_wave_files.py:437`, one per bad type value) plus the test at `test_wave_files.py:811`. Read, not run.
5. **Documentation differences:** pending Director approval. `docs/contracts/systems/drifters/electric-ball/core.md`, Interface, `game/core/drifters/__init__.py`, says the import line goes "after `ufo`". The code puts it between `coin` and `fireball` (`game/core/drifters/__init__.py:9`), because `game/ruff.toml:11` selects `I` (import order) and the file is sorted. Proposed change for the Architect: "Gains one import line, `electric_ball`, in sorted order (between `coin` and `fireball`)." The code needs no change. See DRA-111-01-F1.
6. **Next:** QA Engineer. Open findings: 0 must-fix, 0 should-fix, 2 notes (no action). The contract wording in item 5 waits on the Director.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-111-01-F1 | note | game/core/drifters/__init__.py:9 | no action |
| DRA-111-01-F2 | note | docs/reports/implementation/gameplay/DRA-111-01-gameplay-implementer.md:248 | no action |

### DRA-111-01-F1
The import sits in sorted order, not "after `ufo`" as `electric-ball/core.md`, Interface, says. Ruff's `I` rule (`game/ruff.toml:11`) forces it. The implementer disclosed it under Assumptions. The contract wording is raised in Documentation differences. Change: none.

### DRA-111-01-F2
The "wrong type extra" refusal passes `extra=None` (a missing type extra), not a wrong `DrifterTypeExtra` class. `born` uses `isinstance` (`game/core/drifters/electric_ball.py:149`), so both cases take the same path and the message is the same. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. F1, F2

## For QA
- A ball placed with y on screen: no hitbox on the charge states, the circle hits on the first fire state (`charge_ticks` after it turns ACTIVE), then a new charge after `fire_ticks`.
- A ball leaving the floor while firing: `current_hitbox()` is `()` and `is_off_screen()` is True on the same state (y − 8 >= 480 at the GDD guesses).
- Level 8 charge is 84 ticks; a tuning charge below `telegraph_min` is raised to 45; `fire_ticks` never scales.
- `charge_ray_count()` never passes `charge_rays` and is 0 off screen; `outline_level()` steps with it.
- `invert=True` plays the same as `invert=False`; a seed and a specialty are refused with their messages.
