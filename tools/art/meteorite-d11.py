"""Meteorite design 11: the d10 round 2 rocks as 3D bodies that tumble on a tilted axis.

Why: the shipped d10 rocks turn flat in the picture plane, like a watch hand, in
8 steps of 45 degrees. The Director finds that stiff. Here each rock is a solid:
a core sphere plus lumps (overlapping spheres), flat chipped facets (plane cuts),
round bites and crater dents, all in the rock's own 3D frame. A frame is made by
turning that body about its own axis, and the axis is tilted from vertical (a
different tilt and lean per skin), so the rock tumbles instead of spinning like a
turntable. 32 frames of 11.25 degrees = one full turn, seamless loop.

Look: same soft cartoon asteroid as d10 round 2 (dusty rose lit side into deep
violet, light from the top-left, smooth shading, broad tone patches, small hue
shift per skin, soft craters with a lighter lower lip, thin fuchsia rim on the
bottom edge). The colour ramps and helpers are imported from meteorite-d10.py.

How it is drawn (GDD 12 rule 13: shape turns, light and rim stay fixed):
  * Orthographic ray cast through a signed distance field (sphere tracing) at 8x
    (288 x 288), shrunk to 36 x 36 with an exact box average.
  * Every frame is shaded in view space with one fixed light (top-left, a bit
    toward the viewer). Surface, craters and tone patches are looked up in the
    rock's frame, so they slide under the light. The fuchsia rim is found per
    frame from the projected silhouette, so it stays on the bottom edge.

Frame: 36 x 36. Medium hitbox: circle r14 at the centre. The core sphere (radius
CORE) covers it on every frame; lumps stay inside RMAX, enforced by a final cut
at RMAX_CUT, so the 1 px frame edge stays clear on every frame.

Round 2 (--round 2): the rocks are potatoes, not balls. The base is an ellipsoid
(three different semi-axes per skin) plus big lobes and LARGE plane cuts, so the
outline swings between long and short and shows straight edges and corners as the
rock turns. Flat facets get their own tone, the terminator is firmer, the shadow
side goes deep violet, and the craters are bigger, deeper and lit from the
top-left (dark far wall, lighter lit lip). Round 1 still reproduces byte for byte.

Run: python3 tools/art/meteorite-d11.py [--round 1|2] [--skins abcd] [--no-flat]
Nothing here ships (GDD 15). Pillow and numpy only.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from meteorite_rock import font  # noqa: E402  (shared helper, read only)

_spec = importlib.util.spec_from_file_location("meteorite_d10", HERE / "meteorite-d10.py")
d10 = importlib.util.module_from_spec(_spec)
sys.modules["meteorite_d10"] = d10
_spec.loader.exec_module(d10)  # read-only: palette, helpers, flat renderer

ROOT = HERE.parents[1]
OUT = ROOT / "staging/assets/sprites/anim"

SIZE = d10.SIZE  # 36
SCALE = d10.SCALE  # 8
MASTER = SIZE * SCALE
HITBOX_R = d10.HITBOX_R
BG = d10.BG
FRAMES = 32
STEP_DEG = 360.0 / FRAMES  # 11.25
TICKS = 3  # 1 tick = 1/60 s
CORE = 13.2  # core sphere; r10 always inside, the r14 circle is nearly all covered (see checks)
RMAX_CUT = 16.8  # nothing past this from the centre, in any direction
RB = 17.0  # bounding sphere for the ray start
LIGHT = d10.LIGHT
RIM_DIR = d10.RIM_DIR
FUCHSIA = d10.FUCHSIA
EY = np.array([0.0, 1.0, 0.0])

# ----------------------------------------------------------------- skins
# Rock frame: +y is the spin axis. Positions are (lon deg, lat deg, distance px).
#   axis:    (in-plane lean from vertical, lean toward the viewer), degrees
#   lumps:   (lon, lat, dist, radius)      spheres that swell out of the core
#   facets:  (lon, lat, plane dist)        flat chips, planes cut through everything
#   bites:   (lon, lat, dist, radius)      round scoops out of the edge
#   craters: (lon, lat, radius, tint[, surface dist, depth frac])   dents in the surface
#   patches: (kind, lon, lat, sigma px, amount)  broad soft tone patches
#   hue:     as d10 round 2
# lump dist + radius <= 16.7, so nothing leaves RMAX_CUT.
SKINS = {
    "a": dict(  # wedge: a big flat face on one side, a heavy lobe on the other
        axis=(32.0, 14.0),
        lumps=[(20, 8, 10.0, 6.7), (110, -28, 11.4, 5.2), (235, 30, 11.4, 5.2), (320, -22, 10.0, 6.6), (0, 68, 11.0, 5.6)],
        facets=[(200, 0, 12.2), (285, -40, 12.8), (60, -55, 12.8), (150, 62, 12.6)],
        bites=[(135, 22, 17.0, 5.9), (260, 35, 16.8, 5.3)],
        craters=[(5, 12, 3.4, 0.6, 16.0), (80, 20, 2.2, -0.6), (255, -5, 1.5, 0.3), (160, -30, 1.1, -0.3), (300, 45, 1.0, 0.5), (190, 25, 1.8, 0.4), (330, -45, 1.4, -0.4), (60, 40, 1.3, 0.3)],
        patches=[("light", 345, 25, 6.5, 1.0), ("lav", 185, 5, 5.5, 1.0), ("peach", 85, -15, 5.0, 1.0),
                 ("dark", 255, 25, 2.6, 0.9), ("dark", 30, -35, 2.2, 0.9), ("dark", 135, 55, 2.4, 0.8), ("lav", 5, -30, 5.5, 1.0), ("peach", 240, 30, 5.5, 1.0), ("light", 150, -40, 6.0, 1.0)],
        hue=0.0,
    ),
    "b": dict(  # peanut: waist bites on both sides, a lobe at each end
        axis=(-38.0, -12.0),
        lumps=[(25, 5, 10.8, 5.9), (205, -5, 10.8, 5.8), (115, 50, 11.4, 5.2), (300, -55, 10.8, 5.8)],
        facets=[(205, -5, 15.7), (25, 40, 15.6), (300, 10, 12.8), (160, -45, 12.6)],
        bites=[(115, 0, 16.8, 5.5), (295, 0, 16.8, 5.5), (0, -70, 17.4, 5.9)],
        craters=[(220, 8, 3.0, -0.6, 16.0), (75, 25, 1.9, 0.6), (355, -25, 1.4, 0.4), (160, -10, 1.0, -0.4), (25, 6, 1.7, -0.3, 16.6, 0.75), (120, -30, 1.8, 0.4), (300, 20, 2.0, -0.5), (60, -50, 1.2, 0.3)],
        patches=[("peach", 20, 10, 6.0, 1.0), ("lav", 200, -10, 6.0, 1.0), ("light", 100, 40, 5.0, 0.9),
                 ("dark", 280, 25, 2.5, 0.9), ("dark", 60, -30, 2.2, 0.8), ("dark", 165, 20, 2.0, 0.8), ("peach", 200, 35, 5.5, 1.0), ("lav", 20, -35, 5.5, 1.0), ("light", 290, 0, 5.5, 1.0)],
        hue=9.0,
    ),
    "c": dict(  # rounded triangle: three corner lobes, flat faces between
        axis=(16.0, -10.0),
        lumps=[(90, -10, 10.8, 5.9), (210, 15, 10.6, 6.0), (330, 0, 10.6, 6.0), (0, 75, 10.4, 6.2)],
        facets=[(150, 0, 12.6), (270, -5, 12.5), (30, 10, 12.6), (20, 62, 13.0)],
        bites=[(330, -30, 16.8, 5.4)],
        craters=[(130, 25, 3.2, 0.5, 14.2), (250, -25, 2.2, -0.6), (350, 30, 1.3, 0.4), (60, -40, 0.9, -0.3), (210, 18, 1.8, -0.3, 16.2, 0.8), (30, -20, 2.2, 0.4), (180, 40, 1.5, -0.4), (300, -50, 1.3, 0.3)],
        patches=[("lav", 250, 10, 5.5, 1.0), ("light", 10, 15, 5.5, 1.0), ("peach", 130, -10, 5.5, 1.0),
                 ("dark", 330, -25, 2.5, 0.9), ("dark", 70, 25, 2.5, 0.8), ("dark", 190, -30, 2.2, 0.8), ("lav", 70, 30, 5.5, 1.0), ("light", 190, -10, 5.5, 1.0), ("peach", 320, -35, 5.5, 1.0)],
        hue=-11.0,
    ),
    "d": dict(  # bean: one big scoop, lobes on the other side
        axis=(-24.0, 16.0),
        lumps=[(0, 0, 10.2, 6.4), (70, 15, 11.0, 5.6), (300, -15, 10.5, 6.0), (200, 30, 11.4, 5.0), (130, -60, 10.8, 5.7)],
        facets=[(250, -35, 12.6), (40, -50, 12.5), (170, 52, 12.7)],
        bites=[(160, -8, 17.4, 6.4), (330, 40, 16.8, 5.3)],
        craters=[(10, 15, 3.4, -0.5, 16.2), (240, 10, 2.0, 0.6), (95, -20, 1.4, -0.5), (320, 35, 1.0, 0.4), (330, -10, 1.6, -0.3, 16.2, 0.75), (150, 30, 2.2, 0.4), (270, -30, 1.6, -0.4), (60, 50, 1.2, 0.3)],
        patches=[("peach", 10, 5, 6.0, 1.0), ("light", 290, 5, 5.5, 1.0), ("lav", 120, -15, 5.5, 1.0),
                 ("dark", 220, 15, 2.5, 0.9), ("dark", 45, -30, 2.2, 0.8), ("dark", 345, 35, 2.0, 0.8), ("peach", 190, 30, 5.5, 1.0), ("lav", 330, 25, 5.5, 1.0), ("light", 100, 40, 5.5, 1.0)],
        hue=5.0,
    ),
}


# ----------------------------------------------------------------- round 2 skins
# Extra keys on top of round 1:
#   body:    ellipsoid semi-axes (x, y, z) in the rock frame, y = spin axis (px)
#   ks:      blend widths (lumps, facets, bites, craters); small = crisp edges
#   crater_depth / crater_reach: how deep the dents go, how far the shading reaches
#   facets:  (lon, lat, dist[, tone]) tone is a flat shade offset for that plane
#   tone:    whole-rock shade offset
# Inscribed ball: every plane dist and (bite dist - radius) is >= 11, the short
# body axis is >= 12.5, so the r10 circle is always covered.
SKINS_R2 = {
    "a": dict(  # wedge: one big flat face on one side, a heavy lobe on the other
        body=(17.2, 14.2, 12.6), axis=(32.0, 14.0),
        lumps=[(15, 5, 11.0, 6.0), (235, 30, 11.4, 5.2)],
        facets=[(200, 0, 11.8), (330, -35, 12.6), (60, -50, 12.5), (110, 40, 12.5), (250, 45, 12.7), (0, 62, 12.7), (300, 10, 12.9)],
        bites=[(135, 22, 17.6, 6.0)],
        craters=[(5, 12, 4.7, 0.5), (85, 20, 3.2, -0.5), (255, -5, 2.0, 0.3), (180, -20, 3.2, 0.4)],
        patches=[("light", 345, 25, 6.5, 1.0), ("lav", 185, 5, 5.5, 1.0), ("peach", 85, -15, 5.0, 1.0),
                 ("dark", 255, 25, 2.6, 0.9), ("dark", 30, -35, 2.2, 0.9), ("dark", 135, 55, 2.4, 0.8)],
        hue=0.0, chips=(16, 3, 1.4, 2.4, 12.8),
    ),
    "b": dict(  # shard: a chisel point at one end, a flat chop at the other, cut like a gem
        body=(17.8, 13.2, 12.5), axis=(-38.0, -12.0),
        lumps=[(90, 20, 10.6, 5.8), (270, -25, 10.6, 5.6)],
        facets=[(30, 0, 14.4), (330, 0, 14.4), (180, -4, 12.7, -0.16), (20, 30, 12.8), (160, 20, 12.6), (90, -30, 12.7), (270, 35, 12.7),
                (340, -45, 12.6), (200, -40, 12.5), (50, -10, 12.9), (120, 60, 12.6)],
        bites=[],
        craters=[(220, 8, 4.3, -0.6), (75, 25, 3.2, 0.6), (330, -25, 2.0, 0.4), (130, -15, 3.0, -0.4)],
        patches=[("peach", 20, 10, 6.0, 1.0), ("lav", 200, -10, 6.0, 1.0),
                 ("dark", 280, 25, 3.2, 1.0), ("dark", 60, -30, 3.0, 1.0), ("dark", 165, 20, 3.0, 1.0), ("dark", 330, 35, 2.8, 1.0)],
        hue=9.0, tone=-0.04, limb=0.55, chips=(8, 9, 1.4, 2.4, 12.7),
    ),
    "c": dict(  # rounded triangle: three corner lobes, flat faces between
        body=(15.8, 12.8, 13.6), axis=(16.0, -10.0),
        lumps=[(90, -10, 10.8, 5.9), (210, 15, 10.6, 6.0), (330, 0, 10.6, 6.0), (0, 75, 10.4, 6.2)],
        facets=[(150, 0, 11.4), (270, -5, 11.4), (30, 10, 11.6), (20, 62, 12.4), (200, -50, 12.2), (320, 50, 12.2)],
        bites=[(330, -30, 17.2, 5.8)],
        craters=[(130, 25, 4.6, 0.5), (250, -25, 3.2, -0.6), (350, 30, 2.0, 0.4), (30, -30, 3.0, 0.4)],
        patches=[("lav", 250, 10, 5.5, 1.0), ("light", 10, 15, 5.5, 1.0), ("peach", 130, -10, 5.5, 1.0),
                 ("dark", 330, -25, 2.5, 0.9), ("dark", 70, 25, 2.5, 0.8), ("dark", 190, -30, 2.2, 0.8)],
        hue=-11.0, chips=(10, 21, 1.6, 2.6, 12.6),
    ),
    "d": dict(  # bean: one big scoop, lobes on the other side
        body=(17.0, 12.8, 13.8), axis=(-24.0, 16.0),
        lumps=[(0, 0, 10.4, 6.2), (70, 15, 11.0, 5.6), (300, -15, 10.5, 6.0), (130, -60, 10.8, 5.7)],
        facets=[(250, -35, 12.2), (40, -50, 12.2), (170, 52, 12.4), (200, 30, 12.0), (100, 10, 12.4)],
        bites=[(160, -8, 17.4, 6.4), (330, 40, 17.4, 5.8)],
        craters=[(10, 15, 4.7, -0.5), (240, 10, 3.2, 0.6), (330, -10, 2.0, -0.3), (125, 5, 3.0, 0.4)],
        patches=[("peach", 10, 5, 6.0, 1.0), ("light", 290, 5, 5.5, 1.0), ("lav", 120, -15, 5.5, 1.0),
                 ("dark", 220, 15, 2.5, 0.9), ("dark", 45, -30, 2.2, 0.8), ("dark", 345, 35, 2.0, 0.8)],
        hue=5.0, chips=(8, 33, 1.8, 2.8, 12.7),
    ),
}
# ----------------------------------------------------------------- 3D helpers
def rot(axis, deg):
    """Rodrigues rotation matrix about a unit-ised axis."""
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    t = np.deg2rad(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * (K @ K)


def axis_vector(lean_deg, toward_deg):
    """Spin axis in view space (x right, y down, z toward the viewer), pointing up."""
    a, b = np.deg2rad(lean_deg), np.deg2rad(toward_deg)
    v = np.array([np.sin(a) * np.cos(b), -np.cos(a) * np.cos(b), np.sin(b)])
    return v / np.linalg.norm(v)


def basis_to(a):
    """Rotation taking the rock's +y onto the view-space axis a."""
    v = np.cross(EY, a)
    s = np.linalg.norm(v)
    if s < 1e-9:
        return np.eye(3)
    return rot(v, np.degrees(np.arctan2(s, EY @ a)))


