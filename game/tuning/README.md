# debug_spawns.json

The debug test spawn list. You edit it by hand. Debug mode reads it once at startup (`?debug=1`). Normal mode never reads it.

The loader is `game/app/debug_spawns.py`. The schema is `docs/contracts/schemas/debug-spawn-list.schema.json`. A bad file shows the error screen with the file, the row and the field.

## Fields

| Field | Default | What it does |
|---|---|---|
| `play` | `"list"` | What debug mode plays. `"list"` plays the rows. `"waves"` plays the normal waves and places no row. |
| `mode` | `"all"` | Which rows play. See Modes. |
| `loop_ticks` | `180` | Length of one loop in ticks (60 ticks = 1 s). Whole number, 1 or more. |
| `rows` | required | The rows, in play order. May be empty. |

The rows in play are spread evenly over one loop, in file order. Row `i` of `n` spawns at tick `floor(i * loop_ticks / n)`. The loop then repeats.

## Modes

`mode` is `"all"` or one drifter type. With a type, only the rows of that type play.

| Mode | Plays |
|---|---|
| `all` | every row |
| `meteorite` | meteorite rows |
| `satellite` | satellite rows |
| `chain_lightning` | chain lightning rows |
| `fireball` | fireball rows |
| `coin` | coin rows |
| `floating_island` | floating island rows |
| `planet` | planet rows |
| `ufo` | UFO rows |
| `electric_ball` | electric ball rows |

Any other value is refused. A new drifter type becomes a valid mode when it is added to `DrifterType` in `game/core/drifters/base.py`.

Every row is checked at load, whether it plays or not. A bad row in another mode still fails the load.

## Row fields

Only `type` is always required. Everything else falls back to the drifter's own default.

| Field | Meaning |
|---|---|
| `type` | A drifter type from the Modes table. |
| `x`, `y` | Center position in screen px, y down. Which one a drifter needs is below. |
| `variant` | A variant name from `game/tuning/drifters/<type>.json`. Left out: the drifter's default variant. |
| `invert` | `true` mirrors the drifter. Left out: `false`. |
| `speed` | Level 1 speed in px/tick, above 0. Left out: the drifter's default. |
| `seed` | Whole number, 0 to 4294967295. UFO only. Left out: fixed by the row's index, so the path is the same on every loop. |

## What each drifter needs

| Type | Position | Variants | `invert` | `speed` | `seed` |
|---|---|---|---|---|---|
| `meteorite` | `x` | small, medium, big | no | yes | no |
| `satellite` | `y` | flat, angled | yes | yes | no |
| `chain_lightning` | `x` | pair_flat, pair_diagonal, pair_vertical, trio_line, trio_diagonal, trio_l, trio_triangle | yes | yes | no |
| `fireball` | none, `x`, or `y` (see below) | small, big | yes | yes | no |
| `coin` | `x` (`y` optional) | common, rare | no | no | no |
| `floating_island` | `x` (`y` optional) | rectangle, box, l_shape, t_shape, triangle | l_shape, t_shape, triangle only | no | no |
| `planet` | `x` (`y` optional) | standard | no | no | no |
| `ufo` | `y`, from 188 to 440 | standard | yes | yes | yes |
| `electric_ball` | `x` | standard | accepted, no effect | yes | no |

Variant lists come from `game/tuning/drifters/*.json`. If you add a variant there, it is valid here.

Without `y`, a meteorite, chain lightning, fireball, coin, floating island or planet starts just above the top edge. Without `x`, a satellite or UFO starts just outside the wall it enters from. A coin or floating island with both `x` and `y` shows at that spot at once, with no warning. A planet with both is placed there after its entry warning.

Fireball entry:

- No `x`, no `y`: top-left corner (top-right with `invert`).
- `x` only: along the top edge.
- `y` only: the left wall (the right wall with `invert`).

## Examples

```json
{ "type": "meteorite", "x": 320, "variant": "big" }
{ "type": "satellite", "y": 120, "variant": "angled", "invert": true }
{ "type": "ufo", "y": 300, "seed": 2 }
{ "type": "fireball", "speed": 2.0 }
```

Set `"mode": "ufo"` and only the third row would play.

# background.json

How the background moves and glows. You edit it by hand. The game reads it once at startup, in both run modes, so change a value and reload the page. Nothing else needs rebuilding, except the painting's sway size (see Baked sway below).

