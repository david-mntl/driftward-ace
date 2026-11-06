"""Meteorite design 10: soft cartoon asteroids, a pool of four skins (d10a .. d10d).

Style (Director, in words): stylized, smooth, soft-shaded, like a clean vector
illustration. No texture noise. Chunky irregular silhouettes (lumps, flat chipped
facets, rounded bites, on some rocks a round hole through a lobe). A few round
craters per rock, each a soft dark pocket with a lighter lower lip. Dusty rose lit
side blending into deep violet shadow side, light from the top-left. A thin
fuchsia rim on the bottom edge (GDD 12 rule 8), kept subtle so the coin keeps
solid fuchsia (rule 6).

How it is drawn (GDD 12 rule 13: shape turns, light and rim stay fixed):
  * Each rock is a silhouette (a signed distance field) plus a height field,
    both defined in the rock's own frame. A frame is made by turning the sample
    grid in the plane (45 degrees per frame), so silhouette and craters turn.
  * Every frame is shaded in view space with the same fixed light, and the rim is
    found from the turned silhouette, so it stays at the bottom.
  * Drawn at 8x (288 x 288), shrunk to 36 x 36 with an exact box average.

Frame: 36 x 36. The medium hitbox is a circle r14 at the centre. A solid core
(radius CORE) covers it on every frame; lumps, bites and holes live in the ring
between the core and RMAX, and nothing comes within 1 px of the frame edge.

Run from anywhere: python3 tools/art/meteorite-d10.py [--round 1]
Nothing here ships (GDD 15). Pillow and numpy only.
"""

from __future__ import annotations

import argparse
import colorsys
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meteorite_rock import font  # noqa: E402  (shared helper, read only)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"

SIZE = 36  # frame size, set by the main session for this round
HITBOX_R = 14  # GDD 01-meteorite, medium variant
SCALE = 8  # GDD 12 art_style
MASTER = SIZE * SCALE
FRAMES = 8  # GDD 01-meteorite look_frames
STEP_DEG = 45.0
TICKS = 5
BG = (10, 13, 31)
FUCHSIA = np.array([255.0, 28.0, 178.0])
CORE = 14.45  # solid core radius (hitbox 14 + a little)
RMAX = 16.85  # nothing reaches past this: the 1 px edge stays clear
HIT_W = (20, 28, 40)  # hitbox widths of the three variants
VARIANT_FRAME = {w: round(SIZE * w / 28) for w in HIT_W}  # 26, 36, 51

LIGHT = np.array([-0.55, -0.62, 0.66])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
RIM_DIR = np.array([-0.28, 0.96])
RIM_DIR = RIM_DIR / np.linalg.norm(RIM_DIR)

# colour ramp, shadow -> light. Dusty, desaturated: never bright magenta.
RAMP = [
    (0.00, (38, 26, 70)),
    (0.22, (66, 44, 100)),
    (0.45, (112, 74, 120)),
    (0.68, (154, 102, 134)),
    (0.88, (186, 124, 142)),
    (1.00, (198, 136, 148)),
]

