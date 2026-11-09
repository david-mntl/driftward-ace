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

# ship_look.json

When the ship leans, when its air streaks show and how fast its flame flickers. You edit it by hand. The game reads it once at startup, in both run modes, so change a value and reload the page.

The loader is `game/app/ship_tuning.py`. The schema is `docs/contracts/schemas/ship-look.schema.json`. These values change how the ship looks and nothing else. They never change play or the hitbox.

Every field is optional. A field left out keeps its default from the Default column. `{}` is a valid file. An unknown field, or a value out of range, shows the error screen with the file and the field.

## Fields

| Field | Default | Range | What it does |
|---|---|---|---|
| `lean_speed` | `1.0` | above 0 | Sideways speed (px/tick) from which the ship leans. About 3 ticks of holding an arrow. Top sideways speed is about 6.6. |
| `streak_speed` | `1.0` | above 0 | Sideways speed (px/tick) from which short air streaks trail behind the ship. |
| `streak_long_speed` | `4.0` | above `streak_speed` | Sideways speed (px/tick) from which the streaks are long. About 15 ticks of holding. |
| `flame_ticks_per_frame` | `4` | 1 or more | Ticks each flame and streak flicker frame shows. 60 ticks = 1 second. Smaller flickers faster. |

The sprites are `game/assets/sprites/ship.png` (3 lean frames), `ship_flame.png` (8 flame frames) and `ship_streaks.png` (4 air streak frames). `tools/art/ship_final.py` makes all three from the chosen pose. Run it from the repo root, then copy the PNGs from `staging/assets/sprites/` to `game/assets/sprites/`. How strong the lean is and how long the streaks are is fixed when the images are made: edit the constants at the top of that script.

# hud.json

The side panel and the cockpit frame: colors, sizes, positions, counts and timings. You edit it by hand. The game reads it once at startup, in both run modes. Every field is required.

The loader is `game/app/hud_tuning.py`. The schema is `docs/contracts/schemas/hud.schema.json`, with every field described. These values change how the HUD looks and nothing else. They never change play.

## What needs the tool

Text, digit tiles, bars, the heart that is lit, the radar frame and the motions' timings are drawn from these values when the game starts, so a change shows after a reload. The panel, the frame, the wireframe, the hearts, the radar wedge and the ring are pictures made ahead of time. After changing a color in `palette`, or a size or position of a baked part (`window`, `panel`, `frame`, `score.box`, `level.box`, `hearts`, `graze`, the motion frame counts), run the tool from the repo root, then reload:

```
python3 tools/art/hud_panel.py
```

The game checks every picture against these numbers at startup. A mismatch shows the error screen with the file named.

## Sections

| Section | What it holds |
|---|---|
| `palette` | 17 colors as `#rrggbb`. Meanings are in `docs/design/gdd/12-art-and-audio.md`, HUD colors. |
| `window` | Window size, where the play area sits, how dark the pause and game-over dim is (`dim_alpha`, 0 to 255). |
| `panel` | Where the panel sits and how wide it is. `content_y` centers its content in the taller window. `scale` is the design's size against the mock-up (0.8); only the art tool reads it, and every other number in the file is already at that scale. |
| `frame` | The pillar's width, the glass sheen on or off and its strip height (`sheen_rows`: the game blends only the pixels that have sheen, in strips this tall; the full-size blit halved the browser's frame rate), the corner lights' size. |
| `score` | The score box, the 7 tiles, the 14 segment bar, BEST. `best_separator` is the text between digit groups. |
| `hearts` | Where the three hearts sit, and the wireframe's box. |
| `level` | The level box, the number, the 8 climb bars, the levels where the number warms up (`tier_mid`, `tier_high`) and how far the middle tier goes toward the last-life color (`tier_mid_mix`). |
| `graze` | The dial's centre and radii, the label. |
| `motion` | Every period in ticks (60 per second) and every scale. `break_keys` is the heart's break. |
| `fonts` | The two font files, the sizes, the label spacing. |

# screens.json

The look of the menu, the pause box, the game-over screens, the instructions page, the leaderboard and the credits page: colors, glow, glass, fonts and the size and gaps of each screen. You edit it by hand. The game reads it once at startup, in both run modes. Every field is required.

