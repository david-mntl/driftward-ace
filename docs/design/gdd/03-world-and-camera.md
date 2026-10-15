# World and camera
Status: draft
Depends on: [04-ship.md](04-ship.md), [05-lives-and-damage.md](05-lives-and-damage.md), [08-difficulty.md](08-difficulty.md)

## Summary
The screen is a fixed 640×480 view. It never follows the ship. The world scrolls down past it at a steady speed set by the level, so the ship feels like it flies forward. Distance counts that scroll, wherever the ship is on screen. The top line is a ceiling, the bottom edge is the floor, and the side walls are solid.

```
 x=0                              x=640
  +--------------------------------+  y=0
  |            hazards v           |
  |                                |  warning space
  |- - - - - - TOP LINE - - - - - -|  y=168 (35% down), ceiling
  |                                |
  |               A  ship          |  312 px top line to floor
  |                                |  world scrolls down v
  |################################|  y=480 floor
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
| scroll_start_delay | 30 | ticks (0.5 s) after play starts | — | guess | Director |
| distance_start | 0 | m, when play starts | — | locked | Director |
| ship_start | (320, 240), at rest: the same point as `fall_respawn` ([05-lives-and-damage.md](05-lives-and-damage.md#values)) | screen x, y | — | guess | Director |
| play_area | TBD | px | — | TBD | WC-07 |

## Rules
1. **Coordinates.** World: x to the right, y **up**. Screen: pygame, y **down**. Wave files use world coordinates. Source: Director. The exact conversion is a technical detail, not a design rule.
2. **Top line.** Screen y = `screen_h × top_line_ratio` = 168. It is a ceiling. The ship's top edge is the point that counts. When the ship pushes past it, the top edge is clamped to the line and `vy` becomes 0, the same way the side walls stop `vx`.
3. **The screen never moves.** It doesn't follow the ship, up or down. Source: [01-vision.md](01-vision.md), Locked decisions.
4. **Scroll.** Every tick, the world scrolls down by `scroll_base × scroll multiplier` for the current level ([08-difficulty.md](08-difficulty.md)). The ship never changes the scroll. It starts `scroll_start_delay` ticks after play starts and never stops until game over, including right after a fall.
5. **Floor.** The floor is the bottom edge of the screen. Falling off it costs a life ([05-lives-and-damage.md](05-lives-and-damage.md)). The ship counts as off once it is fully below the floor: its top edge is past the bottom of the screen.
6. **Side walls.** At x = 0 and x = `screen_w`. Solid: the ship's edge is clamped to the wall and `vx` becomes 0. No bounce. Source: [01-vision.md](01-vision.md), Locked decisions.
7. **Lava walls.** In some waves from Level 4 on, the walls turn to lava for a while, and touching them is a hit. When lava is off, rule 6 applies. See [drifters/11-lava-walls.md](drifters/11-lava-walls.md).
8. **Distance** is how far the world has scrolled in this run, in meters. It starts at `distance_start` when play starts and grows only through the scroll. Where the ship is on screen doesn't change it. Scoring is in [06-scoring.md](06-scoring.md).
9. **Drifters and the scroll.** Two kinds:
   - **Parked drifters** sit still in the world (coins, floating islands). They move down the screen with the scroll.
   - **Moving drifters** move on their own (meteorite, fireball, satellite). Their speed is their speed on screen, scaled by the level's hazard speed ([08-difficulty.md](08-difficulty.md)). The scroll doesn't add to it.
   Each drifter's spec says which kind it is.

## Edge cases
- Until WC-07 is answered, every rule here assumes the play area is the whole window. If a HUD strip or side margins are added, walls, floor, top line and fall distance move with the play area.
- The ship hovers in one spot: distance still grows. Points beyond surviving come from coins and grazes, which sit near danger ([01-vision.md](01-vision.md), Pillar 3).

## Open
- WC-07, SH-02.

## How to extend
A new screen-space rule (a new line, zone or edge) goes here, with its value in Values and its ratio of `screen_w` or `screen_h`, never a bare pixel number, so it survives a screen size change.
