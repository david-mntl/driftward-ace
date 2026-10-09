# Fireball
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A fast fireball that crosses the screen on a straight diagonal from a corner or side. It never targets the ship. The entry warning is what makes it fair.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Fast linear hazard | — | — | locked | Director |
| enters_from | Corners, sides | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-06 |
| hitbox | TBD | shape, px | — | TBD | OBJ-06 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-06 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-06 |
| angle | TBD | degrees | — | TBD | OBJ-06 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Orange-yellow comet with a fading trail | — | — | guess | Director |

## Rules
1. **Behavior:** Fast straight diagonal; no targeting.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-06.

## Edge cases
TBD, see OBJ-06.

## Open
- OBJ-06.

## How to extend
Fill every TBD through OBJ-06 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
