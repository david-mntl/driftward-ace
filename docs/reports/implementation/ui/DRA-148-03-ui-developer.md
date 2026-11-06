Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-148-03 (Architect): the level-up look records and the pure motion functions the banner, the flight, the bump and the HUD pop will read. Task file: `docs/contracts/DRA-148/tasks/DRA-148-03-ui-developer.md`.
2. **Delivered:** `/workspace/game/ui/level_up_rules.py` (new), `/workspace/game/ui/level_up_motion.py` (new). No other file touched.
3. **Checks:** run from `/workspace/game`. The acceptance script is `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/motion_check.py` (outside the repo; its asserts are summarised below). Command: `python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/motion_check.py`. Starting values of its own: band open 2..12, close 80..120, glass share 0.5; number fall 10..30, overshoot 8, peak share 0.5, stretch (0.9, 1.1), squash (1.25, 0.8) over 10 ticks; bump 4 px, 12 ticks, peak 0.25; fly start 70, arrival 120, arc 30; pop 20 ticks, start 1.5, undershoot 0.9 at 0.5. Result: `ALL ASSERTS PASSED`. Printed values:
   - `band_shares` (glass, lines): age 0 `(0, 0)`; 7 `(0.5, 0.5)`; 12 to 80 `(1, 1)`; 90 `(0.5, 1.0)`; 100 `(0, 1.0)`; 110 `(0, 0.5)`; 120 and 130 `(0, 0)`. Glass is 0 from age 100, lines from 120: the glass closes before the lines. Lines are 1.0 on every age 12..100.
   - `fall_offset` (distance 200): ages 0, 5, 10 give -200.0; 14 gives -36.9; 20 (the peak) gives exactly 8.0 (the overshoot); 30, 31, 100 give exactly 0.0. Maximum over ages 0..39 is 8.0.
   - `pose_scales`: ages 0 and 29 `(0.9, 1.1)`; 30 `(1.25, 0.8)`; 32 `(1.128, 0.8976)`; 35 `(1.03125, 0.975)`; 40, 41, 100 exactly `(1.0, 1.0)`.
   - `bump_offset` ages 0..49: `0` for ages 0..30, then `3, 4, 4, 4, 3, 3, 2, 2, 1, 1`, then 0 from age 42 on (fall_end 30 + 12 ticks). Peak 4 = bump.pixels at age 33 (peak share 0.25 of 12 = tick 3). Never negative. With `pixels=0`, 0 on every age 0..59.
   - `fly_share`: ages 0 and 70 give 0.0; 95 gives 0.5; 120 and 130 give 1.0. `fly_position`: share 0 equals start exactly, share 1 equals end exactly (tuple equality on `(160.0, 240.0)` and `(550.3, 91.7)`); share 0.5 is `(355.15, 150.85)` with arc 30 and `(355.15, 165.85)` with arc 0 (arc bows up by half the arc, as a quadratic does).
   - `pop_scale`: elapsed 0 gives exactly 1.5 (start scale); 5 gives 1.2; 10 gives exactly 0.9 (undershoot); 15 gives 0.95; 20, 21, 50 give exactly 1.0. Maximum over 0..39 is 1.5 (never above start scale).
   - `fade_share(age, 10, 20)`: 0, 0, 0.5, 1, 1 at ages 0, 10, 15, 20, 30.
   - `python3 -c "import pygame; assert pygame.IS_CE"`: pygame-ce 2.5.8. `python3 -m py_compile` on both files: clean.
   - `game/tests/check.sh lint`: pass (ruff check and format). `game/tests/check.sh typecheck`: pass (mypy strict, 148 files).
   - Grep of both files for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits (the word "pygame" appears once in a docstring saying the module does not use it; neither file imports it). Grep of `game/core/` for `import ui` and `from ui`: no hits.
