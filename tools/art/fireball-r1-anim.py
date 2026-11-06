"""Fireball animation strip converted from the staged r1 look of design 4 (the dying star).

The design script for this look is gone, so the source here is the staged r1 files:
  staging/assets/sprites/fireball-d4-r1-master.png   512 x 512, the 8x master (composite)
  staging/assets/sprites/fireball-d4-r1.piskel       64 x 64 layers; the 'embers' layer says where the sparks are
  staging/assets/sprites/fireball-d4-r1.png          64 x 64 still: the baseline for the coverage checks
Nothing is redrawn: the r1 master is cut into parts and the moving parts are animated.

Over 6 frames that loop seamlessly:
  head     R <= 128 master px around (352, 352) (= game (44, 44), r16): the ball and its fuchsia rim are
           copied from the master, never touched, so they are identical in every frame
  corona   the white halo ring and its 16 spikes (found in the master) flicker: each spike grows and
           shrinks (the content of the ring is pushed in or out along the radius) and brightens and dims,
           each on its own phase. The spikes right behind the head, where the trail joins, stay still
  trail    the sparks are cut out of the master (filled from what is around them); bright streaks then run
           back along the trail axis. The trail's alpha is never lowered
  embers   8 sparks (flat warm color like r1) are born behind the head, drift back along the 35 deg path
           toward the top-left, shrink and fade, staggered so every frame holds sparks at every stage

Spec: docs/design/gdd/drifters/06-fireball.md (art_canvas, hitbox); tuning game/tuning/drifter_looks.json
(fireball.strip: 6 frames of 64 x 64, 4 ticks per frame, loop).

Outputs (staging/assets/sprites/anim/): fireball.png (384 x 64), fireball-master.png (3072 x 512),
fireball-board.png, fireball-preview.gif.

Usage: python3 tools/art/fireball-r1-anim.py
"""

from __future__ import annotations

import base64
import importlib.util
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "staging/assets/sprites"
OUT = ROOT / "staging/assets/sprites/anim"

# values from the GDD (06-fireball.md): none invented here
GAME = 64
SCALE = 8
M = GAME * SCALE
HEAD_CENTER = (44.0, 44.0)
HEAD_R = 16.0
TAIL_R = 8.0
ANGLE = 35.0
FRAMES = 6  # tuning: fireball.strip
BG = (10, 13, 31, 255)

CX, CY = HEAD_CENTER[0] * SCALE, HEAD_CENTER[1] * SCALE  # 352, 352
RH = HEAD_R * SCALE  # 128
A = math.radians(ANGLE)
D = np.array([math.sin(A), math.cos(A)])
B = -D  # back along the path
N = np.array([math.cos(A), -math.sin(A)])

yy, xx = np.mgrid[0:M, 0:M].astype(np.float32)
PX, PY = xx + 0.5 - CX, yy + 0.5 - CY
R = np.hypot(PX, PY)
S = PX * B[0] + PY * B[1]
W = PX * N[0] + PY * N[1]
THETA = np.degrees(np.arctan2(PY, PX)) % 360.0
TRAIL_DEG = math.degrees(math.atan2(B[1], B[0])) % 360.0  # 235

HEAT = [(0.00, (150, 22, 12)), (0.16, (214, 48, 12)), (0.36, (255, 100, 14)), (0.54, (255, 160, 36)),
        (0.72, (255, 210, 84)), (0.88, (255, 242, 190)), (1.00, (255, 255, 248))]  # the design's own ramp


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ramp(v):
    xs = [s[0] for s in HEAT]
    return np.array([np.interp(v, xs, [s[1][c] for s in HEAT]) for c in range(3)], np.float32)


def gauss(a, sigma):
    """Separable gaussian blur of an H x W x C (or H x W) float array."""
    r = int(sigma * 3)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = a
    for axis in (0, 1):
        pad = [(0, 0)] * a.ndim
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode="edge")
        acc = np.zeros_like(out)
        n = out.shape[axis]
        for i, w in enumerate(k):
            sl = [slice(None)] * a.ndim
            sl[axis] = slice(i, i + n)
            acc += w * p[tuple(sl)]
        out = acc
    return out


