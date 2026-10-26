Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-117-02 (Linear DRA-119): build the graze rule in core, from `docs/contracts/DRA-117/tasks/DRA-117-02-gameplay-implementer.md`, by the Architect.

2. **Delivered:**
   - `game/core/graze.py` (new): `GrazeRules`, `DEFAULT_GRAZE_*`, `DEFAULT_GRAZE_RULES`, `GrazeRing`, `GrazeCheck`, `check_grazes`, `graze_popup`, `graze_ring`, `step_graze_rings`.
   - `game/core/popup.py`: `PopupKind` and `PointsPopup.kind` (last field, default COIN).
   - `game/core/run.py`: `Run.grazes`, `Run.graze_rings`, `Run.graze_rules`, the new `score`, `start_run(waves, graze_rules)`, step 3a rings, step 5b (`_apply_graze`), `drifter graze` log line, retry keeps `graze_rules`.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on the three files: clean.
   - `ruff check .` and `ruff format --check .` from `game/`: clean. `game/tests/check.sh lint`: PASS. `check.sh typecheck` (mypy strict): PASS.
   - `check.sh core`: 3160 passed, 1 failed. `check.sh ui`: 46 passed. The one core failure is not in `impact.md`'s table, see Next (item 1). No other test changed result.
   - Acceptance script (below), run twice: both outputs identical (`cmp`). It shows: case 1 OUTSIDE, INSIDE t032 to t049, SPENT on the exit tick t050, one `drifter graze` line, grazes 1, score +25, one GRAZE popup at the ship's center (320, 184) and one ring, both age 0 on that tick; the ring is gone after 15 states (age 15 drops it), the popup climbs 0.5 px a tick and is gone after 60 states. Case 2: SPENT on the touch tick, a hit (lives 2), grazes 0. Case 3 (protected) and 4 (respawn wait): no pay, OUTSIDE after the exit, no popup or ring. Case 5: score +40, ring gone after 5 states. Case 6: game over with grazes 2 and a ring on screen, retry gives grazes 0, no rings, no popups, `graze_rules` the same object (points 40, ring_ticks 60).
   - Grep of `game/core` for the banned names: 9 hits, all the substring `.wav` inside `core.waves` / `.waves` (a module and field name), no audio file, no `time.sleep`, `threading`, `asyncio`, `pygame.display/event/key` or `random.random(`. Nothing to remove.
   - Command, from `game/`: `PYTHONPATH=. SDL_VIDEODRIVER=dummy python graze_check.py` (script below, saved in the scratchpad, not in the repo).

4. **Assumptions:**
   - `check_grazes` returns the same drifter object when its state does not change, and tests touch with `current_hitbox()` before the zone, so a WARNING drifter (no hitbox, no zone) stays OUTSIDE.
   - The script builds the `Meteorite` directly (ACTIVE, entered, medium 28 px, radius 14, speed 0.375 x `TOP_SIDE_SPEED`, GDD values) instead of through `add_drifters`, to skip the 60-tick warning. The acceptance text says "builds a meteorite tuning in code"; the drifter built here carries the same numbers a tuning-built one gets.
   - Case 4 holds `held = ArrowUp` going in, so the held key is not a press and the ship keeps standing.

5. **Documentation differences:** None.

6. **Next:**
   1. Implementation Reviewer: review the task `docs/contracts/DRA-117/tasks/DRA-117-02-gameplay-implementer.md`.
   2. One existing core test fails from this task and is not in `impact.md`'s expected table: `game/tests/core/test_ufo.py::test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds` (line 1324). It compares a UFO the ship touched with an untouched twin (`replace(after, rehit_ticks_left=0, uid=0) == replace(twin, uid=0)`). The touched UFO now has `graze_state` SPENT, as `run.md` step 5b.3 says, so the whole-drifter compare differs on that one field. The behavior is right; the test needs `graze_state` taken out of the comparison. This is the case `impact.md` leaves to QA (DRA-117-05). I did not edit the test.
   3. Left alone: `game/app/` (loader and draw call), the views, tuning files, `core/drifters/`, the module docstring of `core/run.py` (it does not name grazes; no contract line asks for it).

7. **Status:** done.