The loader is `game/app/screens_tuning.py`. The schema is `docs/contracts/schemas/screens.schema.json`, with every field described. These values change how the screens look and nothing else. They never change play. Nothing here is baked into a picture file: the glass, the glow, the icons and the text are drawn once at startup, so a change shows after a reload.

Field names carry their range. `*_alpha` is a whole number from 0 to 255. `*_strength` is a number from 0 to 1. `*_size`, `*_w`, `*_h` and `*_pitch` are whole numbers of 1 or more. Any other whole number is 0 or more.

## Sections

| Section | What it holds |
|---|---|
| `palette` | 13 colors as `#rrggbb`. Meanings are in `docs/design/gdd/12-art-and-audio.md`, Screen colors. Not the HUD palette. |
| `glass` | The see-through panel every box and card shares: fill, border, corner brackets, scan lines, and `blur_down` (how much the picture behind is blurred; 1 is off). |
| `glow` | The soft glow's radius (px) and strength (0 to 1) round boxes, behind text and behind icons. A strength of 0 turns that glow off. All three ship at 0: the screens are flat. |
| `fonts` | The font file and one entry per text role: size (px) and letter-spacing (em). Every role in the file must be there once. |
| `rulers` | The tick marks down both sides of the full-window pages. `enabled` turns them off. |
| `keycap` | The small key caps (ENTER, SPACE, arrows) and the gaps between them. |
| `choice` | The selected choice's fade and brackets, and how dim a not-selected or not-yet-pickable choice is. |
| `pause` | The pause box's size. `blur` turns the blur behind it off. |
| `game_over` | The game-over box with and without the name picker: sizes, padding, the score cells, the slots, the cursor. |
| `menu` | The menu's items, gaps and hint. |
| `instructions` | The page's margins, the card grid and the icon box. `coin_scale`, `common_coin_frame` and `rare_coin_frame` pick the size and the frame of the real coin sprites on the COINS card (scale 1.0 is the size in play; frames count from 0). |
| `leaderboard` | The page's margins, the table and the row sizes. |
| `credits` | The page's margins, the card width, padding and gaps, and how bright the text and the links are. |

`blur` is off by default on the pages that have a moving background (instructions, leaderboard, credits): the blur is the one part drawn live every frame, and it costs frame rate in the browser.

# level_up.json

The level-up moment: the extra rest after a level rise, the banner that plays in it, and the pop in the HUD level box. You edit it by hand. The game reads it once at startup, in both run modes, so change a value and reload the page. Every field of every section is required. Nothing has a default in code.

The loader is `game/app/level_up_tuning.py`. The schema is `docs/contracts/schemas/level-up.schema.json`, with every field described. The rules are in `docs/contracts/systems/level-up/tuning.md`. A missing file, a missing or unknown field, a wrong type or a value out of range shows the error screen with the file and the field.

Only `level_up_rest` touches play: it is a rest between waves. Every other value changes how the banner looks and moves, and nothing else. Nothing here is baked into a picture file. The view builds every image it needs once at startup, so there is no art tool to run.

## Time and position

- **Ticks.** 60 ticks = 1 second. Every `*_start`, `*_end`, `*_tick` and `*_ticks` value is an age: ticks counted from the tick the level rises (age 0). The shipped timeline runs 150 ticks, 2.5 s.
- **Px.** Screen px in the play area. `*_offset_y` is measured down from the band's center, so a negative value moves the thing up. `center_offset_y` in `band` moves the band from the middle of the play area.
- **Whole numbers vs. decimals.** `*_ticks`, `*_px`, `*_size`, `*_width`, `*_steps`, `*_pixels` and `count` are whole numbers. Scales and shares are decimals. A share is above 0 and below 1.
- **Colors.** `#rrggbb`, or a key of the HUD `palette` in `hud.json` (`panel_body`, `frame_lights`, `plating`, `level`, `dim`). Don't use fuchsia: solid fuchsia in the play area means a coin.

## Top level

