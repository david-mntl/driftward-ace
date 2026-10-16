Verdict: ship
Created by: scope-guardian
Feature: DRA-39 Satellite, re-hit cooldown and editable test spawn list
Parent: none

## Request
"I want to proceed creating 5 objects. [...] lets do that one at a time. However would like the architect to have that into account when creating the plans. [...] I would like to have tests against the collisions of the different objects. Because that should work very reliable. [...] How to test the object without waves yet. I would like you to develop sometihng like a list in which we just add these objects there and they appear in a loop (similar to what we do right now with the meteorite)"

Follow-up: "We need to be productive and faster. Cant we not add the shared feature also in the pr of the first drifter that we are gonna develop?"

## Feature
The satellite crosses the screen from a side wall in a straight line. The flat one flies straight across. The angled one sinks 20° below level as it crosses. It enters from the left wall, or from the right wall with `invert`. Its entry warning shows first, at its y against the wall it enters from. For the angled one, the warning copy is tilted along its path. Touching it is a hit. Once it has been on screen, it is removed when it is fully off screen past a side or below the floor. Before it has entered, being off screen doesn't count.

Every hazard, the meteorite included, gets the re-hit cooldown. The hazard that took a life keeps going. It can't hit the ship again for `rehit_cooldown` ticks, and is drawn at `rehit_dim` of its normal brightness meanwhile. When the cooldown ends, it is drawn at full brightness and can hit again. This replaces the DRA-29 stand-in, where a meteorite that hit the ship could never hit it again.

In debug mode, the test spawn list becomes a file the Director edits by hand. Each row places one drifter. A row needs only the drifter type and its position. It may also set the variant, `invert` and the speed. Everything else comes from the drifter's defaults. The list loops. It has two modes: play every row, or play only the rows of one drifter type, such as only satellites. The first version of the file holds the current meteorite rows and example satellite rows.

Collision gets a test structure that stays reliable as shapes and drifters are added. Every pair of shape kinds (circle and box today) has its own set of cases, run both ways round. Every registered drifter is tested against the ship's inverted T, at every variant, without new test code per variant.

## Limits
In:
- Satellite: variants flat and angled, `invert`, start just outside the wall at its placed y, two-box hitbox, placeholder look, entry warning at its y against its wall, tilted copy for angled. Values from 02-satellite.md.
- Removal only after a drifter has entered: a drifter that hasn't yet been at least partly on screen is never removed for being off screen. Applies to every drifter.
- Re-hit cooldown and dim for every hazard (05-lives-and-damage.md rule 1.5 and its edge cases). The meteorite's "hits once" stand-in is removed.
- `rehit_cooldown`, `rehit_dim` and the test list's loop length can be changed in a file. They start at their default values. None of them is required anywhere: left out means default.
- Test spawn list file, debug mode only. Row: drifter type and position required; variant, `invert` and speed optional. Everything else is the drifter's default. Modes: `all` rows, or one drifter type. The Architect proposes the format; the implementers write the first example rows.
- Collision tests for circle and box, and the ship against every variant of the meteorite and the satellite. Case types and guards as the Architect proposed (Decision log).

Out:
- Fireball, chain lightning, score, coin, floating islands. Each is its own feature later.
- Line and polygon shapes. They come with chain lightning and islands.
- Placing a drifter at the ship's x or y at the moment it spawns. A later idea.
- A general game config file (levels, invulnerability, graze margin and the like). On the Director's to-do list.
- Graze scoring, sound, sprite art, waves.

## Player sees
In debug mode, with the list set to satellites only: a warning at the left wall, then a white and blue satellite crossing flat or sinking at an angle. One that hits the ship turns darker for 3 s, then can hit again.

## Fit
- Pillar 1, Master the drift: not touched. No ship physics change. Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: fits. The satellite warns at its wall before it can hit. The dim shows when a hazard that just hit can hurt again. Source: 07-drifters.md rules 1, 9; 05-lives-and-damage.md rule 1.5.
- Pillar 3, Risk brings reward: not touched. Graze zones exist but don't pay yet. Source: 06-scoring.md.
- Locked decision 5, lives and invulnerability: fits. The cooldown follows rule 1.5. Source: 05-lives-and-damage.md.
- Locked decision 6, hazards defined by archetype: fits. The satellite is the Side crosser; flat and angled change values only. Source: 07-drifters.md rule 10.
- Locked decision 7, waves are hand-authored JSON: not touched. The test list is debug only and is not a wave. Source: 15-tech-constraints.md rule 7.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- Overlap with shipped features: DRA-29 (frozen) built the drifter base, the meteorite, its stand-in and the hard-coded test list. This feature replaces the stand-in and the hard-coded list. The Linear issue is linked to DRA-29 as related.

