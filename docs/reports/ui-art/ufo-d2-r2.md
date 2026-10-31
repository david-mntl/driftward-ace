Score: 7.8 | Lowest: 7 | Size: 9

Asset: ufo-d2
Kind: sprite
Round: 2
Image: staging/assets/sprites/ufo-d2-r2.png
Board: staging/assets/sprites/ufo-d2-r2-board.png
Measured: 40 × 20 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/07-ufo.md
Direction judged: design 2, wrecked (dented hull, cracked green dome, scorch marks, still flying; lights never cobalt)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 40 × 20 matches `art_canvas` (40 wide, disc in the bottom 10 rows, dome above it; `guess`). On the board's 4× hitbox overlay, the disc fills the 40 px box width and the hull sits inside the 40 × 10 disc box. The dome sits inside the radius 9 circle centered on the disc's top edge. I judged the row split only from the board overlay, not from measured numbers, so I stop at 9. |
| 2 | World fit | 8 | The wrecked direction follows the world brief ("metal ships and satellites drift dead, or worse, half alive"). The dark crack lines across the dome, the orange-brown scorch patch at the right of the hull and the dented, chipped lower hull read as a damaged ship still flying. It stays lonely, not horror. At 1× the cracks are a few dark pixels, so "cracked" reads weaker than in the 4× view. |
| 3 | Colors | 8 | Better than round 1. The dome is a clean mid-to-light green, as `look_reference` asks, and it is the cleanest shape on the sprite. The hull is now a lighter grey, so its lower half separates from the navy. The scorch is cut to one clear patch at the right, so the hull is not muddy. The yellow and orange window lights and scorch fit "heat, danger". No light is cobalt. The scorch patch is still a brown-orange mix at 1× and softens the right end of the disc a little. |
| 4 | Light & glow | 7 | The fuchsia rim now runs as one thin line along the whole bottom of the disc, with no gap at the dent, as rule 8 asks. It stays a thin accent, so rule 6 holds. The dome keeps a hard pale highlight at upper left ("The light"). The master (shown at 1/2) now has a soft halo, which answers the round 1 note on `glow` (hazards glow; `guess`). At game size the halo is faint: in the board's "1× on a purple glow" strip the sprite still reads almost as a plain silhouette, with a light green haze only around the dome. A warmer or wider halo would show at 1×. |
| 5 | Readability & finish | 7 | At 1× it reads as a saucer with a green dome on the dark background, and the dome is the clear focus (Pillar 2). The interior is much calmer than in round 1: the speckle is gone and the window lights and rim are easy to follow. The dome cracks and hull dents are still hard to see at 1×; they only show at 4×. Edges at 4× are smooth, with a small stair-step on the dome's upper right. |

## Fix first
- Light & glow: make the halo show at 1×. On the purple strip it nearly disappears, so widen or brighten it (green around the dome, warm along the hull), as GDD 12 `glow` asks.
- Readability & finish: make the damage show at game size. Make the dome cracks wider or higher in contrast, and add one clearer dent in the hull outline, so "wrecked" reads without the 4× view.

## Since round 1
- Colors 7 to 8: the lower hull is lighter and the scorch is one clear patch, so the muddy bottom-left is gone.
- Light & glow 6 to 7: the rim is continuous along the bottom and a soft halo exists in the master. It is still faint at 1×.
- Readability & finish 7 to 7: the speckle is gone and the interior is cleaner, but the dome cracks are still lost at 1×, so the score does not move.
- Size 9 and World fit 8: no change.