| Field | Default | What it does |
|---|---|---|
| `level_up_rest` | `150` | Ticks added to the rest after the last wave of a level, when the level rises. The next level's first wave starts only after it. It never scales with level. `0` turns the whole feature off: no rest, no banner, no pop, no sound cue. |
| `arrival_tick` | `124` | The age the flying number reaches the HUD. The level box switches to the new level and pops on this tick. Whole number, 1 or more, below `banner_ticks`. |
| `banner_ticks` | `150` | How many ticks the banner lives (age 0 to `banner_ticks` - 1). Never more than `level_up_rest`, and never less than `arrival_tick` + `pop.ticks`. |

## colors

Every color the banner and the pop use.

| Field | Default | What it colors |
|---|---|---|
| `glass` | `panel_body` | The band's glass. |
| `hairline` | `frame_lights` | The two hairlines and their corner ticks. |
| `label` | `plating` | The word LEVEL. |
| `number_top` | `#fff6d6` | The number's gradient at its top. |
| `number_bottom` | `level` | The number's gradient at its bottom (the level gold). |
| `number_outline` | `panel_body` | The number's outline. |
| `ring` | `#fff6d6` | The ring that bursts out on landing. |
| `streak` | `#fff6d6` | The light streaks. |
| `glint` | `#fff6d6` | The glint that crosses the number. |
| `pip_lit` | `level` | A lit pip. |
| `pip_unlit` | `dim` | An unlit pip. |
| `flash` | `#ffffff` | The white flash of the new pip, the HUD number and the new climb bar. |
| `box_flash` | `level` | The flash of the level box outline. |

## band

The see-through band across the middle of the play area, with a hairline on its top and bottom edge.

| Field | Default | What it does |
|---|---|---|
| `height` | `120` | Height of the glass, px. 2 or more. Keep it tall enough that LEVEL, the number and the pips sit between the hairlines. |
| `alpha` | `0` | Glass opacity, 0 to 255. `0` draws no glass and keeps the hairlines. It ships at 0 because the glass cost frame rate in the browser (about 40 fps while open, against about 58). `120` is the see-through look. |
| `center_offset_y` | `0` | Px the band's center sits below the play area's center. May be negative. |
| `open_start` | `0` | Age the band starts to open. |
| `open_end` | `10` | Age it is fully open. |
| `close_start` | `100` | Age the band starts to close. |
| `close_end` | `124` | Age it is fully closed. At most `arrival_tick`. |
| `close_glass_share` | `0.65` | The share of the closing time in which the glass closes. The hairlines pull in during the rest of it. |
| `hairline_width` | `1` | Hairline thickness, px. |
| `corner_tick_length` | `6` | Length of the small tick at each end of a hairline, px. `0` draws none. |

## number

The big level number: its type, outline, fall and landing squash.

| Field | Default | What it does |
|---|---|---|
| `font_size` | `88` | Exo 2 Bold size, px. 8 or more. |
| `outline_width` | `2` | Outline thickness, px. `0` draws none. |
| `center_offset_y` | `0` | Px the number's resting center sits below the band's center. |
| `fall_start` | `4` | Age the number starts to fall in from above the play area. |
| `fall_end` | `22` | Age it lands. The squash, the bump, the ring and the streaks start on this tick. |
| `fall_overshoot_px` | `10` | Px the number sinks past its resting place before it settles back. `0` for none. |
| `fall_peak_share` | `0.72` | The share of the fall at which the number is deepest past its place. |
| `fall_stretch_x` | `0.92` | Width scale while it falls. Below 1 is narrower. |
| `fall_stretch_y` | `1.12` | Height scale while it falls. Above 1 is taller. |
| `squash_ticks` | `8` | Ticks the landing squash takes to settle back to normal size. |
| `squash_x` | `1.2` | Width scale on the landing tick. |
| `squash_y` | `0.82` | Height scale on the landing tick. |
| `pose_steps` | `4` | How many sizes between the squash and normal size are drawn ahead of time. The view picks the nearest. More steps look smoother and cost more memory at startup. |

## label

The word LEVEL above the number, in Share Tech Mono. Its letters start spread wide and close in as it fades in.

