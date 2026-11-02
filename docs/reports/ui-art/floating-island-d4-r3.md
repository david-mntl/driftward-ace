Score: 7.4 | Lowest: 7 | Size: 9

Asset: floating-island-d4
Kind: sprite
Round: 3
Image: staging/assets/sprites/floating-island-d4-r3.png
Board: staging/assets/sprites/floating-island-d4-r3-board.png
Measured: 320 × 120 px, no frames
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md

Direction for this design: mutated jungle, dark green roots and vines woven into a dense slab.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches `art_canvas` and the rectangle variant exactly (`guess`). On the board the ground reaches all four sides of the hitbox outline, with a darker green rim inside it, so the drawn ground and the hitbox match (rule 10). I can't measure alpha by eye; the corners look filled. |
| 2 | World fit | 7 | The woven vines, the diagonal vine and the claw-like root tips fit "living things mutate" and the jungle direction. Round 3 adds a darker, lumpy back layer between the tubes (the olive and dark green patches behind them), and that starts to read as soil. The three thick horizontal tubes are still evenly spaced and uniform, so the middle of the slab still reads as a bundle of pipes more than a torn-off chunk of ground. The ground mass is only visible in the gaps and in the bottom bed. |
| 3 | Colors | 7 | Greens are clean and vivid, with a darker green edge as `look_reference` asks. Green is outside every color-language meaning, so it can't be read as a hazard or a coin. There is more value range than in round 2: a dark back layer, mid-green tubes and bright front highlights. The bottom bed has gone dark teal and the thin tubes in front of it are pale grey-green, so the bed is now bluer than "dark green" and is close to the navy background at its lower edge. |
| 4 | Light & glow | 7 | The fuchsia rim (rule 8) runs along the wavy underside of the vine layer and down five root tips, and the bottom-edge line now has a slight wave. All of it stays thin, so nothing reads as a coin (rule 6). No glow is correct for a blocker (glow rule: hazards and coins only). The bottom-edge line is still a near-flat, even band and the brightest, most saturated stroke in the sprite. Hard white highlights along the tubes fit "The light". |
| 5 | Readability & finish | 7 | At 1× the slab reads as one solid green block with a dark edge holding the silhouette. Hanging tendrils are down to four short vines plus one long diagonal, and the tubes vary in width (thick top and bottom rows, one thin middle row). It is much calmer than round 2. The remaining noise is the dim, hard-to-see crack and ripple work in the bottom bed, and the leaf tips on the tendrils, which are tiny at 1×. Edges are smooth, with light banding on the tubes. |

## Fix first
- World fit: break the even three-row tube stack with some ground mass, such as a thicker soil band or an uneven top edge, so the slab reads as a chunk of ground and not a bundle of pipes.
- Colors: pull the bottom bed back to dark green and away from teal, so it separates from the navy background. Give it a little more value than the surrounding tubes.

## Since round 2
- World fit 7 → 7: the back layer reads more like soil, but the tube stack is the same.
- Colors 7 → 7: more value range in the vines, offset by the bed turning teal and nearly merging with the background.
- Light & glow 7 → 7: the bottom line has a slight wave, but it is still flat and the brightest stroke.
- Readability & finish 6 → 7: tendrils cut to four plus one diagonal, with varied tube widths, so the slab reads faster at 1×.
- Size 9 → 9: unchanged.
