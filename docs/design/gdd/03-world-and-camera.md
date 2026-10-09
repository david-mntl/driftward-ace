# World and camera
Status: draft
Depends on: [04-ship.md](04-ship.md), [05-lives-and-damage.md](05-lives-and-damage.md), [08-difficulty.md](08-difficulty.md)

## Summary
The screen is a 640×480 window into a tall world. The camera only goes up. It follows the ship when the ship climbs past the top line, and it also rises on its own, so the floor (the bottom edge of the screen) keeps chasing the ship. The side walls are solid.

```
 x=0                              x=640
  +--------------------------------+  y=0
  |            hazards v           |
  |                                |  warning space
  |- - - - - - TOP LINE - - - - - -|  y=168 (35% down)
  |                                |
  |               A  ship          |  312 px top line to floor
  |                                |
  |################################|  y=480 rising floor
  +--------------------------------+
  wall                          wall
```

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| screen_w | 640 | px | — | guess | Director |
| screen_h | 480 | px | — | guess | Director |
| top_line_ratio | 0.35 | of screen_h, from top | — | locked | Director |
| px_per_meter | 10 | px/m | — | locked | Director |
| scroll_base | 1.1 | px/tick | TBD (SH-02) | guess | Director tuning guess |
| altitude_zero | TBD | world y | — | TBD | WC-01 |
| ship_start | TBD | screen x, y | — | TBD | WC-06 |
| play_area | TBD | px | — | TBD | WC-07 |

## Rules
1. **Coordinates.** World: x to the right, y **up**. Screen: pygame, y **down**. Wave files use world coordinates. Source: Director. The exact conversion is a technical detail, not a design rule.
2. **Top line.** Screen y = `screen_h × top_line_ratio` = 168. The ship can't go above it. When the ship pushes past it, the camera moves up instead, by the same amount. See WC-02 for which ship point counts.
3. **Camera never goes down.** Source: [01-vision.md](01-vision.md), Locked decisions.
4. **Auto-rise.** Every tick, the camera rises by `scroll_base × scroll multiplier` for the current level ([08-difficulty.md](08-difficulty.md)). How auto-rise combines with following the ship in the same tick is WC-05. When auto-rise starts and whether it pauses is WC-04.
5. **Floor.** The floor is the bottom edge of the screen. Falling off it costs a life ([05-lives-and-damage.md](05-lives-and-damage.md)). See WC-03 for when the ship counts as off.
6. **Side walls.** At x = 0 and x = `screen_w`. Solid: the ship's edge is clamped to the wall and `vx` becomes 0. No bounce. Source: [01-vision.md](01-vision.md), Locked decisions.
7. **Lava walls.** In some waves from Level 4 on, the walls turn to lava for a while, and touching them is a hit. When lava is off, rule 6 applies. See [objects/11-lava-walls.md](objects/11-lava-walls.md).
8. **Distance** is the highest altitude the ship has reached, in meters. Hovering doesn't add to it. Scoring is in [06-scoring.md](06-scoring.md).

## Edge cases
- Until WC-07 is answered, every rule here assumes the play area is the whole window. If a HUD strip or side margins are added, walls, floor, top line and fall distance move with the play area.
- The ship rides the top line while the camera auto-rises faster than the ship climbs: the ship slides down the screen toward the floor. This is intended. The floor is meant to chase.

## Open
- WC-01, WC-02, WC-03, WC-04, WC-05, WC-06, WC-07, SH-02.

## How to extend
A new screen-space rule (a new line, zone or edge) goes here, with its value in Values and its ratio of `screen_w` or `screen_h`, never a bare pixel number, so it survives a screen size change.
