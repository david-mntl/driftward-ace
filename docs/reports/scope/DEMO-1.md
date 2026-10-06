Verdict: ship
Feature: DEMO-1 Player ship sprite
Parent: none
No-Linear run. No Linear issue exists for this feature.

## Request
"Feature: the player's ship gets a look: one 100x100 PNG spaceship, nose up, transparent background. No animation, no game code. DONT ASK. Approve it inmediately"
## Feature
The player's ship has a look. It is one still image of a spaceship, nose pointing up, on a transparent background.
## Limits
In: one PNG, 100x100 pixels, nose up, transparent background.
Out: animation, extra frames, thrust or damage variants, game code, loading the image in the game, hitbox, any other asset.
## Player sees
Open the PNG: a spaceship with its nose up, on a transparent background, 100x100 pixels.
## Fit
- Pillars: not touched. The image changes no movement, hazard or score rule.
- Controls, camera, walls, lives, tick: not touched. Source: CLAUDE.md, Locked decisions.
- Out-of-scope list: no conflict. The image is not combat, mobile, procedural or an editor. Source: CLAUDE.md, Locked decisions.
- Tech rules: PNG is not restricted. Only audio has a format rule. Source: CLAUDE.md, Tech rules.
## Values needed
- Image size 100x100 px: not in GDD. Stated by the Director in the request.
## Objections
No objection. The feature is one static asset with no rule or code attached. It breaks no pillar, locked decision or out-of-scope line.
## Decision log
- Director asked for immediate approval, no questions: "DONT ASK. Approve it inmediately".
- Director approved the final feature in chat. Line 1 set to `Verdict: ship`.
