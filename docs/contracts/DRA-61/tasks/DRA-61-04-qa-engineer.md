Feature: DRA-61
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md
Status: open
Linear: DRA-66

## Read in the contract
- Interface, `game/core/run.py`: `POINTS_PER_METER`, `coin_points`, `score`, `start_run`.
- Diagram: the score timeline.
- Rules: Score (all of it); a game-over tick; Logging (the "Nothing else" line).
- `docs/contracts/systems/scroll.md`, Rules, Distance (the meters the score counts).

## Builds
- `game/tests/core/test_run_score.py` (new)

## Depends on
DRA-61-01

## Not in the contract
- Like `test_run.py`, the file takes every expected number from the GDD values at the top of the file and none from the code under test. Source: tests/CONTEXT.md, Rules.

## Test
- A new run has score 0 and coin points 0. Rules: Score (Start and retry).
- Through a run, the score equals the whole meters flown, rounded down, 1 point a meter: 0 for the first 30 ticks and until 10 px have scrolled, then counting up. Rules: Score (Formula); scroll.md, Distance.
- The score is the meters plus the coin points: a run with coin points set reads meters + coin points. Rules: Score (Formula, Coin points).
- No playing tick changes the coin points, with falls, the respawn wait and a game over in the run. Rules: Score (Coin points).
- The score never goes down over a long run with falls, respawns and the wait, and keeps counting through them. Rules: Score (Never goes down).
- At game over the score stops: it is the same on every game-over tick until the retry. Rules: Score (Game over); a game-over tick.
- A retry gives score 0 again. Rules: Score (Start and retry).
- No log line names the score, and `game over meters=` keeps its text. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_run_score.py` in the `core` step.

## Out of scope
- Coins, coin collection, grazes (DRA-62 and later).
- The HUD, `score_text` and the Game Over box (tasks DRA-61-05 and DRA-61-07).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or the existing test files.
