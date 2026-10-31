Score: 7.0 | Lowest: 6 | Size: 8

Asset: satellite-drifter-a
Kind: sprite
Round: 2
Image: staging/assets/sprites/satellite-drifter-a-r2.png
Board: staging/assets/sprites/satellite-drifter-a-r2-board.png
Measured: 180 × 12 px, 5 frames of 36 × 12 px
GDD: 12-art-and-audio.md, drifters/02-satellite.md, 07-drifters.md
Previous report: docs/reports/ui-art/satellite-drifter-a-r1.md

## Documentation differences (read first)
- Round 1 flagged the panel swing against rule 13 and rule 8. Both are now covered: `12-art-and-audio.md` rule 13 has the "part that swings on a fixed body" exception, and `drifters/02-satellite.md` rule 8 states the 25° swing and the flat hitbox bar. Nothing left there.
- Still open from round 1: `drifters/02-satellite.md` `look_reference` says only "White body with blue solar panels on both sides". The brief adds "looks destroyed but still able to fly" and "glowing fuchsia magnetism rays on the body". The spec has no line for either. I judged against the brief and the color language. Proposed change, pending Director approval: extend `look_reference` (or add a `look_notes` line) in `drifters/02-satellite.md` with the damage look and the ray look, so the next judge has a GDD rule to score against. This does not change any score below.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | Each frame is 36 × 12, equal to the `size` guess in `drifters/02-satellite.md`. All 5 frames are the same size in one strip (12-art rule 13). The 12 × 12 body sits in the centre and fills the frame height. The green hitbox overlay on the board shows the body box and the 36 × 6 bar both centred. At ±25° (frames 1 and 5) the outer panel ends tilt away from the flat 36 × 6 bar, so the bar's far corners are not covered by drawn panel. Rule 8 allows the flat bar, but the player sees less than the bar at those ends. Panel tips seem to stay inside the frame; I can't confirm from the board whether any row is clipped. |
| 2 | World fit | 7 | The glossy white body with a hard highlight, and the jagged speckled panel edges, fit "Metal ships and satellites drift dead, or worse, half alive" and "The light" (12-art world brief). The body reads as still powered, as the brief asks. "Destroyed" is only hinted: the panel edges are ragged, but at 1× on the navy field there is no clear snapped panel, hole or missing piece. It reads as a worn satellite, not a wreck. The two small antenna nubs on top of the body give it a bug-like face; that fits "mutated" but muddies the satellite silhouette a little. |
| 3 | Colors | 7 | Big improvement: the panels are now mostly cobalt blue with lighter blue highlights, as `look_reference` says. Fuchsia is limited to speckles along the bottom of the panels and the body centre, so it stays a thin accent (12-art rule 6) and nothing reads as a coin. The white body is clean. The panels are mottled: blue and pink pixels are mixed in a noisy pattern on frames 1 to 5 of the 4× board, which looks slightly muddy rather than a clean, well-defined fill. The body's centre is a pink-purple blob that is the strongest fuchsia on the sprite; keep it small. |
| 4 | Light & glow | 6 | A fuchsia rim runs along the lower edge of the panels and body, on the bottom side as rule 8 asks, and it stays fixed in all 5 frames while the panels swing (rule 13). The brief asks for glowing magnetism rays on the body. At 1× I can't pick out separate rays: the body shows a pink glow centre and pink specks, but no thin ray lines coming off it. Hazards may glow (12-art `glow`), so this object is allowed more glow; right now the glow is the weakest part of the sprite and reads as speckle, not as rays. |
| 5 | Readability & finish | 7 | On the navy starfield at 1× (bottom of the board) the sprite reads clearly as a small winged object, and the white body stays bright against navy, which fixes the sinking body from round 1. The swing shows: ±25° is above the 20° floor in rule 13, and frames 1 and 5 look clearly different from frame 3. The loop 1,2,3,4,5,4,3,2 is smooth. Finish is noisy: the blue and pink pixel mix on the panels makes the edges look rough instead of the smooth, glossy edge `art_style` asks for. The 2× smooth view looks cleaner than the 4× zoom. |

## Fix first
- Light & glow: draw the magnetism rays as a few thin, separate fuchsia lines from the body, in the same place in all 5 frames. Keep the bottom-side rim as is.
- Readability & finish (also lifts Colors): clean the panel fill. Make each panel a smooth blue gradient with a hard white highlight line, and keep fuchsia only on the bottom rim and the rays instead of mixed through the blue. Check that the tilted panel ends at ±25° cover the ends of the 36 × 6 bar.

## Since round 1
- World fit 6 → 7: the panels are no longer whole and shiny; the ragged edges hint at damage. It is still not clearly "destroyed".
- Colors 5 → 7: the fuchsia wash is gone from the panels, and they read blue as `look_reference` says. The mottled mix keeps it from going higher.
- Light & glow 5 → 6: the rim now sits on the bottom side. Separate rays are still missing.
- Readability & finish 6 → 7: the white body now stands out from the navy, and the swing and loop read well. Edge noise remains.
- Size 8 → 8: unchanged. The tilted-panel versus flat-bar gap at the ends is still there.
