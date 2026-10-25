# App, debug spawns
Part of: app
Read when: you change the debug spawn list: its file, checks, rows or timing.

## Interface

### game/app/debug_spawns.py (Integration Engineer, DRA-29; editable list DRA-39)
The debug test spawn list, a file the Director edits by hand: `game/tuning/debug_spawns.json`, to `docs/contracts/schemas/debug-spawn-list.schema.json`. A temporary stand-in kept in the scope reports, not in the GDD. Debug mode only.
```python
SPAWN_LIST_FILE: str = (
    "debug_spawns.json"  # in app.tuning.TUNING_DIR, read at call time
)
ALL_ROWS: str = "all"  # the mode that plays every row
DEFAULT_MODE: str = (
    ALL_ROWS  # scope report DRA-39, Values needed (stand-in): mode left out
)
PLAY_LIST: str = "list"    # DRA-76. play: the rows play
PLAY_WAVES: str = "waves"  # DRA-76. play: the normal waves play
DEFAULT_PLAY: str = PLAY_LIST  # DRA-76. scope report DRA-76, Not in GDD (Director): play left out
DEFAULT_LOOP_TICKS: int = (
    180  # scope report DRA-39, Values needed (stand-in, kept from DRA-29):
)
# loop_ticks left out. 3 s


@dataclass(frozen=True, slots=True)
class DebugSpawnList:
    """The checked list, ready to play."""

    play: str  # DRA-76. PLAY_LIST or PLAY_WAVES
    mode: str  # "all" or a DrifterType value
    loop_ticks: int  # ticks, >= 1
    schedule: tuple[
        tuple[int, Placement], ...
    ]  # (offset within the loop, placement) for each row in
    # play, in file order. Offsets from 0 to loop_ticks - 1


def load_debug_spawns(tuning: DrifterTuning) -> DebugSpawnList:
    ...
    # Reads and checks the file, then every row by spawning it once with spawn_drifter(placement, 1,
    # tuning). Builds the schedule for the rows in play. Raises on any problem.


def debug_spawns_due(spawn_list: DebugSpawnList, ticks: int) -> tuple[Placement, ...]:
    ...
    # () when ticks < 1. Otherwise every placement in the schedule whose offset ==
    # (ticks - 1) % spawn_list.loop_ticks, in schedule order.
    # ticks is run.scroll.ticks after the tick: 1 on the first tick of play.
```
Not a startup module: it imports `core.drifters`. DRA-39 removes `DEBUG_SPAWN_PERIOD` and `DEBUG_SPAWNS`; their three meteorite rows move into the file.

## Rules

