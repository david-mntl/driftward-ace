Verdict: ship
Created by: scope-guardian
Feature: DRA-76 Wave system
Parent: none

## Request
"New feature to scope: **Wave system** (the first part of the wave phase). The Director already decided the points below in a design discussion. Treat them as input, not as open questions. Check them against the pillars and the GDD, and flag anything that conflicts.

Goal: Replace the debug-only spawn list with real waves. (however the debug-only spawn list, should not be deleted. It should be converted into a debug mode) A normal run plays Wave 0, then each level's playlist, level after level, until game over. The Director can play it in the browser. With that said debug mode should be possible to be started with normal waves too.

Decided:
- Level goes up when its playlist ends. This fills DF-05: a level starts where the previous level's playlist ends. Levels are no longer set by meters.
- Playlist per level: an ordered list of fixed waves, then `random_count` random waves. Counts differ per level (e.g. L1: 3 fixed, L2: 8, L4: 5). 0 random is allowed. After Level 8, random waves forever.
- Random waves: each authored wave is flagged `fixed` or `pool`. A random slot picks from `pool` waves whose `min_level` ≤ the current level, never the same wave twice in a row. This answers WV-01 and WV-02. Generated waves stay out of scope (stretch goal, later).
- Wave length is a scroll distance in world px, not seconds. Triggers are by distance, so a wave keeps its layout at every level and just arrives faster. 30 s at L1 ≈ 1980 px.
- Coordinates are relative to the wave start (proposed answer to WV-04).
- Seam (WV-06): in a wave's first and last 120 px, none of that wave's hazards are on screen.
- Rest gap (DF-02): kept as a separate pause between waves that shrinks per level (the GDD's Rest gap × row). Value will be 0 until it gets modified. For now remains 0.
- Wave 0: meteorites are the only hazard, plus a few coins. Same every run, always first.
- Drifter values stay shared per type (`game/tuning/drifters/`). No per-wave or per-placement value overrides in this feature.
- The wave and playlist schemas belong to the Architect.

In scope: Wave schema and playlist schema. Game-side wave loader, wave clock and playlist runner, including the remix picker, seam and rest gap. Wave 0 plus 2 Level-1 waves as placeholder content, so the Director can play the flow. Debug overlay: show the current wave id and level.

Out of scope: `wave_check` and the wave editor. Both are Director-owned dev tools in `tools/`, built after this feature, outside the pipeline. Generated waves. Two-wave editing. Per-wave drifter values.

Done when: In the browser, a normal run plays Wave 0 → the Level 1 playlist → the next level, and the debug overlay shows the wave id and level changing.

Make decisions for me and tell me which decisions where made. Let me know when to trigger the architect"

## Feature
A normal run is now made of waves. A wave is a hand-authored group of drifters, each placed at a scroll distance from the wave's start. The wave plays as the world scrolls past.

Every run opens with Wave 0: meteorites and a few coins, the same every run. Then the Level 1 playlist plays: its fixed waves in order, then its random waves. When the last wave of a level's playlist ends, the level goes up by one. The next level's playlist plays at the new level's speeds. After Level 8's playlist, random waves play forever at Level 8.

A random wave is picked from the pool waves allowed at the current level. It is never the wave that just played. Picks differ from run to run.

Between two waves there is a rest gap. It is 0 for now. A wave may add an extra wait after itself, so a hard wave can give the player time to recover. The world keeps scrolling through the gap.

When the level goes up, the scroll gets faster, and drifters that appear from then on use the new level's hazard speed and Timer ×. Drifters already on screen keep their values.

A run ends at game over, as today. Retry starts a fresh run: Wave 0, Level 1, new random picks.

Debug mode can play either the normal waves or the test spawn list, one or the other. The debug overlay shows the current wave id and the level.

## Limits
In:
- Wave format and playlist format. The Architect writes both schemas.
- A wave has an id, a length in scroll px, a flag `fixed` or `pool`, and, for a pool wave, the lowest level it may play at (`min_level`). Each placement has a trigger distance from the wave's start, plus the placement fields drifters already have: drifter type, position, variant, `invert`, specialty switch and `as_level` (07-drifters.md, rule 13; 08-difficulty.md, rule 3). No `speed` field: that stays a debug-only test field (DRA-39).
- A playlist per level, Levels 1 to 8: an ordered list of fixed waves, then `random_count` (0 or more). A fixed wave may appear in more than one level's playlist.
- Loading the wave and playlist files once at startup, in both modes, and refusing bad files with an error that names the file and the problem (the error screen, as for tuning files). Refused at load: a schema error, an unknown drifter type or variant, a playlist naming a wave that doesn't exist, a level with `random_count` > 0 and no pool wave allowed at that level, no pool wave allowed at Level 8, and a hazard triggered inside the wave's first 120 px.
- The wave clock: counts scroll px into the current wave. Spawns each placement when its trigger distance is reached. Ends the wave at its length.
- The playlist runner: Wave 0, then each level's playlist, level by level, then pool waves forever at Level 8.
- The random picker: pool waves with `min_level` ≤ the current level, never the wave that just played. If only one wave is allowed, it plays again. New picks every run, not seeded.
- The level rises the tick the last wave of its playlist ends. Wave 0 plays at Level 1, before the Level 1 playlist. The level never goes past 8.
- The scroll speed follows the level (03-world-and-camera.md, rule 4; 08-difficulty.md, Scroll speed ×). Hazard speed × and Timer × are read at spawn from the run's level, as today.
- The rest gap: a pause between every two waves, `rest_gap_base` × the Rest gap × of the level current when the gap starts, plus the ending wave's extra rest. `rest_gap_base` is 0 ticks for now. The scroll and distance keep going during it.
- Extra rest per wave: each wave may set an extra wait, in ticks, that adds to the rest gap after it. Optional, 0 when left out. It never scales with level. It lets a hard wave give the player time before the next one. Wave 0 may set it too.
- Debug mode: the debug spawn file chooses what plays, the normal waves or the test spawn list. Left out, the test spawn list plays, so today's file keeps working. The spawn list is kept as it is, with its modes and loop.
- Debug overlay: two more lines under `vy`: `wave <id>` and `level <n>`. During a rest gap the wave line reads `wave rest`. With the spawn list playing it reads `wave none`, and the level stays 1.
- Placeholder content, 3 waves and 1 playlist file (see Values needed), written to the Architect's schemas.
- Tests for the loader, the wave clock, the picker, the level rise, the rest gap and the scroll speed per level, with test-only wave files.

Out:
- `wave_check` and the wave editor (Director-owned dev tools, later).
- Generated waves. Two-wave editing. Per-wave or per-placement drifter values.
- Tier checks (DF-01 is TBD). `min_level` is set by hand for now.
- Lava walls and every drifter not built yet.
- The level on the HUD (10-ui.md, rule 2). Debug overlay only in this feature.
- Real content: final Wave 0 (WV-05), real playlists, the wave count (WV-03).
- Starting a debug run at a chosen level or wave. A good next feature for testing later levels; not in this one.
- Any change to drifter behavior or values.

## Player sees
Open the game with `debug=1` and the debug spawn file set to waves. The overlay reads `wave wave_0` and `level 1`. Meteorites fall with a few coins among them. After about 20 s it reads `wave l1_a`, then `wave l1_b`. About 60 s in it reads `level 2`, `wave l1_a` again, and the stars visibly speed up.

## Fit
- Pillar 1, Master the drift: fits. Fixed waves can be learned. Random picks keep the player reading the screen instead of reciting a run. Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: fits. Entry warnings don't change and never shorten with level (07-drifters.md, rule 9). Seams keep 240 px of clear scroll between two waves, so random order never stacks two waves on each other. Risk: without `wave_check`, a placeholder wave could place an unfair spot. Covered by hand checks and the Director's playtest, see "Provisional waves" below.
- Pillar 3, Risk brings reward: fits. Wave 0 coins sit within `coin_near_max` of a meteorite (09-waves.md, rule 6), so the first wave already pays for risk.
- Locked decision 2, scroll speed set by the level: fits. This feature makes the scroll speed follow the level.
- Locked decision 7, Wave 0 is "meteorites-only": conflicts as written. See Objection 1.
- Out of scope, procedural levels: fits. The picker only chooses among hand-authored waves. Generated waves are out of this feature.
- Out of scope, wave editor: not touched by this feature. Flag for later: 01-vision.md lists "wave editor" as out of scope. A Director-only dev tool in `tools/` may still be fine, but the line should say which kind of editor it rules out.
- Stretch goal "generated waves" (Director, later) would conflict with "procedural levels" on the out-of-scope list. Not part of this feature. Flag for later.
- 08-difficulty.md, rule 1 (level from meters) and the Starts at row: replaced by this feature. Not a locked decision. GDD change G2.
- 08-difficulty.md, rule 4 (Timer × scales "spawn times inside a wave"): conflicts with distance triggers. See Objection 2.
- 08-difficulty.md, DF-04 (level change during a wave): no longer happens. The level only rises between waves.
- 09-waves.md, `seam_clear` 120 px "at each seam between waves": the Director's rule clears 120 px at each end of every wave, so two waves meet with 240 px of clear scroll. That is about 3.6 s at Level 1 and 2.1 s at Level 8. It is the safe choice when any pool wave can follow any other, so it stays. GDD change G3.
- 09-waves.md, rule 1 and 03-world-and-camera.md, rule 1 ("wave files use world coordinates, y up"): the Director's answer to WV-04 is relative to the wave's start. The Architect maps it in the schema. GDD change G3 and G4.
- `docs/crew/roster.md`: wave files belong in `game/waves/` (Wave Designer), not `game/tuning/`. The placeholder waves and playlist go to `game/waves/` unless the Architect's contract says otherwise.
- `CLAUDE.md`, "Waves must pass `wave_check` before they count as done": `wave_check` won't exist yet. See "Provisional waves".
- Overlap with shipped features: none. Builds on DRA-13 (scroll), DRA-29 and DRA-39 (spawner, debug spawn list, levels table), DRA-62 (coin).

Provisional waves (proposed by guardian):
- Each placeholder wave gets a critic report in `docs/reports/waves/<wave-id>.md` with line 1 `Verdict: provisional`. It lists which `wave_check` rules were checked by hand (gap ≥ 80 px, seams, coins within 96 px of a hazard, no hazard on the ship at (320, 240)) and which weren't (the bot path, rule 7.3).
- Nothing in the wave file marks it provisional. No extra schema field to drop later.
- The Director's playtest is the second check. Designer and critic are the same session here, so it is not an independent review.
- Once `wave_check` exists, every provisional wave must pass it before the MVP ships. GDD change G3 adds this as an edge case. The Director may also add a line to `CLAUDE.md`.
- Who writes them: the main session, acting as Wave Designer and Wave Critic by the Director's leave, after the Architect's design run and before integration. Same precedent as the tuning files in DRA-29.

GDD changes for the Director to approve (only the Director edits `docs/design/`):
- G1, 01-vision.md, Locked decision 7: "Every run opens with the same fixed Wave 0. Its only hazard is the meteorite; it may also hold coins." Same wording in 09-waves.md rule 3, 14-glossary.md (Wave 0) and drifters/01-meteorite.md Summary ("Wave 0 uses only meteorites" → "the only hazard in Wave 0").
- G2, 08-difficulty.md: Summary, "Level rises with distance flown" → "Level rises when the level's playlist ends." Replace the "Starts at (m)" row with "Playlist: fixed waves, then `random_count`" (values TBD, new DF-06). Rule 1: "Level 1 starts with the run. Each level ends when its playlist's last wave ends; the next level starts on that tick. After Level 8's playlist the level stays 8 and pool waves play forever." Rule 4: drop "spawn times inside a wave"; add "Spawn spacing inside a wave follows the scroll speed, since triggers are distances ([09-waves.md](09-waves.md))." `rest_gap_base` 0 ticks, guess. Rule 6: "Rest gap × multiplies `rest_gap_base`. A wave's extra rest is added after that and never scales ([09-waves.md](09-waves.md))." Edge cases: DF-04 resolved (the level never changes inside a wave); DF-03 resolved ("Cap" = no level past 8, Level 8 values forever); DF-05 resolved.
- G3, 09-waves.md: rule 1, a placement is a trigger distance from the wave's start plus a spawn spot; the schema maps it. New rule: a wave may set an extra rest, in ticks, added to the rest gap after it (0 when left out, never scaled by level). Rule 2 (WV-04): relative to the wave's start. New rule: each wave sets its length in scroll px. New rule: each wave is `fixed` or `pool`; a pool wave sets its `min_level`. Rule 4 (WV-01, WV-02): Wave 0, then each level's playlist (fixed waves in order, then `random_count` pool picks with `min_level` ≤ the level, never the wave that just played; if only one is allowed, it repeats), then pool picks forever at Level 8. Rule 7.4 and `seam_clear` (WV-06): "In a wave's first and last `seam_clear` px of scroll, none of its hazards is on screen. An entry warning counts as on screen." New edge case: "Until `wave_check` exists, a wave checked by hand and playtested by the Director is provisional. Every provisional wave must pass `wave_check` before the MVP ships."
- G4, 03-world-and-camera.md, rule 1: "Wave files use world coordinates" → "Wave placements are relative to the wave's start ([09-waves.md](09-waves.md))."
- G5, 10-ui.md, `debug_overlay` and `debug_overlay_layout`: add `wave <id>` and `level <n>` as lines 5 and 6. Add: "In debug mode the test spawn file chooses the normal waves or the test spawn list."
- G6, 14-glossary.md: add Playlist, Fixed wave, Pool wave.
- G7, 90-open-questions.md: delete WV-01, WV-02, WV-04, WV-06, DF-03, DF-04, DF-05. Keep DF-01, DF-02 (real rest gap value; 0 is a guess), WV-03, WV-05 (final Wave 0; the placeholder is not the answer). Add DF-06: "`random_count` and the fixed waves for each level's playlist."
- G8, 91-decision-log.md: one row each for: level rises at playlist end (replaces row 26 and 08 rule 1); playlists and the pool picker; wave length in px with distance triggers, spawn spacing follows the scroll (replaces "spawn times inside a wave" in 08 rule 4); placements relative to the wave start; seam meaning; rest gap 0 (guess); extra rest per wave; Wave 0 coins (clarifies Locked decision 7); the Level 8 cap; drifter values shared per type, no per-wave overrides; provisional waves until `wave_check`; debug mode plays waves or the spawn list.
- G9, optional: 13-scope-and-schedule.md, week 2 says "Wave loader and wave_check". `wave_check` now comes after, as a Director tool. 01-vision.md, Out of scope: say whether "wave editor" means a player-facing editor.

## Values needed
From the GDD:
- `seam_clear` 120 px: 09-waves.md, locked. Applied at each end of each wave (see Fit).
- Scroll speed ×, hazard speed ×, Rest gap × per level: 08-difficulty.md, locked. Timer ×: guess.
- `scroll_base` 1.1 px/tick: 03-world-and-camera.md, guess.
- `coin_near_max` 3 × ship_w (96 px): 09-waves.md, guess. Used by hand checks.
- `gap_min` 2.5 × ship_w (80 px): 09-waves.md, locked. Used by hand checks.
- Level count 8: 08-difficulty.md, locked.

Not in GDD:
- `rest_gap_base` 0 ticks. Director in chat ("Value will be 0 until it gets modified"). Not in GDD (DF-02 is TBD).
- Wave length example: 30 s at Level 1 = 1980 px. Director in chat. Not in GDD.
- Level cap: the level stays 8 after Level 8's playlist. Director in chat ("After Level 8, random waves forever"). Not in GDD (DF-03).
- Tiers: missing (DF-01). Not enforced in this feature. Not in GDD.
- `random_count` and fixed waves per level: missing for real content. Not in GDD.
- Total wave count: missing (WV-03). Not in GDD.
- Placeholder content, proposed by guardian, approved by Director in chat. Not in GDD:
  - `wave_0`: 1320 px (20 s at Level 1), fixed. 6 meteorites (2 small, 3 medium, 1 big) and 3 common coins, each coin within 96 px of a meteorite.
  - `l1_a`: 1320 px, fixed. Meteorites and satellites, 2 coins.
  - `l1_b`: 1320 px, pool, `min_level` 1. Meteorites and fireballs, 2 coins.
  - Playlist, every level 1 to 8: fixed [`l1_a`], `random_count` 1. After Level 8: `l1_b` forever (the only pool wave, so it repeats).
  - Level 2 starts after 3960 px, about 60 s into the run.
- Extra rest per wave: ticks, ≥ 0, 0 when left out, added after `rest_gap_base` × Rest gap ×, after the wave that sets it. Fixed: it never scales with level. Idea and "fixed" by the Director in chat; unit and placement proposed by guardian, approved by Director in chat. All placeholder waves set 0. Not in GDD.
- Random picks not seeded, new every run. Proposed by guardian, approved by Director in chat. Not in GDD.
- Only one allowed pool wave: it repeats. None allowed: the files are refused at load. Proposed by guardian, approved by Director in chat. Not in GDD.
- The seam counts entry warnings as on screen. Proposed by guardian, approved by Director in chat. Not in GDD.
- Placements may use `as_level`; `speed` stays debug-only. Proposed by guardian, approved by Director in chat. Not in GDD.
- Debug mode default when the choice is left out: the test spawn list. Proposed by guardian, approved by Director in chat. Not in GDD.
- Overlay lines `wave <id>`, `level <n>`, `wave rest`, `wave none`, same font and color as the other overlay lines. Proposed by guardian, approved by Director in chat. Not in GDD.
- Placeholder wave ids `wave_0`, `l1_a`, `l1_b`. Proposed by guardian, approved by Director in chat. Not in GDD.

## Objections
1. Coins in Wave 0 break the wording of Locked decision 7, "Every run opens with the same fixed, meteorites-only Wave 0". Source: 01-vision.md, Locked decisions; 09-waves.md, rule 3. Changing a locked decision needs the Director's explicit go-ahead and a decision-log row. Alternative: read "meteorites-only" as "the meteorite is the only hazard" and reword it (G1). The guardian recommends this: Pillar 3 wants coins next to danger from the first wave, and the wave stays the same every run.
2. Distance triggers don't follow Timer ×. 08-difficulty.md, rule 4 says Timer × shortens "spawn times inside a wave". With distance triggers, spawn spacing shrinks with the scroll speed instead: 1 ÷ 1.7 ≈ 0.59 at Level 8, not 0.70. Source: 08-difficulty.md, rule 4 and the Level table. Alternative: keep the Director's design and drop "spawn times inside a wave" from rule 4 (G2). The guardian recommends this. One rule moves the whole layout together, and entry warnings stay 60 ticks at every level, so Pillar 2 holds. The Director should know Level 8 waves get about 15 % denser in time than the Timer × row suggests.

## Decision log
- Feature shaped from the Director's design discussion, given as input. Linear issue DRA-76 created in Backlog.
- One feature, no split. Schemas, loader, wave clock, runner, picker, rest gap, level rise, scroll speed per level, debug choice and overlay lines are one playable loop. Split out, none of them can be seen in the browser alone.
- The Director said: "Make decisions for me and tell me which decisions where made." The guardian decided, pending approval: scroll speed follows the level (needed for "the next level" to mean anything); the level rises the tick the last wave ends; Wave 0 plays at Level 1; a fixed wave may sit in several playlists; refused-at-load rules; one-pool-wave repeat; unseeded picks; entry warnings count for the seam; `as_level` allowed, `speed` not; debug default stays the spawn list; overlay wording; placeholder content and playlist; `game/waves/` as the folder; provisional marking.
- Tiers (DF-01) not enforced. `min_level` is set by hand until DF-01 is answered.
- Seam: kept as the Director said (120 px at each end of each wave, 240 px between two waves). The guardian notes the pacing cost and agrees it is the safe choice for random order.
- Objection 1, Wave 0 coins. Director: "Agree". Go-ahead to reword Locked decision 7 as in G1. Logged as a clarification row in 91-decision-log.md (G8).
- Seam at 240 px between waves. Director: "We will modify it later. keep it for now".
- Objection 2. Director answered about the rest gap: "That is the rest_gap between waves for? isnt it? so we can define how much time after the seam of the waves is needed for the next wave to appear? every wave can have it attached. So we can specify an extra wait time for starting ( if we know the current wave is too difficult)". The guardian explained the rest gap is outside a wave and Objection 2 is about spacing inside it. Objection 2 stays open (Question 1).
- From that answer, a new In item: extra rest per wave. A wave property, not a drifter value, so it doesn't break "no per-wave drifter values". Shape proposed by the guardian, pending approval.
- The Director gave the main session leave to act as Wave Designer and Wave Critic until those agents exist. The guardian narrowed it to `game/waves/` and `docs/reports/waves/`, per the roster.
- Objection 2. Director: "yes". Distance triggers stay; "spawn times inside a wave" leaves 08-difficulty.md rule 4 (G2).
- Extra rest per wave. Director: "approve fixed". It adds after the scaled rest gap and never scales with level. Rule 6 wording in G2 changed to match.
- Director approved the final feature, in answer to a question that listed every proposed value: "Approved, ship it". Every "proposed by guardian" value above is approved.
- GDD changes G1 to G8. Director: "do it for me". The main session applied them to `docs/design/gdd/` outside the guardian role, on that instruction. G9 (optional) not applied.