| Field | Default | What it does |
|---|---|---|
| `font_size` | `14` | Size, px. 6 or more. |
| `offset_y` | `-48` | Px the label's center sits from the band's center. Negative is above. |
| `fade_in_start` | `22` | Age it starts to fade in. |
| `fade_in_end` | `36` | Age it is fully in, with the spacing back to normal. |
| `spacing_wide` | `14` | Letter spacing at the start of the fade-in, px. |
| `spacing_normal` | `4` | Letter spacing when it has settled, px. |
| `spacing_steps` | `5` | How many spacings between wide and normal are drawn ahead of time. |

## hold

When the label and the pips fade out, just before the flight.

| Field | Default | What it does |
|---|---|---|
| `fade_out_start` | `96` | Age the label and the pips start to fade. |
| `fade_out_end` | `106` | Age they are gone. |

## pips

The row of one diamond per level under the number. The pips up to the new level are lit.

| Field | Default | What it does |
|---|---|---|
| `size` | `10` | Width and height of a diamond, px. 2 or more. |
| `pitch` | `18` | Px from one pip's center to the next. |
| `offset_y` | `48` | Px the row's center sits from the band's center. Positive is below. |
| `start` | `26` | Age the first pip starts to appear. |
| `end` | `48` | Age the last pip is fully in. |
| `pop_ticks` | `6` | Ticks one pip takes to appear. At most `end` - `start`. |
| `flash_ticks` | `10` | Ticks the new pip's white flash takes to fade to its lit color. |

## ring

The ring that bursts out of the number on landing.

| Field | Default | What it does |
|---|---|---|
| `start_diameter` | `48` | Px across on the landing tick. Must be below `end_diameter`. |
| `end_diameter` | `170` | Px across as it fades out. |
| `width` | `2` | Line width, px. |
| `ticks` | `18` | How many ticks it shows, from the landing tick. |

## streaks

The short light streaks that fly out of the number on landing, spread evenly round it.

| Field | Default | What it does |
|---|---|---|
| `count` | `12` | How many streaks. |
| `ticks` | `14` | How many ticks they show, from the landing tick. |
| `length` | `20` | Length of one streak, px. |
| `width` | `2` | Thickness, px. |
| `start_radius` | `34` | Distance of a streak's inner end from the number's center on the landing tick, px. Must be below `end_radius`. |
| `end_radius` | `130` | Distance it flies out to by its last tick, px. |

## glint

The one light band that sweeps across the number.

| Field | Default | What it does |
|---|---|---|
| `start` | `44` | Age the glint starts to cross. |
| `end` | `60` | Age it has crossed. At most `hold.fade_out_start`. |
| `frames` | `8` | How many positions of the glint across the number are drawn ahead of time. |
| `width` | `14` | Width of the glint band, px. |
| `slant_degrees` | `20` | Lean of the band from vertical, 0 to 89. |
| `strength` | `0.8` | How far the glint pulls the number's colors toward the glint color. Above 0, up to 1. |

The glint only lights the digit, never the outline or the space round it.

## bump

The play area's picture dips down on landing and springs back. It is drawing only. No hitbox moves, and neither does the ship.

| Field | Default | What it does |
|---|---|---|
| `pixels` | `3` | Px the picture moves down at its lowest. `0` turns the bump off. |
| `ticks` | `14` | Ticks from the landing tick until the picture is back. |
| `peak_share` | `0.25` | The share of the bump at which the picture is lowest. |

## fly

The number's flight into the HUD level box. It ends on `arrival_tick`.

| Field | Default | What it does |
|---|---|---|
| `start` | `100` | Age the number leaves its place and starts to shrink and fly. Below `arrival_tick`. |
| `arc_px` | `40` | How far the path bows up from the straight line, px. `0` flies straight. |
| `steps` | `8` | How many sizes along the flight are drawn ahead of time. The view picks the nearest. |

## pop

The HUD level box's pop when the number arrives.

