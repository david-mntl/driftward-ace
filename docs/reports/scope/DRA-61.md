Verdict: ship
Created by: scope-guardian
Feature: DRA-61 Score
Parent: none

## Request
"Score, then coin." (Director, picking the next drifter feature after DRA-56. The order agreed in DRA-39 and DRA-56: fireball, then score, then coin. Floating islands later.)

## Feature
Each run keeps a score. Score is the meters flown plus the points from coins. No coin exists yet, so for now the score equals the meters flown. It starts at 0 when a run starts and never goes down. It stops at game over and goes back to 0 on retry.

The HUD shows the score at the top left, on the line kept for it since DRA-13, in normal and debug mode. It reads like `SCORE 1 234 567`. SCORE replaces the `312 m` meters readout, which goes away.

The Game Over box shows the final score.

## Limits
In:
- Score in the run, as one number: `score = meters + coin points`. Coin points stay 0 until the coin feature adds them. Leave room for coins; don't build them. Source: 06-scoring.md, Summary; scope report DRA-39, Decision log ("score = meters + coins for now").
- Meters as they are now: whole meters, rounded down, 1 point per meter. Source: 06-scoring.md, rule 1, points_per_meter, meters_rounding.
- Score 0 at run start and on retry. It freezes at game over with everything else. Source: 02-game-flow.md, rules 3, 5 and 6; 91-decision-log.md, row 30.
- SCORE on HUD line 1, top left, in both modes. Source: 10-ui.md, hud_score (locked), rule 2; systems/hud.md (line 1 kept for SCORE).
- Format: `SCORE`, one space, then the whole number with its digits in groups of three, split by a single space: `SCORE 0`, `SCORE 999`, `SCORE 1 234`, `SCORE 1 234 567`. No leading zeros. No digit limit.
- The SCORE text uses the DRA-13 HUD look: default font, 16 px, white (255, 255, 255).
- The meters readout (`312 m`, HUD line 2) is removed. The meters are still counted; only the readout goes. HUD line 2 stays free for LV and GRAZE later (10-ui.md, hud_level_grazes).
- The final score on the Game Over box. Text and place are left to the design, since the box is redesigned later.
- Tests for the score rule, the SCORE line, the removed readout and the score on the Game Over box.

Out:
- Fixing the top corner warnings under the HUD. Director override of Objection 2; see Decision log. The top-left SCORE and the top-right hearts both stay drawn over corner warnings for now.
- Grazes. They don't pay yet. SC-02 and SC-04 are still open.
- Coins and coin points. The coin is its own feature (DRA-62), built next on the same branch.
- LV and GRAZE on the HUD. Level is always 1 until DF-05 is answered, and grazes don't pay.
- BEST, saves, name entry. Source: 06-scoring.md, rule 7; 10-ui.md, hud_best; FL-03.
- Score popups, sound, any new debug overlay content.
- Any change to how meters are counted.
- A redesign of the Game Over box (UI-04).

## Player sees
Play a run: `SCORE 0` at the top left, no `m` readout, climbing as the world scrolls. At game over the box shows the final score. After a retry it reads `SCORE 0` again.

## Fit
- Pillar 1, Master the drift: not touched. No movement change. Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: conflicts, by Director override. SCORE at the top left can hide the default fireball's corner warning. See Objection 2. Source: 10-ui.md, rule 1; docs/TODO.md.
- Pillar 3, Risk brings reward: not met by this feature alone. Score equals meters until coins pay. The Director accepted this. See Objection 1. Source: 01-vision.md, Pillars; 06-scoring.md, Summary.
- Locked decision 9, saves: not touched. No BEST, no save. Source: 01-vision.md, Locked decisions.
- Out-of-scope list: not touched. No online leaderboard. Source: 01-vision.md, Out of scope.
- 06-scoring.md formula includes `25 × grazes`. This feature builds it without grazes. That is a deferral the Director chose in DRA-39 and confirmed here, not a GDD change.
- 10-ui.md, rule 2 lists no separate meters item. Removing the DRA-13 readout matches it.
- Overlap with shipped features: none. DRA-13 shipped the meters count and readout, DRA-23 the Game Over box. Neither has a score. The score reads the meters DRA-13 already counts.

## Values needed
From the GDD:
- Score formula `meters + coin points + 25 × grazes`. Built here as `meters + coin points`. 06-scoring.md, Summary.
- points_per_meter 1: 06-scoring.md (locked).
- meters_rounding whole meters, rounded down: 06-scoring.md (locked).
- px_per_meter 10: 03-world-and-camera.md (locked).
- Score 0 at run start and on retry: 02-game-flow.md, rule 3; 91-decision-log.md, row 30.
- hud_score top left: 10-ui.md (locked).
- Game over shows the final score: 02-game-flow.md, rule 5.