def tilt_total(skin):
    a = axis_vector(*skin["axis"])
    return float(np.degrees(np.arccos(-a[1])))


def sph(lon, lat, dist=1.0):
    lo, la = np.deg2rad(lon), np.deg2rad(lat)
    return dist * np.array([np.cos(la) * np.cos(lo), np.sin(la), np.cos(la) * np.sin(lo)])


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def norm3(P):
    return np.sqrt((P * P).sum(-1))


def crater_geometry(sk, cr):
    lon, lat, r = cr[0], cr[1], cr[2]
    surf = cr[4] if len(cr) > 4 else body_radius(sk, sph(lon, lat))
    depth = cr[5] if len(cr) > 5 else sk.get("crater_depth", 0.55)
    anchor = sph(lon, lat, surf)
    centre = sph(lon, lat, surf + (1 - depth) * r)
    return anchor, centre, r


def ellipsoid_sdf(P, abc):
    """Close distance estimate to an ellipsoid with semi-axes abc (px)."""
    abc = np.asarray(abc, float)
    k0 = norm3(P / abc)
    k1 = norm3(P / (abc * abc))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def body_radius(sk, direction):
    """Distance from the centre to the base surface along a unit direction."""
    if "body" not in sk:
        return CORE
    abc = np.asarray(sk["body"], float)
    return float(1.0 / np.sqrt(((np.asarray(direction) / abc) ** 2).sum()))


