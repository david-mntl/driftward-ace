Score: 7.8 | Lowest: 7 | Size: 8

Asset: coin-d5
Kind: sprite
Round: 3
Image: staging/assets/sprites/coin-d5-r3.png
Board: staging/assets/sprites/coin-d5-r3-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md
Direction: design 5, nebula (a wispy cloud swirling around the crystal, a soft ring)
Previous report: docs/reports/ui-art/coin-d5-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, which matches `art_canvas`. On the board the crystal is upright and centered in both frames, and the 12 × 10 hitbox outline sits on the crystal body (`hitbox`, `guess`). The ring and halo stay inside each frame and don't clip. I can't read exact crystal pixels by eye, so the 12 × 20 crystal is judged from the board overlay only. The lower triangle still looks a touch shorter than the upper one (`crystal_size`, `guess`). |
| 2 | World fit | 8 | It follows the nebula direction and `look_reference`: a faceted crystal, a swirl of galaxy inside, a pink ring across the middle and a soft haze. It matches "small crystals with a galaxy turning inside" and the mood in GDD 12 ("beautiful and doomed"). The spiral is now a lit pink arm around a dark core, so it reads as a galaxy. The cloud at game size is still a soft diamond-shaped halo around the crystal, not wisps swirling around it. Only the 8× master shows the cloud as a wispy band. |
| 3 | Colors | 7 | Bright and clean, with no mud. The ring and rim are bright red-pink as in `palette`, the shade side is dark black-purple and the core is near black. In the 4× zoom the lit left face looks a little warmer than in round 2, but it still reads magenta-pink, not the crimson (200, 30, 90) in `palette`. The "red, black and purple" fusion in `look_reference` leans pink and purple, and red is still thin. Rule 6 is met: the coin is the one solid fuchsia shape on the dark ground. |
| 4 | Light & glow | 8 | Coins may glow (GDD 12 `glow`). The pink halo lifts the crystal off the navy without hiding it. The brightest rim is on the lower edges of the bottom triangle, the side facing the black hole (rule 8). The rare frame has a white sparkle at the upper left of the crystal, a brighter ring and a stronger halo, so "the rare one shines more" holds. The glint matches (255, 220, 240). |
| 5 | Readability & finish | 8 | At 1× both coins are easy to find on navy. The spiral inside is now a light swirl that shows at 24 px, not the dark smudge from round 2. The ring shows as pink arcs on the left and right of the crystal. The rare sparkle makes common and rare easier to tell apart at a glance (rule 2). Two things are left. The halo edge still steps in blocks around the diamond in the 4× zoom. The crystal's top and bottom edges show some stair-steps. |

## Fix first
- Colors: push the lit face from magenta-pink toward crimson (200, 30, 90), so red shows in the red, black and purple fusion. Keep the shade near black-purple and the ring and rim bright red-pink.
- Readability & finish: smooth the halo falloff so it doesn't step around the diamond. Make the haze read as one or two thin wisps outside the crystal, not a filled diamond. Soften the stair-steps on the top and bottom triangle edges.

## Since round 2
- Readability & finish 7 to 8: the spiral now reads as a light swirl at game size, and the ring arcs are clear at 1×.
- Colors stays 7: the lit face is a little warmer but still magenta-pink, not crimson.
- Size, World fit and Light & glow are unchanged. The haze is still a diamond at game size, so World fit stays 8.
