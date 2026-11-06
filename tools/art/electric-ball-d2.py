"""Electric ball, design 2 (urchin): a pale white-cyan orb with sharp spikes.

Look from docs/design/gdd/drifters/10-electric-ball.md (look_reference,
art_canvas, ball_size) and docs/design/gdd/12-art-and-audio.md (color language,
rules 2, 6, 8, 9). Still image only.

The game image is 24 x 24: the 16 px ball centred, spikes reaching toward the
edge. The master is drawn at 8x (192 x 192, ball 128 px across), with every
shape first drawn at 2x that and averaged down for clean edges, then shrunk
8x to game size with a premultiplied box filter.

Spikes are tapered, jagged white-cyan blades. Thin purple and fuchsia arcs
curl between them. Fuchsia stays thin (rule 6). The only fuchsia mass is the
thin rim on the ball's bottom edge (rule 8). No blue: the ship owns cobalt.

Outputs (in --out-dir, default staging/assets/sprites):
  electric-ball-d2-r<round>.png          24 x 24 game image
  electric-ball-d2-r<round>-master.png   192 x 192 master
  electric-ball-d2-r<round>-board.png    preview board for the UI Art Critic
  electric-ball-d2-r<round>.piskel       the game image as a one-frame Piskel file

Usage: python3 tools/art/electric-ball-d2.py [--round N] [--seed N] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"
NAME = "electric-ball-d2"

GAME = 24  # art_canvas
BALL = 16  # ball_size
UP = 8  # master scale
MASTER = GAME * UP  # 192
SS = 2  # drawing supersample on top of the master
BIG = MASTER * SS
C = MASTER / 2  # centre in master px
BALL_R = BALL * UP / 2  # 64

NAVY = (8, 10, 28)  # the game's dark background
CORE = (240, 253, 255)  # pale white-cyan
CYAN = (150, 235, 255)
PALE = (205, 246, 255)  # pale white-cyan, the ball's edge
SPIKE_TIP = (215, 245, 255)
ARC_PURPLE = (200, 135, 255)  # lifted so it holds against navy
CYAN_DEEP = (90, 190, 235)  # kept greenish-cyan, away from cobalt
PURPLE = (170, 80, 255)
FUCHSIA = (255, 70, 205)
RIM = (255, 90, 215)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def layer(color, mask, strength=1.0):
    """RGBA float array: color with the given L mask as alpha."""
    m = np.asarray(mask, dtype=np.float32) / 255.0 * strength
    out = np.zeros((*m.shape, 4), dtype=np.float32)
    out[..., :3] = np.array(color, dtype=np.float32) / 255.0
    out[..., 3] = m
    return out


def over(dst, src):
    """Alpha-composite src over dst (straight-alpha float RGBA)."""
    sa, da = src[..., 3:4], dst[..., 3:4]
    oa = sa + da * (1 - sa)
    rgb = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    return np.concatenate([rgb, oa], axis=-1)


def to_master(mask_big):
    return mask_big.resize((MASTER, MASTER), Image.LANCZOS)


def pt(angle, r, cx=C, cy=C, s=SS):
    return ((cx + math.cos(angle) * r) * s, (cy + math.sin(angle) * r) * s)


def spike_polygon(rng, angle, r0, r1, width, kinks=4):
    """Tapered jagged blade from radius r0 to r1 (master px), as a big-canvas polygon."""
    pts = []
    for i in range(kinks + 1):
        t = i / kinks
        r = r0 + (r1 - r0) * t
        jit = 0 if i in (0, kinks) else rng.uniform(-1, 1) * width * 0.55
        w = width * (1 - t) ** 0.8 * 0.5
        pts.append((r, jit, w))
    left = []
    right = []
    for r, jit, w in pts:
        left.append(pt(angle, r) if False else None)
    pts_l, pts_r = [], []
    for r, jit, w in pts:
        base = (math.cos(angle) * r, math.sin(angle) * r)
        nx, ny = -math.sin(angle), math.cos(angle)
        pts_l.append(((C + base[0] + nx * (jit + w)) * SS, (C + base[1] + ny * (jit + w)) * SS))
        pts_r.append(((C + base[0] + nx * (jit - w)) * SS, (C + base[1] + ny * (jit - w)) * SS))
    return pts_l + pts_r[::-1], [((C + math.cos(angle) * r + (-math.sin(angle)) * jit) * SS,
                                  (C + math.sin(angle) * r + math.cos(angle) * jit) * SS) for r, jit, w in pts]


def arc_points(a0, a1, r, wobble, rng, steps=24):
    out = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        rr = r + (0 if i in (0, steps) else rng.uniform(-wobble, wobble))
        out.append(pt(a, rr))
    return out


def draw_layers(seed):
    """Return [(name, RGBA float canvas)] bottom first: glow, arcs, spikes, body, rim."""
    rng = random.Random(seed)

    def blank():
        return Image.new("L", (BIG, BIG), 0)

    def empty():
        return np.zeros((MASTER, MASTER, 4), dtype=np.float32)

    yy, xx = np.mgrid[0:MASTER, 0:MASTER].astype(np.float32)
    rad = np.hypot(xx + 0.5 - C, yy + 0.5 - C)

    # 1. soft pre-rendered halo (rule 3): wide purple, tighter pale cyan inside it.
    glow = empty()
    g1 = blank()
    ImageDraw.Draw(g1).ellipse([(C - 80) * SS, (C - 80) * SS, (C + 80) * SS, (C + 80) * SS], fill=255)
    g1 = to_master(g1).filter(ImageFilter.GaussianBlur(10))
    glow = over(glow, layer(PURPLE, g1, 0.85))
    g2 = blank()
    ImageDraw.Draw(g2).ellipse([(C - 70) * SS, (C - 70) * SS, (C + 70) * SS, (C + 70) * SS], fill=255)
    g2 = to_master(g2).filter(ImageFilter.GaussianBlur(7))
    glow = over(glow, layer(CYAN, g2, 0.55))

    # 2. spikes: seven long blades, evenly spread with a little jitter, straight and sharp.
    n = 7
    spikes = []
    for i in range(n):
        a = 2 * math.pi * (i + rng.uniform(-0.12, 0.12)) / n + 0.35
        long_ = i % 2 == 0
        reach = rng.uniform(93, 95) if long_ else rng.uniform(86, 89)
        spikes.append((a, reach, rng.uniform(20, 22) if long_ else rng.uniform(17, 19)))
    spike_mask = blank()
    spine_mask = blank()
    sd = ImageDraw.Draw(spike_mask)
    pd = ImageDraw.Draw(spine_mask)
    for a, reach, width in spikes:
        poly, spine = spike_polygon(rng, a, 52, reach, width, kinks=3)
        sd.polygon(poly, fill=255)
        pd.line(spine, fill=255, width=int(2.4 * SS), joint="curve")
    spike_m = to_master(spike_mask)
    spine_m = to_master(spine_mask)
    t = np.clip((rad - 66) / 30, 0, 1)[..., None]
    root = np.array(CORE, np.float32) / 255
    tip = np.array(SPIKE_TIP, np.float32) / 255
    body = np.zeros((MASTER, MASTER, 4), np.float32)
    body[..., :3] = root * (1 - t) + tip * t
    body[..., 3] = np.asarray(spike_m, np.float32) / 255
    spk = over(empty(), body)
    spk = over(spk, layer(CORE, spine_m, 0.95))

    # 3. arcs: few, short, light purple with a pale core so they hold against navy.
    arc_p = blank()
    arc_f = blank()
    arc_c = blank()
    ap = ImageDraw.Draw(arc_p)
    af = ImageDraw.Draw(arc_f)
    ac = ImageDraw.Draw(arc_c)
    base = rng.uniform(0, 2 * math.pi)
    for k in range(4):
        gap_mid = base + 2 * math.pi * (k + 0.5) / 4 + 0.35
        span = rng.uniform(0.55, 0.75)
        r = rng.uniform(70, 80)
        pts = arc_points(gap_mid - span / 2, gap_mid + span / 2, r, 2.5, rng, steps=14)
        (af if k == 1 else ap).line(pts, fill=255, width=int(5 * SS), joint="curve")
        ac.line(pts, fill=255, width=int(2 * SS), joint="curve")
    arcs = empty()
    arcs = over(arcs, layer(ARC_PURPLE, to_master(arc_p).filter(ImageFilter.GaussianBlur(0.6)), 1.0))
    arcs = over(arcs, layer(FUCHSIA, to_master(arc_f).filter(ImageFilter.GaussianBlur(0.6)), 0.85))
    arcs = over(arcs, layer(CORE, to_master(arc_c), 0.85))

    # 4. the ball: pale white-cyan; a soft cyan only near the lower edge.
    ball = np.zeros((MASTER, MASTER, 4), np.float32)
    u = np.clip(rad / BALL_R, 0, 1)
    cols = np.zeros((MASTER, MASTER, 3), np.float32)
    stops = [(0.0, CORE), (0.55, CORE), (0.85, PALE), (1.0, CYAN)]
    for i in range(len(stops) - 1):
        u0, c0 = stops[i]
        u1, c1 = stops[i + 1]
        m = (u >= u0) & (u <= u1)
        f = ((u - u0) / (u1 - u0))[..., None]
        cols = np.where(m[..., None], np.array(c0, np.float32) * (1 - f) + np.array(c1, np.float32) * f, cols)
    # slightly deeper cyan toward the bottom only
    low = np.clip((yy + 0.5 - C) / BALL_R, 0, 1)[..., None] * np.clip((u[..., None] - 0.6) / 0.4, 0, 1)
    cols = cols * (1 - 0.5 * low) + np.array(CYAN_DEEP, np.float32) * 0.5 * low
    ball[..., :3] = cols / 255
    disc = blank()
    ImageDraw.Draw(disc).ellipse([(C - BALL_R) * SS, (C - BALL_R) * SS, (C + BALL_R) * SS, (C + BALL_R) * SS], fill=255)
    disc_m = to_master(disc)
    ball[..., 3] = np.asarray(disc_m, np.float32) / 255
    bodyc = over(empty(), ball)

    # 5. hard white highlight, upper left
    hl = blank()
    ImageDraw.Draw(hl).ellipse([(C - 32) * SS, (C - 38) * SS, (C - 10) * SS, (C - 18) * SS], fill=255)
    hl = to_master(hl).filter(ImageFilter.GaussianBlur(2.0))
    hl = ImageChops.multiply(hl, disc_m)
    bodyc = over(bodyc, layer((255, 255, 255), hl, 0.95))

    # 6. thin fuchsia rim, about 1 px at game size, bottom edge only (rule 8)
    rim = blank()
    ro = BALL_R
    ri = BALL_R - 2.5
    ImageDraw.Draw(rim).pieslice([(C - ro) * SS, (C - ro) * SS, (C + ro) * SS, (C + ro) * SS], 25, 155, fill=255)
    cut = blank()
    ImageDraw.Draw(cut).ellipse([(C - ri) * SS, (C - ri - 3.5) * SS, (C + ri) * SS, (C + ri - 3.5) * SS], fill=255)
    rim = ImageChops.subtract(rim, cut)
    rim = to_master(rim).filter(ImageFilter.GaussianBlur(0.9))
    rim = ImageChops.multiply(rim, disc_m)
    rimc = over(empty(), layer(RIM, rim, 0.9))

    return [("glow", glow), ("arcs", arcs), ("spikes", spk), ("body", bodyc), ("rim", rimc)]


def draw_master(seed):
    canvas = None
    for _, lay in draw_layers(seed):
        canvas = lay if canvas is None else over(canvas, lay)
    return canvas


def to_image(arr):
    a = np.clip(arr, 0, 1)
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGBA")


def shrink(master: Image.Image) -> Image.Image:
    """8x shrink, premultiplied so transparent pixels don't tint the edge."""
    a = np.asarray(master, np.float32) / 255
    pre = a.copy()
    pre[..., :3] *= a[..., 3:4]
    h = MASTER // UP
    pre = pre.reshape(h, UP, h, UP, 4).mean(axis=(1, 3))
    out = np.zeros_like(pre)
    al = pre[..., 3:4]
    out[..., :3] = np.where(al > 0, pre[..., :3] / np.maximum(al, 1e-6), 0)
    out[..., 3] = pre[..., 3]
    return to_image(out)


