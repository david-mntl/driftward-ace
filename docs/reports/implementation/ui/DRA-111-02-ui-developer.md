Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-111-02 (Architect): build the electric ball's placeholder view and register it. Task `docs/contracts/DRA-111/tasks/DRA-111-02-ui-developer.md`.
2. **Delivered:**
   - `game/ui/drifters/electric_ball_view.py` (new): `render_electric_ball`, the four color constants, `FIRST_RAY_DEGREES`.
   - `game/ui/drifters/__init__.py` (changed): one import line, `electric_ball_view`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `py_compile` on both files: clean.
   - From `game/`: `tests/check.sh lint`: PASS (ruff check and format). `tests/check.sh typecheck`: PASS (mypy strict, 93 files).
   - `tests/check.sh ui`: PASS, 46 tests. `tests/check.sh core`: FAIL, only `tests/core/test_collision.py` failing to collect (`KeyError: 'hitbox'` reading `electric_ball.json`). `impact.md` lists this (the "tuning file" row); DRA-111-04 clears it.
   - Draw run (script and output below): every probe line reads OK. Each color equals `dim_color` of the GDD placeholder_look color (the fill over the background is the alpha blend at `fill_opacity`).
   - Follows the state: ticks 0, 119, 120, off-screen y and re-hit dim each give the picture the contract names. A draw leaves core state unchanged: `repr(ball)` is equal before and after (last output line).
   - Grep of `game/ui/drifters/electric_ball_view.py` for sleep, threading, asyncio, pygame.display/event/key/image.load/mixer, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for `import ui`, `from ui`, `game.ui`: no hits.
   - Command: `cd game && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python <script>`. The script is below; it is not saved in the repo.
4. **Assumptions:**
   - The draw run builds the ball with `ElectricBall.born(Birth(...))` from `game/tuning/drifters/electric_ball.json` values (the app loader does not exist yet), then `dataclasses.replace` for phase, tick and y.
   - The probes sit on pygame's own pixels. A 1 px circle of radius 64 lands at offset 63 to the right of the center and 64 to the left, because pygame-ce draws a circle's right and bottom extreme one pixel short. That is always inside the hitbox circle, so rule 9 holds. The firing image follows the contract (side `2r + 1`, circle on the middle pixel), so it has the same one-pixel asymmetry.
5. **Documentation differences:** One note for the Architect, not blocking. `electric-ball/view.md` and `shared/views.md` put the `__init__.py` import after `ufo_view`. Ruff's `I` rule requires sorted order, so the line sits between `coin_view` and `fireball_view`. Proposed change: say "in sorted order" in both places. Pending approval; no document edited.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-111/tasks/DRA-111-02-ui-developer.md`. Left alone: `ui/shapes.py`, the debug overlay, `entry_warning.py`, `game/app/` (the loader is the Integration Engineer's), tests.
7. **Status:** done.

## Decisions
- Draw order is the contract's: fill and rim, outline, ball, rays. The ball covers the fill's middle so it reads while firing.
- Plain `pygame.draw.circle` and `line` plus the SRCALPHA fill image, as `view.md` gives. No `draw_shape`, since the contract names the calls and the pixel rules.
- The firing image is cached in a module dict `_IMAGES`, key `(r, rim px, alpha, fill color, rim color)` after dimming, built once, as the contract asks. It holds no game state; an entry is never stale.
- The view never decides. `pulse_fires()`, `outline_level()` (0 skips the outline) and `charge_ray_count()` (0 draws no ray) come from core. In WARNING core gives 0 and False, so the entry warning shows the purple ball alone at scale 14/16.
- Colors (170, 80, 255), (200, 150, 255), (200, 160, 255), (240, 220, 255): 10-electric-ball.md, placeholder_look. `FIRST_RAY_DEGREES` 45: 03-chain-lightning.md, ray_length, as the contract says. `MAX_ALPHA` 255 and `FULL_TURN_DEGREES` 360 are scale constants, not game values. Every other number (sizes, widths, opacity, ray count) is read from the ball.
- The view keeps its own `FIRST_RAY_DEGREES` and `FULL_TURN_DEGREES` instead of importing the chain lightning view: the contract's import list does not include it and names the constant in this module.

