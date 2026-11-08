Feature: DRA-158
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-158/impact.md
Status: open
Linear: DRA-161

## Read in the contract
- run.md: Interface, DRA-158: the sound cues; Rules, Sound cues; steps 5a, 5b, 6 and 7; The last life; A last-life tick
- game-flow.md: Rules, `run_stepped`

## Builds
- `game/tests/core/test_run_sound_cues.py` (new)
- `game/tests/CONTEXT.md` (changed): one line for the new file

## Depends on
DRA-158-01

## Not in the contract
None.

## Test
- a collected coin gives one COIN on that tick and nothing on the next. Rules: Sound cues, 1
- one paid graze gives one GRAZE; two paid on one tick give two. Rules: Sound cues, 2
- an unprotected touch gives one HIT, and two touching hazards still give one. Rules: Sound cues, 3
- an unprotected fall, to a life left, gives one HIT. Rules: Sound cues, 3
- a protected fall and a touch while protected give no cue. Rules: Sound cues, 3
- a tick with a coin, a graze and a life lost gives COIN, GRAZE, HIT in that order. Rules: Sound cues
- the tick that loses the last life gives its HIT, by a touch and by a fall, after that tick's COIN and GRAZE. Rules: Sound cues, 3; The last life
- the last-life ticks after it and a game-over tick give no cue. Rules: Sound cues; A last-life tick
- a quiet tick after a tick with cues gives none: a cue is never carried over. Rules: Sound cues
- `start_run()` and `next_run(run)` give no cue. Rules: Sound cues
- a paused tick, with the run holding cues from its last stepped tick, leaves `flow.run_stepped` False. Rules: Sound cues; game-flow.md, `run_stepped`

## Acceptance check
`game/tests/check.sh` ends `QA: pass` with the new tests in it.

## Out of scope
- Tests for the audio player, the mixer, the tuning loader or any `game/app/` code. They run in the browser at integration.
- Changing a contract or game code.
