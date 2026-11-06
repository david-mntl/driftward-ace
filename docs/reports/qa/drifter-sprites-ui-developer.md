Verdict: pass
Created by: qa-engineer

1. **Task:** QA of the direct-edit feature `drifter-sprites` (sprites and animation frames in place of the placeholder looks), implementation report `docs/reports/implementation/ui/drifter-sprites-ui-developer.md` (with `## Fix round 1`), asked for by the main session. No contract, no task file and no review report exist (the Director chose direct edit); the spec is the implementation report, the strip table in the scratchpad (`drifter-sprites-spec.md`), `game/tuning/drifter_looks.json` and the GDD (12-art-and-audio rules 3, 9, 10, 13; drifters 03 to 08 and 10).
2. **Delivered:**
   - `docs/reports/qa/drifter-sprites-ui-developer.md` (this file)
   - `game/tests/ui/test_drifter_looks_tuning.py` (249 tests: loader, strips, grounds)
   - `game/tests/ui/test_drifter_views.py` (73 tests: frames, look pick, placement, charge and fire looks, caches)
   - `game/tests/core/test_cycle_tick.py` (7 tests: `cycle_tick()`)
   - `game/tests/CONTEXT.md` (one bullet for the three files)
3. **Checks:** `game/tests/check.sh` ends `QA: fail (ui)`: 673 ui tests pass, 4 fail, all on the two bugs below. env, lint, format, typecheck and core (3413 tests) pass. Everything else in the request holds:
   - Loader: every field of the shipped file is required (walked from the JSON); a wrong type, an unknown `order`, a count under 1, a short color, an unknown field and broken JSON raise `ValueError` starting `tuning/drifter_looks.json: <field>`. A strip of the wrong width or height raises `ValueError` naming the PNG and `drifter_looks.json`; a missing PNG raises `FileNotFoundError`.
   - Strips: all 12 strips and 3 grounds exist at the tuned frame size, with the frame counts, ticks a frame and order of the Director's table (8, 8, 24, 6, 8, 8, 8, 6, 6, 8, 6, 6) and ink on every frame.
   - Frame selection: loop steps every `ticks_per_frame` and wraps; random never repeats a frame (39 uids x 600 steps) and reaches every frame; the same ticks give the same frame with the wall clock patched to jump; the charge easing advances 0 or 1 frame a tick, speeds up, and its total is within 1 of a numeric integral of 1 / ticks-a-frame (ball 120 ticks, node 90).
   - Look pick: stable per drifter over ticks; all pool members of UFO, planet and island reached; 12 installs gave different pick lists.
   - Placement (alpha >= 128 counts as covered): fireball head fully covered, both sizes, both ways, all frames (tail has ink on every pixel); planet r32 and coin 12 x 10 box covered on every frame; island drawn pixels equal its hitbox pixels exactly for all 8 variant x invert cases, all alpha 255, equal to a centered crop of a ground, never flipped; ring draws nothing outside r64 and fills the circle; every chain arc and node covered while firing, all 7 layouts, both ways; UFO frame rows equal a strip frame at the spec anchor and cover disc and dome as well as the picked stills (379 and 424 of 508 pixels, measured by QA on the stills; frames give 380 to 389 and 424 to 425).
   - Charge and fire looks follow core: with solid-color strips, no fire strip or ring while the ball charges, no charge strip while it fires, no rays while it fires, nothing of the fire look, rays or outline when core says the ball is off screen, the same for chain nodes and arcs (including a three-node chain with one arc firing).
   - Caches: after `install_drifter_looks`, 7,200 draws of every drifter, variant, invert, uid, position and tick add 0 entries to either cache, and 5,400 dimmed draws of the five drifters the run can hit, plus the coin, add 0.
   - `cycle_tick()` equals `ticks_in_phase % (charge + fire)` over three cycles (ball at Level 1 and 8, chain at Level 1), charge and fire boundaries sit where the old method put them, rays 1 + c x 4 // charge.
   - Inline edge runs (not saved): `field_ring_radius_step` 1, 2, 3, 5, 7, 13 and `dim_steps` 1, 2, 3, 16, 64 add no cache entries after install; every view at scale 0.5, 0.75 and 1.5 draws (the island refuses, as documented); brightness 0, 1, 1.7 and -0.3 draw. A draw gives the same pixels before and after other draws (the planet rings change alpha per blit).
   - Mutation checks (scratch copy, not the repo): a 1 px UFO anchor shift, a lost fireball mirror, an oversized ring, a swapped charge/fire condition, a constant look pick, no salt, parity-free random order, a no-easing charge, a wrong island crop and a node-look swap each fail a test.