4. **Assumptions:**
   - `fade_share` takes ints per the contract; the other functions share a private float `_ramp` so the glass's window end (`close_start + window * close_glass_share`) can be fractional.
   - Both modules start with `log = logging.getLogger(__name__)`, as `game/CONTEXT.md` asks of every module with code, and as `hud_rules.py` does. Nothing is logged.
   - Record field types follow the schema: `int` where it says integer, `float` where it says number. `LevelUpLook.colors` is `Mapping[str, RGB]`.
   - `bump_offset` is 0 on the landing tick itself (the bump "rises from 0") and reaches 3 of 4 px on the next tick; `round()` makes the whole px.
   - `fall_offset` crosses 0 on its way to the peak (it goes from -distance to +overshoot); only "negative up to fall_start" is in the contract.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-148/tasks/DRA-148-03-ui-developer.md`. Left alone: the look loader `game/app/level_up_tuning.py` (Integration Engineer), the view (DRA-148-04 and -06), the HUD (DRA-148-05), tests. `git status` also shows `game/core/waves.py` modified and `game/core/level_up.py` new: not mine (Gameplay Implementer's tasks).
7. **Status:** done.

## Decisions
- Easing: `_smooth` (smoothstep) for the band, the flight, the fall's return, the bump's return and both legs of the pop; `_ease_out` (cubic) for the fall's first leg, the squash and the bump's rise. Reason: a fall that hits its end at full speed and then relaxes reads as weight; the squash and the bump should be at full effect on the landing tick. Both are exact at 0 and 1. Source: the task, Not in the contract (architect call).
- One `_mix(a, b, s)` written as `a*(1-s) + b*s`, so share 0 and 1 give `a` and `b` exactly (the contract asks for exact end points: the peak overshoot, the flight's start and end, the pop's end scale). `a + (b-a)*s` does not.
- `fly_position` uses the Bernstein form with weights `(1-s)^2`, `2(1-s)s`, `s^2`: at share 0 the weights are exactly 1, 0, 0 and at share 1 exactly 0, 0, 1, so the end points are exact.
- Early returns for the "from here on" cases (`fall_offset` at or after `fall_end`, `bump_offset` outside its window, `pop_scale` from `pop.ticks`) so the "exactly 0 / exactly 1.0 after" promises do not depend on float rounding.
- `bump_offset` needs no special case for `pixels == 0`: `round(0 * depth)` is 0.
- Division guards are not added: the schema and the loader's order checks (`open_start < open_end`, `fall_start < fall_end`, shares strictly between 0 and 1) keep every denominator above 0. Trusting values inside `ui/` follows `game/CONTEXT.md`.

## Review fix 2026-11-06: docs/reports/review/DRA-148-03-ui-developer.md

Fixed: DRA-148-03-F1

1. **Task:** Answer the review of DRA-148-03 (round 1): carry the acceptance script in the report. Asked by the `/implement` skill.
2. **Delivered:** this section only. No code changed. `game/ui/level_up_rules.py` and `game/ui/level_up_motion.py` are as before.
3. **Checks:** the script below is the full acceptance script. To run it, save the block to any file outside the repo (for example `motion_check.py` in a scratch folder) and run `python3 <that file>`. It puts `/workspace/game` on `sys.path` itself, so the working directory does not matter. Its starting values are in the first lines (band, number, bump, fly, pop records and `ARRIVAL = 120`). Re-run this round: `ALL ASSERTS PASSED`, and the printed numbers are the ones listed in the section above. Also re-run from `/workspace/game`: `python3 -c "import pygame; assert pygame.IS_CE"` (pygame-ce 2.5.8); `python3 -m py_compile` on both files, clean; `tests/check.sh lint` PASS (ruff check and format); `tests/check.sh typecheck` PASS; grep of both files for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits; grep of `game/core/` for `import ui`, `from ui`, `game.ui`: no hits.
4. **Assumptions:** the script text below is the same file the first section named, unchanged. The first section's scratchpad path is session-local and no longer the way to run it.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, on `docs/reports/review/DRA-148-03-ui-developer.md`.
7. **Status:** done.

```python
"""Acceptance script for ui/level_up_motion.py, with starting values of its own."""
import sys
sys.path.insert(0, "/workspace/game")
from dataclasses import replace

from ui.level_up_motion import (band_shares, bump_offset, fade_share, fall_offset, fly_position,
                                fly_share, pop_scale, pose_scales)
from ui.level_up_rules import BandLook, BumpLook, FlyLook, NumberLook, PopLook

