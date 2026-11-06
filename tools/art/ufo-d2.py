"""UFO, design 2: the wrecked saucer. Dented hull, cracked green dome, scorch marks.

Draws the master at 8x the game size (320 x 160 for the 40 x 20 canvas in
docs/design/gdd/drifters/07-ufo.md, art_canvas). The saucer is drawn on the
full box (disc 40 x 10, dome radius 9 on the middle of its top edge), then
scaled to 90% about the bottom centre so it sits inside both hitbox shapes
and leaves about 2 game px of room for the soft hazard glow. The master is shrunk to 40 x 20 with Lanczos. Hitboxes come from the
spec and never change with the look: the drawing only has to sit inside them.

Colors: grey hull and green dome as in the spec's placeholder_look, hot amber
lights and embers (heat, danger), a thin fuchsia rim on the underside (rule 8).
No cobalt blue anywhere: that is the ship's color.

Layers are drawn apart (glow, body, dome, damage, lights, rim) so the Piskel file can
carry them. The still image is the composite of the layers at master size,
shrunk once.

Outputs, for round N (default 1), in --out-dir (default staging/assets/sprites):
  ufo-d2-rN.png          40 x 20 image
  ufo-d2-rN-master.png   320 x 160 master
  ufo-d2-rN-board.png    preview board for the UI Art Critic
  ufo-d2-rN.piskel       layered Piskel file (40 x 20, one frame)

Usage: python3 tools/art/ufo-d2.py [--round N] [--seed S] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from piskel_file import write_piskel  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"

UP = 8  # master scale
GW, GH = 40, 20  # game canvas, spec art_canvas
W, H = GW * UP, GH * UP
DISC_TOP = 10 * UP  # disc box: y 80..160
DISC_CY = DISC_TOP + 5 * UP  # 120
DOME_CX, DOME_CY, DOME_R = W // 2, DISC_TOP, 9 * UP  # circle r 9 on the top edge

BOARD_BG = (10, 12, 34)
TXT = (200, 205, 225)
FUCHSIA = (255, 60, 200)
AMBER = (255, 168, 40)
YELLOW = (255, 232, 130)


# ---------- small helpers ----------

def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(stops, t):
    """stops: [(pos, (r,g,b)), ...] ascending; t array in 0..1 -> (h,w,3) float."""
    t = np.clip(t, 0, 1)
    out = np.zeros(t.shape + (3,), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(t, [p for p, _ in stops], [c[ch] for _, c in stops])
    return out


def mask_from_draw(fn, blur=0.0):
    im = Image.new("L", (W, H), 0)
    fn(ImageDraw.Draw(im))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, dtype=np.float32) / 255.0


def shift(a, dx, dy):
    """Shift an array by whole pixels, filling with 0."""
    out = np.zeros_like(a)
    h, w = a.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    out[ys0 + dy : ys1 + dy, xs0 + dx : xs1 + dx] = a[ys0:ys1, xs0:xs1]
    return out


def to_img(rgb, alpha):
    a = np.clip(alpha, 0, 1)
    arr = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def smooth_noise(rng, scale):
    """Soft 0..1 noise: random grid at 1/scale, bicubic up, light blur."""
    gh, gw = H // scale + 2, W // scale + 2
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * scale, gh * scale), Image.BICUBIC)
    im = im.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(scale / 3))
    n = np.asarray(im, dtype=np.float32) / 255.0
    n = (n - n.min()) / max(1e-6, n.max() - n.min())
    return n


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


# ---------- shapes ----------

def hull_mask():
    """Saucer lens filling the 40 x 10 disc box, with the damage bites cut out."""
    dx = (XX + 0.5 - W / 2) / (W / 2)
    dy = (YY + 0.5 - DISC_CY) / (5 * UP)
    n = np.where(dy < 0, 2.7, 2.2)
    val = np.abs(dx) ** n + np.abs(dy) ** n
    m = np.clip((1.0 - val) * 14.0 + 0.5, 0, 1)  # soft edge
    m *= (YY >= DISC_TOP).astype(np.float32)

    def bites(d):
        # upper-left chunk gone
        d.ellipse([-14, 84, 30, 118], fill=255)
        # jagged tear on the upper right
        d.polygon([(246, 74), (258, 86), (252, 92), (270, 94), (262, 102), (284, 104), (300, 98), (320, 74)], fill=255)
        # small bite out of the belly
        d.polygon([(184, 160), (194, 134), (205, 146), (216, 126), (232, 160)], fill=255)

    cut = mask_from_draw(bites, blur=1.0)
    return np.clip(m * (1 - cut), 0, 1)


def collar_mask():
    return mask_from_draw(lambda d: d.ellipse([DOME_CX - 76, DISC_TOP - 4, DOME_CX + 76, DISC_TOP + 12], fill=255), 1.0)


def dome_mask():
    def f(d):
        d.pieslice([DOME_CX - DOME_R, DOME_CY - DOME_R, DOME_CX + DOME_R, DOME_CY + DOME_R], 180, 360, fill=255)
        d.rectangle([DOME_CX - DOME_R, DOME_CY - 1, DOME_CX + DOME_R, DOME_CY + 5], fill=255)

    return mask_from_draw(f, 1.0)


# ---------- layers ----------

def body_layer(hull, collar, rng):
    # metal gradient: pale top deck, dark belly, deep navy shadow at the very bottom
    t = (YY - DISC_TOP) / (H - DISC_TOP)
    stops = [
        (0.00, (196, 200, 216)),
        (0.25, (160, 164, 184)),
        (0.46, (128, 134, 162)),
        (0.52, (100, 106, 138)),
        (0.80, (86, 92, 126)),
        (1.00, (62, 68, 106)),
    ]
    rgb = lerp_color(stops, t)
    # light from the upper left, shadow to the right
    rgb *= (1.08 - 0.28 * (XX / W))[..., None]

    # hard white highlight along the top edge, strongest left of centre
    top_band = hull * (1 - shift(hull, 0, 7))
    fall = np.clip(1.15 - np.abs(XX - 0.34 * W) / (0.55 * W), 0, 1)
    rgb = rgb * (1 - top_band[..., None] * fall[..., None]) + np.array([255, 255, 255]) * (top_band * fall)[..., None]

    # seam between the deck and the belly, and one lower seam
    def seams(d):
        pts = [(x, 113 + 5 * math.sin(x / 320 * math.pi) * -1 + 0) for x in range(0, W + 1, 8)]
        d.line(pts, fill=255, width=3)
        pts2 = [(x, 141 - 6 * math.sin(x / 320 * math.pi)) for x in range(0, W + 1, 8)]
        d.line(pts2, fill=255, width=2)

    seam = mask_from_draw(seams, 0.8) * hull
    rgb = rgb * (1 - 0.55 * seam[..., None])
    # a thin lit edge under the main seam
    seam_lit = shift(seam, 0, 3) * (1 - seam) * hull
    rgb = rgb + 40 * seam_lit[..., None]

    # dents: dark upper-left inner shadow, lit lower-right inner edge
    def dents(d):
        d.ellipse([100, 94, 154, 130], fill=255)  # big dent, left of the dome
        d.ellipse([210, 118, 250, 144], fill=255)  # small dent, belly right

    dent = mask_from_draw(dents, 1.2)
    shifted = shift(dent, 9, 9)
    shadow = np.clip(dent - shifted, 0, 1)
    lit = np.clip(shifted - dent, 0, 1)
    rgb = rgb * (1 - 0.45 * dent[..., None] * 0.35 - 0.65 * shadow[..., None])
    rgb = rgb + 110 * lit[..., None]
    rgb = rgb * hull[..., None]

    # collar ring under the dome
    ct = np.clip((YY - (DISC_TOP - 4)) / 16.0, 0, 1)
    crgb = lerp_color([(0, (150, 154, 176)), (1, (52, 54, 80))], ct)
    rgb = rgb * (1 - collar[..., None]) + crgb * collar[..., None]

    alpha = np.maximum(hull, collar)
    return to_img(rgb, alpha)


def cracks(rng, origin, count, clip):
    """Jagged cracks fanning out from origin. Returns (dark, light) masks."""
    def draw(shift_xy):
        def f(d):
            ox, oy = origin
            ox += shift_xy[0]
            oy += shift_xy[1]
            for k in range(count):
                ang = math.radians(rng_angles[k])
                x, y = ox, oy
                total = rng_lens[k]
                run = 0
                pts = [(x, y)]
                while run < total:
                    seg = 12 + (k * 7 + int(run)) % 9
                    ang += math.radians(((k * 37 + int(run) * 13) % 41) - 20)
                    x += math.cos(ang) * seg
                    y += math.sin(ang) * seg
                    pts.append((x, y))
                    run += seg
                d.line(pts, fill=255, width=13 if k % 2 == 0 else 10, joint="curve")
            # ring crack around the impact
            d.arc([ox - 30, oy - 24, ox + 30, oy + 24], 190, 330, fill=255, width=11)

        return mask_from_draw(f, 0.8)

    rng_angles = [200, 255, 300, 340, 25, 150, 100]
    rng_lens = [88, 70, 56, 64, 40, 60, 36]
    dark = draw((0, 0)) * clip
    light = np.clip(draw((7, 7)) - draw((0, 0)), 0, 1) * clip
    return dark, light


def dome_layer(dome, rng):
    # green glass lit from the upper left
    dist = np.hypot(XX - 128, YY - 38) / 112.0
    stops = [
        (0.00, (205, 255, 215)),
        (0.18, (120, 235, 140)),
        (0.40, (90, 220, 110)),
        (0.78, (30, 125, 66)),
        (1.00, (10, 62, 38)),
    ]
    rgb = lerp_color(stops, dist)
    # darker near the base, a green bounce light from the hull right at the foot
    base = np.clip((YY - 56) / 28.0, 0, 1)
    rgb = rgb * (1 - 0.40 * base[..., None])
    # deep green outline ring
    inner = shift(dome, 0, 0)
    edge = dome * (1 - np.asarray(Image.fromarray((dome * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9)), dtype=np.float32) / 255.0)
    rgb = rgb * (1 - 0.45 * edge[..., None]) + np.array([4, 40, 24]) * (0.45 * edge[..., None])

    # hard white glints
    def glints(d):
        d.ellipse([100, 22, 146, 40], fill=255)
        d.ellipse([151, 18, 163, 26], fill=255)

    g = mask_from_draw(glints, 2.0) * dome
    g_arc = mask_from_draw(lambda d: d.arc([DOME_CX - 62, DOME_CY - 62, DOME_CX + 62, DOME_CY + 62], 195, 245, fill=255, width=5), 1.0) * dome
    gl = np.clip(g * 0.85 + g_arc * 0.7, 0, 1)
    rgb = rgb * (1 - gl[..., None]) + 255 * gl[..., None]

    # missing shard: a dark hollow, jagged, cut into the upper right
    def hole(d):
        d.polygon(
            [(182, 4), (200, 12), (206, 30), (219, 42), (212, 58), (199, 50), (198, 40), (186, 34), (183, 22), (176, 14)],
            fill=255,
        )

    hole_m = mask_from_draw(hole, 0.8)
    in_dome = dome * (1 - hole_m)
    # inside of the hollow is dark glass, lit a little at its lower edge
    deep = np.asarray(Image.fromarray((dome * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(15)), dtype=np.float32) / 255.0
    hollow = dome * hole_m * deep
    hrgb = lerp_color([(0, (6, 26, 20)), (1, (16, 70, 48))], np.clip((YY - 10) / 50.0, 0, 1))
    rim_in = np.clip(shift(hole_m, -4, -4) - hole_m, 0, 1) * hollow  # not used for clipping below
    rgb = rgb * in_dome[..., None] + hrgb * hollow[..., None]
    # pale broken-glass edge along the hole's lower-left side
    edge_l = np.clip(hole_m - shift(hole_m, 5, -5), 0, 1) * dome
    rgb = rgb * (1 - 0.8 * edge_l[..., None]) + np.array([215, 255, 225]) * (0.8 * edge_l[..., None])

    # cracks fanning from an impact point lower left of the hole
    dark, light = cracks(rng, (166, 54), 7, dome * (1 - hole_m))
    rgb = rgb * (1 - 0.95 * dark[..., None]) + np.array([4, 30, 20]) * (0.95 * dark[..., None])
    rgb = rgb * (1 - 0.8 * light[..., None]) + np.array([200, 255, 215]) * (0.8 * light[..., None])

    return to_img(rgb, in_dome + hollow)


def soot_alpha(rng, blobs, noise_scale=10):
    m = np.zeros((H, W), dtype=np.float32)
    for cx, cy, rx, ry, strength in blobs:
        e = mask_from_draw(lambda d: d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255), blur=rx / 3.2)
        m = np.maximum(m, e * strength)
    n = smooth_noise(rng, noise_scale)
    m = np.clip(m * (0.85 + 0.3 * n), 0, 1)
    return m


def glow(cx, cy, r, color, power=2.0):
    d = np.hypot(XX - cx, YY - cy) / r
    a = np.clip(1 - d, 0, 1) ** power
    return a


def damage_layer(hull, dome, rng):
    body_only = hull * (1 - dome)
    # soot on the hull: round the torn corner, along the belly bite, left stub and under the dome
    soot_h = soot_alpha(
        rng,
        [
            (258, 98, 40, 22, 1.0),
            (214, 148, 24, 11, 1.0),
        ],
    )
    # long streaks trailing left from the tear (it flies right, smoke streams back)
    def streaks(d):
        d.line([(240, 100), (190, 104)], fill=255, width=7)

    st = mask_from_draw(streaks, 2.5) * 0.7
    soot_h = np.clip(np.maximum(soot_h, st), 0, 1)
    soot_h = np.clip((soot_h - 0.25) * 2.2, 0, 0.92)  # crisp patch edges, no speckle
    soot_h *= body_only
    # soot on the dome, near the hollow
    soot_d = soot_alpha(rng, [(232, 56, 26, 24, 0.8)], 8) * dome

    soot = np.clip(soot_h + soot_d, 0, 1)
    soot_rgb = np.zeros((H, W, 3), dtype=np.float32) + np.array([30, 22, 26], dtype=np.float32)

    # embers glowing in the scorch: orange cores with yellow hearts
    emb = np.zeros((H, W), dtype=np.float32)
    ember_pts = [(250, 100, 9), (262, 104, 7), (205, 152, 8), (214, 148, 6), (30, 112, 7), (206, 42, 8), (196, 48, 5)]
    hot = np.zeros((H, W), dtype=np.float32)
    for x, y, r in ember_pts:
        emb = np.maximum(emb, glow(x, y, r * 1.8, None, 2.0) * 0.8)
        hot = np.maximum(hot, glow(x, y, r * 0.7, None, 1.5))
    clip = np.maximum(hull, dome)
    emb *= clip
    hot *= clip
    ember_rgb = lerp_color([(0, (255, 90, 20)), (1, (255, 236, 150))], hot)

    # composite soot under the embers into one layer
    a_soot = soot
    a_emb = np.clip(emb, 0, 1)
    out_a = a_soot + a_emb * (1 - a_soot)
    out_rgb = (soot_rgb * a_soot[..., None] + ember_rgb * (a_emb * (1 - a_soot))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
    # embers glow through the soot too
    mix = np.clip(a_emb * 1.4, 0, 1)[..., None]
    out_rgb = out_rgb * (1 - mix * 0.9) + ember_rgb * (mix * 0.9)
    out_a = np.maximum(out_a, a_emb)
    return to_img(out_rgb, out_a)


def lights_layer(hull):
    """Port lights along the belly. Some lit amber, one flickering yellow, three dead."""
    y = 128
    plan = [
        (40, "amber"),
        (80, "dead"),
        (120, "amber"),
        (160, "yellow"),
        (200, "dead"),
        (240, "amber"),
        (280, "dead"),
    ]
    rgb = np.zeros((H, W, 3), dtype=np.float32)
    alpha = np.zeros((H, W), dtype=np.float32)

    def put(color, a):
        nonlocal rgb, alpha
        out_a = a + alpha * (1 - a)
        rgb = (np.array(color, dtype=np.float32) * a[..., None] + rgb * (alpha * (1 - a))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
        alpha = out_a

    for x, kind in plan:
        yy = y + 4 * math.sin(x / 320 * math.pi) * -1 + 3  # follows the belly curve a little
        if kind == "dead":
            core = np.clip(1 - np.hypot(XX - x, YY - yy) / 7.5, 0, 1) ** 0.5
            put((18, 16, 28), core * 0.95)
            # a fine crack through the dead lamp
            c = mask_from_draw(lambda d: d.line([(x - 6, yy - 6), (x + 1, yy + 1), (x + 6, yy - 1)], fill=255, width=2), 0.5)
            put((120, 110, 130), c * 0.5)
        else:
            col = AMBER if kind == "amber" else YELLOW
            halo = glow(x, yy, 22, None, 2.0) * 0.45
            put(col, halo)
            core = np.clip(1 - np.hypot(XX - x, YY - yy) / 8.5, 0, 1) ** 0.4
            put(col, core)
            put((255, 250, 220), np.clip(1 - np.hypot(XX - x, YY - yy) / 4.0, 0, 1))
    alpha = alpha * hull
    return to_img(rgb, alpha)


def rim_layer(hull):
    """Thin fuchsia rim on the underside, brighter toward the bottom left (rule 8)."""
    # Thin, about 5 px at 8x after the 90% scale, the same
    # strength all along the underside, and it follows the notch: the notch
    # edges face down too, so the rim runs through the damage without a gap.
    band = np.clip(hull * (1 - shift(hull, 0, -6)), 0, 1)
    a = band * 0.85
    rgb = np.zeros((H, W, 3), dtype=np.float32) + np.array(FUCHSIA, dtype=np.float32)
    core = np.clip(hull * (1 - shift(hull, 0, -4)), 0, 1)
    rgb = rgb * (1 - 0.5 * core[..., None]) + np.array([255, 150, 235]) * (0.5 * core[..., None])
    return to_img(rgb, a)


def fit(im):
    """Scale a full-canvas layer to 90% about the bottom centre, 1 game px above the bottom."""
    sc = 0.9
    w, h = round(W * sc), round(H * sc)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(im.resize((w, h), Image.LANCZOS), ((W - w) // 2, H - UP - h))
    return out


def blur_a(im, r):
    a = Image.fromarray((np.asarray(im, dtype=np.uint8)[..., 3]))
    return np.asarray(a.filter(ImageFilter.GaussianBlur(r)), dtype=np.float32) / 255.0


def glow_layer(body, dome):
    """Soft hazard glow: green round the dome, hot amber round the hull. Pre-rendered."""
    gg = np.clip(blur_a(dome, 15) * 2.8, 0, 1) * 0.90
    gw = np.clip(blur_a(body, 13) * 2.6, 0, 1) * 0.85
    green = np.array([70, 235, 130], dtype=np.float32)
    amber = np.array([255, 150, 45], dtype=np.float32)
    wsum = gg + gw
    rgb = (green * gg[..., None] + amber * gw[..., None]) / np.maximum(wsum, 1e-6)[..., None]
    a = 1 - (1 - gg) * (1 - gw)
    # fade to nothing at the canvas edge so the halo is never cut off
    ex = np.minimum(XX, W - 1 - XX) / (2.5 * UP)
    ey = np.minimum(YY, H - 1 - YY) / (2.5 * UP)
    a = a * np.clip(np.minimum(ex, ey), 0, 1) ** 1.2
    return to_img(rgb, a)


# ---------- build ----------

def build(seed):
    rng = np.random.default_rng(seed)
    hull = hull_mask()
    collar = collar_mask()
    dome = dome_mask()
    body = body_layer(hull, collar, rng)
    dome_im = dome_layer(dome, rng)
    damage = damage_layer(np.maximum(hull, collar), dome, rng)
    lights = lights_layer(hull)
    rim = rim_layer(hull)
    layers = [("body", body), ("dome", dome_im), ("damage", damage), ("lights", lights), ("rim", rim)]
    layers = [(n, fit(im)) for n, im in layers]
    glow_im = glow_layer(layers[0][1], layers[1][1])
    layers = [("glow", glow_im)] + layers
    master = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for _, im in layers:
        master = Image.alpha_composite(master, im)
    return layers, master


def shrink(im):
    return im.resize((GW, GH), Image.LANCZOS)


def board(img, out_path):
    z4 = img.resize((GW * 4, GH * 4), Image.NEAREST)
    z4h = z4.copy()
    d = ImageDraw.Draw(z4h)
    # disc box 40 x 10 and dome circle r 9, from the spec, at 4x
    d.rectangle([0, 10 * 4, GW * 4 - 1, GH * 4 - 1], outline=(120, 255, 200, 140))
    cx, cy, r = GW * 2, 10 * 4, 9 * 4
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 255, 200, 140))
    master_view = None
    bw, bh = 20 + 160 + 20 + 160 + 20 + 40 + 20, 300
    bd = Image.new("RGBA", (bw, bh), BOARD_BG + (255,))
    font = ImageFont.load_default()
    dr = ImageDraw.Draw(bd)

    def paste(im, x, y):
        bd.alpha_composite(im, (x, y))

    # 1x
    x = 20
    paste(img, x, 40)
    dr.text((x, 16), "1x", fill=TXT, font=font)
    # 4x clean
    x4 = 20 + 40 + 20
    paste(z4, x4, 40)
    dr.text((x4, 16), "4x", fill=TXT, font=font)
    # 4x with hitbox
    x4h = x4 + 160 + 20
    paste(z4h, x4h, 40)
    dr.text((x4h, 16), "4x with hitbox (disc box, dome circle)", fill=TXT, font=font)
    # master
    mimg = master_view_cache["master"]
    paste(mimg.resize((W // 2, H // 2), Image.LANCZOS), 20, 140)
    dr.text((20, 124), "master 320 x 160, shown at 1/2", fill=TXT, font=font)
    # 1x on a mid-bright background strip to check it still reads
    strip = Image.new("RGBA", (120, 40), (40, 20, 70, 255))
    strip.alpha_composite(img, (40, 10))
    paste(strip, 20 + 160 + 20, 140)
    dr.text((20 + 160 + 20, 124), "1x on a purple glow", fill=TXT, font=font)
    bd.save(out_path)
    return bd.size


master_view_cache: dict = {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()

    layers, master = build(args.seed)
    master_view_cache["master"] = master
    small = shrink(master)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    stem = f"ufo-d2-r{args.round}"
    small.save(out / f"{stem}.png")
    master.save(out / f"{stem}-master.png")
    board(small, out / f"{stem}-board.png")
    write_piskel(out / f"{stem}.piskel", "ufo-d2", [(n, [shrink(im)]) for n, im in layers])
    print(f"wrote {stem}: image {small.size}, master {master.size}")


if __name__ == "__main__":
    main()
