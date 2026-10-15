# Waves
Status: draft
Depends on: [07-drifters.md](07-drifters.md), [08-difficulty.md](08-difficulty.md), [04-ship.md](04-ship.md)

## Summary
Waves are hand-authored JSON files that place hazards and coins. Every run opens with the same meteorites-only Wave 0. A wave must pass `wave_check` before it counts as done. `wave_check` runs the real physics headless at Level 8 and proves the wave is hard but fair.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| check_level | 8 | level | — | locked | Director |
| telegraph_min | see [07-drifters.md](07-drifters.md#values) | — | — | locked | — |
| gap_min | 2.5 | × ship_w | — | locked | Director |
| seam_clear | 120 | px | — | locked | Director |
| coin_near_max | 3 | × ship_w, gap from the coin's hitbox to the nearest hazard hitbox | — | guess | Director (picked by guardian on request) |
| wave_count_mvp | TBD | waves | — | TBD | WV-03 |

## Rules
1. **Format.** JSON. Each drifter entry has world coordinates (x, y up), an entry side and a trigger distance ([03-world-and-camera.md](03-world-and-camera.md) rule 8). Source: Director. The exact field names and types are the wave schema's job, not the GDD's. Never add, rename or drop a field without a schema change.
2. Coordinates are relative to the wave's start or absolute: WV-04.
3. **Wave 0** holds meteorites only, is the same every run, and always comes first. Source: [01-vision.md](01-vision.md), Locked decisions. Its content is WV-05.
4. **Order after Wave 0:** WV-01. **After the last wave:** WV-02. Procedural levels are out of scope ([01-vision.md](01-vision.md)).
5. Only drifters whose tier is unlocked at the current level may appear ([08-difficulty.md](08-difficulty.md)).
6. **Coins** go near hazards, never in safe spots. Source: [01-vision.md](01-vision.md), Pillar 3. Each wave sets how many coins it has; 0 is allowed. Each placement sets how near: anywhere from right beside a hazard (hard) out to `coin_near_max` × `ship_w` (easy), which is 96 px at the guessed ship width.
7. **wave_check** runs at `check_level` and fails the wave unless all of these hold:
   1. Every telegraph lasts ≥ `telegraph_min` ticks.
   2. Every gap the ship must pass is ≥ `gap_min` × `ship_w` ([04-ship.md](04-ship.md)), which is 80 px at the guessed ship width.
   3. A bot using arrow-key thrust and the real physics finds a path with zero hits.
   4. There is `seam_clear` px of clear space at each seam between waves. Meaning confirmed in WV-06.
   5. A hazard with random timing (lava walls) passes for every outcome its random range allows.
   6. Every coin comes within `coin_near_max` × `ship_w` of a hazard's hitbox, at some tick while both are on screen.
   7. No coin sits inside a floating island. Gaps between islands, and between an island and a wall, count for check 2. The bot's physics includes islands blocking ([drifters/05-floating-islands.md](drifters/05-floating-islands.md) rule 4).
   8. Every drifter's own wave_check notes in its spec hold.
8. `wave_check` reruns on any wave change or tuning change. Source: Director.

## Edge cases
- A tuning change (for example lower `thrust_up`) makes an old wave fail: the wave must be fixed before it ships again.

## Open
- WV-01, WV-02, WV-03, WV-04, WV-05, WV-06, DF-02.

## How to extend
A new wave: write the JSON to the wave schema, run `wave_check`, and have it reviewed for pacing. If the schema can't express what you need, that's a schema change, not a wave change.
