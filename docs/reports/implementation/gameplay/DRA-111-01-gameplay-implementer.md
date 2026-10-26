Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** build the electric ball's core: the `ELECTRIC_BALL` type, `core/drifters/electric_ball.py`, the import line. Task `docs/contracts/DRA-111/tasks/DRA-111-01-gameplay-implementer.md`, from the Architect.
2. **Delivered:**
   - `game/core/drifters/base.py`: `DrifterType.ELECTRIC_BALL`, last, after `UFO`.
   - `game/core/drifters/electric_ball.py` (new): `PULSE_DRAW_MARGIN`, `ElectricBallVariantExtra`, `ElectricBallTypeExtra`, `electric_ball_hitbox`, `check_electric_ball_variant`, `ElectricBall`, at the contract's names and signatures.
   - `game/core/drifters/__init__.py`: one import line, `electric_ball`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on the three files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `typecheck`: PASS (mypy strict, 92 files).
   - `game/tests/check.sh core`: 6 failed, 3130 passed. `ui`: 1 failed, 45 passed. Every failure is in `impact.md`'s table for DRA-111-01: `test_collision.py::...[electric_ball-None]` (1), `test_wave_files.py` (the 4 bad-placement-type cases and the type-list test: 5), `test_drifter_registry.py::test_drifter_lists_match_everywhere` (1). No other test changed result.
   - Acceptance script below, run from `game/`; its output is below too. Two runs wrote byte-identical output (`cmp`).
   - Grep of `game/core/` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|random.random(|.mp3|.wav`: hits only in `core/ruff.toml` (the ban messages) and in `core/run.py`, `core/wave_files.py` (`core.waves` matches `.wav`). None in code I wrote.
   - Command (script saved outside the repo, in the session scratchpad; the same text is below):
     `cd game && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python3 <script> > out.txt`
4. **Assumptions:**
   - The import line sits between `coin` and `fireball`, not after `ufo` as the contract's Interface says: `ruff check` (isort) fails on any other order and a `noqa` is not allowed.
   - `PULSE_DRAW_MARGIN` is 1.5, the fireball's `DRAW_MARGIN`, as the contract says it is.
   - "At and above half the ball" for `check_electric_ball_variant`: I print 7 and 8 (refused) and 8.5 and 64 (accepted), since the rule is `pulse_radius > ball_size / 2`.
   - The acceptance script's rows are run-length compressed: one row per run of states whose values differ only in `y`; `hitbox` prints as the circle's radius, checked to be centered on the ball. Every state is stepped.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-111/tasks/DRA-111-01-gameplay-implementer.md`. Left alone: the view (DRA-111-02), `game/app/` loader, the tuning file, debug rows, tests. At Level 1 with x only the ball fires once and is dropped mid-fire at tick 262 (first state fully below the floor), as the rationale says; it never reaches a second charge. Scenario 2 shows the full cycles.
7. **Status:** done.

## Decisions
- Update order: the contract fixes it (`y += speed`, `ticks_in_phase + 1` while ACTIVE; `tick_warning` in WARNING). No physics beyond that.
- `born` checks in the contract's order: specialty, variant extra, type extra. `invert` is read from nothing, so the base's refusal is overridden by simply not calling it (the chain lightning's `born` does the same).
- The seed refusal comes from the spawner's `_check_seed` (`seeded` stays False); no code in the ball.
- `drawn_parts` uses `max(pulse_radius, width / 2 + ray_length) + PULSE_DRAW_MARGIN` as the pulse box's half side, so the rays and the circle are both inside it.
- `outline_level()` is the ray count over `charge_rays`, so it steps on the same ticks as the rays. Source: electric-ball/core.md, Outline level.
- Numbers: none in code. Charge, fire, rays, widths, opacity, radius and size come through `Birth`; the one constant, `PULSE_DRAW_MARGIN`, is the contract's non-game value.
- `log = logging.getLogger(__name__)` is present (`game/CONTEXT.md` rule) and unused: the contract says the module logs nothing.

## Acceptance script and output

The script builds the tuning in code from the GDD values (10-electric-ball.md, Values; 07-drifters.md, entry_warning_ticks; 03-chain-lightning.md, charge_rays and ray_length), then spawns through `spawn_drifter`, the way the run does.

```python
"""Electric ball acceptance script. Run from game/: python <this file>."""

from collections.abc import Callable

import core.drifters  # imports every drifter, so each one registers
from core.collision import Circle
from core.drifters.base import Drifter, DrifterType, TickContext, VariantExtra
from core.drifters.electric_ball import (
    ElectricBall,
    ElectricBallTypeExtra,
    ElectricBallVariantExtra,
    check_electric_ball_variant,
    electric_ball_hitbox,
)
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.ship import spawn

# GDD drifters/10-electric-ball.md, Values; 07-drifters.md, Values (entry_warning_ticks);
# drifters/03-chain-lightning.md, Values (charge_rays, ray_length); placeholder_look (widths).
BALL_SIZE = 16.0
PULSE_RADIUS = 64.0


def build_tuning(
    charge_ticks: int = 120,
    variant_extra: VariantExtra | None = ElectricBallVariantExtra(pulse_radius=PULSE_RADIUS),
    type_extra: ElectricBallTypeExtra | None = None,
) -> DrifterTuning:
    """Build the electric ball's tuning the way app.tuning does (after the variant check)."""
    check_electric_ball_variant(BALL_SIZE, PULSE_RADIUS)
    if type_extra is None:
        type_extra = ElectricBallTypeExtra(
            charge_ticks=charge_ticks,
            fire_ticks=120,
            charge_rays=4,
            ray_length=6.0,
            ray_width=1.0,
            outline_width=1.0,
            rim_width=2.0,
            fill_opacity=0.35,
        )
    variant = VariantTuning(
        width=BALL_SIZE,
        height=BALL_SIZE,
        hitbox=electric_ball_hitbox(PULSE_RADIUS),
        extra=variant_extra,
    )
    return DrifterTuning(
        drifters={
            DrifterType.ELECTRIC_BALL: DrifterTypeTuning(
                variants={"standard": variant},
                default_variant="standard",
                speed_ratio=0.375,
                entry_warning_ticks=60,
                extra=type_extra,
            )
        },
        switches=PlaytestSwitches(),
    )


def hitbox_text(d: ElectricBall) -> str:
    """The current hitbox: '()' or the circle's radius, with a check it is centered on the ball."""
    hitbox = d.current_hitbox()
    if not hitbox:
        return "()"
    (circle,) = hitbox
    assert isinstance(circle, Circle) and (circle.cx, circle.cy) == (d.x, d.y)
    return f"Circle(r={circle.r:g}) at the ball"


def state_key(d: ElectricBall) -> tuple[object, ...]:
    """Everything printed but y."""
    return (
        d.phase.value,
        d.is_charging(),
        d.is_firing(),
        d.ball_on_screen(),
        d.pulse_fires(),
        d.charge_ray_count(),
        d.outline_level(),
        hitbox_text(d),
    )


def fmt(key: tuple[object, ...]) -> str:
    phase, charging, firing, on, fires, rays, outline, hb = key
    return (
        f"phase={phase:7} charging={charging!s:5} firing={firing!s:5} on_screen={on!s:5} "
        f"pulse_fires={fires!s:5} rays={rays} outline={outline:.2f} hitbox={hb}"
    )


def run_states(d: Drifter, stop: Callable[[ElectricBall, int], bool]) -> None:
    """Step like the run does (update, then mark_entered, then the leaving test).

    Prints one row per run of states with identical values but y; `t` is the tick after birth.
    """
    ctx = TickContext(ship=spawn())
    assert isinstance(d, ElectricBall)
    t = 0
    rows: list[tuple[int, int, float, float, tuple[object, ...]]] = []
    start_t, start_y, last_t, last_y, key = 0, d.y, 0, d.y, state_key(d)
    note = ""
    while True:
        d = d.update(ctx).mark_entered()
        t += 1
        if d.is_off_screen():
            rows.append((start_t, last_t, start_y, last_y, key))
            rows.append((t, t, d.y, d.y, state_key(d)))
            note = f"  tick {t}: is_off_screen() True, the run drops it; y={d.y:.3f}"
            break
        if state_key(d) != key:
            rows.append((start_t, last_t, start_y, last_y, key))
            start_t, start_y, key = t, d.y, state_key(d)
        last_t, last_y = t, d.y
        if stop(d, t):
            rows.append((start_t, last_t, start_y, last_y, key))
            note = f"  stopped at tick {t}"
            break
    for a, b, ya, yb, k in rows:
        span = f"t={a}" if a == b else f"t={a}..{b}"
        ys = f"y={ya:.3f}" if a == b else f"y={ya:.3f}..{yb:.3f}"
        print(f"  {span:12} {ys:24} {fmt(k)}")
    print(note)


def birth(label: str, placement: Placement, level: int, tuning: DrifterTuning) -> ElectricBall:
    d = spawn_drifter(placement, level, tuning)
    assert isinstance(d, ElectricBall)
    print(
        f"{label}: x={d.x} y={d.y} speed={d.speed:.4f} warning={d.warning_ticks} "
        f"charge_ticks={d.charge_ticks} fire_ticks={d.fire_ticks}"
    )
    return d


def refusal(label: str, call: Callable[[], object]) -> None:
    try:
        call()
    except ValueError as err:
        print(f"{label}: ValueError({err})")
    else:
        print(f"{label}: accepted, no error")


def main() -> None:
    tuning = build_tuning()

    print("== 1. Level 1, x only, to the drop ==")
    d = birth("born", Placement(DrifterType.ELECTRIC_BALL, x=240.0), 1, tuning)
    run_states(d, lambda _d, _t: False)

    print("== 2. Level 1, y=300, speed 0.05, two cycles ==")
    d = birth("born", Placement(DrifterType.ELECTRIC_BALL, x=240.0, y=300.0, speed=0.05), 1, tuning)
    cycle = d.charge_ticks + d.fire_ticks
    warning = d.warning_ticks
    run_states(d, lambda _d, t: t >= warning + 2 * cycle + 1)

    print("== 3a. Level 8 (charge 120 x 0.70 = 84, fire 120) ==")
    d = birth("born", Placement(DrifterType.ELECTRIC_BALL, x=240.0, y=300.0, speed=0.05), 8, tuning)
    cycle = d.charge_ticks + d.fire_ticks
    run_states(d, lambda _d, t: t >= d.warning_ticks + cycle + 1)

    print("== 3b. tuning charge 30 at Level 8: the floor (telegraph_min 45) applies ==")
    low = build_tuning(charge_ticks=30)
    d = birth("born", Placement(DrifterType.ELECTRIC_BALL, x=240.0, y=300.0, speed=0.05), 8, low)
    cycle = d.charge_ticks + d.fire_ticks
    run_states(d, lambda _d, t: t >= d.warning_ticks + cycle + 1)

    print("== 4. refusals ==")
    ball = Placement(DrifterType.ELECTRIC_BALL, x=240.0)
    refusal("no x", lambda: spawn_drifter(Placement(DrifterType.ELECTRIC_BALL), 1, tuning))
    refusal(
        "specialty",
        lambda: spawn_drifter(Placement(DrifterType.ELECTRIC_BALL, x=240.0, specialty_enabled=True), 1, tuning),
    )
    refusal(
        "seed",
        lambda: spawn_drifter(Placement(DrifterType.ELECTRIC_BALL, x=240.0, seed=7), 1, tuning),
    )
    refusal(
        "wrong variant extra",
        lambda: spawn_drifter(ball, 1, build_tuning(variant_extra=VariantExtra())),
    )
    refusal(
        "no variant extra",
        lambda: spawn_drifter(ball, 1, build_tuning(variant_extra=None)),
    )
    refusal(
        "wrong type extra",
        lambda: spawn_drifter(
            ball,
            1,
            DrifterTuning(
                drifters={
                    DrifterType.ELECTRIC_BALL: DrifterTypeTuning(
                        variants=tuning.drifters[DrifterType.ELECTRIC_BALL].variants,
                        default_variant="standard",
                        speed_ratio=0.375,
                        entry_warning_ticks=60,
                        extra=None,
                    )
                },
                switches=PlaytestSwitches(),
            ),
        ),
    )
    for radius in (7.0, 8.0, 8.5, 64.0):
        refusal(
            f"check_electric_ball_variant(16, {radius:g})",
            lambda r=radius: check_electric_ball_variant(16.0, r) or "accepted",
        )

    print("== 5. invert prints the same states ==")
    rows: dict[bool, list[tuple[object, ...]]] = {}
    for invert in (False, True):
        d = spawn_drifter(
            Placement(DrifterType.ELECTRIC_BALL, x=240.0, y=300.0, speed=0.05, invert=invert),
            1,
            tuning,
        )
        ctx = TickContext(ship=spawn())
        seq: list[tuple[object, ...]] = []
        for _ in range(60 + 2 * 240 + 1):
            seq.append((d.x, d.y, state_key(d)))
            d = d.update(ctx)
        rows[invert] = seq
    print(f"  states compared: {len(rows[False])}, identical: {rows[False] == rows[True]}")


main()
```

Output:

```text
== 1. Level 1, x only, to the drop ==
born: x=240.0 y=-8.0 speed=2.4675 warning=60 charge_ticks=120 fire_ticks=120
  t=0..59      y=-8.000..-8.000         phase=warning charging=False firing=False on_screen=False pulse_fires=False rays=0 outline=0.00 hitbox=()
  t=60         y=-8.000                 phase=active  charging=True  firing=False on_screen=False pulse_fires=False rays=0 outline=0.00 hitbox=()
  t=61..89     y=-5.533..63.557         phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  t=90..119    y=66.025..137.583        phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=2 outline=0.50 hitbox=()
  t=120..149   y=140.050..211.608       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=3 outline=0.75 hitbox=()
  t=150..179   y=214.075..285.632       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=4 outline=1.00 hitbox=()
  t=180..261   y=288.100..487.967       phase=active  charging=False firing=True  on_screen=True  pulse_fires=True  rays=0 outline=0.00 hitbox=Circle(r=64) at the ball
  t=262        y=490.435                phase=active  charging=False firing=True  on_screen=False pulse_fires=False rays=0 outline=0.00 hitbox=()
  tick 262: is_off_screen() True, the run drops it; y=490.435
== 2. Level 1, y=300, speed 0.05, two cycles ==
born: x=240.0 y=300.0 speed=0.0500 warning=60 charge_ticks=120 fire_ticks=120
  t=0..59      y=300.000..300.000       phase=warning charging=False firing=False on_screen=True  pulse_fires=False rays=0 outline=0.00 hitbox=()
  t=60..89     y=300.000..301.450       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  t=90..119    y=301.500..302.950       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=2 outline=0.50 hitbox=()
  t=120..149   y=303.000..304.450       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=3 outline=0.75 hitbox=()
  t=150..179   y=304.500..305.950       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=4 outline=1.00 hitbox=()
  t=180..299   y=306.000..311.950       phase=active  charging=False firing=True  on_screen=True  pulse_fires=True  rays=0 outline=0.00 hitbox=Circle(r=64) at the ball
  t=300..329   y=312.000..313.450       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  t=330..359   y=313.500..314.950       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=2 outline=0.50 hitbox=()
  t=360..389   y=315.000..316.450       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=3 outline=0.75 hitbox=()
  t=390..419   y=316.500..317.950       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=4 outline=1.00 hitbox=()
  t=420..539   y=318.000..323.950       phase=active  charging=False firing=True  on_screen=True  pulse_fires=True  rays=0 outline=0.00 hitbox=Circle(r=64) at the ball
  t=540..541   y=324.000..324.050       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  stopped at tick 541
== 3a. Level 8 (charge 120 x 0.70 = 84, fire 120) ==
born: x=240.0 y=300.0 speed=0.0710 warning=60 charge_ticks=84 fire_ticks=120
  t=0..59      y=300.000..300.000       phase=warning charging=False firing=False on_screen=True  pulse_fires=False rays=0 outline=0.00 hitbox=()
  t=60..80     y=300.000..301.420       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  t=81..101    y=301.491..302.911       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=2 outline=0.50 hitbox=()
  t=102..122   y=302.982..304.402       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=3 outline=0.75 hitbox=()
  t=123..143   y=304.473..305.893       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=4 outline=1.00 hitbox=()
  t=144..263   y=305.964..314.413       phase=active  charging=False firing=True  on_screen=True  pulse_fires=True  rays=0 outline=0.00 hitbox=Circle(r=64) at the ball
  t=264..265   y=314.484..314.555       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  stopped at tick 265
== 3b. tuning charge 30 at Level 8: the floor (telegraph_min 45) applies ==
born: x=240.0 y=300.0 speed=0.0710 warning=60 charge_ticks=45 fire_ticks=120
  t=0..59      y=300.000..300.000       phase=warning charging=False firing=False on_screen=True  pulse_fires=False rays=0 outline=0.00 hitbox=()
  t=60..71     y=300.000..300.781       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  t=72..82     y=300.852..301.562       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=2 outline=0.50 hitbox=()
  t=83..93     y=301.633..302.343       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=3 outline=0.75 hitbox=()
  t=94..104    y=302.414..303.124       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=4 outline=1.00 hitbox=()
  t=105..224   y=303.195..311.644       phase=active  charging=False firing=True  on_screen=True  pulse_fires=True  rays=0 outline=0.00 hitbox=Circle(r=64) at the ball
  t=225..226   y=311.715..311.786       phase=active  charging=True  firing=False on_screen=True  pulse_fires=False rays=1 outline=0.25 hitbox=()
  stopped at tick 226
== 4. refusals ==
no x: ValueError(electric_ball placement needs x)
specialty: ValueError(electric_ball has no specialty)
seed: ValueError(electric_ball has no seed)
wrong variant extra: ValueError(electric_ball variant 'standard' has no pulse_radius)
no variant extra: ValueError(electric_ball variant 'standard' has no pulse_radius)
wrong type extra: ValueError(electric_ball tuning has no type values)
check_electric_ball_variant(16, 7): ValueError(pulse_radius must be more than ball_size / 2 (7 <= 8))
check_electric_ball_variant(16, 8): ValueError(pulse_radius must be more than ball_size / 2 (8 <= 8))
check_electric_ball_variant(16, 8.5): accepted, no error
check_electric_ball_variant(16, 64): accepted, no error
== 5. invert prints the same states ==
  states compared: 541, identical: True
```