# ----------------------------------------------------------------- skins
# lumps:   (angle deg, centre distance, radius)       grow the silhouette
# facets:  (angle deg, plane distance, width px)      flat chips, cut the lumps
# bites:   (angle deg, centre distance, radius)       round bites out of the edge
# hole:    (angle deg, centre distance, radius)       round hole through a lobe
# craters: (angle deg, distance, radius)              depth = 0.55 * radius
# bumps:   (angle deg, distance, sigma, amp)          soft swells of the surface
# Lumps are broad lobes: big circles that mostly overlap the core and swell out
# past it by up to ~2.3 px. Bites are big circles tangent to the core (centre
# distance minus radius = 14.7), so they scoop round valleys between lobes.
# A lobe that carries a hole sits at 22.5 + 45k degrees: each turn step maps it
# onto the same kind of direction, where the square frame is wider than along an
# axis, so it may reach about 17.6 px. Every other lump stays inside RMAX.
SKINS = {
    "a": dict(  # five lobes, two chipped flat, three scooped bites, no hole
        lumps=[(10, 8.8, 7.9), (88, 11.6, 5.0), (165, 10.5, 6.3), (245, 12.0, 4.7), (310, 9.6, 6.8)],
        facets=[(10, 16.1, 3.4), (165, 15.9, 3.2)],
        bites=[(50, 21.0, 6.3), (128, 20.4, 5.7), (205, 21.3, 6.6), (277, 20.5, 5.8)],
        hole=None,
        craters=[(335, 5.0, 3.4), (120, 8.0, 2.2), (215, 8.5, 1.4), (45, 11.0, 1.0), (190, 12.0, 0.8)],
        bumps=[(200, 6, 5, 0.9), (320, 7, 6, 0.8), (60, 9, 5, -0.6)],
    ),
    "b": dict(  # four lobes, hole through the lower-right one, flat chips
        lumps=[(337.5, 11.0, 6.6), (60, 10.5, 6.1), (140, 11.2, 5.4), (225, 9.8, 6.8)],
        facets=[(60, 15.9, 3.4), (140, 15.8, 3.0), (225, 16.2, 3.4)],
        bites=[(10, 21.4, 6.7), (100, 20.6, 5.9), (185, 21.0, 6.3), (282, 20.6, 5.9)],
        hole=(337.5, 16.0, 1.15),
        craters=[(200, 5.5, 3.0), (95, 6.5, 1.9), (20, 8.5, 1.3), (150, 10.5, 0.9)],
        bumps=[(120, 6, 6, 0.9), (300, 7, 5, -0.6)],
    ),
    "c": dict(  # many scooped bites, hole through the top lobe
        lumps=[(247.5, 11.0, 6.6), (320, 10.0, 6.6), (30, 11.8, 4.9), (110, 9.4, 7.3), (185, 11.4, 5.3)],
        facets=[(110, 16.0, 3.4)],
        bites=[(285, 21.2, 6.5), (355, 20.7, 6.0), (70, 21.0, 6.3), (150, 20.8, 6.1), (220, 21.0, 6.3)],
        hole=(247.5, 16.0, 1.15),
        craters=[(20, 5.0, 3.2), (150, 7.5, 2.2), (305, 8.5, 1.3), (95, 11.0, 0.9)],
        bumps=[(210, 6, 5, 0.8), (60, 8, 5, -0.6)],
    ),
    "d": dict(  # three big knobs, a hole through the left one, chunky
        lumps=[(157.5, 11.0, 6.6), (270, 9.2, 7.5), (30, 10.2, 6.4), (215, 12.4, 4.4)],
        facets=[(270, 16.2, 3.6), (30, 15.9, 3.0)],
        bites=[(350, 21.0, 6.3), (95, 20.5, 5.8), (200, 21.2, 6.5), (320, 20.6, 5.9)],
        hole=(157.5, 16.0, 1.15),
        craters=[(0, 5.0, 3.4), (240, 7.5, 2.0), (95, 8.0, 1.4), (320, 11.0, 1.0)],
        bumps=[(300, 6, 6, 0.9), (130, 8, 5, -0.5)],
    ),
}