4. **Assumptions:**
   - "Opaque" in the placement tests means alpha >= 128; the fireball tail only needs ink (alpha > 0), because its trail fades on purpose (art_canvas: the trail may reach past the tail hitbox). 13 to 16 of its 171 tail pixels sit under 128.
   - The request asks for the UFO to be "not worse than the still's coverage the report states". The report states no number, so the stills' own coverage was measured on `staging/assets/sprites/ufo-d2-r2.png` and `ufo-d3-r3.png` and written in the test (`UFO_STILL_COVERAGE`).
   - The two caches have no public count, so the cache tests read `Sprites._images` and `Sprites._built`. If those names change the test fails loudly.
   - The dimmed-cache test leaves the island out: its touch is a block, so the run never dims it (see Observations).
   - Owner of `game/app/` is the Integration Engineer by the roster, though the UI Developer wrote the file in this direct edit. The main session routes the fix.
5. **Documentation differences:** None against the GDD or `CLAUDE.md`. Missing artifacts to note: no contract, no task file, no review report (direct edit, as the main session said). Two items outside the feature, for the main session: `game/tuning/drifters/chain_lightning.json` has `charge_ticks` 90 and `fire_ticks` 80 while `drifters/03-chain-lightning.md` lists 120 and 120 (marked guess; present at HEAD); and `game/tuning/debug_spawns.json` shows as changed in `git diff` (472 lines) and is not in the implementation report's file list. Neither affects a test here.
6. **Next:** The main session routes B1 and B2 (one file, `game/app/drifter_looks_tuning.py`, owner by the roster: Integration Engineer; written by the UI Developer in this direct edit). Re-test then runs the 4 failing tests and `check.sh`. Hand to the Integration Engineer for the browser only after a pass. Open for the browser run: planet ring memory (2.3 MB) and the 2 px ring jump at `field_ring_radius_step` 2, both flagged by the implementer.
7. **Status:** done.

