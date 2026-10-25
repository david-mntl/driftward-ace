Feature: DRA-111
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Impact: docs/contracts/DRA-111/impact.md
Status: open
Linear: DRA-113

## Read in the contract
- systems/drifters/electric-ball/view.md: Interface, Presentation
- systems/drifters/electric-ball/core.md: Interface, Shown only with the ball, Charge rays, Outline level, Fires
- systems/drifters/electric-ball/rationale.md: Rationale
- systems/drifters/shared/views.md: Presentation, Brightness, Entry warning, Rules for every view

## Builds
- `game/ui/drifters/electric_ball_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-111-01

## Not in the contract
None.

## Acceptance check
From `game/`, with `SDL_VIDEODRIVER=dummy`, a script in the implementation report draws an electric ball through `render_drifter` onto blank surfaces and prints the pixel colors that `electric-ball/view.md`, Presentation names:
- charging with one ray, and with every ray: the ball at its center, a ray pixel, a pixel on the outline at each of those two levels, and the background just inside and outside the outline;
- firing: a fill pixel between the ball and the rim (the fill color at `fill_opacity` over the background), a rim pixel, the ball on top, and the background just outside the circle;
- firing with the ball off screen: no fill or rim pixel on the surface;
- during the re-hit cooldown: ball, outline, fill and rim each dimmed by `rehit_dim`;
- in WARNING through `render_drifter`: the entry warning with a small purple disc, no ray and no ring.

Every color matches drifters/10-electric-ball.md, placeholder_look, through `dim_color`. Put the script and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects until the tuning file and the QA tasks exist.

## Out of scope
- The electric ball's rules (core, task DRA-111-01); the debug overlay, `ui/shapes.py`, the entry warning and the other views.
- `game/app/` (the frame draws every drifter through `render_drifter` already), tests, art and sound.
