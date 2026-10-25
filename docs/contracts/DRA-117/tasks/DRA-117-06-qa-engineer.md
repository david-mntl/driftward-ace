Feature: DRA-117
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-117/impact.md
Status: open
Linear: DRA-123

## Read in the contract
- drifters.md: systems/drifters/shared/base-interface.md: GrazeState, Birth (graze_margin), Drifter (graze_margin, graze_state, graze_zone), born_drifter
- drifters.md: systems/drifters/shared/base.md: Rules, Graze zone, Graze state
- drifters.md: systems/drifters/shared/spawner-registry-tuning.md: HazardRules; Rules, Spawner (step 8)
- run.md: Interface, "DRA-117: what graze adds and changes": core/graze.py (`GrazeRules`, `GrazeRing`, `graze_popup`, `graze_ring`, `step_graze_rings`), core/popup.py (`PopupKind`, `kind`)
- run.md: Rules, step 3a (rings), step 5b (Pay)

## Builds
- `game/tests/core/test_graze_feedback.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-117-01, DRA-117-02

## Not in the contract
- Like `test_drifters.py`, the new file builds its own `DrifterTuning` from the GDD values at the top of the file and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- The spawner hands every drifter the hazards' `graze_margin`; a hazard's zone is its hitbox grown by it, for the default and for a tuned margin, for every shape kind a hazard uses; it never changes as the hazard moves or with the level. Rules: base.md, Graze zone; Spawner (step 8).
- Every new drifter's `graze_state` is OUTSIDE, and an update carries it over unchanged. Rules: base.md, Graze state.
- A graze popup is of kind GRAZE, at the ship's center (after its move) on the paying tick, shows the graze points, rises by the rules' rise each tick, shows on exactly the rules' popup ticks and is gone after; a coin's popup keeps kind COIN. Rules: step 3a; step 5b (Pay); Interface (graze_popup, PopupKind).
- A graze ring starts at the start size at full opacity, grows and fades by an even step each state, shows on exactly the rules' ring ticks and is gone after, for the defaults and for non-default `GrazeRules`. Rules: step 3a; Interface (GrazeRing, step_graze_rings).
- Rings and graze popups keep aging during the respawn wait and on protected ticks. Rules: step 3a.
- `GrazeRules()` holds the GDD's graze values. Rules: Interface (GrazeRules); 06-scoring.md, Values.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_graze_feedback.py` in the `core` step and all its tests passing.

## Out of scope
- When a graze pays (task DRA-117-05). The views and the HUD (task DRA-117-07). The loaders in `game/app/`.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
