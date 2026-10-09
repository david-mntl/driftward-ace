# Coin
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A coin worth 50 points, always placed near danger. Taking it is a risk on purpose (Pillar 3).

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Pickup | — | — | locked | Director |
| enters_from | Inside waves | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-04 |
| hitbox | TBD | pickup shape, px | — | TBD | OBJ-04 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-04 |
| graze | no | — | — | locked | 06-scoring.md (coins never pay) |
| look_reference | Yellow four-point sparkle star; '+50' pops up on pickup | — | — | guess | Director |

## Rules
1. **Behavior:** +50 points; placed near danger.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-04.

## Edge cases
TBD, see OBJ-04.

## Open
- OBJ-04.

## How to extend
Fill every TBD through OBJ-04 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
