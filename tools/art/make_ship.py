"""Draw the player ship sprite: 100x100 RGBA, nose up, flat shapes, hard edges.

Four colors only, no antialiasing, no outline. The left half is drawn,
then mirrored so the ship is exactly symmetric.

Usage: python tools/art/make_ship.py [output_path]
"""
import sys
from PIL import Image, ImageDraw

SIZE = 100
HULL = (0xE8, 0xEE, 0xF5, 255)
ACCENT = (0x3F, 0xA9, 0xF5, 255)
SHADE = (0x5B, 0x6B, 0x80, 255)
COCKPIT = (0xFF, 0xC8, 0x57, 255)


def main(out):
    half = Image.new("RGBA", (SIZE // 2, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(half)
    # Left half only; x=49 is the centre column edge.
    d.polygon([(49, 52), (6, 82), (6, 94), (49, 82)], fill=ACCENT)       # wing
    d.polygon([(49, 66), (14, 88), (14, 94), (49, 88)], fill=SHADE)      # wing underside
    d.rectangle([34, 84, 49, 96], fill=SHADE)                            # engine
    d.polygon([(49, 4), (36, 36), (34, 84), (49, 84)], fill=HULL)        # hull
    d.rectangle([40, 56, 42, 84], fill=ACCENT)                           # hull stripe
    d.polygon([(49, 22), (43, 38), (43, 50), (49, 50)], fill=COCKPIT)    # cockpit
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img.paste(half, (0, 0))
    img.paste(half.transpose(Image.FLIP_LEFT_RIGHT), (SIZE // 2, 0))
    img.save(out, "PNG")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "staging/assets/sprites/ship.png")