def make_chips(sk, n, seed, lo, hi, dmin):
    """n extra flat chips spread over the whole body (so the outline shows straight
    edges from every angle): each plane sits lo..hi px under the base surface."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        lat = np.degrees(np.arcsin(z))
        lon = (i * 137.508 + rng.uniform(-18, 18)) % 360
        lat = float(np.clip(lat + rng.uniform(-9, 9), -85, 85))
        dist = max(dmin, body_radius(sk, sph(lon, lat)) - rng.uniform(lo, hi))
        out.append((round(float(lon), 1), round(lat, 1), round(float(dist), 2)))
    return out


for _sk in SKINS_R2.values():
    if "chips" in _sk:
        _sk["facets"] = list(_sk["facets"]) + make_chips(_sk, *_sk["chips"])
    _sk.setdefault("crisp", True)
    _sk.setdefault("ks", (1.0, 0.12, 0.7, 0.2))
    _sk.setdefault("crater_depth", 0.72)
    _sk.setdefault("crater_reach", 1.0)


def sdf(sk, P):
    """Signed distance (px) to the rock, P in rock space (N, 3)."""
    ks = sk.get("ks", (1.6, 0.35, 0.9, 0.45))
    d = ellipsoid_sdf(P, sk["body"]) if "body" in sk else norm3(P) - CORE
    for lon, lat, dist, r in sk["lumps"]:
        d = smin(d, norm3(P - sph(lon, lat, dist)) - r, ks[0])
    for f in sk["facets"]:
        lon, lat, dist = f[:3]
        d = smax(d, P @ sph(lon, lat) - dist, ks[1])
    for lon, lat, dist, r in sk["bites"]:
        d = smax(d, -(norm3(P - sph(lon, lat, dist)) - r), ks[2])
    for cr in sk["craters"]:
        _, c, r = crater_geometry(sk, cr)
        d = smax(d, -(norm3(P - c) - r), ks[3])
    return np.maximum(d, norm3(P) - RMAX_CUT)  # hard bound: the frame edge stays clear


def surface_maps(sk, P):
    """Per hit point in the rock's frame: crater pocket, crater tint, patch weights."""
    pocket = np.zeros(len(P))
    tint = np.zeros(len(P))
    for cr in sk["craters"]:
        anchor, _, r = crater_geometry(sk, cr)
        bowl = np.clip(1 - (norm3(P - anchor) / (sk.get("crater_reach", 0.95) * r)) ** 2, 0, 1) ** 2
        pocket = np.maximum(pocket, bowl)
        tint += cr[3] * bowl
    raw = {}
    for kind, lon, lat, sig, amp in sk["patches"]:
        c = sph(lon, lat, body_radius(sk, sph(lon, lat)))
        g = (amp if kind == "dark" else 1.35 * amp) * np.exp(-((P - c) ** 2).sum(-1) / (2 * sig**2))
        raw[kind] = raw.get(kind, 0) + g
    w = {}
    for kind, v in raw.items():
        u = np.clip((v - 0.18) / 0.6, 0, 1)
        w[kind] = u * u * (3 - 2 * u)
    return pocket, tint, w


