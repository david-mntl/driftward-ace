"""Demo ship sprite (ui-art-loop round 1) for the UI Art Critic homework demo.

Draws the ship's idle look, one frame, at the ship size in
docs/design/gdd/04-ship.md (ship_w x ship_h), after look_reference there and
the style in docs/design/gdd/12-art-and-audio.md: sharp swept blade wings,
pale plating, cobalt neon lines, glossy finish. Drawn at 4x, then shrunk.
Test fixture only, never shipped.

Round 1 has two SEEDED FLAWS (the Director's order for this fixture):
  1. the engine flame is orange, not blue;
  2. the hull has a thin fuchsia rim along its bottom edge, as if the
     anomaly had touched it.

Round 2 (refine of docs/reports/ui-art/demo-ship-r1.md): blue flame, no
fuchsia anywhere, deep navy shadows, the wings split into long separate
blades, and a forked nose with a glass slot flush to the top edge, so the
hitbox bar's top corners are covered (04-ship.md rule 8).

Usage: python3 tools/art/demo_ship.py [round]      (round defaults to 1)
Writes staging/assets/sprites/demo-ship-r<round>.png and ...-board.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_PATH = ROOT / "tools" / "art" / "fonts" / "Exo2[wght].ttf"
OUT_DIR = ROOT / "staging" / "assets" / "sprites"

# From the GDD: 04-ship.md ship_w, ship_h, hitbox; 12 placeholder_bg
SHIP_W, SHIP_H = 32, 32
BAR_W = 12            # hitbox bar: 12 px wide, ship_h tall, centered
FOOT_H = 12           # hitbox foot: ship_w wide, 12 px tall, along the bottom
GAME_BG = (0, 0, 0)

SS = 4                # drawn at 4x, then shrunk (GDD 12 art_style)
W, H = SHIP_W * SS, SHIP_H * SS

# Palette. GDD 12 gives the color language; exact RGB values are stand-ins.
PLATE_HI = np.array([240, 244, 250], float)   # pale plating, lit
PLATE_MID = np.array([178, 188, 204], float)  # silver-grey
PLATE_LO = np.array([28, 34, 66], float)      # deep navy shadow
COBALT = (36, 84, 236)                        # cobalt neon line
COBALT_CORE = (120, 168, 255)                 # neon line hot core
GLASS_DEEP = np.array([10, 22, 70], float)    # cockpit glass
GLASS_LIT = np.array([54, 112, 230], float)
SEAM = (16, 20, 44)                           # panel seam between blades
FLAME_OUTER = (255, 120, 20)                  # SEEDED FLAW: orange flame
FLAME_CORE = (255, 226, 150)
FUCHSIA_RIM = (255, 40, 200)                  # SEEDED FLAW: rim on the bottom edge
# Round 2: the ship's blue flame (color language row "you, untouched")
FLAME2_OUTER = (28, 70, 230)
FLAME2_MID = (70, 130, 255)
FLAME2_CORE = (190, 214, 255)


def mirror(pts):
    """Right-half outline (x >= 64) mirrored into a full closed polygon."""
    left = [(W - x, y) for x, y in reversed(pts)]
    return pts + left


def poly_mask(pts):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


# Shape, at 4x. The fuselage spans the hitbox bar (x 40..88); the wings fill the
# foot (y 80..128) edge to edge, so the hitbox is never bigger than the look.
FUSELAGE_R = [(64, 0), (76, 10), (88, 22), (88, 128)]


def bezier(p0, p1, p2, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / n for i in range(n + 1))]


# Outer blade: the long swept leading blade, root high on the fuselage. Its
# leading edge curves inward (a scimitar sweep) down to a sharp tip at the corner.
LEAD_EDGE = bezier((88, 20), (98, 62), (128, 80))
BLADE_OUT_R = LEAD_EDGE + [(128, 128), (114, 128), (88, 70)]
# Inner blade: the trailing blade tucked under it.
BLADE_IN_R = [(88, 70), (112, 128), (88, 128)]


def pieces():
    fus = poly_mask(mirror(FUSELAGE_R))
    out_r = poly_mask(BLADE_OUT_R)
    out_l = poly_mask([(W - x, y) for x, y in BLADE_OUT_R])
    in_r = poly_mask(BLADE_IN_R)
    in_l = poly_mask([(W - x, y) for x, y in BLADE_IN_R])
    return [fus, out_r, out_l, in_r, in_l]


def shade(mask, bevel=7.0):
    """Glossy plating for one piece: soft bevel from a blurred mask, lit from the top-left."""
    m = np.asarray(mask, float) / 255.0
    hgt = np.asarray(mask.filter(ImageFilter.GaussianBlur(bevel)), float) / 255.0
    gy, gx = np.gradient(hgt)
    n = np.dstack([-gx * 9, -gy * 9, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    light = np.array([-0.45, -0.80, 0.40])
    light /= np.linalg.norm(light)
    diff = np.clip((n * light).sum(2), 0, 1)
    half = light + np.array([0, 0, 1.0])
    half /= np.linalg.norm(half)
    spec = np.clip((n * half).sum(2), 0, 1) ** 28           # hard white highlight
    # top-to-bottom falloff: light from above, the hull's belly sinks to navy
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    base = PLATE_HI[None, None] * (1 - yy[..., None] * 0.35) + PLATE_MID[None, None] * (yy[..., None] * 0.35)
    # per-piece sheen: bright at the top of the piece, darker toward its tail
    rows = np.where(m.any(1))[0]
    t = np.clip((yy - rows[0] / H) / max(1e-6, (rows[-1] - rows[0]) / H), 0, 1)
    k = (0.22 + 1.05 * diff - 0.22 * t)[..., None].clip(0, 1.1)
    col = PLATE_LO * (1 - k) + base * k
    col = np.clip(col + spec[..., None] * 255, 0, 255)
    return col, m


def draw_line(img, pts, width):
    """Cobalt neon line: a cobalt body with a thinner bright core."""
    d = ImageDraw.Draw(img)
    d.line(pts, fill=COBALT + (255,), width=width, joint="curve")
    d.line(pts, fill=COBALT_CORE + (255,), width=max(1, width // 3), joint="curve")


def render_big():
    rgb = np.zeros((H, W, 3), float)
    alpha = np.zeros((H, W), float)
    masks = pieces()
    for i, mk in enumerate(masks):
        col, m = shade(mk, bevel=6.0 if i == 0 else 5.0)
        rgb = rgb * (1 - m[..., None]) + col * m[..., None]
        alpha = np.maximum(alpha, m)
    img = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)

    # seams between the outer and inner blades, and blade roots at the fuselage
    for sgn in (1, -1):
        def X(x):
            return x if sgn == 1 else W - x
        d.line([(X(88), 70), (X(114), 128)], fill=SEAM + (255,), width=3)
        d.line([(X(88), 22), (X(88), 128)], fill=SEAM + (255,), width=3)

    # cobalt neon lines: along each leading edge, inset; along the inner blade; fuselage spine sides
    for sgn in (1, -1):
        def P(pts):
            return [(x if sgn == 1 else W - x, y) for x, y in pts]
        lead = [(x - 1, y + 7) for x, y in LEAD_EDGE[3:]]
        draw_line(img, P(lead + [(123, 122)]), 4)
        draw_line(img, P([(93, 88), (106, 120)]), 4)
        draw_line(img, P([(70, 14), (80, 26), (80, 104)]), 4)

    # cockpit canopy: deep cobalt glass teardrop with a hard white glint
    can = Image.new("L", (W, H), 0)
    ImageDraw.Draw(can).polygon(mirror([(64, 16), (71, 30), (72, 46), (66, 56)]), fill=255)
    cm = np.asarray(can, float)[..., None] / 255.0
    yy = np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1))
    glass = GLASS_LIT * (1 - yy * 1.6).clip(0, 1) + GLASS_DEEP * (yy * 1.6).clip(0, 1)
    arr = np.asarray(img, float)
    arr[..., :3] = arr[..., :3] * (1 - cm) + glass * cm
    img = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    d.line([(61, 24), (59, 36)], fill=(255, 255, 255, 255), width=3)

    # engine nozzle and flame at the tail (SEEDED FLAW: orange)
    d.polygon([(52, 104), (76, 104), (74, 128), (54, 128)], fill=(20, 24, 48, 255))
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    fd.polygon([(55, 110), (73, 110), (70, 128), (58, 128)], fill=FLAME_OUTER + (255,))
    fd.polygon([(60, 112), (68, 112), (66, 128), (62, 128)], fill=FLAME_CORE + (255,))
    img = Image.alpha_composite(img, fl.filter(ImageFilter.GaussianBlur(1.2)))
    # keep the flame inside the hull silhouette
    a = np.asarray(img).copy()
    a[..., 3] = (alpha * 255).astype(np.uint8)
    img = Image.fromarray(a, "RGBA")

    # SEEDED FLAW: thin fuchsia rim on the bottom-facing edges (the side toward the black hole)
    hull = alpha > 0.5
    below = np.zeros_like(hull)
    below[:-SS, :] = hull[SS:, :]
    rim = hull & ~below          # bottom SS px of every column of the hull
    a = np.asarray(img).copy()
    a[rim, :3] = FUCHSIA_RIM
    img = Image.fromarray(a, "RGBA")
    return img


# ---------------------------------------------------------------- round 2
# Fuselage right half: a forked nose. The prong tip sits on the bar's top
# corner and flares a little past it (blade tips may pass the hitbox); the slot
# between the prongs is filled by the canopy glass, flush with the top edge.
FUS2_R = [(64, 0), (91, 0), (88, 12), (88, 128)]
PRONG_IN_R = [(64, 0), (72, 0), (70, 30), (66, 46)]          # inner edge of the right prong
# Upper blade: long and thin, root high on the fuselage, tip out past the foot's corner.
BLADE2_LEAD = bezier((88, 18), (104, 44), (128, 68))
BLADE2_TRAIL = bezier((128, 68), (108, 60), (88, 54))
BLADE2_UP_R = BLADE2_LEAD + BLADE2_TRAIL[1:]
# Lower blade: fills the foot edge to edge, cut from the upper blade by a dark gap
# that stays above the foot (y < 80).
BLADE2_LO_R = [(88, 64), (128, 80), (128, 128), (88, 128)]
# Trailing blade tucked under it: drawn as a seam inside the lower blade.
SEAM2_R = [(92, 80), (116, 128)]


def pieces_r2():
    fus = poly_mask(mirror(FUS2_R))
    out = [fus]
    for pts in (BLADE2_UP_R, BLADE2_LO_R):
        out.append(poly_mask(pts))
        out.append(poly_mask([(W - x, y) for x, y in pts]))
    return out


def shade_r2(mask, bevel=5.0, tail=0.34):
    """Like shade(), but the belly and the shadow side sink to deep navy (The light)."""
    m = np.asarray(mask, float) / 255.0
    hgt = np.asarray(mask.filter(ImageFilter.GaussianBlur(bevel)), float) / 255.0
    gy, gx = np.gradient(hgt)
    n = np.dstack([-gx * 9, -gy * 9, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    light = np.array([-0.45, -0.80, 0.40])
    light /= np.linalg.norm(light)
    diff = np.clip((n * light).sum(2), 0, 1)
    half = light + np.array([0, 0, 1.0])
    half /= np.linalg.norm(half)
    spec = np.clip((n * half).sum(2), 0, 1) ** 28
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    base = PLATE_HI[None, None] * (1 - yy[..., None] * 0.45) + PLATE_MID[None, None] * (yy[..., None] * 0.45)
    rows = np.where(m.any(1))[0]
    t = np.clip((yy - rows[0] / H) / max(1e-6, (rows[-1] - rows[0]) / H), 0, 1)
    k = (0.22 + 1.10 * diff - tail * t ** 1.5)[..., None].clip(0, 1.1)
    col = PLATE_LO * (1 - k) + base * k
    col = np.clip(col + spec[..., None] * 255, 0, 255)
    return col, m


def render_big_r2():
    rgb = np.zeros((H, W, 3), float)
    alpha = np.zeros((H, W), float)
    masks = pieces_r2()
    for i, mk in enumerate(masks):
        # the lower blades are the belly: their tails sink to deep navy
        col, m = shade_r2(mk, bevel=6.0 if i == 0 else 4.0, tail=0.75 if i >= 3 else 0.34)
        rgb = rgb * (1 - m[..., None]) + col * m[..., None]
        alpha = np.maximum(alpha, m)
    img = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)

    for sgn in (1, -1):
        def P(pts):
            return [(x if sgn == 1 else W - x, y) for x, y in pts]
        # navy seams: blade roots, trailing blade
        d.line(P([(88, 14), (88, 128)]), fill=SEAM + (255,), width=3)
        d.line(P(SEAM2_R), fill=SEAM + (255,), width=3)
        # cobalt neon lines: upper blade leading edge, lower blade edge, fuselage sides
        draw_line(img, P([(x, y + 6) for x, y in BLADE2_LEAD[3:-3]]), 3)
        draw_line(img, P([(96, 72), (123, 85), (123, 124)]), 3)
        draw_line(img, P([(73, 1), (71, 30), (67, 46)]), 3)
        draw_line(img, P([(84, 18), (82, 104)]), 3)

    # canopy: deep cobalt glass from the top edge down between the prongs
    can = Image.new("L", (W, H), 0)
    ImageDraw.Draw(can).polygon(mirror([(64, 0)] + PRONG_IN_R[1:] + [(64, 50)]), fill=255)
    cm = np.asarray(can, float)[..., None] / 255.0
    yy = np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1))
    glass = GLASS_LIT * (1 - yy * 2.6).clip(0, 1) + GLASS_DEEP * (yy * 2.6).clip(0, 1)
    arr = np.asarray(img, float)
    arr[..., :3] = arr[..., :3] * (1 - cm) + glass * cm
    img = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    d.line([(61, 4), (60, 18)], fill=(255, 255, 255, 255), width=3)   # hard white glint
    for sgn in (1, -1):     # hard white highlight on each prong tip
        d.line([(sgn * (x - 64) + 64, y) for x, y in [(76, 1), (86, 1), (84, 8)]], fill=(255, 255, 255, 255), width=2)

    # engine nozzle and the blue flame
    d.polygon([(52, 104), (76, 104), (74, 128), (54, 128)], fill=(12, 16, 40, 255))
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    fd.polygon([(55, 108), (73, 108), (70, 128), (58, 128)], fill=FLAME2_OUTER + (255,))
    fd.polygon([(58, 110), (70, 110), (68, 128), (60, 128)], fill=FLAME2_MID + (255,))
    fd.polygon([(61, 112), (67, 112), (65, 128), (63, 128)], fill=FLAME2_CORE + (255,))
    img = Image.alpha_composite(img, fl.filter(ImageFilter.GaussianBlur(1.2)))
    a = np.asarray(img).copy()
    a[..., 3] = (alpha * 255).astype(np.uint8)    # no flame outside the hull
    return Image.fromarray(a, "RGBA")


def shrink(big):
    """Premultiplied shrink, so no dark fringe at the edges."""
    return big.convert("RGBa").resize((SHIP_W, SHIP_H), Image.LANCZOS).convert("RGBA")


def shrink_r2(big):
    """Premultiplied shrink in float, so faint edge pixels keep their true hue
    (Lanczos ringing and the 8-bit RGBa round trip tinted a few warm).
    A 4x box filter is a plain supersample average: no ringing."""
    a = np.asarray(big, float) / 255.0
    pm = a[..., :3] * a[..., 3:4]
    def rs(ch):
        return np.asarray(Image.fromarray(ch.astype(np.float32), "F").resize((SHIP_W, SHIP_H), Image.BOX))
    al = np.clip(rs(a[..., 3]), 0, 1)
    rgb = np.dstack([rs(pm[..., i]) for i in range(3)])
    rgb = np.clip(rgb / np.maximum(al, 1e-6)[..., None], 0, 1)
    out = np.dstack([rgb, al[..., None]]) * 255
    out[al * 255 < 1] = 0
    return Image.fromarray(np.round(out).astype(np.uint8), "RGBA")


def hitbox_boxes():
    bx0 = (SHIP_W - BAR_W) // 2
    return [(bx0, 0, bx0 + BAR_W, SHIP_H), (0, SHIP_H - FOOT_H, SHIP_W, SHIP_H)]


def coverage(sprite):
    """Share of hitbox pixels the look covers with alpha >= 128."""
    a = np.asarray(sprite)[..., 3]
    hb = np.zeros((SHIP_H, SHIP_W), bool)
    for x0, y0, x1, y1 in hitbox_boxes():
        hb[y0:y1, x0:x1] = True
    return (hb & (a >= 128)).sum(), hb.sum()


def load_font(size):
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([400])
    return font


def draw_board(sprite):
    """1x on the game background, 4x zoom with a faint hitbox outline, and the frame row."""
    k = 4
    zoom = sprite.resize((SHIP_W * k, SHIP_H * k), Image.NEAREST)
    zbg = Image.new("RGBA", zoom.size, GAME_BG + (255,))
    zoom = Image.alpha_composite(zbg, zoom)
    ov = Image.new("RGBA", zoom.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for x0, y0, x1, y1 in hitbox_boxes():
        od.rectangle([x0 * k, y0 * k, x1 * k - 1, y1 * k - 1], outline=(120, 255, 140, 90), width=1)
    zoom = Image.alpha_composite(zoom, ov).convert("RGB")

    # 1x on a patch of the game background, with room around it
    patch = Image.new("RGB", (160, 160), GAME_BG)
    patch.paste(sprite, (64, 64), sprite)
    # frame row: one frame (idle), shown at 1x on the background
    row = Image.new("RGB", (SHIP_W + 16, SHIP_H + 16), GAME_BG)
    row.paste(sprite, (8, 8), sprite)

    pad, cap_h = 24, 22
    bw = pad + patch.width + pad + zoom.width + pad + max(row.width, 150) + pad
    bh = pad + cap_h + max(patch.height, zoom.height) + pad
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
    x = pad
    place(patch, x, top, f"1x, {SHIP_W}x{SHIP_H}")
    x += patch.width + pad
    place(zoom, x, top, "4x, hitbox faint")
    x += zoom.width + pad
    place(row, x, top, "frames: idle (1)")
    return board


def main():
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sprite = shrink_r2(render_big_r2()) if rnd >= 2 else shrink(render_big())
    sprite.save(OUT_DIR / f"demo-ship-r{rnd}.png")
    draw_board(sprite).save(OUT_DIR / f"demo-ship-r{rnd}-board.png")
    cov, tot = coverage(sprite)
    print("wrote", OUT_DIR / f"demo-ship-r{rnd}.png", f"hitbox covered {cov}/{tot}")
    a = np.asarray(sprite)[..., 3]
    hb = np.zeros((SHIP_H, SHIP_W), bool)
    for x0, y0, x1, y1 in hitbox_boxes():
        hb[y0:y1, x0:x1] = True
    for y in range(SHIP_H):
        print("".join("#" if a[y, x] >= 128 else ("x" if hb[y, x] else ".") for x in range(SHIP_W)))


if __name__ == "__main__":
    main()
