Score: 7.6 | Lowest: 7 | Size: 9

Asset: floating-island-d2
Kind: sprite
Round: 2
Image: staging/assets/sprites/floating-island-d2-r2.png
Board: staging/assets/sprites/floating-island-d2-r2-board.png
Measured: 320 × 120 px, no frames
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md
Direction: design 2, crystal meadow (green grass ground, a few small dim purple crystals as thin accents).
Previous report: docs/reports/ui-art/floating-island-d2-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches the rectangle variant and `art_canvas` (`guess`). The ground fills the whole box, and on the board the hitbox outline sits on the image edge with no transparent margin, so the ship stops where the ground is drawn (spec rule 10). Not 10 because the fuchsia line on the bottom row and the dark green border are part of the box. Both are solid ground, but the border is a little darker than `placeholder_look` and should still read as ground, not a gap. |
| 2 | World fit | 7 | The meadow over a deep teal-navy soil with strata lines reads as a chunk of cracked planet ground ("planets crack into floating islands"). The soil now falls to a navy-leaning teal at the bottom, closer to "shadows go deep navy". The crystals still tie it to the new-universe look. It is still a flat, matte tile. Nothing in the shape says "floating", and the grass is a soft painted texture, not "glossy and wet" (world brief, The light). The pale pebbles in the soil read as water drops or bubbles more than rock. |
| 3 | Colors | 8 | Green ground with a darker edge follows `look_reference` (`guess`). The grass light green, the mid-green band under it and the teal soil are clean and separate, not muddy. The crystals are now a dark, desaturated violet. That matches "few small dim purple crystals", and they stay far from the solid bright fuchsia that coins own (rule 6). Small gap: the crystals are nearly as dark as the soil strata lines, so they lose some of the purple identity at 1×. A touch more violet in the body, still dim, would keep them clearly purple. |
| 4 | Light & glow | 7 | A thin fuchsia rim runs along the bottom edge, the side facing the black hole (rule 8). It is thin, with no hazard glow, which suits a blocker. A pale highlight line now follows the grass edge, which fixes the missing ground-edge highlight from round 1. The crystals carry small pale tips and a lit left face. The highlight line is soft, not the "hard and white" highlight the world brief asks for. The left, right and top borders have no light, so the lighting reads on the grass line only. The crystals no longer glow. |
| 5 | Readability & finish | 7 | At 1× on the board the green slab is easy to tell from every hazard against navy. The dark border marks the hitbox. The six crystal clusters are small and spaced out, so they stay a thin accent. They are now low contrast against the grass, and at 1× they read as dark ticks. The grass is still a busy streaky texture. The pebbles and strata lines in the soil are fine detail that turns into noise at 1×. Edges are smooth, and the tufts overlap the crystal bases cleanly. |

## Fix first
- World fit: add a hard white highlight along the ground edge and the crystal faces, and a glossier, wetter finish on the soil, so it matches "glossy and wet". Make the underside read as a floating chunk, for example with a darker navy base inside the box, without leaving any transparent edge.
- Light & glow: the grass-edge highlight is soft. Make it a thin, hard white line, and give the crystals a clear hard tip so they read as the new-universe accent. Keep them dim.

## Since round 1
- Colors 7 → 8: the crystals are dimmed to a dark, desaturated violet and no longer sit near coin fuchsia. The soil colors are cleaner.
- World fit 7 → 7: the soil is deeper and navy-leaning, but the ground is still flat and matte, with no floating cue.
- Light & glow 7 → 7: a highlight line now runs along the grass edge, but it is soft, and the crystal highlights are weaker.
- Readability & finish 7 → 7: the crystals no longer pull the eye, but they now have low contrast at 1×, and the soil detail is still noisy.
- Size 9 → 9: no change.
