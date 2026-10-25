# Wave editor

A desktop tool to play, rewind and scrub the real game, edit a wave, and tune drifter values by playing them. It never ships and it never changes game code.

## Start

```
tools/scripts/start-wave-editor.sh                        # plays the debug spawn list
tools/scripts/start-wave-editor.sh game/waves/l1_a.json   # plays one wave, looped
tools/scripts/start-wave-editor.sh tools/wave_editor/sandbox/my_wave.json
```

Needs python3 and pygame-ce. Opening a game wave opens a **copy**. Nothing under `game/` is written except by Promote.

## Screen

- **Left top (WAVE):** the placements, one per row: scroll distance in px, the time it appears, its x and y, then the drifter. Bright rows have already spawned. The highlighted row is selected.
- **Left middle (DRIFTERS):** the palette. Drifter types on the left, the variants of the chosen type on the right (`*` marks the default).
- **Left bottom (KEYS):** the key table.
- **Middle:** the game at 640x480, the timeline under it, then messages. A yellow ring marks the selected drifter.
- **Right top (CONFIG):** level, speed, ghost or fly, start spot, live numbers.
- **Right bottom (WAVE / SELECTED):** the wave's settings, then the graze margin, then the selected placement's fields, then the values of its drifter type, each tagged W, F or P. Variant values sit under a small heading per variant.

## Selecting and editing

Click a drifter in the game view, or press Tab to the WAVE panel and use Up/Down. Tab again goes to the SELECTED panel.

In the SELECTED panel:

| Key | Does |
|---|---|
| Up / Down | pick a row |
| Left / Right (or `-` / `=`) | nudge. Shift + arrow = x10 |
| Enter | type a value |
| D | back to default (see below) |
| F | cycle the named tuning files of this type |
| V | save the type's values as a named file |

Every change goes through the game's own loaders. A bad value is refused, undone, and the error shows under the timeline in red. The run replays to the same tick, so you see the change at once.

## Grazes

The bench plays the game's graze rule with the game's own values (`game/tuning/scoring.json`, `hazards.json`). A paid graze adds its points to the score, shows the popup and the white ring, and the CONFIG panel counts `Grazes` and shows the `Margin` in px. F3 outlines every graze zone next to the hitboxes.

- **Fly mode only.** The ghost is always invulnerable, and an invulnerable ship never grazes. The panel says `ghost: no grazes`. Use F3 in ghost mode to see the zones, and fly mode to see them pay.
- **Graze margin.** The `graze_margin` row (under `graze (all hazards)` in the right panel) is the px every hazard's graze zone grows by. It is one number for all drifters, so it has no F layer: W is your change in this file, P is `hazards.json`. Left/Right nudge 1 px (Shift x10), Enter types a value (above 0), D goes back to production. The sandbox file saves it as `hazards`. Promote lists `tuning/hazards.json` when you changed it, and patches only that number.
- The other graze values (points, popup, ring) are read from `scoring.json` and reload with the file, but are not editable here.

## Path trail

The selected placement's drifter shows its path in the game view, before it even spawns: a dim green line while it warns, a bright one once active, a dot every half second, and a ring where it starts. It follows the level you picked and the ship's position now (a drifter that follows the ship follows that fixed ship). T turns it off.

## New wave

Ctrl+N asks for a name (lower case letters, digits, `_`) and starts an empty fixed wave of 1320 px in the sandbox, with the palette focused. Add drifters, set the length and kind in the right panel, Ctrl+S to save, Ctrl+P to promote it as a new file in `game/waves/`. Remember to add it to `game/waves/playlist.json` yourself.

## Mouse

- **Panels:** click a panel, or any row in it, to give it the focus (no Tab needed). The focused panel has a yellow border. In the wave list a click selects that placement. In the right panel a click puts the cursor on that row.
- **Game view:** click a drifter to select its placement and focus its values, so Left/Right nudge it straight away. Click empty space to give the game view the focus (fly mode steers with the arrow keys only then).
- **Coordinates:** the x and y under the mouse show next to the pointer, in game pixels (the same numbers as the `x` and `y` fields).
- **Placing:** see "Adding a drifter" below.

## Adding a drifter

**With the mouse:** click a drifter type in the DRIFTERS panel (it takes its default variant), or click one of its variants. It is now armed: a crosshair follows the mouse over the game view and the status line says `PLACING`. Click in the game view to place it there. It stays armed, so you can click again and again; Esc stops. The drifter appears at the playhead (rounded to 10 px, never inside the first 120 px). Pause where you want it to appear, or nudge `at_px` afterwards.

**Invert switch:** the pill at the top right of the DRIFTERS panel (or the I key). When it is on, every drifter you place from the palette gets `invert: true`, so you pick the mirrored version from the start. The status line says `INVERTED` while placing. It can be flipped while a drifter is armed, and applies to the next one placed. A drifter with no mirror (the meteorite and the coin) is placed as it is, and the message says so. Inverted: a satellite and a fireball come from the right and fly left; a chain lightning is mirrored.

A click gives a drifter the coordinates it uses: a meteorite, a chain lightning, a fireball, a floating island and a planet take the click's `x` (they come in from the top), a satellite and a UFO take `y` (they cross at that height), a coin takes both. A satellite or a UFO enters from the left unless the invert switch is on.

