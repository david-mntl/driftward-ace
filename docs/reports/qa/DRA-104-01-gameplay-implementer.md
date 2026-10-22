Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-104-01-gameplay-implementer (the UFO and the placement seed), started by /implement. Review status was `reviewed`, with its Re-check done.
2. **Delivered:** docs/reports/qa/DRA-104-01-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: lint, format and typecheck pass. `core` and `ui` fail only in the places the drifters contract's DRA-104 Impact table names (see Harness). Run with `test_collision.py` ignored: 744 pass, 3 fail, all three the unknown-type rows of `test_wave_files.py` (the list now ends `planet, ufo`; task DRA-104-06).
   - Acceptance check: I ran the task's command exactly (from `game/`, `PYTHONPATH=.`): the twelve lines match the task, line for line. Then I re-checked the lines by inline runs. Level 1 and Level 8 births give `-20.0 300.0 1.974 (12.0, 300.0) 60 96` and `660.0 -2.8031 2.272 0.142 42 68`. With the switches off at Level 8 the values are Level 1 (1.974, 1.6, 0.1, 60 to 96). `as_level=8` at Level 1 gives 2.8031, 2.272, 0.142, 42. A debug `speed` of 3.0 at Level 8 gives `velocity_x` 4.26 (3 × 1.42) and leaves `weave_speed_max` 2.272 and `weave_turn` 0.142. The weave starts on n 21 at x 21.454 with `velocity_y` -0.1. With `invert` it starts on n 21 at x 618.546 and is dropped on n 345 (x -21.03). `ufo_hitbox`, `drawn_parts` (40 × 10 and 21 × 21), `effect_on_touch` HIT and the graze zone (68 × 38 box and the r 23 circle) match the contract.
   - Seeds and refusals: `placement_seed('l1_a', 0)` is 3644637674 and `placement_seed('debug_spawns', 3)` is 2528993570, both in range and fixed. Seed 0 is accepted for a UFO. The band ends 188 and 440 are accepted; 187.99, 440.01 and 100.5 are refused with the contract's message. `specialty_enabled=False` is accepted; an unknown variant and an on-screen `x` behave. Same seed twice gives equal states after 500 ticks; one `update` called twice on one state gives equal results.
   - Edge cases: `weave_brake_speed` against an exact `Fraction` k on 20,000 values, including exact thresholds and thresholds ±1e-12: 0 mismatches; distance 0 gives 0.0. `check_ufo_weave` refuses in the contract's order, with the contract's messages and numbers. A step_min of 19.312 passes and 19.3 is refused. `check_ufo_variant` passes at dome radius 9 and 9.5 (drawn box 21 and 22, at most 40) and at 10 (23); refusal starts above 18.5, which the contract's `2 × (r + 1.5) <= disc_width` gives. No bug.
   - A pick within 40 px of a band edge, with x on screen so it weaves on its first ACTIVE tick, 11 start heights × 40 seeds: it always goes the other way when the room in the chosen way is under 40, and every `target_y` is inside the band. A placement with an on-screen `x` weaves on its first ACTIVE tick with `weave_ticks_left` 80, `velocity_y` -0.1.
   - Weave limits, Levels 1, 4 and 8, 60 seeds, 5 start heights, both sides, 700 ticks each: `|velocity_y|` never above `weave_speed_max`, never changing by more than `weave_turn` a tick, no tick passing its target. One failure kind: y outside the band by float dust (B1).
4. **Assumptions:** The band is judged with a hard `>= 188.0` and `<= 440.0`, with no tolerance, because the contract states the band as the UFO's hard limit (Rules, UFO, Band).
5. **Documentation differences:** None. One note for the Architect under B1: Pick step 5 and Ease do not say how the band edge is kept in float. The proposed fix works inside the contract as written.
6. **Next:** Gameplay Implementer, Fix mode, bug report docs/reports/qa/DRA-104-01-gameplay-implementer.md (B1). The Integration Engineer does not start until this report is `pass`.
7. **Status:** done.

