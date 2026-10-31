Score: 7.8 | Lowest: 7 | Size: 9

Asset: coin-d2
Kind: sprite
Round: 2
Image: staging/assets/sprites/coin-d2-r2.png
Board: staging/assets/sprites/coin-d2-r2-board.png
Measured: 48 × 24 px, 2 frames, 24 × 24 each (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md, 07-drifters.md
Previous report: docs/reports/ui-art/coin-d2-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The strip is 48 × 24 with two 24 × 24 frames, exactly `art_canvas` (`guess`). In the 4× zoom the upright crystal and the wide ring fill the frame as the spec asks (12 × 20 crystal, 22 × 8 ring). The faint 12 × 10 hitbox outline sits on the crystal's rectangle and the triangle tips stay outside it, so the hitbox does not exceed what is drawn (07-drifters rule 8). Only the strip and frame sizes come from the measured numbers; crystal and ring proportions are judged by eye on the board. |
| 2 | World fit | 8 | Same strong read as round 1: "a tiny galaxy turning inside a crystal" (world brief, "The new universe"). A hexagonal glass crystal, a glowing ring and an S-shaped galaxy on a dark purple interior. The 8× master has more glass depth than round 1: darker, varied faces with a lighter edge. This fits the "glassy" direction. The bar through the core is still faint, so the galaxy reads as an S, not a barred two-armed spiral. The dusty cloud is still only faint specks near the crystal's inner edge. |
| 3 | Colors | 7 | Still all fuchsia, pink and purple, so rule 6 holds: it reads as a coin. The crystal walls are a little darker and more purple than round 1, and the interior is deeper. But `look_reference` asks for "a fusion of red, black and purple", and the crimson lit side (200, 30, 90) is still not a clear zone: the crystal edges are pink to pale pink and the ring is the same pink. At 1× and in the 4× zoom the coin is still one pink mass with no visible black. The rare glint is clean white-pink. |
| 4 | Light & glow | 8 | Both round-1 gaps moved. The crystal's bottom edges and the lower arc of the ring are now brighter than the top, which follows rule 8 (rim on the bottom side, toward the black hole). The rare frame now shines clearly more at game size: a large soft flare at the upper left of the crystal in the 4× zoom, a star glint at the lower right and a hotter core, as `variants` asks. Coin glow is allowed (`glow`) and is present as a soft halo. What is left: the rim is still wide and soft, not a thin line, and the top of the ring is still fairly bright. |
| 5 | Readability & finish | 7 | On the 1× strip both frames read as a bright pink gem with a ring, well apart from the navy background (Pillar 2, rule 2). The rare frame is now told apart from the common one at a glance, which was a problem in round 1. Edges after the shrink are smooth. At 1× the galaxy, bar and glass detail still merge into one pink blob, and the ring and crystal rim are the same pink where they cross. |

## Fix first
- Colors: make "red, black and purple" show. Put the crimson lit side on the upper-left crystal faces and the black-purple shade side on the right and top faces, and keep bright pink for the ring and a thin bottom rim only. The near-black core must read at 1×.
- Readability & finish: give the galaxy more contrast against the crystal interior and strengthen the bar so the "barred" direction shows at 1×. Separate the ring from the crystal rim where they cross (a darker gap or a different tone).

## Since round 1
- Size: 9 to 9, no change.
- World fit: 8 to 8, no change. The glass depth is better, but the bar and the dusty cloud are still weak.
- Colors: 7 to 7, no change. The walls are slightly darker, but the crimson and black zones still do not read.
- Light & glow: 7 to 8. The bottom rim is now the brighter side, and the rare frame's flare and glints read at game size.
- Readability & finish: 7 to 7, no change. The rare frame is easier to tell from the common one, but the interior detail still blurs at 1×.
