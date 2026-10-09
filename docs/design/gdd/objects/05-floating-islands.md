# Floating islands
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
Static slabs of floating ground span the screen, leaving one gap to fly through. They force the player to a single path.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Forced-path blocker | — | — | locked | Director |
| enters_from | Top | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-05 |
| hitbox | TBD | shape, px | — | TBD | OBJ-05 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-05 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-05 |
| slab_height | TBD | px | — | TBD | OBJ-05 |
| gap_width | TBD | px, ≥ gap_min (09-waves.md) | — | TBD | OBJ-05 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Green slabs with a darker edge | — | — | guess | Director |

## Rules
1. **Behavior:** Static slabs span the screen, leaving one gap.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-05.

## Edge cases
TBD, see OBJ-05.

## Open
- OBJ-05.

## How to extend
Fill every TBD through OBJ-05 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