## Bugs
- **B1** `game/core/drifters/ufo.py:422-425` (`_ease`), Gameplay Implementer. The UFO's center ends a tick a hair outside the band when a pick the other way stops it on the band edge. Reproduce, from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <file>`, the file being:
  ```
  from core.drifters.base import DrifterType, TickContext, Phase
  from core.drifters.spawner import Placement, spawn_drifter
  from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
  from core.drifters.ufo import UfoTypeExtra, ufo_hitbox
  from core.ship import spawn
  weave = UfoTypeExtra(weave_change_ticks_min=60, weave_change_ticks_max=96, weave_step_min=40.0, weave_step_max=120.0, weave_speed_max=1.6, weave_turn=0.1, band_top=188.0, band_bottom=440.0)
  ut = DrifterTypeTuning(variants={'standard': VariantTuning(width=40.0, height=10.0, hitbox=ufo_hitbox(40.0, 10.0, 9.0))}, default_variant='standard', speed_ratio=0.3, entry_warning_ticks=60, extra=weave)
  tuning = DrifterTuning(drifters={DrifterType.UFO: ut}, switches=PlaytestSwitches())
  context = TickContext(ship=spawn())
  d = spawn_drifter(Placement(DrifterType.UFO, y=200.0, seed=51), 1, tuning)
  while d.phase is Phase.WARNING:
      d = d.update(context)
  for n in range(1, 700):
      d = d.update(context).mark_entered()
      if not 188.0 <= d.y <= 440.0:
          print(n, repr(d.y), d.target_y, d.velocity_y)
          break
  ```
  Expected: nothing printed; y stays in 188.0 to 440.0 on every tick. Actual: `449 187.99999999999997 244.71429785948953 -0.055878028970253346`. The UFO is climbing to `target_y` 188.0, 0.0559 px away, and its count runs out on that tick. The pick goes the other way (new target 244.7), the ease brakes it by exactly 0.1, and the last climbing step, 0.0559, lands on 188.0 less float dust. It is 3e-14 px outside. In the property run, 424 ticks over 3,600 runs (Levels 1, 4 and 8, 60 seeds, 5 start heights, both sides) did this: 120 at Level 1, 92 at Level 4, 212 at Level 8. The largest miss was 7e-14. No `target_y` is ever outside the band. The speed and turn limits hold on every tick.
  Source: `docs/contracts/systems/drifters.md`, Rules, UFO, Band ("its center's y never leaves `band_top` to `band_bottom`"; "a pick the other way stops it before the last target"). A test that asserts `band_top <= y <= band_bottom` with no tolerance, as DRA-104-05 will, fails on these ticks.
  Proposed fix: at the end of `_ease` (`ufo.py` after line 425, the arrival snap), clamp the new y into the band: `y = min(max(y, self.band_top), self.band_bottom)`. The clamp only changes y by float dust: every exact result of the Ease rule is inside the band, so the contract's landing, speeds and turn limits are untouched, and it keeps the Band rule true in float. If the Architect prefers the contract to say it, one clause under Ease ("then y is clamped to the band, which only absorbs float dust") settles it.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (collection error `tests/core/test_collision.py`: `KeyError: 'hitbox'`, because `ufo.json` has `disc_width` and no `hitbox`; DRA-104 Impact table row for `test_collision.py`, task DRA-104-04) · ui FAIL (`test_drifter_registry.py::test_drifter_lists_match_everywhere`: no `ufo` view; Impact table row, task DRA-104-03)
Core with `--ignore=tests/core/test_collision.py`: 744 passed, 3 failed (`test_wave_files.py` unknown-type rows for `ufo`, `Meteorite` and `''`; Impact table row, task DRA-104-06).
QA: fail (core ui)

## Round 2 2026-10-22

