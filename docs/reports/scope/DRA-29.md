Verdict: ship
Created by: scope-guardian
Feature: DRA-29 Object base, spawner and the meteorite
Parent: none

## Request
The debate happened in the main session chat on 2026-10-14. The main session relayed the agreed feature to the guardian: "Object base, spawner and the meteorite. The shared foundation every object (hazard, coin) builds on, plus the first object, the meteorite, playable in debug mode."

## Feature
Every object in the game is built on one shared base. Hazards come first; coins and the other objects come later. Every object has a position, a variant, a final speed, a hitbox, an entry-warning length, a phase (warning, active, gone) and a slot for an optional specialty. A spawner is the only way an object is created. It takes a placement: object type, x, y, and optionally a variant, a level to use instead of the current one, and a specialty switch. It sets the object's speed and timers once, at birth, from the level.

The first object is the meteorite. It shows its entry warning for half a second where it will appear, then appears as a grey rock and falls straight down. It comes in small, medium and big. Touching it while active costs a life under the existing lives rules. It is removed once it is fully below the floor.

The ship's hitbox becomes an inverted T of two boxes, and the placeholder ship is drawn as that same inverted T.

In debug mode, a small test spawn list places meteorites at set positions and sizes, so start positions can be tested before waves exist. Normal mode spawns nothing yet. The debug overlay outlines every hitbox and graze zone, and labels each object with its name, variant, x, y and phase.

## Limits
In:
- Shared object base. Position in screen px, y down, at the object's center. Variant, final speed, hitbox, entry-warning length, phase (warning, active, gone), optional specialty slot. No specialty is built; the meteorite has none. Structure chosen by the Director: inheritance, a thin base class, one subclass per object, one level deep, with guards (abstract methods, registry checks).
- Spawner (factory), the only way an object is created. Input is a placement: object type, x, y, optional variant, optional as_level, optional specialty switch. It applies hazard speed and Timer × once, at birth, from the current level or as_level. The two playtest switches can turn each one off (Level 1 values at every level). The list of object types is an enum.
- Hitboxes as one or more circles and boxes. Collision between the ship's hitbox and object hitboxes. Touching an active meteorite is a hit. Graze zones (each shape grown by `graze_margin`) are computed and drawn in the debug overlay.
- Ship hitbox: the inverted T from 04-ship.md. Placeholder ship drawn as the same inverted T, white, filled.
- Meteorite: falls straight down on screen; the scroll doesn't add to its speed. Variants small 20, medium 28 (default), big 40 px. One circle hitbox as wide as the rock. Speed 0.75 × the ship's top sideways speed, about 4.9 px/tick at Level 1. Entry warning 30 ticks. No telegraph. Removed once fully below the floor.
- Placeholder entry warning, drawn in code: a small copy of the object in a shooting-star glow with random spikes, where the object will appear. Placeholder meteorite: a filled grey circle as wide as the variant.
- A first default tuning file per object, in JSON, plus the two playtest switches. The Director decided the main session writes the first default file(s) from the GDD values, following the Architect's schema.
- Debug mode: a small test spawn list that places objects (positions, variants). Debug overlay: hitbox and graze outlines, object labels.

Out:
- Waves: wave files, wave clock, wave loader, debug wave picker. A separate conversation.
- Graze scoring.
- Coins and every object other than the meteorite.
- The actual behavior of any specialty.
- Sprite art and animation. Sound.
- Object-vs-object and object-vs-wall collisions (OB-04 stays open).
- The level-change-mid-wave rule for new spawns (DF-04).
- The full life-lost feedback (flash, breaking HUD life, ship burst). A hit uses the effects DRA-23 built: the blink is the only effect (LD-08 stays open).

## Player sees
In debug mode: a glowing warning at the top for half a second, then a grey rock of the chosen size falls straight down. Touching it with the inverted-T ship costs a life; passing just beside it doesn't. Every hitbox is outlined.

