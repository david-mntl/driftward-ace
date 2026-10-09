# Planet
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A planet that blocks the way and pulls the ship toward it when the ship is inside a fixed radius. The player must spend thrust to escape.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Blocker + gravity well | — | — | locked | Director |
| enters_from | Top | — | — | locked | Director |
| priority | 3 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-08 |
| hitbox | TBD | shape, px | — | TBD | OBJ-08 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-08 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-08 |
| pull_radius | TBD | px | — | TBD | OBJ-08 |
| pull_strength | TBD | px/tick² | — | TBD | OBJ-08 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Purple sphere with faint rings showing the pull radius | — | — | guess | Director |

## Rules
1. **Behavior:** Extra pull inside a fixed radius.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-08.

## Edge cases
TBD, see OBJ-08.

## Open
- OBJ-08.

## How to extend
Fill every TBD through OBJ-08 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
