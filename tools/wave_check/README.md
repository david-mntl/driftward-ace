# wave_check

Tests a wave against the GDD rules ([09-waves.md](../../docs/design/gdd/09-waves.md), rule 7) by running the game's own physics headless. It reads the game and never changes it. The Director owns `config.json`.

**Part 1 is built:** placement sanity, telegraph, coin near a hazard, seam. The bot checks (zero-hit path, gap) are part 2. They show as SKIP, so a part 1 pass is not the full pass.

## Run

```
python tools/wave_check/wave_check.py --wave game/waves/l1_a.json   # one wave, always runs
python tools/wave_check/wave_check.py --changed                     # only waves git sees as changed or new
python tools/wave_check/wave_check.py --changed --base origin/main  # only waves changed since a ref (CI)
python tools/wave_check/wave_check.py --all                         # every wave; fresh passes are skipped
```

`--changed` checks nothing else: if no wave changed it says so and exits 0. It reads git, and if git cannot answer it exits 2, so a broken git never reads as "nothing changed". A tuning change does not count as a changed wave: use `--all` for that.

Options: `--level N` (repeatable, replaces the config levels), `--force` (ignore remembered passes), `--no-record` (do not write `passes.json`), `--json` (machine-readable report), `--config FILE`, `--base REF` (with `--changed` only).

Exit code: 0 all passed, 1 a check failed, 2 a usage, config or game file error.

## What it checks

Each drifter is played alone with the game's physics (ship held at the start spot, world scrolling at the level's speed). The tracks are lined up by trigger tick, so two drifters can be compared at the same moment.

| Check | Fails when |
|---|---|
| placement | a drifter never enters the screen, or a hazard turns active on top of the ship at a start spot (left, center, right) |
| telegraph | a telegraph is under `telegraph_min` at the tested level. Only the chain lightning charge is a telegraph (an entry warning is not). It compares the charge before the game's own floor, because the game clamps it and would hide a bad tuning value. |
| coin_near | a coin never comes within `coin_near_ship_widths` x 32 px (96) of a hazard's hitbox while both are on screen |
| seam | a hazard is on screen in the wave's first `seam_clear_px` (120). An entry warning counts as on screen. The end of a wave is not checked: `extra_rest_ticks` covers it. |
| gap, bot | part 2 |
| lava, per-drifter notes | not in the game yet / no extra notes for the types in the game |

Every finding names the tick (counted from the wave's start), the scroll distance in px, the position and the drifters involved. A coin that fails also names the nearest hazard.

The coin check grows the coin's hitbox by the limit and tests for overlap, so near a box's corner it is a little generous (square, not round).

## Config (`config.json`)

| Key | Meaning |
|---|---|
| `levels` | levels to test. Default `[8]`, the GDD's `check_level` |
| `skip` | wave ids that are never checked |
| `start_spots` | ship x at the start of a wave, by name |
| `limits` | `seam_clear_px`, `coin_near_ship_widths`, `gap_min_ship_widths` (part 2) |
| `track_ticks_max` | longest one drifter is followed |
| `bot` | part 2: `mode`, `reaction_ticks`, `lookahead_ticks` |

`telegraph_min` is not here: it is the game's own value, `game/tuning/hazards.json`.

## Remembered passes

A pass is stored in `passes.json` as `<wave>@<level>` with a fingerprint of the wave (whitespace ignored), every tuning file, the config and the suite name. Change any of them and the pass is stale, so a tuning change reruns every wave. A failing wave drops its old pass. When part 2 arrives the suite name changes, so every part 1 pass goes stale. `--wave` and `--force` always run.

## Tests

```
cd tools/wave_check && python -m pytest -q
```
