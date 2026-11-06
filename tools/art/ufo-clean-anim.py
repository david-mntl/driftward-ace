"""UFO, clean purple saucer: 8 animation frames, a smooth loop.

Built on the picked design, ufo-d3-r3. tools/art/ufo-d3.py is loaded with
importlib (the file name has a hyphen) and its layers are reused as they are
(glow, halo, body, dome, pores, rim; default seed 7, which gives round 3
exactly: the base frame is checked against staging/assets/sprites/ufo-d3-r3).

Motion, one full loop over 8 frames:
  - rim lights chase around the disc: 8 small lime lights sit on the edge of the
    shell; each frame the bright one moves one step, with a fading tail behind it.
    The unlit sockets are in every frame, so the shell looks the same all the time.
  - the dome's inner glow pulses softly: the lime nucleus swells and dims in a sine
    over the 8 frames (frame 0 is the middle, frame 2 the brightest, frame 6 the dimmest);
    the soft green halo round the dome breathes with it.
The hull and dome shapes, the amber pores, the glints and the fuchsia rim stay
fixed. Nothing leaves the 40 x 20 canvas.

Outputs, in --out-dir (default staging/assets/sprites/anim):
  ufo_clean.png            320 x 20 strip, 8 frames of 40 x 20
  ufo_clean-master.png     2560 x 160 master strip (8x)
  ufo_clean-board.png      every frame at 1x, then at 4x with the hitbox
  ufo_clean-preview.gif    the loop at 4x, 5 ticks per frame

Usage: python3 tools/art/ufo-clean-anim.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites/anim"
R3_MASTER = ROOT / "staging/assets/sprites/ufo-d3-r3-master.png"
R3_STILL = ROOT / "staging/assets/sprites/ufo-d3-r3.png"

NAME = "ufo_clean"
FRAMES = 8
TICKS = 5
GW, GH = 40, 20
UP = 8
W, H = GW * UP, GH * UP

BOARD_BG = (10, 13, 31)
TXT = (200, 205, 225)

_spec = importlib.util.spec_from_file_location("ufo_d3", ROOT / "tools/art/ufo-d3.py")
d3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d3)

LIME = np.array([190, 255, 110], dtype=np.float32)
STATIONS = 8
# chase order: head, then its tail (how much of the light stays on behind it)
TAIL = [1.0, 0.55, 0.22]


# ---------- the chase lights ----------

def station_xy(k):
    """Centre of station k on the shell: the belly runs left to right as k goes up.

    k = 0 is the left tip, 4 the right tip. The points sit on a flattened ring
    inside the edge of the disc (disc 320 x 80, middle at (160, 120)).
    """
    a = math.radians(180 - 45 * k)  # 180 deg: left tip; then down through the belly
    # screen y grows downward, so sin > 0 is the belly
    x = 160 + 146 * math.cos(a)
    y = 120 + 30 * math.sin(a)
    return x, y


def light_layer(levels, clip):
    """Eight lime lights; levels[k] 0 = unlit socket only, 1 = fully lit."""
    XX, YY = d3.XX, d3.YY
    rgb = np.zeros((H, W, 3), dtype=np.float32)
    alpha = np.zeros((H, W), dtype=np.float32)

    def put(color, a):
        nonlocal rgb, alpha
        out_a = a + alpha * (1 - a)
        rgb = (np.array(color, dtype=np.float32) * a[..., None] + rgb * (alpha * (1 - a))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
        alpha = out_a

    for k in range(STATIONS):
        x, y = station_xy(k)
        v = levels[k]
        d = np.hypot(XX - x, (YY - y) * 1.1)
        # socket: always there, dark plum with a faint lime tint
        put((54, 28, 70), np.clip(1 - d / 8.5, 0, 1) ** 0.6 * 0.8)
        put(tuple(LIME * 0.55), np.clip(1 - d / 5.0, 0, 1) ** 0.8 * 0.30)
        if v > 0:
            put(tuple(LIME), np.clip(1 - d / 38.0, 0, 1) ** 1.6 * 0.70 * v)
            put(tuple(LIME), np.clip(1 - d / 17.0, 0, 1) ** 0.5 * v)
            put((246, 255, 220), np.clip(1 - d / 9.0, 0, 1) * v)
    return d3.to_img(rgb, alpha * clip)


def chase_levels(frame):
    lv = [0.0] * STATIONS
    for i, t in enumerate(TAIL):
        lv[(frame - i) % STATIONS] = t
    return lv


# ---------- the dome pulse ----------
NUCLEUS = (168, 50)


def pulse_dome(dome_im, s):
    """Inner glow pulse. s in -1..1: swells the lime nucleus (s > 0) or dims it (s < 0). Inside the dome only."""
    arr = np.asarray(dome_im).astype(np.float32)
    rgb, a = arr[..., :3], arr[..., 3] / 255.0
    nx, ny = NUCLEUS
    d = np.hypot(d3.XX - nx, d3.YY - ny)
    if s >= 0:
        bloom = np.clip(1 - d / 34.0, 0, 1) ** 1.3 * 0.62 * s
        hot = np.clip(1 - d / 13.0, 0, 1) ** 0.9 * 0.55 * s
        rgb = rgb * (1 - bloom[..., None]) + np.array([170, 255, 120], dtype=np.float32) * bloom[..., None]
        rgb = rgb * (1 - hot[..., None]) + np.array([248, 255, 225], dtype=np.float32) * hot[..., None]
    else:
        dim = np.clip(1 - d / 30.0, 0, 1) ** 0.9 * 0.55 * (-s)
        rgb = rgb * (1 - dim[..., None]) + np.array([10, 60, 38], dtype=np.float32) * dim[..., None]
    out = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def pulse_value(frame):
    return math.sin(2 * math.pi * (frame - 0) / FRAMES)  # 0 -> up to 1 at frame 2 -> down to -1 at frame 6


# ---------- build ----------

def build():
    d3.SEED[0] = 7
    layers, master = d3.build(7)
    L = dict(layers)
    # the base is round 3 exactly
    r3 = Image.open(R3_MASTER).convert("RGBA")
    assert np.array_equal(np.asarray(master), np.asarray(r3)), "ufo-d3.py no longer draws round 3"
    clip = np.asarray(L["body"])[..., 3].astype(np.float32) / 255.0
    frames = []
    for k in range(FRAMES):
        s = pulse_value(k)
        glow = np.asarray(L["glow"]).copy().astype(np.float32)
        glow[..., 3] = np.clip(glow[..., 3] * (1.0 + 0.22 * s), 0, 255)
        glow = Image.fromarray(glow.astype(np.uint8), "RGBA")
        f = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        stack = [glow, L["halo"], L["body"], light_layer(chase_levels(k), clip), pulse_dome(L["dome"], s), L["pores"], L["rim"]]
        for im in stack:
            f = Image.alpha_composite(f, im)
        frames.append(f)
    return frames, master


def shrink(im):
    return im.resize((GW, GH), Image.LANCZOS)


def guard(small):
    """Resampling ripple must never take a pixel of the still's silhouette below its alpha:
    every frame keeps at least the alpha of the picked still (hitbox coverage never drops)."""
    st = np.asarray(Image.open(R3_STILL).convert("RGBA"))
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
    bh = 18 + GH + 28 + 16 + GH * 4 + 16
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


def gif(smalls, path):
    bg = Image.new("RGBA", (GW * 4 + 32, GH * 4 + 32), BOARD_BG + (255,))
    seq = []
    for _ in range(3):  # three loops in the file; the viewer loops it anyway
        for s in smalls:
            t = bg.copy()
            t.alpha_composite(s.resize((GW * 4, GH * 4), Image.NEAREST), (16, 16))
            seq.append(t.convert("RGB"))
    # 5 ticks = 83.3 ms; GIF delays are in 10 ms steps, so alternate 80 and 90 ms
    durations = [80 if i % 3 else 90 for i in range(len(seq))]
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=durations, loop=0, disposal=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    masters, _ = build()
    smalls = [guard(shrink(m)) for m in masters]
    sheet = strip(smalls)
    sheet.save(out / f"{NAME}.png")
    strip(masters).save(out / f"{NAME}-master.png")
    board(smalls, out / f"{NAME}-board.png")
    gif(smalls, out / f"{NAME}-preview.gif")

    print(f"strip {sheet.size} {sheet.mode}")
    still = Image.open(R3_STILL).convert("RGBA")
    print("still coverage (disc, dome, union):", ["%.4f" % v for v in coverage(still)])
    for i, s in enumerate(smalls):
        print(f"frame {i}:", ["%.4f" % v for v in coverage(s)])


if __name__ == "__main__":
    main()