The loader is `game/app/background_tuning.py`. The schema is `docs/contracts/schemas/background.schema.json`. These values change how the background looks and nothing else. They never change play.

Every field is optional. A field left out keeps its default from the Default column. `{}` is a valid file. An unknown field, or a value out of range, shows the error screen with the file and the field.

Time is in ticks. 60 ticks = 1 second, so 900 ticks = 15 s. A bigger loop number always means slower.

## Fields

| Field | Default | Range | What it does |
|---|---|---|---|
| `sway_loop_ticks` | `900` | whole number, 1 or more | Time for the painted rays to sway through one full loop. The painting is 12 baked frames, and the game fades from each one to the next over this time. Bigger is slower. |
| `planet_count` | `3` | whole number, 0 or more | Broken planets on screen at once. They drift down behind the rivers. `0` shows none. |
| `planet_speed` | `0.15` | number, 0 or more | How far a planet moves down each tick, in px. 0.15 is about 9 px per second. `0` freezes them. |
| `planet_scale` | `1.0` | number above 0 | Planet size against the shipped sprite (about 100 px). `0.5` is half size, `2` is double. |
| `river_light_count` | `30` | whole number, 0 or more | Most glowing specks flowing along the rivers into the black hole at once. They are spread evenly along the trip. `0` shows none. |
| `river_light_loop_ticks` | `900` | whole number, 1 or more | Time a speck takes to go from the screen edge to the black hole. Bigger is slower. Specks still speed up near the hole, as the pull does. |
| `river_light_strength` | `0.6` | 0 to 1 | Brightness of the river specks and the swirl. `0` hides both. Keep it low: the background must stay dimmer than anything you can touch. |
| `swirl_count` | `8` | whole number, 0 or more | Specks circling the black hole, spread evenly around it. `0` shows none. |
| `swirl_loop_ticks` | `480` | whole number, 1 or more | Time for the swirl to turn once around the hole. Bigger is slower. |
| `glow_height` | `40` | whole number, 0 or more | Height of the fuchsia glow along the bottom edge, in px. `0` turns it off. |
| `glow_strength` | `0.25` | 0 to 1 | Brightness of the glow at the very bottom edge. It fades to nothing at its top edge. |

## Quick recipes

| I want | Change |
|---|---|
| Slower river specks | Raise `river_light_loop_ticks` (1350 is about a third slower, 1800 is half speed). Raise `swirl_loop_ticks` by a similar share so the two stay in step. |
| Fewer or more specks | `river_light_count` and `swirl_count`. |
| Dimmer or brighter specks | `river_light_strength`. |
| Slower or faster ray sway | `sway_loop_ticks`. Lower is faster. |
| No planets | `planet_count`: `0`. |
| No bottom glow | `glow_height`: `0`. |

## Baked sway

The painted rays and the turning light on the black hole's rim are not drawn by the game. They are 12 images, `game/assets/background_sway_00.png` to `_11.png`, made ahead of time from `game/assets/background.png`. `sway_loop_ticks` sets how fast they play. How big the sway is, is fixed when the images are made.

To change the size, edit the constants at the top of `tools/art/background_sway.py`, then run it from the repo root and reload the game:

```
python3 tools/art/background_sway.py
```

| Constant | Default | What it does |
|---|---|---|
| `SWAY_PX` | `10` | Peak sideways swing of the rays, in px. Bigger swings further. |
| `FLOW_PX` | `7` | Peak in-and-out ripple of the rays along their curves, in px. |
| `RIM_GAIN` | `0.25` | How strongly the light turning along the black hole's rim rises and falls. `0` turns it off. |
| `RIM_LOBES` | `4` | Bright patches around a full turn of the hole. About one shows on screen. |
| `WAVELENGTH` | `240` | Distance between ripple crests along the rays, in px. Bigger makes longer, calmer waves. |
| `RAY_TWIST` | `3.0` | How much the ripple's timing changes around the hole, so the rays don't all move together. `0` moves them in lockstep. |
| `KEYFRAMES` | `12` | Frames in the loop. More frames fade more smoothly when the sway is big or fast, and cost about 280 KB of download and 1.2 MB of memory each. If you change it, change `SWAY_FRAMES` in `game/app/assets.py` to match. |

Every frame is balanced to the painting's own brightness, so a bigger sway never makes the background brighter.