Not in GDD:
- SCORE format: label `SCORE`, one space, the whole number, groups of three split by a single space, no leading zeros. The label comes from the 10-ui.md mockup; the separator is the Director's. Proposed by guardian, approved by Director in chat. Not in GDD.
- SCORE look: default font, 16 px, white (255, 255, 255), reused from DRA-13. Proposed by guardian, approved by Director in chat. Not in GDD (UI-01 is TBD).
- Meters readout removed, SCORE replaces it. Approved by Director in chat. Not in GDD.
- Max score digits: missing, not in GDD (UI-01). The Director chose to ship without it: "score should be able to be infinite".
- Final score on the Game Over box, its text and its place: missing, not in GDD (UI-04). The Director chose to ship without them: "Wherever".
- HUD margins near the top corner warnings: missing, not in GDD (UI-01). Not fixed in this feature (Director override).

Out of this feature, listed so nobody builds them: coin_points (common 50 locked, rare 100 guess), graze_points 25, graze_margin 14, graze_share_target 20–30%.

## Objections
1. Score equals meters until coins ship. Pillar 3 says going for the risks must always earn more than just surviving. With no coins and no grazes, nothing pays for risk. Source: 01-vision.md, Pillar 3; 06-scoring.md, Summary. Alternative: keep this cut as a step and ship the coin straight after it, as planned. Resolved: the Director accepted it ("Yes"), and the coin follows on the same branch.
2. SCORE at the top left will hide a warning. The default fireball enters at the top-left corner. Its warning sits at about (12, 12), the mirror of the top-right one at (628, 12) in docs/TODO.md. SCORE starts at (4, 4), and the HUD draws on top of everything. The same clash already exists at the top right with the hearts (docs/TODO.md; DRA-56 integration report, Observation 1). Source: 10-ui.md, rule 1 ("never ... hides a warning"); 01-vision.md, Pillar 2. Alternative: fix both top corners in this feature. Overridden by the Director ("No"). See Decision log.

## Decision log
- Feature shaped from 06-scoring.md, 10-ui.md, 02-game-flow.md and the Director's DRA-39 answer "score = meters + coins for now". Linear issue DRA-61 created in Backlog.
- Order kept: score, then coin. Floating islands later. Grazes after the coin, once SC-02 and SC-04 are answered.
- Board sync: DRA-56 set to Done. All four sub-issues (DRA-57 to DRA-60) were Done and docs/reports/integration/DRA-56.md says `Verdict: pass`.
- Scoped in a subagent run. The Director's answers below were relayed word for word by the main session.
- Meters readout. Director asked back: "You mean removing meters and changing it for score?" Asked whether SCORE replaces the `312 m` readout or both show, the Director chose: "SCORE replaces it".
- Format. Director: "lets do thousand separators". Asked which separator, the Director chose: "Space: 1 234 567".
- Look. Reuse the DRA-13 HUD stand-in: "yes".
- Max digits. Director: "Leave it as missing - score should be able to be infinite, right?" Listed as missing. No digit limit in this feature.
- Game Over box. Director: "Ok for now. Wherever - we are gonna redesign the game ove box later". The final score is in; its text and place are missing.
- Objection 1. Accept score = meters until the coin ships: "Yes".
- Grazes. Director: "Yes they are out".
- Director override of Objection 2. Asked whether to fix the corner warnings in this feature, the Director said: "No". Guardian dissent, verbatim: "SCORE at the top left will hide a warning. The default fireball enters at the top-left corner. Its warning sits at about (12, 12), the mirror of the top-right one at (628, 12) in docs/TODO.md. SCORE starts at (4, 4), and the HUD draws on top of everything. The same clash already exists at the top right with the hearts (docs/TODO.md; DRA-56 integration report, Observation 1). Source: 10-ui.md, rule 1 ("never ... hides a warning"); 01-vision.md, Pillar 2. Alternative: fix both top corners in this feature."
- The override touches a pillar and a GDD rule, not a locked decision or the out-of-scope list, so it can ship. 10-ui.md rule 1 is unchanged and stays the target.
- Director approved the final feature, in answer to a question that listed the full final shape and every not-in-GDD value: "Yes! I approved it - However I want in this branch to include score and Coin".
- Coin is its own feature (split rule): DRA-62, related to DRA-61, `Verdict: revising`. Same branch as score, at the Director's request. DRA-61 doesn't wait for it.
