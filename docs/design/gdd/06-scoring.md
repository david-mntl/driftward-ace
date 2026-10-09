# Scoring
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [05-lives-and-damage.md](05-lives-and-damage.md), [07-objects.md](07-objects.md)

## Summary
`score = meters + 50 × coins + 25 × grazes`. Meters come from the highest point reached, so hovering scores nothing. Coins sit near danger. Grazes pay for flying close to a hazard and getting away clean. Grazes should add about 20–30% to a good run.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| points_per_meter | 1 | points/m | — | locked | Director |
| coin_points | 50 | points | — | locked | Director |
| graze_points | 25 | points | — | locked | Director |
| graze_margin | 14 | px added to hitbox radius | — | locked | Director |
| graze_share_target | 20–30 | % of a good run's score | — | locked | Director. A tuning target, not a rule in code |
| meters_rounding | TBD | — | — | TBD | SC-01 |

## Rules
1. **Meters** = highest altitude reached ÷ `px_per_meter` ([03-world-and-camera.md](03-world-and-camera.md)). It never goes down.
2. **Coins.** Touching a coin collects it: +`coin_points`, and the coin disappears. Coins are placed near hazards ([objects/04-coin.md](objects/04-coin.md)). Whether an invulnerable ship can collect is SC-05.
3. **Graze zone** = the hazard's hitbox radius + `graze_margin`. See SC-03 for hazards that aren't circles.
4. **Graze pays** `graze_points` once per hazard, on the tick the ship leaves that hazard's zone without having touched the hazard.
5. **Graze never pays** while the ship is invulnerable, for walls or lava, or for coins. See SC-02 for a ship that enters while invulnerable and leaves after.
6. A hazard that hits the ship pays no graze.
7. **Best score** needs saves. Until saves ship there is no BEST. See [11-save-data.md](11-save-data.md), FL-03.

## Edge cases
- The ship enters and leaves the same hazard's zone several times: it pays once, on the first clean exit.
- A hazard leaves the screen while the ship is still in its zone: SC-04.

## Open
- SC-01, SC-02, SC-03, SC-04, SC-05, FL-03.

## How to extend
A new score source must say: how much, when it pays, whether it pays during invulnerability, and why it doesn't break Pillar 3 (no free safe points, no score for hiding). Add it to the formula in Summary.
