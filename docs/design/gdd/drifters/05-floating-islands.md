# Floating islands
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared drifter rules), [../04-ship.md](../04-ship.md) (tick order), [../05-lives-and-damage.md](../05-lives-and-damage.md) (respawn)

## Summary
Big chunks of floating ground that drift down with the world. They don't hurt. They block, like the side walls do. The ship can stand on one, slide along its slopes, or get held under one and carried toward the floor. A wave lays islands out so only certain paths stay open. The player has to pick a path early and fly it.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Forced-path blocker | — | — | locked | Director |
| enters_from | Top: it scrolls in from just above the top edge ([../07-drifters.md](../07-drifters.md) rule 14) | — | — | locked | Director |
| kind | blocker ([../07-drifters.md](../07-drifters.md)): touching it neither hurts nor pays | — | — | locked | Director |
| scroll_kind | parked drifter: it doesn't move on its own, only with the scroll ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-drifters.md |
| variants | see the shape table below | — | — | guess | Director (standard size); other sizes confirmed when each is built |
| default_variant | rectangle | — | — | guess | Director |
| hitbox | the shape itself, exactly as drawn. The L and the T are two boxes each. The triangle uses a polygon ([../07-drifters.md](../07-drifters.md) rule 8) | px | — | guess | Director |
| entry_warning | none. It can't hurt, and it is visible for about 2.5 s before it reaches the ship's zone | — | — | locked | Director |
| telegraph | none. It never strikes | — | — | locked | Director |
| specialty | none | — | — | locked | Director |
| graze | no. It blocks like a wall, and walls never pay ([../06-scoring.md](../06-scoring.md) rule 5) | — | — | locked | Director |
| look_reference | Green floating ground with a darker edge | — | — | guess | Director |
| placeholder_look | the filled shape in green (70, 160, 80), with a 2 px edge in darker green (35, 90, 45) drawn inside the shape | RGB | — | guess | Director |

**Shapes.** Every size is the box around the shape, centered on the island's position. The arms of the L and the T are `arm` thick. `invert` flips the shape upside down.

| Variant | Size (w × h) | Shape | With `invert` |
|---|---|---|---|
| rectangle | 320 × 120 (half the screen width, a quarter of its height) | a filled rectangle | the same |
| box | 120 × 120 | a filled square | the same |
| l_shape | 320 × 120 | a bar along the bottom, full width; an upright at the left end, full height | upside down: the bar along the top, the upright still at the left end hanging down |
| t_shape | 320 × 120 | a bar along the top, full width; a stem centered under it, down to the bottom | upside down: the bar along the bottom, the stem standing up from its middle |
| triangle | 320 × 120 | a right triangle: flat base along the bottom, straight side up the left edge, slope from the top-left corner down to the bottom-right corner | upside down: flat top, straight side down the left edge, slope from the bottom-left corner up to the top-right corner |

| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| arm | 40 (a third of the shape's height) | px | — | guess | Director (shapes); thickness picked by main session |

## Rules
1. **Appears:** at its placed x and y, or just above the top edge by default, then scrolls into view. No entry warning.
2. **Telegraph:** none.
3. **Moves:** never on its own. It moves down with the scroll, like the world under it. Hazard speed and Timer × don't touch it.
4. **Blocks:** the ship can't enter an island. Every tick, right after the side walls ([../04-ship.md](../04-ship.md) rule 2, step 6):
   1. If the ship overlaps an island, it is moved out the shortest way, just to the surface.
   2. The part of its speed going into the surface, measured against the island's own movement, becomes 0. The part along the surface stays, so the ship slides along a slope. No bounce.
   3. **On top:** the ship can stand on an island and rides down with it. It lifts off when it thrusts up.
   4. **Underneath:** the island's underside holds the ship down and carries it at the island's own speed, never faster. There is no shove. The ship can always slide out sideways.
5. **Hits:** never. Touching an island costs no life and pays nothing. A ship carried off the floor has fallen like any other fall ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 2).
6. **Invulnerable ship:** islands still block. They are ground, not a hazard.
7. **Leaves:** once fully below the floor ([../07-drifters.md](../07-drifters.md) rule 12).
8. **Scales:** nothing. A faster scroll only brings it sooner.
9. **Placing:** the island's center x and y, its variant, and `invert` (L, T and triangle only).
10. **Looks and sounds:** placeholder until the look is drawn. The final art must fill the shape exactly, so the ship stops where the ground is drawn. Sound: none yet.
11. **wave_check notes:** every gap the ship must pass, island to island or island to wall, is at least `gap_min` ([../09-waves.md](../09-waves.md)). No coin sits inside an island. The bot's physics includes rule 4.

## Edge cases
- The ship stands in the respawn wait under an island: the island carries it down like any ship. A player who never presses can be carried off the floor; that is a normal fall.
- The fall respawn point is inside an island: the ship respawns at the nearest clear spot ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 2.3).
- The ship is held under an island and reaches the floor: it is carried off and falls.
- A hazard or a coin overlaps an island: nothing happens. Drifters pass through each other ([../07-drifters.md](../07-drifters.md) rule 15).
- An island touches a side wall: allowed. It's a path the ship can't use.

## Open
- None.

## How to extend
A new shape or size is a new variant in the shape table. An island that moves on its own, breaks or hurts is a new behavior, so a new drifter.
