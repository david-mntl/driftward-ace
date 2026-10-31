Score: 7.4 | Lowest: 7 | Size: 9

Asset: floating-island-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/floating-island-d2-r1.png
Board: staging/assets/sprites/floating-island-d2-r1-board.png
Measured: 320 × 120 px, no frames
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md, 07-drifters.md
Direction: design 2, crystal meadow (green grass ground, a few small dim purple crystals as thin accents).

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches the rectangle variant and `art_canvas` (`guess`). The ground fills the whole box and the board's hitbox outline sits on the image edge with no transparent margin, so the ship stops where the ground is drawn (rule 10 of the spec). Not 10 because the fuchsia line along the bottom is part of the box; check it does not read as a gap in the ground. |
| 2 | World fit | 7 | Meadow on top, darker soil with pebbles and thin strata lines below. It reads as a chunk of planet ground, which fits "planets crack into floating islands". The crystals tie it to the new-universe look. It looks like a flat tile of land, though. Nothing says "floating" or "touched by the anomaly" beyond the bottom line, and the finish is soft and matte, not "glossy and wet" (world brief, The light). |
| 3 | Colors | 7 | Green ground with a darker edge follows `look_reference`. The soil's mid-green and the grass's light green are clean and separate. The crystals are violet, not fuchsia, so rule 6 (coins own solid fuchsia) holds. They are more saturated and brighter than "dim" in the direction, so they pull the eye and sit close to coin territory. Tone them down a step. |
| 4 | Light & glow | 7 | A thin fuchsia rim runs along the bottom edge, on the side facing the black hole (rule 8). It is thin and does not glow like a hazard, which suits a blocker. The crystals have hard white tips and a lit left face, matching "highlights are hard and white". The top edge has a light line and the grass is brightest at the top, but there is no matching bright highlight on the ground's own edge. |
| 5 | Readability & finish | 7 | Clear at 1× on the board: a green slab against navy is easy to tell from any hazard, and the dark border marks the hitbox. The grass is a busy streaky texture, and the six crystal clusters shrink to a few violet ticks at 1×. They stay small and spaced out, as a thin accent should. Edges are smooth and the grass tufts overlap the crystal bases cleanly. The strata lines and pebbles in the soil are fine and low contrast, so the bottom half looks flat. |

## Fix first
- Colors: dim the crystals (lower brightness and saturation of the violet body) so they stay a thin accent and never compete with a coin's fuchsia.
- World fit: give the ground a slightly glossier look (a hard highlight along the top ground edge and the crystal faces, deeper navy-leaning shadow in the soil) so it matches "glossy and wet" and sits in the one-world look.
