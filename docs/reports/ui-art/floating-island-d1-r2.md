Score: 7.4 | Lowest: 6 | Size: 9

Asset: floating-island-d1
Kind: sprite
Round: 2
Image: staging/assets/sprites/floating-island-d1-r2.png
Board: staging/assets/sprites/floating-island-d1-r2-board.png
Measured: 320 × 120 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches the rectangle variant and `art_canvas` (a `guess`). The ground fills the whole box and the board's hitbox outline sits on the image edge with no transparent margin, so the hitbox ("the shape itself, exactly as drawn") is covered. A thin darker vignette runs around the border; that is fine for "no transparent edge". |
| 2 | World fit | 7 | Follows the direction closely: green moss on top with drips, layered strata in the body (tan, rose, violet, indigo, navy), darker edge. The strata now read as a cracked-off chunk of planet, and the vivid, deep-shadowed palette suits "colors are more vivid than they should be". The orange and cyan ovals in the strata look like flat stickers, not glossy "wet" ore, so they sit outside the glossy look in "The light". |
| 3 | Colors | 6 | Round 1's mud is gone: the bands are clearly separated by lightness and hue, and the moss is a clean vivid green (`look_reference`). Two problems with the color language. The orange ovals (left rose band, right violet band, bottom) use orange, which means heat and danger, on a blocker that cannot hurt. The cyan ovals (rose band, violet band, indigo band) are saturated teal; cyan is the electricity color. At 1× both read as small hot or electric spots on harmless ground, against Pillar 2. The rose and violet bands are the largest pink-purple areas; they are muted enough not to read as a coin (rule 6), but they sit close to the anomaly's colors. |
| 4 | Light & glow | 8 | Rule 8 is met: a thin bright fuchsia rim runs the full width of the bottom edge, the side facing the black hole, and it is thin enough for rule 6. Hard white highlights are there: the pale streak along the top of the moss and a few white specks. Shadows in the lower strata and under the moss drips now go deep navy, as "The light" asks. No glow is needed (the island is not a hazard, warning or coin), and none is drawn. |
| 5 | Readability & finish | 7 | At 1× the top surface is clear: a bright green flat edge with a pale highlight line against the dark navy, so the player can see where to stand. The drips give a good silhouette inside the art. Fewer pebbles and specks than round 1. Still, the strata carry visible horizontal streak banding at 1× and the board's 4× view, and the thin dark cracks (left and right of the violet band) and the outlined ovals add noise below the top surface. The moss body is soft and blurry next to the crisp band lines, so the finish is uneven, not "smooth and glossy" throughout. |

## Fix first
- Colors: repaint the orange and cyan ovals in colors that are not heat or electricity (for example a lighter or darker shade of the band they sit in), or remove them. Keep any warm or cold accent out of the play-area color meanings.
- Readability & finish: remove the horizontal streak texture in the strata and soften or drop the outlined ovals and thin cracks, so the moss top stays the clearest thing and the body reads smooth.

## Since round 1
- Light & glow 7 → 8: shadows in the strata and under the moss now go deep navy instead of brown-black, and the fuchsia rim stays thin on the bottom edge.
- Colors stayed at 6: the mud is fixed, but the new orange and cyan ovals break the color language.
- World fit stayed at 7: the strata now read as planet rock, but the flat ovals work against the glossy look.
- Readability & finish stayed at 7: fewer pebbles and specks, but streak banding and the ovals add new noise.
