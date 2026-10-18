Verdict: ship
Created by: scope-guardian
Feature: DRA-62 Coin
Parent: none

## Request
"Yes! I approved it - However I want in this branch to include score and Coin" (Director, approving DRA-61 Score). The coin was already next in the order agreed in DRA-39 and DRA-56: fireball, score, coin. Floating islands later.

## Feature
A coin is a small crystal that sits still in the world and moves down only with the scroll. It enters at its placed x, from just above the top edge. It shows no warning of any kind: nothing appears before the coin itself scrolls in.

When the ship touches it, the coin is collected. The score goes up by its points and the coin disappears. At once, its points (`+50` or `+100`) pop up at the coin's center, drawn over the other drifters. The popup rises slowly up the screen and vanishes after 1 s.

An invulnerable ship collects coins too, and so does a ship that falls below the floor on the tick it touches a coin. A ship standing in the respawn wait does not. If the ship touches a coin and a hazard on the same tick, the coin pays and the hit counts.

A coin that isn't collected is removed once it is fully below the floor. It is lost.

Two variants, same size and hitbox: common (50 points, the default) and rare (100 points), which has a small glint. Coins never hurt, never pay a graze and never change with level.

In debug mode, the test spawn list can place coins at an x and y and play only them.

## Limits
In:
- Coin as in drifters/04-coin.md: variants common and rare, default common, parked, start just above the top edge at the placed x (a placement may set another spot, 07-drifters.md rule 14), no entry warning, no telegraph, the 12 × 10 box hitbox, collect on touch, invulnerable ship collects, respawn wait doesn't, coin and hit on one tick both count, removed fully below the floor, no level scaling.
- No warning of any kind for the coin. Director: "COIN SHOWS NO WARNING." Source: drifters/04-coin.md, entry_warning (locked); 07-drifters.md, rule 9.
- A coin touched on a fall tick pays. The run still tests no hit on that tick (DRA-29).
- Coin points add to the DRA-61 score: `score = meters + coin points`. Source: 06-scoring.md, Summary and rule 2.
- The popup: `+50` or `+100`, in (255, 80, 150), in the HUD's default font at 16 px. It appears the moment the coin is collected, centered on the coin's center on that tick, and is drawn over the other drifters. It rises 0.5 px per tick up the screen and doesn't move with the scroll. It vanishes after 60 ticks, with no fade.
- Placeholder look only: the split crystal with a 1 px rim, the 22 × 8 ring, and, on the rare variant only, a 2 × 2 glint. Source: drifters/04-coin.md, placeholder_look, palette, crystal_size.
- Debug overlay: the coin's hitbox outline and label, like every drifter. No graze zone, because coins have none. Source: 10-ui.md, debug_overlay; drifters/04-coin.md, graze.
- Every value in the tuning file, never hard-coded, like every drifter (precedent: DRA-56).
- Debug spawn list: coin rows set x and y, plus an optional variant. No speed. A coin-only mode. Example rows for both variants.
- Tests: the ship against both variants, the collect rules (invulnerable, respawn wait, same tick as a hit, fall tick), leaving, coin points in the score, and the popup's start, rise and end.

Out:
- Sound. AA-03 is TBD, and the Director said in DRA-39 that sound comes later.
- Final art: the swirling galaxy, the cloud, the glint animation, the shine. Placeholder only.
- Waves, wave_check and `coin_near_max`. Normal mode still spawns no drifters.
- Graze, for coins or anything else.
- A coin count on the HUD or on the Game Over box. Not in the GDD.
- Coins that move, chase or vanish on a timer. That would be a new drifter (drifters/04-coin.md, How to extend).
- Fixing the top corner warnings under the HUD (Director override in DRA-61).

## Player sees
In debug mode, with the list set to coin only: a red-purple crystal with a thin ring scrolls down from the top, with no warning before it. Fly into it: it vanishes, a pink `+50` appears where it was and rises slowly, and SCORE goes up by 50. After 1 s the `+50` is gone.

## Fit
- Pillar 1, Master the drift: fits. A coin is still in the world, so reaching it means steering the drift onto a small target, often next to a hazard. Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: fits for the coin itself. It can't hurt, so it needs no warning. Source: 07-drifters.md, rule 9; 91-decision-log.md, row 42. The popup drawn over drifters conflicts, by Director override; see Objection 1.
- Pillar 3, Risk brings reward: fits in the rules. Coins pay more than meters and always sit near hazards. Source: 06-scoring.md, Summary; 09-waves.md, rule 6. In normal play this only shows once waves place coins. Debug rows can put a coin anywhere; that is a test tool, not play.
- Locked decision 6, hazards defined by archetype: fits. Pickup archetype; common and rare change values only. Source: 07-drifters.md, rule 10.
- Locked decision 7, waves are hand-authored JSON: not touched. Debug list only.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- drifters/04-coin.md, popup ("drift up slowly"): fits. The popup rises, as the GDD says. No GDD change.
- Overlap with shipped features: none. Builds on DRA-29 (drifter base, `TouchEffect.COLLECT` reserved for coins), DRA-39 (debug spawn list, collision test structure) and DRA-61 (score). The coin itself was out of all of them.