## Values needed
From the GDD:
- Satellite: archetype, enters_from, variants flat 0° and angled 20°, default flat, size 36 × 12, hitbox body 12 × 12 and panel bar 36 × 6, speed_ratio 0.375, speed ≈ 2.5 at Level 1, direction and `invert`, placeholder look body (240, 240, 240) and panel (60, 110, 220), start. 02-satellite.md (guess).
- `entry_warning_ticks` 60, shared. 07-drifters.md (guess).
- `rehit_cooldown` 180 ticks, never scales. 05-lives-and-damage.md (guess).
- `rehit_dim` 0.75. 05-lives-and-damage.md (guess).
- `graze_margin` 14 px. 06-scoring.md (locked).
- Ship inverted-T hitbox. 04-ship.md (guess).
- Hazard speed and Timer × per level. 08-difficulty.md.

Not in GDD:
- Removal only after a drifter has entered. Approved by Director in chat; now in the GDD: 07-drifters.md rule 12, 91-decision-log.md row 58.
- Test list loop length: 180 ticks, kept from DRA-29. Temporary stand-in, not GDD content.
- Test list default mode: `all`. Proposed by guardian, approved by Director in chat. Not in GDD; temporary stand-in.
- A row's speed override replaces the drifter's default speed; level scaling still applies on top. Proposed by guardian, approved by Director in chat. Not in GDD; temporary stand-in.

## Objections
None. Nothing breaks a pillar, a locked decision or the out-of-scope list (see Fit).

## Questions
None. All answered by the Director on 2026-10-16 (see Decision log).

## Coming next (for the Architect: leave room, don't build)
Order agreed: satellite (this feature) → fireball → chain lightning → score → coin. Floating islands later.
- **Fireball:** enters at a top corner or along the top and flies at an angle. Its angle is one per fireball type, set in tuning, not per placement. `invert` mirrors it left to right. Its tail is placed behind the head along its path. Its size is the ball. It keeps every entry: top corners, along the top, and the sides (91-decision-log.md row 61).
- **Chain lightning:** a drifter made of parts. Its hitbox changes over time: arcs and nodes hurt only while firing. Line shape with round ends. First telegraph: a timer scaled by Timer ×, rounded up, never below `telegraph_min`. Removed when every node is gone. Entry warning uses the shared look. Rows in the test list may set its charge time.
- **Score:** score in core and the SCORE line in the HUD. Score = meters + coins for now; grazes don't pay yet.
- **Coin:** a pickup with no entry warning and no WARNING phase. A parked drifter that moves only with the scroll. Touch effect is collect, not hit. Pays points and shows a popup. No sound yet.
- **Floating islands (later):** polygon hitboxes (convex triangles). Collision that can tell how deep and which way to push the ship out. Blocking inside the ship step, right after the walls. Respawn moves out of an island.
- **Later idea:** place a drifter at the ship's x or y at the moment it spawns.

## Decision log
- Director: build the five drifters one feature at a time, one branch and one PR each. Order: satellite, fireball, chain lightning, coin last (score as its own feature just before it). Islands later.
- Architect, Advice mode: put the shared work (re-hit cooldown, editable test list, collision test structure) first; build the satellite before the fireball. Director accepted the swap.
- Director: fold the shared work into the first drifter's PR instead of a separate one ("We need to be productive and faster"). The Architect had advised a separate PR, so the hit-rule change is easier to review and undo. Noted; no pillar conflict.
- Director: the test list is a file the Director edits. Two modes: every row, or only one drifter type (guardian's pick for "one", on request).
- Director: only the important values in a row: position, speed, and values that change how a drifter works (for example the lightning's charge time). Everything else stays default. `rehit_cooldown`, `rehit_dim` and the loop length are changeable but default.
- Director: the Architect proposes the list format; the implementers write the first example rows.
- Director: a general game config file (levels, invulnerability and the like) is not now; added to the to-do list.
- Director: re-hit cooldown is already decided in the GDD (05-lives-and-damage.md rule 1.5; 91-decision-log.md rows 54, 56). The guardian had wrongly cited the DRA-29 stand-in.
- Director, answers for later features: drifters are removed only after they have entered; the fireball's angle belongs to its type and its size is its ball; chain lightning line ends are round, nodes hurt while firing, warning uses the shared look, scaled timers round up; the coin has no warning; sound comes later; score = meters + coins for now.
- Director (2026-10-16): the fireball enters from everywhere the spec lists: top corners, along the top, and the sides.
- GDD updated with the Director's answers (2026-10-16): 07-drifters.md rules 8 and 12, 08-difficulty.md rule 4, drifters/03-chain-lightning.md, drifters/06-fireball.md; 91-decision-log.md rows 58 to 61.
- Director approved the guardian's proposals (default mode `all`; speed override with level scaling on top) and the final feature in chat: "And I say approved."
