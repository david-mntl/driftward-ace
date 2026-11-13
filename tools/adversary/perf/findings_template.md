# Driftward Ace: performance adversary findings

## Verdict

1. **It does not hold 60 fps on this box, and the browser makes it worse.** Desktop CPython here needs 9.5 ms (tutorial) to 15 ms (L7) at p50 and 12 to 50 ms at p95 per wave; the browser build costs about 2.3 to 2.6 times the desktop frame in the same units (see Method), so a quiet machine would land near 26 to 30 fps at Level 4 and Level 8. Estimate, not a measurement of the Director's hardware.
2. **Worst drops: Level 4 islands** (w11_lvl4_island p95 50 ms, 28% of its frames over 20 ms of tick alone; w10_lvl4_island_lanes p95 29 ms). Cause: the ship resting on an island runs an exact polygon push-out search every tick (P1). Next: Level 6 planet gates (draw p95 20.6 ms, P4), Level 8 and the endless tail satellite wave w4_lvl8_satellite (37 to 40 drifters, p95 22 to 24 ms, P3), Level 7 UFO waves (p95 19 to 20 ms).
3. **A fixed cost sits under everything:** background painting + river, HUD and starfield cost 6 ms a frame with an empty field, 45 to 85% of the draw and about half the frame in the quiet waves (P2). Plus 25 `dataclasses.replace` calls a frame in core (P5).
4. **No degradation over time seen in 4 min of tail with full drawing (2 runs) and 12 min mostly core-only (tailC: tick slope -0.03 ms/min):** tail cost slope is +0.05 and -0.02 ms per minute (noise), all caches stop growing after the first minute, no gen-2 GC after startup (gen0/gen1 max 3.7 ms); memory flattens (lean core-only run: RSS +0.16 MB/min over minutes 5 to 10). I could not run the 20 minutes asked: see Method.
5. **The endless tail plays only three waves** (w3_lvl2_satellite, w4_lvl8_satellite, w6_lvl5_chain_lightning; `pool_ids(8)`), and w4_lvl8_satellite is the heavy one (P3, P9).

## Method and limits (read first)

