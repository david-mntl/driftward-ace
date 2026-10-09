# <Object name>
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules)

## Summary
<2–3 plain sentences: what it is, what it does, why the player fears or wants it.>

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | <from the routing table> | — | — | locked | 07-objects.md |
| enters_from | <top / sides / corners / mid-screen> | — | — | locked | 07-objects.md |
| priority | <1–4> | — | — | guess | 07-objects.md |
| size | TBD | px | — | TBD | <ID> |
| hitbox | TBD | shape, px | — | TBD | <ID> |
| speed | TBD | px/tick at Level 1 | — | TBD | <ID> |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | <ID> |
| graze | yes / no | — | — | — | 06-scoring.md |

Add one row per extra value (pull strength, pulse period, lunge range...).

## Rules
1. **Appears:** where and how it enters, and its entry warning.
2. **Telegraph:** what the player sees before it can hit, and for how long.
3. **Moves:** its path, step by step, in ticks. Say "no targeting" or say exactly how it reacts to the ship.
4. **Hits:** what touching it does. Default: a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)).
5. **Leaves:** when it despawns.
6. **Scales:** which values the level's hazard speed multiplies ([../08-difficulty.md](../08-difficulty.md)).
7. **Looks and sounds:** sprite notes, animation, sound cue.
8. **wave_check notes:** anything the checker must test for this object.

## Edge cases
<the ship touches it while invulnerable; it meets a wall; it leaves the screen; two overlap...>

## Open
<IDs from ../90-open-questions.md>

## How to extend
A variant with the same archetype changes values only and stays in this file. A new behavior is a new object: copy the template.
