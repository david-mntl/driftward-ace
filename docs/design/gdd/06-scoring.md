# Scoring
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [05-lives-and-damage.md](05-lives-and-damage.md), [07-drifters.md](07-drifters.md)

## Summary
`score = meters + coin points + 25 × grazes`. Meters count distance flown, so surviving earns them. Coins and grazes pay extra for going near danger, so taking risks always beats just surviving. Coins sit near danger. Grazes pay for flying close to a hazard and getting away clean. Grazes should add about 20–30% to a good run.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| points_per_meter | 1 | points/m | — | locked | Director |
| coin_points | set per coin variant: common 50, rare 100 ([drifters/04-coin.md](drifters/04-coin.md)) | points | — | common 50: locked; rare 100: guess | Director |
| graze_points | 25 | points | — | locked | Director |
| graze_margin | 14 | px added around each hitbox shape | — | locked | Director |
| graze_share_target | 20–30 | % of a good run's score | — | locked | Director. A tuning target, not a rule in code |
| meters_rounding | whole meters, rounded down | — | — | locked | Director |

## Rules
1. **Meters** = distance ÷ `px_per_meter` ([03-world-and-camera.md](03-world-and-camera.md) rule 8), rounded per `meters_rounding`. It never goes down.
2. **Coins.** Touching a coin collects it: + its variant's `coin_points`, and the coin disappears. Coins are placed near hazards ([drifters/04-coin.md](drifters/04-coin.md)). An invulnerable ship collects coins too.
3. **Graze zone** = each shape of the hazard's hitbox, grown by `graze_margin` on every side: a circle's radius grows by it, a box grows by it on all four sides, a line grows by it on each side and at both ends, a polygon grows by it outward from every edge. A spec may limit when its zone counts (chain lightning: only while an arc fires).
4. **Graze pays** `graze_points` once per hazard, on the tick the ship leaves that hazard's zone without having touched the hazard.
5. **Graze never pays** while the ship is invulnerable, for walls, lava or blockers (floating islands), or for coins. See SC-02 for a ship that enters while invulnerable and leaves after.
6. A hazard that hits the ship pays no graze.
7. **Best score** needs saves. Until saves ship there is no BEST. See [11-save-data.md](11-save-data.md), FL-03.

## Edge cases
- The ship enters and leaves the same hazard's zone several times: it pays once, on the first clean exit.
- A hazard leaves the screen while the ship is still in its zone: SC-04.

## Open
- SC-02, SC-04, FL-03.

## How to extend
A new score source must say: how much, when it pays, whether it pays during invulnerability, and why it doesn't break Pillar 3 (no free safe points, no score for hiding). Add it to the formula in Summary.