1. **Task:** Re-test of B1 after the Gameplay Implementer's `## Fix 2026-10-22` section, started by /implement.
2. **Delivered:** this round, appended to docs/reports/qa/DRA-104-01-gameplay-implementer.md.
3. **Checks:**
   - B1 reproduce script, run as filed: prints nothing for the loop (seed 51, start y 200, 699 ticks). It was `449 187.99999999999997 ...` before.
   - Wider run, Level 1 values, 400 seeds x 5 start heights (188, 200, 314, 430, 440) x both sides x 900 ticks = 3,600,000 ticks: 0 ticks with y outside 188.0 to 440.0 (no tolerance), 0 `target_y` outside the band, 0 ticks with `|velocity_y|` above 1.6, 0 ticks with a speed change above 0.1 (1e-12 slack on that assert only).
   - Neighbor check, the clamp against the landing rule: 300 seeds x 3 start heights, 700 ticks: no tick lands on a band edge as `target_y` with a speed above `weave_turn`, so the clamp only absorbs dust and does not cut a landing short. Same seed twice: identical y, velocity and target on all 700 ticks.
   - Acceptance check (task command, from `game/`, `PYTHONPATH=.`): the twelve lines match the task, line for line.
   - `core` with `--ignore=tests/core/test_collision.py`: 744 pass, 3 fail, the same three unknown-type rows of `test_wave_files.py` (DRA-104-06). No new failure.
4. **Assumptions:** The Verdict is `blocked`, not `pass`, because `check.sh` cannot end `QA: pass` yet. Its three failures are all rows of the drifters contract's DRA-104 Impact table that later tasks fix (see Harness). No bug is open.
5. **Documentation differences:** None. The Architect note from round 1 (Pick step 5 and Ease do not say how the band edge is kept in float) still stands. The clamp works inside the contract as written.
6. **Next:** No fix needed from the Gameplay Implementer for this task. The Integration Engineer starts only once tasks DRA-104-03, -04 and -06 land and `check.sh` ends `QA: pass`. QA re-checks then, and flips this line to `pass` if nothing new appears. The Director decides if the pipeline may continue meanwhile.
7. **Status:** blocked: the harness failures wait on later tasks, not on this task's code.

## Bugs
- **B1** fixed. `game/core/drifters/ufo.py:426` now clamps y into the band after the arrival snap. Reproduce script prints nothing; 3,600,000 ticks stay inside 188.0 to 440.0.
- No new bugs.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (collection error `tests/core/test_collision.py`: `KeyError: 'hitbox'`, Impact table row, task DRA-104-04) · ui FAIL (`test_drifter_registry.py::test_drifter_lists_match_everywhere`: no `ufo` view, Impact table row, task DRA-104-03)
Core with `--ignore=tests/core/test_collision.py`: 744 passed, 3 failed (`test_wave_files.py` unknown-type rows for `ufo`, `Meteorite` and `''`; task DRA-104-06).
QA: fail (core ui)

## Round 3 2026-10-22

1. **Task:** Re-test of DRA-104-01 after tasks DRA-104-03, -04 and -06 landed, started by /implement. Sets the final verdict.
2. **Delivered:** this round, appended to docs/reports/qa/DRA-104-01-gameplay-implementer.md.
3. **Checks:**
   - `game/tests/check.sh`: all six steps pass. core: 3132 passed (includes `test_collision.py`, `test_ufo.py` and the `test_wave_files.py` unknown-type rows). ui: 46 passed (includes `test_drifter_registry.py`). Last line `QA: pass`.
   - B1 reproduce script, run again over seeds 51 to 250 (start y 200, 699 ticks each): 0 ticks with y outside 188.0 to 440.0, no tolerance.
   - The acceptance check and the wider property runs passed in round 2. No code in `game/core/drifters/ufo.py` changed since then, so I did not repeat them.
4. **Assumptions:** None new.
5. **Documentation differences:** None. The round 1 note to the Architect (Pick step 5 and Ease do not say how the band edge is kept in float) still stands. It does not block.
6. **Next:** The Integration Engineer, for DRA-104.
7. **Status:** done.

## Bugs
- **B1** fixed (confirmed in round 2 and again here).
- No open bugs.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
