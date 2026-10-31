Score: 8.2 | Lowest: 8 | Size: 9

Asset: ufo-d2
Kind: sprite
Round: 3
Image: staging/assets/sprites/ufo-d2-r3.png
Board: staging/assets/sprites/ufo-d2-r3-board.png
Measured: 40 × 20 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/07-ufo.md
Direction judged: design 2, wrecked (dented hull, cracked green dome, scorch marks, still flying; lights never cobalt)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 40 × 20 matches `art_canvas` (40 wide, disc in the bottom 10 rows, dome above it; `guess`). On the board's 4× hitbox overlay, the hull fills the 40 px width of the disc box and sits inside it. The dome sits inside the radius 9 circle centered on the disc's top edge. I read the row split from the overlay only, not from measured numbers, so I stop at 9. |
| 2 | World fit | 8 | The wrecked direction follows the world brief ("metal ships and satellites drift dead, or worse, half alive"). Heavy dark cracks on the dome, orange scorch at both ends of the hull and a chipped lower hull read as a damaged ship still flying. It stays lonely, not horror. The cracks are now so thick that in the 1/2-scale master they look like a dark claw or glyph across the dome more than fracture lines. They could branch thinner from one impact point. |
| 3 | Colors | 8 | The dome is a clean green, as `look_reference` asks, and it is still the cleanest shape on the sprite. The hull is a light-to-mid grey that separates from the navy. The orange and yellow scorch and window lights fit "heat, danger" (color language). No light is cobalt. Fuchsia stays a thin accent (rule 6). The scorch at the hull ends still mixes into a brown-orange at 1× and softens the disc's ends a little. |
| 4 | Light & glow | 8 | Better than round 2. In the 4× view and the master, a green halo now wraps the dome and a warm orange glow follows the hull ends, which answers the round 2 note and the `glow` rule (hazards glow; `guess`). The thin fuchsia rim runs along the bottom of the disc, as rule 8 asks, and does not turn into a solid fuchsia shape. The dome keeps a hard pale highlight at upper left ("The light"). On the board's "1× on a purple glow" strip the halo is still soft; only a light green haze around the dome shows, and the warm glow on the hull is hard to see. |
| 5 | Readability & finish | 8 | At 1× it reads as a saucer with a green dome, and the dome is the focus (Pillar 2). The dome cracks are now dark enough to show at 1× as dark strokes on the green, so "cracked" reads without the 4× view. That was the main round 2 gap. The hull dents are still subtle at 1×. The cracks are heavy enough to break up the dome's round outline at its upper right. Edges at 4× are smooth. |

## Fix first
- Light & glow: raise the warm glow along the hull so it shows on the purple strip at 1×, not only in the 4× view and the master.
- Readability & finish: thin the dome cracks and branch them from one point, so the dome still reads as a round green shape. Add one clearer dent in the hull outline that shows at 1×.

## Since round 2
- Light & glow 7 to 8: the halo is wider, green around the dome and warm at the hull ends. It is still faint at 1× on the purple strip.
- Readability & finish 7 to 8: the dome cracks now show at 1×. The heavy strokes cost some of the dome's round shape.
- Size 9, World fit 8, Colors 8: no change.
