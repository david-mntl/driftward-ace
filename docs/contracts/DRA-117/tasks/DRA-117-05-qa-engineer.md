Feature: DRA-117
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md
Impact: docs/contracts/DRA-117/impact.md
Status: done
Linear: DRA-122

## Read in the contract
- Diagram: the two graze state tables
- Interface, "DRA-117: what graze adds and changes": core/graze.py (`check_grazes`, `GrazeCheck`, `GrazeRules`), core/run.py
- Rules: step 5b (all ten items); a game-over tick (retry); Score (Formula, Grazes, Never goes down, Game over); Other rules (game over tick, Grazes); Logging (`drifter graze`, the order inside one tick, Nothing else)

## Builds
- `game/tests/core/test_run_graze.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)
- Any existing core test that `impact.md` lets fail from DRA-117-02 (changed), only where it fails for that reason

## Depends on
DRA-117-01, DRA-117-02

## Not in the contract
- Like `test_run_score.py` and `test_coin.py`, the new file builds its own `DrifterTuning` from the GDD values at the top of the file and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- A hazard the ship passes beside, never touching it, pays one graze on the tick the ship leaves its zone, and none before. Rules: step 5b (Inside now, Exit, Pay).
- Entering and leaving the same hazard's zone again pays nothing more. Rules: step 5b (Spent stays spent).
- A hazard that hits the ship never pays, before or after the hit; neither does one the ship passed through while invulnerable, nor one it touched while standing in the respawn wait. Rules: step 5b (Touch).
- An exit on a protected tick pays nothing and leaves the hazard OUTSIDE; a later clean exit by the same hazard, unprotected, pays. The last protected tick doesn't pay; the first unprotected one does. Rules: step 5b (Exit, Protected).
- A ship that entered the zone while invulnerable and leaves after protection ended pays. Rules: step 5b (Protected).
- An exit while standing in the respawn wait pays nothing, even after invulnerability ran out; an exit on the press tick that ends the wait pays. A ship hovering in place can graze. Rules: step 5b (Waiting).
- A chain lightning or an electric ball that stops firing with the ship in its zone pays; its next firing never pays again. Rules: step 5b (Inside now, Exit, Spent stays spent).
- A hazard dropped off screen with the ship in its zone pays on the tick it is dropped. Rules: step 5b (Inside now).
- Coins and floating islands never change graze state and never pay. Rules: step 5b (Who takes part).
- Two hazards left on one tick pay two grazes, in drifter order, with two popups and two rings. Rules: step 5b (Pay).
- Grazes stack with no cap: the score is meters plus coin points plus the grazes times the graze points, also with non-default `GrazeRules` points. Rules: Score (Formula, Grazes).
- A graze and a hit by another hazard on one tick: the graze pays, then the hit counts; on the last life the final score includes the graze. A graze on a fall tick pays. Rules: step 5b (item 10); Score (Game over).
- Game over freezes the grazes and the rings; a retry gives 0 grazes, no rings and the same graze values, with and without waves. Rules: a game-over tick; Score (Grazes).
- `start_run()` with no graze values has the GDD defaults, and the score with no graze equals the old formula. Rules: Score (Formula); Interface (start_run).
- It logs one `drifter graze id=<n> type=<type>` per paid graze, after the collect lines and before the hit lines, and nothing for an entry, a touch or a blocked exit. Rules: Logging.
- `check_grazes` never mutates its input; the same input gives the same result. Rules: step 5b.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_run_graze.py` in the `core` step and all its tests passing.

## Out of scope
- The graze margin from tuning, the popup's and the ring's own state over time (task DRA-117-06). The views and the HUD (task DRA-117-07).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