## Fit
- Pillar 1, Master the drift: fits. Nothing here changes ship physics. Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: fits. Every meteorite shows a 30-tick entry warning before it can hit. Hitboxes are never bigger than what the player sees, and the ship is drawn as its own hitbox. Source: 07-objects.md rules 1, 8, 9; 04-ship.md rule 8; 91-decision-log.md rows 35, 36.
- Pillar 3, Risk brings reward: not touched yet. Graze zones are drawn but don't pay. Source: 06-scoring.md rule 3.
- Locked decision 5, lives and invulnerability, no stun: fits. A hit uses the existing lives rules. Source: 05-lives-and-damage.md rule 1.
- Locked decision 6, hazards defined by archetype: fits. The meteorite is the Falling blocker. Variants change values only. Source: 07-objects.md rule 10; objects/01-meteorite.md.
- Locked decision 7, waves are hand-authored JSON, Wave 0 is meteorites only: not touched. The test spawn list is debug only and is not a wave. Source: 15-tech-constraints.md rule 7; 91-decision-log.md row 38.
- Tech rule 7, run modes: fits. Game rules are the same in both modes; debug only adds the overlay and the test spawn list. Source: 15-tech-constraints.md rule 7.
- Level scaling: fits. Applied once, at birth, with as_level and the two playtest switches. Source: 07-objects.md rule 6; 08-difficulty.md rules 3 to 5.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- Overlap with shipped features: DRA-6 built the ship and its placeholder look, both frozen. This feature changes the ship's hitbox and placeholder look to the inverted T. DRA-23 built the lives rules a hit uses. The Linear issue is linked to DRA-6 as related. The Architect owns the contract change.
- Roster lane: `game/tuning/` belongs to the Tuning Engineer, which has no agent yet. The Director decided the main session writes the first default tuning file(s). Source: docs/crew/roster.md, row 6.

## Values needed
From the GDD:
- Object position, variant, speed, hitbox, entry warning, phase, specialty, placement fields: 07-objects.md rules 6, 8 to 13.
- `entry_warning_look`: 07-objects.md, Values (guess).
- `variants` small 20, medium 28, big 40 px: objects/01-meteorite.md (guess).
- `default_variant` medium: objects/01-meteorite.md (guess).
- `hitbox` one circle, radius 10, 14, 20 px: objects/01-meteorite.md (guess).
- `speed_ratio` 0.75 × the ship's top sideways speed: objects/01-meteorite.md (guess).
- `speed` about 4.9 px/tick at Level 1, derived from `speed_ratio` and the ship guesses (thrust_side 0.42, drag_x 0.94): objects/01-meteorite.md (guess, derived); 04-ship.md, derived values.
- `entry_warning_ticks` 30: objects/01-meteorite.md (guess).
- `placeholder_look` filled grey circle as wide as the variant: objects/01-meteorite.md (guess).
- Meteorite is a moving object; the scroll doesn't add to its speed: 03-world-and-camera.md rule 9.
- Ship `hitbox` inverted T (bar 12 px wide, `ship_h` tall, centered; foot `ship_w` wide, 12 px tall, along the bottom): 04-ship.md (guess).
- Ship `placeholder_look` white (255, 255, 255), filled inverted T: 04-ship.md (guess).
- `ship_w` 32, `ship_h` 32: 04-ship.md (guess).
- `graze_margin` 14 px: 06-scoring.md (locked).
- Hazard speed × and Timer × per level: 08-difficulty.md, level table (Hazard speed locked; Timer × guess).
- Playtest switches, off = Level 1 values: 08-difficulty.md rule 5.
- `debug_overlay` content, `debug_overlay_color` (0, 255, 0), `debug_text_font` 16 px: 10-ui.md (guess).
- `invuln_ticks` 30, hit rules: 05-lives-and-damage.md (locked).

