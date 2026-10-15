# Difficulty
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [07-drifters.md](07-drifters.md), [09-waves.md](09-waves.md)

## Summary
Difficulty is one function of level. Level rises with distance flown. Each level sets where it starts (DF-05). Each level makes the world scroll faster, hazards move faster, their timers shorter and the rest between waves shorter, and some levels unlock new hazard tiers. Nothing else scales, and authored waves never gain drifters.

## Values
Level table. Source: Director. Status: locked, except the Timer × row: guess (1 ÷ hazard speed), Director.

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Starts at (m) | 0 | TBD (DF-05) | TBD (DF-05) | TBD (DF-05) | TBD (DF-05) | TBD (DF-05) | TBD (DF-05) | TBD (DF-05) |
| Scroll speed × | 1.0 | 1.1 | 1.2 | 1.3 | 1.4 | 1.5 | 1.6 | 1.7 |
| Hazard speed × | 1.00 | 1.06 | 1.12 | 1.18 | 1.24 | 1.30 | 1.36 | 1.42 |
| Timer × | 1.00 | 0.94 | 0.89 | 0.85 | 0.81 | 0.77 | 0.74 | 0.70 |
| Rest gap × | 1.00 | 0.90 | 0.81 | 0.73 | 0.66 | 0.59 | 0.53 | 0.48 |
| Adds | Tier 1 | — | Tier 2 | Lava (in waves) | Tier 3 | — | — | Cap |

| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| rest_gap_base | TBD | ticks | — | TBD | DF-02 |
| tier_1_drifters | TBD | — | — | TBD | DF-01 |
| tier_2_drifters | TBD | — | — | TBD | DF-01 |
| tier_3_drifters | TBD | — | — | TBD | DF-01 |

## Rules
1. **Level** = the highest level whose "starts at" is ≤ the run's meters ([06-scoring.md](06-scoring.md)). Meters never go down, so level never goes down.
2. **Scroll speed** multiplies `scroll_base` ([03-world-and-camera.md](03-world-and-camera.md)).
3. **Hazard speed** multiplies every hazard's movement speed ([07-drifters.md](07-drifters.md)). It is applied once, when the drifter appears, and the drifter keeps that speed for its whole life. A placement may name another level for that drifter; then that level's values are used instead.
4. **Timer ×** multiplies a drifter's timers the same way: spawn times inside a wave, charge times, pulse and patrol periods, lava on and off times. It never shortens an entry warning, and never pushes a telegraph below `telegraph_min` ([07-drifters.md](07-drifters.md)). A spec may exempt one of its timers (chain lightning's fire time).
5. **Switches for playtesting.** Hazard speed and Timer × can each be switched off. Off means Level 1 values at every level.
6. **Rest gap** multiplies `rest_gap_base`, the pause between waves.
7. **Tier unlocks.** From its level on, a tier's drifters may appear in waves.
8. **Lava** becomes available from Level 4. It is a wave hazard with random timing, not an always-on state ([drifters/11-lava-walls.md](drifters/11-lava-walls.md)).
9. **Nothing else scales.** No extra drifters, no bigger hitboxes, no shorter warnings beyond what hazard speed and Timer × imply. Source: Director.

## Edge cases
- What "Cap" means at Level 8: DF-03.
- The level changes in the middle of a wave: drifters already on screen keep their speed and timers (rule 3). For drifters that appear later in the wave: DF-04.
- Each level is designed one by one and sets its own start distance: DF-05.

## Open
- DF-01, DF-02, DF-03, DF-04, DF-05.

## How to extend
A new level is a new column. A new scaling row must say what it multiplies and why it doesn't break "nothing else scales". Both are design changes for the Director, logged in [91-decision-log.md](91-decision-log.md).
