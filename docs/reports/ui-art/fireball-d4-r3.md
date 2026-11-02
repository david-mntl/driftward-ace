Score: 8.2 | Lowest: 8 | Size: 9

Asset: fireball-d4
Kind: sprite
Round: 3
Image: staging/assets/sprites/fireball-d4-r3.png
Board: staging/assets/sprites/fireball-d4-r3-board.png
Measured: 64 × 64 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md (shared hazard rules, not reopened this round)

Direction for this design (from the brief): dying star, with a corona around the head and a streaming trail.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The 64 × 64 canvas matches `art_canvas` (a `guess`). The head sits at the lower right of the canvas, flying down-right, and fills the head circle of radius 16 on the board. The tail circle (radius 8, up-left of the head) now lies on bright orange and yellow fire plus one lit ember, so the hit area matches what the player sees (rule 8). This fixes the round 2 gap, where its upper-left part sat on the dim end of the trail. Head position and tail coverage are read from the board, not measured. |
| 2 | World fit | 8 | A burning ball with a warm halo and a long glowing trail toward the top-left reads as a dying star dragged in ("Stars die and are dragged in, still burning"), and it follows the direction. The corona is clear. The trail is still one straight, even stream with no curl or break, so "streaming" is partly there. The embers along it are evenly spaced and look a little like beads on a line. |
| 3 | Colors | 8 | Heat colors only: pale yellow core, orange body, red-orange edge, trail yellow to orange. This follows "Orange and yellow mean heat, danger". The trail stays yellow farther back and no longer turns grey-brown, which fixes round 2. Gradients are smooth and vivid. Fuchsia is a thin line on the head's lower right only, so rule 6 holds. The far end still fades quickly into navy. |
| 4 | Light & glow | 8 | A hard white highlight sits at the head's upper left ("Highlights are hard and white"). The thin fuchsia rim runs along the lower-right edge, toward the black hole (rule 8), and is easy to see. A soft warm glow surrounds the head and trail, as `glow` asks for hazards. The highlight is small, a short slash; it could be a little bigger. |
| 5 | Readability & finish | 8 | The head and trail read clearly at 1× on the dark and the painting backgrounds (Pillar 2). The hard square specks beside the trail are gone, replaced by round, soft embers. The head's outline looks clean at 1×. At 4× the head edge and trail edges still show faint stair steps. The trail's embers are slightly lumpy where they overlap the trail body. |

## Fix first
- Light & glow (and World fit): make the white highlight a little larger, and give the trail one gentle bend or a slight uneven width so it streams instead of running as a straight, even band.
- Colors, Readability & finish: smooth the stair steps on the head edge and trail edges at 4×, and vary the ember size and spacing so they stop reading as beads on a line.

## Since round 2
- Size 8 → 9: the tail circle now lies on bright fire, not on the dim end of the trail.
- World fit 8 → 8: no change. The trail is still straight and even.
- Colors 8 → 8: no change. The grey-brown far end is fixed, but the fade into navy is still quick.
- Light & glow 8 → 8: no change.
- Readability & finish 7 → 8: the square specks are replaced by soft round embers, and the trail's edges are smoother. Small stair steps remain at 4×.
