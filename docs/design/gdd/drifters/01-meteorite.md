# Meteorite
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (top sideways speed)

## Summary
A rock that falls straight down from the top. It has no logic: it just falls. It's the first hazard every player meets, and Wave 0 uses only meteorites.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Falling blocker | — | — | locked | Director |
| enters_from | Top | — | — | locked | Director |
| kind | moving drifter ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 1 | — | — | guess | 07-drifters.md |
| variants | small 20, medium 28, big 40 | px wide | — | guess | Director |
| default_variant | medium | — | — | guess | Director |
| hitbox | one circle as wide as the rock: radius 10, 14, 20 | px | — | guess | Director |
| speed_ratio | 0.375 × the ship's top sideways speed ([../04-ship.md](../04-ship.md), derived values) | — | — | guess | Director |
| speed | ≈ 2.5 at Level 1, from `speed_ratio` and the current ship guesses | px/tick | — | guess | derived |
| entry_warning_ticks | 60 (1.0 s) | ticks | — | guess | Director |
| telegraph | none. It never strikes; it only falls | — | — | locked | Director |
| specialty | none | — | — | locked | Director |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | A rock like a shooting star, with a small glowing tail. May be animated | — | — | guess | Director |
| placeholder_look | a filled circle as wide as the variant, grey (140, 140, 140) | RGB | — | guess | Director |
| start_y | just above the top edge: its bottom edge on the top edge, so center y = −width ÷ 2. A placement may set another y | px | — | guess | Director |

## Rules
1. **Appears:** at its placed x and `start_y`, then falls into view. Its entry warning shows first, at its x against the top edge ([../07-drifters.md](../07-drifters.md) rule 9).
2. **Telegraph:** none. The entry warning is its only warning.
3. **Moves:** straight down at `speed` on screen, every tick. No sideways drift, no spin, no targeting. The scroll doesn't add to it ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
4. **Hits:** touching it is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)).
5. **Leaves:** once fully below the floor ([../07-drifters.md](../07-drifters.md) rule 12).
6. **Scales:** `speed` × the level's hazard speed, set when it appears ([../08-difficulty.md](../08-difficulty.md)).
7. **Looks and sounds:** placeholder grey circle until the look is drawn. Sound: none yet.
8. **wave_check notes:** none beyond the shared rules.

## Edge cases
- The ship is invulnerable when it touches the rock: no hit, the rock keeps falling.
- The ship is still inside the rock that hit it when invulnerability ends: LD-06.
- Two meteorites overlap: OB-04.

## Open
- OB-04, LD-06.

## How to extend
A new size or speed is a new variant in Values. Sideways drift or spin would be a specialty, added later with the Director's approval.
