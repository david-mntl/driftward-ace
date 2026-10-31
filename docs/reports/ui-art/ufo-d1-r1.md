Score: 8.0 | Lowest: 7 | Size: 9

Asset: ufo-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/ufo-d1-r1.png
Board: staging/assets/sprites/ufo-d1-r1-board.png
Measured: 40 × 20 px, 1 frame (still image, no animation frames asked for)
GDD: 12-art-and-audio.md, drifters/07-ufo.md (also read for the entry warning: 07-drifters.md is not needed for a still image)

Direction followed: design 1, "classic": silver saucer, green glass dome, a row of small warm lights along the rim, no beam, no cobalt.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The measured 40 × 20 px equals `art_canvas` (`guess`). On the board's hitbox overlay the disc fills the bottom half and spans the full 40 px width, which matches the 40 × 10 disc box. The dome sits centered on the disc's top edge and fills the radius 9 circle, with no part outside it. I judged the overlay by eye only, so the exact row split is not measured. The thin darker belly under the disc is inside the disc box. |
| 2 | World fit | 8 | It reads as a saucer with a green dome (`look_reference`, `guess`). Smooth gradients and a hard white highlight on the dome's upper left fit "The light" and the "smooth and glossy, not pixel art" `art_style`. The silver disc reads as a metal wreck, close to the "half alive" metal drifters. The look is a little plain and friendly, but the brief says never horror. |
| 3 | Colors | 8 | No cobalt anywhere, so the ship's blue stays the ship's. The dome is a vivid, clean green with a lighter top and deeper bottom. The disc is a silver-grey ramp, which matches the placeholder grey. The rim lights are amber. Orange and yellow mean heat and danger in the color language, which fits a hazard, but those lights are small and they don't read as lava or fire. The top face of the disc is a flat mid-grey band and looks a bit dull next to the dome. |
| 4 | Light & glow | 7 | Rule 8 is met: a thin fuchsia rim runs along the bottom of the disc, the side facing the black hole, and it is a thin accent, not a solid fuchsia shape (rule 6). The dome has a hard white highlight. Glow (the `glow` value covers hazards in play) is weak: the dome and the warm lights have no visible soft halo on the navy, so the saucer looks lit by outside light, not glowing. Adding a pre-rendered soft halo around the dome and the lights would meet `glow` better. |
| 5 | Readability & finish | 8 | At 1× on the board the three copies read at once as a green-domed saucer on navy. The green dome is the strongest part. The silver disc has enough contrast against the dark ground. The edges are smooth, and the lights read as a row of small dots. The dark belly under the disc nearly merges with the navy except for the fuchsia line, so the bottom outline depends on that thin line. |

## Fix first
- Light & glow: add a soft pre-rendered glow around the dome and the rim lights so the hazard glows, as `glow` asks. Keep the fuchsia rim thin and on the bottom side.
- Colors: lift the disc's top face from a flat mid-grey into a brighter silver ramp with a hard highlight, so it matches the glossy dome. Keep the lights warm and the palette free of cobalt.
