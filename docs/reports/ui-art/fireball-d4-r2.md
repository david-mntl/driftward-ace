Score: 7.8 | Lowest: 7 | Size: 8

Asset: fireball-d4
Kind: sprite
Round: 2
Image: staging/assets/sprites/fireball-d4-r2.png
Board: staging/assets/sprites/fireball-d4-r2-board.png
Measured: 64 × 64 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md

Direction for this design (from the brief): dying star, with a corona around the head and a streaming trail.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The 64 × 64 canvas matches `art_canvas` (a `guess`). On the board the head spans about 32 px and sits at about (44, 44), flying down-right at the 35° angle, so it fills the head circle of radius 16 (`guess`). The tail circle (radius 8, centre about 24 px up-left of the head centre) now sits on visible orange fire along its lower half, which fixes the round 1 gap. Its upper-left part still lies over the faded, dim end of the trail, so a little of the circle is lightly covered (rule 8, never bigger than what the player sees). |
| 2 | World fit | 8 | A burning ball with a soft halo and a long trail toward the top-left reads as a dying star dragged in ("Stars die and are dragged in, still burning"). The beaded ring is gone. A warm halo around the head now gives the corona the direction asks for. The trail is still one straight, even stream with no curl or break, so "streaming" is only partly there. |
| 3 | Colors | 8 | Heat colors only: pale yellow core, orange body, red-orange edge, trail fading from orange to yellow. This follows "Orange and yellow mean heat, danger". Gradients are smooth and vivid, not muddy. The fuchsia is only a thin line on the head's lower right, so rule 6 holds. The far end of the trail loses color toward grey-brown against the navy. |
| 4 | Light & glow | 8 | The hard white highlight is now at the head's upper left ("Highlights are hard and white"). The thin fuchsia rim runs along the lower-right edge, the side toward the black hole, and is easy to see (rule 8). A soft warm glow surrounds the head, so the hazard glows as `glow` asks. The highlight is small and the rim is thin; both could be a little stronger. |
| 5 | Readability & finish | 7 | The head and trail read clearly at 1× on both the dark and the painting backgrounds (Pillar 2), and the trail is much wider than in round 1. Finish still falls short of `art_style`: about four hard square specks remain beside the trail (upper middle of the board at 4×), and they look blocky, not smooth. The trail's edges show stair steps along its length, and the far end fades to a dull tone before the top-left corner. |

## Fix first
- Readability & finish: remove or soften the square specks beside the trail (make them small round, soft-edged embers, or drop them), and smooth the trail's edges where they step.
- Size, Readability & finish: keep the trail's fire brighter farther back, so the tail circle's upper-left part sits on visible orange, and the far end does not turn dull grey-brown.

## Since round 1
- Size 7 → 8: the trail is wider and brighter where the tail circle lies, so the circle is mostly filled with fire.
- World fit 7 → 8: the beaded ring is replaced by a warm halo, so the corona now reads.
- Colors 8 → 8: no change.
- Light & glow 6 → 8: a hard white highlight and a soft glow around the head were added; the fuchsia rim is clearer.
- Readability & finish 6 → 7: the trail is wider and smoother, and the beaded ring is gone, but square specks and stair-stepped trail edges remain.
