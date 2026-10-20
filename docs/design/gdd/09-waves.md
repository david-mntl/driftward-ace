# Waves
Status: draft
Depends on: [07-drifters.md](07-drifters.md), [08-difficulty.md](08-difficulty.md), [04-ship.md](04-ship.md)

## Summary
Waves are hand-authored JSON files that place hazards and coins. Every run opens with the same Wave 0, then plays each level's playlist of fixed and random waves. A wave must pass `wave_check` before it counts as done. `wave_check` runs the real physics headless at Level 8 and proves the wave is hard but fair.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| check_level | 8 | level | — | locked | Director |
| telegraph_min | see [07-drifters.md](07-drifters.md#values) | — | — | locked | — |
| gap_min | 2.5 | × ship_w | — | locked | Director |
| seam_clear | 120 | px of scroll, at the start of every wave | — | locked | Director |
| coin_near_max | 3 | × ship_w, gap from the coin's hitbox to the nearest hazard hitbox | — | guess | Director (picked by guardian on request) |
| wave_count_mvp | TBD | waves | — | TBD | WV-03 |

## Rules
1. **Format.** JSON. Each drifter entry has a trigger distance and a spawn spot, with the placement fields of [07-drifters.md](07-drifters.md) rule 13. Source: Director. The exact field names and types are the wave schema's job, not the GDD's. Never add, rename or drop a field without a schema change.
2. **Relative.** Trigger distances count in px of scroll from the wave's start, so a wave plays the same wherever it falls in a run. Source: Director.
3. **Wave 0.** Its only hazard is the meteorite; it may hold coins. It is the same every run, plays at Level 1 and always comes first. Source: [01-vision.md](01-vision.md), Locked decisions. Its content is WV-05.
4. **Order.** After Wave 0, each level plays its playlist ([08-difficulty.md](08-difficulty.md), Playlist row): its fixed waves in order, then `random_count` random waves (0 allowed). A random wave is picked from the pool waves whose `min_level` ≤ the current level, never the wave that just played. If only one pool wave is allowed, it plays again. Picks are new every run. A fixed wave may sit in more than one playlist. After Level 8's playlist, random waves play forever at Level 8. Source: Director. Procedural levels are out of scope ([01-vision.md](01-vision.md)): only hand-authored waves are picked.
5. Only drifters whose tier is unlocked at the current level may appear ([08-difficulty.md](08-difficulty.md)).
6. **Coins** go near hazards, never in safe spots. Source: [01-vision.md](01-vision.md), Pillar 3. Each wave sets how many coins it has; 0 is allowed. Each placement sets how near: anywhere from right beside a hazard (hard) out to `coin_near_max` × `ship_w` (easy), which is 96 px at the guessed ship width.
7. **wave_check** runs at `check_level` and fails the wave unless all of these hold:
   1. Every telegraph lasts ≥ `telegraph_min` ticks.
   2. Every gap the ship must pass is ≥ `gap_min` × `ship_w` ([04-ship.md](04-ship.md)), which is 80 px at the guessed ship width.
   3. A bot using arrow-key thrust and the real physics finds a path with zero hits.
   4. In the wave's first `seam_clear` px of scroll, none of its hazards is on screen. An entry warning counts as on screen. The end of a wave has no such rule: a wave that needs a clear stretch before the next one sets an extra rest (rule 11). Source: Director.
   5. A hazard with random timing (lava walls) passes for every outcome its random range allows.
   6. Every coin comes within `coin_near_max` × `ship_w` of a hazard's hitbox, at some tick while both are on screen.
   7. No coin sits inside a floating island. Gaps between islands, and between an island and a wall, count for check 2. The bot's physics includes islands blocking ([drifters/05-floating-islands.md](drifters/05-floating-islands.md) rule 4).
   8. Every drifter's own wave_check notes in its spec hold.
8. `wave_check` reruns on any wave change or tuning change. Source: Director.
9. **Length.** Each wave sets its length in px of scroll. The wave ends when the world has scrolled that far since its start. Triggers are distances, so a wave keeps its layout at every level and just arrives faster. Example: 30 s at Level 1 is 1980 px. Source: Director.
10. **Fixed or pool.** Each wave is `fixed` (played where a playlist names it) or `pool` (picked for random slots). A pool wave sets `min_level`, the lowest level it may play at. Source: Director.
11. **Extra rest.** A wave may set an extra rest in ticks, 0 when left out. It is added to the rest gap after that wave and never scales with level ([08-difficulty.md](08-difficulty.md) rule 6). A hard wave can use it to give the player time to recover. Source: Director.
12. **Drifter values** are shared per drifter type. A wave never sets them; a placement uses only the placement fields of [07-drifters.md](07-drifters.md) rule 13. Source: Director.

## Edge cases
- A tuning change (for example lower `thrust_up`) makes an old wave fail: the wave must be fixed before it ships again.
- **Provisional waves.** Until `wave_check` exists, a wave checked by hand against rule 7 and playtested by the Director counts as provisional. Every provisional wave must pass `wave_check` before the MVP ships.
- Seam pacing: `seam_clear` is about 1.8 s of clear scroll at Level 1 and 1 s at Level 8. A wave's end has no clear stretch of its own; the rest gap and the extra rest give it.

## Open
- WV-03, WV-05, DF-01, DF-02, DF-06.

## How to extend
A new wave: write the JSON to the wave schema, run `wave_check`, and have it reviewed for pacing. If the schema can't express what you need, that's a schema change, not a wave change.
