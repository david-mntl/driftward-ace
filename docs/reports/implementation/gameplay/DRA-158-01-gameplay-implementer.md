Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-158/tasks/DRA-158-01-gameplay-implementer.md`: add `SoundCue` and the `Run.sound_cues` field, filled in the playing tick, the last-life tick and the game-over path (Architect).
2. **Delivered:**
   - `game/core/sound_cue.py` (new): `SoundCue` enum, HIT, GRAZE, COIN. Stdlib only, no logger.
   - `game/core/run.py` (changed): field `sound_cues`; `_step_playing` starts it at `()`; `_apply_collect` adds one COIN per collected pickup; `_apply_graze` one GRAZE per paid graze; `_apply_fall` and `_apply_hit` one HIT per life lost (new helper `_with_hit_cue`); `_step_last_life` and the game-over path of `step_run` give `()`.
3. **Checks:**
   - IS_CE true (pygame-ce 2.5.8). `py_compile` clean on both files.
   - `game/tests/check.sh lint`: pass (ruff check and format). `typecheck`: pass (mypy strict, 155 files). `core`: 3483 passed, no failure.
   - Smoke run (script below, run from `game/`): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python smoke.py`. Output below shows every case of the acceptance check.
   - Determinism: ran it twice, outputs byte-identical (`cmp`).
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no hits.
4. **Assumptions:**
   - Run.md says "`hold_arrows` (through `step_run`)" gives `()` and also that a tick the flow does not step "leaves the previous cues". I read both as consistent: `hold_arrows` itself stays `replace(run, held=thrust)` (the flow's paused path keeps the cues, read only after `run_stepped`); `step_run` on a game-over run clears them. `hold_arrows` is unchanged.
   - The smoke script reuses the QA fixtures `tests/core/test_run_graze.py` and `test_coin.py` (read only, not edited). Run it from `game/` so `core` imports.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-158/tasks/DRA-158-01-gameplay-implementer.md`. Left alone: `game/core/game_flow.py` (out of scope, no change needed), `game/app/`, tuning, tests. No existing core test changed result, as `impact.md` expects.
7. **Status:** done.

## Decisions
- Cues are built by appending inside the step helpers that already own each event (collect, graze, fall, hit), so the order is the step order: COIN, GRAZE, HIT. No second pass over the run.
- `_step_playing` sets `sound_cues=()` in the `replace` that builds the tick's run, so cues never carry over from the run that came in.
- One HIT per life lost: the cue sits beside the `lives - 1` in `_apply_fall` (not protected) and `_apply_hit` (not protected, at least one touching), so a protected fall or touch adds none and several touching hazards add one. A fall tick skips step 7, so it gives one HIT. The last life gets its HIT too, appended before `_start_last_life`, after the tick's COIN and GRAZE.
- `_step_last_life` clears with `sound_cues=()` in its `replace`. The tick that ends the burst (game over) comes out `()` as well.
- No logging added: the contract's logging list has no cue line.
- No number in code. The enum values come from `audio.md`, Interface.

## Smoke script
```python
import sys
sys.path[:0] = ["/workspace/game", "/workspace/game/tests/core"]
from dataclasses import replace
import test_run_graze as g
import test_coin as c
from core.run import start_run, next_run, step_run, hold_arrows
from core.ship import Ship, Thrust

NO = Thrust()

def show(label, run):
    print(f"{label:55s} {tuple(x.name for x in run.sound_cues)}")
    return run

def place(run, *specs):
    """specs: (gap, left) per drifter index; ship back at home."""
    ds = [g.at_gap(d, gap, left=left) for d, (gap, left) in zip(run.drifters, specs)]
    ds += list(run.drifters[len(ds):])
    return replace(run, ship=g.HOME, drifters=tuple(ds))

print("start_run / next_run")
r0 = show("start_run()", start_run())
show("next_run(run)", next_run(r0))

print("coin")
run = c.run_of(c.resting(c.HOME_X, c.HOME_Y), c.coin("common"))
run = show("tick collects a coin", step_run(run, NO))
show("next tick, nothing", step_run(run, NO))

print("graze")
run = g.run_of(g.rock())
run = place(run, (g.IN, False)); run = step_run(replace(run, ship=g.HOME), NO)
show("tick enters zone", run)
run = show("tick exits zone: one graze", step_run(place(run, (g.OUT, False)), NO))
show("next tick, nothing", step_run(run, NO))
run = g.run_of(g.rock(), g.rock())
run = step_run(place(run, (g.IN, False), (g.IN, True)), NO)
run = show("tick exits two zones: two grazes", step_run(place(run, (g.OUT, False), (g.OUT, True)), NO))

print("hit")
run = g.run_of(g.rock(), g.rock())
run = show("two hazards touch, unprotected: one HIT", step_run(place(run, (g.TOUCH, False), (g.TOUCH, True)), NO))
show("next tick, nothing (protected)", step_run(run, NO))
run = g.run_of(g.rock(), invuln_ticks_left=60)
show("touch while protected", step_run(place(run, (g.TOUCH, False)), NO))

print("fall")
fall = lambda **kw: c.run_of(c.fall_ship(), **kw)
run = show("unprotected fall: one HIT", step_run(fall(), NO))
show("next tick after fall, nothing", step_run(run, NO))
show("protected fall", step_run(fall(invuln_ticks_left=60), NO))

print("coin + graze + life lost, one tick")
run = g.run_of(g.rock(), g.rock(), g.coin(50.0, 50.0), lives=5)
run = step_run(place(run, (g.IN, False), (g.OUT, True)), NO)
run = place(run, (g.OUT, False), (g.TOUCH, True))
run = replace(run, drifters=run.drifters[:2] + (replace(run.drifters[2], x=g.HOME_X, y=g.HOME_Y),))
run = show("coin, graze, HIT in that order", step_run(run, NO))
print("   lives", run.lives, "grazes", run.grazes, "coin_points", run.coin_points)

print("last life by touch")
run = g.run_of(g.rock(), lives=1)
run = show("tick loses last life by touch: HIT", step_run(place(run, (g.TOUCH, False)), NO))
nxt = step_run(run, NO)
show("last-life tick after it", nxt)
ticks = 0
while not nxt.game_over:
    nxt = step_run(nxt, NO); ticks += 1
    assert nxt.sound_cues == (), nxt.sound_cues
print(f"{'all last-life ticks to game over (%d) give' % ticks:55s} ()")
show("game-over tick", step_run(nxt, NO))

print("last life by fall")
run = show("tick loses last life by fall: HIT", step_run(c.run_of(c.fall_ship(), lives=1), NO))
show("last-life tick after it", step_run(run, NO))

print("coin + last life by touch")
run = g.run_of(g.rock(), g.coin(g.HOME_X, g.HOME_Y), lives=1)
run = show("coin + last-life touch: COIN then HIT", step_run(place(run, (g.TOUCH, False)), NO))

print("hold_arrows and a carried cue")
run = step_run(c.run_of(c.fall_ship()), NO)
show("hold_arrows keeps the cues (flow, paused)", hold_arrows(run, NO))
show("step_run next tick clears them", step_run(run, NO))
```

## Smoke output
```
start_run / next_run
start_run()                                             ()
next_run(run)                                           ()
coin
tick collects a coin                                    ('COIN',)
next tick, nothing                                      ()
graze
tick enters zone                                        ()
tick exits zone: one graze                              ('GRAZE',)
next tick, nothing                                      ()
tick exits two zones: two grazes                        ('GRAZE', 'GRAZE')
hit
two hazards touch, unprotected: one HIT                 ('HIT',)
next tick, nothing (protected)                          ()
touch while protected                                   ()
fall
unprotected fall: one HIT                               ('HIT',)
next tick after fall, nothing                           ()
protected fall                                          ()
coin + graze + life lost, one tick
coin, graze, HIT in that order                          ('COIN', 'GRAZE', 'HIT')
   lives 4 grazes 1 coin_points 50
last life by touch
tick loses last life by touch: HIT                      ('HIT',)
last-life tick after it                                 ()
all last-life ticks to game over (119) give             ()
game-over tick                                          ()
last life by fall
tick loses last life by fall: HIT                       ('HIT',)
last-life tick after it                                 ()
coin + last life by touch
coin + last-life touch: COIN then HIT                   ('COIN', 'HIT')
hold_arrows and a carried cue
hold_arrows keeps the cues (flow, paused)               ('HIT',)
step_run next tick clears them                          ()
```