# Round 2: the Director lets the r14 hit circle poke out of the drawn rock a
# little (at least 88% of it covered, no bite deeper than 3 px, the centre r10
# fully covered). The core is smaller and cuts go into the circle on one side
# while a lobe sticks out on the other. Extra keys:
#   core:    radius of the base disk (13.6 or so; r10 always stays inside)
#   patches: (kind, angle, distance, sigma px, amount) broad soft tone patches;
#            kinds: light (lighter rose), lav (cool lavender-grey),
#            peach (warm sand), dark (mottled dark)
#   craters: a 4th number tints the pocket, + warm, - cool
#   hue:     small hue shift of the whole skin, degrees in YIQ
SKINS_R2 = {
    "a": dict(  # wedge: one big flat face on the left, a heavy lobe on the right
        core=13.4,
        lumps=[(340, 10.0, 6.8), (80, 11.4, 5.2), (205, 10.5, 4.6)],
        facets=[(180, 12.2, 3.6), (255, 12.8, 3.0)],
        bites=[(125, 17.0, 5.7)],
        hole=None,
        craters=[(345, 5.0, 3.4, 0.6), (95, 8.0, 2.2, -0.6), (215, 6.0, 1.5, 0.3), (20, 11.5, 1.1, -0.3), (160, 8.0, 0.9, 0.5)],
        bumps=[(200, 6, 5, 0.9), (320, 7, 6, 0.8), (60, 9, 5, -0.6)],
        patches=[("light", 330, 6, 6.5, 1.0), ("lav", 170, 8, 5.5, 1.0), ("peach", 70, 9, 5.0, 1.0),
                 ("dark", 250, 5, 2.6, 0.9), ("dark", 20, 11, 2.2, 0.9), ("dark", 130, 6, 2.4, 0.8)],
        hue=0.0,
    ),
    "b": dict(  # peanut: waist bites on both sides, hole through one end
        core=13.2,
        lumps=[(22.5, 11.0, 6.6), (202.5, 11.2, 5.6)],
        facets=[(202.5, 16.0, 3.0)],
        bites=[(112.5, 16.4, 5.3), (292.5, 16.6, 5.5)],
        hole=(22.5, 16.0, 1.15),
        craters=[(215, 6.5, 3.0, -0.6), (70, 7.0, 1.9, 0.6), (350, 8.5, 1.4, 0.4), (150, 9.5, 1.0, -0.4)],
        bumps=[(120, 6, 6, 0.9), (300, 7, 5, -0.6)],
        patches=[("peach", 20, 9, 6.0, 1.0), ("lav", 200, 9, 6.0, 1.0), ("light", 100, 4, 5.0, 0.9),
                 ("dark", 280, 6, 2.5, 0.9), ("dark", 60, 8, 2.2, 0.8), ("dark", 170, 11, 2.0, 0.8)],
        hue=9.0,
    ),
    "c": dict(  # rounded triangle: three corner lobes, flat faces between them
        core=12.7,
        lumps=[(247.5, 11.0, 6.6), (7.5, 10.4, 6.3), (127.5, 10.4, 6.3)],
        facets=[(307.5, 12.5, 3.4), (67.5, 12.4, 3.4), (187.5, 12.6, 3.4)],
        bites=[],
        hole=(247.5, 16.0, 1.15),
        craters=[(20, 5.5, 3.2, 0.5), (150, 7.5, 2.2, -0.6), (310, 8.5, 1.3, 0.4), (95, 11.0, 0.9, -0.3)],
        bumps=[(210, 6, 5, 0.8), (60, 8, 5, -0.6)],
        patches=[("lav", 250, 8, 5.5, 1.0), ("light", 10, 8, 5.5, 1.0), ("peach", 130, 8, 5.5, 1.0),
                 ("dark", 330, 6, 2.5, 0.9), ("dark", 70, 6, 2.5, 0.8), ("dark", 190, 5, 2.2, 0.8)],
        hue=-11.0,
    ),
    "d": dict(  # bean: one big scoop on the lower left, lobes on the right
        core=13.5,
        lumps=[(0, 10.2, 6.4), (70, 11.0, 5.6), (300, 10.5, 6.0), (200, 11.5, 4.3)],
        facets=[(250, 12.6, 3.4)],
        bites=[(160, 17.6, 6.5)],
        hole=None,
        craters=[(0, 5.0, 3.4, -0.5), (240, 7.5, 2.0, 0.6), (80, 8.0, 1.4, -0.5), (320, 11.0, 1.0, 0.4)],
        bumps=[(300, 6, 6, 0.9), (130, 8, 5, -0.5)],
        patches=[("peach", 10, 8, 6.0, 1.0), ("light", 290, 8, 5.5, 1.0), ("lav", 120, 7, 5.5, 1.0),
                 ("dark", 220, 7, 2.5, 0.9), ("dark", 40, 12, 2.2, 0.8), ("dark", 340, 6, 2.0, 0.8)],
        hue=5.0,
    ),
}
SKINS_BY_ROUND = {1: SKINS, 2: SKINS_R2}


