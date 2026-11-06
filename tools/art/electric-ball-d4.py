"""Electric ball, design 4 (storm core): a swirling vortex of electricity.

Look from docs/design/gdd/drifters/10-electric-ball.md (look_reference,
art_canvas, ball_size) and docs/design/gdd/12-art-and-audio.md (color language,
rules 2, 6, 8, 9). Still image only.

The game image is 24 x 24: the 16 px ball centred, arcs may reach the edge.
The master is drawn at 8x (192 x 192, ball 128 px across), every shape at 2x
that and averaged down, then shrunk 8x with a premultiplied box filter.

A dark violet disc holds a pale white-cyan core. Four tapering arms of
lightning curl out of the core in a spiral, thick and white-cyan at the root,
purple wrapping them, with one thin fuchsia arm among them (rule 6: thin
accents only). Two arms run on past the disc as arcs that reach the edge.
Fuchsia mass is only the rim on the bottom side (rule 8). No cobalt.

Outputs (in --out-dir, default staging/assets/sprites):
  electric-ball-d4-r<round>.png          24 x 24 game image
  electric-ball-d4-r<round>-master.png   192 x 192 master
  electric-ball-d4-r<round>-board.png    preview board for the UI Art Critic
  electric-ball-d4-r<round>.piskel       the game image as a one-frame Piskel file

Usage: python3 tools/art/electric-ball-d4.py [--round N] [--seed N] [--out-dir DIR]
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
NAME = "electric-ball-d4"

GAME = 24  # art_canvas
BALL = 16  # ball_size
UP = 8  # master scale
MASTER = GAME * UP  # 192
SS = 2  # drawing supersample on top of the master
BIG = MASTER * SS
C = MASTER / 2
BALL_R = BALL * UP / 2  # 64

NAVY = (8, 10, 28)
CORE = (244, 254, 255)  # pale white-cyan
CYAN = (150, 235, 255)
SHELL = (200, 244, 255)
CYAN_DEEP = (95, 195, 232)  # greenish cyan, away from cobalt
GLASS_IN = (40, 22, 100)  # glass interior, violet
GLASS_MID = (84, 46, 160)
PURPLE = (170, 80, 255)
ARC_PURPLE = (205, 145, 255)
FUCHSIA = (255, 70, 205)
RIM = (255, 90, 215)


def layer(color, mask, strength=1.0):
    m = np.asarray(mask, dtype=np.float32) / 255.0 * strength
    out = np.zeros((*m.shape, 4), dtype=np.float32)
    out[..., :3] = np.array(color, dtype=np.float32) / 255.0
    out[..., 3] = m
    return out


def over(dst, src):
    sa, da = src[..., 3:4], dst[..., 3:4]
    oa = sa + da * (1 - sa)
    rgb = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    return np.concatenate([rgb, oa], axis=-1)


def to_master(mask_big):
    return mask_big.resize((MASTER, MASTER), Image.LANCZOS)


def blank():
    return Image.new("L", (BIG, BIG), 0)


def empty():
    return np.zeros((MASTER, MASTER, 4), dtype=np.float32)


def P(x, y):
    return (x * SS, y * SS)


def bolt(rng, a, r0, r1, kinks, jitter, cx=C, cy=C):
    """Jagged polyline from radius r0 to r1 along angle a (master px, big-canvas coords)."""
    nx, ny = -math.sin(a), math.cos(a)
    pts = []
    for i in range(kinks + 1):
        t = i / kinks
        r = r0 + (r1 - r0) * t
        j = 0 if i == kinks else rng.uniform(-1, 1) * jitter * (0.4 + t)
        pts.append(P(cx + math.cos(a) * r + nx * j, cy + math.sin(a) * r + ny * j))
    return pts


def circle(d, x, y, r, fill=255):
    d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)


def spiral(rng, a0, r0, r1, turn, kinks, jitter):
    """Points of a jagged spiral arm: angle grows by `turn` rad from radius r0 to r1."""
    pts = []
    for i in range(kinks + 1):
        t = i / kinks
        r = r0 + (r1 - r0) * (t ** 0.85)
        a = a0 + turn * (t ** 0.8)
        j = 0 if i in (0, kinks) else rng.uniform(-1, 1) * jitter
        rr = r + j
        pts.append((C + math.cos(a) * rr, C + math.sin(a) * rr))
    return pts


def taper(draw, pts, w0, w1, steps=6):
    """Draw a polyline whose width goes from w0 to w1, as overlapping discs (master px)."""
    n = len(pts) - 1
    for i in range(n):
        for s in range(steps):
            f = s / steps
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
            t = (i + f) / n
            circle(draw, x, y, (w0 + (w1 - w0) * t) / 2)


def draw_layers(seed):
    """Return [(name, RGBA canvas)] bottom first: glow, disc, arms, fuchsia, core, rim."""
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:MASTER, 0:MASTER].astype(np.float32)
    rad = np.hypot(xx + 0.5 - C, yy + 0.5 - C)

    disc = blank()
    circle(ImageDraw.Draw(disc), C, C, BALL_R * 0.8)
    disc_m = to_master(disc)
    dm = np.asarray(disc_m, np.float32) / 255

    # 1. halo, purple, tight (rule 3: pre-rendered)
    glow = empty()
    g1 = blank()
    circle(ImageDraw.Draw(g1), C, C, 68)
    g1 = to_master(g1).filter(ImageFilter.GaussianBlur(6))
    glow = over(glow, layer(PURPLE, g1, 0.3))
    g2 = blank()
    circle(ImageDraw.Draw(g2), C, C, 52)
    g2 = to_master(g2).filter(ImageFilter.GaussianBlur(10))
    glow = over(glow, layer(CYAN, g2, 0.45))
    g3 = blank()
    circle(ImageDraw.Draw(g3), C, C, 66)
    g3 = to_master(g3).filter(ImageFilter.GaussianBlur(4))
    glow = over(glow, layer(CYAN, g3, 0.35))

    # 2. dark violet disc, a little brighter toward the core: the eye of the storm
    body = np.zeros((MASTER, MASTER, 4), np.float32)
    t = np.clip(rad / (BALL_R * 0.8), 0, 1)[..., None]
    cols = np.array((40, 110, 150), np.float32) * (1 - t) ** 1.5 + np.array((26, 14, 70), np.float32) * (1 - (1 - t) ** 1.5)
    body[..., :3] = cols / 255
    body[..., 3] = dm * 1.0
    # faint concentric swirl bands in the disc (purple), so the whole ball turns
    ang = np.arctan2(yy + 0.5 - C, xx + 0.5 - C)
    band = 0.5 + 0.5 * np.sin(ang * 3 - rad * 0.13)
    body[..., :3] += (np.array(PURPLE, np.float32) / 255 * 0.12) * (band * np.clip(rad / BALL_R, 0, 1) * 0.9)[..., None]
    body = np.clip(body, 0, 1)

    # 3. arms: counter-clockwise spirals out of the core
    base = rng.uniform(0, 2 * math.pi)
    arms = []
    n = 3
    for k in range(n):
        a0 = base + 2 * math.pi * k / n + rng.uniform(-0.1, 0.1)
        reach = 94 if k in (0, 1) else BALL_R - 4   # two arms run to the edge
        arms.append((a0, reach))
    yy_, xx_ = np.mgrid[0:MASTER, 0:MASTER].astype(np.float32)
    ap_, ac_, af_ = blank(), blank(), blank()
    apd, acd, afd = ImageDraw.Draw(ap_), ImageDraw.Draw(ac_), ImageDraw.Draw(af_)
    for k, (a0, reach) in enumerate(arms):
        pts = spiral(rng, a0, 8, reach, 2.0, 7, 1.6)
        taper_pts = pts
        taper(apd, taper_pts, 24, 11)
        taper(acd, taper_pts, 20, 9)
    # one thin fuchsia arm threading between the others, wound the same way
    fp = spiral(rng, base + math.pi / 4, 12, 70, 2.3, 8, 2.6)
    taper(afd, fp, 7, 3.5)
    afd.rectangle([0, 0, BIG, (C + 8) * SS], fill=0)  # rule 8: fuchsia only on the bottom side
    # a short purple side-arc off the second arm, to break the symmetry
    sp = spiral(rng, base + math.pi + 0.5, 30, 84, 1.3, 6, 3)

    arms_l = empty()
    arms_l = over(arms_l, layer(PURPLE, to_master(ap_).filter(ImageFilter.GaussianBlur(1.0)), 0.5))
    arms_l = over(arms_l, layer(CYAN, to_master(ac_).filter(ImageFilter.GaussianBlur(1.2)), 0.8))
    arms_l = over(arms_l, layer(CYAN, to_master(ac_), 1.0))
    # spikes: short jagged tips round the disc edge, cyan-white (spiky orb)
    sk = blank()
    skd = ImageDraw.Draw(sk)
    ns = 6
    sa0 = rng.uniform(0, 2 * math.pi)
    for i in range(ns):
        a = sa0 + 2 * math.pi * i / ns + rng.uniform(-0.08, 0.08)
        r_out = BALL_R + 3
        w = 0.3
        r_in = BALL_R * 0.72
        skd.polygon([P(C + math.cos(a - w) * r_in, C + math.sin(a - w) * r_in),
                     P(C + math.cos(a) * r_out, C + math.sin(a) * r_out),
                     P(C + math.cos(a + w) * r_in, C + math.sin(a + w) * r_in)], fill=255)
    skm = to_master(sk)
    arms_l = over(arms_l, layer(CYAN_DEEP, skm.filter(ImageFilter.GaussianBlur(1.0)), 0.9))
    arms_l = over(arms_l, layer(SHELL, skm, 0.85))
    fuch = over(empty(), layer(FUCHSIA, to_master(af_).filter(ImageFilter.GaussianBlur(0.8)), 0.85))

    # 4. core: pale white-cyan blob with a hot white center and a short halo
    cp, cc = blank(), blank()
    circle(ImageDraw.Draw(cp), C, C, 26)
    circle(ImageDraw.Draw(cc), C, C, 17)
    core = empty()
    core = over(core, layer(CYAN, to_master(cp).filter(ImageFilter.GaussianBlur(3)), 0.8))
    core = over(core, layer(CYAN, to_master(cp).filter(ImageFilter.GaussianBlur(5)), 0.0 + 0.55))
    core = over(core, layer(CORE, to_master(cc).filter(ImageFilter.GaussianBlur(1.5)), 1.0))
    hot = blank()
    circle(ImageDraw.Draw(hot), C, C, 8)
    core = over(core, layer((255, 255, 255), to_master(hot), 1.0))

    # 5. thin fuchsia rim, bottom side only (rule 8)
    rim = blank()
    ro, ri2 = BALL_R + 0.5, BALL_R - 3.5
    ImageDraw.Draw(rim).pieslice([(C - ro) * SS, (C - ro) * SS, (C + ro) * SS, (C + ro) * SS], 30, 150, fill=255)
    cut = blank()
    ImageDraw.Draw(cut).ellipse([(C - ri2) * SS, (C - ri2 - 3) * SS, (C + ri2) * SS, (C + ri2 - 3) * SS], fill=255)
    rim = ImageChops.subtract(rim, cut)
    rim = to_master(rim).filter(ImageFilter.GaussianBlur(0.9))
    rimc = over(empty(), layer(RIM, rim, 0.9))

    return [("glow", glow), ("disc", body), ("arms", arms_l), ("fuchsia", fuch), ("core", core), ("rim", rimc)]


def draw_master(seed):
    canvas = None
    for _, lay in draw_layers(seed):
        canvas = lay if canvas is None else over(canvas, lay)
    return canvas


def to_image(arr):
    a = np.clip(arr, 0, 1)
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGBA")


def shrink(master: Image.Image) -> Image.Image:
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
    TXT = (200, 205, 225)

    def paste(im, xy):
        img.alpha_composite(im, xy)

    d.text((16, 12), f"electric-ball-d4 r{rnd}  24x24, ball 16 px, storm core", fill=TXT, font=font)
    d.text((16, 40), "1x", fill=TXT, font=font)
    paste(game, (16, 56))
    d.text((80, 40), "frames (1)", fill=TXT, font=font)
    paste(game, (80, 56))
    d.text((16, 100), "4x zoom (ring = 16 px ball, no hitbox)", fill=TXT, font=font)
    z = game.resize((GAME * 4, GAME * 4), Image.NEAREST)
    zx, zy = 16, 120
    paste(z, (zx, zy))
    ring = Image.new("RGBA", z.size, (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([4 * 4, 4 * 4, 20 * 4 - 1, 20 * 4 - 1], outline=(255, 255, 255, 70))
    paste(ring, (zx, zy))
    d.rectangle([zx - 1, zy - 1, zx + z.width, zy + z.height], outline=(60, 70, 120))
    d.text((220, 100), "8x zoom", fill=TXT, font=font)
    z8 = game.resize((GAME * 8, GAME * 8), Image.NEAREST)
    paste(z8, (220, 120))
    d.rectangle([219, 119, 220 + z8.width, 120 + z8.height], outline=(60, 70, 120))
    d.text((430, 100), "master 192x192 (8x), smooth", fill=TXT, font=font)
    paste(master, (430, 120))
    d.rectangle([429, 119, 430 + MASTER, 120 + MASTER], outline=(60, 70, 120))
    d.text((16, 330), "on a dim purple haze (background stays dimmer)", fill=TXT, font=font)
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
