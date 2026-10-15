Feature: DRA-29
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/debug-overlay.md#presentation
Status: done
Linear: DRA-35

## Do
Add hitbox and graze outlines and object labels to the debug overlay. Needs tasks DRA-29-03 (`Run.objects`) and DRA-29-04 (`ui/shapes.py`) done first.

In `game/ui/debug_overlay.py`, from `docs/contracts/systems/debug-overlay.md`, Interface, Presentation and Impact:
- New `draw_debug_hitboxes(surface: pygame.Surface, run: Run) -> None`. In this order:
  1. every object's `graze_zone()`, outlined 1 px;
  2. the ship's `ship_hitbox(run.ship)`, outlined 1 px, whether or not the ship is visible this frame; then every object's `current_hitbox()`, outlined 1 px;
  3. one label per object: `f"{type} {variant} x {x:z.2f} y {y:z.2f} {phase}"` with `obj.object_type.value` and `obj.phase.value`, in the overlay's own cached font, antialiased. Its top-left at `(round(obj.x - obj.width / 2), round(obj.y + obj.height / 2))`, then moved just enough to lie fully on the surface (0 when the label is bigger).
  - All in `OVERLAY_COLOR`. Outlines with `ui.shapes.draw_hitbox(surface, OVERLAY_COLOR, hitbox, 1)`.
- `draw_debug_overlay` and `overlay_text_bottom` don't change at all: same signature, same pixels.
- The module docstring names the new function. Imports gain `core.run`, `core.objects.base` and `ui.shapes`. Never app. Never reads the run mode.
- The view only draws: it never fills, flips, logs per frame, catches an error or changes the run.
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint`, `typecheck` and `ui` before handoff. `tests/ui/test_hud.py` must still pass unchanged.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame; pygame.init()
from core.collision import Circle
from core.objects.base import ObjectType
from core.objects.spawner import Placement
from core.objects.tuning import ObjectTuning, ObjectTypeTuning, PlaytestSwitches, VariantTuning
from core.run import add_objects, start_run, step_run
from core.ship import Thrust
from ui.debug_overlay import draw_debug_hitboxes
def v(w): return VariantTuning(width=w, height=w, hitbox=(Circle(0, 0, w / 2),))
met = ObjectTypeTuning(variants={'small': v(20), 'medium': v(28), 'big': v(40)}, default_variant='medium', speed_ratio=0.75, entry_warning_ticks=30)
tuning = ObjectTuning(objects={ObjectType.METEORITE: met}, switches=PlaytestSwitches())
r = add_objects(start_run(), [Placement(ObjectType.METEORITE, x=320.0, y=120.0)], tuning)
for _ in range(30): r = step_run(r, Thrust())
s = pygame.Surface((640, 480)); s.fill((0, 0, 0)); draw_debug_hitboxes(s, r)
G = (0, 255, 0)
def green(x, y): return tuple(s.get_at((x, y)))[:3] == G
print(r.objects[0].phase.value, any(green(320, y) for y in range(105, 108)), any(green(320, y) for y in range(91, 94)), green(320, 120))
print(any(green(314, y) for y in range(300, 320)), any(green(x, y) for x in range(350, 640) for y in range(134, 156)))
"
```
It prints two lines:
- `active True True False`: the medium rock at (320, 120) has its hitbox outline (radius 14) and its graze outline (radius 28) in green, and its center is not filled.
- `True True`: the falling ship's bar has its green outline on column 314, and the green label sits below the rock (rows 134 to 155; it starts at x 306 and runs right, past the graze circle, which ends near x 348).
Put the command, its output and one saved screenshot (outside the repo) in the implementation report.

## Out of scope
- Calling `draw_debug_hitboxes` and the F3 toggle (`game/app/`, Integration Engineer).
- Any change to the four text lines, the two lines or `overlay_text_bottom`.
- Graze counting, hit markers, any content the contract doesn't list. Tests.
