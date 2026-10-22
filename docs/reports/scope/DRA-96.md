Verdict: ship
Created by: scope-guardian
Feature: DRA-96 Planet
Parent: none

## Request
"Next feature: the Planet drifter (docs/design/gdd/drifters/08-planet.md, priority 3, spec Open: None). It's a gravity well that drifts down with the scroll and pulls the ship toward its center inside pull_radius. The pull is added to the ship's tick right after gravity, so the frozen ship contract will need to reopen. Please scope it, check it against the pillars, and open the Linear feature issue." (Director)

## Feature
A planet is a purple sphere that drifts down with the world, wrapped in a gravity field the player can see. It doesn't move on its own. Its entry warning shows at its x against the top edge, then it scrolls in from just above the top edge.

While the ship's center is inside the field, the planet pulls the ship toward its center. The pull is 0 at the field's edge and rises in a straight line to its full strength at the planet's surface. It is added right after gravity, on every tick gravity applies: also while the ship is invulnerable, never during the respawn wait. Overlapping fields add up. The pull acts on the ship only, never on other drifters.

Touching the planet is a hit and costs a life. The field never hits. Thrust always beats the pull, so the player can always fly out. Nothing about the planet changes with level; a faster scroll only brings it sooner.

The field is always on and always drawn: a ring at the field's edge, and two faint rings that drift inward from it and fade.

In debug mode, the test spawn list can place planets and play only them.

## Limits
In:
- The planet as in drifters/08-planet.md: kind hazard, parked, enters from the top at the placed x (a placement may set another spot, 07-drifters.md rule 14), shared entry warning, no telegraph, no specialty, no level scaling.
- One variant, standard: a 64 px circle, hitbox one circle of radius 32.
- The pull, in the ship's tick right after gravity (04-ship.md, rule 2, step 2; drifters/08-planet.md, rule 4). Linear from 0 at `pull_radius` to `pull_max` at the surface, toward the center. Sums over every planet. Applies while invulnerable; not during the respawn wait. This reopens the frozen ship contract, and the run and drifters contracts with it. That goes through the structural lane like DRA-86 did.
- The escape rule as a guard: the game refuses a tuning where `pull_max` + `gravity` ≥ `thrust_up`, or `pull_max` ≥ `thrust_side` (04-ship.md, rule 5; drifters/08-planet.md, rule 5). Today: 0.36 < 0.42 and 0.2 < 0.42.
- Hits through the shared hit rules, re-hit cooldown included (05-lives-and-damage.md, rules 1.5 and 2.7).
- Placeholder look: body filled in (140, 70, 200); a 1 px ring at `pull_radius` and two 1 px inner rings in (180, 120, 255) that slide inward to the surface over `field_ring_trip`, `field_ring_gap` apart, fading by `field_ring_fade`. Looks only, never scaled by level.
- Start and leaving judged on everything drawn, field ring included (07-drifters.md, rules 12 and 14). The planet starts with its ring touching the top edge (center 151 px above it) and stays, still pulling, until the ring is fully below the floor.
- Debug overlay: the planet's hitbox outline, label and graze zone, like every hazard. No new overlay item for the field; the field ring is already drawn.
- Every value in the tuning file, never hard-coded (precedent: DRA-56, DRA-62, DRA-86).
- Planets are a valid drifter type in wave files, with placement fields x and y only (drifters/08-planet.md, rule 9).
- Debug spawn list rows for planets: x required; y optional, and left out the planet enters from the top like in play (drifters/08-planet.md, rule 1); no variant, no speed. A planets-only mode. Example rows: one planet, and two with overlapping fields. Same pattern as the coin and islands (DRA-62, DRA-86).
- wave_check knows the planet: it counts as a hazard for seam, placement and coin near, measured from its body, never its field (09-waves.md, rule 7; drifters/08-planet.md, rule 11). Built by the main session after the tasks pass QA, in `tools/wave_check/`, with tests. Not an Architect task.
- Tests: pull at the edge, mid-field and surface; no pull outside; two fields summed; pull while invulnerable; no pull in the respawn wait; escape with thrust from the surface (up and sideways); hit and re-hit; start, entering and leaving; the rule 5 guard.

Out:
- Graze pay, for planets or anything else. SC-02 and SC-04 are still open (precedent: DRA-61, DRA-62, DRA-86).
- The wave_check bot and gap checks, including the bot's pull physics (drifters/08-planet.md, rule 11). They are part 2 of wave_check, not built for any drifter.
- Wave content: a planet wave and its playlist slot. A wave request, after this feature.
- Final art and sound (AA-01, AA-03).
- The skin list and the random look pick. With one placeholder look the pick has nothing to choose from. Built when the art feature adds a second skin. `look_pick` (locked) is still met: one look, picked every time.
- Moving the ship's physics values to a tuning file. They stay where they are (ship contract, Rationale); the guard reads them there.
- A pull on other drifters, a pulsing or pushing field, a field that switches off. Each is a new drifter (drifters/08-planet.md, How to extend).
- Drifters colliding with planets or islands (07-drifters.md, rule 15).