| Field | Default | What it does |
|---|---|---|
| `ticks` | `24` | Ticks from arrival until the pop is over. At least as long as `flash_ticks`, `bar_flash_ticks` and `box_flash_ticks`. |
| `start_scale` | `1.45` | Size of the number on arrival, as a multiple of its normal size. Above 1. |
| `undershoot_scale` | `0.94` | The smallest multiple the number settles through before it rests at 1. Above 0, at most 1. |
| `undershoot_share` | `0.6` | The share of the pop at which the number is at `undershoot_scale`. |
| `flash_ticks` | `14` | Ticks the number's white flash takes to fade to its tier color. |
| `steps` | `12` | How many frames of the pop are drawn ahead of time, per level (size and flash together). |
| `bar_flash_ticks` | `18` | Ticks the new climb bar's white flash takes to fade to its lit color. |
| `box_flash_ticks` | `20` | Ticks the level box outline's flash takes to fade out. |
| `box_flash_width` | `1` | Thickness of the flashing outline, px. |
| `box_corner_cut` | `8` | Size of the level box's two cut corners, px. It must match the cut the panel art draws (10 × `panel.scale` in `tools/art/hud_panel.py`). Change it only with the art. |

## Timing rules

The loader refuses a file that breaks one of these, and names the fields:

- `arrival_tick` is below `banner_ticks`. With `level_up_rest` above 0, `banner_ticks` is at most `level_up_rest`.
- `arrival_tick` + `pop.ticks` is at most `banner_ticks`.
- Band: `open_start` < `open_end` ≤ `close_start` < `close_end` ≤ `arrival_tick`.
- Number: `fall_start` < `fall_end`, and `fall_end` + `squash_ticks` is at most `fly.start`.
- What starts on landing ends before the flight: `fall_end` + the longest of `ring.ticks`, `streaks.ticks` and `bump.ticks` is at most `fly.start`.
- Label and pips: `label.fade_in_start` < `label.fade_in_end` ≤ `hold.fade_out_start` < `hold.fade_out_end` ≤ `arrival_tick`. And `pips.start` < `pips.end` ≤ `hold.fade_out_start`.
- Glint: `glint.start` < `glint.end` ≤ `hold.fade_out_start`.
- Flight: `fly.start` < `arrival_tick`.

To make the banner longer, raise `level_up_rest` first, then `banner_ticks`, then move the later ages (`close_*`, `hold.*`, `fly.start`, `arrival_tick`) to match.


---

# audio.json

How loud the music and the sound effects are. The loader is `game/app/audio_tuning.py`. The schema is `docs/contracts/schemas/audio.schema.json`.

The file must exist and every field is required. Nothing has a default in code. A missing field, an unknown field, a value out of range or a bad type shows the error screen with the file and the field.

A sound's loudness is its master times its own level. Both are percents. Muting a sound is `0`. The game never sets a volume above 100%: if a sound is too quiet at 100, the file itself has to be made louder.

## Fields

| Field | Value now | Range | What it does |
|---|---|---|---|
| `music_master` | `80` | 0 to 100 | Master level of the music. |
| `effects_master` | `80` | 0 to 100 | Master level of every effect. |
| `loop_level` | `100` | 0 to 100 | Level of the music loop, under the music master. |
| `hit_level` | `100` | 0 to 100 | Level of the hit sound, played on every life lost. |
| `graze_level` | `25` | 0 to 100 | Level of the graze sound. |
| `coin_level` | `83` | 0 to 100 | Level of the coin sound. |
| `game_over_level` | `100` | 0 to 100 | Level of the game-over sound, played as the ship bursts on the last life, after the hit. |
| `level_up_level` | `60` | 0 to 100 | Level of the level-up sound, played when the level-up banner starts. |
| `effect_channels` | `8` | whole number, 1 or more | How many effects can sound at once. When all are busy, a new sound is dropped. A playing sound is never cut. |

The sound files are in `game/assets/audio/`: `music_loop.ogg`, `sfx_hit.ogg`, `sfx_graze.ogg`, `sfx_coin.ogg`, `sfx_game_over.ogg` and `sfx_level_up.ogg`. They are read once at startup.

---

# mute_icon.json

The small icon that shows while the music is muted (M key). A speaker with a slash, in the bottom-right corner of the window. The loader is `game/app/mute_icon_tuning.py`. The schema is `docs/contracts/schemas/mute_icon.schema.json`.

The file must exist and every field is required. An unknown field, a missing field, a bad type, or an icon that would touch the play area or leave the window shows the error screen with the file and the field.

## Fields

