Score: 7.0 | Lowest: 6 | Size: 9

Asset: coin-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/coin-d4-r1.png
Board: staging/assets/sprites/coin-d4-r1-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md, 07-drifters.md
Direction for this design: clean prism with flat facets and a ring of tiny bright specks.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The strip is 48 × 24 with two 24 × 24 frames, which is the `art_canvas` (`guess`). The prism spans the middle of each frame and fills the 12 × 10 hitbox box drawn on the board, so the ship must really touch the crystal. The ring sits across the crystal's middle as `art_canvas` asks. The ring's left and right specks sit close to the frame edge. I can't confirm the exact crystal and ring pixel sizes by eye. |
| 2 | World fit | 6 | The direction is followed: flat facets (lit left, dark right) and a ring of tiny specks. It reads as a gem. The "tiny swirling galaxy" in `look_reference` does not read. The dark inner panel carries a pink "S" or "5" shape that looks like a digit or a letter, not a spiral. There is no visible cloud inside the square (`art_canvas`). The crystal is opaque, not "transparent". The collapse and "new universe" feeling is weak. |
| 3 | Colors | 7 | Crimson to hot pink on the lit side and black-purple on the shade side follow the coin `palette`, with a bright red-pink ring. It owns solid fuchsia as coins should (rule 6) and stays well apart from hazard orange and electric cyan. On the 4× zoom the lit facets lean light pink-magenta, not the crimson (200, 30, 90) in the spec. The facets blur together into a pink mass, and the dark panel is the only deep value. |
| 4 | Light & glow | 7 | A coin must glow (GDD 12 `glow`). The 8× master has a soft pink halo around the ring and a hard white highlight at the upper left (rule 8 and "The light"). The rare one shines more: a big white-pink glint at the upper left and a small one at the lower right (`palette` rare glint). At 1× the halo almost disappears, so common and rare look close. The rim is lit all the way round, so the bottom side facing the black hole is not stronger than the top (rule 8). |
| 5 | Readability & finish | 6 | At 1× on the board's dark navy it reads as a small pink gem with a ring, so it stands out from the background (rule 2). The finish is weak at game size. The ring specks merge into a lumpy band on the 4× zoom. The inner "S" is a few mushy pixels and the facet lines are soft, not clean flat facets. The common and rare strip entries differ only by the glints, which are small at 1×. |

## Fix first
- World fit: make the galaxy inside read as a spiral with a visible cloud (red, black and purple), not a glyph that looks like a "5". Keep the near-black core.
- Readability & finish: keep the ring specks apart so they survive the shrink, and make the facet edges and the common-to-rare difference clearer at 1×.
