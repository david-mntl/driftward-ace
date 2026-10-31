Score: 7.8 | Lowest: 7 | Size: 9

Asset: meteorite-d1
Kind: sprite
Round: 3
Image: staging/assets/sprites/meteorite-d1-r3.png
Board: staging/assets/sprites/meteorite-d1-r3-board.png
Measured: 28 × 28 px, no frames (one still)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md (07-drifters.md not re-read; only the 01 and 12 rules were checked)

Direction followed: dark basalt, blocky and angular, near-black with deep cracks, hard white highlights on the up-right edges.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (`guess`). On the board the rock fills the hitbox circle (radius 14, `guess`) and stays inside it, so the hitbox never exceeds what the player sees (07-drifters rule 8). Coverage is near full; the outline is still a round polygon with tiny gaps against the circle at the top-left. |
| 2 | World fit | 7 | A plain rock, no tail, no glow, as `look_reference` asks. The hard white edge top-right and the deep crack fit "The light". But the body is now a light lilac with a smooth round outline, so on the board it reads closer to a small violet planet or orb than to a "blocky, angular, near-black" basalt rock (the design direction). The crack is still the one clear rock detail; the silhouette has little angularity. |
| 3 | Colors | 8 | The mid-tones moved toward violet as asked in r2 and the body is now clean and vivid ("more vivid than they should be", GDD 12 light). It separates well from the navy backdrop. No heat colors, correct for a plain rock. Cost: the body is now much lighter than "near-black", so the basalt direction is weakened. The crack and the left shadow side are still deep navy-violet, which keeps some contrast. |
| 4 | Light & glow | 7 | Hard white highlight on the up-right edge, no glow (correct for the meteorite). The fuchsia rim sits on the bottom side facing the black hole (rule 8). On the board it still reads as a fairly thick, bright band across the bottom; rule 6 allows fuchsia on a hazard only as a thin accent, and a bright solid band edges toward the coin look. A thin white ring also seems to wrap past the up-right edge toward the top-left, so the highlight is less one-sided than the direction asks. The edge steps are softer than r2 but still show at 4×. |
| 5 | Readability & finish | 8 | At 1× on the dim backdrop the rock reads as a rock with a clear crack, and the lighter body no longer sinks into the navy. The white edge and the bottom rim give a clear silhouette. Finish is clean; slight stair steps remain on the top-right edge on the 4× board. |

## Fix first
- World fit: bring the body back toward near-black basalt and give the outline a few flat, angular cuts, so it reads as a blocky rock and not a round orb. Keep the violet in the mid-tones, only darker.
- Light & glow: thin the fuchsia rim along the bottom and fade it toward both ends (rule 6). Keep the white highlight on the up-right edge only, and smooth its last stair steps.

## Since round 2
- Colors: 7 to 8. Mid-tones are now violet and vivid, and the body separates from the navy.
- World fit: 7 to 7. Unchanged. The lighter, rounder body moved away from the near-black angular direction, which cancelled the gain from the smoother finish.
- Size: 9 to 9. Unchanged.
- Light & glow: 7 to 7. Unchanged. Edge is smoother, but the rim is still thick and the highlight reaches past the up-right.
- Readability & finish: 8 to 8. Unchanged.
