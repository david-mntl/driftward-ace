# Lives and damage
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [04-ship.md](04-ship.md), [07-objects.md](07-objects.md), [10-ui.md](10-ui.md)

## Summary
The ship has 3 lives. Touching a hazard is a **hit**. Dropping below the floor is a **fall**. Both cost a life. There is no stun: the ship keeps its momentum and the player keeps control, because Pillar 1 rules out an instant stop. Instead the game makes the loss impossible to miss (flash, breaking life icon, ship bursting and rebuilding) and gives half a second of invulnerability to recover. No lives left means game over.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| lives_start | 3 | lives | — | locked | [01-vision.md](01-vision.md), Locked decisions |
| invuln_ticks | 30 | ticks (0.5 s) | — | locked | Director |
| invuln_blink | yes | — | — | locked | Director |
| blink_period | TBD | ticks | — | TBD | LD-04 |
| fall_respawn | screen center (320, 240), at rest | screen px | — | locked | Director |

## Rules
1. **Hit.** The ship touches a hazard's hitbox while not invulnerable.
   1. Lose 1 life.
   2. Play the **life-lost feedback** (rule 3).
   3. Become invulnerable for `invuln_ticks`, blinking.
   4. Nothing else changes. Position, velocity and control stay as they were. No stun, no freeze.
2. **Fall.** The ship drops off the floor ([03-world-and-camera.md](03-world-and-camera.md), WC-03).
   1. Lose 1 life.
   2. Play the **life-lost feedback** (rule 3).
   3. Respawn at `fall_respawn`: x 320, y 240, `vx = vy = 0`.
   4. Become invulnerable for `invuln_ticks`, blinking.
3. **Life-lost feedback.** On every lost life, all three play at once. They are looks only: none of them changes physics, control or the camera.
   1. **Screen flash.** A brief full-screen flash.
   2. **HUD life breaks.** The lost life in the top-right visibly breaks.
   3. **Ship burst and rebuild.** The ship bursts into particles, which then pull back together into the ship while it blinks. The rebuild ends by the time invulnerability ends.

   Look, colors and timings: [10-ui.md](10-ui.md), LD-08.
4. **Invulnerable** means hazards pass through the ship with no hit. Lava walls count as hazards. Whether falls still count is LD-05.
5. **Game over** happens the tick lives reach 0. See [02-game-flow.md](02-game-flow.md). Whether the last life plays the feedback before the game-over screen is LD-09.
6. The GDD has no way to gain a life. Adding one is a new feature and needs the Director's approval.

## Edge cases
- Two hazards touch the ship in the same tick: one hit, one life lost.
- The hazard that hit the ship, and the ship still overlapping it when invulnerability ends: LD-06.
- The fall respawn point at screen center has a hazard on it. Pillar 2 rules out spawns on top of the ship. See LD-07.
- The ship's hitbox while it is drawn as particles: unchanged. The burst is a look, not a state.

## Open
- LD-04, LD-05, LD-06, LD-07, LD-08, LD-09.

## How to extend
A new way to lose a life must say where the ship ends up, whether invulnerability blocks it, and that it plays the life-lost feedback. Add it as a numbered rule here and link it from the object's spec.
