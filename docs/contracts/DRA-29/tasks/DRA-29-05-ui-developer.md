Feature: DRA-29
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/objects.md#presentation
Status: done
Linear: DRA-34

## Do
Build the object views: a view registry, the shared entry-warning view, and the placeholder meteorite. Needs task DRA-29-02 (`core.objects`) done first.

Everything below is exactly the `game/ui/objects/` block of `docs/contracts/systems/objects.md`, Interface, with the looks and rules in its Presentation:
- `game/ui/objects/registry.py` (new): `ObjectView`, `register_view(object_type)` (a decorator; a second view for the same type raises `ValueError`), `registered_views()`, and `render_object(surface, obj)`: the entry warning in WARNING, the registered view at `(obj.x, obj.y)` and scale 1.0 in ACTIVE, nothing in GONE. An unregistered type raises `ValueError`.
- `game/ui/objects/entry_warning.py` (new): the six constants with their sources, and `draw_entry_warning(surface, obj, view)`. The whole warning fits inside the object's own width: with `R = WARNING_SIZE_RATIO × obj.width / 2`,
  - one `pygame.SRCALPHA` image per object, side `2 × ceil(R) + 1`, center on its middle pixel, built on its first warning frame: a filled circle in `ENTRY_WARNING_GLOW` of radius `GLOW_RATIO × R`; 6 to 9 spikes from `random.Random(obj.uid)` (count, then an angle and a length per spike, in that order; length between `GLOW_RATIO × R` and `R`), each a 1 px line in the glow color from the center; then the object's own view at half size on top, centered;
  - kept in a dict keyed by `(obj.uid, obj.object_type, obj.variant)` and blitted centered on `obj.warning_center()`, rounded. `render_object` drops the entry on the first frame it draws that object ACTIVE. Never rebuilt per frame.
- `game/ui/objects/meteorite_view.py` (new): `METEORITE_COLOR = (140, 140, 140)` and `render_meteorite(surface, obj, center, scale)`, registered with `@register_view(ObjectType.METEORITE)`: a filled circle, center `(round(center[0]), round(center[1]))`, radius `round(obj.width * scale / 2)`.
- `game/ui/objects/__init__.py` (new): a package docstring and one import of `ui.objects.meteorite_view`, so the view registers when anything in `ui.objects` is imported.
- Imports pygame, stdlib and `core`. Never app. Views only draw: they never fill the background, flip, log per frame, catch an error, change an object or read the run mode or a key. Every fact comes from the object's fields and `warning_center()`; no view works out a rule.
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint`, `typecheck` and `ui` before handoff.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame; pygame.init()
from dataclasses import replace
from core.collision import Circle
from core.objects.base import ObjectType, Phase
from core.objects.spawner import Placement, spawn_object
from core.objects.tuning import ObjectTuning, ObjectTypeTuning, PlaytestSwitches, VariantTuning
from ui.objects.registry import registered_views, render_object
def v(w): return VariantTuning(width=w, height=w, hitbox=(Circle(0, 0, w / 2),))
met = ObjectTypeTuning(variants={'small': v(20), 'medium': v(28), 'big': v(40)}, default_variant='medium', speed_ratio=0.75, entry_warning_ticks=30)
tuning = ObjectTuning(objects={ObjectType.METEORITE: met}, switches=PlaytestSwitches())
def count(s, c): return sum(1 for x in range(640) for y in range(480) if tuple(s.get_at((x, y)))[:3] == c)
GLOW, GREY = (255, 220, 120), (140, 140, 140)
m = replace(spawn_object(Placement(ObjectType.METEORITE, x=160.0, variant='small'), 1, tuning), uid=1)
s = pygame.Surface((640, 480)); s.fill((0, 0, 0)); render_object(s, m)
print(sorted(t.value for t in registered_views()), m.warning_center(), tuple(s.get_at((160, 10)))[:3], count(s, GLOW) > 0, count(s, GREY))
inked = [(x, y) for x in range(640) for y in range(480) if tuple(s.get_at((x, y)))[:3] != (0, 0, 0)]
print(min(x for x, _ in inked) >= 150, max(x for x, _ in inked) <= 170, max(y for _, y in inked) <= 20)
a = replace(m, phase=Phase.ACTIVE, y=240.0)
s2 = pygame.Surface((640, 480)); s2.fill((0, 0, 0)); render_object(s2, a)
print(tuple(s2.get_at((160, 240)))[:3], count(s2, GREY), count(s2, GLOW))
"
```
It prints three lines:
- `['meteorite'] (160.0, 10.0) (140, 140, 140) True <n>`: the small meteorite's warning sits just inside the top edge at its x, with a grey half-size copy (radius 5, so `<n>` is near 80) on a warm glow (radius 7.5).
- `True True True`: every pixel of the warning lies within the small rock's 20 px width (x 150 to 170, rows 0 to 20).
- `(140, 140, 140) <m> 0`: once active, it is a grey disc of radius 10 (`<m>` near 314) at its position, with no glow.
Put the command, its output and one saved screenshot of each surface (outside the repo) in the implementation report.

## Out of scope
- The core objects and their rules (task DRA-29-02).
- Calling `render_object` each frame (`game/app/`, Integration Engineer).
- Debug outlines and labels (task DRA-29-06). The ship view (task DRA-29-04).
- Sprite art, animation, sound. Tests (task DRA-29-09).
