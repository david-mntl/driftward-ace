Score: 8.0 | Lowest: 7 | Size: 9

Asset: coin-d2
Kind: sprite
Round: 3
Image: staging/assets/sprites/coin-d2-r3.png
Board: staging/assets/sprites/coin-d2-r3-board.png
Measured: 48 × 24 px, 2 frames, 24 × 24 each (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md, 07-drifters.md
Previous report: docs/reports/ui-art/coin-d2-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The strip is 48 × 24 with two 24 × 24 frames, exactly `art_canvas` (`guess`). On the 4× zoom the upright crystal and the wide ring fill the frame as the spec asks (12 × 20 crystal, 22 × 8 ring), and the faint 12 × 10 hitbox outline sits on the crystal's rectangle with the triangle tips outside it, so the hitbox is not bigger than what is drawn (07-drifters rule 8). Only the strip and frame sizes come from the measured numbers; crystal and ring proportions are judged by eye on the board. |
| 2 | World fit | 8 | Still reads as "a small crystal with a galaxy turning inside" (world brief, "The new universe"): a hexagonal glass crystal, a glowing ring and a bright S-shaped galaxy on a dark interior. The 8× master has good glass depth: a dark body, a lighter edge and a faint glassy sheen on the left face. Two gaps against the "glassy" direction remain. The galaxy is still one S-stroke, not a barred two-armed spiral, because the straight bar through the core is not drawn. The dusty cloud is still only faint specks around the crystal and ring. |
| 3 | Colors | 7 | All fuchsia, pink and purple, so rule 6 holds and it reads as a coin. The crystal body is now clearly black-purple and the near-black interior shows at 1×, which moves `look_reference` ("red, black and purple") closer: black and purple are in, bright pink is the ring and rim. The crimson (200, 30, 90) lit side is still not a clear zone. The left and upper-left faces are dark maroon, close to the shade side, and the edges and ring are the same bright pink. The coin reads as a dark gem with pink outlines, not as crimson and black halves. The rare glint is a clean white-pink. |
| 4 | Light & glow | 8 | The crystal's bottom edges and the lower arc of the ring are the brightest parts, which follows rule 8 (rim on the bottom side, toward the black hole). The rare frame shines clearly more at game size: a large soft flare at the upper left, a star glint at the lower right and a hotter galaxy, as `variants` asks. Coin glow is allowed (`glow`) and is a soft halo. What is left: the rim is still wide and soft in the master, not a thin line, and the top arc of the ring is still fairly bright. |
| 5 | Readability & finish | 8 | At 1× on the strip both frames read as a pink gem with a ring on the navy background (Pillar 2, rule 2). The darker interior now makes the bright S visible inside the crystal at 1×, which was not true in round 2. The rare frame is told apart from the common one at a glance. Edges after the shrink are smooth. What is left: the galaxy is a single S with no bar or arms at 1×, and where the ring crosses the crystal's lower faces the two pinks still merge. |

## Fix first
- Colors: make the crimson lit side show. Paint the upper-left crystal faces in (200, 30, 90), clearly lighter than the black-purple right and top faces, and keep the bright pink for the ring and a thin bottom rim.
- Readability & finish: add the straight bar through the galaxy core, with two arms leaving its ends, so "barred two-armed" reads at 1×. Put a darker gap or a different tone where the ring crosses the lower crystal faces.

## Since round 2
- Size: 9 to 9, no change.
- World fit: 8 to 8, no change. The glass depth is good; the bar and the dusty cloud are still weak.
- Colors: 7 to 7, no change. Black-purple now shows, but the crimson lit side still does not read as its own zone.
- Light & glow: 8 to 8, no change.
- Readability & finish: 7 to 8. The dark interior now gives the galaxy contrast at 1×.
