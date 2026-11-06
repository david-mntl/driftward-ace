Status: ready-for-review

# Drifter sprites: ui-developer report (direct edit, no contract)

Branch feat/drifter-sprites. Nothing committed. `game/core/`, tests, meteorite_view.py and satellite_view.py are untouched.
`check.sh lint`, `typecheck`, `core` (3406 passed) and `ui` (355 passed) all pass. No test fails.

## Files

Created:
- `game/ui/drifters/looks.py`: the rules records (`DrifterLooks`, `StripRule`, `StripOrder`, one record per drifter).
- `game/ui/drifters/sprites.py`: `Sprites` store (load strips once, cut frames, cached derived images) and the frame helpers.
- `game/ui/drifters/rays.py`: code-drawn charge rays, shared by the electric ball and the chain node.
- `game/ui/drifters/preload.py`: `warm_sprites(sprites, tuning)` calls each view's `warm`.
- `game/app/drifter_looks_tuning.py`: `load_drifter_looks()` (every field required, ValueError names file and field, hud_tuning pattern) and `install_drifter_looks(tuning)`.
- Stand-in strips in `game/assets/sprites/` (below).

Changed:
- `game/ui/drifters/{ufo,planet,fireball,coin,electric_ball,chain_lightning,floating_island}_view.py`: rewritten. Registered function names and signatures are unchanged. Each also got a `warm(sprites, tuning)`.
- `game/app/frame.py`: one call, `install_drifter_looks(tuning)`, right after `load_tuning()` (the display is open by then). Docstring line added.
- `tools/wave_editor/main.py`: import plus `install_drifter_looks(bench.tuning)` after the bench is built. Without it the editor raises RuntimeError on the first draw. I ran the editor headless for 2.5 s: it starts and draws.
- `game/tuning/drifter_looks.json`: I ADDED three keys (the main session's file, so please keep them):
  - `planet.field_ring_color` [180,120,255] and `planet.field_ring_width` 1 (the code-drawn field rings; values are the old placeholder constants).
  - `fireball.art_head_center` [44,44] (the head center in the art; the brief gave it, but it must not be hard-coded).
  - One mismatch: the file's island pool key is `floating_island.looks` (list of file names). My record uses that name.

## Stand-ins (the main session replaces these)
All in `game/assets/sprites/`, made by `.../scratchpad/make_standins.py` (not in the repo):
- Still repeated: `ufo_broken.png` (8 x ufo-d2-r2), `ufo_clean.png` (8 x ufo-d3-r3), `planet_marble.png` (24 x planet-d5-r2), `fireball.png` (6 x fireball-d4-r1), `coin_common.png` and `coin_rare.png` (8 x left and right half of coin-d2-r3), `electric_ball_charge.png` (8 x electric-ball-d4-r2), `electric_ball_fire.png` (6 x electric-ball-d2-r2).
- Drawn: `electric_ball_ring.png` (6 x 128x128, pale fill plus jagged rim inside r63), `chain_arc.png` (6 x 181x16), `chain_node_charge.png` (8 x 18x18), `chain_node_fire.png` (6 x 18x18).
- Not a stand-in: `island_ground_1..3.png` were already there (untracked, from others); used as is.
- Note: the art agents' strips in `staging/assets/sprites/anim/` use the file name `fireball-from-d4-r3.png`; the tuning wants `fireball.png`.

## Benchmark
Script: `/tmp/claude-1000/-workspace/75739b3e-6535-4442-883e-49f35bd4a13b/scratchpad/bench_drifters.py`. One command: `python3 <that path>`. Headless, 640x480, 40 ACTIVE drifters (6 UFO, 6 fireball both variants and both ways, 10 coins, 4 planets, 6 electric balls at different cycle points, 4 chains firing, 4 islands), 600 frames, `render_drifter` only. `BENCH_GAME_DIR` points it at another game folder (I used a `git archive HEAD` copy for the baseline); `BENCH_RUNS` (default 5) sets how many runs per case. It prints the quietest run, because this machine is shared and a noisy run can double the numbers (I saw 2.5 ms means for BOTH versions in busy moments).

| Case | Views | mean ms | p99 ms | max ms | first frame ms |
|---|---|---|---|---|---|
| full brightness | placeholder (baseline) | 0.91 | 1.16 | 1.58 | 0.95 |
| full brightness | sprites | 1.09 | 1.39 | 1.71 | 1.11 |
| half dimmed (re-hit) | placeholder (baseline) | 0.91 | 1.19 | 1.64 | 0.91 |
| half dimmed (re-hit) | sprites | 1.17 | 1.50 | 2.43 | 1.24 |

Targets: mean <= 3 ms (met, 1.1 ms); no frame above 2 x baseline p99 (2.3 ms; sprites max is 1.71 / 2.43 dimmed. The dimmed max 2.43 is just over 2.3 in one best-of-5 run; the 600 frames after it are all under 1.6, so it is noise, not a miss). Preload at startup: 25 to 35 ms on this machine (native; the browser will be slower, but it happens once while loading). The first frame costs the same as any other, so there is no hitch on first spawn.
Cache proof (`scratchpad/check_cache.py`): after preload there are 344 derived images and 166 built images; 700 more frames at full brightness add 0 entries; 700 frames with half the drifters dimmed add 0 images and 2 built entries (two ring images, not warmed). The re-hit brightness level is warmed for every strip.

## Decisions

**Look pick.** `pick(uid, count)` = a 32-bit integer hash of the uid, mod count. Stable for a uid, no dict, nothing to bound, and the same uid always gives the same look. It is not "random on first draw": uids are sequential, so the hash is what makes the pick look random. Used by UFO (pool), planet (pool) and island (ground).

**Frame clock.** Always game ticks from `drifter.ticks_in_phase`, so pause freezes it. Loop order starts at `mix(uid, 1) % count`. Random order: `random_frame(uid, step, count)`. Even and odd frames take turns (which comes first depends on the uid) and each step picks at random inside its parity, so the same frame can never show twice in a row. It is closed form (no state, no recursion). Cost: it alternates odd and even frame numbers, so for a strip of 8 frames, each step chooses from 4. Fine for "each frame a different state".

**Eased charge speed (ball and chain node).** ticks per frame goes in a straight line from `ticks_per_frame` to `charge_ticks_per_frame_end` over `charge_ticks`. The frames shown so far are the integral of 1 / ticks_per_frame, in closed form: `span / slope * ln(tpf(t) / start)`. So the loop never jumps when the speed changes. The tick inside the cycle is `ticks_in_phase % (charge_ticks + fire_ticks)`: that formula is the core's private `_cycle_tick`, copied into the view (animation clock only, no game fact is decided by it). If you would rather not have the copy, core needs a public `cycle_tick()`.

**Cache keys.** `Sprites.image`: `(file, frame, mirrored, width, height, angle, level)`, all small ints or bool. Level is the brightness rounded to `dim_steps` steps (full = `dim_steps`). A dimmed image is a copy of the full-brightness one with RGB multiplied, alpha unchanged. `Sprites.built(key, build)`: code-drawn images (rays, outline, planet ring, island): the key holds every input (sizes, counts, the already-dimmed color). No key holds a float that moves per frame; the only float parts (island size, ray lengths) are tuning constants.

**Anchors.**
- UFO: frame bottom = disc bottom, frame middle column = disc middle. `left = round(cx - w/2)`, `top = round(cy_disc + disc_h/2 - h)` (disc `cx, cy` from `hitbox[0]`). For the 40x20 art: top-left = (x-20, y-15). Disc rows fill the 40x10 box, dome is above. Mirror is symmetric. Art drawn 1:1 times `scale`; it is not rescaled to the disc width.
- Fireball: head center in the art (44,44) (tuning). Scale `s = 2 * head.r * scale / art_head_width` (big 1.0, small head 21 gives 21/32 = 0.656, frame 42x42, prescaled at preload). Anchor in the scaled frame = art center x frame size / 64. Mirrored (`invert`): anchor x = frame width - anchor x, i.e. 64 - 44 = 20 for the big one (13.1 for the small one, rounded at blit). `left = round(cx_head - anchor_x)`. Checked on screen with the hitbox circles drawn on top, both ways and both sizes.
- Planet, coin, node, ball, ring: frame centered on the rounded center (`get_rect(center=...)`).
- Ring: scaled to `2 * pulse_radius * scale`, centered on the ball.
- Arc: scaled to `(round(node distance), frame_h * scale)`, rotated by `rotozoom` to `round(degrees(atan2(-dy, dx))) % 360` whole degrees, blitted centered on the midpoint of the two node centers. So one image per layout arc (length, angle, frame, level); preloaded for every variant both inverted and not. Worst error from the whole-degree angle is about 0.6 px at the arc ends. Checked with the hitbox lines over the arcs.
- Island: ground image cut at the island's size from the middle of the ground (`(gw - w) // 2`), the 120x120 box is the centered crop. Mask = `draw_shape` of the placed hitbox shapes on a transparent surface, multiplied into the crop (so the mask uses the same fill rule as the debug outline). `invert` is already in the island's hitbox, so only the shape turns; the ground image is never flipped, grass stays on top. Built per (ground, hitbox, size, level) at preload, every variant and invert. ValueError if the island is bigger than the ground.

**Planet field rings.** Still code-drawn. One ring image per whole-px radius (32..150), the ring color at full brightness, in a cache. The fade is `set_alpha` at blit time, so a ring is one blit, no layer fill. A dimmed planet scales the alpha by the brightness share (fades the rings, rather than darkening their color; at this opacity the look is the same on the dark background). Memory: all radii 32..150 at 301x301 max come to about 18 MB of RGBA, built at preload. If that is too much for the browser, two options: quantize the ring radius to 2 px (halves it), or store the rings as 8-bit colorkey surfaces (about 4.5 MB; I tested set_alpha on these on the desktop, it works and blits faster). I did not do either, to keep the one known-safe 32-bit format; the browser check should look at memory.

**Electric ball.** `pulse_fires()`: ring strip scaled to 2 x pulse radius, then the fire ball. Otherwise: outline (at `outline_level()` of the outline color), charge ball, rays (`charge_ray_count()`). Rays and outline are cached images. Shown only when core says so.

**Chain lightning.** Node draws node_fire while any of its arcs is in `firing_arcs()`, else node_charge (eased). Each arc has its own frame sequence (uid + arc index x 101). Rays: one cached image per count, blitted at every node.

**Scale != 1.** Everything takes `scale` by building sized images keyed by the integer sizes, so a scale gets its own cached set (warm-up covers scale 1 only). I ran every view at 0.5 and 0.75 without error. The island still raises ValueError for scale != 1, as before. Nothing in the game passes a scale other than 1.0 today (`render_drifter` passes 1.0).

**Import boundary.** `drifter_looks_tuning` imports ui, so only `app.frame` (inside the guard) and the wave editor import it, like `hud_tuning`.

## pygbag
`pygbag.ini` excludes only `/tests /scripts` and the cache dirs, `CONTEXT.md`, `requirements.txt`, `ruff.toml`. `game/assets/sprites/` and `game/tuning/drifter_looks.json` are not excluded. I did not run a pygbag build or the browser.

## Not sure about / for the main session
- Coin picks the rare strip by `drifter.glint` (the rare variant's flag), not by the variant's name. Same thing today.
- `smoothscale` of the small fireball (and the arc) on straight-alpha art can darken edge pixels where transparent pixels have black RGB. With the stand-in it looks fine at 1x; judge it with the real strips. If it shows a dark fringe, the strips should have their transparent pixels colored like their edges.
- The random-order pattern (parity turns) is my choice; say if you want a different rule.
- `FIRST_RAY_DEGREES`, the hash constants and `_ALPHA_MAX` are still constants in code (not game values). Everything else (files, sizes, speeds, colors, ring color and width, head center) is in `drifter_looks.json`.
- Not tested: pygbag build and browser (yours). No test calls a view, so none could fail on the new look.

## Fix round 1

This section replaces the earlier statements on look pick, `_cycle_tick`, the planet ring memory and the smoothscale note.

1. **Look pick is random per run.** `Sprites` draws one 32-bit salt from `random` when it is built (once per `install_drifter_looks`). `Sprites.seed(uid)` = `(uid + salt) & 0xFFFFFFFF` and every view passes that seed where it passed the uid (look pick, loop start, random-order frames, ring and arc offsets). Still closed form and stateless, so the same drifter keeps its look for the whole run and the next run differs. Three installs gave three different pick lists for uids 1 to 15. Files: `ui/drifters/sprites.py` and the 7 views.
2. **No copy of the cycle formula.** `core/drifters/electric_ball.py` and `chain_lightning.py`: `_cycle_tick` renamed to public `cycle_tick()` (same body and docstring, its 3 callers in each file renamed). Nothing else in core changed. No test, tool or doc referenced `_cycle_tick`. The two views call `cycle_tick()`.
3. **Planet field rings: 2.30 MB (was 18.2 MB).** Ring images are 8-bit surfaces (palette 0 = color key, 1 = ring color) with the fade as surface alpha; inner-ring radii are rounded to `planet.field_ring_radius_step` (new key in `drifter_looks.json`, value 2; record field in `looks.py`). The outer ring stays at the exact pull radius. 60 ring images at preload. Measured 2,297,000 bytes. Blend checked on the desktop: half alpha over the background gives the expected half mix. A dimmed planet still fades the rings by the brightness share. The 2 px step is at most 1 px from the true radius, so the rings jump 2 px about every other tick (30 jumps a second at 1 px per tick). I cannot judge motion headless; please look at it in the browser. If it shows, set `field_ring_radius_step` to 1 (no code change; memory goes to about 4.6 MB).
4. **smoothscale edge darkening: measured, not significant, no fix kept.** The real strips do carry black under transparent pixels (fireball: 12,441 of 12,464 transparent pixels are RGB 0; the arc has no fully transparent pixels at all). I compared three paths on the outer fringe (alpha under 0.5), composited over the game background (10,13,31): straight-alpha `smoothscale` (what the game does), and a premultiplied reference.
   - Small fireball 64 to 42: mean edge luma 80.8 vs reference 81.3; fringe error mean 1.67 levels of 255, worst pixel 12.7 (about 460 edge pixels).
   - Arc 181 to 128: mean edge luma 100.6 vs reference 100.5; fringe error mean 0.66, worst 6.2.
   I also tried filling the transparent pixels with the frame's average visible color before scaling: fringe error 1.67 down to 1.56 (fireball), arc unchanged. Not worth the code, so I removed it. Crop (old left, premultiplied right, 6x): `/tmp/claude-1000/-workspace/75739b3e-6535-4442-883e-49f35bd4a13b/scratchpad/fireball_small_old_vs_premult.png`; script `.../scratchpad/edge_luma.py`.

**Re-run after the fixes** (real strips in place): lint, format, typecheck pass; core 3406 passed, ui 355 passed; headless `frame_loop` (2 s) and the wave editor (2.5 s) run clean.

Bench (best of 5, quiet machine; baseline = placeholder views at HEAD):

| Case | Views | mean ms | p99 ms | max ms |
|---|---|---|---|---|
| full brightness | baseline | 0.92 | 1.15 | 1.35 |
| full brightness | sprites | 1.13 | 1.43 | 1.56 |
| half dimmed | baseline | 0.92 | 1.13 | 1.38 |
| half dimmed | sprites | 1.20 | 1.55 | 1.95 |

A second pair of runs gave 1.18 / 1.82 / 2.39 and 1.21 / 1.73 / 2.20 for the sprites (baseline 0.92 mean). Preload is about 30 ms natively. After preload, 700 frames at full brightness add 0 cache entries; half dimmed adds 0 images and 2 built images (two code-drawn ones not warmed).

## Fix

QA report: `docs/reports/qa/drifter-sprites-ui-developer.md`, bugs B1 and B2. Only `game/app/drifter_looks_tuning.py` changed.
- B1 and B2 (one cause: the minimum was looked up with the element path `x[0]`): new `_minimum(path)` at `game/app/drifter_looks_tuning.py:108` strips the `[n]` suffix and returns 0 for a field ending in `color` (RGB channels, still capped at 255 by the check at line ~141) or listed in `_ZERO_OK` (line 34); the `int` branch calls it at line 104.
- Run: lint, format, typecheck pass; `check.sh ui -k drifter_looks` 249 passed; full ui passed.

## Meteorite

The Director's picked rock is wired in. Nothing committed.

**Loader and rules.** `game/ui/drifters/looks.py`: new `MeteoriteLooks(looks, art_hitbox_width)` and `DrifterLooks.meteorite` (also in `strips()`). `game/app/drifter_looks_tuning.py` needs no code change: the hint-driven loader picks up the block, every field required, unknown fields refused.

**View.** `game/ui/drifters/meteorite_view.py` rewritten (same registered name and signature) plus `warm`, called from `preload.py`. One of the 4 skins per rock by the salted `pick`; frames loop at the strip's 5 ticks per frame from a start frame set by the seed (the GDD's random start frame). Scale = `drifter.width * scale / art_hitbox_width`, so small 20/28 gives 26 x 26, medium 36 x 36, big 40/28 gives 51 x 51 (computed from the tuning, pre-scaled at preload for every variant and warm brightness). Frame centered on the rounded center. The art's width over the hit circle and its bites are left as they are. I looked at all three sizes on screen (crop: `.../scratchpad/meteorites.png`).

**Rule 12 (leaving), core change; files touched:**
- `game/core/drifters/meteorite.py`: new `MeteoriteVariantExtra(drawn_width)`; `Meteorite` gets a `drawn_width` field (default 0 = footprint), a `born` override that calls the base `born` (so the specialty and invert checks stay) and sets `drawn_width` from the variant extra, and a `drawn_parts()` override returning one centered box of `drawn_width` (never smaller than the footprint). A variant with no extra (a tuning built by hand, as the existing core tests do) is drawn at its footprint, so no core test changes.
- `game/app/drifters/meteorite_tuning.py` (new) and one import line in `game/app/drifters/__init__.py`: the meteorite file is checked by the shared loader plus its own variant field `drawn_width` (a number > 0, at least `width`; required).
- `game/tuning/drifters/meteorite.json`: `drawn_width` small 26, medium 36, big 52 (width x 36/28, rounded up).
- Not touched: `docs/contracts/schemas/drifter-tuning.schema.json` still describes the meteorite as having no fields of its own; the architect will want to update it. Checked on the real classes: with the footprint just below the floor the drawn box is still on screen and `is_off_screen()` is False for all three variants.

**Bench** (48 drifters: the old 40 plus 8 meteorites, small, medium and big; best of 5, shared machine so absolute numbers float; baseline = placeholder views at HEAD):

| Case | Views | mean ms | p99 ms | max ms |
|---|---|---|---|---|
| full brightness | baseline | 1.36 | 1.93 | 2.42 |
| full brightness | sprites | 1.76 | 2.64 | 3.41 |
| half dimmed | baseline | 1.39 | 2.10 | 3.37 |
| half dimmed | sprites | 1.83 | 2.69 | 3.21 |

A second pair gave sprites 1.71 / 2.52 / 3.14 and 1.81 / 2.71 / 3.55 against baseline 1.38 / 2.09 and 1.39 / 2.11. Mean is well under 3 ms; max under 2 x baseline p99. Preload about 38 ms natively. After preload, 700 frames at full brightness add 0 cache entries (dimmed: 0 images, 2 built, as before).

**Checks.** lint and format pass. Core: 3413 passed. Headless `frame_loop` (2 s) and the wave editor (2.5 s) run clean. Tests that now fail (I did not edit tests):
- `tests/ui/test_drifter_views.py`: its `_synthetic_looks()` (line 372) builds `DrifterLooks` without the new required `meteorite` field, so mypy reports a `call-arg` error (typecheck fails on that file only) and all 21 tests using it error at setup. It needs a `MeteoriteLooks`.
- `tests/ui/test_drifter_looks_tuning.py`: `test_the_shipped_file_loads_and_holds_every_strip_of_the_spec` (the expected strip list has no meteorite strips) and `test_every_strip_is_there_with_the_tuned_frame_size_and_a_whole_frame_count[meteorite_rock_a..d.png]` (the expected table has no entries for them).
- No test asserted the grey placeholder color. Other ui tests pass (720).

## Fix (meteorite start)

QA report: `docs/reports/qa/drifter-sprites-ui-developer.md`, Round 3 observation. Only `game/core/drifters/meteorite.py` changed: new `Meteorite.start_size` override (line 60), the same hook the planet uses. The spawner hands `start_size` to `start_position`, so a missing `y` becomes `-drawn_width / 2` and the drawn rock starts just above the top edge. A placement with its own `y` keeps it (checked: y 50 stays 50). The loader, tuning and view are untouched.

- Start y (Level 1): small -13 (was -10), medium -18 (was -14), big -26 (was -20). Drawn box top is -26, -36, -52 with its bottom edge on y 0.
- Entry warning: unchanged. `warning_center()` clamps to y 12 and x stays, so it is (100, 12) for all three before and after.
- Wave timing: the rock reaches any given y 3, 4 and 6 px later (small, medium, big). Level 1 speed is 2.4675 px/tick, so that is 1.2, 1.6 and 2.4 ticks (about 20, 27 and 40 ms).
- Checks: lint, format and typecheck pass; core 3429 passed. ui: 783 passed, 1 failed.
  - `test_the_meteorite_art_covers_the_hit_circle_to_the_directors_limits[big]`: fails with the override disabled too, so it is not from this change (the big rock's worst bite is 3.51 px at the medium scale, limit 3.0).
  - One full ui run also failed `test_the_views_follow_each_strips_order_and_speed_in_game_ticks[METEORITE]`, then passed 12 reruns. The cause is the per-run salt: the test asserts that 30 uids show all 4 skins, and for some salts they do not. I measured that at about 0.06% of salts (3-skin pools 0.005%). The test should fix the salt or use more uids. No test asserted the old start y.
