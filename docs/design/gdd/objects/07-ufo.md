# UFO
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A UFO that moves in random but readable patterns. It's the one hazard the player can't fully memorize.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Wildcard mover | — | — | locked | Director |
| enters_from | Sides | — | — | locked | Director |
| priority | 3 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-07 |
| hitbox | TBD | shape, px | — | TBD | OBJ-07 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-07 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-07 |
| pattern_set | TBD | list of patterns | — | TBD | OBJ-07 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Saucer with a green dome, with a translucent cone beam below it | — | — | guess | Director |

## Rules
1. **Behavior:** Random but readable patterns.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-07.

## Edge cases
TBD, see OBJ-07.

## Open
- OBJ-07.

## How to extend
Fill every TBD through OBJ-07 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