| Field | Value now | Range | What it does |
|---|---|---|---|
| `margin` | `8` | whole number, 0 or more | Distance in px from the window's right edge and from its bottom edge to the icon. |
| `size` | `24` | whole number, 1 or more | Width and height of the icon on screen, in px. The picture `game/assets/mute_icon.png` must be exactly this size. |
| `speaker_color` | `"#f4f1ff"` | `#rrggbb` | Color of the speaker. Only the art script reads it. |
| `slash_color` | `"#ff00ae"` | `#rrggbb` | Color of the slash. Only the art script reads it. |

The colors are baked into the picture. After you change a color or `size`, run `python tools/art/mute_icon.py --ship` to redraw it. Changing `margin` needs no redraw.

---

# demo.json

The demo flight: the short scripted flight that plays the first time Play is picked after a page load, before the run starts. It shows how the ship drifts and what a coin is. Enter or Space skips it. A page reload shows it again; nothing is saved. You edit it by hand. The game reads it once at startup, in both run modes, so change a value and reload the page.

The loader is `game/app/demo_tuning.py`. The schema is `docs/contracts/schemas/demo.schema.json`. The spec is `docs/contracts/systems/demo.md`.

The file must exist and every field is required. Nothing has a default in code. A missing field, an unknown field, a value out of range or a bad type shows the error screen with the file and the field.

Time is in ticks. 60 ticks = 1 second.

## Top level

| Field | Value now | Range | What it does |
|---|---|---|---|
| `enabled` | `true` | `true` or `false` | `false` turns the demo off: Play starts the run at once. |
| `steps` | 8 steps, 388 ticks (about 6.5 s) | a list, 1 step or more | The script, played in order. See Steps below. |
| `coin_step` | `5` | a step's index, counting from 0 | The step at whose last tick the ship reaches the coin. The game flies the script ahead once and puts the coin where the ship is then, so the coin is always collected, whatever the ship's values. |
| `coin_type` | `"coin"` | a drifter type | What the ship collects. It must be a pickup. |
| `coin_variant` | `"common"` | a variant of `coin_type` | `"rare"` shows the rare coin and pays its points. |
| `fade_out_ticks` | `0` | whole number, 0 or more | The last ticks of the demo, in which the play area fades to black. `0` goes straight to the run: the ship ends hovering in the middle, where the run starts it, so no fade is needed. |
| `pilot` | see Autopilot | object | How the autopilot taps the arrows. |

## Steps

Each step is one row in `steps`.

| Field | Range | What it does |
|---|---|---|
| `keys` | a list of `"up"`, `"down"`, `"left"`, `"right"`, each once at most | The arrows the script holds through the step. They light up on the key caps and thrust the ship. `[]` holds nothing: the ship drifts. |
| `ticks` | whole number, 1 or more | How long the step lasts. |
| `caption` | text, or `null` | The caption shown from this step on. `null` keeps the last caption. Write it in capitals, as the other screens do. |
| `stand` | `true` or `false` | `true` keeps the ship still, with no flame and the keys dark, as it waits to respawn. Use it at the start only: mid-air it looks frozen. A standing step holds no keys and has no `pilot_to`. |
| `pilot_to` | `null`, or `[x, y]` inside 640 x 480 | The autopilot flies the ship to that spot and hovers there, tapping the real arrows as a player would; the keys light with each tap. Such a step has `"keys": []` and `"stand": false`. The middle of the play area, where a run starts, is `[320, 240]`. |

The script now: stand 60 (HOLD UP TO THRUST), hold up 18, let go 60 (LET GO AND GRAVITY PULLS YOU DOWN), hover in the middle 50 (TAP UP TO HOVER) and 40 more (HOLD UP + RIGHT TO STEER), hold up and right 20 (the coin), fly back to the middle 90 (COINS ARE POINTS) and hover 50 (START).

A caption set on a hover step shows before the move it names, so the player reads it first.

## Autopilot

`pilot`. Speeds are px per tick, distances px. These change how the autopilot flies, so after a change check the ship still settles (see Quick recipes).

| Field | Value now | Range | What it does |
|---|---|---|---|
| `gain` | `0.06` | above 0 | Speed wanted per px of distance to the spot. Bigger flies in harder and can overshoot. |
| `max_speed` | `3.0` | above 0 | Fastest speed the autopilot asks for up or down. Sideways it allows 1.5 times this. |
| `band` | `0.35` | above 0 | How far the speed may stray before a key goes down or up. Bigger gives longer, calmer taps and a little more bob while hovering. |
| `near_px` | `6` | 0 or more | Within this distance sideways, and slower than `near_speed`, no side key is tapped: drag settles the rest. Stops the left-right twitching near the spot. |
| `near_speed` | `0.8` | 0 or more | See `near_px`. |

