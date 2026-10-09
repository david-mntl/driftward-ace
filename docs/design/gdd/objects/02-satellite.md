# Satellite
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A satellite that crosses the screen from the side in a fixed pattern that repeats. The player learns the pattern and threads past it.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Patrol mover | — | — | locked | Director |
| enters_from | Sides | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-02 |
| hitbox | TBD | shape, px | — | TBD | OBJ-02 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-02 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-02 |
| pattern | TBD | path shape | — | TBD | OBJ-02 |
| period | TBD | ticks | — | TBD | OBJ-02 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | White body with blue solar panels on both sides | — | — | guess | Director |

## Rules
1. **Behavior:** Crosses in a fixed, repeating pattern.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-02.

## Edge cases
TBD, see OBJ-02.

## Open
- OBJ-02.

## How to extend
Fill every TBD through OBJ-02 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
