Verdict: ship
Created by: scope-guardian
Feature: DRA-13 World scroll and distance counter
Parent: none

## Request
"The screen moving is just optical feeling and logic of the background moving. But we always have the same screen where the objects will start appearing when we set it. That means even if the ship remains always on the center, the score and the meters have to keep moving forward. The screen does not move with the ship. I want to add the meters that we have flown so far. Just the counter for now and the logic behind it. So we can either draw a background or add a picture for it."

## Feature
The screen stays fixed and never follows the ship. Half a second after the ship first appears at screen center, the world starts to scroll down past the screen at Level 1 speed. It never stops, not even after a fall. Distance counts that scroll. It starts at 0 m, and where the ship sits on screen doesn't change it, so a hovering ship still earns meters. A HUD readout shows the distance in whole meters, rounded down, like "312 m". A dim starfield moves down at the scroll speed so the player can see the motion. The top line stays a ceiling: the ship's top edge stops there and its vertical speed becomes 0. In debug mode the debug overlay sits above the HUD on screen, and the two never overlap.

## Limits
In:
- The world scroll at `scroll_base` × the Level 1 scroll speed. It starts `scroll_start_delay` ticks after the ship first appears at screen center, and never stops after that.
- The distance counter: starts at 0 m, grows only through the scroll, whole meters rounded down.
- The HUD meters readout. Only the meters show; SCORE, lives, LV and GRAZE come later.
- In debug mode, the HUD sits below the debug overlay with no overlap.
- A one-layer starfield that moves at the scroll speed and wraps from bottom to top.
- The top line as a permanent ceiling. DRA-6 built it as a stand-in; it is now the real rule (03-world-and-camera.md rule 2, 04-ship.md step 7). The behavior doesn't change.
- The DRA-6 fall stand-in stays as it is: fully below the floor → back to `fall_respawn` at rest, no life lost. The scroll and the counter keep going through it.

Out: levels and level speed changes, lives, hits, invulnerability, hazards, coins, score, the rest of the HUD (SCORE, lives, LV, GRAZE), a picture background, parallax, the control card, any change to ship physics, any new content in the debug overlay (no distance line; it keeps exactly what DRA-6 shows).

## Player sees
Launch the game and wait: half a second after the ship appears, the stars drift down and the readout counts up from "0 m", about 6.6 m per second, whether the ship hovers, climbs, or falls off and respawns.