## Draw script
```python
import dataclasses
import json
import sys

import pygame

sys.path.insert(0, ".")
from core.collision import Circle
from core.drifters.base import Birth, Phase
from core.drifters.electric_ball import ElectricBall, ElectricBallTypeExtra, ElectricBallVariantExtra
import ui.drifters  # registers every view
from ui.drifters import electric_ball_view as v
from ui.drifters.registry import dim_color, render_drifter

pygame.init()
BG = (10, 10, 30)
t = json.load(open("tuning/drifters/electric_ball.json"))
var = t["variants"]["standard"]
extra = ElectricBallTypeExtra(
    charge_ticks=t["charge_ticks"], fire_ticks=t["fire_ticks"], charge_rays=t["charge_rays"],
    ray_length=float(t["ray_length"]), ray_width=float(t["ray_width"]),
    outline_width=float(t["outline_width"]), rim_width=float(t["rim_width"]),
    fill_opacity=t["fill_opacity"],
)
birth = Birth(
    x=320.0, y=240.0, variant="standard", width=16.0, height=16.0,
    hitbox=(Circle(0.0, 0.0, 64.0),), speed=2.5, warning_ticks=60, timer_mult=1.0,
    specialty_enabled=None, invert=False, variant_extra=ElectricBallVariantExtra(64.0),
    rehit_cooldown_ticks=60, rehit_dim=0.75, type_extra=extra, telegraph_min_ticks=1,
)
base = ElectricBall.born(birth)


def ball_at(tick, y=240.0, dim=False):
    return dataclasses.replace(
        base, phase=Phase.ACTIVE, ticks_in_phase=tick, y=y, rehit_ticks_left=30 if dim else 0
    )


def draw(obj):
    s = pygame.Surface((640, 480))
    s.fill(BG)
    render_drifter(s, obj)
    return s


def over(color, alpha):
    return tuple(round(c * alpha + b * (1 - alpha)) for c, b in zip(color, BG))


def show(label, s, dx, dy, expect):
    got = tuple(s.get_at((320 + dx, 240 + dy)))[:3]
    print(f"{label:30s} got={got} expect={expect} {'OK' if got == tuple(expect) else 'DIFF'}")


def level(label, tick, b, n_rays):
    o = ball_at(tick, dim=b < 1)
    assert o.charge_ray_count() == n_rays, o.charge_ray_count()
    s = draw(o)
    lv = o.outline_level()
    print(f"-- {label}: tick {tick}, rays {n_rays}, outline_level {lv}, brightness {o.brightness()}")
    show("ball center", s, 0, 0, dim_color(v.ELECTRIC_BALL_COLOR, b))
    show("ray 0 pixel (7,-8)", s, 7, -8, dim_color(v.ELECTRIC_CHARGE_COLOR, b))
    show("outline pixel (63,0)", s, 63, 0, dim_color(v.ELECTRIC_CHARGE_COLOR, b * lv))
    show("inside outline (62,0)", s, 62, 0, BG)
    show("outside outline (64,0)", s, 64, 0, BG)


level("charging, one ray", 0, 1.0, 1)
level("charging, every ray", 119, 1.0, 4)
level("charging, every ray, re-hit dim", 119, 0.75, 4)


def fire(label, b):
    o = ball_at(120, dim=b < 1)
    assert o.pulse_fires()
    s = draw(o)
    print(f"-- {label}: tick 120, brightness {o.brightness()}")
    fill = dim_color(v.ELECTRIC_FILL_COLOR, b)
    show("fill pixel (30,0)", s, 30, 0, over(fill, round(255 * 0.35) / 255))
    show("rim pixel (63,0)", s, 63, 0, dim_color(v.ELECTRIC_RIM_COLOR, b))
    show("rim pixel (62,0)", s, 62, 0, dim_color(v.ELECTRIC_RIM_COLOR, b))
    show("fill inside rim (61,0)", s, 61, 0, over(fill, round(255 * 0.35) / 255))
    show("ball on top (0,0)", s, 0, 0, dim_color(v.ELECTRIC_BALL_COLOR, b))
    show("outside circle (64,0)", s, 64, 0, BG)


fire("firing", 1.0)
fire("firing, re-hit dim", 0.75)

off = ball_at(120, y=-8.0)
assert not off.ball_on_screen() and off.is_firing() and not off.pulse_fires()
s = draw(off)
hits = [
    c for c in (v.ELECTRIC_FILL_COLOR, v.ELECTRIC_RIM_COLOR)
]
bad = sum(
    1 for x in range(640) for y in range(480)
    if tuple(s.get_at((x, y)))[:3] != BG and tuple(s.get_at((x, y)))[:3] != v.ELECTRIC_BALL_COLOR
)
print(f"-- firing, ball off screen: pixels that are not background or ball colour: {bad}")

warn = dataclasses.replace(base, y=-8.0)
assert warn.phase is Phase.WARNING
s = draw(warn)
cx, cy = (round(c) for c in warn.warning_center())
ball_px = tuple(s.get_at((cx, cy)))[:3]
glow_px = tuple(s.get_at((cx + 8, cy)))[:3]
colors = {tuple(s.get_at((x, y)))[:3] for x in range(640) for y in range(480)}
print(f"-- WARNING at {(cx, cy)}: centre {ball_px} expect {v.ELECTRIC_BALL_COLOR}; "
      f"glow {glow_px}")
print("   charge/fill/rim colors on surface:",
      [c in colors for c in (v.ELECTRIC_CHARGE_COLOR, v.ELECTRIC_FILL_COLOR, v.ELECTRIC_RIM_COLOR)])
print("   purple disc radius px (row of ball color at center row):",
      sum(1 for x in range(640) if tuple(s.get_at((x, cy)))[:3] == v.ELECTRIC_BALL_COLOR))
print("   cached fire images:", len(v._IMAGES))
o = ball_at(120)
before = repr(o)
draw(o)
print("core state unchanged by draw:", repr(o) == before)
```

