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
| 12 | 2026-10-09 | fall_cap is 5.5 px/tick (guess). | Under the 5.77 bound with headroom: a top-line fall takes about 57 ticks. Answers SH-01. | — |
| 13 | 2026-10-09 | The ship's top edge is the point the top line stops. The ship has fallen once it is fully below the floor. | Answers WC-02 and WC-03. | — |
| 14 | 2026-10-09 | A run starts with the ship at (320, 240), at rest, the same point as the fall respawn. | One spawn point to learn. Answers WC-06. | — |
| 15 | 2026-10-09 | Debug overlay: ship x, y, vx, vy and lines at the top line and floor. Debug mode only, shown from the first frame, F3 toggles. Default font 16 px, green (0, 255, 0). | Tuning the drift needs the numbers on screen. Answers UI-05. | — |
| 16 | 2026-10-09 | Two run modes, normal by default and debug. Debug is chosen at launch by URL parameter `debug=1`, environment variable `DRIFTWARD_DEBUG=1`, or the launch script's debug option. Game rules are the same in both. | Debug help without changing what players get. | — |
| 17 | 2026-10-09 | Logging: INFO in normal mode, DEBUG in debug mode, format `HH:MM:SS LEVEL logger: message`, log by event, never by tick. | Python in WebAssembly is slow; a line per tick floods the console. | — |
| 18 | 2026-10-09 | An unexpected error is logged with its trace and shows "Something broke. Reload the page." in white. Debug mode adds the error type and message. | The page must never freeze silently. | — |
| 19 | 2026-10-09 | Error screen: main line in the default font at 24 px, centered. Debug line in the default font at 16 px, centered one line-height below, shown as `<ErrorType>: <message>` and cut to the screen width. A debug switch with any value other than `1` means normal mode plus one WARNING. | Readable at a glance. The full detail always stays in the log. | — |
| 20 | 2026-10-09 | Debug overlay layout: four text lines (x, y, vx, vy, two decimals) at the top-left, 4 px in. 1 px full-width lines on row 168 and row 479. | The floor at y 480 is one row past the screen, so its line sits on the last visible row. | — |
| 21 | 2026-10-09 | At most 5 ticks run per frame. Owed time beyond that is dropped. | After a hidden tab or a stall, the game carries on instead of jumping the ship ahead, and a slow frame can't snowball. | — |
| 22 | 2026-10-12 | Locked decision 2 changed. The screen is fixed and never follows the ship. The world scrolls down past it at `scroll_base` × the level's scroll speed. The top line is a ceiling: the ship's top edge is clamped there and `vy` becomes 0. Hazards and coins move down with the scroll, plus any movement of their own. | The moving world gives the feeling of flying forward. The ship's position never changes the scroll. WC-05 no longer applies. | Locked decision 2 (camera follows the ship, floor rises) |
| 23 | 2026-10-12 | Distance counts how far the world has scrolled, so a ship that just survives earns meters. Coins and grazes must pay more than surviving. | Director: going for the risks earns more points than just surviving. Pillar 3 still holds. | Meters from the highest point reached |
| 24 | 2026-10-12 | The scroll starts 30 ticks (0.5 s) after play starts and never stops until game over, including after a fall. | Answers WC-04. | — |
| 25 | 2026-10-12 | Distance starts at 0 m when play starts. Meters are whole meters, rounded down. | Answers WC-01 and SC-01. | — |
| 26 | 2026-10-12 | Levels no longer start every 400 m. Each level is designed one by one and sets its own start distance (DF-05). | Director: levels are designed explicitly. | Level table "Starts at" row (every 400 m) |