## Fit
- Pillar 1, Master the drift: fits. The scroll never touches the ship's physics, and the ship never changes the scroll. Source: 03-world-and-camera.md rule 4; 04-ship.md rules 3 and 4.
- Pillar 2, See it before it hits you: no hazards yet. The starfield is dim and has to stay behind hazards and warnings when they arrive. Source: 12-art-and-audio.md rule 2.
- Pillar 3, Risk brings reward: fits. "Surviving earns distance" is now in the pillar, and a hovering ship earning meters is an intended edge case. Source: 01-vision.md, Pillars; 03-world-and-camera.md, Edge cases.
- Locked decision 2, fixed screen and scrolling world: this feature builds it. Source: 01-vision.md, Locked decisions; 91-decision-log.md row 22.
- Locked decision 4, fixed 60 Hz tick: fits. The scroll is a fixed amount per tick.
- Locked decision 5, lives: not built. The DRA-6 fall stand-in stays, as before.
- Locked decision 8, control card: not built, not contradicted. Until it exists, play starts when the ship first appears at screen center (Director's answer).
- 10-ui.md, Values and rule 2: the HUD lists SCORE, lives, level and grazes. A separate meters readout is not one of them. The Director approved it as a temporary stand-in and chose not to change the GDD.
- 12-art-and-audio.md, Summary and AA-02: the background is a black placeholder until the style is set. The starfield is a temporary stand-in the Director approved, and the GDD stays as it is.
- 10-ui.md, rule 7 and `debug_overlay_layout`: the overlay stays as it is, at the top-left. The HUD moves below it in debug mode so they never overlap (Director's answer). The exact numbers are under Values needed.
- Overlap with shipped features: DRA-6 already built the top-line stop. This feature keeps it and doesn't expand DRA-6, so Parent is none.

## Values needed
From the GDD:
- `scroll_base` 1.1 px/tick: 03-world-and-camera.md, Values (guess).
- Level 1 scroll speed × 1.0: 08-difficulty.md, Values (locked).
- `scroll_start_delay` 30 ticks: 03-world-and-camera.md, Values (guess).
- `distance_start` 0 m: 03-world-and-camera.md, Values (locked).
- `px_per_meter` 10: 03-world-and-camera.md, Values (locked).
- `meters_rounding` whole meters, rounded down: 06-scoring.md, Values (locked).
- `top_line_ratio` 0.35 and the ceiling rule: 03-world-and-camera.md, Values (locked) and rule 2; 04-ship.md, step 7.
- `screen_w` × `screen_h` 640×480: 03-world-and-camera.md, Values (guess).
- `fall_respawn` (320, 240), at rest: 05-lives-and-damage.md, Values (locked).
- `placeholder_bg` (0, 0, 0), behind the starfield: 12-art-and-audio.md, Values (guess).
- Debug overlay content and layout, unchanged: 10-ui.md, `debug_overlay`, `debug_overlay_layout`, `debug_text_font`, `debug_overlay_color` (guess).

Temporary stand-ins, approved by the Director in chat. Not in GDD, on the Director's instruction: "don't add those values to the GDD, since we are not gonna leave it like this, but use these values for now."
- Meters readout position: the HUD's second line, after where LV and GRAZE will go later (mockup: "LV 2   GRAZE 5   312 m"). For now only the meters show. Not in GDD.
- Meters readout text: default font, 16 px, white (255, 255, 255). Not in GDD.
- Meters readout format: the whole number, a space, then "m", like "312 m". Agreed in chat as part of the feature. Not in GDD.
- Starfield: 50 dots, 1–2 px each, dim blue-grey (90, 100, 140), one layer, moving at the scroll speed, wrapping from bottom to top, with the same layout every run. Not in GDD.
- When play starts, for `scroll_start_delay`, until the control card exists: the tick the ship first appears at screen center. Director's answer in chat. Not in GDD.
- In debug mode the overlay sits above the HUD on screen, and they must never overlap. Director's answer in chat. Not in GDD.

Carried over from DRA-6:
- Fall respawn with no life lost: temporary build rule, approved by the Director in chat for DRA-6. Not in GDD, on purpose, because the final design costs a life.

HUD layout, proposed by guardian, approved by Director in chat. Not in GDD (UI-01 is TBD):
- HUD left margin: 4 px, the same as the debug overlay. Not in GDD.
- HUD line spacing: 20 px (16 px font + 4 px). Not in GDD.
- Normal mode: the HUD's first line starts at y 4 and stays empty for now. The meters readout is the second line, at y 24. Not in GDD.
- Debug mode: the whole HUD starts 4 px below the debug overlay's fourth text line. Not in GDD.
- In debug mode the HUD stays moved down even when F3 hides the overlay, so the readout never jumps. Not in GDD.

## Objections
None. The request matches the GDD as updated on 2026-10-12 (91-decision-log.md rows 22–26). The two GDD differences (the meters readout as its own HUD item, and the starfield) are temporary stand-ins the Director approved, and they're listed under Fit. They break no pillar, locked decision or out-of-scope line.

## Decision log
- Director picked candidate A (camera and rising floor) from the guardian's proposal, then replaced the camera model. The GDD was updated on 2026-10-12 with the Director's approval: fixed screen and scrolling world, top line as a ceiling, scroll start delay, distance from the scroll in whole meters, levels' start distances moved to DF-05 (91-decision-log.md rows 22–26).
- Director limited the feature to the scroll and the distance counter at Level 1 speed, a HUD meters readout, and a simple starfield. Levels, lives, hazards, coins, the rest of the HUD, picture backgrounds and parallax are out.
- Director kept the DRA-6 fall stand-in: respawn at center, no life lost.
- Director approved three temporary stand-ins in chat (readout position, readout text, starfield) and said: "don't add those values to the GDD, since we are not gonna leave it like this, but use these values for now."
- Overlay overlap. Director: "Debug information appears top of the HUD of the game. Overlap is not acceptable."
- HUD numbers. Director: "use ones on your own. Overlap should not happen." The guardian proposed them in chat.
- Play start. Director: "Exactly after the Shiip appears in the center."
- Distance in the debug overlay. Director: "No, Leave it simple as before. Debug just add the extra info it already has."
- Director approved the HUD values and the final feature in the main session chat: "I accept your proposed values. I approve this." The guardian wouldn't ship on a relayed approval, so the main session applied the ship steps on the Director's direct approval.
