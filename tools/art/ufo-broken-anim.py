"""UFO, broken saucer: 8 animation frames, played in random order.

Built on the picked design, ufo-d2-r2 (staging/assets/sprites/ufo-d2-r2-master.png).
tools/art/ufo-d2.py is loaded with importlib (the file name has a hyphen) and
its drawing is reused: its layer code re-draws the port lights, and its
helpers do the compositing. NOTE: ufo-d2.py now draws round 3 (wider glow,
other cracks and bites). Round 2 is not reproducible from it, so the staged
round 2 master is the base of every frame, pixel for pixel. The port-light
zone of the belly is re-composited from ufo-d2.py's layers, which match the
round 2 master there (checked: the baseline light levels give a zero diff).

Every frame is a self-contained state of a dying machine, so any order works:
  - port lights: each lamp lit, dim or dead, unevenly from frame to frame
  - sparks popping from the torn corner, the left chip and the belly notch
  - one thin smoke wisp from the tear (a second, shorter one in some frames)
  - the dome glint flickers: a bloom on the main glint and a small star
The hull and dome stay where they are: the silhouette is the round 2 silhouette
in every frame, and all motion only adds light, sparks and smoke on top.

Outputs, in --out-dir (default staging/assets/sprites/anim):
  ufo_broken.png            320 x 20 strip, 8 frames of 40 x 20
  ufo_broken-master.png     2560 x 160 master strip (8x)
  ufo_broken-board.png      every frame at 1x, then at 4x with the hitbox
  ufo_broken-preview.gif    the loop at 4x, random order, 3 ticks per frame

Usage: python3 tools/art/ufo-broken-anim.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites/anim"
R2_MASTER = ROOT / "staging/assets/sprites/ufo-d2-r2-master.png"
R2_STILL = ROOT / "staging/assets/sprites/ufo-d2-r2.png"

NAME = "ufo_broken"
FRAMES = 8
TICKS = 3  # ticks per frame (1 tick = 1/60 s)
GW, GH = 40, 20
UP = 8
W, H = GW * UP, GH * UP

BOARD_BG = (10, 13, 31)
TXT = (200, 205, 225)

# ---------- load the design script ----------
_spec = importlib.util.spec_from_file_location("ufo_d2", ROOT / "tools/art/ufo-d2.py")
d2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d2)


def fit_xy(x, y):
    """Design-canvas point -> master point after ufo-d2's 90% fit about the bottom centre."""
    return 0.9 * x + 16, 0.9 * y + 8


# ---------- port lights (levels per lamp) ----------
LAMP_X = [40, 80, 120, 160, 200, 240, 280]
LAMP_KIND = ["amber", "dead", "amber", "yellow", "dead", "amber", "dead"]
BASE_LEVELS = [1, 0, 1, 1, 0, 1, 0]

# The lamp at x 200 sits in the belly notch, which ufo-d2.py (round 3) draws bigger than the
# round 2 master, so that lamp stays dead in every frame (as in the still).
# one row per frame; 1 = fully lit, 0 = dead socket, between = a sputtering lamp.
# Total light stays about the same in every frame, so any order looks the same kind of broken.
FRAME_LEVELS = [
    [1.0, 0.0, 0.0, 1.0, 0.0, 0.45, 0.0],
    [0.0, 0.0, 1.0, 0.35, 0.0, 1.0, 0.6],
    [0.5, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.6, 1.0, 0.0, 1.0, 0.0],
    [1.0, 0.4, 1.0, 0.0, 0.0, 0.0, 1.0],
    [0.3, 0.0, 0.0, 0.8, 0.0, 0.5, 0.0],
    [0.0, 1.0, 0.4, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0, 0.5, 0.0, 0.0, 1.0],
]