def polar(ang_deg, dist):
    a = np.deg2rad(ang_deg)
    return dist * np.cos(a), dist * np.sin(a)


# ----------------------------------------------------------------- fields
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def circle(x, y, cx, cy, r):
    return np.hypot(x - cx, y - cy) - r


def silhouette(sk, x, y):
    """Signed distance (px) in the rock's frame. Negative inside."""
    d = circle(x, y, 0, 0, sk.get("core", CORE))
    for ang, rc, rad in sk["lumps"]:
        cx, cy = polar(ang, rc)
        d = smin(d, circle(x, y, cx, cy, rad), 1.6)
    for ang, dist, _w in sk["facets"]:
        nx, ny = polar(ang, 1.0)
        d = smax(d, nx * x + ny * y - dist, 0.35)
    for ang, rc, rad in sk["bites"]:
        cx, cy = polar(ang, rc)
        d = smax(d, -circle(x, y, cx, cy, rad), 0.9)
    if sk["hole"]:
        ang, rc, rad = sk["hole"]
        cx, cy = polar(ang, rc)
        d = smax(d, -circle(x, y, cx, cy, rad), 0.2)
    return d


def height(sk, x, y, sdf):
    """Soft height field (px) in the rock's frame: a pillow, swells, chipped
    facets and round craters. Returns (h, crater_pocket_0to1, crater_tint)."""
    din = np.clip(-sdf, 0, None)
    W, H = 9.0, 8.0
    u = 1 - np.minimum(din / W, 1)
    h = H * np.sqrt(np.clip(1 - u * u, 0, 1))
    for ang, dist, sig, amp in sk["bumps"]:
        cx, cy = polar(ang, dist)
        h += amp * 2.0 * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sig**2))
    for ang, dist, width in sk["facets"]:
        nx, ny = polar(ang, 1.0)
        t = np.clip((nx * x + ny * y - (dist - width)) / width, 0, 1)
        h -= 2.4 * t * t * (3 - 2 * t) * np.clip(din / 1.5, 0, 1) + 0.0
    pocket = np.zeros_like(h)
    tint = np.zeros_like(h)
    for cr in sk["craters"]:
        ang, dist, r = cr[:3]
        cx, cy = polar(ang, dist)
        d = np.hypot(x - cx, y - cy)
        depth = 0.55 * r
        bowl = np.clip(1 - (d / r) ** 2, 0, 1) ** 2
        lip = np.exp(-(((d - r * 1.08) / (0.22 * r + 0.15)) ** 2))
        h += -depth * 2.2 * bowl + 0.22 * depth * lip
        pocket = np.maximum(pocket, bowl)
        if len(cr) > 3:
            tint += cr[3] * bowl
    return h, pocket, tint


def blur(a, s):
    """Separable gaussian blur, sigma s in samples."""
    r = int(3 * s) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k /= k.sum()
    p = np.pad(a, r, mode="edge")
    p = np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 0, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 1, p)


def ramp(t):
    xs = np.array([s[0] for s in RAMP])
    cs = np.array([s[1] for s in RAMP], float)
    return np.stack([np.interp(t, xs, cs[:, c]) for c in range(3)], -1)