def board(game: Image.Image, master: Image.Image, rnd: int = 1) -> Image.Image:
    from PIL import ImageFont

    font = ImageFont.load_default()
    W, H = 660, 470
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(img)

    def paste(im, xy):
        img.alpha_composite(im, xy)

    d.text((16, 12), f"electric-ball-d2 r{rnd}  24x24, ball 16 px, urchin", fill=(200, 205, 225), font=font)
    # 1x on the dark background
    d.text((16, 40), "1x", fill=(200, 205, 225), font=font)
    paste(game, (16, 56))
    # frame row: the single frame (still image)
    d.text((80, 40), "frames (1)", fill=(200, 205, 225), font=font)
    paste(game, (80, 56))
    # 4x zoom, nearest, with the 16 px ball outline faint
    d.text((16, 100), "4x zoom (ring = 16 px ball, no hitbox)", fill=(200, 205, 225), font=font)
    z = game.resize((GAME * 4, GAME * 4), Image.NEAREST)
    zx, zy = 16, 120
    paste(z, (zx, zy))
    ring = Image.new("RGBA", z.size, (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([4 * 4, 4 * 4, 20 * 4 - 1, 20 * 4 - 1], outline=(255, 255, 255, 70))
    paste(ring, (zx, zy))
    # canvas edge
    d.rectangle([zx - 1, zy - 1, zx + z.width, zy + z.height], outline=(60, 70, 120))
    # 8x zoom
    d.text((220, 100), "8x zoom", fill=(200, 205, 225), font=font)
    z8 = game.resize((GAME * 8, GAME * 8), Image.NEAREST)
    paste(z8, (220, 120))
    d.rectangle([219, 119, 220 + z8.width, 120 + z8.height], outline=(60, 70, 120))
    # master, smooth
    d.text((430, 100), "master 192x192 (8x), smooth", fill=(200, 205, 225), font=font)
    paste(master, (430, 120))
    d.rectangle([429, 119, 430 + MASTER, 120 + MASTER], outline=(60, 70, 120))
    # over a lighter play-area patch and over the starfield-dim bg
    d.text((16, 330), "on a dim purple haze (background stays dimmer)", fill=(200, 205, 225), font=font)
    patch = Image.new("RGBA", (300, 110), (24, 14, 48, 255))
    paste(patch, (16, 350))
    for i, x in enumerate((40, 110, 180)):
        paste(game, (x, 380 - 10 * (i % 2)))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{NAME}-r{args.round}"

    master = to_image(draw_master(args.seed))
    game = shrink(master)
    master.save(out / f"{stem}-master.png")
    game.save(out / f"{stem}.png")
    board(game, master, args.round).convert("RGBA").save(out / f"{stem}-board.png")

    spec = importlib.util.spec_from_file_location("piskel_file", ROOT / "tools/art/piskel_file.py")
    pk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pk)
    layers = [(nm, [shrink(to_image(lay))]) for nm, lay in draw_layers(args.seed)]
    pk.write_piskel(out / f"{stem}.piskel", NAME, layers)
    print("wrote", stem, game.size, master.size)


if __name__ == "__main__":
    main()
