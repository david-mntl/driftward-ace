Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-47/tasks/DRA-47-02-gameplay-implementer.md`, from the Architect: the shared base pieces the chain lightning needs (telegraph floor, type extra, warning hooks, timer scaling) and the warning settle in `add_drifters`.
2. **Delivered:**
   - `game/core/drifters/base.py`: `DEFAULT_TELEGRAPH_MIN_TICKS`, `DrifterTypeExtra`, `Birth.type_extra` and `Birth.telegraph_min_ticks`, `Drifter.warning_copy`, `Drifter.settle_warning`, `scale_timer`, `scale_telegraph`.
   - `game/core/drifters/tuning.py`: `DrifterTypeTuning.extra`, `HazardRules.telegraph_min_ticks`.
   - `game/core/drifters/spawner.py`: `Birth` gets `type_extra` and `telegraph_min_ticks` (step 8).
   - `game/core/run.py`: `add_drifters` settles each new drifter's warning after giving it its uid.
3. **Checks:**
   - IS_CE true (pygame-ce 2.5.8). `py_compile` clean on the four files.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `check.sh core -k "not collision"`: 78 passed, no test changed.
   - `check.sh typecheck` fails, but not in my files: `ui/shapes.py:30`, `app/tuning.py:250-251` and `tests/core/test_collision.py` report the new `Line` shape in the `Hitbox` union (the uncommitted `core/collision.py` change from DRA-47-01). Nothing in `core/drifters/` or `core/run.py` is flagged.
   - Acceptance smoke, run twice, identical output. Command (from `game/`; I ran it with `PYTHONPATH=.` because the script sat outside `game/`): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<the task's command>"`. Output:
     ```
     [120, 113, 107, 102, 98, 93, 89, 84] 45 84
     45 None True True 1
     ```
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: only hits are the ban list strings in `core/ruff.toml`. No code hit.
4. **Assumptions:** None. The new `Birth` fields have no defaults, as the contract lists them; `spawner.py` is the only caller in `game/`.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-47/tasks/DRA-47-02-gameplay-implementer.md`. The typecheck failures above come from `Line` in `collision.py` reaching `ui/shapes.py` and `app/tuning.py`; the Director or Architect should confirm which later DRA-47 task fixes them. I left those files alone. `DrifterType.CHAIN_LIGHTNING` is still missing (task DRA-47-03).
7. **Status:** done.

## Decisions
- `scale_timer` is `math.ceil(round(ticks * timer_mult, 6))` and `scale_telegraph` is `max(scale_timer(...), telegraph_min_ticks)`, as the contract's Timers rule says. The 6 is a named constant, `TIMER_ROUND_DIGITS`.
- `DEFAULT_TELEGRAPH_MIN_TICKS` 45: 07-drifters.md, telegraph_min (locked). It is the default of `HazardRules.telegraph_min_ticks`; the tuning file may override it.
- `add_drifters` order: spawn, `replace(uid=...)`, then `settle_warning(TickContext(ship=run.ship))`, per the run contract. Every drifter in a call settles against the same `run.ship`. The spawn log line still reads the settled drifter, which has the same fields.
- `warning_copy` and `settle_warning` are concrete no-ops on the base (return `self`), so the meteorite, the satellite and the registry test stubs need no change.
