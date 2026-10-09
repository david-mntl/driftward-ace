# Electric ball
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
An electric ball that floats slowly and sends out a pulse on a timer. The pulse briefly makes its danger zone much bigger.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Slow patrol + pulse | — | — | locked | Director |
| enters_from | Mid-screen | — | — | locked | Director |
| priority | 4 | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | OBJ-10 |
| hitbox | TBD | shape, px | — | TBD | OBJ-10 |
| speed | TBD | px/tick at Level 1 | — | TBD | OBJ-10 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-10 |
| pulse_period | TBD | ticks | — | TBD | OBJ-10 |
| pulse_radius | TBD | px | — | TBD | OBJ-10 |
| pulse_ticks | TBD | ticks | — | TBD | OBJ-10 |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Purple spiky glowing orb | — | — | guess | Director |

## Rules
1. **Behavior:** Floats slowly; pulses on a timer.
2. Shared hazard rules apply ([../07-objects.md](../07-objects.md)).
3. Appears, telegraph, moves, hits, leaves, scales: TBD, see OBJ-10.

## Edge cases
TBD, see OBJ-10.

## Open
- OBJ-10.

## How to extend
Fill every TBD through OBJ-10 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
