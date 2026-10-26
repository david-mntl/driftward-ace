"""Demo game-over screen for the UI Art Critic homework demo.

Draws the game-over screen as one 640x480 picture over the placeholder
background, per `game_over_look` in docs/design/gdd/10-ui.md. Test fixture
only, never shipped.

SEEDED FLAWS (the Director's order for this fixture):
1. The example score is off the top 10, so the message should be GAME OVER
   (no letter picker). The screen says "NEW BEST SCORE!" instead.
2. A chatty line sits 8 px under the message at 18 px, and the score sits
   32 px under that line instead of 32 px under the message.
Round 1 keeps both flaws. Round 2 and later fix them, per
docs/reports/ui-art/demo-gameover-r1.md: the message is GAME OVER as written
(game_over_message, locked), and the chatty line is gone, so the score sits
32 px under the message (game_over_look).

The whole screen is drawn at 4x, then shrunk once, so text and the arrow get
smooth edges and exact spacing (GDD 12 art_style).

Usage: python3 tools/art/demo_gameover.py [round]      (round defaults to 1)
Writes staging/assets/ui/demo-gameover-r<round>.png and ...-board.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = ROOT / "tools" / "art" / "fonts" / "Exo2[wght].ttf"
OUT_DIR = ROOT / "staging" / "assets" / "ui"

# From the GDD: 03-world-and-camera.md (screen), 12 placeholder_bg, 10 game_over_look
SCREEN_W, SCREEN_H = 640, 480
BG = (0, 0, 0)
FONT_WEIGHT = 400                 # Exo 2 Regular
TEXT_COLOR = (226, 232, 242)      # pale silver-white
COBALT = (58, 108, 232)           # selected-item arrow
MSG_SIZE, SCORE_SIZE, ITEM_SIZE = 36, 24, 20
GAP_SCORE = 32                    # score under the message (here: under the chatty line, flaw 2)
GAP_ITEMS = 40                    # RETRY under the score
GAP_ITEM_ITEM = 12                # MENU under RETRY

# Example run: score 1234, off the top 10 (the real message would be GAME OVER)
SCORE = 1234

# SEEDED FLAWS (Director's request for this fixture), used in round 1 only
FLAWED_MESSAGE = "NEW BEST SCORE!"
CHATTY = "Oh no! You got smashed by space rocks! Better luck next time, hero!"
CHATTY_SIZE = 18
GAP_CHATTY = 8

# Round 2 fix: off the top 10 -> GAME OVER, exactly as written (10 game_over_message, locked)
MESSAGE = "GAME OVER"

# STAND-INS: the GDD says only "a small cobalt arrow on its left".
ARROW_H_OF_CAP = 1.0     # arrow height = cap height of the item text (derived from 20 px)
ARROW_W_OF_H = 0.75      # arrow width as a share of its height, stand-in
ARROW_GAP = 8            # px between the arrow and the item text, stand-in

SS = 4  # drawn at 4x, then shrunk


def load_font(size):
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([FONT_WEIGHT])
    return font


def line_metrics(txt, size):
    """At 4x: (font, ink left, ink width, cap top offset, baseline offset) from the draw origin.

    Spacing is measured from a line's baseline to the next line's cap top, so
    descenders in mixed-case text don't shift the stack.
    """
    font = load_font(size * SS)
    l, t, r, b = font.getbbox(txt)
    cap_top = font.getbbox("H")[1]
    baseline = font.getmetrics()[0]
    return font, l, r - l, cap_top, baseline


def draw_screen(flawed):
    W, H = SCREEN_W * SS, SCREEN_H * SS
    big = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(big)

    message = FLAWED_MESSAGE if flawed else MESSAGE
    lines = [(message, MSG_SIZE, 0)]  # (text, size, gap above in px, measured baseline-to-cap-top)
    if flawed:
        lines.append((CHATTY, CHATTY_SIZE, GAP_CHATTY))
    lines += [
        (f"SCORE {SCORE}", SCORE_SIZE, GAP_SCORE),
        ("RETRY", ITEM_SIZE, GAP_ITEMS),
        ("MENU", ITEM_SIZE, GAP_ITEM_ITEM),
    ]
    metrics = [line_metrics(t, s) for t, s, _ in lines]

    # stack height at 4x: first cap top to last baseline
    tops, y = [], 0
    for (txt, size, gap), (font, l, w, cap, base) in zip(lines, metrics):
        y += gap * SS
        tops.append(y)                 # cap top of this line, stack coords
        y += base - cap                # down to its baseline
    stack_h = y
    y0 = (H - stack_h) // 2

    boxes = {}
    for (txt, size, gap), (font, l, w, cap, base), top in zip(lines, metrics, tops):
        x = (W - w) // 2 - l
        yy = y0 + top - cap
        d.text((x, yy), txt, font=font, fill=TEXT_COLOR)
        boxes[txt] = ((W - w) // 2, y0 + top, (W - w) // 2 + w, y0 + top + base - cap)

    # cobalt arrow left of RETRY (selected), centered on its cap height
    rl, rt, rr, rb = boxes["RETRY"]
    ah = (rb - rt) * ARROW_H_OF_CAP
    aw = ah * ARROW_W_OF_H
    ax1 = rl - ARROW_GAP * SS
    ax0 = ax1 - aw
    cy = (rt + rb) / 2
    d.polygon([(ax0, cy - ah / 2), (ax1, cy), (ax0, cy + ah / 2)], fill=COBALT)

    screen = big.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
    # blocks in 1x px for the board zooms
    def to1(b, pad=6):
        return (max(0, b[0] // SS - pad), max(0, b[1] // SS - pad),
                min(SCREEN_W, -(-b[2] // SS) + pad), min(SCREEN_H, -(-b[3] // SS) + pad))
    top_lines = [boxes[t] for t, _, _ in lines[:-2]]  # message (+ chatty) + score
    msg_block = to1((min(b[0] for b in top_lines), boxes[message][1],
                     max(b[2] for b in top_lines), boxes[f"SCORE {SCORE}"][3]))
    menu_block = to1((int(ax0), boxes["RETRY"][1],
                      max(boxes["RETRY"][2], boxes["MENU"][2]), boxes["MENU"][3]))
    return screen, msg_block, menu_block


def zoom(img, box, k=4):
    crop = img.crop(box)
    return crop.resize((crop.width * k, crop.height * k), Image.NEAREST)


def draw_board(screen, msg_box, menu_box):
    """1x screen on the dark background, plus 4x zooms of the message block and the RETRY/MENU block."""
    zm, zi = zoom(screen, msg_box), zoom(screen, menu_box)
    pad, cap_h = 24, 22
    row1_h = max(SCREEN_H, zi.height)
    bw = pad + max(SCREEN_W + pad + zi.width, zm.width) + pad
    bh = pad + cap_h + row1_h + pad + cap_h + zm.height + pad
    board = Image.new("RGB", (bw, bh), (14, 14, 18))
    d = ImageDraw.Draw(board)
    cap_font = load_font(14)
    cap_col = (140, 146, 158)
    frame = (60, 64, 74)

    def place(im, x, y, caption):
        d.text((x, y - cap_h), caption, font=cap_font, fill=cap_col)
        board.paste(im, (x, y))
        d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=frame)

    def span(b):
        return f"{b[0]},{b[1]} to {b[2]},{b[3]}"

    top = pad + cap_h
    place(screen, pad, top, f"1x, {SCREEN_W}x{SCREEN_H}")
    place(zi, pad + SCREEN_W + pad, top, f"4x, RETRY/MENU block ({span(menu_box)})")
    place(zm, pad, top + row1_h + pad + cap_h, f"4x, message block ({span(msg_box)})")
    return board


def main():
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    screen, msg_box, menu_box = draw_screen(flawed=(rnd == 1))
    screen.save(OUT_DIR / f"demo-gameover-r{rnd}.png")
    draw_board(screen, msg_box, menu_box).save(OUT_DIR / f"demo-gameover-r{rnd}-board.png")
    print("wrote", OUT_DIR / f"demo-gameover-r{rnd}.png")


if __name__ == "__main__":
    main()