## Observations (not bugs)
- `floating_island_view.warm` warms full brightness only, while every other view also warms the re-hit level. A dimmed island builds 16 new image entries on first draw. The run never dims an island (`run.py:567` sets the cooldown on a HIT only; the island's touch is BLOCK), so nothing in the game reaches it. If an island ever takes a hit, loop `sprites.warm_levels` in `warm`.
- A strip size error names the PNG, the size and `drifter_looks.json`, not the rule's field name (for example `ufo.looks[0]`). It is enough to find the strip.
- The UFO art sits 1 px low of the best fit (shifting the frame up 1 px covers about 5 more hitbox pixels). The picked stills have the same offset, so it is the art, not the view.
- The planet ring jumps 2 px about every other tick at the default step. Cannot judge motion headless; flagged by the implementer for the browser.
- Whole-pixel drawing leaves the electric ring up to 0.71 px past r64 when the ball's center is fractional (the hitbox is at the float center). On a whole-pixel center it is inside r64 on every pixel. Arc ends carry the 0.6 px the report names.
- The new tests read every pixel and add about 30 s to `check.sh` (was about 30 s, now about 65 s). Draws are on small surfaces already.

## Bugs
- **B1** `game/app/drifter_looks_tuning.py:104` (`_convert`, the `int` branch), Integration Engineer by the roster (UI Developer wrote it). A color channel of 0 is refused. Reproduce: `SDL_VIDEODRIVER=dummy python -c "import json,tempfile,pathlib;import app.drifter_looks_tuning as m;d=json.load(open('tuning/drifter_looks.json'));d['planet']['field_ring_color']=[0,120,255];t=pathlib.Path(tempfile.mkdtemp());(t/'drifter_looks.json').write_text(json.dumps(d));m.TUNING_DIR=t;m.load_drifter_looks()"` from `game/`, or `game/tests/check.sh ui -k color_channel_of_zero`. Expected: loads, since a color is RGB 0 to 255 (`looks.py` fields `field_ring_color`, `ray_color`, `outline_color` say "RGB 0..255", and the loader's own error says "channels must be 0 to 255"). Actual: `ValueError: tuning/drifter_looks.json: planet.field_ring_color[0] must be an integer >= 1`. Any color with a 0 channel (pure cyan (0, 255, 255), black, (255, 0, 255)) cannot be used; the shipped colors have none, so the game runs today. Source: `ui/drifters/looks.py` field docstrings; the loader's own message. Proposed fix: in `_convert`, read the minimum from the field name, not the whole path: `minimum = 0 if path.split("[")[0] in _ZERO_OK or path.split("[")[0].endswith("color") else 1`. The existing channel check below it still refuses values over 255, and the three failing tests `test_a_color_channel_of_zero_loads` pass.
- **B2** `game/app/drifter_looks_tuning.py:34` and `:104`, same owner. `_ZERO_OK = {"fireball.art_head_center"}` never matches: the loader checks `path in _ZERO_OK` with the element path `fireball.art_head_center[0]`, so the exemption is dead and `[0, 0]` is refused. Reproduce: `check.sh ui -k head_center_of_zero`. Expected: loads, the set exists to allow it. Actual: `ValueError: tuning/drifter_looks.json: fireball.art_head_center[0] must be an integer >= 1`. Source: the loader's own `_ZERO_OK` docstring ("Integer fields that may be 0"); `looks.py` `art_head_center` (px from the top-left of a frame). Proposed fix: the same one-line change as B1 (strip the `[n]` from the path before looking it up). If the intent changed and a 0 head center is not wanted, delete `_ZERO_OK` and the test `test_a_head_center_of_zero_loads` instead; the implementer or the main session decides.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3413 passed) · ui FAIL (673 passed, 4 failed: `test_a_color_channel_of_zero_loads[value0..value2]`, `test_a_head_center_of_zero_loads`)
QA: fail (ui)

## Round 2 2026-11-05

1. **Task:** Re-test of B1 and B2 after the `## Fix` section of `docs/reports/implementation/ui/drifter-sprites-ui-developer.md`, asked for by the main session.
2. **Delivered:** this section; line 1 set to `Verdict: pass`. No test file changed.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core (3413 passed), ui (677 passed, 0 failed). The 4 tests that failed in round 1 now pass: `test_a_color_channel_of_zero_loads[value0..value2]` and `test_a_head_center_of_zero_loads`. Neighbors of the fix, run inline: a color channel of 0 loads; -1, True and 2.5 in a color still raise (`must be an integer >= 0`); 256 still raises `channels must be 0 to 255`; `art_head_center` [0, 0] and [44, 0] load, [-1, 0] raises; `art_head_width` 0 and `field_ring_width` 0 still raise `>= 1`. The tests for every other field (missing, wrong type, count under 1) still pass.
4. **Assumptions:** `game/tuning/debug_spawns.json` is being edited by the Integration Engineer for its browser run and is not part of this feature; the harness passed with it as it is now.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, browser run. Open for it: planet ring memory (2.3 MB) and the 2 px ring jump at `field_ring_radius_step` 2.
7. **Status:** done.

### Bugs
- **B1** fixed. `_minimum(path)` in `game/app/drifter_looks_tuning.py` gives 0 for a color channel.
- **B2** fixed. The same function strips `[n]` before the `_ZERO_OK` lookup, so the head center may be 0.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3413 passed) · ui PASS (677 passed)
QA: pass

## Round 3 2026-11-05 (meteorite look)

1. **Task:** Verify the meteorite look the Director approved: 4 skins (`meteorite_rock_a..d.png`), the `meteorite` block of `drifter_looks.json`, the rewritten `meteorite_view.py`, `drawn_width` per variant in `game/tuning/drifters/meteorite.json` (26, 36, 52), `Meteorite.drawn_parts()` and `app/drifters/meteorite_tuning.py`. Spec: the `## Meteorite` section of the implementation report and the Director's decision of 2026-11-05 (the art covers at least 88% of the r14 circle at medium, the center r10 fully, no bite deeper than 3 px; the hit circle may poke out of the rock). No contract, task file or review report (direct edit). The decision is not in the GDD yet.
2. **Delivered:**
   - `game/tests/ui/test_drifter_views.py` (synthetic store gets the four skins; meteorite added to the pick, order, cache, dimmed and same-pixels tests; new start-frame, coverage and drawn-box tests)
   - `game/tests/ui/test_drifter_looks_tuning.py` (strip table has the four rocks; meteorite block and `drawn_width` loader tests)
   - `game/tests/core/test_meteorite_drawn_box.py` (new, 16 tests: `drawn_parts()` and rule 12)
   - `game/tests/CONTEXT.md` (the three files described)
3. **Checks:** `game/tests/check.sh` ends `QA: fail (ui)`: env, lint, format, typecheck pass; core 3429 passed; ui 783 passed, 1 failed (`test_the_meteorite_art_covers_the_hit_circle_to_the_directors_limits[big]`, bug B3). What holds:
   - Strips and tuning: the four skins are 8 frames of 36 x 36, 5 ticks a frame, loop; every field of the new block is required (the walk of the file covers `meteorite.*`); an empty `looks` list and `art_hitbox_width` under 1 raise; the shipped `drawn_width` is 26, 36, 52. The loader requires `drawn_width`, refuses a string, bool, null, list, object, 0, negative, NaN and inf, **refuses `drawn_width` below `width`** (27 and 27.99 at width 28 raise `drawn_width must be at least width`), accepts equal or larger, and refuses an unknown variant field. It has no upper bound (100 loads), see Observations.
   - Look pick and frames: all four skins are reached; a rock keeps its skin; frames loop at 5 ticks a frame and wrap; 40 rocks start on at least 4 different frames, and each rock's own frame at tick t is its start frame plus t // 5.
   - Coverage, by variant (alpha >= 128 is covered, a pixel counts when its center is in the circle, 24 uids x 8 frames each, all four skins): the center disc (r10 at medium, scaled by width / 28) is fully covered at all three sizes. The covered share of the hit circle is at least 88% at all three (worst 0.886 small, 0.883 medium, 0.896 big). Deepest bite: small 1.72 px (limit 2.14), medium 2.58 px (limit 3), big **5.02 px (limit 4.29): fails, B3**.
   - Rule 12: `drawn_parts()` is one box of `drawn_width` centered on the rock and never smaller than the footprint (also for a variant with no extra). A rock whose footprint is fully below the floor stays while its drawn box is on screen and is removed when the drawn box touches or passes the floor; the same at both sides; never removed at the top or before it has entered; a rock falling 2 px a tick is dropped 2 ticks (small, medium) or 3 ticks (big) after its footprint clears the floor, as worked out. Every pixel the view draws lies inside the drawn box (to the half pixel of a whole-pixel blit), at all three sizes.
   - Caches: with meteorites in the draw (the full draw and the dimmed draw, which now includes the meteorite because its touch is a hit), no entry is added after install.
4. **Assumptions:** Covered means alpha >= 128, as in the other placement tests. The bite depth is the distance from the circle edge to the deepest uncovered pixel center, divided by width / 28 for small and big ("scaled" as asked). With a lower bar (any ink, alpha > 0) the big rock's deepest bite is 3.68 px, which is 2.57 px at medium scale and would pass. I kept alpha >= 128 so one reading of "covered" is used in every test.
5. **Documentation differences:** The Director's decision (88%, r10, 3 px) is not in the GDD yet; `drifters/01-meteorite.md` still says "the rock filling the hitbox circle" (art_canvas) and `start_y` as the footprint. Pending the main session writing it back. The schema `docs/contracts/schemas/drifter-tuning.schema.json` still describes the meteorite with no own field (the implementer noted it; the Architect's).
6. **Next:** UI Developer (art/view) for B3, or the Director rules whether the big rock's bites are acceptable: if yes, the test's bite check moves to "any ink" (alpha > 0) by a one-line change in `_circle_scan`, which I make only when asked. Re-test then.
7. **Status:** done.

