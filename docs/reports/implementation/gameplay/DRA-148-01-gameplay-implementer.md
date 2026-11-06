Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the level-up rules record, banner state and shown level, and add the level-up rest and rise flag to the wave clock (`docs/contracts/DRA-148/tasks/DRA-148-01-gameplay-implementer.md`, from the Architect).
2. **Delivered:**
   - `game/core/level_up.py` (new): `LevelUpRules`, `NO_LEVEL_UP`, `LevelUpBanner`, `start_level_up`, `step_level_up`, `shown_level`.
   - `game/core/waves.py` (changed): `WaveRun.level_up_rules`, `WaveRun.level_rose` (last, with defaults), `start_waves(book, seed, level_up_rules=NO_LEVEL_UP)`, `next_run_waves` keeps the rules, `step_waves` clears the flag, `_end_wave` adds the rest and sets the flag.
3. **Checks:**
   - IS_CE true. `py_compile` clean on both files.
   - `game/tests/check.sh lint` PASS (ruff check and format), `typecheck` PASS (mypy strict), `core` PASS (3441 passed, no failure; `impact.md` expects none).
   - Smoke (rules rest 20, arrival 6, banner 15; book: Wave 0 with extra rest 5, Level 1 playlist = fixed wave `a` with extra rest 3, pool wave `p`; waves are 10 px, 1 px per tick). Command:
     `SDL_VIDEODRIVER=dummy python3 -I <scratchpad>/smoke.py` (inline script, not saved in the repo). Output, key lines:
     ```
     with rules
      t= 10 wave=w0 level=1 level_rose=False resting=True left=5     <- Wave 0 ends: no flag, no extra rest
      t= 14 wave=w0 level=1 level_rose=False resting=True left=1
      t= 25 wave=a  level=2 level_rose=True  resting=True left=23     <- rise: 0 gap + 3 extra + 20 level-up
      t= 26..: level_rose False on every other state (only t=25 and the next rise t=58 print it)
     no rules (NO_LEVEL_UP)
      t= 10 resting=True left=5                                       <- same as before
      t= 25 level=2 level_rose=True resting=True left=3               <- gap + extra only; flag still True
     level 8, wave past its playlist ends: level 8, level_rose False, rest 3 (extra only, no level-up rest)
     next_run_waves keeps the rules: True
     banner: shown_level 1 at age 0, 2 at age 6 (arrival); step_level_up drops it after 15 steps (banner_ticks)
     ```
   - Determinism: two runs, same inputs, byte-identical output (`cmp`).
   - Grep of `game/core/level_up.py` and `waves.py` for the banned names: the only hits are `\.wav` matching `.wave_id` / `.waves` (false positives). None real.
4. **Assumptions:** `NO_LEVEL_UP` has `arrival_ticks=1`, `banner_ticks=2`, the smallest values the record allows. The contract gives only `rest_ticks` 0 for it. While off, only `rest_ticks` is read.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-148/tasks/DRA-148-01-gameplay-implementer.md`. Left alone: `game/core/run.py` (task DRA-148-02), the `game/ui/level_up_*.py` files another agent had in the tree, `rest_gap_ticks`, the picker and the wave files.
7. **Status:** done.

## Decisions
- Flag: `step_waves` clears `level_rose` with `spawns_due` at the start of the call. `_end_wave` sets `level_rose = state.level_rose or rose`, so a rise stays visible if a later wave ends in the same call with no rise.
- Rest: `rest = rest_gap_ticks(level, extra) + rules.rest_ticks` only when 3.1 raised the level in that `_end_wave` call. For a skipped (empty) level it is added once, for the level reached. It is never scaled and `rest_gap_ticks` is unchanged. Source: level-up core.md, The level-up rest; waves.md step 3.2.
- Wave 0 and Level 8: neither raises the level in 3.1, so no flag and no level-up rest (shown in the smoke).
- `core/level_up.py` keeps the `log` line CONTEXT.md asks for but logs nothing, as the contract says. No validation inside: values are checked at load (tuning contract).
- All numbers come from the rules passed in; none in code except the `NO_LEVEL_UP` minimums above.
