"""UFO, design 3: the half-alive saucer. Ribbed organic shell, bio-green dome.

Draws the master at 8x the game size (320 x 160 for the 40 x 20 canvas in
docs/design/gdd/drifters/07-ufo.md, art_canvas): the disc fills the bottom 10
rows (a 40 x 10 box), the dome (radius 9) stands on the middle of the disc's
top edge. The master is shrunk to 40 x 20 with Lanczos. Hitboxes come from the
spec and never change with the look: the drawing only has to sit inside them.

Direction: half alive. The shell is warm grey-violet with a few crisp radial ribs
fanning out from under the dome (light ridges, dark grooves, one hue family),
a plum belly with scalloped edge, and glowing amber pores. The dome is green glass with a living organ inside: veins and a
bright lime nucleus. No cobalt blue anywhere (the ship's color). A thin
fuchsia rim on the underside (GDD 12 rule 8). A soft pre-rendered green glow
around the dome (GDD 12 `glow`).

Layers are drawn apart (glow, halo, body, dome, pores, rim) for the Piskel file. The
still image is their composite at master size, shrunk once.

Outputs, for round N (default 1), in --out-dir (default staging/assets/sprites):
  ufo-d3-rN.png          40 x 20 image
  ufo-d3-rN-master.png   320 x 160 master
  ufo-d3-rN-board.png    preview board for the UI Art Critic
  ufo-d3-rN.piskel       layered Piskel file (40 x 20, one frame)

Usage: python3 tools/art/ufo-d3.py [--round N] [--seed S] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from piskel_file import write_piskel  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"

UP = 8
GW, GH = 40, 20
W, H = GW * UP, GH * UP
DISC_TOP = 10 * UP  # 80
DISC_CY = DISC_TOP + 5 * UP  # 120
DOME_CX, DOME_CY, DOME_R = W // 2, DISC_TOP, 9 * UP

BOARD_BG = (10, 12, 34)
TXT = (200, 205, 225)
FUCHSIA = (255, 60, 200)
AMBER = (255, 170, 50)
LIME = (190, 255, 110)

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

SEED = [7]
RIB_N = 25  # ribs: angular frequency, about 6 game px apart at the disc
RIB_ORIGIN_Y = -100.0  # ribs fan out from a point above the sprite


def lerp_color(stops, t):
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
    gh, gw = H // scale + 2, W // scale + 2
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * scale, gh * scale), Image.BICUBIC)
    im = im.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(scale / 3))
    n = np.asarray(im, dtype=np.float32) / 255.0
    return (n - n.min()) / max(1e-6, n.max() - n.min())


def min_filter(m, size):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(size))
    return np.asarray(im, dtype=np.float32) / 255.0


_WARP = {}


def warp_fields():
    """Low-frequency random fields, fixed per seed: they bend the rib phase and the rim."""
    if not _WARP:
        rng = np.random.default_rng(SEED[0])
        _WARP["phase"] = smooth_noise(rng, 40)
        _WARP["edge"] = smooth_noise(rng, 24)
        _WARP["wide"] = smooth_noise(rng, 64)
    return _WARP


def rib_wave():
    """0..1 across the disc: 1 on a rib ridge, 0 in a groove. Radial fan, grown not machined.

    The phase is bent by noise and the rib spacing drifts across the disc, so the
    bands differ in width and gap. A second slow wave makes some ribs fat, some thin.
    """
    wf = warp_fields()
    ang = np.arctan2(XX + 0.5 - W / 2, YY + 0.5 - RIB_ORIGIN_Y)
    drift = ang * RIB_N * (1.0 + 0.22 * (wf["wide"] - 0.5))
    ph = drift + (wf["phase"] - 0.5) * 3.4 + 0.9 * np.sin(ang * 9.0 + 1.3)
    return 0.5 + 0.5 * np.cos(ph)


# ---------- shapes ----------

def hull_mask():
    """Lens filling the 40 x 10 disc box; the belly edge is scalloped by the ribs."""
    dx = (XX + 0.5 - W / 2) / (W / 2)
    dy = (YY + 0.5 - DISC_CY) / (5 * UP)
    rib = rib_wave()
    # grooves pull the lower edge in a little: lobed, fleshy underside
    dy = np.where(dy > 0, dy * (1.0 + 0.16 * (1 - rib)), dy)
    n = np.where(dy < 0, 2.7, 2.3)
    val = np.abs(dx) ** n + np.abs(dy) ** n
    wf = warp_fields()
    # bulges and dents along the edge; the edge only moves inward, so the shell stays in its box
    val = val * (1.0 + 0.16 * (1 - wf["edge"]) * np.clip(np.abs(dx) ** 1.5 + np.abs(dy) ** 2, 0, 1))
    m = np.clip((1.0 - val) * 14.0 + 0.5, 0, 1)
    return m * (YY >= DISC_TOP).astype(np.float32)


def collar_mask():
    return mask_from_draw(lambda d: d.ellipse([DOME_CX - 78, DISC_TOP - 5, DOME_CX + 78, DISC_TOP + 13], fill=255), 1.2)


def dome_mask():
    def f(d):
        d.pieslice([DOME_CX - DOME_R, DOME_CY - DOME_R, DOME_CX + DOME_R, DOME_CY + DOME_R], 180, 360, fill=255)
        d.rectangle([DOME_CX - DOME_R, DOME_CY - 1, DOME_CX + DOME_R, DOME_CY + 5], fill=255)

    return mask_from_draw(f, 1.0)


# ---------- layers ----------

def glow_layer(dome, hull):
    """Soft green halo around the dome, pre-rendered, kept tight and faint."""
    d = np.hypot(XX - DOME_CX, (YY - DOME_CY) * 1.05) / 92.0
    a = np.clip(1 - d, 0, 1) ** 2.4 * 0.42
    a = a * (YY < DISC_TOP + 18)
    rgb = np.zeros((H, W, 3), dtype=np.float32) + np.array([90, 255, 120], dtype=np.float32)
    return to_img(rgb, a)


def halo_layer(hull, collar):
    """Soft hot halo (GDD 12 glow: hazards glow hot): amber-orange around the shell and pores."""
    solid = np.maximum(hull, collar)
    blur = np.asarray(
        Image.fromarray((solid * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), dtype=np.float32
    ) / 255.0
    a = np.clip(blur * 1.5, 0, 1) ** 1.3 * 0.46
    # strongest toward the belly, where the pores glow
    a = a * (0.55 + 0.45 * np.clip((YY - DISC_TOP) / 80.0, 0, 1))
    rgb = np.zeros((H, W, 3), dtype=np.float32) + np.array([255, 120, 40], dtype=np.float32)
    return to_img(rgb, a)


def smoothstep(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def body_layer(hull, collar, rng):
    """Shell in one family (warm grey-violet) with crisp light ridges and dark grooves.

    No noise, no dither, no mottling: at 40 px only a few clear bands survive, so
    the ribs are drawn as bands (round 2 fix for the muddy disc of round 1).
    """
    rib = rib_wave()
    t = np.clip((YY - DISC_TOP) / (H - DISC_TOP), 0, 1)
    # ridge tones: pale grey-violet on top, mid violet at the tips, plum belly
    ridge_stops = [
        (0.00, (236, 226, 244)),
        (0.35, (206, 184, 224)),
        (0.60, (168, 126, 176)),
        (1.00, (110, 62, 120)),
    ]
    groove_stops = [
        (0.00, (140, 112, 170)),
        (0.35, (104, 76, 140)),
        (0.60, (78, 48, 108)),
        (1.00, (44, 24, 76)),
    ]
    ridge_rgb = lerp_color(ridge_stops, t)
    groove_rgb = lerp_color(groove_stops, t)
    band = smoothstep(0.38, 0.62, rib)[..., None]
    rgb = groove_rgb * (1 - band) + ridge_rgb * band
    # light from the upper left, gentle so the right tip stays readable
    rgb *= (1.06 - 0.12 * (XX / W))[..., None]

    # hard white highlight along the top edge, strongest left of centre
    top_band = hull * (1 - shift(hull, 0, 6))
    fall = np.clip(1.15 - np.abs(XX - 0.30 * W) / (0.55 * W), 0, 1)
    rgb = rgb * (1 - top_band[..., None] * fall[..., None]) + 255 * (top_band * fall)[..., None]

    # one clean fold line where shell meets belly
    def fold(d):
        pts = [(x, 112 + 8 * math.sin(x / 320 * math.pi)) for x in range(0, W + 1, 8)]
        d.line(pts, fill=255, width=4)

    f = mask_from_draw(fold, 1.0) * hull
    rgb = rgb * (1 - 0.4 * f[..., None]) + np.array([50, 24, 80]) * (0.4 * f[..., None])

    rgb = rgb * hull[..., None]

    # collar ring under the dome: plain smooth gradient of the same family
    ct = np.clip((YY - (DISC_TOP - 5)) / 18.0, 0, 1)
    crgb = lerp_color([(0, (230, 220, 240)), (0.5, (170, 130, 186)), (1, (96, 56, 112))], ct)
    rgb = rgb * (1 - collar[..., None]) + crgb * collar[..., None]

    alpha = np.maximum(hull, collar)
    return to_img(rgb, alpha)


def dome_layer(dome, rng):
    # green glass lit from the upper left, deep green at the base
    dist = np.hypot(XX - 126, YY - 36) / 114.0
    stops = [
        (0.00, (214, 255, 200)),
        (0.18, (130, 240, 130)),
        (0.42, (80, 214, 96)),
        (0.80, (28, 130, 64)),
        (1.00, (8, 70, 40)),
    ]
    rgb = lerp_color(stops, dist)
    base = np.clip((YY - 56) / 28.0, 0, 1)
    rgb = rgb * (1 - 0.35 * base[..., None])

    # the living thing inside: a dark organ blob with a glowing lime nucleus and veins
    ox, oy = 168, 50
    organ_d = np.hypot((XX - ox) / 1.25, (YY - oy)) / 24.0
    organ = np.clip(1 - organ_d, 0, 1) ** 0.6
    org_rgb = lerp_color([(0, (22, 90, 48)), (1, (10, 56, 40))], np.clip(organ_d, 0, 1))
    rgb = rgb * (1 - 0.78 * organ[..., None]) + org_rgb * (0.78 * organ[..., None])

    def veins(d):
        for ang, ln in [(150, 52), (200, 44), (250, 40), (320, 34), (20, 30), (95, 24)]:
            a = math.radians(ang)
            x, y = ox, oy
            pts = [(x, y)]
            for k in range(4):
                a += math.radians(((ang * 7 + k * 31) % 33) - 16)
                x += math.cos(a) * ln / 4
                y += math.sin(a) * ln / 4
                pts.append((x, y))
            d.line(pts, fill=255, width=3, joint="curve")

    vm = mask_from_draw(veins, 1.0) * dome
    rgb = rgb * (1 - 0.62 * vm[..., None]) + np.array([14, 80, 44]) * (0.62 * vm[..., None])

    # nucleus: lime heart with a white-hot centre
    core_d = np.hypot(XX - ox, YY - oy)
    core = np.clip(1 - core_d / 15.0, 0, 1) ** 0.8
    rgb = rgb * (1 - core[..., None]) + np.array(LIME) * core[..., None]
    hot = np.clip(1 - core_d / 6.0, 0, 1)
    rgb = rgb * (1 - hot[..., None]) + np.array([245, 255, 215]) * hot[..., None]

    # darker rim ring on the glass
    edge = dome * (1 - min_filter(dome, 9))
    rgb = rgb * (1 - 0.45 * edge[..., None]) + np.array([4, 44, 26]) * (0.45 * edge[..., None])

    # hard white glints, upper left
    g = mask_from_draw(lambda d: (d.ellipse([96, 20, 142, 38], fill=255), d.ellipse([148, 16, 160, 24], fill=255)), 2.0) * dome
    g_arc = mask_from_draw(lambda d: d.arc([DOME_CX - 62, DOME_CY - 62, DOME_CX + 62, DOME_CY + 62], 195, 245, fill=255, width=5), 1.0) * dome
    gl = np.clip(g * 0.85 + g_arc * 0.7, 0, 1)
    rgb = rgb * (1 - gl[..., None]) + 255 * gl[..., None]
    return to_img(rgb, dome)


def pores_layer(hull):
    """Glowing amber pores along the belly, with soft halos: bioluminescent, warm."""
    xs = [44, 98, 160, 222, 276]
    rgb = np.zeros((H, W, 3), dtype=np.float32)
    alpha = np.zeros((H, W), dtype=np.float32)

    def put(color, a):
        nonlocal rgb, alpha
        out_a = a + alpha * (1 - a)
        rgb = (np.array(color, dtype=np.float32) * a[..., None] + rgb * (alpha * (1 - a))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
        alpha = out_a

    for i, x in enumerate(xs):
        yy = 128 + 8 * math.sin(x / 320 * math.pi) * -1 + 6
        r = 9.0 if i % 2 == 0 else 7.0
        d = np.hypot(XX - x, (YY - yy) * 1.1)
        put(AMBER, np.clip(1 - d / 24, 0, 1) ** 2 * 0.42)
        put((120, 30, 40), np.clip(1 - d / (r + 3), 0, 1) ** 0.5 * 0.9)  # dark socket
        put(AMBER, np.clip(1 - d / r, 0, 1) ** 0.45)
        put((255, 240, 190), np.clip(1 - d / (r * 0.45), 0, 1))
    return to_img(rgb, alpha * hull)


def rim_layer(hull):
    """Thin fuchsia rim on the underside, brighter toward the bottom left (rule 8)."""
    band = np.clip(hull * (1 - shift(hull, 0, -4)), 0, 1) * (YY > DISC_CY)
    face = np.clip(1.0 - 0.5 * (XX / W) - 0.15 * ((YY - DISC_TOP) / 80 - 1), 0.0, 1.0)
    a = band * (0.30 + 0.35 * face)
    rgb = np.zeros((H, W, 3), dtype=np.float32) + np.array(FUCHSIA, dtype=np.float32)
    core = np.clip(hull * (1 - shift(hull, 0, -2)), 0, 1)
    rgb = rgb * (1 - 0.5 * core[..., None]) + np.array([255, 150, 235]) * (0.5 * core[..., None])
    return to_img(rgb, a)


# ---------- build ----------

def build(seed):
    rng = np.random.default_rng(seed)
    hull = hull_mask()
    collar = collar_mask()
    dome = dome_mask()
    solid = np.maximum(hull, collar)
    layers = [
        ("glow", glow_layer(dome, hull)),
        ("halo", halo_layer(hull, collar)),
        ("body", body_layer(hull, collar, rng)),
        ("dome", dome_layer(dome, rng)),
        ("pores", pores_layer(hull)),
        ("rim", rim_layer(hull)),
    ]
    master = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for _, im in layers:
        master = Image.alpha_composite(master, im)
    return layers, master


def shrink(im):
    return im.resize((GW, GH), Image.LANCZOS)


def board(img, master, out_path):
    z4 = img.resize((GW * 4, GH * 4), Image.NEAREST)
    z4h = z4.copy()
    d = ImageDraw.Draw(z4h)
    d.rectangle([0, 10 * 4, GW * 4 - 1, GH * 4 - 1], outline=(120, 255, 200, 140))
    cx, cy, r = GW * 2, 10 * 4, 9 * 4
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 255, 200, 140))
    bw, bh = 20 + 40 + 20 + 160 + 20 + 160 + 20, 300
    bd = Image.new("RGBA", (bw, bh), BOARD_BG + (255,))
    font = ImageFont.load_default()
    dr = ImageDraw.Draw(bd)
    x = 20
    bd.alpha_composite(img, (x, 40))
    dr.text((x, 16), "1x", fill=TXT, font=font)
    x4 = 20 + 40 + 20
    bd.alpha_composite(z4, (x4, 40))
    dr.text((x4, 16), "4x", fill=TXT, font=font)
    x4h = x4 + 160 + 20
    bd.alpha_composite(z4h, (x4h, 40))
    dr.text((x4h, 16), "4x with hitbox (disc box, dome circle)", fill=TXT, font=font)
    bd.alpha_composite(master.resize((W // 2, H // 2), Image.LANCZOS), (20, 140))
    dr.text((20, 124), "master 320 x 160, shown at 1/2", fill=TXT, font=font)
    strip = Image.new("RGBA", (120, 40), (40, 20, 70, 255))
    strip.alpha_composite(img, (40, 10))
    bd.alpha_composite(strip, (20 + 160 + 20, 140))
    dr.text((20 + 160 + 20, 124), "1x on a purple glow", fill=TXT, font=font)
    bd.save(out_path)
    return bd.size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()

    SEED[0] = args.seed
    layers, master = build(args.seed)
    small = shrink(master)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    stem = f"ufo-d3-r{args.round}"
    small.save(out / f"{stem}.png")
    master.save(out / f"{stem}-master.png")
    board(small, master, out / f"{stem}-board.png")
    write_piskel(out / f"{stem}.piskel", "ufo-d3", [(n, [shrink(im)]) for n, im in layers])
    print(f"wrote {stem}: image {small.size}, master {master.size}")


if __name__ == "__main__":
    main()