**With the keyboard:**

Tab to the palette (or click it), Up/Down to pick, Left/Right to switch between types and variants, Enter to add it at the playhead (rounded to 10 px, never inside the first 120 px, the seam), at the middle of the screen. A type without a variant pick adds its default variant.

The new placement gets the fields the game needs (an `x` of 320 or a `y` of 240), is selected, and the cursor sits on `at_px` so you can nudge it at once. The game's own checks run on it: if it refuses, nothing is added and the reason shows. The mouse wheel scrolls a list that is longer than the panel. Needs a wave, so open one first (Ctrl+O) when the bench started on the spawn list.

**Wave settings** are the first rows of that panel (Tab to it, cursor on `length_px`):

| Row | Edit |
|---|---|
| `length_px` | Left/Right nudge 10 px (Shift 100), or Enter and type. The heading shows the length in seconds at the current level. |
| `kind` | Left/Right toggles fixed / pool. Pool adds `min_level` 1, fixed removes it. |
| `min_level` | Left/Right, pool waves only (1 to 8) |
| `extra_rest_ticks` | Left/Right, D removes it |

Placement fields: `at_px`, `x`, `y`, `variant`, `invert` are editable. The type is fixed until the palette (C-lite). In the WAVE panel, Del deletes the selected placement.

## Time and defaults

`at_px` also shows when the drifter appears: `300  4.5s` means 300 px of scroll, which is 4.5 seconds into the wave **at the level you picked** (scroll gets faster with the level, so the same px is earlier at Level 8). The WAVE list on the left shows the same time next to each placement, and the heading of the wave settings shows the length in seconds.

D puts the selected row back to its default:

| Row | D does |
|---|---|
| a drifter value (tuning) | drops the W change, back to the drifter's tuning file (P, or the named file F) |
| `variant` | removes it, so the drifter uses its tuning's `default_variant`. The row shows `default (medium)` |
| `invert` | removes it |
| `x`, `y` | removes it, so the drifter uses its own start position. If the drifter has none (a meteorite needs an `x`, a satellite a `y`), it goes back to the value a new placement starts with: 320 / 240 |
| `at_px` | no default: it is where you want the drifter to appear |
| `length_px`, `kind`, `min_level` | back to what a new wave gets: 1320, fixed, 1 |
| `extra_rest_ticks` | removed (0) |

## The three layers (W, F, P)

Each drifter value comes from the first layer that has it:

- **W** inline change in this sandbox file. Only the values you touched.
- **F** a named tuning file, a full copy in `sandbox/tuning/`. It never moves when production changes.
- **P** production, `game/tuning/drifters/<type>.json`.

Nudge or type a value and it becomes **W**. D on a W value drops it back to F or P. D on an F value unlinks the named file, so all of that type's values go back to production. V writes the type's current values to a new named file and links it.

## Files

| Key | Does |
|---|---|
| Ctrl+S | save the sandbox file (`tools/wave_editor/sandbox/<name>.json`) |
| Ctrl+Shift+S | save as (type a path, it never writes under `game/`) |
| Ctrl+N | new empty wave |
| Ctrl+O | open a sandbox file or a game wave |
| Ctrl+P | promote |

**Promote** lists what it would write: the wave file in `game/waves/`, one `game/tuning/drifters/<type>.json` per changed type, with the value diffs and which other waves use that type, and `game/tuning/hazards.json` if the graze margin changed. Space ticks an item, Enter writes only the ticked ones. A tuning file is patched in place, so only the changed numbers differ. After writing a type, its W and F layers are dropped, because production now has them. The same goes for the graze margin after `hazards.json`. `playlist.json` is never touched. Nothing is committed. `wave_check` is not built yet.

## Play keys

| Key | Does |
|---|---|
| Space | play / pause |
| `,` `.` | step 10 ticks back / forward |
| Z X | step 1 tick back / forward |
| W / S | speed up / down (0.25x to 4x) |
| Home | restart |
| `[` `]` | level down / up (restarts) |
| G | ghost or fly (restarts) |
| 1 2 3 | ghost start spot: left, centre, right (restarts) |
| L | loop on / off |
| F3 | hitboxes |
| T | path trail on / off |
| Esc | stop placing, or cancel a prompt, or give the focus back to the game view. It never quits. |
| window close button | quit |
| drag the bar | scrub |

**Ghost:** the ship is hidden and held at the start spot. It cannot be hit, so the wave plays by itself.
**Fly:** you steer with the arrow keys (only while the game view has focus). Lives and game over work as in the game.

## Hot reload

Edit a file in `game/tuning/` or the wave file you opened, and save. The bench reloads within about half a second and replays to the same tick. If the file has an error, the old values stay and the message shows in red. A sandbox file you edited in the tool is not re-read from disk until you save it.

## Limits for now

- One wave at a time.
- Changing a placement's type: delete it and add a new one.
- The path trail is one drifter alone: it does not show hits or the other drifters.
- Scrubbing past the furthest tick plays ahead with no thrust.
- The ghost's hitbox outline shows when F3 is on.
- Plan and next parts: [PLAN-wave-editor.md](../PLAN-wave-editor.md).
