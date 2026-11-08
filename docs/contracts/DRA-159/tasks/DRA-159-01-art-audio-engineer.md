Feature: DRA-159
Created by: architect
Assignee: art-audio-engineer
Writes to: tools/art/, staging/assets/, game/assets/
Contract: docs/contracts/systems/mute-icon.md, docs/contracts/schemas/mute_icon.schema.json
Impact: docs/contracts/DRA-159/impact.md
Status: done
Linear: DRA-162

## Read in the contract
- mute-icon.md: Interface, The picture, game/tuning/mute_icon.json, Rules, Look, Cost, Cheap to draw, Rationale, A picture, baked from tuning
- mute_icon.schema.json: `size`, `speaker_color`, `slash_color`

## Builds
- `tools/art/mute_icon.py` (new): reads `game/tuning/mute_icon.json`, draws the large master, shrinks it and writes the picture
- `staging/assets/ui/mute_icon.png` (new), `staging/assets/ui/mute_icon-master.png` (new)
- `staging/assets/CREDITS.md` (changed): one entry
- `game/assets/mute_icon.png` (new): the staged picture, moved after the checks
- `game/assets/CREDITS.md` (changed): the entry moved

## Depends on
None

## Not in the contract
- No separate approval round is needed. The Director left the look to the main session, which treats it as approved (`docs/design/gdd/91-decision-log.md`, row 148; `docs/design/gdd/10-ui.md`, `mute_icon_look`). Stage the files, run the checks, then move the picture to `game/assets/` and its CREDITS entry, and report done. This task file names `game/assets/mute_icon.png`, so it counts as the explicit request your rules ask for.
- `game/tuning/mute_icon.json` is written by the main session before this task runs. If it does not exist, stop and report blocked. You never write it. If the two colors it holds look wrong on the dark panel at 1x, say so under Next with the hex values you propose from the palettes in `12-art-and-audio.md`: the main session changes the file and you run the script again.
- Master factor: the one `mute_icon_look` names. `art_style` names a different factor for small sprites; the Architect has asked the Director to settle the difference, so use the row's.

## Acceptance check
`python tools/art/mute_icon.py` writes the picture. `game/assets/mute_icon.png` opens, is exactly `size` x `size` px with `size` from `game/tuning/mute_icon.json`, has an alpha channel with a transparent background, and shows a pale violet-white speaker with a fuchsia slash through it, in the two colors of that file. Its CREDITS entry names the script and the task.

## Out of scope
- Any tuning value, any code in `game/`, any other picture, any sound.
- Changing the icon's look beyond what `mute_icon_look` says: no blink frames, no glow, no text.