## Player sees
In debug mode, with the list set to planets only: after its warning, a purple ball inside a lilac ring scrolls down from the top, with two faint rings sliding inward. Fly into the ring: the ship is tugged toward the ball, harder the closer it gets. Thrust out and escape. Touch the ball: a life is lost.

## Fit
- Pillar 1, Master the drift: fits. The pull is an acceleration, never a set speed, so it bends the ship's drift and the player fights back with thrust (04-ship.md, rule 4). Escape is always possible (rule 5). Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: fits. Shared entry warning before it appears, the field is always drawn at its true edge, and the body never strikes. The tug starts at 0 at the ring, so the player feels it build. Source: drifters/08-planet.md, rules 1, 2 and 4; 07-drifters.md, rule 9.
- Pillar 3, Risk brings reward: fits in design, not yet in play. Skimming the surface pays a graze once grazes pay. Until then a planet earns nothing extra, like every hazard so far. Source: 06-scoring.md, rules 3 and 4.
- Locked decision 4, fixed tick, gravity always on: fits. The pull adds after gravity and never replaces it. Source: 01-vision.md, Locked decisions; 04-ship.md, rule 2.
- Locked decision 5, no stun: fits. The pull never takes control away, and thrust always beats it.
- Locked decision 6, archetype: fits. Gravity well; looks are skins, not variants. Source: 07-drifters.md, rule 10.
- Locked decision 7, waves are hand-authored JSON: fits. Planets are placed by hand.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- Overlap with shipped features: none. Builds on DRA-29 (drifter base), DRA-39 (debug spawn list, re-hit cooldown), DRA-62 (parked drifters) and DRA-86 (a drifter feeding the ship step).

## Values needed
From the GDD (drifters/08-planet.md unless noted; guesses unless noted):
- archetype Gravity well, enters_from top, kind parked, pull_shape, telegraph none, specialty none, graze yes, look_pick random: locked.
- variants: one, standard (default).
- size 64, hitbox circle radius 32.
- pull_radius 150 px, from the center.
- pull_max 0.2 px/tick² at the surface (32 px from the center).
- entry_warning_ticks 60: the shared value, 07-drifters.md.
- placeholder_look: body (140, 70, 200); rings (180, 120, 255), 1 px.
- look_reference: purple sphere with faint rings.
- field_ring_trip 120 ticks, field_ring_gap 60 ticks, field_ring_fade 50% to 0%: proposed by guardian, approved by Director in chat, written into drifters/08-planet.md (decision log row 76) on the Director's go-ahead.
- gravity 0.16, thrust_up 0.42, thrust_side 0.42: 04-ship.md, for the rule 5 guard.
- Scroll: scroll_base and the level's scroll speed. 03-world-and-camera.md; 08-difficulty.md.
- Leaving: 07-drifters.md, rule 12; drifters/08-planet.md, rule 7.
- sound: none yet.

Not in GDD:
- Debug planet row: x required, y optional (left out: enters from the top), no variant, no speed; a planets-only mode. Approved by Director in chat. Not in GDD; temporary stand-in.

## Objections
No objection. The planet is fully specified in the GDD with no TBD, and it fits every pillar and locked decision (see Fit). Reopening the frozen ship contract is the normal structural lane, as DRA-86 did for islands.

## Decision log
- Feature shaped from drifters/08-planet.md, 04-ship.md rules 2 and 5, 07-drifters.md rules 9, 12 and 14, 05-lives-and-damage.md rules 1.5, 2.5 and 2.7, 06-scoring.md, 09-waves.md rule 7, and the DRA-86 precedent for wave_check and debug rows. Linear issue DRA-96 created in Backlog, related to DRA-86 and DRA-62.
- Scoped in the main session with the scope-guardian definition loaded.
- Q1, start and leave. Director: "I confirm the reading." Start and leaving are judged on the field ring too.
- Q3, debug rows. Director: "Yes ... However planets also come from the top." Rows take x; y is optional and, left out, the planet enters from the top.
- Q2, inner rings. Director: "Figure it out. Make it reasonable." Guardian proposed a 120-tick trip from the field edge to the surface, the two rings 60 ticks apart, fading 50% to 0%. Director: "Approve as proposed".
- Pull shape. The Director asked whether one constant pull inside the ring is better. Guardian recommended keeping the ramp: a constant pull jolts the ship at the ring and makes the surface no riskier than the edge (Pillars 1 and 3), saves no build work, and `pull_shape` is locked. Director chose "Ramp". The spec is unchanged.
- Q4, skin picker. Re-explained in plain words. Director: "With the art".
- GDD write-back. Director: "everything thats needed to be modified". The main session added `field_ring_trip`, `field_ring_gap` and `field_ring_fade` to drifters/08-planet.md, a line to its rule 10, and row 76 to 91-decision-log.md. The debug row stays out of the GDD as a temporary stand-in.
- Director approved the final feature in chat: "I approve after this", given with the open points, all settled above.