### Observations (not bugs)
- Pop-in at the top: a meteorite starts with its footprint touching the top edge (GDD 01 `start_y`: center y = -width / 2), so its drawn rock, wider than the footprint, shows 3 px (small), 4 px (medium) and 6 px (big) on screen from its first ACTIVE tick (checked on the real classes). The GDD's start rule is stated for the footprint, so this is as specified; if the rock should start fully off screen (07-drifters.md rule 14 read with rule 12), `start_position` should use `drawn_width`.
- `drawn_width` has no upper limit: 100 loads, and a rock that big would stay on screen long after it is gone from view. It also does not check that the art fits: the view test shows the art (26, 36, 51 px) fits the 26, 36 and 52 boxes.
- `docs/contracts/schemas/drifter-tuning.schema.json` is behind the meteorite file (see 5).

### Bugs
- **B3** `game/assets/sprites/meteorite_rock_*.png` scaled by `game/ui/drifters/meteorite_view.py` (`scaled_size`, `smoothscale`), owner UI Developer (art by the art agents). At the big rock the deepest bite is 5.02 px deep at alpha >= 128, over the Director's 3 px scaled to the big rock (4.29 px; 3 x 40 / 28). The 3 px limit is also exceeded unscaled. Reproduce: `game/tests/check.sh ui -k "meteorite_art_covers and big"`. Expected: no bite deeper than 3 px at medium, scaled by width / 28 elsewhere (Director decision 2026-11-05). Actual: small 1.72 px of 2.14 allowed, medium 2.58 of 3, big 5.02 of 4.29 (3.51 px at medium scale). The native strip's deepest bite is 2.58 px at the 28 px circle (rock_b and rock_d), so the extra comes from scaling the 36 px frame up to 51 px: bilinear scaling softens a bite's edge over about 2 px and the half-alpha line moves inward. Source: the Director's decision above. Proposed fix, one of: (a) the Director accepts the big rock as is and the bar is read at any ink (the big rock then measures 3.68 px, inside 4.29); (b) draw a big strip at its own size (51 x 51 frames, so no upscale) and add it as a second strip for the big variant; (c) in `meteorite_view.py` upscale the big rock with a method that keeps the edge sharp (`pygame.transform.scale`, nearest) or sharpen the alpha after `smoothscale`, once at preload. (b) is the cleanest for the look; (a) costs nothing.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3429 passed) · ui FAIL (783 passed, 1 failed: `test_the_meteorite_art_covers_the_hit_circle_to_the_directors_limits[big]`)
QA: fail (ui)

