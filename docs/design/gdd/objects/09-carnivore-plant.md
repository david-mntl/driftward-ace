# Carnivore plant
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
A plant fixed to a side wall. When the ship comes near, it charges, then lunges. It punishes hugging the walls.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Static + lunge attack | — | — | locked | Director |
| enters_from | Sides | — | — | locked | Director |
| priority | 4 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-09 |
| hitbox | TBD | shape, px | — | TBD | OBJ-09 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-09 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-09 |
| trigger_range | TBD | px | — | TBD | OBJ-09 |
| charge_ticks | TBD | ticks | — | TBD | OBJ-09 |
| lunge_reach | TBD | px | — | TBD | OBJ-09 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Red flytrap head on a green stem with leaves | — | — | guess | Director |

## Rules
1. **Behavior:** Charges when you're near, then lunges.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-09.

## Edge cases
TBD, see OBJ-09.

## Open
- OBJ-09.

## How to extend
Fill every TBD through OBJ-09 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
