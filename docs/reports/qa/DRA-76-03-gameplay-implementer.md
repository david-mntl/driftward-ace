Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-76-03-gameplay-implementer (`game/core/waves.py`: wave book, wave state, wave clock, playlist runner, random picker), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-76-03-gameplay-implementer.md. No test files saved (Verify mode).
3. **Checks:**
   - `game/tests/check.sh`: all steps PASS, last line `QA: pass`.
   - Acceptance check, run from `game/` with `SDL_VIDEODRIVER=dummy PYTHONPATH=.`, matches the task on all three lines:
     ```
     w0/1/0 w0/1/0 w0/1/1 a/1/0 a/1/0 a/1/0 a/1/1 rest/1/0 rest/1/0 p/1/0 p/1/0 p/1/0 p/1/1 q/2/0 q/2/0
     q p ('a', None) ('p', 'q')
     w0 1 True
     ```
     Same script twice: identical output (md5 equal).
   - Edge cases run inline, all correct:
     - Rest gap: extra rest 2 shows `rest` on exactly 2 states (rest_ticks_left 2, 1), next wave starts at the distance of the tick the rest ends.
     - No rest, wave ends partway through a tick: next wave starts at old start + length (200 after a wave of 100 stepped to 230). A trigger of 0 in the next wave is due the same tick; `spawns_due` held Wave 0's due placement and the next wave's two trigger-0 placements, in order.
     - One big jump (0 to 1000 px) plays through every wave on one call; spawns in order; level 8 reached; a placement past the wave's length (at_px 150 in a 100 px wave) never due.
     - A placement exactly at the end is due on the ending tick; 99.99 px and 99.9999994 px (rounds to 99.999999) do not end the wave.
     - Level rise: level is already 2 in the state of the tick the Level 1 playlist's last wave ends. Empty playlists skipped with one `level up` line (level 1 to 3 logged once). At Level 8 the level stays 8 for 400 waves, random picks continue.
     - Level rise happens before the rest gap: `level up` precedes `rest start`, log order `wave end`, `level up`, `rest start` or `wave start`.
     - Picker: no consecutive repeat in 400 level-8 picks with 3 pool waves, and none across 200 seeds over Level 1 to 8 changes and after Wave 0 (a pool Wave 0 never repeats). With one pool wave it repeats. Same seed gives same sequence, different seed a different one.
     - `next_run_waves`: `run_seed` equals `Random(5).getrandbits(64)`, Wave 0, Level 1, nothing due. Input state not mutated by `step_waves`.
     - Float boundaries: with the scroll's 1.1 px/tick sum, triggers at 1.1 x k for k 1 to 399 come due on tick k exactly (0 off-by-one).
     - Placeholder timeline from the contract played with `core.scroll`: waves start on tick 1230 (l1_a), 2430 (l1_b), 3630 (l1_a, Level 2), 4721, 5812, 6812. Matches the contract table. Run twice: identical.
     - `rest_gap_ticks` 0 at Levels 1 to 8 with extra 0, equal to the extra with extra 3. Levels 0 and 9 raise `ValueError` from `rest_gap_ticks`, `level_slots`.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer (no bug open). Tests for this module are task DRA-76-07-qa-engineer.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