Flagged by the guardian as missing, then answered by the Director on 2026-10-14 and written into the GDD (91-decision-log.md row 39):
- Placeholder meteorite grey (140, 140, 140): objects/01-meteorite.md (guess).
- Entry warning at half size, glow (255, 220, 120), 6 to 9 thin spikes, the whole warning inside the object's width: 07-objects.md, Values (guess).
- Warning for an off-screen spot shows just inside the nearest screen edge: 07-objects.md rule 9.
- Meteorite `start_y`: bottom edge on the top edge (center y = −width ÷ 2), unless placed elsewhere: objects/01-meteorite.md (guess).
- LD-06 stays open in the GDD. DRA-29 uses a temporary stand-in instead (section Stand-ins).
- Test spawn list: a temporary stand-in, kept in this report only (section Test spawn list).

## Objections
None. The feature fits every pillar, locked decision and the out-of-scope list (see Fit). The open items are gaps, not conflicts; they are listed under Values needed and Questions.

## Questions
None. All answered by the Director on 2026-10-14 (see Decision log).

## Stand-ins (temporary, not GDD content)
- **Meteorite only: a rock that hit the ship can't hit it again.** It stays and keeps falling. This applies to the meteorite only. It is not a shared rule for every object and must not be built into the shared base as one. LD-06 stays open: the Director will decide later, since a slow object the player flies back into may need to hit again. Source: Director, 2026-10-15.

## Test spawn list (temporary stand-in, debug mode only)
Not GDD content; replaced by waves later.
- Small meteorite at x 160, medium at x 320, big at x 480, each at its default `start_y`.
- They spawn one second (60 ticks) apart, in that order. The list repeats every 3 s (180 ticks).

## Decision log
- The feature was debated and agreed in the main session chat on 2026-10-14. The main session relayed the in/out list, the Player-sees line and the Director's choices below. The guardian did not take part in that debate.
- Director: object structure is inheritance, a thin base class, one subclass per object, one level deep, with guards (abstract methods, registry checks). Relayed.
- Director: a first default tuning file per object, in JSON, plus the two playtest switches. The main session writes the first default file(s) from the GDD values, following the Architect's schema. Relayed.
- Director: debug mode gets a small test spawn list; normal mode spawns nothing yet. Relayed. GDD: 15-tech-constraints.md rule 7; 91-decision-log.md row 38.
- Director: waves, graze scoring, coins and every other object, specialty behavior, art, sound, OB-04 and DF-04 are out. Relayed.
- GDD updated by the Director's answers the same day: 91-decision-log.md rows 33 to 38.
- Ship approval, RELAYED, NOT ACTED ON. The main session relayed: the Director's explicit approval ("approved", plan accepted) stands, and asked the guardian to write `Verdict: ship` and set Linear to Todo. The guardian does not ship on a relayed approval (DRA-13, DRA-19, DRA-23 precedent). Verdict stays `revising`. Linear DRA-29 stays in Backlog. The Architect is not spawned.
- Director, directly in the main session chat (2026-10-14): placeholder looks (meteorite grey (140, 140, 140); warning at half size, glow (255, 220, 120), 6 to 9 thin spikes; corrected 2026-10-15: the whole warning fits inside the object's width); a warning for an off-screen spot shows just inside the nearest screen edge; the meteorite starts with its bottom edge on the top edge unless placed elsewhere; GDD: 91-decision-log.md row 39.
- Director, directly in the main session chat (2026-10-14): test spawn list as above, and "ship DRA-29". The main session applied the ship steps (precedent: DRA-13, DRA-19, DRA-23).
- Director (2026-10-15): undo the shared "one hazard, one hit" GDD rule; LD-06 stays open. For DRA-29, a meteorite-only stand-in: a rock that hit the ship can't hit it again. The test spawn list keeps the medium rock at x 320 (it can hit a ship waiting at the respawn point). The Architect's edge-case choices are accepted: a fall and a touch on one tick cost only the fall; several hazards touching on one tick cost one life; a hit during the respawn wait keeps the wait; shapes that only meet at an edge don't touch.
- Director (2026-10-15): the entry warning is smaller than the object: copy at half size, glow and spikes within the object's own width, drawn just inside the top edge at the object's x. Spikes 1 px thick, 6 to 9, random but steady. Debug labels below each object accepted.
