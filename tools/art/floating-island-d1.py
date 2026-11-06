"""Floating island, design 1 (rectangle): mossy crust.

Green moss on top, layered rock strata in the body, a darker green-brown edge,
and a thin fuchsia rim on the bottom side (brightest toward the bottom left,
where the black hole is). The ground fills the whole 320 x 120 box: there is no
transparent pixel, so the art matches the hitbox (the shape, exactly as drawn).

The master is drawn at 4x (1280 x 480) in four layers, then shrunk:
  rock   the strata, soft seams and pebbles, opaque
  moss   the moss cap, its drips, its shadow on the rock, the top highlight
  edge   the darker green-brown edge, laid over everything
  rim    the thin fuchsia rim and its faint spill on the bottom side

Sizes come from docs/design/gdd/drifters/05-floating-islands.md (art_canvas
320 x 120) and docs/design/gdd/12-art-and-audio.md (art_style: 4x for sprites
bigger than 64 px, rules 6 and 8 for the fuchsia). Colors: the placeholder
green (70, 160, 80) and edge (35, 90, 45) from the spec set the moss and the
edge; the rock browns are new and picked for this design.

Outputs (in --out-dir, default staging/assets/sprites), for round n:
  floating-island-d1-r<n>.png          320 x 120, opaque
  floating-island-d1-r<n>-master.png   1280 x 480
  floating-island-d1-r<n>-board.png    1x, 4x zoom with the hitbox outline
  floating-island-d1-r<n>.piskel       the four layers, one frame

Round 3 changes: no orange or cyan ovals (pebbles are shades of their own band),
no streak banding, no cracks, softer seams, strata shifted off pink.

Usage: python3 tools/art/floating-island-d1.py [--round N] [--seed S] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/art"))
from piskel_file import write_piskel  # noqa: E402

OUT = ROOT / "staging/assets/sprites"
NAME = "floating-island-d1"

GAME_W, GAME_H = 320, 120  # art_canvas
SCALE = 4  # art_style: 4x for sprites bigger than 64 px
W, H = GAME_W * SCALE, GAME_H * SCALE

NAVY = (8, 10, 28)  # the game's dark background, for the board

# Colors
MOSS_HI = np.array((128, 226, 96), float)
MOSS_MID = np.array((52, 178, 84), float)
MOSS_LOW = np.array((26, 110, 74), float)
EDGE_TOP = np.array((16, 62, 52), float)  # dark teal-green on the moss
EDGE_LOW = np.array((22, 24, 62), float)  # deep navy-violet on the rock
# Rock strata, top to bottom: (light, dark) of each band
STRATA = [
    ((214, 162, 104), (178, 126, 84)),   # warm tan
    ((190, 114, 84), (150, 84, 70)),     # clay (warm, away from the anomaly's pink)
    ((126, 92, 140), (92, 64, 114)),     # dusty mauve
    ((78, 74, 146), (56, 54, 118)),      # indigo violet
    ((52, 48, 112), (30, 30, 78)),       # deep navy violet
]
RIM = np.array((236, 50, 184), float)  # fuchsia, thin accent only


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def wave(rng, xs, amps, periods):
    """A sum of sines with random phases, over xs (master px)."""
    out = np.zeros_like(xs, dtype=float)
    for amp, per in zip(amps, periods):
        out += amp * np.sin(2 * np.pi * xs / per + rng.uniform(0, 2 * np.pi))
    return out


def stretched_noise(rng, sx, sy, lo=0.0, hi=1.0):
    """Noise stretched sx px wide and sy px tall per cell, size H x W."""
    small = rng.random((max(2, H // sy + 2), max(2, W // sx + 2))).astype(np.float32)
    img = Image.fromarray(small, mode="F").resize((W, H), Image.BICUBIC)
    return lo + (hi - lo) * np.asarray(img)


def to_img(rgb, alpha):
    arr = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def lerp3(a, b, t):
    return a[None, None, :] * (1 - t[..., None]) + b[None, None, :] * t[..., None]


def make_rock(rng, xs, yy, xx):
    """Layered strata with wavy seams, grain, pebbles, cracks."""
    bounds = [200, 262, 326, 392]
    curves = []
    for b in bounds:
        curves.append(b + wave(rng, xs, [10, 6, 3], [W * 0.9, W * 0.37, W * 0.16]))
    # band index and position inside the band (0 top .. 1 bottom)
    idx = np.zeros((H, W), int)
    top = np.zeros((H, W), float)
    bot = np.full((H, W), float(H))
    edges = [np.full(W, 0.0)] + curves + [np.full(W, float(H))]
    for i in range(len(edges) - 1):
        in_band = (yy >= edges[i][None, :]) & (yy < edges[i + 1][None, :])
        idx[in_band] = i
        top = np.where(in_band, edges[i][None, :], top)
        bot = np.where(in_band, edges[i + 1][None, :], bot)
    t = np.clip((yy - top) / np.maximum(bot - top, 1), 0, 1)

    light = np.array([s[0] for s in STRATA], float)[idx]
    dark = np.array([s[1] for s in STRATA], float)[idx]
    rgb = light * (1 - t[..., None]) + dark * t[..., None]

    # broad, soft mottling only (no streaks): the body stays smooth
    mott = stretched_noise(rng, 220, 60)
    rgb *= (0.97 + 0.06 * mott)[..., None]
    fine = rng.random((H, W)).astype(np.float32)
    rgb *= (0.98 + 0.04 * fine)[..., None]
    # green tint: moss stain bleeding into the upper strata
    stain = stretched_noise(rng, 140, 40) * smooth(300, 140, yy)
    rgb = rgb * (1 - 0.18 * stain[..., None]) + MOSS_LOW * (0.18 * stain[..., None])
    # overall: darker toward the bottom
    rgb *= (1.0 - 0.10 * smooth(160, H, yy))[..., None]

    # seams: dark line on each boundary, light lip just under it
    for c in curves:
        d = yy - c[None, :]
        seam = np.exp(-((d - 1) / 4.5) ** 2)
        lip = np.exp(-((d - 10) / 4.0) ** 2) * (d > 0) * 0.7
        rgb = rgb * (1 - 0.38 * seam[..., None]) + np.array((8, 10, 34)) * (0.38 * seam[..., None])
        rgb = rgb + np.array((40, 30, 36)) * lip[..., None]

    base_img = to_img(rgb, np.ones((H, W)))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # details, laid over the base
    dr = ImageDraw.Draw(img, "RGBA")

    # pebbles: soft lumps in a lighter or darker shade of the band they sit in
    # (no outline, no hot or cold accent colors), with a glossy hard highlight
    for _ in range(9):
        cx = float(rng.uniform(30, W - 30))
        cy = float(rng.uniform(215, H - 50))
        rx = float(rng.uniform(8, 20))
        ry = rx * float(rng.uniform(0.5, 0.75))
        local = rgb[int(cy), int(cx)]
        k = float(rng.choice([0.80, 1.16]))
        col = tuple(int(np.clip(c * k, 0, 255)) for c in local)
        dr.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (200,))
        dr.ellipse([cx - rx * 0.7, cy - ry * 0.8, cx + rx * 0.1, cy - ry * 0.2],
                   fill=(min(col[0] + 40, 255), min(col[1] + 40, 255), min(col[2] + 40, 255), 110))
    # mineral glints: tiny hard pale specks
    for _ in range(6):
        gx = float(rng.uniform(10, W - 10))
        gy = float(rng.uniform(205, H - 20))
        r = float(rng.uniform(1.5, 3.2))
        dr.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(236, 240, 220, 190))
    img = Image.alpha_composite(base_img, img)
    return img.filter(ImageFilter.GaussianBlur(1.2)), curves


def make_moss(rng, xs, yy, xx):
    """The moss cap: wavy lower border with drips, shadow under it, highlights."""
    base = 150 + wave(rng, xs, [9, 6, 4], [W * 0.8, W * 0.31, W * 0.12])
    drip = np.zeros(W)
    for cx in rng.uniform(40, W - 40, 11):
        depth = rng.uniform(18, 50)
        width = rng.uniform(22, 44)
        drip += depth * np.exp(-((xs - cx) / width) ** 2)
    bottom = base + np.minimum(drip, 60)

    d = yy - bottom[None, :]
    alpha = 1 - smooth(-2.5, 2.5, d)

    depth_t = np.clip(yy / np.maximum(bottom[None, :], 1), 0, 1)
    rgb = np.where(
        (depth_t < 0.35)[..., None],
        lerp3(MOSS_HI, MOSS_MID, smooth(0.0, 0.35, depth_t)),
        lerp3(MOSS_MID, MOSS_LOW, smooth(0.35, 1.0, depth_t)),
    )
    # clumpy mottling and blade strokes
    clump = stretched_noise(rng, 36, 22)
    rgb *= (0.84 + 0.30 * clump)[..., None]
    fine = rng.random((H, W)).astype(np.float32)
    rgb *= (0.985 + 0.03 * fine)[..., None]
    # darker rim at the moss's lower border
    rgb = rgb * (1 - 0.35 * smooth(-18, 0, d)[..., None])

    base_img = to_img(rgb, alpha)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # details, clipped to the moss below
    dr = ImageDraw.Draw(img, "RGBA")
    # grass blades: short bright strokes leaning left or right, near the top
    for _ in range(260):
        bx = float(rng.uniform(10, W - 10))
        by = float(rng.uniform(34, 110))
        ln = float(rng.uniform(10, 22))
        lean = float(rng.uniform(-7, 7))
        bright = int(rng.integers(0, 2))
        col = [(150, 224, 110, 150), (52, 128, 66, 150)][bright]
        dr.line([(bx, by), (bx + lean, by - ln)], fill=col, width=3)
    # moss pads: lighter round clumps
    for _ in range(30):
        cx = float(rng.uniform(10, W - 10))
        cy = float(rng.uniform(40, 130))
        r = float(rng.uniform(8, 20))
        dr.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], fill=(150, 220, 108, 40))
    # little pale flowers and spores (hard white-green highlights)
    for _ in range(12):
        fx = float(rng.uniform(14, W - 14))
        fy = float(rng.uniform(40, 120))
        r = float(rng.uniform(2.0, 3.6))
        dr.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(232, 250, 214, 230))
    img = Image.alpha_composite(base_img, img).filter(ImageFilter.GaussianBlur(0.6))
    # keep the moss's own border: details never reach below it
    img.putalpha(Image.fromarray((alpha * 255).astype(np.uint8), "L"))

    # shadow the moss casts on the rock below its border
    sh_alpha = np.exp(-((d - 14) / 16.0) ** 2) * (d > -2) * 0.6
    sh = to_img(np.zeros((H, W, 3)) + np.array((6, 10, 40)), sh_alpha)
    # glossy hard highlight just inside the top edge, in broken segments
    hl = np.zeros((H, W))
    seg = stretched_noise(rng, 150, 400)  # varies along x only
    on = smooth(0.38, 0.52, seg)
    hl = np.exp(-((yy - 30) / 3.0) ** 2) * on
    hl2 = np.exp(-((yy - 44) / 6.0) ** 2) * 0.22
    hl_img = to_img(np.zeros((H, W, 3)) + np.array((236, 255, 226)), np.clip(hl * 0.5 + hl2, 0, 1) * alpha)
    out = Image.alpha_composite(sh, img)
    return Image.alpha_composite(out, hl_img)


def make_edge(xs, yy, xx):
    """Darker green-brown edge, inside the box, fading inward."""
    d = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    soft = 1 - smooth(0, 30, d)
    hard = 1 - smooth(6, 14, d)
    alpha = np.clip(0.55 * soft + 0.45 * hard, 0, 1)
    t = smooth(110, 230, yy)  # green at the top, brown lower
    rgb = lerp3(EDGE_TOP, EDGE_LOW, t)
    # corners a little darker
    return to_img(rgb, alpha)


def make_rim(xs, yy, xx):
    """Thin fuchsia rim on the bottom side, brightest at the left."""
    dist = (H - 1 - yy).astype(float)
    strength = 0.35 + 0.55 * (1 - xx / W) ** 1.4
    core = (1 - smooth(2, 7, dist)) * strength  # about 1.5 px at game size
    spill = np.exp(-(dist / 22.0) ** 2) * 0.25 * strength
    alpha = np.clip(core + spill, 0, 1)
    rgb = np.broadcast_to(RIM, (H, W, 3)).copy()
    # a hot pale line in the very bottom pixels, left half only
    hot = (1 - smooth(1, 5, dist)) * (1 - smooth(0.0, 0.7, xx / W))
    rgb = rgb * (1 - 0.35 * hot[..., None]) + np.array((255, 190, 240)) * (0.35 * hot[..., None])
    return to_img(rgb, alpha)


def build(seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xs = np.arange(W, dtype=float)
    rock, _ = make_rock(rng, xs, yy, xx)
    moss = make_moss(rng, xs, yy, xx)
    edge = make_edge(xs, yy, xx)
    rim = make_rim(xs, yy, xx)
    master = rock
    for layer in (moss, edge, rim):
        master = Image.alpha_composite(master, layer)
    return master, [("rock", rock), ("moss", moss), ("edge", edge), ("rim", rim)]


def shrink(img):
    return img.resize((GAME_W, GAME_H), Image.LANCZOS)


def make_board(art, path):
    """1x on the dark background, the 4x zoom with the hitbox outline."""
    pad = 24
    zoom = art.resize((GAME_W * 4, GAME_H * 4), Image.NEAREST)
    bw = GAME_W * 4 + pad * 2
    bh = pad + GAME_H + pad + GAME_H * 4 + pad
    board = Image.new("RGBA", (bw, bh), NAVY + (255,))
    board.paste(art, (pad, pad), art)
    zy = pad + GAME_H + pad
    board.paste(zoom, (pad, zy), zoom)
    dr = ImageDraw.Draw(board, "RGBA")
    # hitbox: the rectangle itself, drawn faintly just outside the art
    dr.rectangle([pad - 1, zy - 1, pad + zoom.width, zy + zoom.height], outline=(139, 233, 255, 110))
    dr.rectangle([pad - 1, pad - 1, pad + GAME_W, pad + GAME_H], outline=(139, 233, 255, 70))
    dr.text((pad, 6), "1x", fill=(200, 200, 230, 255))
    dr.text((pad, zy - 16), "4x, hitbox outline = the whole 320 x 120 box", fill=(200, 200, 230, 255))
    board.save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    a = ap.parse_args(argv)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    stem = a.out_dir / f"{NAME}-r{a.round}"

    master, layers = build(a.seed)
    master.save(f"{stem}-master.png")
    art = shrink(master)
    # opaque: the ground fills the box (alpha stays 255, kept as an RGBA file)
    assert np.asarray(art)[..., 3].min() == 255
    art.save(f"{stem}.png")
    make_board(art, f"{stem}-board.png")
    write_piskel(f"{stem}.piskel", NAME, [(n, [shrink(im)]) for n, im in layers])
    print("wrote", stem)


if __name__ == "__main__":
    main()
