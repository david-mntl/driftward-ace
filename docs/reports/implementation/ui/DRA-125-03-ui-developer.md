Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the burst view, `draw_burst` and `BURST_COLOR`, for DRA-125 (task `docs/contracts/DRA-125/tasks/DRA-125-03-ui-developer.md`, from the Architect).
2. **Delivered:** `game/ui/burst_view.py` (new). This report.
3. **Checks:**
   - `python3 -c "import pygame; assert pygame.IS_CE"`: pygame-ce 2.5.8, passes.
   - `python3 -m py_compile game/ui/burst_view.py`: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format, 107 files).
   - Headless draw run, `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/burst_check.py` (a scratch script outside the repo; it flood-fills 8-connected non-black pixels into blobs). Black 640 x 480 surface. Blob centers are pixel-box centers; the radius is the distance from the origin and carries up to about 1 px of pixel rounding. Each PNG is `burst_<x>_<y>_<age>.png` in `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/`.

     | Burst | opacity | blobs | radius (px) | max channel | px per blob |
     |---|---|---|---|---|---|
     | (320,240) age 0 | 1.000 | 1 (see Assumptions) | 0.7 | 255 | 9 |
     | (320,240) age 30 | 0.750 | 12 | 29.3 to 30.5 | 191 | 9 |
     | (320,240) age 60 | 0.500 | 12 | 59.4 to 60.5 | 128 | 9 |
     | (320,240) age 119 | 0.008 | 12 | 118.5 to 119.5 | 2 | 9 |
     | (320,480) age 30 | 0.750 | 7 | 29.3 to 30.5 | 191 | 6 or 9 |

     Radius is age x 1 px, as the age gives. Fainter with age: 255, 191, 128, 2. After the bottom-edge burst: 7 blobs, the lower half off the canvas. The two squares on the horizontal (y = 479.0 center) are cut to 6 px. The five lower ones are off the canvas.
   - Follows the state: ages 0 to 119 above move the squares out and fade them. The script asserts `repr(burst)` is the same before and after each draw (core state unchanged).
   - Grep of `game/ui/burst_view.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `import game.ui|from game.ui|from ui|import ui`: no hits.
   - `check.sh typecheck`: FAIL, 7 errors in 4 test files, all `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py` and `test_coin.py`. This is the failure `impact.md` expects from DRA-125-01 (cleared by DRA-125-09). No error in `game/ui/burst_view.py`.
   - `check.sh ui`: 65 passed.
   - `check.sh core`: 26 failed, 3205 passed. All 26 are in `test_coin.py`, `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py` and `test_run_waves.py`. All 26 come from DRA-125-01 changing the last-life tick. Most are named in `impact.md`. Eight are not named but fit its general rule (any test that loses the last life and expects `game_over` on that tick, a frozen world, or the retry): `test_a_held_arrow_never_retries`, `test_a_new_run_starts_like_the_first`, `test_a_fall_and_a_touch_on_one_tick_cost_only_the_fall`, `test_a_graze_and_a_hit_by_another_hazard_on_one_tick_the_graze_pays_then_the_hit_counts`, `test_no_playing_tick_changes_the_coin_points`, `test_score_never_goes_down_and_keeps_counting_through_falls_and_waits`, `test_the_waves_step_once_on_every_playing_tick` and `test_the_same_first_seed_gives_the_same_run_of_waves_and_retries`. I did not touch core or tests.
4. **Assumptions:**
   - At age 0 all 12 squares sit at the origin, so they show as one 3 x 3 blob, not 12 on a circle (radius 0). That is what core's `particle_centers` gives. The 12 blobs appear from age 3 on. This differs from the acceptance check's "12 blobs" at age 0 only in that overlap.
   - Alpha blends: overlapped squares at age 0 add up, so the max channel there is 255 either way.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-125/tasks/DRA-125-03-ui-developer.md`. Left alone: the frame wiring (`game/app/frame.py`, Integration Engineer), core and tests. The 8 core failures above are not in `impact.md`'s list by name; DRA-125-09 should confirm them.
7. **Status:** done.

## Decisions
- One module-level `@cache` function, `_square_image(size, alpha)`, as `graze_view.py` does for its ring: a square image built once per key, kept, so no new surface per square per frame. Source: run.md, Presentation, Burst, Cache.
- `draw_burst` computes size and alpha once, gets one image, and blits it at each center from `burst.particle_centers`. Opacity and positions come from core; nothing is copied or computed in the view.
- Top-left is `round(c - size / 2)`, with Python's banker's rounding at .5, as the contract's formula says (`round`).
- `BURST_COLOR` is (255, 255, 255). Source: scope report DRA-125, Values needed, Burst (white, stand-in until LD-08). `MAX_ALPHA` 255 is the 8-bit alpha range, as in `graze_view.py`.
- The module has `log = logging.getLogger(__name__)` per `game/CONTEXT.md` and logs nothing per frame.