RAMP_LAV = [  # cooler lavender-grey patches
    (0.00, (36, 30, 70)),
    (0.22, (62, 52, 98)),
    (0.45, (102, 88, 128)),
    (0.68, (140, 126, 160)),
    (0.88, (166, 152, 182)),
    (1.00, (178, 166, 192)),
]
RAMP_PEACH = [  # warmer peach / sand patches
    (0.00, (46, 28, 62)),
    (0.22, (80, 48, 84)),
    (0.45, (126, 84, 104)),
    (0.68, (166, 118, 120)),
    (0.88, (194, 146, 132)),
    (1.00, (204, 158, 140)),
]
CRATER_WARM = np.array([16.0, 4.0, -10.0])
CRATER_COOL = np.array([-10.0, -2.0, 16.0])


def ramp_of(stops, t):
    xs = np.array([q[0] for q in stops])
    cs = np.array([q[1] for q in stops], float)
    return np.stack([np.interp(t, xs, cs[:, c]) for c in range(3)], -1)


def patch_weights(sk, x, y):
    """Broad soft patches in the rock's frame: kind -> weight 0..1."""
    raw = {}
    for kind, ang, dist, sig, amp in sk["patches"]:
        cx, cy = polar(ang, dist)
        g = amp * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sig**2))
        raw[kind] = raw.get(kind, 0) + g
    out = {}
    for kind, v in raw.items():
        u = np.clip((v - 0.18) / 0.6, 0, 1)
        out[kind] = u * u * (3 - 2 * u)
    return out


def hue_shift(rgb, deg):
    """Rotate chroma in YIQ by deg: a small hue shift that keeps brightness."""
    a = np.deg2rad(deg)
    m = np.array([[0.299, 0.587, 0.114], [0.596, -0.274, -0.322], [0.211, -0.523, 0.312]])
    yiq = rgb @ m.T
    c, s_ = np.cos(a), np.sin(a)
    i2 = yiq[..., 1] * c - yiq[..., 2] * s_
    q2 = yiq[..., 1] * s_ + yiq[..., 2] * c
    yiq = np.stack([yiq[..., 0], i2, q2], -1)
    return yiq @ np.linalg.inv(m).T


