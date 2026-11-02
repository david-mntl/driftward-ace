Score: 7.6 | Lowest: 7 | Size: 9

Asset: coin-d4
Kind: sprite
Round: 2
Image: staging/assets/sprites/coin-d4-r2.png
Board: staging/assets/sprites/coin-d4-r2-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md, 07-drifters.md (not needed beyond the coin spec), previous report docs/reports/ui-art/coin-d4-r1.md
Direction for this design: clean prism with flat facets and a ring of tiny bright specks.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The strip is 48 × 24 with two 24 × 24 frames, which is the `art_canvas` (`guess`). The prism stands upright in the middle of each frame and the dark panel fills the 12 × 10 hitbox box drawn on the board, so the ship must really touch the crystal (`hitbox`, `guess`). The ring of specks crosses the crystal's middle as `art_canvas` asks. I can't confirm exact crystal and ring pixel sizes by eye; the score rests on the frame numbers you gave. |
| 2 | World fit | 7 | Better than round 1. On the 8× master a clear pink spiral with a near-black core now sits in a dark panel, so "a tiny swirling galaxy" (`look_reference`) reads, and the purple haze around the crystal gives a cloud feel. Two gaps remain. The crystal body still looks solid, not "transparent", and the cloud is only outside the prism, not inside the square (`art_canvas`). At the 4× zoom the spiral shrinks to a pink blob, so the galaxy idea only shows on the master. |
| 3 | Colors | 8 | Crimson and hot pink on the lit left facets, black-purple on the right shade side, near-black core and bright red-pink ring all follow the coin `palette`. The dark panel gives the one deep value, so the pink spiral pops. It owns solid fuchsia as coins should (rule 6) and stays apart from hazard orange and electric cyan. The lit facets still lean slightly toward light pink-magenta, not the crimson (200, 30, 90) in the spec, but it is vivid and clean, not muddy. |
| 4 | Light & glow | 7 | A coin must glow (GDD 12 `glow`). The 8× master has a soft violet-pink halo around the prism and a bright lower edge along the bottom facets, so the rim leans toward the black hole side (rule 8). The rare one shines more: a big white-pink star glint at the upper left plus two small sparkles (`palette` rare glint, "the rare one shines more"). At 1× the rare's upper-left glint now shows, so common and rare differ. The halo is still very faint at 1× on the navy, so the common coin glows less than a coin should at game size. |
| 5 | Readability & finish | 7 | At 1× on the board it reads as a small pink gem with dots either side, and it stands out from the navy background (rule 2). The ring specks stay separate dots on the 4× zoom, which fixes the round 1 merge. The facet edges are cleaner on the master. At the 4× zoom the shrink is soft: the inner spiral is a mushy pink patch and the facet lines blur together, so the "flat facets" direction is weaker at game size than on the master. |

## Fix first
- Light & glow: strengthen the halo at 24 × 24 so the common coin reads as glowing at 1×, not only on the 8× master.
- Readability & finish: keep the spiral and the facet lines wide enough to survive the shrink (one clear arm and a darker panel edge), so the 4× zoom shows more than a pink patch. Add a hint of cloud inside the square if room allows.

## Since round 1
- World fit 6 to 7: the spiral now reads on the master, with a near-black core and a haze around the crystal. The crystal is still opaque and the cloud is not inside the square.
- Colors 7 to 8: the deep dark panel makes the pink pop and the palette is followed closely.
- Light & glow 7 to 7: the rare's glint now reads at 1×, but the common's halo is still faint at 1× and the rim is only mildly stronger at the bottom.
- Readability & finish 6 to 7: the ring specks stay apart after the shrink; the spiral and facets still go soft.
- Size 9 to 9: no change.