## Round 4 2026-11-05

1. **Task:** Re-test after three inputs: B3 accepted by the main session on the Director's rule; the salt-dependent test; the `## Fix (meteorite start)` section of the implementation report (meteorite starts fully off screen by its drawn size).
2. **Delivered:**
   - `game/tests/ui/test_drifter_views.py` (bite check changed, stores built under a fixed salt)
   - `game/tests/core/test_meteorite_drawn_box.py` (start tests added, 32 tests)
   - `game/tests/CONTEXT.md`
3. **Checks:** `game/tests/check.sh` run twice, both ends `QA: pass`: env, lint, format, typecheck pass; core 3441 passed; ui 784 passed, 0 failed (identical in both runs).
   - B3 test: the bite of the medium rock (native art) is read at alpha >= 128 with the 3 px limit, as before (2.58 px). The scaled small and big rocks are read at visible ink (alpha >= 32) with the limit scaled by width / 28 (small 2.14 px, big 4.29 px); both pass. The 88% coverage and the full r10 centre disc stay at alpha >= 128 and pass at all sizes.
   - Salt: the real and synthetic stores are now built with the global `random` seeded (`SALT_SEED`, state restored afterwards), so `Sprites` draws the same salt on every run. This also covers the other tests that expect every skin of a pool within a few uids (the pick, start-frame and coverage tests). `..._follow_each_strips_order_and_speed_in_game_ticks[METEORITE]` and the whole views file pass on both full runs and on a standalone run.
   - Meteorite start (tests: `test_a_rock_with_no_y_starts_with_its_whole_drawn_box_just_above_the_top_edge`, `test_a_rock_with_no_drawn_width_starts_by_its_footprint_and_a_placed_y_is_kept`): with no `y` the rock starts at y = -drawn_width / 2 (-13, -18, -26) at Levels 1, 4 and 8, x kept, its drawn box's bottom edge on y 0, not partly on screen in WARNING or on its first ACTIVE state, not entered; one px of fall puts it on screen and it enters; the footprint is unchanged; a variant with no drawn width starts by its footprint; a placed y (50, 0, -100, 479.5) is kept.