def sample(img, x, y):
    """Bilinear sample of an H x W x C array at pixel-index coordinates."""
    x = np.clip(x, 0, M - 1.001)
    y = np.clip(y, 0, M - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


# ------------------------------------------------------------------ source and its parts
def load_source():
    master = np.asarray(Image.open(SRC / "fireball-d4-r1-master.png").convert("RGBA"), np.float32)
    doc = json.loads((SRC / "fireball-d4-r1.piskel").read_text())
    emb = None
    for l in doc["piskel"]["layers"]:
        L = json.loads(l)
        if L["name"] == "embers":
            emb = Image.open(io.BytesIO(base64.b64decode(L["chunks"][0]["base64PNG"].split(",")[1]))).convert("RGBA")
    return master, emb


def premult(a):
    out = a.copy()
    out[..., :3] = a[..., :3] * (a[..., 3:4] / 255.0)
    return out


def unpremult(p):
    a = np.clip(p[..., 3:4], 0, 255)
    out = p.copy()
    out[..., :3] = np.where(a > 0.5, p[..., :3] / np.maximum(a / 255.0, 1e-4), 0)
    out[..., 3] = a[..., 0]
    return np.clip(out, 0, 255)


def remove_embers(master, emb_layer):
    """Cut the r1 sparks out of the master: fill their spots from the pixels around them."""
    al = emb_layer.getchannel("A").resize((M, M), Image.BICUBIC)
    hole = (np.asarray(al, np.float32) > 14).astype(np.uint8) * 255
    hole = Image.fromarray(hole).filter(ImageFilter.MaxFilter(25))  # dilate by 12 master px
    hole_f = np.asarray(hole, np.float32) / 255.0
    valid = (1 - hole_f)[..., None]
    p = premult(master)
    num = gauss(p * valid, 14.0)
    den = np.maximum(gauss(valid, 14.0), 1e-4)
    fill = num / den
    soft = np.asarray(Image.fromarray((hole_f * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255.0
    soft = np.clip(soft * 1.0, 0, 1)[..., None]
    out = p * (1 - soft) + fill * soft
    return unpremult(out), hole_f


def find_spikes(master):
    """Angles (deg) of the corona's spikes: peaks of alpha on a ring just outside the head."""
    th = np.radians(np.arange(0, 360, 0.5))
    r = 141
    p = sample(master, CX - 0.5 + r * np.cos(th), CY - 0.5 + r * np.sin(th))[..., 3]
    a2 = np.convolve(np.r_[p[-3:], p, p[:3]], np.ones(7) / 7, "valid")
    out = []
    n = len(a2)
    for i in range(n):
        win = [a2[(i + j) % n] for j in range(-24, 25)]
        if a2[i] == max(win) and a2[i] - min(win) > 25:
            out.append(i / 2.0)
    return out


def ang_diff(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


# ------------------------------------------------------------------ per-frame animation
def corona_field(spikes, k):
    """Per pixel: s (radial scale of the ring content) and g (brightness gain), both from the spikes' phases."""
    ph = 2 * math.pi * k / FRAMES
    rng = np.random.default_rng(7)
    s = np.ones((M, M), np.float32)
    g = np.ones((M, M), np.float32)
    for sp in spikes:
        m = int(rng.integers(1, 3))
        p0 = rng.random() * 2 * math.pi
        # the spikes right behind the head, where the trail joins, stay still
        keep = float(smoothstep(32.0, 70.0, abs(ang_diff(sp, TRAIL_DEG))))
        v = math.sin(m * ph + p0) * keep
        bump = np.exp(-((ang_diff(THETA, sp) / 8.0) ** 2)).astype(np.float32)
        s += 0.55 * v * bump
        g += 0.22 * v * bump
    return s, g


def corona_frame(base, spikes, k):
    s, g = corona_field(spikes, k)
    fo = 1.0 - smoothstep(45.0, 95.0, R - RH)  # the effect fades out away from the head
    s_eff = 1.0 + (s - 1.0) * fo
    r_src = RH + np.maximum(R - RH, 0) / np.maximum(s_eff, 0.2)
    r_src = np.where(R > RH, r_src, R)
    ratio = r_src / np.maximum(R, 1e-3)
    sx = CX - 0.5 + PX * ratio
    sy = CY - 0.5 + PY * ratio
    p = sample(premult(base), sx, sy)
    gain = 1.0 + (g - 1.0) * fo
    p[..., :3] *= gain[..., None]
    p[..., 3] = np.clip(p[..., 3] * np.where(R > RH, gain, 1.0), 0, 255)
    return unpremult(p)


def trail_shimmer(img, k):
    """Bright streaks run back along the trail axis. Alpha is only raised."""
    s = np.maximum(S, 0.0)
    lam1, lam2 = 150.0, 90.0
    w1 = 0.5 + 0.5 * np.sin(2 * math.pi * (s / lam1 - k / FRAMES) + W / 50.0)
    w2 = 0.5 + 0.5 * np.sin(2 * math.pi * (s / lam2 - 2 * k / FRAMES) - W / 35.0 + 1.3)
    wave = smoothstep(0.30, 0.95, np.clip(0.65 * w1 + 0.35 * w2, 0, 1))
    zone = smoothstep(150.0, 215.0, R) * smoothstep(60.0, 170.0, S)
    wave = (wave * zone).astype(np.float32)
    out = img.copy()
    hot = np.array([255, 228, 150], np.float32)
    mix = (0.30 * wave)[..., None]
    out[..., :3] = out[..., :3] * (1 - mix) + hot * mix
    out[..., :3] *= (0.82 + 0.36 * wave)[..., None] * zone[..., None] + (1 - zone[..., None])
    out[..., :3] = np.clip(out[..., :3], 0, 255)
    out[..., 3] = np.clip(out[..., 3] * (1.0 + 0.14 * wave + 0.06 * zone), 0, 255)
    return out


def ember_params():
    rng = np.random.default_rng(404 + 31)
    n = 8
    w0 = np.linspace(-120, 120, n)
    rng.shuffle(w0)
    return [dict(phase=i / n + (rng.random() - 0.5) * 0.06, w0=float(w0[i]), rad=9.0 + rng.random() * 6.0,
                 wob=float(rng.random() * 2 * math.pi), wob_amp=6.0 + rng.random() * 8.0) for i in range(n)]


EMBERS = ember_params()
EMBER_S0, EMBER_S1 = 175.0, 410.0


def add_embers(img, k):
    p = premult(img)
    for e in EMBERS:
        u = (k / FRAMES + e["phase"]) % 1.0
        s_ = EMBER_S0 + (EMBER_S1 - EMBER_S0) * u
        w_ = e["w0"] * (0.35 + 0.65 * u) + e["wob_amp"] * math.sin(2 * math.pi * 1.5 * u + e["wob"])
        x = CX + B[0] * s_ + N[0] * w_
        y = CY + B[1] * s_ + N[1] * w_
        rad = e["rad"] * (1.0 - 0.40 * u)
        env = float(smoothstep(0.0, 0.10, u) * (1 - u) ** 0.9)
        dist = np.hypot(xx + 0.5 - x, yy + 0.5 - y)
        a = np.clip((rad + 6.0 - dist) / 12.0, 0, 1)
        a = a * a * (3 - 2 * a) * env
        col = ramp(0.86 - 0.30 * u)  # warm like r1's sparks, cooling as they age
        a3 = a[..., None]
        p[..., :3] = col * a3 * 255.0 / 255.0 + p[..., :3] * (1 - a3)
        p[..., 3] = a * 255.0 + p[..., 3] * (1 - a)
    return unpremult(p)


def build_frames():
    master, emb = load_source()
    clean, _hole = remove_embers(master, emb)
    spikes = find_spikes(master)
    head = R <= RH
    frames = []
    for k in range(FRAMES):
        f = corona_frame(clean, spikes, k)
        f = trail_shimmer(f, k)
        f = add_embers(f, k)
        f[head] = master[head]  # the ball and its rim: exactly the r1 master
        frames.append(Image.fromarray(np.clip(f.round(), 0, 255).astype(np.uint8), "RGBA"))
    return master, spikes, frames


# ------------------------------------------------------------------ checks, board, gif
def shrink(img, size=GAME):
    return img.resize((size, size), Image.LANCZOS)


def circles():
    hc = np.array(HEAD_CENTER)
    return (hc, HEAD_R), (hc + B * (HEAD_R + TAIL_R), TAIL_R)


def circle_mask(c, r):
    y, x = np.mgrid[0:GAME, 0:GAME] + 0.5
    return np.hypot(x - c[0], y - c[1]) <= r


def share(frame, c, r, thr=128):
    return float((np.asarray(frame)[..., 3][circle_mask(c, r)] >= thr).mean())


def font(sz=12):
    try:
        return ImageFont.truetype(str(ROOT / "tools/art/fonts/ShareTechMono.ttf"), sz)
    except Exception:
        return ImageFont.load_default()


def make_board(frames, smalls, path):
    pad, z, gap = 12, 4, 8
    f = font()
    lab = (160, 170, 210, 255)
    w = pad * 2 + FRAMES * (GAME * z + gap)
    h = pad + 16 + GAME + pad + 16 + 42 + pad + 16 + GAME * z + pad
    board = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(board)
    y = pad
    d.text((pad, y), "1x on the game background, every frame", font=f, fill=lab)
    y += 16
    for i, fr in enumerate(frames):
        board.alpha_composite(fr, (pad + i * (GAME + gap), y))
    y += GAME + pad
    d.text((pad, y), "small variant 42 px (the game shrinks the frame), every frame", font=f, fill=lab)
    y += 16
    for i, sm in enumerate(smalls):
        board.alpha_composite(sm, (pad + i * (GAME + gap), y))
    y += 42 + pad
    d.text((pad, y), "4x, hitbox circles (head r16, tail r8) drawn faintly", font=f, fill=lab)
    y += 16
    for i, fr in enumerate(frames):
        x0 = pad + i * (GAME * z + gap)
        tile = Image.new("RGBA", (GAME * z, GAME * z), BG)
        tile.alpha_composite(fr.resize((GAME * z, GAME * z), Image.NEAREST))
        ov = Image.new("RGBA", tile.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for c, r in circles():
            od.ellipse([(c[0] - r) * z, (c[1] - r) * z, (c[0] + r) * z, (c[1] + r) * z], outline=(120, 255, 200, 120), width=1)
        tile.alpha_composite(ov)
        board.paste(tile, (x0, y))
    board.convert("RGB").save(path)


def make_gif(frames, path):
    z = 4
    imgs = []
    for fr in frames:
        tile = Image.new("RGBA", (GAME * z, GAME * z), BG)
        tile.alpha_composite(fr.resize((GAME * z, GAME * z), Image.NEAREST))
        imgs.append(tile.convert("RGB"))
    # 4 ticks = 66.7 ms; GIF delays are in 10 ms units, so alternate 70 and 60 (average 66.7)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=[70, 60, 70, 70, 60, 70], loop=0, disposal=2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    master, spikes, masters = build_frames()
    print("spikes found:", len(spikes))
    frames = [shrink(m) for m in masters]
    smalls = [shrink(m, 42) for m in masters]
    strip = Image.new("RGBA", (GAME * FRAMES, GAME), (0, 0, 0, 0))
    mstrip = Image.new("RGBA", (M * FRAMES, M), (0, 0, 0, 0))
    for i, (fr, m) in enumerate(zip(frames, masters)):
        strip.paste(fr, (GAME * i, 0))
        mstrip.paste(m, (M * i, 0))
    strip.save(OUT / "fireball.png")
    mstrip.save(OUT / "fireball-master.png")
    make_board(frames, smalls, OUT / "fireball-board.png")
    make_gif(frames, OUT / "fireball-preview.gif")

    still = Image.open(SRC / "fireball-d4-r1.png").convert("RGBA")
    (hc, hr), (tc, tr) = circles()
    tm = circle_mask(tc, tr)
    print("still   head %.3f tail %.3f  tail alpha min/mean %d/%.1f" % (
        share(still, hc, hr), share(still, tc, tr), np.asarray(still)[..., 3][tm].min(), np.asarray(still)[..., 3][tm].mean()))
    inner = circle_mask(hc, 12.0)  # beyond r12 the Lanczos shrink reaches past the head edge into the flickering corona
    s0 = np.asarray(frames[0])
    for i, fr in enumerate(frames):
        a = np.asarray(fr)
        print("frame %d head %.3f tail %.3f  tail alpha min/mean %d/%.1f  head(r12) identical to frame 0: %s" % (
            i, share(fr, hc, hr), share(fr, tc, tr), a[..., 3][tm].min(), a[..., 3][tm].mean(),
            bool((a[inner] == s0[inner]).all())))
    print("strip", strip.size, strip.mode, "master", mstrip.size)


if __name__ == "__main__":
    main()
