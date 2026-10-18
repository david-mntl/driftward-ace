# Fireball
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (top sideways speed)

## Summary
A comet that dives across the screen on a straight, steep diagonal. By default it enters at a top corner and flies inward. It never targets the ship. It falls about as fast as a meteorite but also slides sideways, so the safe spot keeps moving. Its entry warning shows where it appears and which way it will fly.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Fast linear hazard | — | — | locked | Director |
| enters_from | Top corners (default), anywhere along the top, or the sides | — | — | locked | Director |
| kind | moving drifter ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-drifters.md |
| variants | small 21, big 32 (head width) | px | — | guess | Director |
| default_variant | small | — | — | guess | Director |
| size | the ball (the head): 21 small, 32 big. It sets when the fireball counts as off screen. The tail doesn't count | px | — | guess | Director |
| hitbox | two circles: the head, radius = head width ÷ 2 (10.5, 16); the tail, half the head's radius (5.25, 8), touching the head from behind, along its path | px | — | guess | Director |
| speed_ratio | 0.47 × the ship's top sideways speed ([../04-ship.md](../04-ship.md), derived values), measured along its path | — | — | guess | Director |
| speed | ≈ 3.1 at Level 1, along its path, from `speed_ratio` and the current ship guesses. Both variants share it | px/tick | — | guess | derived |
| angle | 35° from straight down. Fixed for every fireball; changed only by tuning | degrees | — | guess | Director |
| direction | left to right, unless the placement sets `invert`, which mirrors it: right to left | — | — | guess | Director |
| entry_warning_ticks | the shared value ([../07-drifters.md](../07-drifters.md)) | ticks | — | — | 07-drifters.md |
| telegraph | none. It never strikes; it only flies | — | — | locked | Director |
| specialty | none | — | — | locked | Director |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | Orange-yellow comet with a fading trail | — | — | guess | Director |
| placeholder_look | two filled circles the size of its hitbox: head orange (255, 140, 0), tail dark yellow (200, 160, 0) | RGB | — | guess | Director |
| start | just outside the screen ([../07-drifters.md](../07-drifters.md) rule 14). Default: at the top-left corner, head's center on the left wall, head's bottom edge on the top edge. With `invert`: the same at the right wall. A placement may set another x along the top, or a side entry at a set y | px | — | guess | Director |

At Level 1 the 35° path splits into about 2.5 px/tick down and 1.8 px/tick sideways. From the top-left corner it crosses the floor near x 336, about 3.2 s later. Derived from the guesses above; not tuning keys.

## Rules
1. **Appears:** at its start spot, then flies into view. Its entry warning shows first, where it will appear: at its x against the top edge for a top entry, at its y against the side edge for a side entry ([../07-drifters.md](../07-drifters.md) rule 9). The warning copy is tilted along its path, with the tail pointing back, so it also shows which way it will fly.
2. **Telegraph:** none. The entry warning is its only warning.
3. **Moves:** in a straight line at `speed` along its path, at `angle` from straight down, every tick. Down and to the right; down and to the left with `invert`. A side entry from the left wall flies right; with `invert` it enters from the right wall and flies left. No targeting, no turning. The scroll doesn't add to it ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
4. **Hits:** touching the head or the tail is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)).
5. **Leaves:** once fully off screen at a side or the bottom ([../07-drifters.md](../07-drifters.md) rule 12). It flies through the walls ([../07-drifters.md](../07-drifters.md) rule 15).
6. **Scales:** `speed` × the level's hazard speed, set when it appears ([../08-difficulty.md](../08-difficulty.md)). The angle never scales.
7. **Looks and sounds:** placeholder circles until the look is drawn. Sound: none yet.
8. **wave_check notes:** none beyond the shared rules.

## Edge cases
- The ship is invulnerable when it touches the fireball: no hit, the fireball keeps flying.
- The ship is still inside the fireball that hit it when invulnerability ends: no hit until its re-hit cooldown ends ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 1.5).
- A fireball meets a wall or another drifter: it flies through ([../07-drifters.md](../07-drifters.md) rule 15).

## Open
- None.

## How to extend
A new size is a new variant in Values. A curved path or a homing turn is a new behavior, so a new drifter, never a variant.
