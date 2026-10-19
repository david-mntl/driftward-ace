# Difficulty
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [07-drifters.md](07-drifters.md), [09-waves.md](09-waves.md)

## Summary
Difficulty is one function of level. Level rises when the level's playlist of waves ends ([09-waves.md](09-waves.md)). Each level makes the world scroll faster, hazards move faster, their timers shorter and the rest between waves shorter, and some levels unlock new hazard tiers. Nothing else scales, and authored waves never gain drifters.

## Values
Level table. Source: Director. Status: locked, except the Timer × row: guess (1 ÷ hazard speed), Director; and the Playlist row: TBD (DF-06).

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Playlist (fixed waves, then `random_count`) | TBD (DF-06) | TBD (DF-06) | TBD (DF-06) | TBD (DF-06) | TBD (DF-06) | TBD (DF-06) | TBD (DF-06) | TBD (DF-06) |
| Scroll speed × | 1.0 | 1.1 | 1.2 | 1.3 | 1.4 | 1.5 | 1.6 | 1.7 |
| Hazard speed × | 1.00 | 1.06 | 1.12 | 1.18 | 1.24 | 1.30 | 1.36 | 1.42 |
| Timer × | 1.00 | 0.94 | 0.89 | 0.85 | 0.81 | 0.77 | 0.74 | 0.70 |
| Rest gap × | 1.00 | 0.90 | 0.81 | 0.73 | 0.66 | 0.59 | 0.53 | 0.48 |
| Adds | Tier 1 | — | Tier 2 | Lava (in waves) | Tier 3 | — | — | Cap |

| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| rest_gap_base | 0 | ticks | — | guess | Director. The real value is DF-02 |
| tier_1_drifters | TBD | — | — | TBD | DF-01 |
| tier_2_drifters | TBD | — | — | TBD | DF-01 |
| tier_3_drifters | TBD | — | — | TBD | DF-01 |

## Rules
1. **Level.** A run starts at Level 1. Wave 0 plays at Level 1, before the Level 1 playlist. Each level ends on the tick the last wave of its playlist ends, and the next level starts on that tick. After Level 8's playlist the level stays 8 and random waves play forever ([09-waves.md](09-waves.md) rule 4). Level never goes down.
2. **Scroll speed** multiplies `scroll_base` ([03-world-and-camera.md](03-world-and-camera.md)).
3. **Hazard speed** multiplies every hazard's movement speed ([07-drifters.md](07-drifters.md)). It is applied once, when the drifter appears, and the drifter keeps that speed for its whole life. A placement may name another level for that drifter; then that level's values are used instead.
4. **Timer ×** multiplies a drifter's own timers the same way: charge times, pulse and patrol periods, lava on and off times. It doesn't touch the spacing of spawns inside a wave: triggers are scroll distances, so that spacing follows the scroll speed ([09-waves.md](09-waves.md) rule 9). It never shortens an entry warning, and never pushes a telegraph below `telegraph_min` ([07-drifters.md](07-drifters.md)). A spec may exempt one of its timers (chain lightning's fire time). A scaled timer rounds up to a whole tick.
5. **Switches for playtesting.** Hazard speed and Timer × can each be switched off. Off means Level 1 values at every level.
6. **Rest gap** multiplies `rest_gap_base`, the pause between waves. It uses the level current when the gap starts. A wave's extra rest is added after that and never scales ([09-waves.md](09-waves.md) rule 11).
7. **Tier unlocks.** From its level on, a tier's drifters may appear in waves.
8. **Lava** becomes available from Level 4. It is a wave hazard with random timing, not an always-on state ([drifters/11-lava-walls.md](drifters/11-lava-walls.md)).
9. **Nothing else scales.** No extra drifters, no bigger hitboxes, no shorter warnings beyond what hazard speed and Timer × imply. Source: Director.

## Edge cases
- **Cap at Level 8:** there is no Level 9. After Level 8's playlist, Level 8 values hold forever (rule 1).
- The level never changes inside a wave. It rises only when a wave ends (rule 1). Drifters still on screen keep their speed and timers (rule 3). The scroll speed changes on the tick the level rises.
- Each level's playlist is designed one by one: DF-06.

## Open
- DF-01, DF-02, DF-06.

## How to extend
A new level is a new column. A new scaling row must say what it multiplies and why it doesn't break "nothing else scales". Both are design changes for the Director, logged in [91-decision-log.md](91-decision-log.md).
