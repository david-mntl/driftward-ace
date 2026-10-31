Score: 7.6 | Lowest: 7 | Size: 9

Asset: coin-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/coin-d2-r1.png
Board: staging/assets/sprites/coin-d2-r1-board.png
Measured: 48 × 24 px, 2 frames, 24 × 24 each (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The strip is 48 × 24 with two 24 × 24 frames, which is exactly `art_canvas`. In the 4× zoom the upright crystal and the wide ring fill the frame as the spec asks (12 × 20 crystal, 22 × 8 ring, `guess`). The faint 12 × 10 hitbox outline sits on the crystal's rectangle and the triangle tips stay outside it. I judged the crystal and ring proportions by eye on the board; only the strip and frame sizes come from the measured numbers. |
| 2 | World fit | 8 | It reads as "a galaxy turning inside a crystal" (world brief, "The new universe"): a hexagonal glassy crystal, a ring around it, and a dark purple interior with a glowing S-shaped galaxy. The direction was "glassy, barred two-armed galaxy, dusty soft cloud". The glass is clear in the 8× master. The two arms read as an S. The bar through the core is weak and the dusty cloud shows only as faint specks near the crystal edge, so at 1× the galaxy is a pink S-blob. |
| 3 | Colors | 7 | Everything stays in fuchsia, pink and purple, so rule 6 holds: it reads as a coin. The `look_reference` asks for "a fusion of red, black and purple". The crystal walls are mostly bright pink and the crimson lit side (200, 30, 90) hardly shows. The near-black core is only visible in the 8× master, so the 4× zoom looks flatter and pinker than the palette. The rare glint is white-pink and clean. |
| 4 | Light & glow | 7 | Coins in play are meant to glow (`glow`), and they do: a soft pink halo around the ring and a bright glow in the galaxy. The rare frame shines more, with a hard white glint at the upper left of the crystal, a small star glint at the lower right and a hotter galaxy core, as the spec asks. Two gaps. Rule 8 puts the rim on the bottom side, but the crystal and ring edges look about equally bright all the way round. At game size the rare frame differs from the common one only by a small white dot at the top left of the crystal. |
| 5 | Readability & finish | 7 | On the 1× strip both frames read at once as a bright pink gem with a ring, clearly apart from the navy background, which is Pillar 2. Edges after the shrink are smooth. The small interior detail (the bar, the cloud, the glass) blurs to a single pink mass at 1×. The ring and the crystal rim are the same pink and merge where they cross. |

## Fix first
- Colors: let the crimson lit side and the black-purple shade side show on the crystal faces and around the core, so "red, black and purple" reads at 1×. Keep bright pink for the ring and a thin rim.
- Light & glow: put the brighter rim on the bottom of the crystal and ring (rule 8) and make the rare frame's extra shine clearer at 1× than one small dot.
- Also, if there is room: make the galaxy's bar a little stronger so the "barred" direction shows.
