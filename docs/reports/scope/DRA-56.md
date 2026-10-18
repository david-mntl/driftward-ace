Verdict: ship
Created by: scope-guardian
Feature: DRA-56 Fireball
Parent: none

## Request
"Ok now lets continue with the next drifters on the list"

## Feature
A fireball dives across the screen in a straight line, 35° from straight down. By default it enters at the top-left corner and flies down and to the right. `invert` mirrors it: it enters at the top-right corner and flies down and to the left. A placement may instead start it at any x along the top, or at a y on a side wall. A side entry from the left wall flies right. With `invert`, it enters from the right wall and flies left.

Its entry warning shows first, where it will appear: at its x against the top edge for a corner or top entry, at its y against the side edge for a side entry. The warning copy is tilted along its path, with the tail pointing back, so it shows which way the fireball will fly.

Then it flies at a fixed speed. It never turns and never aims at the ship. Touching its head or its tail is a hit. It flies through walls and other drifters. Once it has been on screen, it is removed when its head and its tail are both fully off screen at a side or the bottom. Nothing of it is still visible when it goes. After it takes a life, it dims for the re-hit cooldown, like every hazard.

Two variants: small (21 px head, the default) and big (32 px head). Both fly at the same speed.

In debug mode, the test spawn list can place fireballs and play only them.

## Limits
In:
- Fireball as in 06-fireball.md: variants small and big, default small, `invert`, all three entries (top corner by default, an x along the top, a y on a side), the straight 35° path, hits, level scaling (speed × hazard speed, the angle never scales).
- Hitbox: two circles. The head, plus a tail at half the head's radius, touching the head from behind along its path. Circles exist already, so no new shape kind.
- Leaving: only once the head and the tail are both fully off screen. 07-drifters.md rule 12, 06-fireball.md rule 5, 91-decision-log.md row 64.
- Entry warning in the shared look and fixed size, the copy tilted along the path with the tail back.
- Re-hit cooldown and dim, as for every hazard (05-lives-and-damage.md rule 1.5).
- Collision tests in the DRA-39 structure: the ship against every fireball variant.
- Placeholder look only: an orange head circle and a dark yellow tail circle, the size of the hitbox.
- Every value in the tuning file, never hard-coded.
- Debug spawn list: fireball rows (type, position, optional variant, `invert` and speed). The position picks the entry: the default corner, an x along the top, or a y on a side. A fireball-only mode. Example rows for both variants, both directions and all three entries.

Out:
- Graze scoring. No score exists yet. Score is the next feature.
- Trail art, sprite art, sound.
- Score, coin, floating islands. Each is its own feature.
- Waves and wave_check.
- Ship-relative placement (Director's to-do list).
- Curved or homing paths. A new behavior is a new drifter (06-fireball.md, How to extend).

## Player sees
In debug mode, with the list set to fireball only: a tilted warning in a top corner, then an orange ball with a dark yellow tail diving down across the screen at a steep angle. Touching it costs a life.

## Fit
- Pillar 1, Master the drift: fits. It falls about as fast as a meteorite but also slides sideways, so the safe spot keeps moving and the player has to drift with it. Source: 01-vision.md, Pillars; 06-fireball.md, Summary.
- Pillar 2, See it before it hits you: fits. The entry warning shows where it appears and, tilted, where it goes, also for side entries. Source: 07-drifters.md rules 1 and 9; 06-fireball.md rule 1.
- Pillar 3, Risk brings reward: not touched. It has a graze zone, but scoring is out. Source: 06-scoring.md.
- Locked decision 6, hazards defined by archetype: fits. Fast linear hazard. Small and big change values only. Source: 07-drifters.md rule 10.
- Locked decision 7, waves are hand-authored JSON: not touched. The test list is debug only. Source: 15-tech-constraints.md.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- Overlap with shipped features: builds on DRA-29 (drifter base), DRA-39 (re-hit cooldown, tilted warning copy, debug spawn list, collision test structure) and DRA-47 (the shared hooks and the fixed warning size). No overlap: the fireball itself was out of all three. The Linear issue is linked to DRA-39 as related.

## Values needed
From the GDD (06-fireball.md, all guesses unless noted):
- archetype, enters_from, kind, telegraph, specialty, graze: locked.
- variants small 21 and big 32 px head width, default small.
- hitbox: head radius 10.5 and 16, tail radius 5.25 and 8, touching the head from behind along the path.
- speed_ratio 0.47 × the ship's top sideways speed, measured along the path. Speed ≈ 3.1 px/tick at Level 1. Both variants share it.
- angle 35° from straight down, fixed per fireball type.
- direction left to right, `invert` mirrors it.
- start: just outside the screen. Default at the top-left corner, head's center on the left wall, head's bottom edge on the top edge. With `invert`, the same at the right wall.
- placeholder_look: head (255, 140, 0), tail (200, 160, 0).
- entry_warning_ticks 60, and the shared warning look and fixed size of 24 px (glow 18, copy 14). Source: 07-drifters.md.
- rehit_cooldown 180 ticks, rehit_dim 0.75. Source: 05-lives-and-damage.md.
- Hazard speed per level. Source: 08-difficulty.md.

Changed in the GDD on 2026-10-18, on the Director's go-ahead in chat ("wrtie it as a rule"):
- A drifter is fully off screen only when nothing of it that is drawn is still on screen. For the fireball: head and tail both off. Chain lightning is the one exception, kept as it is. 07-drifters.md rule 12; 06-fireball.md `size` row and rule 5; 91-decision-log.md row 64.

Not in GDD:
- A debug row's speed sets the speed along the path, and level scaling still applies on top. This follows the DRA-39 rule for every row ("proposed by guardian, approved by Director in chat"). It is a temporary stand-in, not GDD content.

## Objections
None. Every behavior and number is in 06-fireball.md, and the Director settled the open points in decision log rows 44 and 61. Nothing breaks a pillar, a locked decision or the out-of-scope list.

## Questions
None.

## Decision log
- Feature shaped from 06-fireball.md and decision log rows 44, 61 and 63. Linear issue DRA-56 created in Backlog.
- Order kept from DRA-39: fireball, then score, then coin. Floating islands later.
- Board sync: DRA-39 and DRA-47 set to Done. All their sub-issues were Done and both integration reports say `Verdict: pass`.
- Director approved the feature with one change: "Approv[e]. One thing. Can we not make that the fireball dissapears when the tail is also outside? [...] Everything that can be seen from the object is out." The fireball is removed only once its head and tail are both off screen. Fits Pillar 2: the tail can hit until the moment it disappears. 
- Director: make it a rule for every drifter ("wrtie it as a rule"), but leave chain lightning as it is for now. Rule 12 names chain lightning as the exception. The GDD was edited in this chat on that go-ahead.
- If a shipped drifter other than chain lightning breaks the new rule 12, that is a follow-up with its own id, not part of DRA-56.
