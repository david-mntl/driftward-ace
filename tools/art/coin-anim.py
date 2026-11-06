"""Coin animation strips from design 2 (the crystal with the swirl), round 3, common and rare.

Loads tools/art/coin-d2.py (not changed) and draws its coins frame by frame with the same seeds
(common 2, rare 3), so frame 0 of the swirl is the still. Over 8 frames that loop seamlessly:
  swirl   the galaxy inside (bar, arms, nucleus, stars) turns one full turn, 45 deg per frame
          (GDD 12 rule 13: steps of 45 deg or less). The crystal, cloud, ring, facets and rim stay put.
  glint   a soft white-pink glint slides down the lit left edge of the crystal, top to bottom,
          fading in at the top and out at the bottom so the wrap is calm
  rare    the star glint (upper left) twinkles: grows, peaks, fades; the small lower-right star
          twinkles four frames later
The hitbox (12 x 10 box, centered) is never touched: the crystal is drawn exactly as in the still.

Spec: docs/design/gdd/drifters/04-coin.md; tuning game/tuning/drifter_looks.json (coin.common and
coin.rare: 8 frames of 24 x 24, 6 ticks per frame, loop).

Outputs (staging/assets/sprites/anim/), for <stem> in coin_common, coin_rare:
  <stem>.png            192 x 24 strip, 8 frames of 24 x 24
  <stem>-master.png     1536 x 192 master strip (8x)
  <stem>-board.png      every frame at 1x, every frame at 4x with the hitbox drawn faintly
  <stem>-preview.gif    the loop at 4x on the dark background, 6 ticks per frame (100 ms)

Usage: python3 tools/art/coin-anim.py
"""

from __future__ import annotations

import importlib.util
import math
import warnings
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites/anim"

spec = importlib.util.spec_from_file_location("coin_d2", ROOT / "tools/art/coin-d2.py")
d2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d2)

FRAMES = 8  # Director's request
CANVAS = d2.CANVAS
M = d2.M
CX = CY = d2.CX
HITBOX = d2.HITBOX
BG = (10, 13, 31, 255)
GLINT = d2.GLINT

STATE = {"angle": 0.0, "tw": None}  # tw: None = the still; else {"main": f, "small": f}

_orig_galaxy = d2.galaxy
_orig_sparkle = d2.sparkle


def _rotated(arr, deg):
    if deg == 0:
        return arr
    img = Image.fromarray(arr.astype(np.float32), "F")
    out = img.rotate(deg, resample=Image.BICUBIC, center=(CX + 0.5, CY + 0.5))
    return np.clip(np.asarray(out, float), 0, None)


def galaxy(rng, rare):
    bright, disc = _orig_galaxy(rng, rare)
    # PIL turns counter-clockwise for a positive angle: the arms trail behind, as a galaxy's do
    return _rotated(bright, STATE["angle"]), disc


def sparkle(cx, cy, size, power=1.0):
    tw = STATE["tw"]
    if tw is None:
        return _orig_sparkle(cx, cy, size, power)
    if (cx, cy, size) == (63, 59, 16):  # the common coin's still glint: replaced by the sliding one
        return np.zeros((M, M))
    if (cx, cy, size) == (66, 60, 64):  # the rare star glint
        f = tw["main"]
        return _orig_sparkle(cx, cy, size * f, power * (0.55 + 0.45 * f))
    if (cx, cy, size) == (138, 134, 34):  # the small lower-right star
        f = tw["small"]
        return _orig_sparkle(cx, cy, size * f, power * (0.55 + 0.45 * f))
    return _orig_sparkle(cx, cy, size, power)


d2.galaxy = galaxy
d2.sparkle = sparkle


def twinkle(k, shift=0, floor=0.30):
    """1 at the peak, `floor` at the dimmest; grows, peaks, fades; periodic in FRAMES."""
    peak = 3 + shift
    c = 0.5 + 0.5 * math.cos(2 * math.pi * (k - peak) / FRAMES)
    return floor + (1 - floor) * c ** 1.5


# the lit left edge: top apex, upper-left corner, lower-left corner, bottom apex (master px)
_HW, _HR, _HH = d2.CRYSTAL_W * d2.UP / 2, d2.RECT_H * d2.UP / 2, d2.CRYSTAL_H * d2.UP / 2
EDGE = [(CX, CY - _HH), (CX - _HW, CY - _HR), (CX - _HW, CY + _HR), (CX, CY + _HH)]


def edge_point(t):
    """Point and unit tangent at fraction t (0..1) of the left-edge path."""
    segs = [(np.array(EDGE[i], float), np.array(EDGE[i + 1], float)) for i in range(3)]
    lens = [np.linalg.norm(b - a) for a, b in segs]
    d = t * sum(lens)
    for i, ((a, b), ln) in enumerate(zip(segs, lens)):
        if d <= ln or i == len(segs) - 1:
            u = np.clip(d / ln, 0, 1)
            tan = (b - a) / ln
            return a + (b - a) * u, tan
        d -= ln