def render_frame(sk, deg):
    """One frame at master size. Returns float rgba (288, 288, 4), premultiplied."""
    i = (np.arange(MASTER) + 0.5) / SCALE - SIZE / 2
    X, Y = np.meshgrid(i, i)  # view space, px, y down
    a = np.deg2rad(deg)
    # rock frame = view frame turned back by the frame angle
    rx = np.cos(a) * X + np.sin(a) * Y
    ry = -np.sin(a) * X + np.cos(a) * Y
    sdf = silhouette(sk, rx, ry)
    h, pocket, tint = height(sk, rx, ry, sdf)
    h = blur(h, 2.2)
    hy, hx = np.gradient(h, 1 / SCALE)
    n = np.stack([-hx, -hy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    lam = n @ LIGHT
    t = np.clip((lam - 0.08) / 0.62, 0, 1)
    # big soft view-space gradient: light top-left, dark bottom-right (fixed)
    g = 0.5 + 0.5 * (X * -0.62 + Y * -0.78) / 15.0
    gg = np.clip((g - 0.5) * 1.55 + 0.52, 0, 1)
    t = np.clip(0.5 * t + 0.5 * gg, 0, 1)
    if "patches" not in sk:  # round 1 look
        t = t * (1 - 0.34 * pocket)  # soft dark pocket
        rgb = ramp(t)
    else:  # round 2 look: broad soft tone patches that turn with the rock
        w = patch_weights(sk, rx, ry)
        zero = np.zeros_like(t)
        t = np.clip(t + 0.13 * w.get("light", zero), 0, 1)
        t = t * (1 - 0.34 * pocket)
        wl, wp = w.get("lav", zero), w.get("peach", zero)
        tot = np.maximum(wl + wp, 1.0)
        wl, wp = wl / tot, wp / tot
        rgb = ramp_of(RAMP, t) * (1 - wl - wp)[..., None] + ramp_of(RAMP_LAV, t) * wl[..., None] + ramp_of(RAMP_PEACH, t) * wp[..., None]
        wd = w.get("dark", zero)
        rgb = rgb * (1 - 0.34 * wd[..., None]) + np.array([34.0, 22.0, 64.0]) * (0.34 * wd[..., None])
        rgb = rgb + np.clip(tint, 0, 1)[..., None] * CRATER_WARM + np.clip(-tint, 0, 1)[..., None] * CRATER_COOL
        rgb = hue_shift(rgb, sk.get("hue", 0.0))
        rgb = np.clip(rgb, 0, 255)

    # silhouette in view space: alpha and thin bottom rim
    alpha = np.clip(0.5 - sdf * SCALE, 0, 1)
    sg_y, sg_x = np.gradient(blur(sdf, 1.5), 1 / SCALE)
    ng = np.hypot(sg_x, sg_y) + 1e-9
    face = np.clip((sg_x * RIM_DIR[0] + sg_y * RIM_DIR[1]) / ng, 0, 1)
    din = np.clip(-sdf, 0, None)
    edge = np.clip(1 - din / 1.25, 0, 1) ** 1.6
    m = np.clip(0.55 * edge * face**0.8, 0, 0.55)
    rgb = rgb * (1 - m[..., None]) + FUCHSIA * m[..., None]
    out = np.zeros((MASTER, MASTER, 4))
    out[..., :3] = rgb
    out[..., 3] = alpha * 255
    return out


def to_img(a):
    """Float rgba (straight) -> Image."""
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "RGBA")


def shrink_box(rgba):
    """Exact box average to SIZE, colour weighted by alpha."""
    s = SCALE
    a = rgba[..., 3] / 255.0
    pre = rgba[..., :3] * a[..., None]
    pre = pre.reshape(SIZE, s, SIZE, s, 3).mean((1, 3))
    aa = a.reshape(SIZE, s, SIZE, s).mean((1, 3))
    col = pre / np.maximum(aa[..., None], 1e-6)
    out = np.zeros((SIZE, SIZE, 4))
    out[..., :3] = col
    out[..., 3] = aa * 255
    return out


def on_bg(img, bg=None):
    b = Image.new("RGBA", img.size, BG + (255,)) if bg is None else bg.copy().convert("RGBA")
    b.alpha_composite(img)
    return b


def bg_crop(w, h, x0=150, y0=60):
    src = Image.open(ROOT / "game/assets/background_sway_00.png").convert("RGBA")
    tile = src.crop((x0, y0, x0 + 400, y0 + h))
    out = Image.new("RGBA", (w, h))
    for x in range(0, w, 400):
        out.paste(tile, (x, 0))
    return out


# ----------------------------------------------------------------- checks
YY, XX = np.mgrid[0:SIZE, 0:SIZE]
RR = np.hypot(XX + 0.5 - SIZE / 2, YY + 0.5 - SIZE / 2)


def hsv_stats(rgb):
    r = rgb.reshape(-1, 3) / 255.0
    mx, mn = r.max(1), r.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0)
    return float(sat.mean()), float(mx.mean())


def coin_stats():
    c = np.asarray(Image.open(ROOT / "game/assets/sprites/coin_common.png").convert("RGBA"))[:, :24].astype(float)
    op = c[..., 3] >= 128
    px = c[..., :3][op]
    s_all = hsv_stats(px)
    mx = px.max(1)
    top = px[mx >= np.percentile(mx, 75)]
    return s_all, hsv_stats(top)


