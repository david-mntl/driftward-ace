---
name: ui-art-loop
description: Make one art asset and refine it against the GDD with no input from the Director. Runs the Art & Audio Engineer (make), the UI Art Critic (score) and the Art & Audio Engineer again (refine), up to 3 rounds. The Director starts it with /ui-art-loop <asset> <kind> <brief>.
argument-hint: <asset> <sprite|screen|background> <brief>
disable-model-invocation: true
---

Run the art loop for `$ARGUMENTS`. You only start agents, measure images and read reports. Never draw, edit or move an image, and never write a report yourself. Never ask the Director anything during the run.

## 0. Read the arguments
- First word: the asset name, lowercase with dashes, for example `meteorite-a`. Every file of the run carries it.
- Second word: the kind, `sprite`, `screen` or `background`. Its folder in `staging/assets/`: `sprites/`, `ui/`, `backgrounds/`.
- The rest: the brief for round 1. What to make, which GDD spec it follows, and how: a script, a photo URL to convert, or a file in `staging/art-inbox/` to convert.

If the name, the kind or the brief is missing, or the kind is not one of the three, stop and show the usage line.

Files of round `<n>`:
- image: `staging/assets/<folder>/<asset>-r<n>.png`
- board: `staging/assets/<folder>/<asset>-r<n>-board.png`
- report: `docs/reports/ui-art/<asset>-r<n>.md`

## 1. Resume or start
List `docs/reports/ui-art/<asset>-r*.md`.
- None: if the round 1 image and board exist, go to step 3 for round 1. Otherwise start at round 1, step 2.
- Some: take the highest round `<n>`. If the round `<n+1>` image and board already exist, go to step 3 for round `<n+1>`. Otherwise read line 1 of report `<n>`. If it meets the stop rule (step 5), or `<n>` is 3, the loop already ended: go to the final message. Otherwise go to step 6 for round `<n>`.

## 2. Make (round 1)
Start `art-audio-engineer` with:
"Loop round 1. Asset: `<asset>`. Kind: `<kind>`. Brief: `<brief>`. Write the image `<image path>` and the board `<board path>`."

The agent picks Request or Convert mode from the brief. Read its delivery report. Status `staged` means the files wait in staging for the Director; that is a success, go on. Status blocked, or the image or the board is missing: stop.

## 3. Measure
Run, for the round's image:
```
python3 -c "import sys; from PIL import Image; print('%d x %d px' % Image.open(sys.argv[1]).size)" <image path>
```
Keep the output and the frame count and frame size from the art agent's Checks.

## 4. Score
Start `ui-art-critic` with:
"Judge mode. Asset: `<asset>`. Kind: `<kind>`. Round: `<n>`. Image: `<image path>`. Board: `<board path>`. Measured: `<size>`; frames: `<count and frame size, or none>`. Meant to be: `<brief>`. Previous report: `<path, or none>`."

Read line 1 of the round's report: `Score: <avg> | Lowest: <n> | Size: <n>`. Status blocked, or no report: stop.

## 5. Stop rule
Stop when all three hold:
- Score is 8 or more,
- Lowest is 6 or more,
- Size is 8 or more. `Size: n/a` counts as met; list it in the final message.

Also stop after round 3, whatever the score. Otherwise go on.

## 6. Refine (rounds 2 and 3)
Start `art-audio-engineer` with:
"Refine mode. Report: `docs/reports/ui-art/<asset>-r<n>.md`. Write the image `<round n+1 image path>` and the board `<round n+1 board path>`."

Status `staged` is a success, as in step 2. Status blocked, or a file missing: stop. Otherwise go to step 3 with round `<n+1>`.

## When to stop early
Stop and tell the Director when:
- an agent reports `blocked` (not `staged`), or a pending documentation difference
- a round's image, board or report is missing
- the measure step fails

Say which round and step you stopped on, and the file to read.

## Final message
Keep it short:
- one row per round: round, Score, Lowest, Size, image, board, report
- why it stopped: the stop rule met in round `<n>`, or the 3-round cap
- the best round, if it isn't the last one
- anything the agents listed as unsure, and any `n/a` criterion with its open-question ID
- next: every round waits in `staging/assets/<folder>/` for the Director. Nothing moves to `game/assets/` until the Director names the file to approve.