def lights_levels(hull, levels):
    """Same drawing as ufo-d2.lights_layer, with a level per lamp (1 lit, 0 dead).

    At the baseline levels this is identical to ufo-d2.lights_layer.
    """
    XX, YY = d2.XX, d2.YY
    rgb = np.zeros((d2.H, d2.W, 3), dtype=np.float32)
    alpha = np.zeros((d2.H, d2.W), dtype=np.float32)

    def put(color, a):
        nonlocal rgb, alpha
        out_a = a + alpha * (1 - a)
        rgb = (np.array(color, dtype=np.float32) * a[..., None] + rgb * (alpha * (1 - a))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
        alpha = out_a

    for x, kind, v in zip(LAMP_X, LAMP_KIND, levels):
        yy = 128 + 4 * math.sin(x / 320 * math.pi) * -1 + 3
        if v < 1.0:
            # dead socket, weaker as the lamp comes back
            w = 1.0 - v
            core = np.clip(1 - np.hypot(XX - x, YY - yy) / 7.5, 0, 1) ** 0.5
            put((18, 16, 28), core * 0.95 * w)
            c = d2.mask_from_draw(lambda d: d.line([(x - 6, yy - 6), (x + 1, yy + 1), (x + 6, yy - 1)], fill=255, width=2), 0.5)
            put((120, 110, 130), c * 0.5 * w)
        if v > 0.0:
            col = d2.YELLOW if kind == "yellow" else d2.AMBER
            halo = d2.glow(x, yy, 22, None, 2.0) * 0.45
            put(col, halo * v)
            core = np.clip(1 - np.hypot(XX - x, YY - yy) / 8.5, 0, 1) ** 0.4
            put(col, core * v)
            put((255, 250, 220), np.clip(1 - np.hypot(XX - x, YY - yy) / 4.0, 0, 1) * v)
    alpha = alpha * hull
    return d2.to_img(rgb, alpha)


# ---------- sparks, smoke, glint ----------
SPARK_SRC = {
    "tear": (fit_xy(262, 100), (-150, -25)),  # torn upper right corner, sparks fly up and out
    "chip": (fit_xy(34, 106), (195, 255)),  # chipped left tip, sparks fly left and up
    "notch": (fit_xy(205, 140), (0, 360)),  # belly notch: short crackle in any direction, close
}

# per frame: [(source, pop flash 0..1)] and the sparks (source, angle deg, length, head size, brightness)
SPARKS = [
    [("tear", 1.0, [(-120, 30, 5, 1.0), (-70, 22, 4, 0.8), (-35, 36, 4, 0.7)]), ("notch", 0.0, [(20, 12, 3, 0.8)])],
    [("chip", 1.0, [(-170, 28, 5, 1.0), (-130, 34, 4, 0.8)]), ("tear", 0.0, [(-95, 18, 4, 0.8)])],
    [("notch", 1.0, [(150, 14, 3, 1.0), (35, 12, 3, 0.8), (-80, 10, 3, 0.7), (200, 12, 3, 0.8)])],
    [("tear", 0.5, [(-140, 38, 5, 0.9), (-55, 28, 4, 1.0)]), ("chip", 0.0, [(-100, 18, 4, 0.8), (-150, 24, 4, 0.7)])],
    [("chip", 0.6, [(-110, 36, 5, 1.0)]), ("notch", 1.0, [(-30, 13, 3, 0.9), (170, 11, 3, 0.9)])],
    [("tear", 1.0, [(-80, 38, 5, 1.0), (-110, 26, 4, 0.9), (-20, 24, 4, 0.8), (-150, 20, 4, 0.7)])],
    [("notch", 0.4, [(60, 12, 3, 0.8)]), ("chip", 1.0, [(-155, 30, 5, 1.0), (-120, 38, 4, 0.8), (-90, 20, 4, 0.7)])],
    [("tear", 0.7, [(-100, 24, 4, 0.9), (-45, 30, 4, 0.8)]), ("notch", 0.7, [(-60, 12, 3, 0.9), (110, 11, 3, 0.8)])],
]

# smoke wisp from the tear: (phase, sway, lean, height, thickness); second wisp from the chip or None
SMOKE = [
    (0.0, 9, -4, 46, 1.0, None),
    (1.3, 12, -9, 40, 0.9, (0.5, 6, 3, 24)),
    (2.6, 7, 3, 50, 1.1, None),
    (4.0, 13, -12, 36, 1.0, (2.0, 5, -4, 28)),
    (5.1, 8, -2, 44, 0.9, None),
    (0.7, 11, 6, 48, 1.1, (3.5, 6, 4, 22)),
    (3.3, 10, -7, 38, 1.0, None),
    (2.0, 6, -1, 52, 1.0, (1.2, 6, 2, 26)),
]

# glint: (bloom on the main glint 0..1, star on the small glint 0..1)
GLINT = [(1.0, 0.0), (0.0, 1.0), (0.4, 0.0), (0.0, 0.0), (0.7, 1.0), (0.2, 0.0), (1.0, 0.0), (0.0, 0.6)]
GLINT_MAIN = fit_xy(123, 31)
GLINT_STAR = fit_xy(157, 22)


def draw_sparks(frame_idx):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd, cd = ImageDraw.Draw(glow), ImageDraw.Draw(core)
    for src, pop, sparks in SPARKS[frame_idx]:
        (sx, sy), _ = SPARK_SRC[src]
        if pop > 0:
            r = (22 if src != "notch" else 14) * (0.6 + 0.4 * pop)
            gd.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 170, 50, int(230 * pop)))
            r2 = r * 0.35
            cd.ellipse([sx - r2, sy - r2, sx + r2, sy + r2], fill=(255, 245, 200, int(255 * pop)))
        for ang, ln, head, br in sparks:
            a = math.radians(ang)
            ex, ey = sx + math.cos(a) * ln, sy + math.sin(a) * ln
            # streak: thin at the source, thick and pale at the head
            steps = 6
            for i in range(steps):
                t0, t1 = i / steps, (i + 1) / steps
                p0 = (sx + (ex - sx) * t0, sy + (ey - sy) * t0)
                p1 = (sx + (ex - sx) * t1, sy + (ey - sy) * t1)
                col = (255, int(130 + 110 * t1), int(40 + 150 * t1), int(255 * br))
                gd.line([p0, p1], fill=(255, 150, 40, int(170 * br * t1)), width=int(2 + head * 2.2 * t1))
                cd.line([p0, p1], fill=col, width=max(2, int(1.5 + head * 0.8 * t1)))
            hr = head * 0.6
            cd.ellipse([ex - hr, ey - hr, ex + hr, ey + hr], fill=(255, 252, 225, int(255 * br)))
    glow = glow.filter(ImageFilter.GaussianBlur(3.5))
    core = core.filter(ImageFilter.GaussianBlur(0.7))
    return Image.alpha_composite(glow, core)