def facet_maps(sk, P):
    """Round 2: weight of being on a flat facet (0..1) and that facet's tone offset."""
    fw = np.zeros(len(P))
    ft = np.zeros(len(P))
    tones = (0.15, -0.12, 0.08, -0.18, 0.16, -0.08, 0.11)
    for i, f in enumerate(sk["facets"]):
        dist = P @ sph(f[0], f[1]) - f[2]
        on = np.clip(1 - np.abs(dist) / 0.22, 0, 1)
        tone = f[3] if len(f) > 3 else tones[i % len(tones)]
        ft = np.where(on > fw, tone, ft)
        fw = np.maximum(fw, on)
    return fw, ft


# ----------------------------------------------------------------- render
TETRA = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], float)


def cast(sk, M):
    """Sphere-trace the rock turned by M (rock -> view). Returns mask (S,S) bool,
    P_hit rock-space points (n,3) in raster order of the mask, and view normals (n,3)."""
    i = (np.arange(MASTER) + 0.5) / SCALE - SIZE / 2
    X, Y = np.meshgrid(i, i)
    rho2 = (X * X + Y * Y).ravel()
    idx = np.flatnonzero(rho2 < RB * RB)
    x, y = X.ravel()[idx], Y.ravel()[idx]
    z0 = np.sqrt(RB * RB - rho2[idx])
    base = np.stack([x, y, np.zeros_like(x)], -1) @ M  # rock coords at view z = 0
    dz = M[2]  # rock-space step for +1 along view z
    za = z0.copy()
    hit = np.zeros(len(idx), bool)
    act = np.arange(len(idx))
    for _ in range(90):
        P = base[act] + za[act, None] * dz
        d = sdf(sk, P)
        h = d < 0.02
        hit[act[h]] = True
        za[act] -= d * 0.92
        alive = (~h) & (za[act] > -z0[act])
        act = act[alive]
        if act.size == 0:
            break
    hi = np.flatnonzero(hit)
    Ph = base[hi] + za[hi, None] * dz
    eps = 0.35
    n = np.zeros_like(Ph)
    for k in TETRA:
        n += k[None, :] * sdf(sk, Ph + eps * (k @ M))[:, None]
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    mask = np.zeros(MASTER * MASTER, bool)
    mask[idx[hi]] = True
    return mask.reshape(MASTER, MASTER), Ph, n, idx[hi]


