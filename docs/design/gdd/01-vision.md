# Vision
Status: draft
Depends on: —

## Summary
You can't shoot. You can only fly better. Driftward Ace is an endless arcade dodger for the desktop browser. Gravity drags the ship down every tick, the arrow keys fight back with thrust, and the ship keeps drifting after you let go. The floor chases you from below while hazards come from the top, the sides and mid-screen. There's no safe lane and no weapon. React fast or fall.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| genre | Endless arcade dodger, no weapons | — | — | locked | Director |
| players | Single-player | — | — | locked | Director |
| platform | Desktop web browser, no install | — | — | locked | Director |
| lose_condition | All lives lost | — | — | locked | Director |
| win_condition | Beat your best score | — | — | locked | Director. Needs saves, see FL-03 |

## Pillars
Every decision gets checked against these three. A design that breaks one is wrong, however good it feels.

1. **Master the drift.** Momentum control and fast reflexes are the core skills.
   Rules out: weapons, instant stop, set-speed control.
2. **See it before it hits you.** Every hazard warns before it strikes, even side entries. Deaths must feel fair.
   Rules out: instant hits, spawns on top of the ship.
3. **Risk brings reward.** The best points sit next to danger.
   Rules out: free safe pickups, score for hiding.

## Locked decisions
Do not reopen. Changing one needs the Director's explicit go-ahead and a row in [91-decision-log.md](91-decision-log.md). Details live in the linked file.

1. Controls are arrow keys only. [02-game-flow.md](02-game-flow.md)
2. The camera follows the ship up and never down. It also rises on its own, so the floor keeps rising. Falling off the floor costs a life. [03-world-and-camera.md](03-world-and-camera.md)
3. Side walls are solid. They stop the ship with no bounce. [03-world-and-camera.md](03-world-and-camera.md)
4. Every game rule runs on a fixed 60 Hz tick. Gravity is always on. Horizontal velocity has drag. Fall speed is capped. [04-ship.md](04-ship.md)
5. The ship has 3 lives. A hit or a fall costs one, then brief invulnerability. No stun: losing a life never freezes the ship or takes control away. [05-lives-and-damage.md](05-lives-and-damage.md)
6. Hazards are defined by behavior archetype, not by visual skin. [07-objects.md](07-objects.md)
7. Waves are hand-authored JSON. Every run opens with the same fixed, meteorites-only Wave 0. [09-waves.md](09-waves.md)
8. A control card shows after click-to-start. [02-game-flow.md](02-game-flow.md)
9. If saves ship, they go to browser localStorage: nickname, score and level reached. Nothing else. [11-save-data.md](11-save-data.md)

## Out of scope
Combat, online leaderboard, mobile or touch controls, multiplayer, procedural levels, wave editor.

## Rules
1. The fun is surviving longer and beating your last score.
2. The game is hard on purpose. Every death must teach the player something, so every death must be readable: the player can say what hit them and why.
3. Feel words, for art, sound and tuning: drag, fight back, drift, chase, fall. The ship should feel heavy but controllable, never floaty and never stiff.

## Edge cases
- A run with no BEST to beat (saves are a stretch goal): see FL-03.

## Open
- FL-03: what "win" shows while saves are deferred.

## How to extend
A new pillar, locked decision or out-of-scope item goes here, only with the Director's go-ahead, with a row in [91-decision-log.md](91-decision-log.md). Put its details in the file it links to, not here.
