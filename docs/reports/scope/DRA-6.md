Verdict: ship
Created by: scope-guardian
Feature: DRA-6 Ship movement screen
Parent: none

## Request
"I want to create a first screen where the ship is gonna get the basics of the movement."

The full request is in DRA-5. This report covers the ship movement. It builds on DRA-5.

## Feature
A white 32×32 ship starts at screen center, at rest. Gravity pulls it down every tick. The arrow keys add thrust. Sideways speed bleeds off through drag, and fall speed is capped. The side walls stop the ship with no bounce. The top line stops the ship's top edge. When the ship falls fully below the floor, it reappears at screen center, at rest. In debug mode, an overlay shows the ship's x, y, vx and vy and draws the top line and the floor. F3 hides or shows the overlay.

## Limits
In:
- The ship, drawn as the placeholder rectangle.
- The start position.
- The 04-ship tick order, steps 1 to 6: thrust, gravity, drag, fall cap, move, side walls.
- Top-line stop. **Temporary**, until the camera exists: the ship's top edge can't pass y 168, and vy becomes 0 when it hits.
- Floor respawn. **Temporary**, until lives exist: fully below the floor → back to `fall_respawn` at rest. No life is lost, no feedback plays, no invulnerability.
- The debug overlay and its F3 toggle, in debug mode only.

Out: camera and auto-rise, lives, life-lost feedback, invulnerability, hazards, HUD, score, control card, thrust flame, sprite art, tuning tool and tuning file.

## Player sees
Hold Up: the ship climbs to y 168 and stops there. Let go: it falls, drops off the floor, and reappears at screen center.

## Fit
- Pillar 1, Master the drift: fits. Input only changes acceleration; drag and gravity carry the ship. Source: 04-ship.md, rules 2 and 4.
- Pillar 2, See it before it hits you: no hazards yet. Not touched.
- Pillar 3, Risk brings reward: no score yet. Not touched.
- Locked decision 1, arrow keys only: fits. F3 works only in debug mode, which isn't play. Source: 10-ui.md, rule 7.
- Locked decision 3, solid side walls, no bounce: fits. Source: 03-world-and-camera.md, rule 6.
- Locked decision 4, fixed 60 Hz tick, gravity always on, drag on x, capped fall: fits. Source: 04-ship.md.
- Locked decision 2, camera and falls costing a life: not built yet. The two temporary stand-ins replace them for this screen only. They don't change the design.
- Locked decision 8, control card: not built yet, not contradicted.

## Values needed
- ship_w, ship_h 32 × 32, placeholder_look white: 04-ship.md, Values (guess).
- gravity 0.16, thrust_side, thrust_up and thrust_down 0.42 each, drag_x 0.94: 04-ship.md, Values (guess).
- fall_cap 5.5 px/tick: 04-ship.md, Values (guess). Proposed by guardian, approved by Director in chat.
- ship_start (320, 240), at rest: 03-world-and-camera.md, Values (guess). Approved by Director in chat.
- fall_respawn (320, 240), at rest: 05-lives-and-damage.md, Values (locked).
- Top line y 168, with the ship's top edge as the point that counts: 03-world-and-camera.md, rule 2.
- Fall test, fully below the floor: 03-world-and-camera.md, rule 5.
- screen_w × screen_h 640×480: 03-world-and-camera.md, Values (guess).
- debug_overlay, debug_overlay_toggle, debug_text_font, debug_overlay_color: 10-ui.md, Values (guess). Approved by Director in chat.
- placeholder_bg (0, 0, 0): 12-art-and-audio.md, Values (guess).
- Top-line stop sets vy = 0: temporary build rule for this feature. Not in GDD, on purpose, because the final design moves the camera instead. Approved by Director in chat.
- Floor respawn with no life lost: temporary build rule for this feature. Not in GDD, on purpose, because the final design costs a life. Approved by Director in chat.

## Objections
None. The temporary stand-ins were the guardian's reshape to keep the camera (WC-04, WC-05) and lives out of this feature.

## Decision log
- Director chose fall_cap 5.5 px/tick.
- Director chose: start at `fall_respawn`, and respawn there when the ship is fully below the floor, with no life lost.
- Director chose: the top line stops the ship's top edge until the camera exists.
- Director chose the overlay content (ship x, y, vx, vy, top-line and floor lines). Shown from the first frame in debug mode, F3 toggles.
- Director approved the final feature in chat by approving the plan ("Yes, and use auto mode").
