Score: 7.4 | Lowest: 6 | Size: 8

Asset: ufo-d5
Kind: sprite
Round: 2
Image: staging/assets/sprites/ufo-d5-r2.png
Board: staging/assets/sprites/ufo-d5-r2-board.png
Measured: 40 × 20 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/07-ufo.md, 07-drifters.md (read for shared looks; the entry warning is not part of this still)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 40 × 20 matches `art_canvas` (`guess`). On the board's hitbox view the disc now runs square to both ends of the 40 × 10 box in the bottom half, so the tapered empty corners from round 1 are gone and the hull covers the disc hitbox. The dome is centered on the disc's top edge, but it still sits well inside the radius-9 dome circle (`guess`): the circle's top arc clears the dome by a clear gap on the 4x view. The direction asks for a "small" dome, so this is a mild gap. |
| 2 | World fit | 7 | A thick disc with seams, vents and a row of underside lights fits "metal ships drift dead, or worse, half alive" and the "heavy" direction. The green dome reads as "saucer with a green dome, no beam" (`look_reference`). The master (shown at 1/2) has a hard white highlight on the dome and a pale top edge on the hull, as "The light" asks. At 1× the vents and panels still blur into grey speckle, so the heavy look is less clear than the master promises. |
| 3 | Colors | 8 | The dome is a clean, vivid green. The hull is mid grey to navy, with no cobalt anywhere, as the direction asks. The round 1 orange edge glow on top is gone, and orange now stays on the small underside lights, so the saucer no longer borrows the "orange and yellow = heat" meaning (color language). The hull grey is still a little flat at the far ends, close to the navy. |
| 4 | Light & glow | 8 | The warm halo on the upper edge is gone. A thin fuchsia rim runs along the bottom of the disc in the master, and it shows as a pink line on the 1× purple and black views. That matches rule 8 (bottom side, the side facing the black hole) and keeps rule 6 (coins own solid fuchsia). The rim is faint on the plain 1× view, and the 4x view barely shows it. It could be a touch stronger so it holds at game size. |
| 5 | Readability & finish | 6 | The green dome reads at once at 1× on navy, purple and black, and the saucer silhouette is clear. The hull is the weak part. The 4x view still shows blocky mottling: scattered dark and orange specks on the hull, uneven pixel steps along the top edge, and a soft jagged join where the dome meets the disc. The master has bolder seams than the 1× result keeps, so the shrink step is losing the larger shapes. |

## Fix first
- Readability & finish: after the shrink, the hull still breaks into noisy specks. Keep the 3 or 4 largest seams and vents and drop the small dark and orange specks on the hull face. Smooth the dome-to-disc join and the top edge of the hull.
- Size: enlarge the dome toward the radius-9 hitbox circle (a few more rows and px wide), still centered on the disc's top edge. Keep the square disc ends.

## Since round 1
- Size 8 to 8: the disc ends now fill the box, but the dome is still smaller than its hitbox circle, so the score stays.
- World fit 7 to 7: the heavy look is the same. The hull panel detail still blurs at 1×.
- Colors 7 to 8: the orange edge glow is removed and orange is limited to the small lights.
- Light & glow 7 to 8: the upper halo is gone, so the bottom fuchsia rim is the one edge light.
- Readability & finish 7 to 6: scored against a stricter reading of the 4x view. The hull is still mottled and the top edge and the dome join are still jagged. The round 1 fix on this point did not carry through the shrink.