4. **Assumptions:** None new. The medium rock keeps the half-alpha reading because it is the native art the Director judged.
5. **Documentation differences:** None new. Still pending from round 3: the Director's meteorite limits (88%, r10, 3 px, and now the accepted reading for scaled rocks) are not in the GDD, and `drifter-tuning.schema.json` has no meteorite field.
6. **Next:** Integration Engineer, browser run.
7. **Status:** done.

### Bugs
- **B3** closed, accepted. Reason: the main session, acting on the Director's rule ("it does not matter that the look in a corner is less than the hitbox, if the other side is maintaining the shape"), accepted the big rock's softer bites: scaling softens a bite's edge and moves the half-alpha line, not the rock. The test now reads scaled rocks at visible ink (alpha >= 32) with the limit scaled by size; both pass.
- No new bugs. The Round 3 observation on the meteorite's start is fixed.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3441 passed) · ui PASS (784 passed)
QA: pass (two runs)

## Round 5 2026-11-05 (new meteorite art: 32 frames, 3 ticks a frame)

1. **Task:** Re-test after the main session's change (Director-approved 2026-11-05): `meteorite_rock_a..d.png` are 32 frames of 36 x 36 (1152 x 36 strips), `ticks_per_frame` 3 in `game/tuning/drifter_looks.json`, GDD `drifters/01-meteorite.md` updated, strip table in `test_drifter_looks_tuning.py` updated. Limits unchanged: at least 88% of the r14 circle covered, r10 centre fully covered, no bite deeper than 3 px, the 1 px frame edge clear.
2. **Delivered:**
   - `game/tests/ui/test_drifter_views.py` (coverage test and drawn-box test now walk a whole turn of the rock; stale docstring fixed)
   - `game/tests/CONTEXT.md` (strip counts and the frame walk described)
   - this section. Verdict stays `pass`.
