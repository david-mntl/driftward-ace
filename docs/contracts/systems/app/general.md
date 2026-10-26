# App, overview
Part of: app
Read when: you want the overview of the app, or a rule that fits no area.

## Purpose

Start the game, set up logging once, read the run mode once, run the async loop on the fixed 60 Hz tick, and catch any unexpected error so the page shows the error screen instead of freezing. That includes an error raised while importing pygame, core, the views or the frame loop. Build a release package that holds only runtime files.

Before the first frame the app loads and checks, once, the tuning files (the drifter files, the playtest switches and the shared hazard values) and the wave files (every wave and the playlist), in both modes, and the debug test spawn list in debug mode only, and hands the checked values to core. It holds one `GameFlow` (`docs/contracts/systems/game-flow.md`), which holds the `Run` (`docs/contracts/systems/run.md`). After pygbag's click-to-start the menu shows; play starts when Play is picked and the ship first appears. The app reads the arrows, Enter and Space, and the page's focus, and hands them to the flow each tick. The run plays the waves (`docs/contracts/systems/waves.md`), started with one seed the app draws at startup, except in debug mode when the spawn list's `play` is `list` (the default): then the run has no waves and the test spawn list plays instead. Each tick the app calls `step_flow` once; core does the screens, the pause, the ship, the scroll at the level's speed, the drifters, the lives, the respawn wait, the waves and the level, the last life, game over and retry. After each tick it hands the run the drifters that are due, the waves' or the spawn list's, through `core.game_flow.add_flow_drifters`, which adds them only after a tick the run was stepped.

Each frame draws the starfield, the drifters (entry warnings, meteorites, satellites, chain lightnings, fireballs, coins, floating islands, planets with their field rings, UFOs and electric balls with their pulse circles) behind the ship, the coins' points popups over the drifters and behind the ship, the ship while `run.ship_visible` (the blink), in debug mode the hitbox and graze outlines, drifter labels and the debug overlay with the wave and the level (F3 toggles them), the burst during the last life, the PAUSE box while paused, the game-over screen with the final score, RETRY and MENU at game over, and the HUD with SCORE and the hearts on top. On the menu, the instructions page and the leaderboard page it draws that page alone on the background. The arrow-key log lines carry the ship's x and y. The guard removes null characters from the debug-mode detail line, so an error message holding one still shows the error screen. Source: scope reports DRA-5 to DRA-47; `docs/contracts/systems/drifters.md`.

## Interface

Import root is `game/`, as in the tests: `from app.loop import run`, `from ui.error_screen import draw_error_screen`.

### game/app/drifters/registry.py (Integration Engineer)
```python
type TuningLoader = Callable[[str, object], DrifterTypeTuning]  # (file name, parsed JSON)
def register_tuning(drifter_type: DrifterType) -> Callable[[TuningLoader], TuningLoader]: ...
    # Function decorator. ValueError when the type already has a loader.
def tuning_loader(drifter_type: DrifterType) -> TuningLoader | None: ...
    # None: the drifter's file follows drifter-tuning.schema.json.
```

### game/app/drifters/checks.py (Integration Engineer)
```python
type OwnFields = tuple[frozenset[str], ExtraBuilder]  # a drifter's own variant fields and their checker
def load_generic(name: str, data: object, own: OwnFields | None = None) -> DrifterTypeTuning: ...
    # The shared schema. `own`: the drifter's own variant fields, when its schema adds some.
# Also the shared field checks every drifter module builds on (check_fields, check_number,
# check_positive, check_integer, check_boolean, check_variant_name, check_warning_ticks,
# check_shape, check_inside, check_even_size, is_number), each raising ValueError that names
# the file and the field.
```

### game/app/drifters/<drifter>_tuning.py (Integration Engineer)
A drifter whose file has a schema of its own has one module here that registers its loader with
`@register_tuning(DrifterType.<MEMBER>)` and holds that drifter's field sets and checks. It is
imported once in `game/app/drifters/__init__.py`. Today: `satellite`, `chain_lightning`,
`fireball`, `coin`, `floating_island`, `planet`, `ufo`, `electric_ball` (DRA-111). The meteorite has none.
