# Waves
Status: draft
Depends on: [07-objects.md](07-objects.md), [08-difficulty.md](08-difficulty.md), [04-ship.md](04-ship.md)

## Summary
Waves are hand-authored JSON files that place hazards and coins. Every run opens with the same meteorites-only Wave 0. A wave must pass `wave_check` before it counts as done. `wave_check` runs the real physics headless at Level 8 and proves the wave is hard but fair.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| check_level | 8 | level | — | locked | Director |
| telegraph_min | see [07-objects.md](07-objects.md#values) | — | — | locked | — |
| gap_min | 2.5 | × ship_w | — | locked | Director |
| seam_clear | 120 | px | — | locked | Director |
| wave_count_mvp | TBD | waves | — | TBD | WV-03 |

## Rules
1. **Format.** JSON. Each object entry has world coordinates (x, y up), an entry side and a trigger altitude. Source: Director. The exact field names and types are the wave schema's job, not the GDD's. Never add, rename or drop a field without a schema change.
2. Coordinates are relative to the wave's start or absolute: WV-04.
3. **Wave 0** holds meteorites only, is the same every run, and always comes first. Source: [01-vision.md](01-vision.md), Locked decisions. Its content is WV-05.
4. **Order after Wave 0:** WV-01. **After the last wave:** WV-02. Procedural levels are out of scope ([01-vision.md](01-vision.md)).
5. Only objects whose tier is unlocked at the current level may appear ([08-difficulty.md](08-difficulty.md)).
6. **Coins** go near hazards, never in safe spots. Source: [01-vision.md](01-vision.md), Pillar 3. How many and how near: WV-07.
7. **wave_check** runs at `check_level` and fails the wave unless all of these hold:
   1. Every telegraph lasts ≥ `telegraph_min` ticks.
   2. Every gap the ship must pass is ≥ `gap_min` × `ship_w` ([04-ship.md](04-ship.md)), which is 80 px at the guessed ship width.
   3. A bot using arrow-key thrust and the real physics finds a path with zero hits.
   4. There is `seam_clear` px of clear space at each seam between waves. Meaning confirmed in WV-06.
   5. A hazard with random timing (lava walls) passes for every outcome its random range allows.
8. `wave_check` reruns on any wave change or tuning change. Source: Director.

## Edge cases
- A tuning change (for example lower `thrust_up`) makes an old wave fail: the wave must be fixed before it ships again.

## Open
- WV-01, WV-02, WV-03, WV-04, WV-05, WV-06, WV-07, DF-02.

## How to extend
A new wave: write the JSON to the wave schema, run `wave_check`, and have it reviewed for pacing. If the schema can't express what you need, that's a schema change, not a wave change.
