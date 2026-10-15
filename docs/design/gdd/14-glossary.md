# Glossary
Status: draft
Depends on: —

## Summary
One line per term. Where a term has a value, the link points to the value's home.

## Values
None. Terms only.

## Rules
| Term | Meaning |
|---|---|
| Archetype | A hazard's behavior class (falling blocker, patrol mover...). It defines the object, not its looks. See [07-objects.md](07-objects.md). |
| Camera | The fixed 640×480 view. It never moves; the world scrolls down past it. See [03-world-and-camera.md](03-world-and-camera.md). |
| Distance | How far the world has scrolled in this run, in px or m. Hovering still adds to it. See [03-world-and-camera.md](03-world-and-camera.md). |
| Drift | The ship keeps moving after a key is released, because only drag and gravity change its speed. |
| Entry warning | The marker that shows where a hazard will enter, before it does. See [07-objects.md](07-objects.md). |
| Fall | Dropping off the floor. Costs a life; the ship respawns at the screen center. See [05-lives-and-damage.md](05-lives-and-damage.md). |
| Floor | The bottom edge of the screen. |
| Graze | Leaving a hazard's graze zone without touching it. Pays points. See [06-scoring.md](06-scoring.md). |
| Graze zone | Each shape of a hazard's hitbox, grown by the graze margin. See [06-scoring.md](06-scoring.md). |
| Hit | Touching a hazard while not invulnerable. Costs a life. The ship keeps moving. |
| Invulnerable | A period after a hit or fall when hazards can't hurt the ship. The ship blinks. |
| Life-lost feedback | The flash, HUD life break and ship burst-and-rebuild that play when a life is lost. |
| Level | Difficulty step set by meters flown. See [08-difficulty.md](08-difficulty.md). |
| Meter (m) | 10 px of distance. |
| Moving object | An object that moves on its own. Its speed is its on-screen speed; the scroll doesn't add to it. See [03-world-and-camera.md](03-world-and-camera.md). |
| Parked object | An object that sits still in the world and slides down with the scroll. |
| Rest gap | The pause between two waves. Shrinks with level. |
| Scroll | The world sliding down past the fixed screen. See [03-world-and-camera.md](03-world-and-camera.md). |
| Seam | Where one wave ends and the next starts. Must be clear (wave_check). |
| Specialty | An optional extra behavior an object has on top of its movement (a pull, a lunge, a pulse). Can be on or off. See [07-objects.md](07-objects.md). |
| Telegraph | A hazard's warning before it strikes (a charge line, a glow). |
| Tick | One fixed game step, 1/60 s. |
| Tier | A group of objects unlocked at a level. See [08-difficulty.md](08-difficulty.md). |
| Timer × | The level's multiplier on hazard timers. See [08-difficulty.md](08-difficulty.md). |
| Top line | Screen line 35% down. A ceiling: the ship can't go above it. |
| Variant | A named version of an object (small, medium, big) that changes its values, never its behavior. See [07-objects.md](07-objects.md). |
| Wave | A hand-authored JSON group of hazards and coins. See [09-waves.md](09-waves.md). |
| Wave 0 | The fixed, meteorites-only wave that opens every run. |
| wave_check | The headless tool that tests a wave for fairness at Level 8. |

## Edge cases
None.

## Open
None.

## How to extend
Add one row, in alphabetical order. Define the term in one plain sentence and link to the file that owns its value.
