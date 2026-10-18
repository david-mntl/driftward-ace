Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the Gameplay Implementer's DRA-62-02 work (`scroll_step_px`, the scroll step in step 3, popups in step 3a, collect in step 5a) against `docs/contracts/DRA-62/tasks/DRA-62-02-gameplay-implementer.md`, `docs/contracts/systems/run.md` and `scroll.md`. Asked by the `/implement` skill.

2. **Delivered:** this report, `docs/reports/review/DRA-62-02-gameplay-implementer.md`. Files read: `game/core/run.py`, `game/core/scroll.py`, and `game/core/drifters/base.py` (for `TickContext`, `collect_points`, `collect_popup`, `effect_on_touch`).

3. **Checks:** Read only, nothing run. Compared `scroll_step_px`, `Run.popups`, the `start_run` docstring and steps 3, 3a, 5a, 6, 7, 8 and 9 of `_step_playing` with the contract's Interface and Rules. Traced the five acceptance lines by hand: `scroll_step_px` gives 0.0 at ticks 0 and 1.1 at ticks 30; a waiting ship skips `_apply_collect`; an invulnerable ship collects on tick 1 (the coin is GONE, then dropped in step 9, popup at age 0); the popup is still there after 59 more ticks and gone on the 60th. Checked log order against the contract's order line. Checked the 100-column limit in `game/ruff.toml` by eye. Searched the two files for wall-clock time, randomness, `pygame`, `ui` and `app` imports: none.

4. **Assumptions:** The implementer's `check.sh` and acceptance output are taken from its report. I did not run them. The one failing `test_collision.py` coin case is the one the contract's DRA-62 Impact table expects until DRA-62-05.

5. **Documentation differences:** None.

6. **Next:** QA Engineer. Report path: `docs/reports/review/DRA-62-02-gameplay-implementer.md`.

7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-62-02-F1 | note | game/core/run.py:279 | no action |

### DRA-62-02-F1
The `drifter touch id=%d type=%s effect=%s` log call in `_apply_collect` (run.py:279-284) repeats the one in `_apply_hit` (run.py:368-373). Two copies of a five-line call is small, and the contract names both sites. Rule: smells, duplicated blocks (implementers' standards). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. note only: F1
9. pass
10. pass

## For QA
- Coin touched while the ship stands in the respawn wait: it must stay and pay nothing. On the tick an arrow press ends the wait, it must pay.
- Coin and a hazard touched on one tick: the coin pays, then the hit costs a life. On the last life the final score includes the coin.
- Coin touched on a fall tick (protected and not protected): it pays, then the fall counts. No hit is tested.
- Popup lifetime: shown on exactly 60 states, rises 0.5 px a tick, never moves with the scroll. It freezes at game over and a retry starts with none.
- Log order on a collect tick: `invulnerable end` (if due), `drifter touch ... effect=collect`, the fall or hit lines, then `drifter gone`. No `drifter active` for a coin.