DISK_R = 11
OFFS = [(dx, dy) for dy in range(-DISK_R, DISK_R + 1) for dx in range(-DISK_R, DISK_R + 1) if 0 < dx * dx + dy * dy <= DISK_R**2]


def silhouette_edge(mask):
    """Depth into the silhouette (px, capped) and the outward direction, per sample."""
    R = DISK_R
    pad = np.pad(mask, R, constant_values=False)
    h, w = mask.shape
    dmin = np.full(mask.shape, float(R + 1))
    nx = np.zeros(mask.shape)
    ny = np.zeros(mask.shape)
    for dx, dy in OFFS:
        out = ~pad[R + dy : R + dy + h, R + dx : R + dx + w]
        r = np.hypot(dx, dy)
        dmin = np.where(out & (r < dmin), r, dmin)
        nx += out * dx
        ny += out * dy
    return dmin / SCALE, nx, ny


def render_frame(sk, k):
    """One frame at master size, float straight rgba (288, 288, 4)."""
    M = basis_to(axis_vector(*sk["axis"])) @ rot(EY, STEP_DEG * k)
    mask, Ph, nrm, flat = cast(sk, M)
    i = (np.arange(MASTER) + 0.5) / SCALE - SIZE / 2
    X, Y = np.meshgrid(i, i)
    Xf, Yf = X.ravel()[flat], Y.ravel()[flat]
    pocket, tint, w = surface_maps(sk, Ph)

    lam = nrm @ LIGHT
    zero = np.zeros(len(Xf))
    if sk.get("crisp"):
        fw, ft = facet_maps(sk, Ph)
        tl = np.clip((lam - 0.10) / 0.55, 0, 1)
        tl = 0.65 * tl * tl * (3 - 2 * tl) + 0.35 * tl  # firmer terminator
        g = 0.5 + 0.5 * (Xf * -0.62 + Yf * -0.78) / 15.0
        gg = np.clip((g - 0.5) * 1.55 + 0.52, 0, 1)
        wg = 0.26 - 0.17 * fw  # flat facets keep their own flat tone
        t = np.clip((1 - wg) * tl + wg * gg, 0, 1)
        t = np.clip(0.93 * t + ft * fw + sk.get("tone", 0.0), 0, 1)
        sd = np.clip((Xf * 0.62 + Yf * 0.78) / 15.0, 0, 1)  # deep violet toward the shadow limb
        t = t * (1 - sk.get("limb", 0.5) * sd**1.4)
        t = np.clip(t + 0.13 * w.get("light", zero), 0, 1)
        # craters: dark floor, dark far wall (up-left), lighter lit lip (down-right)
        nb = Ph / np.asarray(sk["body"]) ** 2
        nb = (nb / np.linalg.norm(nb, axis=-1, keepdims=True)) @ M.T
        wide = np.zeros(len(Xf))
        for cr in sk["craters"]:
            anchor, _, r = crater_geometry(sk, cr)
            wide = np.maximum(wide, np.clip(1 - (norm3(Ph - anchor) / (1.25 * r)) ** 2, 0, 1) ** 0.8)
        lip = sk.get("lip", 1.8) * (lam - nb @ LIGHT) * wide
        t = np.clip(t * (1 - sk.get("floor", 0.62) * pocket) + lip, 0, 1)
    else:
        t = np.clip((lam - 0.08) / 0.62, 0, 1)
        g = 0.5 + 0.5 * (Xf * -0.62 + Yf * -0.78) / 15.0  # fixed view-space gradient
        gg = np.clip((g - 0.5) * 1.55 + 0.52, 0, 1)
        t = np.clip(0.64 * t + 0.36 * gg, 0, 1)
        zero = np.zeros_like(t)
        t = np.clip(t + 0.13 * w.get("light", zero), 0, 1)
        t = t * (1 - 0.55 * pocket)
    wl, wp = w.get("lav", zero), w.get("peach", zero)
    tot = np.maximum(wl + wp, 1.0)
    wl, wp = wl / tot, wp / tot
    rgb = (d10.ramp_of(d10.RAMP, t) * (1 - wl - wp)[:, None] + d10.ramp_of(d10.RAMP_LAV, t) * wl[:, None]
           + d10.ramp_of(d10.RAMP_PEACH, t) * wp[:, None])
    wd = w.get("dark", zero)
    rgb = rgb * (1 - 0.34 * wd[:, None]) + np.array([34.0, 22.0, 64.0]) * (0.34 * wd[:, None])
    rgb = rgb + np.clip(tint, 0, 1)[:, None] * d10.CRATER_WARM + np.clip(-tint, 0, 1)[:, None] * d10.CRATER_COOL
    rgb = np.clip(d10.hue_shift(rgb, sk.get("hue", 0.0)), 0, 255)

    img = np.zeros((MASTER * MASTER, 3))
    img[flat] = rgb
    img = img.reshape(MASTER, MASTER, 3)

    # soft light-only smoothing inside the shape keeps the vector look (no noise)
    din, nx, ny = silhouette_edge(mask)
    nn = np.hypot(nx, ny) + 1e-9
    face = np.clip((nx * RIM_DIR[0] + ny * RIM_DIR[1]) / nn, 0, 1)
    edge = np.clip(1 - din / 1.25, 0, 1) ** 1.6
    m = np.clip(0.55 * edge * face**0.8, 0, 0.55) * mask
    img = img * (1 - m[..., None]) + FUCHSIA * m[..., None]
    out = np.zeros((MASTER, MASTER, 4))
    out[..., :3] = img
    out[..., 3] = mask * 255.0
    return out