- The container was heavily oversubscribed by other jobs for the whole session: load average 40 to 60 on 8 cores. A fixed pure-Python loop (3000 iterations, the "canary", recorded every frame) took 1.3 to 1.5 ms here; I expect a normal desktop to need roughly a tenth of that (estimate, not measured). So absolute milliseconds below are inflated and the 8 ms rule flags every wave, even the tutorial. Use them as a ranking and as ratios.
- Timers use thread CPU time (`time.thread_time`), not wall clock, so being descheduled does not count. Each timer call costs about 8 us on this box; with ~25 section timers and 2 per drawn drifter that is about 0.5 ms a frame of overhead inside the numbers.
- "p95n" is p95 corrected to the quiet-machine canary speed (rolling median of the canary). "canary units" is the p50 frame cost divided by the median canary, a machine-independent ratio.
- Wall-clock budget made the 20-minute endless soak impossible (about 20 CPU-minutes of drawing, with the box giving each process 10 to 20% of a core). What ran instead, all with the real frame loop, fake clock, 1 tick per frame, immortal autopilot (the same one as `local/stutter-probe/harness.py`; lives reset to 5 on a hit, 32 hits absorbed in the level runs):
  - Level 1 to Level 8 start as 8 parallel segments (`seg1..seg8`, 19,754 frames; segments 2 to 8 start with the waves jumped to that level, which skips earlier levels' ramp but not their waves). Level 8 ran to the first endless wave.
  - Endless tail: `tailA` + `tailB`, 4 game-minutes each with full drawing (different seeds); `tailC`, 12 game-minutes (first 10 core-only with drawing off, the last two drawn) for drift in core cost and memory.
  - Memory: lean runs `leanA` (10 tail min, core only) and `leanB` (3.7 tail min, drawn) without per-frame recording; RSS, allocated blocks, gc object counts and the size of every cache/container owned by game modules every 600 frames. tracemalloc ran only for 1,300 frames (`tm2`); too short to say more than "satellite pose cache fills".
  - cProfile: first 600 frames of each level (`prof`) and 500 frames of each of the 4 worst waves (`pw4 pw10 pw11 pw15`). cProfile inflates 2 to 3 times; shares are what counts.
- Browser: the pygbag build ran (Chromium headless, build + serve took 16 s), but at 1.1 to 1.5 fps because of the same load (canary median 26 to 32 ms instead of 1.7 ms at its quietest). Only ratios are usable. Two runs of 4 min (`?jump=4`, `?jump=tail`) rather than a continuous run to Level 8, because 15,000 ticks at that rate would take hours; the probe copy starts the waves at that level. Level 8 start was not run in the browser.

## Tables

### Per level, desktop (segments 1 to 8, then the tail from tailA + tailB)

cost = tick ms + draw ms, raw ms on this box. Counts include the rest gaps between waves.

{{LEVELS}}

Endless tail (tailA + tailB, 28,802 frames, 4 min each):

{{TAIL_LEVELS}}

### Per wave (active frames only)

{{WAVES}}

Tail waves (only these three exist in the tail):

{{TAIL_WAVES}}

Frames over budget per level (raw cost on this box): L1 3%, L2 0%, L3 3%, **L4 40% (>33 ms: 13.9%, >50 ms: 2.8%)**, L5 1%, **L6 33%**, **L7 32%**, L8 10% over 16.7 ms.

### Worst 15 frames (levels run)

{{WORST}}

### Worst 15 frames (tail)

{{TAIL_WORST}}

### Where the time goes, per level (mean ms per frame)

{{PARTS}}

### Drifter types

{{TYPES}}

{{MARG}}

### Endless tail trend and memory

{{TREND}}

### Browser (probed pygbag build, jump to the level; machine at 1.1 to 1.5 fps, read the ratios only)

```
{{BROWSER}}
```

Browser vs desktop in canary units (p50 frame work / median canary): Level 4 w10 22.7 vs 9.9 desktop (L4 all), endless tail 19.8 vs 8.1. Ratio 2.3 to 2.4. At the canary's quietest in the browser (1.7 ms) that is about 39 ms for Level 4 and 34 ms in the tail per frame (26 to 29 fps). The worst browser frame (1,826 ms at canary 31) is 59 canary units, about 100 ms on a quiet box.

## Findings

## P1: Ship resting on a floating island makes the tick 5 to 7 times slower
Severity: critical (visible lag; this is the Level 4 drop)
Confidence: measured (desktop, cProfile); browser effect estimated from the 2.3x ratio
Where: Level 4 w11_lvl4_island (tick p50 7.2 ms, p95 42.7, max 53 ms; 262 of 923 frames over 20 ms) and w10_lvl4_island_lanes (p95 21.7, max 35). Code: `core/ship.py:block_ship` -> `_shortest_way_out` -> `core/collision.py:exit_distance` -> `_blocked_span` / `_projection` / `_unit_normals` / `_edges`. Frames with 6 islands in view cost 2.4 ms of tick per island on average (OLS), versus 0.14 to 0.41 ms for every other drifter.
Numbers: in w11, `_shortest_way_out` is 56% of the wave's profiled time (73 calls in 500 frames, 8 directions each, 8,160 `_blocked_span` calls, 168,000 `_projection` calls, 26,500 `_unit_normals`). 40% of all Level 4 frames exceed 16.7 ms and 13.9% exceed 33 ms on desktop; PR #31 removed the every-tick geometry for hits but this contact path still runs it every tick the ship is pushed.
Repro: `cd tools/adversary/perf && python soak.py --label pw11 --lean --nodraw-until-profile --profile-frames 500 --jump 4 --jump-slot 1 --profile-waves w11_lvl4_island --max-frames 800 && python profrep.py ../out/perf/prof_pw11` (top of its report below). Table: `python soak.py --label seg4 --jump 4 --stop-level 4 && python analyze.py seg4`.
Idea for a fix: the islands' polygons are static shapes, so cache their edges and unit normals once instead of rebuilding them in every `exit_distance` call, and try last tick's push direction first (or skip the search while the ship is still touching the same island with the same ground motion).

Top functions, w11_lvl4_island (own and cumulative, core vs drawing):

```
{{PW11}}
```

w10_lvl4_island_lanes shows the same chain (`_shortest_way_out` 55% of its time):

```
{{PW10}}
```

## P2: A fixed draw cost of about 6 ms per frame, before any drifter
Severity: major
Confidence: measured
Where: every wave. `ui/background_view.py:draw_background` 4.2 ms (`_draw_painting` cross-fade 2.65, `_draw_river` 1.08, planets and swirl about 0.5), `ui/hud.py:HudView.draw` 1.2 ms, `ui/starfield.py:draw_starfield` 0.5 ms. OLS says the empty-field draw is 6.05 ms and the empty-field tick 1.2 ms.
Numbers: tutorial wave w0: p50 9.5 ms total, of which about 6 ms is this. At the browser's 2.3 times factor the fixed part alone is about 14 ms of the 16.7 ms budget on a quiet box. `Surface.blit` is the top own-time function in every level's cProfile (25,000 to 49,000 calls per 600 frames, 15 to 20% of profiled time).
Repro: `python analyze.py levels` (table "Mean ms per frame by part") or `python soak.py --label x --lean --nodraw-until-profile --sweep 600` then `python profrep.py ../out/perf/prof_x`.
Idea for a fix: bake the painting and river into one pre-blended frame set (or update them every second frame), and draw the HUD panel from a cached surface that only redraws the changed fields.

## P3: Satellite waves, and with them the whole endless tail
Severity: major
Confidence: measured
Where: w4_lvl8_satellite (Level 8 slot 1, and 7,490 of the 27,000 tail frames): 37 to 40 drifters, p50 15.2, p95 24.0, max 28.7 ms desktop. Code: `core/run.py:_apply_graze` -> `core/graze.py:check_grazes` -> `_check_one` -> `_touches_ship` -> `satellite.py:current_hitbox` (15,600 calls per 500 frames, about 31 a frame) -> `collision.py:place_hitbox` / `_move_shape` / `_bounds` / `hitboxes_overlap`.
Numbers: graze plus hit checks are about 33% of the wave's profiled time. The two other tail waves (w3 satellite, w6 chain lightning) sit at p95 15 ms. Tick marginal cost per satellite is 0.31 ms, per UFO 0.34, per electric ball 0.41 (OLS).
Repro: `python soak.py --label pw4 --lean --nodraw-until-profile --profile-frames 500 --jump 8 --jump-slot 0 --profile-waves w4_lvl8_satellite --max-frames 800 && python profrep.py ../out/perf/prof_pw4`; tail table: `python soak.py --label tailA --seed 2 --jump tail --tail-minutes 4 && python analyze.py tailA`.
Idea for a fix: compute each drifter's placed hitbox once per tick and share it between the graze and hit tests (the same shapes are moved and bounded several times per tick), and reject on the bounding box before building the exact shape.

```
{{PW4}}
```

## P4: Planet draw cost, Level 6 planet gates
Severity: major
Confidence: measured
Where: w15_lvl6_planet_gates draw p50 13.4, p95 20.6, max 24.9 ms (every other wave draws at 7 to 9.5 ms). `ui/drifters/planet_view.py:render_planet` -> `_blit_ring`; planets cost 0.59 ms per planet on screen (OLS), 4 times the next type; Level 6 mean drifter draw 4.6 ms a frame versus 0.5 to 2.3 elsewhere.
Numbers: 33% of Level 6 frames are over 16.7 ms on desktop; planet draw is mostly blits (`blit` 17 s own of 73 s profiled in 500 frames).
Repro: `python soak.py --label pw15 --lean --nodraw-until-profile --profile-frames 500 --jump 6 --jump-slot 1 --profile-waves w15_lvl6_planet_gates --max-frames 800 && python profrep.py ../out/perf/prof_pw15`
Idea for a fix: pre-render each planet's ring stack once per size and blit one surface per planet.

```
{{PW15}}
```

## P5: `dataclasses.replace` in core costs 6 to 9% of every frame
Severity: minor
Confidence: measured (cProfile shares)
Where: `core/run.py` (and ship, drifters, waves) frozen dataclasses: 10,000 to 22,500 `replace` calls per 600 frames (17 to 38 a frame), second-largest own-time entry in every level's profile (5 to 14 s of 92 to 200 s profiled).
Numbers: 6% of profiled own time at Level 1, 8% at Level 3, 9% at Level 8 (cumulative share is larger).
Repro: `python soak.py --label x --lean --nodraw-until-profile --sweep 600` then `python profrep.py ../out/perf/prof_x` (file `L8.prof` section).
Idea for a fix: build the next `Run` once per tick from local variables (one `Run(...)` call) instead of chaining `replace` steps.

Level sweep profile (first 600 frames of each level; top own-time entries per level):

```
{{SWEEP}}
```

## P6: Chain lightning and electric balls are the dearest small drifters
Severity: minor
Confidence: measured
Where: `ui/drifters/chain_lightning_view.py` draws 0.27 ms per drifter (mean 1.39 ms a frame when present, 5,564 frames); electric ball view 0.15 ms and its tick 0.41 ms each. Meteorites, satellites, fireballs and coins draw at 0.07 to 0.08 ms each.
Numbers: Level 5 mean drifter draw 1.58 ms, p95 total 15.3 ms: fine alone, it adds to P2.
Repro: `python analyze.py levels` (table "Drifter draw cost by type").
Idea for a fix: cache the bolt segments per phase like the other views do.

## P7: First-use spikes in popup and HUD text
Severity: minor
Confidence: measured
Where: `ui/popup_view.py:_popup_surface` (first render of each points value: 5.6 to 6.6 ms, 8 frames in 19,700) and `HudView` number caches (`TEXT_CACHE_SIZE = 8`; 6 to 7.7 ms spikes in `hud.draw`, 2 frames over 3 times the median). Both are single frames, below 8 ms on desktop; in the browser about 2.3 times that.
Numbers: popup `pop` max 6.6 ms; `hud` max 7.7 ms; ring first draw 0.5 ms.
Repro: `python analyze.py levels` and read the part spikes, or search `p:pop` > 3 in `out/perf/soak_levels.npz`.
Idea for a fix: warm the popup and HUD number caches for the known points values at load, before the freeze.

## P8: Memory and GC are healthy
Severity: info
Confidence: measured (10 min core-only lean run, 3.7 min drawn lean run, 12 min recorded tail); tracemalloc only 1,300 frames
Where: whole run. After startup there is no gen-2 collection; gen0 max 3.7 ms, gen1 max 3.7 ms (30 to 44 collections per 2,000 to 4,000 frames). The startup gen-2 pair (the freeze) costs about 28 ms each and happens before the first frame.
Numbers: in the lean run (`leanA`, no per-frame recording, 36,051 frames, 10 tail minutes, core only) RSS goes 86.5 -> 89.1 (1.7 min) -> 90.4 (5 min) -> 91.2 MB (10 min): the last 5 minutes add 0.8 MB (0.16 MB/min), and allocated blocks flatten (172.9k at 6.7 min, 175.4k at 10 min). Drawn lean run (`leanB`, 3.7 min): 86.6 -> 91.6 MB. Caches (`satellite._pose_offsets` 44 entries, `graze_view._ring_image` 15, `_popup_surface` 3, HUD number caches) stop growing within the first minute; the container census is flat at 1,512 items from minute 1 to 10. The recorded runs (`tailA..C`) show a steady +0.7 MB/min in "RSS minus arrays"; that is my per-frame recording arrays (63 arrays) and not the game, because the lean run flattens.
Repro: `python soak.py --label leanA --seed 2 --jump tail --lean --nodraw-tail-minutes 99 --tail-minutes 10` then read `out/perf/soak_leanA_meta.json` samples (rss_kb, blocks, census).
Idea for a fix: none needed; the satellite and popup caches are bounded by their key spaces, but they have no size cap if a new key space is added.

## P9: The endless tail has a 3-wave pool, one of them the heaviest
Severity: info
Confidence: measured
Where: `core/waves.py:pick_pool_wave`; `WaveBook.pool_ids(8)` returns only w3_lvl2_satellite, w4_lvl8_satellite and w6_lvl5_chain_lightning, so Level 8's 6 random slots and the whole tail draw from these three (no immediate repeat). Tail cost is therefore bounded and repeats: p50 12.3, p95 21.4, p99 24.3, max 28.7 ms; peak 40 drifters.
Numbers: w4 is 27% of tail frames and has the p95 24.0; w6 and w3 p95 about 15.
Repro: `python -c "import sys; sys.path.insert(0,'tools/adversary'); import simkit; print(simkit.load_kit().book.pool_ids(8))"`
Idea for a fix: not a performance fix; adding waves to the pool (a design call) also spreads the load.

## P10: Browser run could not give absolute numbers
Severity: info
Confidence: measured (ratios), unsure (absolute)
Where: the pygbag build does run in this container (Chromium headless, `?jump=` probe). Under load it ran at 1.1 to 1.5 fps with a median canary of 26 to 32 ms.
Numbers: frame work in canary units is 2.3 to 2.4 times the desktop figure at Level 4 and in the tail; at the canary's quietest in the browser (1.7 ms, the same as desktop CPython at its quietest) that gives about 39 ms at Level 4 and 34 ms in the tail, i.e. 26 to 29 fps, and about 60 to 100 ms for contact-with-island frames. In the browser the fixed draw alone (bg 130 to 250 ms, hud 76 to 320 ms in the worst frames at canary 30) dominates.
Repro: `cd tools/adversary/perf && ./start-probe.sh && node drive.js "?jump=4" 240 ../out/perf/browser/jump_4.json && python report_browser.py ../out/perf/browser/jump_4.json; kill "$(cat server.pid)"`
Idea for a fix: rerun both browser jumps (`?jump=4`, `?jump=8`, `?jump=tail`) on a quiet machine before and after P1 to P4 are fixed; that is the number that matters.

{{EXTRA}}