## Values needed
From the GDD (drifters/04-coin.md unless noted; guesses unless noted):
- archetype Pickup, enters_from top, kind parked, entry_warning none, graze no: locked.
- variants: common 50 (locked), rare 100 (guess). Same size and hitbox. default_variant common.
- crystal_size 12 wide, 20 tall: a 12 × 10 rectangle with a 5 px triangle on top and one below.
- hitbox: one 12 × 10 box, centered, the crystal's rectangle only.
- popup: the points as `+50` or `+100`, where it was collected, drifting up slowly, gone after 60 ticks.
- popup_color (255, 80, 150).
- palette: lit side (200, 30, 90), shade side (70, 0, 60), galaxy core (15, 0, 20), ring and rim (255, 80, 150), rare glint (255, 220, 240).
- placeholder_look: crystal split down the middle (left lit, right shade), 1 px rim, a 1 px ring as a 22 × 8 ellipse across the middle, the rare glint at the upper left. No cloud, no animation.
- Scroll: scroll_base 1.1 px/tick (guess) × Level 1 scroll speed 1.0. 03-world-and-camera.md; 08-difficulty.md.
- Leaving: fully off screen means nothing drawn is still on screen, the ring included. 07-drifters.md, rule 12.
- coin_points add to the score. 06-scoring.md, rule 2.
- sound: TBD (AA-03). Out of this feature.

Not in GDD:
- Popup rise speed: 0.5 px/tick up the screen, about 30 px over its 60 ticks. Picked by the Director in chat from options the main session offered. Not in GDD.
- Popup start: centered on the coin's center on the tick it is collected. Approved by Director in chat. Not in GDD.
- Popup appears the moment the coin is collected. Approved by Director in chat. Not in GDD.
- Popup font and size: default font, 16 px, the HUD look from DRA-13. Color stays the GDD's popup_color. Approved by Director in chat. Not in GDD.
- Popup end: vanishes at 60 ticks, no fade. Approved by Director in chat. Not in GDD.
- Popup layer: drawn over the other drifters. Approved by Director in chat (override of Objection 1). Not in GDD.
- Rare glint: a solid 2 × 2 px square in (255, 220, 240), its top-left pixel at (3, 3) in the crystal's 12 × 20 box, inside the left half of the top triangle, clear of the 1 px rim and the ring. No animation. Proposed by guardian, approved by Director in chat. Not in GDD.
- A coin touched on a fall tick pays. Approved by Director in chat. Not in GDD.
- Debug coin row: x and y, an optional variant, no speed; a coin-only mode. Approved by Director in chat. Not in GDD; temporary stand-in.

## Objections
1. The popup can cover a hazard. Coins always sit near hazards (09-waves.md, rule 6), so the popup starts right next to one and stays for 1 s. Drawn over the drifters, the pink text can hide part of a hazard or its edge. Source: 01-vision.md, Pillar 2; 12-art-and-audio.md, rule 2 ("Hazards, warnings and coins must stand out ... at a glance"). Alternative: draw the popup under every drifter and warning, above the background, so it never hides a threat. Overridden by the Director; see Decision log.

## Decision log
- Feature shaped from drifters/04-coin.md, 06-scoring.md, 07-drifters.md, 09-waves.md and the DRA-39 notes for the coin (no warning, parked, collect, popup, no sound). Linear issue DRA-62 created in Backlog, related to DRA-61.
- Split rule: coin is its own feature with its own id, not part of DRA-61. DRA-61 shipped without it.
- Director: build score and coin on the same branch ("I want in this branch to include score and Coin").
- Scoped in a subagent run. The Director's answers below were relayed word for word by the main session.
- Director: "COIN: IMPORTANT: COIN SHOWS NO WARNING." Matches drifters/04-coin.md, entry_warning (locked). Nothing shows before the coin scrolls in.
- Q1, popup rise speed. Director: "As soon as the coin is collected." Read as when the popup appears, not a speed.
- Q2, popup font, reuse the HUD look. Director: "yes".
- Q3, vanish or fade. Director: "vanishes".
- Q4, popup start and motion. Director: "scroll down with the void and then it just vanishes". Superseded by the later answer below.
- Q5, popup layer. Director: "the pop up appears where the coin was touched and it is drawn over the other drifters." Director override of Objection 1. Guardian dissent, verbatim: "The popup can cover a hazard. Coins always sit near hazards (09-waves.md, rule 6), so the popup starts right next to one and stays for 1 s. Drawn over the drifters, the pink text can hide part of a hazard or its edge. Source: 01-vision.md, Pillar 2; 12-art-and-audio.md, rule 2 ("Hazards, warnings and coins must stand out ... at a glance"). Alternative: draw the popup under every drifter and warning, above the background, so it never hides a threat."
- The override touches a pillar and a GDD rule, not a locked decision or the out-of-scope list, so it doesn't block shipping.
- Q6, rare glint. Director: "Decided it yourself to fit". Guardian proposed the 2 × 2 glint.
- Q7, fall-tick collect. Director: "yes". A coin touched on a fall tick pays.
- Q8, debug rows. Director: "yes but it shows position x and y." A coin row sets x and y, plus an optional variant, no speed. A coin-only mode.
- Popup motion, asked as a yes/no (no rise, moves down with the scroll). Director: "No, it should rise". The GDD's "drift up slowly" stays. The proposed GDD change is dropped. Answer Q4 is superseded.
- Rise speed. Director: "0.5 px/tick", picked from options the main session offered.
- Popup start point. Director: "Coin's center", the center of the coin on the tick it is collected.
- Rare glint. Director: "Approve the 2×2 glint".
- Director approved the final feature, in answer to a question that listed the final shape: "Approved, ship it".
