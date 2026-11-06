Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-148-06-ui-developer (`LevelUpView.draw_flight` and the flight's pre-rendered sizes), started by /implement. Review is `reviewed` (F1 fixed, F2 and F3 no action). Per the main session's note (away log D2, tick 124), the white flash on the pop's first frame instead of the tier color is accepted and not a bug. Checked only size and position at the hand-off.
2. **Delivered:** `docs/reports/qa/DRA-148-06-ui-developer.md`. Inline scripts only, kept outside the repo in the scratchpad (`qa06c.py`, `qa06d.py`, `qa06e.py`, `qa06f.py`). Nothing saved in `game/tests/`.
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass` (786 ui and core tests).
   - Acceptance check, nothing outside the flight: window pixel-equal to the HUD alone for ages 0 to 99 and 124 to 150 at level 3, and for levels 2 to 8 at ages 0 to 99 and 124 to 153. Also equal for banner None, age -5 and age 1,000,000. Ages 100 to 123 draw at every level 2 to 8.
   - Acceptance check, start: age 100 ink center (336, 250), at the resting place (336.5, 250 in the implementer's run).
   - Acceptance check, flight: x grows every tick, the ink box shrinks 47x68 to 23x33 and never grows, y at age 112 is 301 against the straight line's 320.9 (bows up). The last age 123 has the ink center on the slot center (718, 383), within 1 px. This holds at levels 2 to 8 (level 4: 719, 383, and level 8: 719, 383, both as the slot).
   - Acceptance check, size: the last flight image equals the HUD's pop frame 0 in size at levels 2 to 8 (23x51, 26x51, 25x51, 28x51 for the slot sizes 16/18/17/19 x 35 times 1.45). The share is exactly 1.0 and the position equals the slot center at age 123 for every level.
   - Cost: 500 `draw_flight` calls across ages 100 to 123 and levels 2 to 8 built 0 surfaces, rendered 0 text and called no scale or rotate. `__init__` made 185 surfaces, 12 renders and 84 scales.
   - Same inputs twice, ages 100 to 123: byte-identical windows. A paused flight holds still because the age is the only clock; `hud.dim` over the flight runs without error.
   - Arrival variants: `arrival_ticks` 101, 124 and 200 each draw on their last age without error. Levels 1, 0, 9 and 99 raise `KeyError`: outside the contract's 2 to 8, and the core never builds them (`LevelUpBanner.level` is 2 to `LEVEL_COUNT`), so not a bug.
   - Hand-off at the arrival tick (age 123 to 124), size and position: the image size and center match, but the digit's visible ink does not. See B1.
4. **Assumptions:** Source of "no jump": the task's Acceptance check (center and size within 1 px), `view.md` "The flight" ("the HUD's first pop frame is the same image where it lands") and the main session's note to check size and position at the hand-off. I measured the visible ink, not only the image box, because the box has empty rows in it.
5. **Documentation differences:** None.
6. **Next:** UI Developer, Fix mode, on B1 in this report. Integration Engineer only after a pass.
7. **Status:** done.

## Bugs
- **B1** `game/ui/level_up_view.py:433-439` (`_flight_frame`), UI Developer. The flight's last image holds its digit centered in the image. The HUD's pop frame 0 holds its digit lower in the same 23x51 image, so the visible digit drops 2.5 to 3.5 px on the arrival tick. Reproduce (from `game/`): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa06e.py /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa06shots` (compares `_flights[level].frames[-1]` with `hud._pop_frames[level][0]`; `qa06c.py` to `qa06f.py` set up the same window the implementer's script does). Window check: `qa06f.py`.
  Expected: at age 123 the flight's last image and at age 124 the HUD's first pop frame put the digit's ink at the same place. Size and center are met, and so should the glyph be: no jump in position.
  Actual: same image size, different ink rows. Level 2: flight ink rect `(0, 9, 23, 32)`, pop frame `(1, 11, 22, 33)` (ink center y 25 against 27.5). Level 3: `(0, 9, 23, 33)` against `(1, 13, 22, 31)` (25.5 against 28.5). Level 4: `(0, 10, 26, 31)` against `(0, 13, 26, 31)` (25.5 against 28.5). Level 8: `(0, 6, 28, 38)` against `(2, 13, 25, 31)` (25 against 28.5). In the window at level 3, the flight's ink center is y 383.5 on age 123 and the pop's digit ink center is y 386.5 on age 124: a 3 px step down, against the 1 to 2 px the number moved per tick at the end of the flight. Level 8 is also 3 px wide of the pop's ink (28 against 25 in ink width, outline included, 6 px taller).
  Source of the expected value: `docs/contracts/systems/level-up/view.md`, "The flight" ("so the HUD's first pop frame is the same image where it lands"); `rationale.md`, "The flight ends on the pop's first size"; task acceptance check (center and size within 1 px); main session's brief (size and position match, no jump). The flat tier color on the last frame is accepted and is not part of this bug.
  Proposed fix: in `_build_flight`, take the HUD's pop frame 0 ink rect (`hud._pop_frames[level][0].get_bounding_rect()`, read in `__init__` where `hud` is still in hand) and in `_flight_frame` place the fitted number so its ink rect center is the interpolation, by `share`, from the image center (share 0) to the pop frame's ink center (share 1), instead of the image center always. Also fit the ink to that rect's size at share 1 (scale by the ink rect against the pop's ink rect, not the whole image against the whole image) so the visible height matches too (flight 32 to 38 px against the pop's 31 px). That keeps one scale per frame image at startup, no per-frame work, and makes the flight's last frame and the pop's first frame the same picture in place, as `view.md` says. If the Director prefers, the Architect can word the contract so the match is by the image box only; then B1 is not a bug. Say so under Next.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass

## Round 2 2026-11-06

1. **Task:** Re-test of B1 after the UI Developer's fix (`## Fix 2026-11-06` in `docs/reports/implementation/ui/DRA-148-06-ui-developer.md`). Per the main session's decision (for the Director, away): at the hand-off the visible digit must sit where the HUD's pop frame 0 draws it. That wins over "ink center on the slot center"; the image box center stays on the slot center. So the old acceptance assert "ink center within 1 px of the slot center" no longer applies.
2. **Delivered:** `docs/reports/qa/DRA-148-06-ui-developer.md` (this round). Inline scripts only, in the scratchpad (`qa06c.py`, `qa06e.py`, `qa06g.py`, `qa06h.py`). Nothing saved in `game/tests/`.
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass`.
   - B1, hand-off ink center, drawn pixels (`draw_flight` at age 123 on a black window, against pop frame 0 blitted centered on the slot as `HudView._draw_level` does): the ink centers are equal at every level 2 to 8 (center delta (0, 0) each). Centers: level 2 (719, 385), 3 (719, 386), 4 (719, 386), 5 (719, 386), 6 (719, 385), 7 (719, 386), 8 (719, 386). The step from age 123 to the pop's first frame is (0, 0) at levels 3 and 8.
   - Ink size at age 123 against pop frame 0: equal at levels 4, 5, 6; within 1 to 2 px elsewhere (level 2: 22x31 against 22x33; 3: 21x31 against 22x31; 7: 22x30 against 22x31; 8: 23x31 against 25x31). This is the implementer's stated even fit, no stretch. I accept it: no jump in position, and the size gap is at most 2 px.
   - Image sizes: flight last frame equals pop frame 0 at every level (23x51, 23x51, 26x51, 23x51, 25x51, 23x51, 28x51 for levels 2 to 8). Image box center equals the slot center at share 1.0 (718/719, 383).
   - Flight path, levels 3 and 8, ages 100 to 123: ink width and height never grow (level 3: 47x68 down to 21x31; level 8: 50x68 down to 23x31). Per-tick steps shrink at the end: last steps (6, 4) then (2, 1) px. Start at age 100: ink center (336, 250), unchanged. Hand-off adds no step.
   - Outside the flight: window pixel-equal to the HUD alone for ages 0 to 99 and 124 to 153 at levels 2 to 8; also equal for age -5 and 1,000,000 (earlier script, rerun).
   - Cost: 168 `draw_flight` calls (levels 2 to 8, ages 100 to 123) made 0 surfaces and called no scale, smoothscale, rotate or rotozoom.
   - Same inputs twice, ages 100 to 123: byte-identical windows. `hud.dim` over the flight runs. `arrival_ticks` 101, 124 and 200 draw on their last age. Levels 1, 0, 9 and 99 raise `KeyError`, outside the contract's 2 to 8 (as in round 1, not a bug).
4. **Assumptions:** The white-versus-tier flat color on the last frame stays accepted (away log D2). Source for the new rule: the main session's decision above, which replaces the old center-on-slot wording of the task's Acceptance check for the ink, not for the image box.
5. **Documentation differences:** None pending from me. The task's acceptance wording "ink center within 1 px of the slot center" and `view.md` "The flight" now read looser than what is built (the ink lands where the pop draws it, 2 to 3 px below the slot center, because the HUD's number image has empty rows above its ink). The Architect may want to word it as "image box center on the slot center and the ink at the pop's first frame's ink". Not a bug and not blocking.
6. **Next:** Integration Engineer.
7. **Status:** done.

## Bugs (Round 2)
- **B1** fixed. Reproduced with the same comparison: ink center delta (0, 0) at levels 2 to 8, no new bug found.

## Harness (Round 2)
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass

