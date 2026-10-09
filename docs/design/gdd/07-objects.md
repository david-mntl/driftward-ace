# Objects
Status: draft
Depends on: [05-lives-and-damage.md](05-lives-and-damage.md), [06-scoring.md](06-scoring.md), [08-difficulty.md](08-difficulty.md)

## Summary
The MVP has 11 objects: 9 hazards, 1 pickup (coin) and 1 boundary hazard (lava walls). Each one is defined by its **archetype**, meaning how it behaves, not how it looks. Source: [01-vision.md](01-vision.md), Locked decisions. This file routes to each spec and holds the rules every hazard shares.

## Routing table
Priority 1 is built first. Priorities are a starting proposal, so the Director adjusts them in the objects round.

| # | Object | Archetype | Enters from | Priority | Spec | Spec status |
|---|---|---|---|---|---|---|
| 1 | Meteorite | Falling blocker | Top | 1 | [objects/01-meteorite.md](objects/01-meteorite.md) | draft |
| 2 | Satellite | Patrol mover | Sides | 2 | [objects/02-satellite.md](objects/02-satellite.md) | draft |
| 3 | Chain lightning | Telegraphed link | Mid-screen | 2 | [objects/03-chain-lightning.md](objects/03-chain-lightning.md) | draft |
| 4 | Coin | Pickup | Inside waves | 2 | [objects/04-coin.md](objects/04-coin.md) | draft |
| 5 | Floating islands | Forced-path blocker | Top | 2 | [objects/05-floating-islands.md](objects/05-floating-islands.md) | draft |
| 6 | Fireball | Fast linear hazard | Corners, sides | 2 | [objects/06-fireball.md](objects/06-fireball.md) | draft |
| 7 | UFO | Wildcard mover | Sides | 3 | [objects/07-ufo.md](objects/07-ufo.md) | draft |
| 8 | Planet | Blocker + gravity well | Top | 3 | [objects/08-planet.md](objects/08-planet.md) | draft |
| 9 | Carnivore plant | Static + lunge attack | Sides | 4 | [objects/09-carnivore-plant.md](objects/09-carnivore-plant.md) | draft |
| 10 | Electric ball | Slow patrol + pulse | Mid-screen | 4 | [objects/10-electric-ball.md](objects/10-electric-ball.md) | draft |
| 11 | Lava walls | Boundary hazard | Sides (in waves, Level 4+) | 3 | [objects/11-lava-walls.md](objects/11-lava-walls.md) | draft |

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| telegraph_min | 45 | ticks, at Level 8 | — | locked | Director |
| entry_warning | TBD | look and ticks | — | TBD | OB-01 |

## Rules shared by every hazard
1. **Warn first.** Every hazard shows a warning before it can hit, including side and corner entries. Source: [01-vision.md](01-vision.md), Pillar 2.
2. **Telegraphs** last at least `telegraph_min` ticks even at Level 8 speeds. wave_check enforces it ([09-waves.md](09-waves.md)).
3. **No spawn on the ship.** No hazard may appear overlapping the ship. Source: [01-vision.md](01-vision.md), Pillar 2.
4. **Touch = hit**, unless the spec says otherwise. What a hit does is in [05-lives-and-damage.md](05-lives-and-damage.md).
5. **Graze** applies to every hazard except walls and lava ([06-scoring.md](06-scoring.md)).
6. **Speed** is multiplied by the level's hazard speed ([08-difficulty.md](08-difficulty.md)). Whether timers scale too is OB-02.
7. A wave never gains objects as the level rises. Source: Director.

## Edge cases
- When a hazard leaves the screen or falls below the floor: OB-03.
- Hazards touching each other or the walls: OB-04.

## Open
- OB-01, OB-02, OB-03, OB-04.

## How to extend
1. Get the Director's approval for the new object first.
2. Copy [objects/_template.md](objects/_template.md) to `objects/NN-name.md`, using the next number.
3. Fill every field. Unknowns are TBD with an ID in [90-open-questions.md](90-open-questions.md).
4. Add a row to the routing table above.
5. If it is a new archetype, say why no existing archetype fits.
