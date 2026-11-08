# World and camera
Status: draft
Depends on: [04-ship.md](04-ship.md), [05-lives-and-damage.md](05-lives-and-damage.md), [08-difficulty.md](08-difficulty.md)

## Summary
The play area is a fixed 640×480 view, the glass of a cockpit window. It never follows the ship. The world scrolls down past it at a steady speed set by the level, so the ship feels like it flies forward. Distance counts that scroll, wherever the ship is on screen. The top line is a ceiling, the bottom edge is the floor, and the side walls are solid. The window is larger: a frame runs round the play area and a side panel sits to its right. Neither covers a pixel of it.

```
 window 856 × 518
 +------------------------------------------------------+ y=0
 | frame                                    |pillar|     |
 |  +-----------------------------+         |      |     |
 |  | play area 640 × 480         |         | side panel |
 |  |        hazards v            |         | 184 wide   |
 |  |- - - - - TOP LINE - - - - - |         |            |
 |  |             A  ship         |         |            |
 |  |#############################|         |            |
 |  +-----------------------------+         |            |
 | frame                                    |            |
 +------------------------------------------------------+ y=518
   x=16 to 656 inside the window; y=10 to 490
```
Walls, top line, floor and every wave coordinate count from the play area's own top-left, as before.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| screen_w | 640. The play area's width | px | — | guess | Director |
| screen_h | 480. The play area's height | px | — | guess | Director |
| top_line_ratio | 0.175 | of screen_h, from top | — | locked | Director |
| px_per_meter | 10 | px/m | — | locked | Director |
| scroll_base | 1.1 | px/tick | TBD (SH-02) | guess | Director tuning guess |
| scroll_start_delay | 30 | ticks (0.5 s) after play starts | — | guess | Director |
| distance_start | 0 | m, when play starts | — | locked | Director |
| ship_start | (320, 240), at rest: the same point as `fall_respawn` ([05-lives-and-damage.md](05-lives-and-damage.md#values)) | screen x, y | — | guess | Director |
| window_w | 856 | px | — | guess | Director |
| window_h | 518 | px | — | guess | Director |
| play_area_x | 16. Distance from the window's left edge to the play area | px | — | guess | Director |
| play_area_y | 10. Distance from the window's top edge to the play area | px | — | guess | Director |
| play_area | exactly `screen_w` × `screen_h`, at (`play_area_x`, `play_area_y`) in the window. The rest of the window is the frame (16 px left and right, 10 px above, 28 px below) and the side panel ([10-ui.md](10-ui.md)) | — | — | locked | Director |

## Rules
1. **Coordinates.** World: x to the right, y **up**. Screen: pygame, y **down**. Wave placements count from the wave's start ([09-waves.md](09-waves.md) rule 2). Source: Director. The exact conversion is a technical detail, not a design rule.
2. **Top line.** Screen y = `screen_h × top_line_ratio` = 84. It is a ceiling. The ship's top edge is the point that counts. When the ship pushes past it, the top edge is clamped to the line and `vy` becomes 0, the same way the side walls stop `vx`.
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

10. **Window and play area.** The window is `window_w` × `window_h`. The play area sits inside it at (`play_area_x`, `play_area_y`). The frame, the pillar and the panel are drawn outside the play area and never over it, so the player sees every hazard right up to the wall and floor. Where the frame's corners are cut or rounded, the cut is outside the play area. Source: Director.
11. **Screens that fill the window.** The menu, the instructions page, the leaderboard page and the credits page use the whole window. Their background fills it too. The pause box and the game-over screen are centered on the whole window ([10-ui.md](10-ui.md)).

## Edge cases
- Walls, floor, top line and fall distance move with the play area, not with the window. A frame or panel change never moves them.
- The ship hovers in one spot: distance still grows. Points beyond surviving come from coins and grazes, which sit near danger ([01-vision.md](01-vision.md), Pillar 3).

## Open
- SH-02.

## How to extend
A new screen-space rule (a new line, zone or edge) goes here, with its value in Values and its ratio of `screen_w` or `screen_h`, never a bare pixel number, so it survives a screen size change.
