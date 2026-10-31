Score: 7.8 | Lowest: 7 | Size: 9

Asset: floating-island-d1
Kind: sprite
Round: 3
Image: staging/assets/sprites/floating-island-d1-r3.png
Board: staging/assets/sprites/floating-island-d1-r3-board.png
Measured: 320 × 120 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches the rectangle variant and `art_canvas` (a `guess`). The ground fills the whole box. The board's hitbox outline sits on the image edge with no transparent margin, so the hitbox ("the shape itself, exactly as drawn") is covered. The dark green fade around the border is still ground, not a transparent edge. |
| 2 | World fit | 8 | Follows the direction closely: green moss on top with drips, layered strata in the body (tan, rose-brown, violet, indigo, navy), a darker green-brown edge. It reads as a cracked-off chunk of planet. The vivid colors and deep navy shadows at the bottom suit "The light". The flat ovals from round 2 are gone, so nothing breaks the glossy look any more. The moss is still soft and cloudy, more painted than "glossy and wet". |
| 3 | Colors | 7 | The orange and cyan ovals are gone, so heat and electricity no longer sit on a harmless blocker. The moss is a clean vivid green (`look_reference`), and the bands separate clearly by lightness and hue. Two small notes. The rose band is a large salmon-orange area. It is muted enough to read as soil, not as heat, but it sits close to the warm meaning. A few dark and blue-grey blobs remain in the violet and indigo bands (left of center). They are low contrast and don't read as a color meaning. |
| 4 | Light & glow | 8 | Rule 8 is met: a thin bright fuchsia rim runs the full width of the bottom edge, the side facing the black hole, and it is thin enough for rule 6. Hard white highlights are there: the pale streak along the top of the moss and the white specks. The highlight streak stops about three quarters of the way across the top, so the light looks uneven. Shadows in the lower strata go deep navy. No glow is drawn, and none is needed (the island is not a hazard, warning or coin). |
| 5 | Readability & finish | 7 | Streak banding in the strata is gone, and the bands now read smooth with clean wavy edges. The drips give a strong silhouette. Two things hold the score back. First, the top edge. The moss fades into a dark green vignette at the box edge, so at 1× the standing surface is less crisp than in round 2, and it sits close to the navy background. Second, the moss body is blurry (cloudy blobs, faint grass strokes) next to the crisp band lines, so the finish is uneven. |

## Fix first
- Readability & finish: sharpen the top edge so the standing surface reads as a clear bright green line against the navy, and give the moss body the same clean, smooth finish as the band lines.
- Colors: pull the rose band toward a cooler, less orange tone so it can't read as the heat color, and drop the leftover dark blobs in the violet and indigo bands.

## Since round 2
- World fit 7 → 8: the flat ovals are removed, so the strata read as glossy planet rock.
- Colors 6 → 7: the orange and cyan ovals no longer break the color language. The rose band is still warm.
- Readability & finish 7 → 7: the streak banding and the outlined ovals are gone, but the top edge now fades into a dark vignette and the moss is still blurry.
- Size 9 and Light & glow 8: unchanged.