def draw_wisp(points, width0, alpha0):
    """A thin smoke wisp along points: soft puffs that grow, thin out and fade toward the top."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n = len(points) - 1
    for i in range(n + 1):
        t = i / n
        r = width0 * (0.55 + 0.7 * t)
        a = int(255 * min(1.0, alpha0 * (1.15 - t)))
        x, y = points[i]
        d.ellipse([x - r, y - r, x + r, y + r], fill=(215, 205, 225, a))
    return im.filter(ImageFilter.GaussianBlur(1.6))


def smoke_layer(k):
    phase, sway, lean, height, thick, second = SMOKE[k]
    sx, sy = fit_xy(256, 96)
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((sx + lean * t * 2 + sway * math.sin(phase + t * 3.4) * t, sy - height * t))
    im = draw_wisp(pts, 5.0 * thick, 0.9)
    if second:
        ph2, sw2, ln2, h2 = second
        cx, cy = fit_xy(34, 100)
        p2 = [(cx + ln2 * (i / 6) * 2 + sw2 * math.sin(ph2 + (i / 6) * 3.4) * (i / 6), cy - h2 * (i / 6)) for i in range(7)]
        im = Image.alpha_composite(im, draw_wisp(p2, 4.0, 0.75))
    return im


def glint_layer(k, dome_alpha):
    bloom, star = GLINT[k]
    a = np.zeros((H, W), dtype=np.float32)
    YY, XX = d2.YY, d2.XX
    if bloom > 0:
        mx, my = GLINT_MAIN
        a = np.maximum(a, np.clip(1 - np.hypot((XX - mx) / 1.5, YY - my) / 24.0, 0, 1) ** 1.0 * 0.95 * bloom)
    if star > 0:
        sx, sy = GLINT_STAR
        arm = 13.0 * star + 3
        cross = np.clip(1 - np.abs(XX - sx) / 3.2, 0, 1) * np.clip(1 - np.abs(YY - sy) / arm, 0, 1) ** 1.5
        cross2 = np.clip(1 - np.abs(YY - sy) / 3.2, 0, 1) * np.clip(1 - np.abs(XX - sx) / arm, 0, 1) ** 1.5
        a = np.maximum(a, np.maximum(cross, cross2) * star)
    a = a * dome_alpha
    rgb = np.zeros((H, W, 3), dtype=np.float32) + np.array([255, 255, 245], dtype=np.float32)
    return d2.to_img(rgb, a)


# ---------- build ----------

def build():
    d2_layers, _ = d2.build(7)
    names = [n for n, _ in d2_layers]
    L = dict(d2_layers)
    hull = d2.hull_mask()
    base_lights = d2.fit(lights_levels(hull, BASE_LEVELS))
    # identity check: our light drawing at baseline levels equals ufo-d2's own
    own = d2.fit(d2.lights_layer(hull))
    assert np.array_equal(np.asarray(base_lights), np.asarray(own)), "lights_levels differs from ufo-d2.lights_layer"

    r2 = Image.open(R2_MASTER).convert("RGBA")
    under = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in ("glow", "body", "dome", "damage"):
        under = Image.alpha_composite(under, L[n])
    solid = np.asarray(L["body"])[..., 3] >= 254
    dome_alpha = np.asarray(L["dome"])[..., 3].astype(np.float32) / 255.0

    # baseline: the recomposited light zone must equal the round 2 master
    zone_base = (np.asarray(base_lights)[..., 3] > 0) & solid
    cz = Image.alpha_composite(Image.alpha_composite(under, base_lights), L["rim"])
    diff = np.abs(np.asarray(cz).astype(int) - np.asarray(r2).astype(int)).max(axis=2)
    # pixels where round 3 geometry (belly notch) differs from round 2 keep the round 2 pixel
    mism = Image.fromarray(((diff > 0) & zone_base).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))
    keep_r2 = np.asarray(mism) > 0
    base_zone_diff = int(diff[zone_base & ~keep_r2].max())
    print(f"light zone: {int(zone_base.sum())} master px, {int((zone_base & keep_r2).sum())} keep the round 2 pixel (notch)")

    frames = []
    for k in range(FRAMES):
        lights = d2.fit(lights_levels(hull, FRAME_LEVELS[k]))
        zone = ((np.asarray(lights)[..., 3] > 0) | (np.asarray(base_lights)[..., 3] > 0)) & solid & ~keep_r2
        cz = Image.alpha_composite(Image.alpha_composite(under, lights), L["rim"])
        f = np.where(zone[..., None], np.asarray(cz), np.asarray(r2))
        f = Image.fromarray(f.astype(np.uint8), "RGBA")
        f = Image.alpha_composite(f, glint_layer(k, dome_alpha))
        f = Image.alpha_composite(f, smoke_layer(k))
        f = Image.alpha_composite(f, draw_sparks(k))
        frames.append(f)
    return frames, base_zone_diff


def shrink(im):
    return im.resize((GW, GH), Image.LANCZOS)


def guard(small):
    """Resampling ripple must never take a pixel of the still's silhouette below its alpha:
    every frame keeps at least the alpha of the picked still (hitbox coverage never drops)."""
    st = np.asarray(Image.open(R2_STILL).convert("RGBA"))
    a = np.asarray(small).copy()
    a[..., 3] = np.maximum(a[..., 3], st[..., 3])
    return Image.fromarray(a, "RGBA")


def strip(frames):
    fw, fh = frames[0].size
    s = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * fw, 0))
    return s


# ---------- checks, board, gif ----------

def hitbox_masks():
    """Pixel-centre masks: disc box 40 x 10 in the bottom 10 rows; dome circle r 9 at (20, 10), rows above the disc."""
    yy, xx = np.mgrid[0:GH, 0:GW].astype(np.float32) + 0.5
    disc = yy >= 10
    dome = (np.hypot(xx - 20, yy - 10) <= 9) & (yy < 10)
    return disc, dome


def coverage(im):
    a = np.asarray(im)[..., 3]
    disc, dome = hitbox_masks()
    return (a[disc] >= 128).mean(), (a[dome] >= 128).mean(), (a[disc | dome] >= 128).mean()


def board(smalls, path):
    pad = 16
    w4 = GW * 4
    bw = pad + FRAMES * (w4 + pad)
    bh = 16 + GH + 28 + 16 + GH * 4 + 16
    bd = Image.new("RGBA", (bw, bh), BOARD_BG + (255,))
    font = ImageFont.load_default()
    dr = ImageDraw.Draw(bd)
    dr.text((pad, 4), "1x on the game background", fill=TXT, font=font)
    y1 = 18
    for i, f in enumerate(smalls):
        bd.alpha_composite(f, (pad + i * (w4 + pad), y1))
        dr.text((pad + i * (w4 + pad), y1 + GH + 2), f"frame {i}", fill=TXT, font=font)
    y4 = y1 + GH + 28
    dr.text((pad, y4 - 12), "4x with the hitbox (disc box and dome circle, faint)", fill=TXT, font=font)
    for i, f in enumerate(smalls):
        x0 = pad + i * (w4 + pad)
        z = f.resize((w4, GH * 4), Image.NEAREST)
        ov = Image.new("RGBA", z.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rectangle([0, 40, w4 - 1, GH * 4 - 1], outline=(120, 255, 200, 90))
        od.ellipse([w4 // 2 - 36, 40 - 36, w4 // 2 + 36, 40 + 36], outline=(120, 255, 200, 90))
        z = Image.alpha_composite(z, ov)
        bd.alpha_composite(z, (x0, y4))
    bd.save(path)


def gif(smalls, path, order):
    bg = Image.new("RGBA", (GW * 4 + 32, GH * 4 + 32), BOARD_BG + (255,))
    seq = []
    for i in order:
        t = bg.copy()
        t.alpha_composite(smalls[i].resize((GW * 4, GH * 4), Image.NEAREST), (16, 16))
        seq.append(t.convert("RGB"))
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=int(round(TICKS * 1000 / 60 / 10)) * 10, loop=0, disposal=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    masters, base_zone_diff = build()
    smalls = [guard(shrink(m)) for m in masters]
    sheet = strip(smalls)
    sheet.save(out / f"{NAME}.png")
    strip(masters).save(out / f"{NAME}-master.png")
    board(smalls, out / f"{NAME}-board.png")
    # preview: the pool played in random order, never the same frame twice in a row
    rng = random.Random(3)
    order, last = [], -1
    for _ in range(48):
        c = rng.choice([i for i in range(FRAMES) if i != last])
        order.append(c)
        last = c
    gif(smalls, out / f"{NAME}-preview.gif", order)

    print(f"strip {sheet.size} {sheet.mode}; recomposited light zone vs round 2 master, max diff {base_zone_diff}")
    still = Image.open(R2_STILL).convert("RGBA")
    print("still coverage (disc, dome, union):", ["%.4f" % v for v in coverage(still)])
    for i, s in enumerate(smalls):
        print(f"frame {i}:", ["%.4f" % v for v in coverage(s)])


if __name__ == "__main__":
    main()
