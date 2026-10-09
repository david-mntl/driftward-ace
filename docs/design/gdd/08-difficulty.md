# Difficulty
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [07-objects.md](07-objects.md), [09-waves.md](09-waves.md)

## Summary
Difficulty is one function of level. Level rises with altitude, every 400 m. Each level makes the floor rise faster, hazards move faster and the rest between waves shorter, and some levels unlock new hazard tiers. Nothing else scales, and authored waves never gain objects.

## Values
Level table. Source: Director. Status: locked.

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Starts at (m) | 0 | 400 | 800 | 1,200 | 1,600 | 2,000 | 2,400 | 2,800 |
| Scroll speed × | 1.0 | 1.1 | 1.2 | 1.3 | 1.4 | 1.5 | 1.6 | 1.7 |
| Hazard speed × | 1.00 | 1.06 | 1.12 | 1.18 | 1.24 | 1.30 | 1.36 | 1.42 |
| Rest gap × | 1.00 | 0.90 | 0.81 | 0.73 | 0.66 | 0.59 | 0.53 | 0.48 |
| Adds | Tier 1 | — | Tier 2 | Lava (in waves) | Tier 3 | — | — | Cap |

| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| rest_gap_base | TBD | ticks | — | TBD | DF-02 |
| tier_1_objects | TBD | — | — | TBD | DF-01 |
| tier_2_objects | TBD | — | — | TBD | DF-01 |
| tier_3_objects | TBD | — | — | TBD | DF-01 |

## Rules
1. **Level** = the highest level whose "starts at" is ≤ the run's meters ([06-scoring.md](06-scoring.md)). Meters never go down, so level never goes down.
2. **Scroll speed** multiplies `scroll_base` ([03-world-and-camera.md](03-world-and-camera.md)).
3. **Hazard speed** multiplies every hazard's movement speed ([07-objects.md](07-objects.md)).
4. **Rest gap** multiplies `rest_gap_base`, the pause between waves.
5. **Tier unlocks.** From its level on, a tier's objects may appear in waves.
6. **Lava** becomes available from Level 4. It is a wave hazard with random timing, not an always-on state ([objects/11-lava-walls.md](objects/11-lava-walls.md)).
7. **Nothing else scales.** No extra objects, no bigger hitboxes, no shorter warnings beyond what hazard speed implies. Source: Director.

## Edge cases
- What "Cap" means at Level 8: DF-03.
- The level changes in the middle of a wave: DF-04.

## Open
- DF-01, DF-02, DF-03, DF-04, OB-02.

## How to extend
A new level is a new column. A new scaling row must say what it multiplies and why it doesn't break "nothing else scales". Both are design changes for the Director, logged in [91-decision-log.md](91-decision-log.md).
