Verdict: ship
Created by: scope-guardian
Feature: DRA-86 Floating islands
Parent: none

## Request
"I want to continue with Island drifter is there any open question? otherwise I want you to take care of everything" (Director). Islands were the next drifter in the order agreed in DRA-39, DRA-56, DRA-61 and DRA-62: fireball, score, coin, then floating islands.

## Feature
Floating islands are big chunks of green ground that drift down with the world. They don't move on their own. They enter at their placed x, from just above the top edge, with no warning of any kind.

Touching an island never costs a life and never pays. It blocks the ship like a side wall, with no bounce. The ship is moved out the shortest way, and the part of its speed going into the surface drops to 0. The part along the surface stays, so the ship slides down a slope.

The ship can stand on top of an island and ride down with it, and lift off by thrusting up. Under an island, the underside holds the ship down and carries it at the island's own speed, never faster. The ship can always slide out sideways. A ship carried off the floor has fallen, like any fall.

Islands block an invulnerable ship and a ship in the respawn wait too. If the fall respawn point is inside an island, the ship respawns at the nearest clear spot straight above or below. It goes below if above would put its top edge past the top line.

Five shapes: rectangle (default), box, L, T and triangle. `invert` flips the L, the T and the triangle upside down.

An island that has entered is removed once it is fully below the floor.

In debug mode, the test spawn list can place islands and play only them.

## Limits
In:
- Floating islands as in drifters/05-floating-islands.md: kind blocker, parked, enters from the top at the placed x (a placement may set another spot, 07-drifters.md rule 14), no entry warning, no telegraph, no specialty, no graze, no hit, no level scaling.
- All five variants at the sizes in the shape table, with `arm` 40 and `invert` for the L, T and triangle. Director: "All five, listed sizes".
- The polygon hitbox shape (07-drifters.md, rule 8), for the triangle. The L and the T are two boxes each.
- Blocking in the ship step, right after the side walls (04-ship.md, rule 2, step 6; drifters/05-floating-islands.md, rule 4): push out the shortest way, drop the speed into the surface, keep the speed along it, stand and ride, held and carried underneath, no shove.
- Fall respawn moved out of an island (05-lives-and-damage.md, rule 2.3).
- Placeholder look: the filled shape in (70, 160, 80) with a 2 px edge in (35, 90, 45) drawn inside the shape. The edge never draws outside the hitbox.
- Debug overlay: the island's hitbox outline and label, like every drifter. No graze zone.
- Every value in the tuning file, never hard-coded, like every drifter (precedent: DRA-56, DRA-62).
- Islands are a valid drifter type in wave files, with the placement fields they already have: position, variant, `invert`.
- Debug spawn list rows for islands: x and y, an optional variant and `invert`, no speed. An islands-only mode. Example rows for every variant, inverted where it applies. Same pattern as the coin (DRA-62).
- wave_check: islands keep counting as hazards (seam, placement, coin near), as `_is_hazard` does today. A new check fails a coin whose hitbox sits inside an island (09-waves.md, rule 7.7). Built by the main session after the tasks pass QA, in `tools/wave_check/`, with tests. Not an Architect task.
- Tests: the ship against every variant and `invert`, push-out from every side, slope slide, stand and ride, held and carried, carried off the floor, invulnerable and respawn-wait blocking, respawn inside an island, leaving.

Out:
- Wave content: an island wave and its playlist slot. That is a wave request, after this feature.
- The wave_check bot and gap checks. They are part 2 of wave_check, not built for any drifter.
- The wave editor. It draws drifters through the game's own renderer; any island gap there is a follow-up.
- Final art and sound (AA-01, AA-03).
- Graze, for islands or anything else.
- Islands that move on their own, break or hurt. Each would be a new drifter (drifters/05-floating-islands.md, How to extend).
- Drifters colliding with islands. Drifters pass through each other (07-drifters.md, rule 15).