Debug test spawn list (`app/debug_spawns.py`). Source: scope report DRA-39, Feature, Limits and Values needed (temporary stand-ins, debug mode only, not in the GDD); 15-tech-constraints.md, rule 7; 91-decision-log.md, row 38:
- **File.** `app.tuning.TUNING_DIR / SPAWN_LIST_FILE` (`game/tuning/debug_spawns.json`), read once at startup in debug mode, UTF-8, `json.loads`. The Director edits it by hand; a change shows on the next page load.
- **Checks**, by hand, every rule of `docs/contracts/schemas/debug-spawn-list.schema.json`: `rows` required, a list (may be empty); `play` (DRA-76), `mode` and `loop_ticks` optional; no unknown field anywhere; types exact, never a `bool` for a number. Each row: `type` required; `x`, `y` optional numbers (DRA-56: a row may leave out both; the drifter decides what it needs); `variant` a string matching `^[a-z][a-z0-9_]*$`; `invert` a boolean; `speed` a number > 0; `seed` (DRA-104) an `int` from 0 to `MAX_SEED` (4294967295), never a `bool`. `loop_ticks` an `int` ≥ 1.
- **Checks the schema can't express.** `mode` is `"all"` or a `DrifterType` value. Each row's `type` is a `DrifterType` value. Then every row, in or out of play, is turned into a `Placement(drifter_type, x=..., y=..., variant=..., invert=..., speed=..., seed=...)`, absent fields left at their `Placement` defaults but one: a row of a seeded drifter (`drifter_class(drifter_type).seeded`, the UFO) with no `seed` gets `placement_seed(DEBUG_SPAWNS_SOURCE, i)`, `i` its index in `rows` (DRA-104, `core.drifters.spawner`). That placement, seed included, is the one the schedule keeps, so the row flies the same path on every loop and every page load. Each is spawned once with `spawn_drifter(placement, 1, tuning)`, and the result thrown away. Whatever that raises (a missing coordinate the drifter needs, an unknown variant, an invert the drifter lacks) is raised again as `ValueError` naming the row, e.g. `tuning/debug_spawns.json: rows[2]: satellite placement needs y`, `from` the original.
- **Errors** name the file and the field like the tuning loader: `tuning/debug_spawns.json: mode must be "all" or a drifter type (meteorite, satellite)`, `tuning/debug_spawns.json: rows[0].speed must be a number > 0`. Invalid JSON and a missing file as in the tuning loader. Never a default for a missing file.
- **Defaults.** `mode` left out: `DEFAULT_MODE`, `"all"`. `loop_ticks` left out: `DEFAULT_LOOP_TICKS`, 180. A row field left out: the drifter's default (`Placement`'s None or False). `play` left out: `DEFAULT_PLAY`, `"list"` (DRA-76). Source: scope report DRA-39, Values needed; scope report DRA-76, Not in GDD.
- **What plays** (DRA-76). `play` is `"list"` or `"waves"`; anything else raises `ValueError`: `tuning/debug_spawns.json: play must be "list" or "waves"`. With `"list"` the rows play as below and the run has no waves. With `"waves"` the run plays the normal waves, as in normal mode, and no row is placed. Either way the whole file is read and checked, rows included, so switching `play` never reveals a broken row. One or the other, never both. Source: 10-ui.md, rule 7; 91-decision-log.md, row 73; scope report DRA-76, Limits ("The spawn list is kept as it is, with its modes and loop").
- **Rows in play.** With mode `"all"`, every row. With a drifter type, only the rows of that type. File order is kept.
- **Chain lightning rows** (DRA-47). `"type": "chain_lightning"` with `x` (required), and optionally `y`, `variant`, `invert` and `speed`; `"mode": "chain_lightning"` plays only those rows. No new code in this module: the type list, the mode check and the load-time spawn all go through `DrifterType` and `spawn_drifter`, so a chain lightning row without `x` fails with `chain_lightning placement needs x`. Its entry warning is settled by `add_drifters` in the run, not here. Source: scope report DRA-47, Limits.
- **Fireball rows** (DRA-56). `"type": "fireball"`, and optionally `x`, `y`, `variant`, `invert` and `speed`; `"mode": "fireball"` plays only those rows. The position picks the entry: neither `x` nor `y` is the default corner (top-left, or top-right with `invert`), `x` alone an entry along the top, `y` alone a side entry (the left wall, or the right with `invert`). So the loader no longer requires `x` or `y` in a row: that check moves to the drifter's own `start_position`, through the load-time spawn. A meteorite or chain lightning row without `x` still fails with `<type> placement needs x`, a satellite row without `y` with `satellite placement needs y`. `speed` is the Level 1 speed along the fireball's path; hazard speed × applies on top. No other new code: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. Source: scope report DRA-56, Limits and Not in GDD (speed).
- **Coin rows** (DRA-62). `"type": "coin"` with `x` (required) and optionally `y` and `variant`; `"mode": "coin"` plays only those rows. `x` alone starts it just above the top edge at that x; `x` and `y` place it at that spot, where it shows at once, with no warning. No new code in this module: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. So a coin row without `x` fails with `coin placement needs x`, one with `speed` with `coin has no speed`, and one with `invert: true` with `coin has no invert`, each named by its row as for every drifter. Source: scope report DRA-62, Limits ("coin rows set x and y, plus an optional variant. No speed. A coin-only mode") and Not in GDD (Director: "it shows position x and y"); 07-drifters.md, rule 14.
- **Floating island rows** (DRA-86). `"type": "floating_island"` with `x` (required) and optionally `y`, `variant` and `invert` (for `l_shape`, `t_shape` and `triangle` only); `"mode": "floating_island"` plays only those rows, the islands-only mode. `x` alone starts it just above the top edge at that x; `x` and `y` place it at that spot, where it shows at once, with no warning. No new code in this module: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. So a row without `x` fails with `floating_island placement needs x`, one with `speed` with `floating_island has no speed`, and one with `invert: true` on the rectangle or the box with `floating_island variant 'rectangle' has no invert` (or `'box'`), each named by its row as for every drifter. Source: scope report DRA-86, Limits ("Debug spawn list rows for islands: x and y, an optional variant and `invert`, no speed. An islands-only mode") and Not in GDD (Director approval, temporary stand-in).
- **Planet rows** (DRA-96). `"type": "planet"` with `x` (required) and optionally `y` and `variant` (only `standard` exists); `"mode": "planet"` plays only those rows, the planets-only mode. `x` alone shows its entry warning at that x against the top edge, then the planet enters from just above the top edge, its field ring touching it, as in play; `x` and `y` show the warning at that spot and the planet appears there when it ends. No new code in this module: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. So a row without `x` fails with `planet placement needs x`, one with `speed` with `planet has no speed`, and one with `invert: true` with `planet has no invert`, each named by its row as for every drifter. Source: scope report DRA-96, Limits ("Debug spawn list rows for planets: x required; y optional ... no variant, no speed. A planets-only mode") and Not in GDD (Director approval, temporary stand-in); drifters/08-planet.md, rule 1.
- **UFO rows** (DRA-104). `"type": "ufo"` with `y` (required, inside the band) and optionally `x`, `variant` (only `standard` exists), `invert`, `seed` and `speed`; `"mode": "ufo"` plays only those rows, the UFO-only mode. `y` alone shows the entry warning at that y against the left wall (the right with `invert`), then the UFO crosses from just outside it. `speed` is the Level 1 speed across the screen; hazard speed × applies on top, and the weave keeps the file's values. No `seed`: the row's default, fixed by its index. Rows may share a seed: the list is not a wave. Beyond the default seed, no new code in this module: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. So a row without `y` fails with `ufo placement needs y`, one with `y` outside the band with `ufo placement y <y> is outside its band 188 to 440`, and a `seed` on any other drifter with `<type> has no seed`, each named by its row as for every drifter. Source: scope report DRA-104, Limits and Decision log (Q1: approved by the main session for the Director, temporary stand-in, not in the GDD).
- **Electric ball rows** (DRA-111). `"type": "electric_ball"` with `x` (required) and optionally `speed`; `y`, `variant` (only `standard` exists) and `invert` (no effect) work as for every drifter. `"mode": "electric_ball"` plays only those rows, the electric-ball-only mode. `x` alone shows the entry warning at that x against the top edge, then the ball falls in from just above it. `speed` is the Level 1 speed straight down; hazard speed × applies on top, and the charge and fire keep the file's timings. No new code in this module: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. So a row without `x` fails with `electric_ball placement needs x`, and one with `seed` with `electric_ball has no seed`, each named by its row as for every drifter. The example rows are in `integration-checks/DRA-111.md`. Source: scope report DRA-111, Limits ("Debug spawn list rows for electric balls and an electric-ball-only mode, with example rows") and Decision log (approved by the main session for the Director, temporary stand-in, not in the GDD).
- **Timing.** The `n` rows in play are spread evenly over one loop: row `i` (from 0) has offset `(i × loop_ticks) // n`. `debug_spawns_due` places a row on every tick where `(run.scroll.ticks - 1) % loop_ticks` equals its offset. So the first row in play is placed on the first tick of play (`run.scroll.ticks == 1`), and the loop repeats every `loop_ticks` ticks. Rows that share an offset (more rows than ticks) are placed on the same tick, in file order. With the three DRA-29 meteorite rows in play and `loop_ticks` 180, they are placed on ticks 1, 61 and 121, then again from 181, exactly as in DRA-29. Source: scope report DRA-39, Feature ("The list loops"), Decision log (rows need only type and position); this contract, Rationale.
- The list counts the run's own ticks, so it freezes at game over and starts again with a retry.
- **Log.** One INFO line after a good load: `debug spawns loaded mode=%s rows=%d loop_ticks=%d play=%s`, with the number of rows in play and, from DRA-76, `play` at the end. INFO because it is startup. Nothing else, and nothing per tick.
- Called only in debug mode. Never in normal mode. Game rules stay the same in both modes; the list only places drifters.
- Not a wave. It has no wave clock and no level: while it plays the run has no waves, stays at Level 1, and the overlay reads `wave none`. Source: scope report DRA-39, Out; scope report DRA-76, Limits.
