Score: 7.2 | Lowest: 7 | Size: 8

Asset: satellite-drifter-a
Kind: sprite
Round: 3
Image: staging/assets/sprites/satellite-drifter-a-r3.png
Board: staging/assets/sprites/satellite-drifter-a-r3-board.png
Measured: 180 × 12 px, 5 frames of 36 × 12 px
GDD: 12-art-and-audio.md, drifters/02-satellite.md, 07-drifters.md
Previous report: docs/reports/ui-art/satellite-drifter-a-r2.md

## Documentation differences (read first)
- The gap flagged in rounds 1 and 2 is closed. `drifters/02-satellite.md` `look_reference` now says "torn panel edges, a scorched, cracked body" and "Thin fuchsia magnetism rays glow on it and move with the panel swing". I scored the damage look and the rays against that line. Nothing left to change.
- One thing to check, not a conflict: `look_reference` says the rays "move with the panel swing". Rule 13 in `12-art-and-audio.md` says the light and rim stay fixed while a shape turns. I read the rays as part of the swing (they may move) and the bottom rim as fixed. If the Director means something else, the GDD should say so.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | Each frame is 36 × 12, equal to the `size` guess in `drifters/02-satellite.md`. All 5 frames are the same size in one strip (12-art rule 13). The 12 × 12 body is centred and fills the frame height. The green overlay on the board shows the body box and the 36 × 6 bar both centred. At ±25° (frames 1 and 5) the outer panel ends tilt away from the flat bar, so the bar's far corners are still not fully covered by drawn panel. Rule 8 allows the flat bar, but the player sees a little less than the bar at those ends. I can't confirm from the board whether any edge row is clipped. |
| 2 | World fit | 7 | The glossy white body with a hard highlight and the ragged, speckled panel edges fit "Metal ships and satellites drift dead, or worse, half alive" (world brief). The body still reads as powered. The damage `look_reference` asks for is only partly there: the panel edges are torn, but at 1× I can't see a clear crack or scorch mark on the body, and no panel is clearly snapped. It reads as worn, not wrecked. The antenna nubs on top still give a bug-like face. |
| 3 | Colors | 7 | Panels are cobalt blue with lighter highlights and fuchsia stays an accent, so nothing reads as a coin (12-art rule 6). The white body is clean. The panel fill is still mottled: blue and pink pixels mix in blocks on all 5 frames at 4× zoom, which looks noisy, not clean and well defined. The body's pink-purple centre is the strongest fuchsia on the sprite and stays small enough. |
| 4 | Light & glow | 7 | Better than round 2. Thin fuchsia streaks now come off the body and the panel tips, as the rays in `look_reference` ask, and they shift between frames with the swing. The bottom-side rim is still there and fixed (rule 8, rule 13). At 1× on the navy field the rays read as small pink ticks around the tips, not as clear lines off the body. They are easy to lose, and part of them blends into the pink speckle on the panels. The glow suits a hazard (12-art `glow`). |
| 5 | Readability & finish | 7 | At 1× on the navy starfield (bottom of the board) the sprite reads as a small winged object. The white body stands out. The swing shows: ±25° is above the 20° floor (rule 13), and frames 1 and 5 are clearly different from frame 3. The loop 1,2,3,4,5,4,3,2 is smooth. The finish is still noisy: the pixel mix on the panels makes the edges look rough instead of the smooth, glossy edge `art_style` asks for. The 2× smooth view is cleaner than the 4× view. |

## Fix first
- Colors and Readability & finish (the same cause): clean the panel fill. Make each panel one smooth blue gradient with a hard white highlight line. Put fuchsia only on the bottom rim and the rays, not mixed through the blue.
- Light & glow: make the rays stand apart from the panels. Draw a few thin, longer fuchsia lines from the body so they read at 1× and don't blend into the panel speckle.
- Optional, for World fit: add one clear sign of damage on the body (a crack or a scorch) and one visibly broken panel edge.

## Since round 2
- Light & glow 6 → 7: thin fuchsia rays now come off the body and panel tips and move with the swing. They are still small at 1×.
- World fit 7 → 7: unchanged. The damage look is still only hinted.
- Colors 7 → 7: unchanged. The panel fill is still mottled.
- Readability & finish 7 → 7: unchanged. The swing and loop read well. The edge noise remains.
- Size 8 → 8: unchanged. The tilted ends versus the flat bar gap is still there.
