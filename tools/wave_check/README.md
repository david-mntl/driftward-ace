# wave_check

Tests a wave against the GDD rules ([09-waves.md](../../docs/design/gdd/09-waves.md), rule 7) by running the game's own physics headless. It reads the game and never changes it. The Director owns `config.json`.

**Built:** placement sanity, telegraph, coin near a hazard, seam, and the bot (zero-hit path). The bot is slower, so it runs on its own with `--bot`, and CI runs it as its own step. The gap check is not built yet and shows as SKIP.

## Run

```
python tools/wave_check/wave_check.py --wave game/waves/l1_a.json   # one wave, always runs
python tools/wave_check/wave_check.py --changed                     # only waves git sees as changed or new
python tools/wave_check/wave_check.py --changed --base origin/main  # only waves changed since a ref (CI)
python tools/wave_check/wave_check.py --all                         # every wave; fresh passes are skipped
python tools/wave_check/wave_check.py --changed --bot               # the bot check alone, on the changed waves
```

`--bot` works with every mode above and runs only the bot check. Without it the bot row shows SKIP. The bot takes about 10 to 20 s a wave at the shipped settings, so `--all --bot` takes a couple of minutes.

`--changed` checks nothing else: if no wave changed it says so and exits 0. It reads git, and if git cannot answer it exits 2, so a broken git never reads as "nothing changed". A tuning change does not count as a changed wave: use `--all` for that.

Options: `--bot` (the bot check alone), `--level N` (repeatable, replaces the config levels), `--force` (ignore remembered passes), `--no-record` (do not write `passes.json`), `--json` (machine-readable report), `--config FILE`, `--base REF` (with `--changed` only).

Exit code: 0 all passed, 1 a check failed, 2 a usage, config or game file error.

## What it checks

A floating island counts as a hazard here (09-waves.md, rule 7), though in play it never hurts: it counts for placement, coin near and the seam.

A planet is a hazard like any other. Coin near and the bot use its body, never its field (drifters/08-planet.md, rule 11). The game's wave loader already refuses a planet inside the seam.

Each drifter is played alone with the game's physics (ship held at the start spot, world scrolling at the level's speed). The tracks are lined up by trigger tick, so two drifters can be compared at the same moment.

| Check | Fails when |
|---|---|
| placement | a drifter never enters the screen, or a hazard turns active on top of the ship at a start spot (left, center, right) |
| telegraph | a telegraph is under `telegraph_min` at the tested level. Only the chain lightning charge is a telegraph (an entry warning is not). It compares the charge before the game's own floor, because the game clamps it and would hide a bad tuning value. |
| coin_near | a coin never comes within `coin_near_ship_widths` x 32 px (96) of a hazard's hitbox while both are on screen |
| coin_in_island | a coin's hitbox shares area with a floating island's hitbox at some tick (09-waves.md, rule 7.7). Touching an edge from outside passes. The triangle uses its slope, not its box. |
| seam | a hazard is on screen in the wave's first `seam_clear_px` (120). An entry warning counts as on screen. The end of a wave is not checked: `extra_rest_ticks` covers it. |
| bot (`--bot`) | from a start spot, no path gets through the wave with zero hits (09-waves.md, rule 7.3). See [The bot](#the-bot). |
| gap | not built yet |
| lava, per-drifter notes | lava is not in the game yet. Floating island: coin inside is its own check above. Planet: measured from its body, as above. Gaps and the bot's island and planet physics are not built. |

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
| `bot` | how the bot searches, see [The bot](#the-bot) |

`telegraph_min` is not here: it is the game's own value, `game/tuning/hazards.json`.

## The bot

The bot knows where every hazard will be on every tick, so it plans a path rather than reacting like a player. It starts at rest at each start spot. It tries every arrow-key combination (9, since opposite keys cancel), holds it for `decision_ticks`, and drops any ship that is hit or falls past the floor. It flies the game's own ship step and hitboxes. After each choice it keeps `beam_width` ships, spread over the screen and over sideways speeds, safest first. One ship alive when the wave's last hazard is gone is a pass for that spot. Every spot must pass.

A failure names the start spot, the tick and scroll distance where the last ships were lost, where the safest of them was, and the hazards (or the floor) that hit them.

The bot can wrongly fail a wave that a person could fly, since it doesn't try every path. If it fails a wave you think is fair, raise `beam_width` or lower `cell_px` and run it again. Both make it slower.

| `bot` key | Meaning | Shipped |
|---|---|---|
| `start_spots` | start spot names to fly from; `[]` means all of them | `[]` |
| `decision_ticks` | ticks each arrow-key choice is held | 4 |
| `beam_width` | ships kept after each choice | 60 |
| `cell_px`, `cell_speed` | ships closer than this in position (px) and speed (px/tick) count as one | 8, 1 |
| `spread_px`, `spread_speed` | screen square (px) and sideways speed step (px/tick) the kept ships are spread over | 64, 3 |
| `safe_px` | room to the nearest hazard, or to the floor, past which a ship counts as safe | 96 |
| `margin_px` | grows every hazard hitbox for the bot only, so it keeps room to spare like a person would. 0 is the game's exact hitbox. | 6 |

The tracks play each drifter with the ship held at the spawn. No drifter in the game moves or hits by where the ship is (the chain lightning only places its warning by it). A future drifter that chases the ship would need the bot to play the whole game instead.

The bot does not fly two drifters' effects on the ship yet: islands don't carry or block it, and a planet's field doesn't pull it (09-waves.md, rule 7.7; drifters/08-planet.md, rule 11). A wave with planets can pass the bot while a pulled ship would not get through. Fly such a wave yourself.

## Remembered passes

A pass is stored in `passes.json` as `<wave>@<level>` with a fingerprint of the wave (whitespace ignored), every tuning file, the config and the suite name. Change any of them and the pass is stale, so a tuning change reruns every wave. A failing wave drops its old pass. `--wave` and `--force` always run.

A bot pass is stored apart, as `<wave>@<level>/bot`. Its fingerprint also holds `game/core/ship.py`, since the bot flies the ship's physics.

## Tests

```
cd tools/wave_check && python -m pytest -q
```