## look

How the overlay looks. Colors and the font come from `screens.json` (`frame_lights` cyan, `panel_body`, `plating`). These values never change play.

| Field | Value now | Range | What it does |
|---|---|---|---|
| `key_size` | `30` | whole number, 1 or more | Side of each arrow key cap, in px. |
| `key_gap` | `6` | whole number, 0 or more | Space between key caps, in px. |
| `key_radius` | `5` | whole number, 0 or more | Corner radius of a key cap, in px. |
| `key_bottom` | `28` | whole number, 0 or more | Gap from the play area's bottom edge to the bottom row of keys, in px. |
| `arrow_size` | `6` | whole number, 1 or more | Half the width of the arrow on a key cap, in px. |
| `key_fade_ticks` | `5` | whole number, 1 or more | Ticks a key takes to light up or go dark. Short taps light it only partly. |
| `press_depth` | `2` | whole number, 0 or more | How far a held key sinks, in px. `0` keeps it still. |
| `idle_fill_alpha` | `26` | 0 to 255 | Fill of a key cap that is not held. |
| `idle_border_alpha` | `153` | 0 to 255 | Border of a key cap that is not held. |
| `lit_fill_alpha` | `235` | 0 to 255 | Fill of a held key cap. |
| `caption_role` | `"menu_item"` | a text role in `screens.json` `fonts` | Size and letter-spacing of the caption. |
| `caption_gap` | `18` | whole number, 0 or more | Gap from the caption's bottom to the top key, in px. |
| `caption_fade_ticks` | `10` | whole number, 1 or more | Ticks a new caption takes to fade in. |
| `caption_rise` | `6` | whole number, 0 or more | How far a new caption rises while it fades in, in px. `0` keeps it still. |
| `skip_margin` | `12` | whole number, 0 or more | Gap from the play area's top and right edges to the ENTER SPACE SKIP hint, in px. |
| `skip_word` | `"SKIP"` | text | The word after the skip keys. |
| `fade_in_ticks` | `0` | whole number, 0 or more | Ticks the run after the demo takes to fade in from black. `0` turns it off. |
| `coin_ring_radius` | `20` | whole number, 0 or more | Middle radius of the pulsing ring round the waiting coin, in px. `0` turns the ring off. |
| `coin_ring_pulse` | `3` | whole number, 0 or more | How far the ring's radius swings either way, in px. |
| `coin_ring_period_ticks` | `40` | whole number, 1 or more | Ticks of one pulse. Bigger is slower. |
| `coin_ring_alpha` | `200` | 0 to 255 | Brightness of the ring at its brightest. |
| `start_text` | `"START"` | text | The word that shows at the end, as the run is about to start. |
| `start_role` | `"menu_title"` | a text role in `screens.json` `fonts` | Size and letter-spacing of the start word. |
| `start_ticks` | `50` | whole number, 0 or more | The last ticks of the demo in which the start word shows instead of the caption. The HUD score goes back to 0 then. `0`: no start word. |
| `start_pop_ticks` | `12` | whole number, 1 or more | Ticks the start word takes to fade in and shrink to its size. |
| `start_scale` | `1.6` | number, 1 or more | How big the start word starts, times its size. `1` just fades in. |
| `start_y` | `150` | whole number, 0 or more | Height of the start word's center, px from the play area's top. |

## Quick recipes

| I want | Change |
|---|---|
| Longer or shorter hovers | `ticks` of the `pilot_to` steps. 60 is 1 s. |
| A longer START | `start_ticks`, and the same number more on the last hover step. |
| A different move | `keys` and `ticks` of a step. The coin follows the path on its own. Check the ship stays on screen: `game/tests/check.sh ui -k shipped_script`. |
| No demo | `enabled`: `false`. |
| Show the rare coin | `coin_variant`: `"rare"`. |
| No ring round the coin | `coin_ring_radius`: `0`. |
