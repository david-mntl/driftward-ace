Feature: DRA-39
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/drifters.md
Status: done
Linear: DRA-46

## Read in the contract
- run.md: Diagram (one tick, re-hit cooldown); Rules, a playing tick, steps 2, 3, 6, 7, 8 and 9; A game-over tick; Other rules; Logging; Impact.
- drifters.md: Rules, The base (Entering, Leaving, Re-hit cooldown); Satellite (Start, Leaving, Speed at Level 1); Diagram, Re-hit cooldown of one hazard, Meteorite timeline and Satellite timeline.

## Builds
- `game/tests/core/test_run_drifters.py` (changed: the DRA-29 tests brought up to the contract, and the new tests)

## Depends on
DRA-39-01, DRA-39-03

## Not in the contract
- Satellite and re-hit numbers come from drifters/02-satellite.md and 05-lives-and-damage.md, copied with their source; never imported from the code under test.

## Test
- A hit sets `rehit_ticks_left` to the drifter's `rehit_cooldown_ticks` on every touching drifter, costs one life, and the drifter stays and keeps moving. Rules: run.md, step 7.3 and 7.6.
- The hazard that hit can't hit on the next `rehit_cooldown_ticks` ticks while it keeps overlapping the ship, with invulnerability long over, and hits again on the tick after: at the default 180 and at a small set value. Rules: run.md, steps 7.1 and 8; drifters.md, Re-hit cooldown.
- Along the way `brightness()` is `rehit_dim` from the state after the hit through the state after the 179th tick after it, and 1.0 from the state after the 180th. Rules: run.md, step 8; drifters.md, Diagram (re-hit timeline).
- While one hazard cools down, another one touching the ship hits as soon as invulnerability ends, and only its own cooldown starts; the first one's count goes on unchanged. Rules: run.md, step 7.3.
- Two hazards touching on one tick cost one life and both start their cooldown. Rules: run.md, step 7.3.
- A touch on a protected tick starts no cooldown; a running count keeps going on protected ticks, during the respawn wait and on a tick with a fall; it freezes at game over, and a retry starts with no drifters. Rules: run.md, steps 7.2 and 8; Other rules.
- A flat satellite placed just outside the left wall at Level 1 is not dropped while it sits outside (including its first ACTIVE state at x −18), enters on its next tick, and is dropped on the state after its 274th active tick. Rules: run.md, steps 3 and 9; drifters.md, Leaving; Satellite timeline.
- A drifter that never enters (a satellite placed outside the left wall with `invert`, so it flies away) is never dropped. A meteorite is still dropped after 206 active ticks. Rules: run.md, step 9; drifters.md, Leaving; Meteorite timeline.
- A satellite's life logs exactly one `drifter spawn`, one `drifter active` and one `drifter gone`, in that order, plus one `drifter touch` per hit. Rules: run.md, Logging.
- The DRA-29 tests are brought up to the contract: `rock()` without `hit_ship`, every `hit_ship` check turned into a `rehit_ticks_left` check, and `test_a_meteorite_hits_once` replaced by the cooldown tests above. Rules: run.md, Impact.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` (with tasks DRA-39-05 and DRA-39-06 done, or only their own files failing), and the `core` step runs the updated `tests/core/test_run_drifters.py` with the new cooldown and entering tests in it.

## Out of scope
- Collision tables (task DRA-39-05). Base, spawner and satellite unit tests (task DRA-39-06).
- `tests/core/test_run.py`: it must still pass unchanged.
- Views, pixels, the app's loaders and the spawn list.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
