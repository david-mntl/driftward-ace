"""Coin, design 2 (glassy): the crystal coin, common and rare side by side.

Spec: docs/design/gdd/drifters/04-coin.md (look_reference, art_canvas,
crystal_size, hitbox, palette) and docs/design/gdd/12-art-and-audio.md
(world brief, color language, rules 2, 6, 8, 9).

Direction: a more transparent crystal, a barred two-armed galaxy inside, a
dusty soft cloud around it, and the 22 x 8 ring across the middle.

Canvas: 24 x 24 per coin, drawn at 8x (192 x 192) and shrunk. The crystal is
12 x 20 and centered: a 12 x 10 rectangle with a 5 px triangle above and one
below. The hitbox is the rectangle only (12 x 10), drawn on the board and
never on the sprite.

Outputs (all in --out-dir, default staging/assets/sprites):
  coin-d2-r<n>.png         48 x 24 strip, common then rare
  coin-d2-r<n>-board.png   preview board: 1x, 4x with hitbox, 8x master view
  coin-d2-r<n>-master.png  384 x 192 master at 8x, before the shrink
  coin-d2-r<n>.piskel      the two game-size frames, for editing in Piskel

Usage: python3 tools/art/coin-d2.py [--round N] [--seed N] [--out-dir DIR]
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

# From the coin spec (palette, art_canvas, crystal_size, hitbox).
CANVAS = 24
UP = 8
M = CANVAS * UP  # master frame size, 192
LIT = np.array([200, 30, 90], float)
SHADE = np.array([70, 0, 60], float)
CORE = np.array([15, 0, 20], float)
PINK = np.array([255, 80, 150], float)
GLINT = np.array([255, 220, 240], float)
CRYSTAL_W, CRYSTAL_H, RECT_H = 12, 20, 10
RING_W, RING_H = 22, 8
HITBOX = (12, 10)

NAVY = (8, 10, 28)  # board background
TXT = (200, 205, 225)

YY, XX = np.mgrid[0:M, 0:M].astype(float)
CX = CY = M / 2


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur(arr, radius):
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "L")
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), float) / 255


class Stack:
    """Premultiplied float RGBA, composited bottom to top."""

    def __init__(self):
        self.rgb = np.zeros((M, M, 3))
        self.a = np.zeros((M, M))

    def over(self, color, alpha):
        alpha = np.clip(alpha, 0, 1)
        color = np.broadcast_to(np.asarray(color, float), (M, M, 3))
        self.rgb = color * alpha[..., None] + self.rgb * (1 - alpha[..., None])
        self.a = alpha + self.a * (1 - alpha)

    def image(self):
        a = np.maximum(self.a, 1e-6)[..., None]
        straight = np.clip(self.rgb / a, 0, 255)
        out = np.dstack([straight, np.clip(self.a, 0, 1) * 255])
        return Image.fromarray(out.round().astype(np.uint8), "RGBA")


def ramp(i, rare):
    """Galaxy brightness 0..1.3 to color: near-black, crimson, bright red-pink, glint."""
    i = np.asarray(i)[..., None]
    c = CORE + (LIT - CORE) * np.clip(i / 0.45, 0, 1)
    c = c + (PINK - LIT) * np.clip((i - 0.45) / 0.45, 0, 1)
    if rare:
        c = c + (GLINT - PINK) * np.clip((i - 0.9) / 0.4, 0, 1)
    return c


def crystal_mask():
    """The 12 x 20 crystal: rectangle with a triangle above and below."""
    half_w = CRYSTAL_W * UP / 2
    half_r = RECT_H * UP / 2
    half_h = CRYSTAL_H * UP / 2
    pts = [
        (CX, CY - half_h), (CX + half_w, CY - half_r), (CX + half_w, CY + half_r),
        (CX, CY + half_h), (CX - half_w, CY + half_r), (CX - half_w, CY - half_r),
    ]
    img = Image.new("L", (M, M), 0)
    ImageDraw.Draw(img).polygon(pts, fill=255)
    return img, pts


def cloud(rng, rare):
    """A dusty soft cloud inside the 24 x 24 square."""
    n = np.zeros((M, M))
    amp, total = 1.0, 0.0
    for cells in (4, 7, 13, 26):
        low = rng.random((cells, cells))
        big = Image.fromarray((low * 255).astype(np.uint8), "L").resize((M, M), Image.BICUBIC)
        n += amp * np.asarray(big, float) / 255
        total += amp
        amp *= 0.55
    n = smooth(0.35, 0.8, n / total)
    dx, dy = (XX - CX) / 84, (YY - CY) / 74
    env = np.exp(-(dx * dx + dy * dy) * 1.6)
    edge = np.minimum.reduce([XX, YY, M - 1 - XX, M - 1 - YY])
    env *= smooth(4, 26, edge)
    strength = 0.8 if rare else 0.6
    alpha = env * (0.25 + 0.75 * n) * strength
    mix = smooth(0.2, 0.9, n * env * 1.6)[..., None]
    color = SHADE + (LIT - SHADE) * mix
    # fine dust grains
    grains = np.zeros((M, M))
    for _ in range(170 if rare else 120):
        gx, gy = rng.normal(CX, 52), rng.normal(CY, 50)
        if 6 < gx < M - 6 and 6 < gy < M - 6:
            grains[int(gy) - 1:int(gy) + 2, int(gx) - 1:int(gx) + 2] = rng.uniform(0.4, 1.0)
    grains = blur(grains, 2.0) * 2.2
    return color, alpha, grains * env


def ring_field():
    """Distance (master px) from the 22 x 8 ellipse, and the vertical offset."""
    a, b = RING_W * UP / 2, RING_H * UP / 2
    dx, dy = XX - CX, YY - CY
    d = np.sqrt((dx / a) ** 2 + (dy / b) ** 2) + 1e-9
    grad = np.sqrt((dx / (a * a * d)) ** 2 + (dy / (b * b * d)) ** 2)
    return (d - 1) / grad, dy


def galaxy(rng, rare):
    """Barred two-armed galaxy: brightness field and disc alpha."""
    bar_len = 21.0
    reach = 37.0
    theta = math.radians(-28)
    u = (XX - CX) * math.cos(theta) + (YY - CY) * math.sin(theta)
    v = -(XX - CX) * math.sin(theta) + (YY - CY) * math.cos(theta)
    bar = np.exp(-((u / bar_len) ** 4) - (v / 6.6) ** 2) * 1.9
    bright = bar.copy()
    steps = 140
    for k in (0, 1):
        phi0 = theta + k * math.pi
        for t in np.linspace(0, 1, steps):
            r = bar_len * 0.9 + (reach - bar_len * 0.9) * t ** 0.85
            ang = phi0 + 1.75 * t
            px, py = CX + r * math.cos(ang), CY + r * math.sin(ang)
            sigma = 4.4 - 1.6 * t
            peak = 1.2 - 0.6 * t
            w = peak * 0.36 / (2.507 * sigma)
            bright += w * np.exp(-((XX - px) ** 2 + (YY - py) ** 2) / (2 * sigma ** 2))
    nucleus = np.exp(-((XX - CX) ** 2 + (YY - CY) ** 2) / (2 * 5.0 ** 2))
    bright += nucleus * (0.45 if rare else 0.18)
    # a few stars in the disc
    for _ in range(9):
        r, ang = reach * math.sqrt(rng.uniform(0.2, 1.0)), rng.uniform(0, 2 * math.pi)
        px, py = CX + r * math.cos(ang), CY + r * math.sin(ang)
        bright += rng.uniform(0.3, 0.6) * np.exp(-((XX - px) ** 2 + (YY - py) ** 2) / (2 * 2.6 ** 2))
    dd = np.sqrt((XX - CX) ** 2 + (YY - CY) ** 2)
    disc = np.exp(-((dd / 44.0) ** 2)) * 0.55
    return bright, disc


def sparkle(cx, cy, size, power=1.0):
    """A four-point glint, a soft cross with a bright center."""
    dx, dy = XX - cx, YY - cy
    h = np.exp(-(dy / (size * 0.10)) ** 2) * np.exp(-np.abs(dx) / (size * 0.42))
    v = np.exp(-(dx / (size * 0.10)) ** 2) * np.exp(-np.abs(dy) / (size * 0.42))
    c = np.exp(-(dx * dx + dy * dy) / (2 * (size * 0.14) ** 2))
    return np.clip((h + v) * 0.8 + c, 0, 1) * power


def draw_coin(rare, rng):
    st = Stack()
    mask_img, pts = crystal_mask()
    mask = np.asarray(mask_img.filter(ImageFilter.GaussianBlur(0.8)), float) / 255
    inner = np.asarray(mask_img.filter(ImageFilter.MinFilter(11)).filter(ImageFilter.GaussianBlur(1.2)), float) / 255
    rim = np.clip(mask - inner, 0, 1)

    sd, ring_dy = ring_field()
    ring_core = np.exp(-((sd / 5.0) ** 2))
    ring_halo = np.exp(-((sd / 20.0) ** 2))
    front = smooth(-20, 20, ring_dy)  # lower half of the ring passes in front

    # soft outer glow, pre-rendered (rule 3), kept inside the canvas
    edge = np.minimum.reduce([XX, YY, M - 1 - XX, M - 1 - YY])
    glow_src = np.maximum(blur(mask, 16), ring_halo * 0.7)
    glow = glow_src * smooth(2, 22, edge) * (0.62 if rare else 0.2)
    st.over(PINK * 0.8, glow)

    # dusty cloud
    c_color, c_alpha, c_grain = cloud(rng, rare)
    st.over(c_color, c_alpha)
    st.over(PINK, np.clip(c_grain, 0, 1) * (0.55 if rare else 0.4))

    # ring, back half: seen through the glass, dimmer
    back_a = (ring_core * 0.85 + ring_halo * 0.12) * (1 - front) * (0.8 if rare else 0.65)
    st.over(LIT + (PINK - LIT) * 0.35, back_a * 0.9)

    # crystal body: translucent, lit side left, shade side right
    t = (XX - CX) / (CRYSTAL_W * UP / 2)
    ty = (YY - CY) / (CRYSTAL_H * UP / 2)
    # crimson on the upper-left faces, black-purple on the right and top faces
    side = smooth(-0.25, 0.3, t + 0.25 * ty)
    side = np.clip(side + 0.45 * smooth(-0.55, -1.0, ty) * smooth(-0.6, 0.0, t), 0, 1)[..., None]
    body_color = (LIT * 1.05) + (SHADE * 0.55 - LIT * 1.05) * side
    body_a = (0.9 - 0.04 * side[..., 0]) * mask
    st.over(body_color, body_a)
    # a near-black pool around the galaxy so the core reads dark at 1x
    pool = np.exp(-(((XX - CX) / 50) ** 2 + ((YY - CY) / 52) ** 2) ** 1.5)
    st.over(CORE, pool * mask * 0.95)

    # galaxy inside the glass
    bright, disc = galaxy(rng, rare)
    g_a = np.maximum(disc * 1.3, np.clip(bright * 1.35, 0, 1)) * mask
    st.over(ramp(bright, rare), g_a)

    # facets: girdle lines, center edge, and the lit-side refraction band
    lines = Image.new("L", (M, M), 0)
    ld = ImageDraw.Draw(lines)
    top, bot = pts[0], pts[3]
    ld.line([pts[5], pts[1]], fill=200, width=3)
    ld.line([pts[4], pts[2]], fill=200, width=3)
    ld.line([top, (CX, CY - RECT_H * UP / 2)], fill=140, width=3)
    ld.line([bot, (CX, CY + RECT_H * UP / 2)], fill=140, width=3)
    ld.line([top, pts[5]], fill=120, width=3)
    ld.line([bot, pts[4]], fill=120, width=3)
    facets = np.asarray(lines.filter(ImageFilter.GaussianBlur(1.6)), float) / 255
    st.over(np.array([255, 150, 200]), facets * mask * (0.16 if rare else 0.10))
    band = np.exp(-(((XX - 66) + (YY - 60) * 0.1) / 5.0) ** 2) * smooth(52, 70, YY) * (1 - smooth(112, 134, YY))
    st.over(np.array([255, 190, 220]), band * mask * (0.22 if rare else 0.12))
    # shade side: a faint cool echo along the inner right edge
    echo = np.exp(-(((XX - 128) / 5.0) ** 2)) * smooth(58, 74, YY) * (1 - smooth(120, 136, YY))
    st.over(np.array([160, 60, 200]), echo * mask * 0.28)

    # rim: thin fuchsia, strongest on the bottom side (rule 8)
    bottom = smooth(80, 176, YY)
    leftlit = smooth(CX, CX - 48, XX)
    top_rim = LIT * 0.85 + SHADE * 0.15
    rim_color = top_rim[None, None, :] * (1 - bottom[..., None]) + PINK * bottom[..., None]
    rim_color = rim_color + (GLINT - PINK) * (bottom * 0.45)[..., None]
    rim_color = rim_color + (GLINT - top_rim) * (leftlit * (1 - bottom) * 0.12)[..., None]
    rightdark = smooth(CX, CX + 40, XX) * (1 - bottom)
    rim_color = rim_color * (1 - rightdark[..., None] * 0.6) + SHADE * (rightdark[..., None] * 0.6)
    st.over(rim_color, rim * (0.75 + 0.25 * bottom))
    # bottom rim light: a bright line along the two lower edges (rule 8)
    st.over(GLINT, rim * smooth(120, 170, YY) * (0.55 if rare else 0.35))

    # dark gap around the front ring where it crosses the glass
    gap = np.exp(-((sd / 9.5) ** 4)) * front * mask
    st.over(CORE, gap * 0.85)
    # ring, front half: bright, over the glass
    front_a = (ring_core * 0.95 + ring_halo * 0.14) * front
    ring_color = LIT + (PINK - LIT) * (0.55 + 0.45 * front)[..., None]
    ring_color = ring_color + (GLINT - PINK) * (ring_core * 0.2 * front * smooth(CY, CY + 36, YY))[..., None]
    if rare:
        ring_color = ring_color + (GLINT - PINK) * (ring_core * 0.35 * front)[..., None]
    st.over(ring_color, front_a)
    # the ring's top half where it leaves the crystal sides stays thin
    # glints
    if rare:
        st.over(PINK, blur(sparkle(66, 60, 64), 9) * 0.7)
        st.over(GLINT, sparkle(66, 60, 64, 1.0))
        st.over(GLINT, sparkle(138, 134, 34, 0.95))
        st.over(GLINT, sparkle(100, 100, 20, 0.8) * mask)
    else:
        st.over(np.array([255, 190, 220]), sparkle(63, 59, 16, 0.55))
    return st.image()


def shrink(master):
    return master.resize((CANVAS, CANVAS), Image.LANCZOS)


def board(frames, masters, path):
    pad = 10
    label_font = ImageFont.load_default(11)
    names = ["common", "rare"]
    w4 = CANVAS * 4
    w8 = CANVAS * 8
    width = pad * 4 + w8 * 2 + 2 * pad
    rows_h = [CANVAS + 14, w4 + 30, w8 + 14]
    height = pad + sum(rows_h) + pad * 4
    img = Image.new("RGBA", (width, height), NAVY + (255,))
    d = ImageDraw.Draw(img)
    y = pad
    # 1x row
    d.text((pad, y), "1x on the game background", font=label_font, fill=TXT)
    for i, f in enumerate(frames):
        img.alpha_composite(f, (pad + i * (CANVAS + 12), y + 14))
    y += rows_h[0] + pad
    # 4x row with hitbox
    d.text((pad, y), "4x zoom, hitbox 12 x 10 (faint outline)", font=label_font, fill=TXT)
    for i, f in enumerate(frames):
        x0 = pad + i * (w4 + 14)
        big = f.resize((w4, w4), Image.NEAREST)
        img.alpha_composite(big, (x0, y + 14))
        hx, hy = (CANVAS - HITBOX[0]) * 2, (CANVAS - HITBOX[1]) * 2
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rectangle(
            [x0 + hx, y + 14 + hy, x0 + hx + HITBOX[0] * 4 - 1, y + 14 + hy + HITBOX[1] * 4 - 1],
            outline=(120, 255, 220, 110),
        )
        img.alpha_composite(ov)
        d.text((x0, y + 14 + w4 + 2), names[i], font=label_font, fill=TXT)
    y += rows_h[1] + pad
    # 8x master view
    d.text((pad, y), "8x master (before the shrink), common then rare", font=label_font, fill=TXT)
    for i, m in enumerate(masters):
        img.alpha_composite(m.resize((w8, w8), Image.LANCZOS), (pad + i * (w8 + pad), y + 14))
    img.convert("RGBA").save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=3)
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--out-dir", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"coin-d2-r{args.round}"

    masters = [draw_coin(False, np.random.default_rng(args.seed)),
               draw_coin(True, np.random.default_rng(args.seed + 1))]
    frames = [shrink(m) for m in masters]

    strip = Image.new("RGBA", (CANVAS * 2, CANVAS), (0, 0, 0, 0))
    master_strip = Image.new("RGBA", (M * 2, M), (0, 0, 0, 0))
    for i, (f, m) in enumerate(zip(frames, masters)):
        strip.paste(f, (CANVAS * i, 0))
        master_strip.paste(m, (M * i, 0))
    strip.save(out / f"{stem}.png")
    master_strip.save(out / f"{stem}-master.png")
    board(frames, masters, out / f"{stem}-board.png")
    write_piskel(out / f"{stem}.piskel", "coin-d2", [("coin", frames)])
    print("wrote", out / f"{stem}.png", strip.size)


if __name__ == "__main__":
    main()