## Player sees
In debug mode, with the list set to islands only: a green slab with a darker edge scrolls down from the top, with no warning. Land on it: the ship stands and rides down. Fly under it: the ship is held and carried toward the floor, and slides out sideways. Land on the triangle: the ship slides down its slope.

## Fit
- Pillar 1, Master the drift: fits. Islands shape the path. Sliding along slopes and riding tops is pure momentum play, and a carried ship can always slide out, so there is no instant stop. Source: 01-vision.md, Pillars; 91-decision-log.md, row 49.
- Pillar 2, See it before it hits you: fits. Islands can't hurt, so they need no warning. They are big and in view about 2.5 s before they reach the ship's zone. Source: drifters/05-floating-islands.md, entry_warning (locked).
- Pillar 3, Risk brings reward: not touched by the island itself. Waves can make narrow island paths that pay through coins later.
- Locked decision 3, solid walls with no bounce: fits. Islands block the same way. Source: 01-vision.md, Locked decisions.
- Locked decision 5, no stun: fits. Being carried never takes control away; the ship can always slide out.
- Locked decision 6, archetype: fits. Forced-path blocker; variants change shape only. Source: 07-drifters.md, rule 10.
- Locked decision 7, waves are hand-authored JSON: fits. Islands are placed by hand like any drifter.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- Overlap with shipped features: none. Builds on DRA-29 (drifter base), DRA-39 (debug spawn list, collision tests), DRA-47 (line hitbox; polygon left for islands), DRA-62 (parked drifters) and DRA-76 (waves).

## Values needed
From the GDD (drifters/05-floating-islands.md unless noted; guesses unless noted):
- archetype Forced-path blocker, enters_from top, kind blocker, scroll_kind parked, entry_warning none, telegraph none, specialty none, graze no: locked.
- variants: rectangle 320 × 120 (default), box 120 × 120, l_shape 320 × 120, t_shape 320 × 120, triangle 320 × 120. Shapes as in the shape table.
- wave_check: an island counts as a hazard for seam, placement and coin near. 09-waves.md, rule 7 (added 2026-10-21, decision log row 75).
- arm: 40 px.
- hitbox: the shape exactly as drawn. L and T are two boxes each; the triangle is a polygon.
- placeholder_look: fill (70, 160, 80), 2 px edge (35, 90, 45) inside the shape.
- Scroll: scroll_base and the level's scroll speed. 03-world-and-camera.md; 08-difficulty.md.
- fall_respawn: x 320, y 240. 05-lives-and-damage.md, rule 2.3.
- Leaving: fully below the floor. 07-drifters.md, rule 12.
- sound: none yet.

Not in GDD:
- Debug island row: x and y, an optional variant and `invert`, no speed; an islands-only mode. Approved by Director in chat. Not in GDD; temporary stand-in.

## Objections
No objection. Islands are fully specified in the GDD with no TBD, and they fit every pillar and locked decision (see Fit).

## Decision log
- Feature shaped from drifters/05-floating-islands.md, 07-drifters.md, 04-ship.md rule 2, 05-lives-and-damage.md rule 2.3, 09-waves.md rule 7.7 and the DRA-39 notes for islands. Linear issue DRA-86 created in Backlog, related to DRA-62 and DRA-47.
- Scoped in the main session with the scope-guardian definition loaded.
- Q1, wave_check and islands. Director: "we will have island as a hazard. It is just a different kind". Confirmed in a follow-up: in play, touching an island still never hurts; wave_check treats islands as hazards (seam, placement, coin near), as it does today. Director: "Right, add the coin check": a new check fails a coin inside an island.
- GDD note. Director: "Yes, add the line". The main session added the wave_check line to 09-waves.md, rule 7, and row 75 to 91-decision-log.md.
- Q2, shapes. Director: "All five, listed sizes".
- Q3, debug rows. Director: "Yes, like the coin".
- Director approved the final feature, in answer to a question that listed the final shape and the full pipeline: "Approved, run everything".
