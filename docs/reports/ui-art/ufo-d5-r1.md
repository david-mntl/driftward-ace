Score: 7.2 | Lowest: 7 | Size: 8

Asset: ufo-d5
Kind: sprite
Round: 1
Image: staging/assets/sprites/ufo-d5-r1.png
Board: staging/assets/sprites/ufo-d5-r1-board.png
Measured: 40 × 20 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/07-ufo.md, 07-drifters.md (not needed beyond the spec; entry warning is not part of this still)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 40 × 20 matches `art_canvas`. On the board's hitbox view the disc fills the 40 × 10 box in the bottom half, so it covers the disc hitbox. The dome sits centered on the disc's top edge but is only about 6 rows tall and about 14 px wide. The dome hitbox circle (radius 9, `guess`) reaches well above it, so the circle is bigger than the drawn dome. The direction asks for a "small" dome, so this is a mild gap. The ends of the disc taper, which leaves small empty corners inside the box. |
| 2 | World fit | 7 | Heavy thick disc with panel seams, vents and a row of underside lights fits the "metal ships drift dead, or worse, half alive" brief and the "heavy" direction. The green dome reads as "saucer with a green dome, no beam" (`look_reference`). The master (shown at 1/2) has hard white highlights on the dome and the hull, as "The light" asks. At 1× the panel detail turns into grey noise, so the heavy look is less crisp than the master promises. |
| 3 | Colors | 7 | Lights are orange, yellow and white, never cobalt, as the direction asks. The dome is a clean, vivid green and the hull is mid grey with navy shadows. Watch-outs: the orange lights and the orange edge glow along the top of the disc in the master sit on the "orange and yellow = heat, danger" meaning and could read as a fireball cue. The hull grey is slightly flat and close to the navy at the left and right ends. |
| 4 | Light & glow | 7 | A fuchsia rim runs along the bottom of the disc in the master and shows as a pink line on the 1× views, which matches rule 8 (bottom side, thin). It stays thin, so rule 6 (coins own solid fuchsia) holds. A hazard may glow, and the warm halo around the hull helps it stand out. The halo is strongest on the upper edge in the master, and rim and glow are on opposite sides. That blurs which side faces the black hole. Keep the warm glow subtle or move it to the underside. |
| 5 | Readability & finish | 7 | The green dome and the lit underside make the shape readable at 1× on both the navy and the purple glow, and the pale hull outline separates it from black. The disc's panel texture is busy at 1×: the 4× view shows blocky mottling and uneven edge pixels along the top of the hull. The dome's edge against the disc has a soft, slightly jagged step. A smoother, simpler hull gradient with fewer small panels would read cleaner at game size. |

## Fix first
- Size: enlarge the dome toward the radius-9 hitbox circle (a few more rows and px wide), still centered on the disc's top edge, and fill the tapered disc ends so the hull covers the 40 × 10 box.
- Colors, light and finish (tied at 7): cut the hull panel detail to bolder, larger seams so it holds at 1×, and keep the orange to the small lights only. Move or soften the warm halo on the upper edge so the fuchsia rim on the bottom is the one clear edge light.
