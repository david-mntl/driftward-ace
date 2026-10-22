# Lives and damage
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [04-ship.md](04-ship.md), [07-drifters.md](07-drifters.md), [10-ui.md](10-ui.md)

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
| rehit_cooldown | 180 (3 s): how long the hazard that took a life can't hurt the ship again. Never scales with level | ticks | — | guess | Director |
| rehit_dim | 0.75: during its cooldown the hazard is drawn at this share of its normal brightness, a little darker. It returns to full brightness the tick the cooldown ends | × brightness | — | guess | Director (darker); 0.75 is a starting pick |

## Rules
1. **Hit.** The ship touches a hazard's hitbox while not invulnerable.
   1. Lose 1 life.
   2. Play the **life-lost feedback** (rule 3).
   3. Become invulnerable for `invuln_ticks`, blinking.
   4. Nothing else changes. Position, velocity and control stay as they were. No stun, no freeze.
   5. **Re-hit cooldown.** The hazard that hit keeps going as normal: it doesn't vanish or change. That one hazard can't hit the ship again for `rehit_cooldown` ticks. Every other hazard can hit as soon as invulnerability ends. During the cooldown it is drawn a little darker (`rehit_dim`), so the player sees it is harmless for now and when it turns dangerous again. After the cooldown, if the ship still touches it, it hits again. A drifter made of parts (chain lightning's arcs) counts as one hazard, and all its parts dim together.
2. **Fall.** The ship drops fully below the floor ([03-world-and-camera.md](03-world-and-camera.md) rule 5).
   1. Lose 1 life.
   2. Play the **life-lost feedback** (rule 3).
   3. Respawn at `fall_respawn`: x 320, y 240, `vx = vy = 0`. If a floating island would overlap the ship at that point, the ship respawns at the nearest clear spot straight above or below it. If the spot above would put the ship's top edge past the top line, it goes below ([drifters/05-floating-islands.md](drifters/05-floating-islands.md)).
   4. Become invulnerable for `invuln_ticks`, blinking.
   5. The ship stands at `fall_respawn`, at rest, until the first arrow key press. Invulnerability counts down during this wait. An arrow held through the fall does not count; the player releases it and presses again. The respawn completes at that press. That press also thrusts the ship on the same tick. Gravity and drag apply from then on. The world keeps scrolling during the wait. The wait has no time limit.
   6. **Fall while invulnerable.** The fall costs no life. The ship respawns at `fall_respawn`, at rest, and does not wait for a key. The invulnerability timer keeps running. No life-lost feedback plays.
   7. **Respawn on a hazard.** The fall respawn point is never moved for a hazard. If the ship respawns on one, invulnerability protects it. The player has `invuln_ticks` to fly clear, or the hazard moves away. If the ship still touches a hazard when invulnerability ends, it's a hit. Floating islands are ground, not a hazard; they move the respawn point instead (rule 2.3).
3. **Life-lost feedback.** On every lost life, all three play at once. They are looks only: none of them changes physics, control or the camera.
   1. **Screen flash.** A brief full-screen flash.
   2. **HUD life breaks.** The lost life in the top-right visibly breaks.
   3. **Ship burst and rebuild.** The ship bursts into particles, which then pull back together into the ship while it blinks. The rebuild ends by the time invulnerability ends.

   Look, colors and timings: [10-ui.md](10-ui.md), LD-08.
4. **Invulnerable** means hazards pass through the ship with no hit. Lava walls count as hazards. A fall while invulnerable follows rule 2.6.
5. **Game over** happens the tick lives reach 0. See [02-game-flow.md](02-game-flow.md). Whether the last life plays the feedback before the game-over screen is LD-09.
6. The GDD has no way to gain a life. Adding one is a new feature and needs the Director's approval.

## Edge cases
- Two hazards touch the ship in the same tick: one hit, one life lost. Both start their `rehit_cooldown`.
- The ship still overlaps the hazard that hit it when invulnerability ends: no hit until `rehit_cooldown` ends (rule 1.5).
- The ship is hit by one hazard, then touches another after invulnerability ends: the second one hits. Its own cooldown starts then.
- The fall respawn point at screen center is inside a floating island: rule 2.3.
- The fall respawn point at screen center has a hazard on it: rule 2.7.
- The ship's hitbox while it is drawn as particles: unchanged. The burst is a look, not a state.

## Open
- LD-04, LD-08, LD-09.

## How to extend
A new way to lose a life must say where the ship ends up, whether invulnerability blocks it, and that it plays the life-lost feedback. Add it as a numbered rule here and link it from the drifter's spec.
