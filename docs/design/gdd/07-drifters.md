# Drifters
Status: draft
Depends on: [05-lives-and-damage.md](05-lives-and-damage.md), [06-scoring.md](06-scoring.md), [08-difficulty.md](08-difficulty.md)

## Summary
A **drifter** is anything that appears in the ship's path during a run, good or bad. The name comes from the game's title: drifters are what comes at the ship as it drifts forward. It names a role, not a movement; some drifters never move. Every hazard warns first. Every drifter appears, behaves by its archetype, has a hitbox and leaves. They come in three kinds, set by what touching them does:
- **Hazard:** touching it is a hit and costs a life. Grazing it pays.
- **Pickup:** touching it pays. A pickup always sits near a hazard (Pillar 3).
- **Blocker:** touching it neither hurts nor pays. It blocks the ship like ground (floating islands).

The MVP has 11 drifters: 8 hazards, 1 blocker (floating islands), 1 pickup (coin) and 1 boundary hazard (lava walls). Each one is defined by its **archetype**, meaning how it behaves, not how it looks. Source: [01-vision.md](01-vision.md), Locked decisions. This file routes to each spec and holds the rules every hazard shares.

## Routing table
Priority 1 is built first. Priorities are a starting proposal, so the Director adjusts them in the drifters round.

| # | Drifter | Archetype | Enters from | Priority | Spec | Spec status |
|---|---|---|---|---|---|---|
| 1 | Meteorite | Falling blocker | Top | 1 | [drifters/01-meteorite.md](drifters/01-meteorite.md) | draft |
| 2 | Satellite | Side crosser | Sides | 2 | [drifters/02-satellite.md](drifters/02-satellite.md) | draft |
| 3 | Chain lightning | Telegraphed link | Top | 2 | [drifters/03-chain-lightning.md](drifters/03-chain-lightning.md) | draft |
| 4 | Coin | Pickup | Top (scrolls in) | 2 | [drifters/04-coin.md](drifters/04-coin.md) | draft |
| 5 | Floating islands | Forced-path blocker | Top | 2 | [drifters/05-floating-islands.md](drifters/05-floating-islands.md) | draft |
| 6 | Fireball | Fast linear hazard | Top corners, top, sides | 2 | [drifters/06-fireball.md](drifters/06-fireball.md) | draft |
| 7 | UFO | Wildcard mover | Sides | 3 | [drifters/07-ufo.md](drifters/07-ufo.md) | draft |
| 8 | Planet | Gravity well | Top | 3 | [drifters/08-planet.md](drifters/08-planet.md) | draft |
| 9 | Carnivore plant | Static + lunge attack | Sides | 4 | [drifters/09-carnivore-plant.md](drifters/09-carnivore-plant.md) | draft |
| 10 | Electric ball | Pulse node | Top | 4 | [drifters/10-electric-ball.md](drifters/10-electric-ball.md) | draft |
| 11 | Lava walls | Boundary hazard | Sides (in waves, Level 4+) | 3 | [drifters/11-lava-walls.md](drifters/11-lava-walls.md) | draft |

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| telegraph_min | 45 | ticks, at Level 8 | — | locked | Director |
| entry_warning_look | a copy of the drifter at half its size, inside a shooting-star glow with random spikes | — | — | guess | Director (placeholder look) |
| entry_warning_glow | (255, 220, 120), warm yellow-white | RGB | — | guess | Director |
| entry_warning_spikes | 6 to 9 thin spikes (1 px) out of the glow, random per drifter and steady while it shows | count, px | — | guess | Director |
| entry_warning_size | the whole warning (copy, glow and spikes) fits inside the drifter's own width; the copy is half that size | px | — | guess | Director |
| entry_warning_ticks | 60 (1.0 s), shared by every hazard. A spec may set another length only with the Director's approval. Pickups have none | ticks | — | guess | Director |

## Rules shared by every hazard
1. **Warn first.** Every hazard shows a warning before it can hit, including side and corner entries. Source: [01-vision.md](01-vision.md), Pillar 2.
2. **Telegraphs** last at least `telegraph_min` ticks even at Level 8 speeds. wave_check enforces it ([09-waves.md](09-waves.md)).
3. **No spawn on the ship.** No hazard may appear overlapping the ship. Source: [01-vision.md](01-vision.md), Pillar 2.
4. **Touch = hit**, unless the spec says otherwise. What a hit does is in [05-lives-and-damage.md](05-lives-and-damage.md).
5. **Graze** applies to every hazard except walls and lava ([06-scoring.md](06-scoring.md)).
6. **Level scaling.** A drifter's speed is multiplied by the level's hazard speed, and its timers by the level's timer factor ([08-difficulty.md](08-difficulty.md)). Both are set once, when the drifter appears, and kept for its whole life.
7. A wave never gains drifters as the level rises. Source: Director.
8. **Hitbox.** One or more circles, boxes, lines and polygons, set per drifter (and per variant). A line runs straight from point A to point B with a set thickness, at any angle. A polygon is a filled shape with straight edges, such as a diamond or a triangle. Never bigger than what the player sees. Source: [01-vision.md](01-vision.md), Pillar 2.
9. **Entry warning.** Before a hazard appears, its entry warning shows for `entry_warning_ticks`, at the spot where it will appear. If that spot is off screen, the warning shows just inside the nearest screen edge, in line with it (for a top entry: at the drifter's x, against the top edge). When the warning ends, the hazard appears and can hit. Entry warnings never shorten with level. An entry warning is not a telegraph: a telegraph warns before a strike ([14-glossary.md](14-glossary.md)).
10. **Variants.** A drifter may have named variants, such as small, medium and big. A variant changes values only (size, hitbox, speed), never behavior. Each drifter names a default variant. A new behavior is a new drifter.
11. **Specialty.** A drifter may have one extra behavior on top of its movement, such as a pull, a lunge or a pulse. A specialty can be switched on or off. Its default is in the drifter's spec; a placement may switch it. A drifter without one just moves.
12. **Leaving.** A drifter that has appeared is removed once it is fully off screen at a side or the bottom. Never at the top, where drifters enter.
13. **Placing a drifter** names the drifter, its position and, if wanted, a variant, a level to use instead of the current one (rule 6, [08-difficulty.md](08-difficulty.md) rule 3) and a specialty switch. A spec may add its own placement fields, such as the fireball's `invert`.
14. **Start.** A drifter that enters from an edge starts just outside it: fully off screen, touching that edge. A placement may set another spot.
15. **Fly freely.** Drifters pass through the walls and through each other. Only the ship collides. Source: Director, for now.

## Edge cases
- Two drifters overlap, or a drifter reaches a wall: both keep going (rule 15).

## Open
- None.

## How to extend
1. Get the Director's approval for the new drifter first.
2. Copy [drifters/_template.md](drifters/_template.md) to `drifters/NN-name.md`, using the next number.
3. Fill every field. Unknowns are TBD with an ID in [90-open-questions.md](90-open-questions.md).
4. Add a row to the routing table above.
5. If it is a new archetype, say why no existing archetype fits.
