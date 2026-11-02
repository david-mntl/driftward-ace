Score: 7.2 | Lowest: 6 | Size: 9

Asset: floating-island-d4
Kind: sprite
Round: 2
Image: staging/assets/sprites/floating-island-d4-r2.png
Board: staging/assets/sprites/floating-island-d4-r2-board.png
Measured: 320 × 120 px, no frames
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md

Direction for this design: mutated jungle, dark green roots and vines woven into a dense slab.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches `art_canvas` and the rectangle variant exactly (`guess`). On the board the ground reaches all four sides of the hitbox outline, with a darker green rim inside it, so the drawn ground and the hitbox match (rule 10). I can't measure alpha by eye; the corners look filled. |
| 2 | World fit | 7 | Woven vines over a dark root bed with hanging claw-like root tips fit "living things mutate" and "planets crack into floating islands" (world brief), and follow the jungle direction. The top two thirds still read as a stack of identical smooth tubes, like cables or pipes, more than a torn-off chunk of ground. Nothing says "ground" except the dark bed at the bottom. |
| 3 | Colors | 7 | Greens are clean and vivid, with a darker green edge as `look_reference` asks. Green is outside every color-language meaning, so it can't be read as a hazard or a coin. The bottom bed is now a deeper green and less grey-blue than round 1, which fits "dark green". The vines are still mostly one mid green with the same highlight on each, so layers don't separate by value. |
| 4 | Light & glow | 7 | The fuchsia rim (rule 8) is now visible at 1× on the board. It follows the wavy underside of the vine layer and runs down the root tips, and a thin line runs along the very bottom edge. No glow is correct for a blocker (glow rule: hazards and coins only). Two issues. The bottom-edge line is still a flat, straight, even band that ignores the outline. The root tips are small solid fuchsia strokes and are the brightest things in the sprite; they are thin accents now, but keep them thin so they never read as a coin (rule 6). Hard white highlights along the vines fit "The light". |
| 5 | Readability & finish | 6 | At 1× the slab reads as a solid green block against the navy and the dark edge holds the silhouette. Inside, the tangle is still busy: about a dozen horizontal tubes of similar width, plus around ten thin hanging tendrils with leaf tips that cross them, so there is no single shape to hold the eye at game size. The tendrils are the main noise. The vine edges and shading are smoother than round 1, with only light banding on the tubes. The bed at the bottom is dim and its crack lines are barely visible. |

## Fix first
- Readability & finish: cut the thin hanging tendrils to a few (3 or 4) and vary the tube widths, with some thick and some thin, so the slab reads in one glance at 1×.
- World fit / Colors: give the vines more value range (darker back tubes, brighter front ones) and break the even horizontal stack with some ground mass, so it reads as a chunk of ground and not a bundle of pipes.

## Since round 1
- Light & glow 6 → 7: the fuchsia rim is now visible at 1× and follows the vine edge and the root tips. The bottom line is still flat.
- Colors 7 → 7: the bottom bed is deeper green and less muddy. The vines still share one mid green, so the score stays.
- Readability & finish 6 → 6: edges are smoother, but the number of tendrils and similar tubes is about the same.
- Size 9 → 9, World fit 7 → 7: unchanged.
