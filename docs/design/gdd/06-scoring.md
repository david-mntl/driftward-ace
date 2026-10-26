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
| graze_cap | none. Every graze pays the full `graze_points`, and the count has no limit. No multiplier | — | — | locked | Director |
| graze_popup | `+25` (the `graze_points`) at the ship's center on the tick the graze pays. It rises 0.5 px per tick and is gone after 60 ticks (1 s). Same text size as the coin popup ([drifters/04-coin.md](drifters/04-coin.md)) | — | — | guess | Director |
| graze_popup_color | (255, 255, 255) | RGB | — | guess | Director |
| graze_ring | a thin ring (1 px) on the ship's center, following the ship. It grows from 16 px to 32 px across in 15 ticks and fades out as it grows. Shows on the tick the graze pays, with the popup | — | — | guess | Director |
| graze_ring_color | (255, 255, 255) | RGB | — | guess | Director |
| graze_sound | none yet. Comes with the game's sound ([12-art-and-audio.md](12-art-and-audio.md), AA-03) | — | — | — | Director |

## Rules
1. **Meters** = distance ÷ `px_per_meter` ([03-world-and-camera.md](03-world-and-camera.md) rule 8), rounded per `meters_rounding`. It never goes down.
2. **Coins.** Touching a coin collects it: + its variant's `coin_points`, and the coin disappears. Coins are placed near hazards ([drifters/04-coin.md](drifters/04-coin.md)). An invulnerable ship collects coins too.
3. **Graze zone** = each shape of the hazard's hitbox, grown by `graze_margin` on every side: a circle's radius grows by it, a box grows by it on all four sides, a line grows by it on each side and at both ends, a polygon grows by it outward from every edge. A spec may limit when its zone counts (chain lightning: only while an arc fires).
4. **Graze pays** `graze_points` once per hazard, on the tick the ship leaves that hazard's zone without having touched the hazard. The zone going away with the ship still inside counts as leaving it: the hazard leaves the screen, or its zone switches off (a hazard that grazes only while it fires stops firing).
5. **Graze never pays** while the ship is invulnerable or in the respawn wait ([05-lives-and-damage.md](05-lives-and-damage.md) rule 2.5), for walls, lava or blockers (floating islands), or for coins. Only the ship's state on the tick it leaves counts: a ship that enters while invulnerable and leaves after invulnerability ends pays. A ship hovering in place is still flying and can graze.
6. A hazard that hits the ship pays no graze.
7. **No cap.** Grazes stack: each one adds the full `graze_points`, with no limit and no multiplier.
8. **Feedback.** When a graze pays, `graze_popup` and `graze_ring` show, and the HUD's graze count goes up by one ([10-ui.md](10-ui.md) rule 2). Sound: none yet.
9. **Best score** needs saves. Until saves ship there is no BEST. See [11-save-data.md](11-save-data.md), FL-03.

## Edge cases
- The ship enters and leaves the same hazard's zone several times: it pays once, on the first clean exit.
- A hazard leaves the screen while the ship is still in its zone: it pays, if the ship never touched it (rule 4).
- A hazard that grazes only while it fires stops firing while the ship is in its zone: it pays, if the ship never touched it (rule 4). Its next firing can't pay again: once per hazard.
- The ship is in the respawn wait when it leaves a zone: no pay, even after invulnerability has run out (rule 5).

## Open
- FL-03.

## How to extend
A new score source must say: how much, when it pays, whether it pays during invulnerability, and why it doesn't break Pillar 3 (no free safe points, no score for hiding). Add it to the formula in Summary.