def frame_checks(frames):
    """frames: list of float rgba (36, 36, 4). Returns dict of numbers."""
    cov, cov10, depth, border, lit_px, rmax = [], [], [], 0, [], 0.0
    for f in frames:
        al = f[..., 3]
        cov.append(float((al[RR <= HITBOX_R] >= 128).mean() * 100))
        cov10.append(float((al[RR <= 10] >= 128).mean() * 100))
        hole = (al < 128) & (RR <= HITBOX_R)  # circle pixels the rock does not cover
        depth.append(float(HITBOX_R - RR[hole].min()) if hole.any() else 0.0)
        e = np.zeros_like(al, bool)
        e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = True
        border += int((al[e] > 0).sum())
        op = al >= 128
        rmax = max(rmax, float(RR[op].max()))
        lit = op & ((XX + YY) < SIZE - 2)  # upper-left half
        lit_px.append(f[..., :3][lit])
    lit_px = np.concatenate(lit_px)
    mx = lit_px.max(1)
    top = lit_px[mx >= np.percentile(mx, 75)]
    return dict(cov=cov, cov10=cov10, depth=depth, border=border, rmax=rmax, lit=hsv_stats(lit_px), lit_top=hsv_stats(top))


# ----------------------------------------------------------------- outputs
def make_gif(frames, path):
    imgs = [on_bg(f.resize((SIZE * 4, SIZE * 4), Image.NEAREST)).convert("RGB") for f in frames]
    dur = [80, 90, 80, 80, 90, 80, 80, 90]  # 5 ticks = 83.3 ms
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=dur, loop=0, disposal=2)


