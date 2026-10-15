# Electric ball
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (top sideways speed), [../06-scoring.md](../06-scoring.md) (graze), [03-chain-lightning.md](03-chain-lightning.md) (same cycle)

## Summary
A single glowing ball falls from the top. It charges, and a faint ring shows how far its strike will reach. Then it fires a full circle of lightning around itself, stops, and charges again until it leaves. The ball itself is harmless; only the circle hurts. It works like a chain lightning with one node.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Pulse node | — | — | locked | Director |
| enters_from | Top, at the x the placement sets | — | — | locked | Director |
| kind | moving drifter ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 4 | — | — | guess | 07-drifters.md |
| variants | one: standard | — | — | guess | Director |
| default_variant | standard | — | — | guess | Director |
| ball_size | 16, a circle | px | — | guess | Director |
| pulse_radius | 64, from the ball's center (128 px across, the chain lightning's node spacing) | px | — | guess | Director |
| hitbox | while firing only: one circle, radius `pulse_radius`. The ball has none | px | — | guess | Director |
| speed_ratio | 0.375 × the ship's top sideways speed ([../04-ship.md](../04-ship.md), derived values), straight down. Its own number; it only starts equal to the chain lightning's | — | — | guess | Director |
| speed | ≈ 2.5 at Level 1, from `speed_ratio` and the current ship guesses | px/tick | — | guess | derived |
| charge_ticks | 120 (2 s) | ticks | — | guess | Director (same as chain lightning) |
| fire_ticks | 120 (2 s). Timer × never shortens it | ticks | — | guess | Director (same as chain lightning) |
| cycle | charge, fire, charge, fire… until it leaves. No pause besides the charge | — | — | locked | Director |
| entry_warning_ticks | the shared value ([../07-drifters.md](../07-drifters.md)) | ticks | — | — | 07-drifters.md |
| telegraph | the charge: blue rays grow around the ball, more and faster as the charge fills, and a faint outline of the pulse circle brightens with them. It shows when and exactly where the strike lands | — | — | locked | Director |
| specialty | none | — | — | locked | Director |
| graze | yes, only while it fires, and once per electric ball | — | — | locked | Director |
| look_reference | Purple spiky glowing orb | — | — | guess | Director |
| placeholder_look | ball: filled purple circle (170, 80, 255), 16 px. Charge: short 1 px rays (200, 150, 255) around the ball, more as the charge fills, and a 1 px outline of the pulse circle in the same color, brighter as it fills. Fire: the pulse circle filled translucent (200, 160, 255) with a 2 px bright rim (240, 220, 255) | RGB | — | guess | Director |

## Rules
1. **Appears:** at its placed x, just above the top edge ([../07-drifters.md](../07-drifters.md) rule 14), then falls into view. Its entry warning shows first, at its x against the top edge.
2. **Telegraph:** the charge starts the moment it appears and lasts `charge_ticks`.
3. **Moves:** straight down at `speed` on screen, every tick. No targeting. The scroll doesn't add to it ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
4. **Fires:** after the charge, the pulse circle fires for `fire_ticks`, then the next charge starts. It fires only while the ball is on screen (any part visible).
5. **Hits:** touching the firing circle is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)). The ball and the charge outline never hit.
6. **Leaves:** once the ball is fully below the floor ([../07-drifters.md](../07-drifters.md) rule 12).
7. **Scales:** `speed` × the level's hazard speed; `charge_ticks` × the level's Timer ×, never below `telegraph_min` ([../08-difficulty.md](../08-difficulty.md)). `fire_ticks` and `pulse_radius` never scale.
8. **Placing:** its x. `invert` has no effect.
9. **Looks and sounds:** placeholder until the look is drawn. The firing look stays inside the pulse circle, so the hitbox is never bigger than what the player sees. Sound: none yet.
10. **wave_check notes:** the charge at Level 8 (120 × 0.70 = 84 ticks) must stay ≥ `telegraph_min`. The circle counts as a hazard for the bot's path only while firing.

## Edge cases
- The ship touches the firing circle while invulnerable: no hit, the circle keeps firing.
- The ship is still inside the circle that hit it when invulnerability ends: no hit until its re-hit cooldown ends ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 1.5).
- The ship sits on the ball while it charges: no hit. When the fire starts, the ship is inside the circle and is hit.
- The ball leaves the screen while firing: the circle stops at once.
- The circle passes over a coin, an island or another drifter: nothing happens ([../07-drifters.md](../07-drifters.md) rule 15).

## Open
- None.

## How to extend
A new pulse size or timing is a new variant in Values. A ball that drifts sideways, follows the ship or chains to other balls is a new behavior, so a new drifter.
