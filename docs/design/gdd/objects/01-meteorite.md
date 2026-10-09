# Meteorite
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A rock that drifts down from the top. It has no logic: it just falls. It's the first hazard every player meets, and Wave 0 uses only meteorites.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Falling blocker | — | — | locked | Director |
| enters_from | Top | — | — | locked | Director |
| priority | 1 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-01 |
| hitbox | TBD | shape, px | — | TBD | OBJ-01 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-01 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-01 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Grey rock with craters | — | — | guess | Director |

## Rules
1. **Behavior:** Drifts down; no logic.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-01.

## Edge cases
TBD, see OBJ-01.

## Open
- OBJ-01.

## How to extend
Fill every TBD through OBJ-01 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
