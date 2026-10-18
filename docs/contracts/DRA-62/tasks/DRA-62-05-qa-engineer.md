Feature: DRA-62
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-74

## Read in the contract
- Interface, `game/core/drifters/coin.py`: `CoinVariantExtra`, `CoinTypeExtra`, `coin_hitbox`.
- Rules: Collision (strict overlap); Coin (Size and hitbox; Born; No warning of any kind; Touch); Tuning files (The coin's file: what the loader builds from it).
- `docs/contracts/schemas/coin-tuning.schema.json`: the file the test reads.
- Impact, the DRA-62 table (the `test_collision.py` row: why the file breaks today).

## Builds
- `game/tests/core/test_collision.py` (changed)
- `game/tests/CONTEXT.md` (changed: the `core/test_collision.py` paragraph)

## Depends on
DRA-62-01, DRA-62-03, and `game/tuning/drifters/coin.json` filled to its schema (content, by whoever the Director names; contract Impact).

## Not in the contract
- Like the fireball's, the coin gets its own branch in `load_variant_cases`, built from the file the way `app.tuning` builds it (contract, Tuning files), with no variant named in test code. Source: tests/CONTEXT.md, Rules (the `core/test_collision.py` paragraph).

## Test
- The ship meets every coin variant at its own touching distance from each of the four sides: it overlaps with the coin's box 0.5 px inside the ship, and doesn't when just clear. Rules: Coin (Size and hitbox); Collision.
- A coin overlaps the ship on the very state it is spawned on: it has no WARNING state with an empty hitbox. Rules: Coin (Born; No warning of any kind).
- Only the 12 × 10 box counts: a coin placed so that its points or its ring would cross the ship's edge, but its box doesn't, doesn't overlap. Rules: Coin (Size and hitbox).
- A coin's touch is a collect, never a hit, for every variant. Rules: Coin (Touch).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the coin cases in `test_collision.py` in the `core` step.

## Out of scope
- The coin's own behavior, the run's collect rules and the popups (task DRA-62-06).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
