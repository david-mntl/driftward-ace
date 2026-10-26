"""Demo HUD picture (ui-art-loop, rounds 1 and 2) for the Step 6 homework demo.

Draws the in-run HUD as one 640x480 picture over the placeholder background,
in the layout of the sketch in docs/design/gdd/10-ui.md. Test fixture only,
never shipped.

Round 1 has the SEEDED FLAW (the Director's order for this fixture): the lives
icons are small ship silhouettes filled solid bright fuchsia, not hearts.
Round 2 (refine, per docs/reports/ui-art/demo-hud-r1.md) draws hearts in cobalt
blue instead, and sets the text at 4x then shrinks it, with explicit word gaps.

Usage: python3 tools/art/demo_hud.py [round]      (round defaults to 1)
Writes staging/assets/ui/demo-hud-r<round>.png and ...-board.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = ROOT / "tools" / "art" / "fonts" / "Exo2[wght].ttf"
OUT_DIR = ROOT / "staging" / "assets" / "ui"

# From the GDD (03-world-and-camera.md, 05-lives-and-damage.md, 12 placeholder_bg)
SCREEN_W, SCREEN_H = 640, 480
BG = (0, 0, 0)
LIVES = 3
SCORE, LEVEL, GRAZES = 1234, 2, 5

# STAND-INS (GDD values TBD: UI-01 for size/colors/margins, palette for exact RGB)
FONT_SIZE = 20            # stand-in for UI-01
FONT_WEIGHT = 400         # Exo 2 Regular, stand-in for UI-01
TEXT_COLOR = (226, 232, 242)   # pale silver-white, stand-in for UI-01 / palette
MARGIN = 12               # px from the left, top and right edges, stand-in for UI-01
GAP_LV_GRAZE = 24         # px between "LV 2" and "GRAZE 5", stand-in for UI-01
ICON_W, ICON_H = 20, 22   # lives icon size, stand-in for UI-01
ICON_GAP = 8              # px between lives icons, stand-in for UI-01
FUCHSIA = (255, 0, 204)   # SEEDED FLAW color, stand-in for the palette's fuchsia

COBALT = (58, 108, 232)        # round 2 heart fill: "you, untouched" blue (GDD 12 color language), stand-in RGB
HEART_EDGE = (214, 224, 240)   # round 2 heart outline: pale plating, stand-in RGB
WORD_GAP = 7                   # px between a label and its value in round 2, stand-in for UI-01

SS = 4  # icons are drawn at 4x, then shrunk (GDD 12 art_style)


def load_font(size):
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([FONT_WEIGHT])
    return font


def ship_icon():
    """Small ship silhouette, solid fuchsia (the seeded flaw), drawn at 4x then shrunk."""
    w, h = ICON_W * SS, ICON_H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # nose up, swept wings, notched tail; coordinates as fractions of the icon box
    pts = [(0.50, 0.00), (0.62, 0.30), (0.62, 0.50), (1.00, 0.80), (1.00, 1.00),
           (0.66, 0.90), (0.50, 0.96), (0.34, 0.90), (0.00, 1.00), (0.00, 0.80),
           (0.38, 0.50), (0.38, 0.30)]
    d.polygon([(x * (w - 1), y * (h - 1)) for x, y in pts], fill=FUCHSIA + (255,))
    return img.resize((ICON_W, ICON_H), Image.LANCZOS)


def heart_icon():
    """Flat heart, cobalt fill with a thin pale edge, drawn at 4x then shrunk."""
    import math
    w, h = ICON_W * SS, ICON_H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(200):  # classic heart curve
        t = 2 * math.pi * i / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x, -y))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 2 * SS
    sx = (w - 2 * pad) / (max(xs) - min(xs))
    sy = (h - 2 * pad) / (max(ys) - min(ys))
    k = min(sx, sy)
    ox = w / 2 - k * (max(xs) + min(xs)) / 2
    oy = h / 2 - k * (max(ys) + min(ys)) / 2
    poly = [(ox + k * x, oy + k * y) for x, y in pts]
    d.polygon(poly, fill=HEART_EDGE + (255,))
    # inner fill: same shape shrunk toward its center
    cx, cy = w / 2, h / 2
    inner = [(cx + (x - cx) * 0.78, cy + (y - cy) * 0.78) for x, y in poly]
    d.polygon(inner, fill=COBALT + (255,))
    return img.resize((ICON_W, ICON_H), Image.LANCZOS)


def text_img(txt, size, color):
    """Text drawn at 4x and shrunk, so spacing is even (no hinting snaps). Returns RGBA."""
    font = load_font(size * SS)
    l, t, r, b = font.getbbox(txt)
    asc, desc = font.getmetrics()
    w, h = r + SS * 2, asc + desc
    big = Image.new("RGBA", (w, h), color + (0,))
    ImageDraw.Draw(big).text((0, 0), txt, font=font, fill=color + (255,))
    w4, h4 = -(-w // SS) * SS, -(-h // SS) * SS
    pad = Image.new("RGBA", (w4, h4), color + (0,))
    pad.paste(big, (0, 0))
    return pad.resize((w4 // SS, h4 // SS), Image.LANCZOS)


def draw_hud_r2():
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), BG)
    line_h = text_img("SCORE", FONT_SIZE, TEXT_COLOR).height

    def put(txt, x, y):
        im = text_img(txt, FONT_SIZE, TEXT_COLOR)
        img.paste(im, (x, y), im)
        return x + im.width

    # row 1: SCORE and its value, top-left, with a clear gap
    x = put("SCORE", MARGIN, MARGIN) + WORD_GAP
    put(str(SCORE), x, MARGIN)
    # row 2: LV and GRAZE, below the score; labels and values each get the same gap
    y2 = MARGIN + line_h
    x = put("LV", MARGIN, y2) + WORD_GAP
    x = put(str(LEVEL), x, y2) + GAP_LV_GRAZE
    x = put("GRAZE", x, y2) + WORD_GAP
    put(str(GRAZES), x, y2)
    # lives: hearts, top-right, centered on row 1
    icon = heart_icon()
    total_w = LIVES * ICON_W + (LIVES - 1) * ICON_GAP
    x = SCREEN_W - MARGIN - total_w
    y = MARGIN + (line_h - ICON_H) // 2
    for _ in range(LIVES):
        img.paste(icon, (x, y), icon)
        x += ICON_W + ICON_GAP
    return img


def draw_hud():
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), BG)
    d = ImageDraw.Draw(img)
    font = load_font(FONT_SIZE)
    asc, desc = font.getmetrics()
    line_h = asc + desc

    # row 1: SCORE, top-left
    d.text((MARGIN, MARGIN), f"SCORE {SCORE}", font=font, fill=TEXT_COLOR)
    # row 2: LV and GRAZE, below the score
    y2 = MARGIN + line_h
    lv = f"LV {LEVEL}"
    d.text((MARGIN, y2), lv, font=font, fill=TEXT_COLOR)
    x_graze = MARGIN + round(font.getlength(lv)) + GAP_LV_GRAZE
    d.text((x_graze, y2), f"GRAZE {GRAZES}", font=font, fill=TEXT_COLOR)

    # lives, top-right, vertically centered on row 1
    icon = ship_icon()
    total_w = LIVES * ICON_W + (LIVES - 1) * ICON_GAP
    x = SCREEN_W - MARGIN - total_w
    y = MARGIN + (line_h - ICON_H) // 2
    for _ in range(LIVES):
        img.paste(icon, (x, y), icon)
        x += ICON_W + ICON_GAP
    return img


def zoom(img, box, k=4):
    crop = img.crop(box)
    return crop.resize((crop.width * k, crop.height * k), Image.NEAREST)


def draw_board(hud):
    """1x HUD on the dark background, plus 4x zooms of the top-left and top-right areas."""
    zl_box = (0, 0, 200, 64)
    zr_box = (SCREEN_W - 140, 0, SCREEN_W, 64)
    zl, zr = zoom(hud, zl_box), zoom(hud, zr_box)
    pad, cap_h = 24, 22
    bw = pad + SCREEN_W + pad + zl.width + pad
    bh = pad + cap_h + max(SCREEN_H, zl.height + pad + cap_h + zr.height) + pad
    board = Image.new("RGB", (bw, bh), (14, 14, 18))
    d = ImageDraw.Draw(board)
    cap_font = load_font(14)
    cap_col = (140, 146, 158)
    frame = (60, 64, 74)

    def place(im, x, y, caption):
        d.text((x, y - cap_h), caption, font=cap_font, fill=cap_col)
        board.paste(im, (x, y))
        d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=frame)

    top = pad + cap_h
    place(hud, pad, top, f"1x, {SCREEN_W}x{SCREEN_H}")
    x2 = pad + SCREEN_W + pad
    place(zl, x2, top, "4x, top-left (0,0 to 200,64)")
    place(zr, x2, top + zl.height + pad + cap_h, "4x, top-right (500,0 to 640,64)")
    return board


def main():
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    hud = draw_hud_r2() if rnd >= 2 else draw_hud()
    hud.save(OUT_DIR / f"demo-hud-r{rnd}.png")
    draw_board(hud).save(OUT_DIR / f"demo-hud-r{rnd}-board.png")
    print("wrote", OUT_DIR / f"demo-hud-r{rnd}.png")


if __name__ == "__main__":
    main()