def make_board(skin_frames, path, rnd=1, compare=None):
    names = list(skin_frames)
    f = font(11)
    col = (190, 196, 220)
    pad = 12
    c4 = SIZE * 4
    gap = 8
    W = FRAMES * (c4 + gap) + 2 * pad
    coin = Image.open(ROOT / "game/assets/sprites/coin_common.png").convert("RGBA").crop((0, 0, 24, 24))
    planet = Image.open(ROOT / "game/assets/sprites/planet_marble.png").convert("RGBA").crop((0, 0, 64, 64))
    H = pad + 16 + 4 * 46 + 18 + 4 * (c4 + 6) + 18 + 66 + 18 + 70 + 18 + 70 + 20 + (80 if compare else 0)
    b = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(b)
    y = 4
    d.text((pad, y), f"meteorite d10 round {rnd}, skins a-d: 1x on the game background (36 x 36 frames, 8 per skin)", fill=col, font=f)
    y += 16
    for n in names:
        strip = bg_crop(FRAMES * (c4 + gap), 40)
        b.paste(strip, (pad, y))
        d.text((pad - 10, y + 14), n, fill=col, font=f)
        for i, im in enumerate(skin_frames[n]):
            b.alpha_composite(im, (pad + i * (c4 + gap) + (c4 - SIZE) // 2, y + 2))
        y += 46
    y += 2
    d.text((pad, y), "4x, hitbox circle r14 drawn faintly (cyan)", fill=col, font=f)
    y += 16
    for n in names:
        d.text((2, y + 6), n, fill=col, font=f)
        for i, im in enumerate(skin_frames[n]):
            z = on_bg(im.resize((c4, c4), Image.NEAREST))
            zd = ImageDraw.Draw(z, "RGBA")
            cc, r = c4 / 2, HITBOX_R * 4
            zd.ellipse((cc - r, cc - r, cc + r - 1, cc + r - 1), outline=(90, 220, 255, 110), width=1)
            b.paste(z, (pad + i * (c4 + gap), y))
        y += c4 + 6
    d.text((pad, y), "the three sizes at 1x: hitbox 20 (frame 26), 28 (frame 36), 40 (frame 51); frames 1 and 4 of each skin", fill=col, font=f)
    y += 18
    strip = bg_crop(W - 2 * pad, 62)
    b.paste(strip, (pad, y))
    x = pad + 10
    for n in names:
        for fi in (0, 3):
            for w in HIT_W:
                fs = VARIANT_FRAME[w]
                im = skin_frames[n][fi].resize((fs, fs), Image.LANCZOS)
                b.alpha_composite(im, (x, y + 31 - fs // 2))
                x += fs + 6
            x += 10
    y += 66
    for label, fi in (("readability: coin, four rocks (medium), planet, frame 1", 0), ("same, rocks on frame 3 (turned 135 deg)", 3)):
        d.text((pad, y), label, fill=col, font=f)
        y += 16
        strip = bg_crop(W - 2 * pad, 70)
        b.paste(strip, (pad, y))
        x = pad + 20
        b.alpha_composite(coin, (x, y + 23))
        x += 24 + 24
        for n in names:
            b.alpha_composite(skin_frames[n][fi], (x, y + 17))
            x += SIZE + 24
        b.alpha_composite(planet, (x, y + 3))
        y += 74
    if compare:
        d.text((pad, y), "r1 (left) vs r2 (right) of each skin at 1x, frames 1 and 4", fill=col, font=f)
        y += 16
        strip = bg_crop(W - 2 * pad, 50)
        b.paste(strip, (pad, y))
        x = pad + 20
        for n in names:
            for fi in (0, 3):
                b.alpha_composite(compare[n][fi], (x, y + 7))
                b.alpha_composite(skin_frames[n][fi], (x + SIZE + 3, y + 7))
                x += 2 * SIZE + 14
            x += 18
    b.convert("RGB").save(path)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    a = ap.parse_args(argv)
    out = a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    skin_imgs = {}
    coin_all, coin_top = coin_stats()
    print(f"coin crystal: all-opaque sat {coin_all[0]:.2f} val {coin_all[1]:.2f} | top-quarter sat {coin_top[0]:.2f} val {coin_top[1]:.2f}")
    for n, sk in SKINS_BY_ROUND.get(a.round, SKINS_R2).items():
        stem = f"meteorite-d10{n}-r{a.round}"
        masters, small = [], []
        for k in range(FRAMES):
            m = render_frame(sk, STEP_DEG * k)
            masters.append(m)
            small.append(shrink_box(m))
        mi = [to_img(m) for m in masters]
        si = [to_img(s) for s in small]
        strip = Image.new("RGBA", (SIZE * FRAMES, SIZE), (0, 0, 0, 0))
        mstrip = Image.new("RGBA", (MASTER * FRAMES, MASTER), (0, 0, 0, 0))
        for k in range(FRAMES):
            strip.paste(si[k], (k * SIZE, 0))
            mstrip.paste(mi[k], (k * MASTER, 0))
        strip.save(out / f"{stem}.png")
        mstrip.save(out / f"{stem}-master.png")
        make_gif(si, out / f"{stem}-preview.gif")
        skin_imgs[n] = si
        ck = frame_checks([np.asarray(s).astype(float) for s in si])
        print(f"skin {n}: strip {strip.size} {strip.mode}, master {mstrip.size}")
        print("  r14 cover % per frame: " + " ".join(f"{c:.1f}" for c in ck["cov"]))
        print("  r10 cover % per frame: " + " ".join(f"{c:.1f}" for c in ck["cov10"]))
        print("  deepest bite into the r14 circle (px) per frame: " + " ".join(f"{c:.2f}" for c in ck["depth"]) + f"  max {max(ck['depth']):.2f}")
        print(f"  outer-border px with alpha>0: {ck['border']}, max opaque radius {ck['rmax']:.2f} px")
        print(f"  lit half: sat {ck['lit'][0]:.2f} val {ck['lit'][1]:.2f} | brightest quarter sat {ck['lit_top'][0]:.2f} val {ck['lit_top'][1]:.2f}")
    compare = None
    r1 = out / "meteorite-d10a-r1.png"
    if a.round > 1 and r1.exists():
        compare = {}
        for n in SKINS:
            st = Image.open(out / f"meteorite-d10{n}-r1.png").convert("RGBA")
            compare[n] = [st.crop((k * SIZE, 0, k * SIZE + SIZE, SIZE)) for k in range(FRAMES)]
    make_board(skin_imgs, out / f"meteorite-d10-r{a.round}-board.png", a.round, compare)
    print("board written")


if __name__ == "__main__":
    main()
