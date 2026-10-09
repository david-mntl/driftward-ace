# Decision log
Why the GDD says what it says. Newest at the bottom. When a decision changes an earlier one, the **Replaces** column names that row, so the newest row always wins.

| # | Date | Decision | Why | Replaces |
|---|---|---|---|---|
| 1 | 2026-10-09 | The GDD is a folder of atomic files with a routing index. Objects get one spec each, routed from `07-objects.md`. This folder is the only design source. | Readers open only what they need. Every gap is visible. | — |
| 2 | 2026-10-09 | Screen is 640×480, landscape. | Director's starting size. | — |
| 3 | 2026-10-09 | Thrust is three tuning keys, `thrust_side`, `thrust_up` and `thrust_down`, all starting at 0.42. | Splitting one key later is a schema change. Three keys from the start cost nothing. | — |
| 4 | 2026-10-09 | Physics values live as default + slider range + status in the GDD. The live value lives in the tuning file. The Director copies tuned values back. | Feel needs playtesting, not guessing. | — |
| 5 | 2026-10-09 | Starting guesses: gravity 0.16, drag_x 0.94, scroll_base 1.1 px/tick at Level 1. | Director's tuning guesses. | — |
| 6 | 2026-10-09 | No stun. A hit or fall gives 30 ticks (0.5 s) of invulnerability, with the ship blinking, and plays the life-lost feedback: screen flash, HUD life breaks, ship bursts into particles and rebuilds. | A stun that freezes the ship is an instant stop, which Pillar 1 rules out. The feedback makes a lost life unmistakable without taking control away. | — |
| 7 | 2026-10-09 | After a hit the ship stays where it was, with its velocity. After a fall it respawns at the screen center, at rest. | Director's call. | — |
| 8 | 2026-10-09 | Saves, nickname and local top 10 are a stretch goal. Until then the HUD has no BEST. | Focus the MVP. | — |
| 9 | 2026-10-09 | Objects have a build priority (1 first), not a build week. Starting proposal: P1 meteorite; P2 coin, satellite, fireball, floating islands, chain lightning; P3 UFO, planet, lava walls; P4 carnivore plant, electric ball. | Order matters more than dates. | — |
| 10 | 2026-10-09 | Team, process and budget are not in the GDD. | The GDD describes the game only, so any team can build from it. | — |
| 11 | 2026-10-09 | The GDD owns the pillars, locked decisions, out of scope ([01-vision.md](01-vision.md)) and tech constraints ([15-tech-constraints.md](15-tech-constraints.md)). Project setup files point here. | The GDD must stand alone. | — |