def _job(args):
    kind, n, k = args
    if kind == "axis":
        m = render_frame(SKIN_SET[n], k)
    else:  # flat 32: d10 round 2 rock, spun in the plane in finer steps
        m = d10.render_frame(d10.SKINS_R2[n], STEP_DEG * k)
    return kind, n, k, m.astype(np.float32), d10.shrink_box(m.astype(float))


SKIN_SET = SKINS  # set by main(): SKINS (round 1) or SKINS_R2 (round 2)


# ----------------------------------------------------------------- outputs
def make_strip(imgs, size):
    s = Image.new("RGBA", (size * len(imgs), size), (0, 0, 0, 0))
    for k, im in enumerate(imgs):
        s.paste(im, (k * size, 0))
    return s


def make_preview(frames, path):
    imgs = [d10.on_bg(f.resize((SIZE * 4, SIZE * 4), Image.NEAREST)).convert("RGB") for f in frames]
    pal = quant_palette(imgs)
    qs = [im.quantize(palette=pal, dither=Image.NONE) for im in imgs]
    dur = [50] * len(qs)  # 3 ticks = 50 ms
    qs[0].save(path, save_all=True, append_images=qs[1:], duration=dur, loop=0, disposal=1)


def quant_palette(imgs):
    w, h = imgs[0].size
    n = min(len(imgs), 16)
    sheet = Image.new("RGB", (w * n, h))
    step = max(1, len(imgs) // n)
    for j in range(n):
        sheet.paste(imgs[j * step], (j * w, 0))
    return sheet.quantize(256, dither=Image.NONE)


def make_board(skin_frames, path, title=None):
    col = (190, 196, 220)
    f = font(11)
    pad, c4, gap = 12, SIZE * 4, 4
    names = list(skin_frames)
    W = max(FRAMES * SIZE, 8 * (c4 + gap)) + 2 * pad
    H = 4 + 16 + 4 * 44 + 22 + 4 * (c4 + 6) + 10
    b = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(b)
    y = 4
    d.text((pad, y), title or f"meteorite d11, skins a-d: 3D tumble, 32 frames of {STEP_DEG:g} deg, 1x on the game background (36 x 36)", fill=col, font=f)
    y += 16
    for n in names:
        d.text((2, y + 12), n, fill=col, font=f)
        for k, im in enumerate(skin_frames[n]):
            b.alpha_composite(im, (pad + k * SIZE, y + 4))
        y += 44
    y += 4
    d.text((pad, y), "4x, every 4th frame (0, 45, 90 ... deg), hitbox circle r14 drawn faintly (cyan)", fill=col, font=f)
    y += 18
    for n in names:
        d.text((2, y + 6), n, fill=col, font=f)
        for j in range(8):
            im = skin_frames[n][4 * j]
            z = d10.on_bg(im.resize((c4, c4), Image.NEAREST))
            zd = ImageDraw.Draw(z, "RGBA")
            cc, r = c4 / 2, HITBOX_R * 4
            zd.ellipse((cc - r, cc - r, cc + r - 1, cc + r - 1), outline=(90, 220, 255, 110), width=1)
            b.paste(z, (pad + j * (c4 + gap), y))
        y += c4 + 6
    b.convert("RGB").save(path)


def make_compare(now, flat, axis, path):
    """Three rows (now / flat 32 / axis 32), four skins at 1x and 3x, same wall clock."""
    names = list(axis)
    col = (190, 196, 220)
    f = font(12)
    fs = font(11)
    c3 = SIZE * 3
    lab_w, cell_w, gap = 150, SIZE + 10 + c3, 18
    row_h = c3 + 14
    left = lab_w + 4 * (cell_w + gap)
    panel_w = 120
    W = left + panel_w + 10
    H = 24 + 3 * row_h + 8
    rows = [("now: 8 frames,", "10 ticks each (167 ms)", now), ("flat 32: d10 r2", "spun flat, 3 ticks", flat), ("axis 32: d11", "tilted axis, 3 ticks", axis)]

    def draw(tn, ta, tf):
        im = Image.new("RGBA", (W, H), BG + (255,))
        dr = ImageDraw.Draw(im)
        dr.text((6, 5), "meteorite: current vs finer flat spin vs 3D tumble (all 1 tick = 1/60 s, same wall clock; each rock at 1x and 3x)", fill=col, font=fs)
        for ri, (l1, l2, src) in enumerate(rows):
            y = 24 + ri * row_h
            dr.text((6, y + 36), l1, fill=col, font=f)
            dr.text((6, y + 50), l2, fill=col, font=fs)
            idx = (tn, tf, ta)[ri]
            for si, n in enumerate(names):
                x = lab_w + si * (cell_w + gap)
                fr = src[n][idx]
                im.alpha_composite(fr, (x, y + (c3 - SIZE) // 2))
                im.alpha_composite(fr.resize((c3, c3), Image.NEAREST), (x + SIZE + 10, y))
        px, py = left + 10, 24
        dr.text((px, py), "d11 at 26 / 52 px", fill=col, font=fs)
        py += 16
        for n in names:
            fr = axis[n][ta]
            im.alpha_composite(fr.resize((26, 26), Image.LANCZOS), (px, py + 14))
            im.alpha_composite(fr.resize((52, 52), Image.LANCZOS), (px + 40, py))
            py += 58
        return im.convert("RGB")

    period = 8000
    ev = set()
    n = 0
    while round(n * 50 / 10) * 10 < period:
        ev.add(round(n * 50 / 10) * 10)
        n += 1
    n = 0
    while round(n * (1000 / 6) / 10) * 10 < period:
        ev.add(round(n * (1000 / 6) / 10) * 10)
        n += 1
    ts = sorted(ev)
    durs = [b - a for a, b in zip(ts, ts[1:] + [period])]
    assert min(durs) >= 20, min(durs)
    frames = []
    for t in ts:
        frames.append(draw(int((t + 5) / (1000 / 6)) % 8, int((t + 5) / 50) % FRAMES, int((t + 5) / 50) % FRAMES))
    pal = quant_palette(frames[:: max(1, len(frames) // 16)])
    qs = [fr.quantize(palette=pal, dither=Image.NONE) for fr in frames]
    qs[0].save(path, save_all=True, append_images=qs[1:], duration=durs, loop=0, disposal=1, optimize=False)
    return len(ts), W, H


def make_compare_r2(now, r1, r2, path):
    """Three rows (now / axis r1 / axis r2), four skins at 1x and 3x (now at 1x only),
    r2 also at 26 and 52 px in a corner. Same wall clock; 1 tick = 1/60 s."""
    names = list(r2)
    col = (190, 196, 220)
    f = font(12)
    fs = font(11)
    c3 = SIZE * 3
    lab_w, cell_w, gap = 150, SIZE + 10 + c3, 18
    row_h = c3 + 14
    left = lab_w + 4 * (cell_w + gap)
    panel_w = 130
    W = left + panel_w + 10
    H = 24 + 3 * row_h + 8
    rows = [("now: 8 frames,", "10 ticks each (167 ms)", now, False), ("axis r1: round balls", "tilted axis, 3 ticks", r1, True),
            ("axis r2: potatoes", "tilted axis, 3 ticks", r2, True)]

    def draw(tn, ta):
        im = Image.new("RGBA", (W, H), BG + (255,))
        dr = ImageDraw.Draw(im)
        dr.text((6, 5), "meteorite: current vs axis round 1 vs axis round 2 (1 tick = 1/60 s, same wall clock; each rock at 1x and 3x)", fill=col, font=fs)
        for ri, (l1, l2, src, big) in enumerate(rows):
            y = 24 + ri * row_h
            dr.text((6, y + 36), l1, fill=col, font=f)
            dr.text((6, y + 50), l2, fill=col, font=fs)
            idx = tn if ri == 0 else ta
            for si, n in enumerate(names):
                x = lab_w + si * (cell_w + gap)
                fr = src[n][idx]
                im.alpha_composite(fr, (x, y + (c3 - SIZE) // 2))
                if big:
                    im.alpha_composite(fr.resize((c3, c3), Image.NEAREST), (x + SIZE + 10, y))
        px, py = left + 10, 24
        dr.text((px, py), "r2 at 26 / 52 px", fill=col, font=fs)
        py += 16
        for n in names:
            fr = r2[n][ta]
            im.alpha_composite(fr.resize((26, 26), Image.LANCZOS), (px, py + 14))
            im.alpha_composite(fr.resize((52, 52), Image.LANCZOS), (px + 40, py))
            py += 58
        return im.convert("RGB")

    period = 8000
    ev = set()
    for step in (50, 1000 / 6):
        n = 0
        while round(n * step / 10) * 10 < period:
            ev.add(round(n * step / 10) * 10)
            n += 1
    ts = sorted(ev)
    durs = [b - a for a, b in zip(ts, ts[1:] + [period])]
    assert min(durs) >= 20, min(durs)
    frames = [draw(int((t + 5) / (1000 / 6)) % 8, int((t + 5) / 50) % FRAMES) for t in ts]
    pal = quant_palette(frames[:: max(1, len(frames) // 16)])
    qs = [fr.quantize(palette=pal, dither=Image.NONE) for fr in frames]
    qs[0].save(path, save_all=True, append_images=qs[1:], duration=durs, loop=0, disposal=1, optimize=False)
    return len(ts), W, H


def to_img(a):
    return d10.to_img(a)


def checks(frames):
    return d10.frame_checks([np.asarray(s).astype(float) for s in frames])


def main(argv=None):
    global SKIN_SET
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1, choices=(1, 2))
    ap.add_argument("--skins", default="abcd")
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--no-flat", action="store_true", help="round 1: skip the flat-32 renders (no compare gif)")
    a = ap.parse_args(argv)
    out = a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    names = list(a.skins)
    rnd = a.round
    SKIN_SET = SKINS if rnd == 1 else SKINS_R2
    suffix = "" if rnd == 1 else "-r2"
    jobs = [("axis", n, k) for n in names for k in range(FRAMES)]
    if rnd == 1 and not a.no_flat:
        jobs += [("flat", n, k) for n in names for k in range(FRAMES)]
    with Pool(8) as pool:
        res = pool.map(_job, jobs, chunksize=2)
    axis_m = {n: [None] * FRAMES for n in names}
    axis_s = {n: [None] * FRAMES for n in names}
    flat_s = {n: [None] * FRAMES for n in names}
    for kind, n, k, m, s in res:
        if kind == "axis":
            axis_m[n][k] = m
            axis_s[n][k] = to_img(s)
        else:
            flat_s[n][k] = to_img(s)
    for n in names:
        sk = SKIN_SET[n]
        stem = f"meteorite-d11{n}{suffix}"
        strip = make_strip(axis_s[n], SIZE)
        strip.save(out / f"{stem}.png")
        mstrip = make_strip([to_img(m.astype(float)) for m in axis_m[n]], MASTER)
        mstrip.save(out / f"{stem}-master.png")
        make_preview(axis_s[n], out / f"{stem}-preview.gif")
        ck = checks(axis_s[n])
        iw = int(np.argmin(ck["cov"]))
        print(f"skin {n}: axis lean {sk['axis'][0]:+.0f} in plane, {sk['axis'][1]:+.0f} toward viewer, total tilt {tilt_total(sk):.1f} deg"
              + (f", body {sk['body']}" if "body" in sk else "") + f"; strip {strip.size} {strip.mode}, master {mstrip.size}")
        print(f"  worst r14 cover {min(ck['cov']):.1f}% (frame {iw + 1}); r10 cover min {min(ck['cov10']):.1f}%; deepest bite {max(ck['depth']):.2f} px; "
              f"max opaque radius {ck['rmax']:.2f}; border px {ck['border']}")
    if rnd == 1:
        make_board(axis_s, out / "meteorite-d11-board.png")
        if not a.no_flat and len(names) == 4:
            now = {}
            for n, sn in zip(names, "abcd"):
                st = Image.open(ROOT / f"game/assets/sprites/meteorite_rock_{sn}.png").convert("RGBA")
                now[n] = [st.crop((k * SIZE, 0, k * SIZE + SIZE, SIZE)) for k in range(8)]
            cnt, w, h = make_compare(now, flat_s, axis_s, out / "meteorite-compare.gif")
            print(f"compare gif: {cnt} frames, {w} x {h}")
    else:
        make_board(axis_s, out / "meteorite-d11-r2-board.png",
                   title=f"meteorite d11 round 2, skins a-d: potato bodies, 3D tumble, 32 frames of {STEP_DEG:g} deg, 1x on the game background (36 x 36)")
        if len(names) == 4:
            now, r1 = {}, {}
            for n in names:
                st = Image.open(ROOT / f"game/assets/sprites/meteorite_rock_{n}.png").convert("RGBA")
                now[n] = [st.crop((k * SIZE, 0, k * SIZE + SIZE, SIZE)) for k in range(8)]
                s1 = Image.open(out / f"meteorite-d11{n}.png").convert("RGBA")
                r1[n] = [s1.crop((k * SIZE, 0, k * SIZE + SIZE, SIZE)) for k in range(FRAMES)]
            cnt, w, h = make_compare_r2(now, r1, axis_s, out / "meteorite-compare-r2.gif")
            print(f"compare gif: {cnt} frames, {w} x {h}")


if __name__ == "__main__":
    main()