## Decisions
- Update order: unchanged from DRA-62. Step 3a ages popups and rings together (in the same `replace` as the ship and scroll), then collect, then graze (5b), then fall or hit. The graze runs on the ship from step 4, before step 6 can respawn it, and with `protected` taken going into the tick (step 2).
- `may_pay = not protected and not stands`. `stands` is `waiting` after step 4, so a press tick pays (the ship is stepped) and a standing ship never does.
- `_check_one` order: not HIT or SPENT, return as is; touch (strict overlap of the current hitbox) gives SPENT and no pay; inside the zone (not off screen) gives INSIDE; was INSIDE and left gives SPENT plus pay with `may_pay`, else OUTSIDE; otherwise OUTSIDE. An off-screen drifter counts as outside, so the "dropped with the ship inside" case pays on its drop tick (step 5b.4).
- One `replace` in `_apply_graze` adds all paid grazes: `(popup,) * paid` and `(ring,) * paid` keep drifter order and put two identical popups and rings for two hazards paid on one tick. Log lines come in `check.paid` order, after the collect's lines and before the fall's.
- The retry passes `run.graze_rules` to `start_run`, so a new run keeps the values. `start_run()` and `start_run(waves)` build the old run with the GDD graze values.
- Numbers: `DEFAULT_GRAZE_POINTS` 25 (06-scoring.md, graze_points, locked); popup 60 ticks and 0.5 px per tick, ring 15 ticks, 16 to 32 px, 1 px width (06-scoring.md, graze_popup and graze_ring, guess). They equal `game/tuning/scoring.json`. Case 5 and 6 use values built in code, not a file.
- `GrazeRing.diameter` and `opacity` are the contract's formulas, a steady step per tick. At age 14 of 15 the opacity is 0.067, still above 0, and the ring drops at age 15.

## Acceptance script
```python
"""DRA-117-02 acceptance script. Run from game/: python <this file>."""

import logging
import sys
from dataclasses import replace

from core.collision import Circle
from core.drifters.base import Phase
from core.drifters.meteorite import Meteorite
from core.graze import GrazeRules
from core.ship import SHIP_H, TOP_SIDE_SPEED, Ship, Thrust
from core.world import TOP_LINE_Y
from core.run import Run, start_run, step_run

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="    log %(name)s %(message)s")
for noisy in ("core.ship", "core.scroll", "core.waves"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

UP = Thrust(up=True)
SPEED = 0.375 * TOP_SIDE_SPEED  # drifters/01-meteorite.md, speed_ratio, Level 1
SHIP_Y = TOP_LINE_Y + SHIP_H / 2  # the ship sits on the top line
SHIP_X = 320.0


def rock(x: float, y: float) -> Meteorite:
    """A medium meteorite (28 px, radius 14) falling at the Level 1 speed, already on screen."""
    return Meteorite(
        uid=1, x=x, y=y, variant="medium", width=28.0, height=28.0, speed=SPEED,
        hitbox=(Circle(0, 0, 14.0),), warning_ticks=60, phase=Phase.ACTIVE, has_entered=True,
        rehit_cooldown_ticks=180, rehit_dim=0.75,
    )


def start(x: float, **fields: object) -> Run:
    rules = fields.pop("rules", None)
    run = start_run() if rules is None else start_run(graze_rules=rules)
    ship = Ship(x=SHIP_X, y=SHIP_Y, vx=0.0, vy=0.0)
    return replace(run, ship=ship, held=UP, drifters=(rock(x, SHIP_Y - 90.0),), **fields)


def row(tick: int, run: Run, base: int) -> str:
    states = ",".join(d.graze_state.name for d in run.drifters) or "-"
    popups = " ".join(f"{p.kind.name}(x={p.x:.0f},y={p.y:.1f},age={p.age_ticks})" for p in run.popups)
    rings = " ".join(f"({r.age_ticks},d={r.diameter:.2f},o={r.opacity:.3f})" for r in run.graze_rings)
    return (f"t{tick:03d} {states:8} grazes={run.grazes} score+={run.score - base - run.scroll.meters}"
            f" lives={run.lives} popups[{popups}] rings[{rings}]")


def play(title: str, run: Run, ticks: int, thrust: Thrust = UP) -> Run:
    print(f"== {title}")
    base = run.score
    last = ""
    for tick in range(1, ticks + 1):
        run = step_run(run, thrust)
        line = row(tick, run, base)
        key = line.split(" ", 1)[1]
        ages = {p.age_ticks for p in run.popups}
        if key != last or run.graze_rings or ages & {0, 1, 30, 59} or (last and not run.popups and "GRAZE" in last):
            print(line)
        last = key
    return run


play("1 graze past the side", start(358.0), 120)
play("2 falling onto the ship: a hit", start(SHIP_X), 40)
play("3 protected on the exit tick", start(358.0, invuln_ticks_left=200), 80)
play("4 standing in the respawn wait", start(358.0, waiting=True), 80)
play("5 GrazeRules(points=40, ring_ticks=5)", start(358.0, rules=GrazeRules(points=40, ring_ticks=5)), 80)

print("== 6 game over, then a retry")
rules = GrazeRules(points=40, ring_ticks=60)
run = start(SHIP_X + 0.0, rules=rules, lives=1)
run = replace(run, grazes=2, graze_rings=(__import__("core.graze").graze.graze_ring(rules),))
for _ in range(40):
    run = step_run(run, UP)
    if run.game_over:
        break
print(f"game over: {run.game_over} grazes={run.grazes} rings={len(run.graze_rings)} score={run.score}")
run = step_run(run, Thrust())
run = step_run(run, UP)
print(f"retry: game_over={run.game_over} grazes={run.grazes} rings={len(run.graze_rings)} "
      f"popups={len(run.popups)} drifters={len(run.drifters)} rules={run.graze_rules}")
print("same rules object kept:", run.graze_rules is rules)
```

