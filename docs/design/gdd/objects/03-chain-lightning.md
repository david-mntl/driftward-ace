# Chain lightning
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
Glowing nodes appear mid-screen. A charge line shows between them, then an arc fires along that line. The warning is the whole point: the player sees exactly where the strike will land.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Telegraphed link | — | — | locked | Director |
| enters_from | Mid-screen | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-03 |
| hitbox | TBD | shape, px | — | TBD | OBJ-03 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-03 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-03 |
| node_count | TBD | nodes | — | TBD | OBJ-03 |
| charge_ticks | TBD | ticks | — | TBD | OBJ-03 |
| arc_ticks | TBD | ticks | — | TBD | OBJ-03 |
| arc_width | TBD | px | — | TBD | OBJ-03 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Cyan glowing nodes joined by a jagged white-blue arc; a dotted line while charging | — | — | guess | Director |

## Rules
1. **Behavior:** Charge line shows, then an arc fires.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-03.

## Edge cases
TBD, see OBJ-03.

## Open
- OBJ-03.

## How to extend
Fill every TBD through OBJ-03 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
