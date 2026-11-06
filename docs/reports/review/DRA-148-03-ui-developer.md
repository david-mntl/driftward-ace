Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-148-03 (the level-up look records and pure motion functions), asked by the `/implement` skill. Implementation report: `docs/reports/implementation/ui/DRA-148-03-ui-developer.md`.
2. **Delivered:** this review file. Code read: `game/ui/level_up_rules.py`, `game/ui/level_up_motion.py`. Contract read: `docs/contracts/systems/level-up/view.md`, `docs/contracts/schemas/level-up.schema.json`, the task file.
3. **Checks:** by reading only, nothing run. Every field name, order and type of the 12 records matches the schema; every function signature matches the Interface block. I traced each function at its end points (the exact-0, exact-1, exact-overshoot, exact-start and exact-end promises hold in the code). I read the scratchpad script the report names: its asserts match the report's claims and the code can pass them.
4. **Assumptions:** the implementer's Decisions (easing choices, `_mix` form, early returns, no division guards) are inside the task's "Not in the contract" room and match the code. I read the loader's order checks as given by the schema and `tuning.md`; that loader is another task.
5. **Documentation differences:** None.
6. **Next:** the Implementation Reviewer's one finding is a should-fix about where the acceptance script lives. The implementer answers it in Review fix mode. Then the task goes to QA.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-148-03-F1 | should-fix | docs/reports/implementation/ui/DRA-148-03-ui-developer.md:6 | fixed |

### DRA-148-03-F1
The acceptance script is not in the implementation report. The report names a file in a session scratchpad (`/tmp/claude-1000/.../scratchpad/motion_check.py`) and summarises its asserts. The task's Acceptance check says "A script (in the implementation report)". The scratchpad is session-local and goes away, so QA and the Director cannot re-run the check or see the starting values behind the printed numbers (the report lists the values only in prose).
Rule: task DRA-148-03, Acceptance check; "leave a result the Director can check", CLAUDE.md, Rules for every agent.
Change: put the script's text in the implementation report in a `## Review fix` section (a fenced code block, with its path to run it from), or save it where the task allows. The code needs no change.

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
10. The report's claims match the files; the script is not carried in the report: F1

## For QA
- `bump_offset` with `bump.pixels` 0: 0 on every age.
- `bump_offset` with a `peak_share` that does not land on a whole tick: check the peak still reaches `bump.pixels` or one px less after `round()`.
- `fall_offset` at the start tick, at `fall_end` and one tick after: -distance, 0, 0. It crosses 0 on its way up to the overshoot; a view that clips on sign must not read that as the landing.
- `band_shares` over `close_start..close_end` with the live tuning: glass reaches 0 before the lines.
- `fly_position` at share 0 and 1: exactly the start and the HUD slot center, so no one-pixel jump on the arrival tick.

## Re-check 2026-11-06
1. **Task:** Re-check the answer to DRA-148-03-F1 (round 2, the last), asked by the `/implement` skill.
2. **Delivered:** this section, the findings table and line 1 of this file.
3. **Checks:** by reading only, nothing run. I read the implementation report's `## Review fix 2026-11-06` section: it names this review and carries the full acceptance script in a fenced block (`docs/reports/implementation/ui/DRA-148-03-ui-developer.md:47-111`) with its run instructions and starting values. The script puts `/workspace/game` on `sys.path` itself, so it runs from any folder. The report states no code changed.
4. **Assumptions:** the script text equals the scratchpad file the first section named; I took the implementer's word on that and did not diff it.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on this report. No must-fix or should-fix is open.
7. **Status:** done.

- DRA-148-03-F1: fixed. The script is now in the implementation report (lines 47-111), with the run command and the starting values in its first lines.