## Acceptance output
```
== 1 graze past the side
t001 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
t032 INSIDE   grazes=0 score+=0 lives=3 popups[] rings[]
    log core.run drifter graze id=1 type=meteorite
t050 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=184.0,age=0)] rings[(0,d=16.00,o=1.000)]
t051 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=183.5,age=1)] rings[(1,d=17.07,o=0.933)]
t052 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=183.0,age=2)] rings[(2,d=18.13,o=0.867)]
t053 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=182.5,age=3)] rings[(3,d=19.20,o=0.800)]
t054 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=182.0,age=4)] rings[(4,d=20.27,o=0.733)]
t055 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=181.5,age=5)] rings[(5,d=21.33,o=0.667)]
t056 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=181.0,age=6)] rings[(6,d=22.40,o=0.600)]
t057 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=180.5,age=7)] rings[(7,d=23.47,o=0.533)]
t058 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=180.0,age=8)] rings[(8,d=24.53,o=0.467)]
t059 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=179.5,age=9)] rings[(9,d=25.60,o=0.400)]
t060 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=179.0,age=10)] rings[(10,d=26.67,o=0.333)]
t061 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=178.5,age=11)] rings[(11,d=27.73,o=0.267)]
t062 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=178.0,age=12)] rings[(12,d=28.80,o=0.200)]
t063 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=177.5,age=13)] rings[(13,d=29.87,o=0.133)]
t064 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=177.0,age=14)] rings[(14,d=30.93,o=0.067)]
t065 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=176.5,age=15)] rings[]
t066 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=176.0,age=16)] rings[]
t067 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=175.5,age=17)] rings[]
t068 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=175.0,age=18)] rings[]
t069 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=174.5,age=19)] rings[]
t070 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=174.0,age=20)] rings[]
t071 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=173.5,age=21)] rings[]
t072 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=173.0,age=22)] rings[]
t073 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=172.5,age=23)] rings[]
t074 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=172.0,age=24)] rings[]
t075 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=171.5,age=25)] rings[]
t076 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=171.0,age=26)] rings[]
t077 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=170.5,age=27)] rings[]
t078 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=170.0,age=28)] rings[]
t079 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=169.5,age=29)] rings[]
t080 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=169.0,age=30)] rings[]
t081 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=168.5,age=31)] rings[]
t082 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=168.0,age=32)] rings[]
t083 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=167.5,age=33)] rings[]
t084 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=167.0,age=34)] rings[]
t085 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=166.5,age=35)] rings[]
t086 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=166.0,age=36)] rings[]
t087 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=165.5,age=37)] rings[]
t088 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=165.0,age=38)] rings[]
t089 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=164.5,age=39)] rings[]
t090 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=164.0,age=40)] rings[]
t091 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=163.5,age=41)] rings[]
t092 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=163.0,age=42)] rings[]
t093 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=162.5,age=43)] rings[]
t094 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=162.0,age=44)] rings[]
t095 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=161.5,age=45)] rings[]
t096 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=161.0,age=46)] rings[]
t097 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=160.5,age=47)] rings[]
t098 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=160.0,age=48)] rings[]
t099 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=159.5,age=49)] rings[]
t100 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=159.0,age=50)] rings[]
t101 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=158.5,age=51)] rings[]
t102 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=158.0,age=52)] rings[]
t103 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=157.5,age=53)] rings[]
t104 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=157.0,age=54)] rings[]
t105 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=156.5,age=55)] rings[]
t106 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=156.0,age=56)] rings[]
t107 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=155.5,age=57)] rings[]
t108 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=155.0,age=58)] rings[]
t109 SPENT    grazes=1 score+=25 lives=3 popups[GRAZE(x=320,y=154.5,age=59)] rings[]
t110 SPENT    grazes=1 score+=25 lives=3 popups[] rings[]
== 2 falling onto the ship: a hit
t001 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
t019 INSIDE   grazes=0 score+=0 lives=3 popups[] rings[]
    log core.run drifter touch id=1 type=meteorite effect=hit
    log core.run life lost lives=2
t025 SPENT    grazes=0 score+=0 lives=2 popups[] rings[]
== 3 protected on the exit tick
t001 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
t032 INSIDE   grazes=0 score+=0 lives=3 popups[] rings[]
t050 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
== 4 standing in the respawn wait
t001 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
t032 INSIDE   grazes=0 score+=0 lives=3 popups[] rings[]
t050 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
== 5 GrazeRules(points=40, ring_ticks=5)
t001 OUTSIDE  grazes=0 score+=0 lives=3 popups[] rings[]
t032 INSIDE   grazes=0 score+=0 lives=3 popups[] rings[]
    log core.run drifter graze id=1 type=meteorite
t050 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=184.0,age=0)] rings[(0,d=16.00,o=1.000)]
t051 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=183.5,age=1)] rings[(1,d=19.20,o=0.800)]
t052 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=183.0,age=2)] rings[(2,d=22.40,o=0.600)]
t053 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=182.5,age=3)] rings[(3,d=25.60,o=0.400)]
t054 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=182.0,age=4)] rings[(4,d=28.80,o=0.200)]
t055 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=181.5,age=5)] rings[]
t056 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=181.0,age=6)] rings[]
t057 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=180.5,age=7)] rings[]
t058 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=180.0,age=8)] rings[]
t059 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=179.5,age=9)] rings[]
t060 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=179.0,age=10)] rings[]
t061 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=178.5,age=11)] rings[]
t062 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=178.0,age=12)] rings[]
t063 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=177.5,age=13)] rings[]
t064 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=177.0,age=14)] rings[]
t065 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=176.5,age=15)] rings[]
t066 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=176.0,age=16)] rings[]
t067 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=175.5,age=17)] rings[]
t068 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=175.0,age=18)] rings[]
t069 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=174.5,age=19)] rings[]
t070 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=174.0,age=20)] rings[]
t071 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=173.5,age=21)] rings[]
t072 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=173.0,age=22)] rings[]
t073 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=172.5,age=23)] rings[]
t074 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=172.0,age=24)] rings[]
t075 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=171.5,age=25)] rings[]
t076 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=171.0,age=26)] rings[]
t077 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=170.5,age=27)] rings[]
t078 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=170.0,age=28)] rings[]
t079 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=169.5,age=29)] rings[]
t080 SPENT    grazes=1 score+=40 lives=3 popups[GRAZE(x=320,y=169.0,age=30)] rings[]
== 6 game over, then a retry
    log core.run drifter touch id=1 type=meteorite effect=hit
    log core.run life lost lives=0
    log core.run game over meters=0
game over: True grazes=2 rings=1 score=80
    log core.run new run
retry: game_over=False grazes=0 rings=0 popups=0 drifters=0 rules=GrazeRules(points=40, popup_ticks=60, popup_rise_per_tick=0.5, ring_ticks=60, ring_start_diameter=16.0, ring_end_diameter=32.0, ring_width=1)
same rules object kept: True
```