band = BandLook(100, 100, 0, 2, 12, 80, 120, 0.5, 1, 5)
num = NumberLook(80, 2, 0, 10, 30, 8.0, 0.5, 0.9, 1.1, 10, 1.25, 0.8, 4)
bump = BumpLook(4, 12, 0.25)
fly = FlyLook(70, 30.0, 8)
pop = PopLook(20, 1.5, 0.9, 0.5, 10, 8, 10, 10, 1, 8)
ARRIVAL = 120

print("fade_share(age,10,20):", [(a, fade_share(a, 10, 20)) for a in (0, 10, 15, 20, 30)])
print("band_shares (glass, lines):")
for a in (0, 2, 7, 12, 50, 80, 90, 100, 101, 110, 120, 130):
    print("  ", a, band_shares(a, band))
g = [band_shares(a, band) for a in range(0, 131)]
assert g[0] == (0.0, 0.0) and g[50] == (1.0, 1.0) and g[130] == (0.0, 0.0)
glass_zero = next(a for a in range(80, 131) if g[a][0] == 0.0)
lines_zero = next(a for a in range(80, 131) if g[a][1] == 0.0)
print("glass is 0 from", glass_zero, "lines from", lines_zero)
assert glass_zero < lines_zero and all(g[a][1] == 1.0 for a in range(12, 101))

D = 200.0
print("fall_offset:")
for a in (0, 5, 10, 14, 20, 30, 31, 100):
    print("  ", a, fall_offset(a, num, D))
assert all(fall_offset(a, num, D) < 0 for a in range(0, 11))
assert fall_offset(0, num, D) == fall_offset(10, num, D) == -D
assert fall_offset(20, num, D) == num.fall_overshoot_px  # peak share 0.5 of 10..30
assert fall_offset(30, num, D) == 0.0 and fall_offset(99, num, D) == 0.0
assert max(fall_offset(a, num, D) for a in range(0, 40)) == 8.0

print("pose_scales:")
for a in (0, 29, 30, 32, 35, 39, 40, 41, 100):
    print("  ", a, pose_scales(a, num))
assert pose_scales(29, num) == (0.9, 1.1) and pose_scales(30, num) == (1.25, 0.8)
assert pose_scales(40, num) == (1.0, 1.0) and pose_scales(100, num) == (1.0, 1.0)

print("bump_offset:")
vals = [bump_offset(a, num, bump) for a in range(0, 50)]
print("  ", vals)
assert all(v == 0 for v in vals[:30]) and all(v == 0 for v in vals[30 + bump.ticks:])
assert max(vals) == bump.pixels and vals[33] == bump.pixels and min(vals) == 0
assert all(bump_offset(a, num, replace(bump, pixels=0)) == 0 for a in range(0, 60))

print("fly_share:", [(a, fly_share(a, fly, ARRIVAL)) for a in (0, 70, 95, 120, 130)])
assert fly_share(70, fly, ARRIVAL) == 0.0 and fly_share(120, fly, ARRIVAL) == 1.0
start, end = (160.0, 240.0), (550.3, 91.7)
for s in (0.0, 0.5, 1.0):
    print("fly_position", s, fly_position(s, start, end, fly.arc_px))
assert fly_position(0.0, start, end, 30.0) == start and fly_position(1.0, start, end, 30.0) == end
print("fly_position arc 0, share .5:", fly_position(0.5, start, end, 0.0))

print("pop_scale:", [(e, round(pop_scale(e, pop), 4)) for e in (0, 5, 10, 15, 19, 20, 21, 50)])
assert pop_scale(0, pop) == pop.start_scale and pop_scale(10, pop) == pop.undershoot_scale
assert pop_scale(20, pop) == 1.0 and pop_scale(21, pop) == 1.0
assert max(pop_scale(e, pop) for e in range(0, 40)) == pop.start_scale
print("ALL ASSERTS PASSED")
```

## Decisions
- The script is pasted unchanged so the numbers in the first section stay reproducible. Its paths are absolute (`/workspace/game`), as the repo lives there.

## Answers
- DRA-148-03-F1. Fixed: docs/reports/implementation/ui/DRA-148-03-ui-developer.md (this `## Review fix` section), the full acceptance script is now in a fenced block with the run instructions and its starting values.