## Draw script output
```
-- charging, one ray: tick 0, rays 1, outline_level 0.25, brightness 1.0
ball center                    got=(170, 80, 255) expect=(170, 80, 255) OK
ray 0 pixel (7,-8)             got=(200, 150, 255) expect=(200, 150, 255) OK
outline pixel (63,0)           got=(50, 38, 64) expect=(50, 38, 64) OK
inside outline (62,0)          got=(10, 10, 30) expect=(10, 10, 30) OK
outside outline (64,0)         got=(10, 10, 30) expect=(10, 10, 30) OK
-- charging, every ray: tick 119, rays 4, outline_level 1.0, brightness 1.0
ball center                    got=(170, 80, 255) expect=(170, 80, 255) OK
ray 0 pixel (7,-8)             got=(200, 150, 255) expect=(200, 150, 255) OK
outline pixel (63,0)           got=(200, 150, 255) expect=(200, 150, 255) OK
inside outline (62,0)          got=(10, 10, 30) expect=(10, 10, 30) OK
outside outline (64,0)         got=(10, 10, 30) expect=(10, 10, 30) OK
-- charging, every ray, re-hit dim: tick 119, rays 4, outline_level 1.0, brightness 0.75
ball center                    got=(128, 60, 191) expect=(128, 60, 191) OK
ray 0 pixel (7,-8)             got=(150, 113, 191) expect=(150, 113, 191) OK
outline pixel (63,0)           got=(150, 113, 191) expect=(150, 113, 191) OK
inside outline (62,0)          got=(10, 10, 30) expect=(10, 10, 30) OK
outside outline (64,0)         got=(10, 10, 30) expect=(10, 10, 30) OK
-- firing: tick 120, brightness 1.0
fill pixel (30,0)              got=(76, 62, 109) expect=(76, 62, 109) OK
rim pixel (63,0)               got=(240, 220, 255) expect=(240, 220, 255) OK
rim pixel (62,0)               got=(240, 220, 255) expect=(240, 220, 255) OK
fill inside rim (61,0)         got=(76, 62, 109) expect=(76, 62, 109) OK
ball on top (0,0)              got=(170, 80, 255) expect=(170, 80, 255) OK
outside circle (64,0)          got=(10, 10, 30) expect=(10, 10, 30) OK
-- firing, re-hit dim: tick 120, brightness 0.75
fill pixel (30,0)              got=(59, 48, 86) expect=(59, 48, 86) OK
rim pixel (63,0)               got=(180, 165, 191) expect=(180, 165, 191) OK
rim pixel (62,0)               got=(180, 165, 191) expect=(180, 165, 191) OK
fill inside rim (61,0)         got=(59, 48, 86) expect=(59, 48, 86) OK
ball on top (0,0)              got=(128, 60, 191) expect=(128, 60, 191) OK
outside circle (64,0)          got=(10, 10, 30) expect=(10, 10, 30) OK
-- firing, ball off screen: pixels that are not background or ball colour: 0
-- WARNING at (320, 12): centre (170, 80, 255) expect (170, 80, 255); glow (255, 220, 120)
   charge/fill/rim colors on surface: [False, False, False]
   purple disc radius px (row of ball color at center row): 14
   cached fire images: 2
core state unchanged by draw: True
```
