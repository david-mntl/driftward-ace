Feature: DRA-158
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/audio.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-158/impact.md
Status: done
Linear: DRA-160

## Read in the contract
- audio.md: Interface, `game/core/sound_cue.py`, Rules, Which sounds
- run.md: Interface, DRA-158: the sound cues, Rules, Sound cues, step 5a, step 5b, step 6, step 7, The last life, A last-life tick, A game-over tick, `hold_arrows`, `next_run`

## Builds
- `game/core/sound_cue.py` (new): `SoundCue`
- `game/core/run.py` (changed): the `sound_cues` field, and its filling in the playing tick, the last-life tick and the game-over path

## Depends on
None

## Not in the contract
None.

## Acceptance check
A headless script (in the implementation report) steps runs and prints `sound_cues` after each tick it names. It shows: a tick that collects a coin gives `(COIN,)`; a tick that pays one graze gives `(GRAZE,)` and one that pays two gives two; a tick with an unprotected touch by two hazards gives one `HIT`; an unprotected fall gives one `HIT`; a protected fall and a touch while protected give `()`; a tick with a coin, a graze and a life lost gives them in that order; the tick that loses the last life, by a touch and by a fall, gives its `HIT`; the last-life ticks after it give `()`; the next tick after any of these, with nothing happening, gives `()`; `start_run()` and `next_run(run)` give `()`. `game/tests/check.sh lint` and `typecheck` pass and `core` has no failure `impact.md` doesn't expect.

## Out of scope
- Any sound, mixer, file, tuning file or `game/app/` code. Any view. `core/game_flow.py`.
- A sound for `level_up` or game over. Tests.
