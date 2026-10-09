# Lava walls
Status: draft
Depends on: [../07-objects.md](../07-objects.md) (shared hazard rules), [../08-difficulty.md](../08-difficulty.md), [../09-waves.md](../09-waves.md)

## Summary
A wave hazard that turns the side walls to lava for a while. It can show up in waves from Level 4 on. It is not always on: in a wave it may switch on for a few seconds, switch off, come back, or stay on for the whole wave. The timing is random for each wave. While it's on, touching a wall is a hit. It takes away the safe wall-hug.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Boundary hazard | — | — | locked | Director |
| enters_from | Sides | — | — | locked | Director |
| available_from | Level 4 | level | — | locked | Director, [../08-difficulty.md](../08-difficulty.md) |
| priority | 3 | — | — | guess | 07-objects.md |
| activation | random per wave: on for a while, maybe again, maybe the whole wave | — | — | locked | Director |
| random_ranges | TBD | ticks, count | — | TBD | OBJ-11 |
| lava_width | TBD | px | — | TBD | OBJ-11 |
| hitbox | TBD | wall strip, px | — | TBD | OBJ-11 |
| telegraph | TBD | look, ticks at Level 1 | — | TBD | OBJ-11 |
| graze | no | — | — | locked | 06-scoring.md (walls and lava never pay) |
| look_reference | Wavy yellow-orange glowing lava strips along the edges | — | — | guess | Director |

## Rules
1. **Part of a wave.** Lava is placed in a wave like any other hazard. A wave without lava has plain solid walls the whole time.
2. **Available from Level 4.** A wave played below Level 4 never turns on lava ([../08-difficulty.md](../08-difficulty.md)).
3. **Random timing.** In a wave that has lava, these are random each time the wave plays: when lava turns on, how long it stays on, and whether it comes back. It may also stay on until the wave ends. Ranges: OBJ-11.
4. **Warn first.** Every switch to lava shows a warning first, at least `telegraph_min` ticks at Level 8 ([../07-objects.md](../07-objects.md)).
5. **While on:** touching the lava is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)). Invulnerability protects as usual.
6. **While off:** the walls are plain solid walls ([../03-world-and-camera.md](../03-world-and-camera.md)).
7. **wave_check** must pass for every outcome the random ranges allow, including lava on for the whole wave.
8. Never pays graze.

## Edge cases
- The ship is touching a wall when lava turns on. The warning gave it time to leave, so it's a hit.
- Lava turns off while the ship is invulnerable and inside it: nothing happens.
- Still open: see OBJ-11.

## Open
- OBJ-11.

## How to extend
Fill every TBD through OBJ-11 in [../90-open-questions.md](../90-open-questions.md), using the rule list in [_template.md](_template.md).