3. **Checks:**
   - `game/tests/check.sh` run twice, both end `QA: pass`: env, lint, format, typecheck pass; core 3441 passed; ui 784 passed, 0 failed (identical in both runs; the run takes about 3 min now).
   - **Tests did not cover all 32 frames.** The coverage test sampled `ticks` 0, 5, ..., 35 for uids 1 to 24: about 8 consecutive frames at 3 ticks a frame per rock, so about a quarter of each skin. The drawn-box test sampled `ticks` 0, 10, 20, 30 (four frames). Nothing else was hard-coded to 8 frames or 5 ticks in the real-strip tests (the strip table already says `(32, 36, 36, 3, "loop")`). Both tests now take uids 1 to 8 (`FRAME_WALK_UIDS`, which reach all four skins under `SALT_SEED`) and step `ticks` from 0 to `count x ticks_per_frame` in steps of `ticks_per_frame`, with count and speed read from the real rule, so each rock shows a whole turn at small, medium and big. The coverage test also asserts that all 4 x 32 (skin, frame) pairs were drawn.
   - Stale wording: the docstring of `test_each_meteorite_starts_its_turn_at_its_own_frame` said "8 frames, 5 ticks each". It now says the synthetic strips have 8 frames and 5 ticks (its `// 5` is the synthetic rule's own and is correct) and that the test reads no number from the real strips.
   - **Independent measurement** (inline script, not saved; every frame of each skin, drawn through the real views at (60, 60), alpha >= 128 covered, a pixel counts when its centre is inside the circle; bite at alpha >= 128 for medium and at alpha >= 32 for the scaled small and big, limit scaled by width / 28, as agreed in round 4). Worst frame per rock per size:

     | size | rock | worst coverage (frame) | deepest bite at medium scale (frame) | r10 centre full |
     |---|---|---|---|---|
     | small | a | 0.896 (20) | 0.54 (30) | yes |
     | small | b | 0.896 (6) | 0.54 (29) | yes |
     | small | c | 0.886 (19) | 1.60 (3) | yes |
     | small | d | 0.899 (27) | 1.13 (27) | yes |
     | medium | a | 0.888 (20) | 1.65 (30) | yes |
     | medium | b | 0.894 (20) | 1.49 (30) | yes |
     | medium | c | 0.888 (3) | 2.40 (3) | yes |
     | medium | d | 0.903 (27) | 1.90 (7) | yes |
     | big | a | 0.916 (20) | 1.87 (14) | yes |
     | big | b | 0.907 (6) | 1.16 (28) | yes |
     | big | c | 0.891 (19) | 2.49 (19) | yes |
     | big | d | 0.914 (7) | 1.63 (23) | yes |

     All 12 cases are over 88% (lowest 0.886, small rock_c frame 19), under 3 px (largest 2.49 px at medium scale, big rock_c) and have a full centre. 32 distinct frames were shown per rock in each case.
   - **Frame edge:** on all 4 x 32 frames, the outer 1 px ring has 0 pixels with any alpha.
   - **Seam:** mean absolute RGBA difference between neighbouring frames. Ordinary steps: a 5.85 to 9.99, b 4.64 to 10.79, c 5.52 to 9.98, d 6.58 to 9.50 (means 7.3 to 8.1). Last frame to first: a 8.20, b 6.75, c 7.40, d 8.14. Each is at the mean of its rock and inside its own step range, so the loop closes smoothly.
   - **Memory** (real `install_drifter_looks`, surfaces counted at width x height x 4 bytes): the meteorite adds 768 images to the scaled and dimmed cache (4 rocks x 32 frames x 3 sizes x 2 brightness levels: full and the re-hit level) = 4.68 MB, against 1.17 MB at 8 frames (+3.5 MB). Whole `_images` cache 1,112 entries, 9.41 MB; `_built` (planet rings, rays, outline, island) 107 entries, 13.11 MB, none of it the meteorite. The raw strips are 4 x 1152 x 36 x 4 = 0.66 MB. Process peak 54 MB at the headless run. Bounded: it is fixed at install (frames x sizes x levels), and 3 sizes x 199 uids x 34 ticks of draws added 0 entries (1,112 before and after). Whether 5 MB is acceptable in pygbag is for the browser run.
4. **Assumptions:** The walk uses `strip_frame` to record which frames were reached; the placement itself is read from drawn pixels. Uids 1 to 8 reach all four skins only under the fixed salt the tests already set, and the test asserts all skins and frames were reached.
5. **Documentation differences:** None new. Still pending from round 3: the Director's meteorite limits (88%, r10, 3 px, and the reading for scaled rocks) are not in the GDD, and `drifter-tuning.schema.json` has no meteorite field.
6. **Next:** Integration Engineer, browser run. Open for it: planet ring memory (2.3 MB), the 2 px ring jump at `field_ring_radius_step` 2, and the meteorite's extra 3.5 MB of scaled frames.
7. **Status:** done.

### Bugs
None open. No new bugs.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3441 passed) · ui PASS (784 passed)
QA: pass (two runs)