def glint_layer(k):
    t = 0.07 + 0.86 * k / (FRAMES - 1)
    p, tan = edge_point(t)
    nrm = np.array([tan[1], -tan[0]])  # points to the right of the travel direction (down the left edge: inward)
    if nrm[0] < 0:
        nrm = -nrm
    c = p + nrm * 8.0
    dx, dy = d2.XX - c[0], d2.YY - c[1]
    u = dx * tan[0] + dy * tan[1]
    v = dx * nrm[0] + dy * nrm[1]
    env = math.sin(math.pi * (k + 0.5) / FRAMES) ** 1.3
    soft = np.exp(-((u / 16.0) ** 2) - (v / 7.0) ** 2)
    core = np.exp(-((u / 7.0) ** 2) - (v / 3.5) ** 2)
    a = np.clip((soft * 0.75 + core * 0.55) * env, 0, 1)
    arr = np.zeros((M, M, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = GLINT[0], GLINT[1], GLINT[2]
    arr[..., 3] = (a * 255).round().astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_frame(rare, k):
    STATE["angle"] = 45.0 * k
    STATE["tw"] = {"main": twinkle(k), "small": twinkle(k, shift=4, floor=0.35)} if rare else {}
    seed = 3 if rare else 2
    m = d2.draw_coin(rare, np.random.default_rng(seed))
    return Image.alpha_composite(m, glint_layer(k))


def draw_still(rare):
    STATE["angle"], STATE["tw"] = 0.0, None
    seed = 3 if rare else 2
    return d2.draw_coin(rare, np.random.default_rng(seed))


def shrink(m):
    return m.resize((CANVAS, CANVAS), Image.LANCZOS)


def box_share(frame, thr=128):
    a = np.asarray(frame)[..., 3]
    x0, y0 = (CANVAS - HITBOX[0]) // 2, (CANVAS - HITBOX[1]) // 2
    return float((a[y0:y0 + HITBOX[1], x0:x0 + HITBOX[0]] >= thr).mean())


def font(sz=11):
    return ImageFont.load_default(sz)


def make_board(name, frames, path):
    pad, z, gap = 12, 4, 10
    f = font()
    lab = (160, 170, 210, 255)
    w = pad * 2 + FRAMES * (CANVAS * z + gap)
    h = pad + 16 + CANVAS + pad + 16 + CANVAS * z + pad
    board = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(board)
    y = pad
    d.text((pad, y), f"{name}, 1x on the game background, every frame", font=f, fill=lab)
    y += 16
    for i, fr in enumerate(frames):
        board.alpha_composite(fr, (pad + i * (CANVAS * z + gap), y))
    y += CANVAS + pad
    d.text((pad, y), "4x, hitbox 12 x 10 drawn faintly", font=f, fill=lab)
    y += 16
    hx, hy = (CANVAS - HITBOX[0]) // 2, (CANVAS - HITBOX[1]) // 2
    for i, fr in enumerate(frames):
        x0 = pad + i * (CANVAS * z + gap)
        big = fr.resize((CANVAS * z, CANVAS * z), Image.NEAREST)
        tile = Image.new("RGBA", big.size, BG)
        tile.alpha_composite(big)
        ov = Image.new("RGBA", big.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rectangle([hx * z, hy * z, (hx + HITBOX[0]) * z - 1, (hy + HITBOX[1]) * z - 1],
                                     outline=(120, 255, 220, 120))
        tile.alpha_composite(ov)
        board.paste(tile, (x0, y))
        d.text((x0, y + CANVAS * z - 14), str(i), font=f, fill=lab)
    board.convert("RGB").save(path)


def make_gif(frames, path):
    z = 4
    imgs = []
    for fr in frames:
        tile = Image.new("RGBA", (CANVAS * z, CANVAS * z), BG)
        tile.alpha_composite(fr.resize((CANVAS * z, CANVAS * z), Image.NEAREST))
        imgs.append(tile.convert("RGB"))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=100, loop=0, disposal=2)  # 6 ticks = 100 ms


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for rare, stem in ((False, "coin_common"), (True, "coin_rare")):
        still = shrink(draw_still(rare))
        masters = [draw_frame(rare, k) for k in range(FRAMES)]
        frames = [shrink(m) for m in masters]
        strip = Image.new("RGBA", (CANVAS * FRAMES, CANVAS), (0, 0, 0, 0))
        mstrip = Image.new("RGBA", (M * FRAMES, M), (0, 0, 0, 0))
        for i, (fr, m) in enumerate(zip(frames, masters)):
            strip.paste(fr, (CANVAS * i, 0))
            mstrip.paste(m, (M * i, 0))
        strip.save(OUT / f"{stem}.png")
        mstrip.save(OUT / f"{stem}-master.png")
        make_board(stem, frames, OUT / f"{stem}-board.png")
        make_gif(frames, OUT / f"{stem}-preview.gif")
        print(stem, strip.size, "still box share %.3f" % box_share(still),
              "frames", ["%.3f" % box_share(fr) for fr in frames])


if __name__ == "__main__":
    main()
