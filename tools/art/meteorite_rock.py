"""Shared renderer for the real-rock meteorite designs d7, d8 and d9.

Each design script (the d7 to d9 ones, no longer kept) defined a rock in 3D (a signed
distance field plus a shader). This module turns it into the 8-frame turn:

  * The rock is ray-marched in orthographic view at 8x the game size, turned
    45 degrees per frame about a tilted axis (8 steps = one full turn, so the
    loop is seamless). The light stays fixed (top-left) while the rock turns,
    because the shading is computed in view space (GDD 12 rule 13).
  * The hitbox is a circle r14 in the 28 x 28 frame (GDD 01-meteorite). The
    rock must never be smaller than it (GDD 07 rule 8). A design's field is
    calibrated here so that a sphere of radius 1 (= the hitbox, in rock
    radii) sits inside the rock with a margin: every frame then covers the
    whole circle, whatever the turn. The irregular parts reach out into the
    square's corners. Anything past the square is cut by the frame.
  * The thin fuchsia rim is added on the bottom side of the silhouette in
    view space, so it stays on the bottom while the rock turns (rule 8).

Nothing here ships (GDD 15). Libraries: Pillow and numpy only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"

SIZE = 28  # GDD 01-meteorite art_canvas (medium rock)
HITBOX_R = 14  # GDD 01-meteorite hitbox, medium variant
SCALE = 8  # GDD 12 art_style, sprites up to 64 px
MASTER = SIZE * SCALE
FRAMES = 8  # GDD 01-meteorite look_frames
STEP_DEG = 45.0  # GDD 01-meteorite look_frames
TICKS = 5  # GDD 01-meteorite look_ticks_per_frame
BG = (10, 13, 31)  # the dark game background
FUCHSIA = np.array([255.0, 28.0, 178.0])
RIM_DIR = np.array([-0.30, 0.95]) / np.hypot(-0.30, 0.95)  # bottom, leaning bottom-left
LIGHT = np.array([-0.52, -0.62, 0.60])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
VIEW_H = LIGHT + np.array([0.0, 0.0, 1.0])
VIEW_H = VIEW_H / np.linalg.norm(VIEW_H)
MARGIN = 0.035  # the rock is at least this much (rock radii) bigger than the hitbox


# ---------------------------------------------------------------- helpers
def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9)


def smoothstep(a: float, b: float, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ramp(x, stops):
    """stops: list of (x, (r, g, b)). Returns (..., 3) float."""
    xs = np.array([s[0] for s in stops], dtype=float)
    cs = np.array([s[1] for s in stops], dtype=float)
    return np.stack([np.interp(x, xs, cs[:, c]) for c in range(3)], -1)


def rotation(axis, deg: float) -> np.ndarray:
    a = np.asarray(axis, dtype=float)
    a = a / np.linalg.norm(a)
    t = np.deg2rad(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * (K @ K)


def fibonacci(n: int) -> np.ndarray:
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5**0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], -1)


def poly_field(P, normals, d, k):
    """Smooth intersection of half-spaces. Returns f (>=max plane, 1-Lipschitz)
    and the plane values g (N, m)."""
    g = P @ normals.T - d[None, :]
    gm = g.max(1)
    f = gm + np.log(np.exp(k * (g - gm[:, None])).sum(1)) / k
    return f, g


def smin(a, b, k):
    """Polynomial smooth minimum (a union that blends)."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def bowl(dist, r):
    t = np.clip(1 - (dist / r) ** 2, 0, 1)
    return t * t


class Lattice:
    """Value noise and cell (Worley) noise in 3D on a wrapped lattice."""

    def __init__(self, seed: int, n: int = 32):
        rng = np.random.default_rng(seed)
        self.n = n
        self.v = rng.random((n, n, n))
        self.w = rng.random((n, n, n, 4))

    def noise(self, P, freq):
        Q = P * freq
        i = np.floor(Q).astype(np.int64)
        f = Q - i
        u = f * f * f * (f * (f * 6 - 15) + 10)
        m = self.n - 1
        out = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    val = self.v[(i[:, 0] + dx) & m, (i[:, 1] + dy) & m, (i[:, 2] + dz) & m]
                    wx = u[:, 0] if dx else 1 - u[:, 0]
                    wy = u[:, 1] if dy else 1 - u[:, 1]
                    wz = u[:, 2] if dz else 1 - u[:, 2]
                    out = out + val * wx * wy * wz
        return out

    def fbm(self, P, freq, octaves=3):
        tot, amp, norm = 0.0, 1.0, 0.0
        for o in range(octaves):
            tot = tot + amp * self.noise(P + 7.13 * o, freq * 2**o)
            norm += amp
            amp *= 0.5
        return tot / norm

    def grad(self, P, freq, octaves=1, eps=0.01):
        """Gradient of the noise with respect to P (N, 3)."""
        fn = (lambda Q: self.noise(Q, freq)) if octaves == 1 else (lambda Q: self.fbm(Q, freq, octaves))
        g = np.zeros_like(P)
        for a in range(3):
            e = np.zeros(3)
            e[a] = eps
            g[:, a] = (fn(P + e) - fn(P - e)) / (2 * eps)
        return g

    def worley(self, P, scale, rad_lo=0.16, rad_span=0.12):
        """Nearest 'grain' by distance relative to its own radius.
        Returns (q, centre, radius) in object units; q < 1 is inside a grain."""
        Q = P * scale
        ci = np.floor(Q).astype(np.int64)
        m = self.n - 1
        best = np.full(len(P), 1e9)
        bc = np.zeros_like(P)
        br = np.ones(len(P))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cell = ci + np.array([dx, dy, dz])
                    w = self.w[cell[:, 0] & m, cell[:, 1] & m, cell[:, 2] & m]
                    feat = cell + 0.15 + 0.7 * w[:, :3]
                    rad = rad_lo + rad_span * w[:, 3]  # in cell units
                    q = np.linalg.norm(Q - feat, axis=1) / rad
                    sel = q < best
                    best = np.where(sel, q, best)
                    bc = np.where(sel[:, None], feat / scale, bc)
                    br = np.where(sel, rad / scale, br)
        return best, bc, br


def tangent(grad, n):
    return grad - (grad * n).sum(1, keepdims=True) * n


def lambert(nv):
    return np.clip(nv @ LIGHT, 0, 1)


def blinn(nv):
    return np.clip(nv @ VIEW_H, 0, 1)


def ao(design, Po, n, h=0.14):
    return np.clip(design.field(Po + n * h) / h, 0, 1)


# ---------------------------------------------------------------- calibration
def calibrate(design, n_samples: int = 120000) -> float:
    """Shift the field so a sphere of radius 1 is inside the rock by MARGIN."""
    rng = np.random.default_rng(1)
    u = normalize(rng.normal(size=(n_samples, 3)))
    # also the fibonacci spiral, dense, for evenly spread points
    u = np.concatenate([u, fibonacci(40000)])
    f = np.concatenate([design.field_raw(u[i : i + 40000]) for i in range(0, len(u), 40000)])
    return float(f.max() + MARGIN)


# ---------------------------------------------------------------- render
def render_frame(design, R: np.ndarray, half: float = 1.25):
    """One frame at master size. Returns (rgba float (224,224,4), cut px at master)."""
    n = int(round(MASTER * half))
    c = n / 2
    ys, xs = np.mgrid[0:n, 0:n]
    x = ((xs + 0.5 - c) / (MASTER / 2)).ravel()
    y = ((ys + 0.5 - c) / (MASTER / 2)).ravel()
    bound = design.bound
    r2 = x * x + y * y
    alive = np.nonzero(r2 < bound**2)[0]
    zc = np.sqrt(bound**2 - r2[alive])
    zmin = -zc.copy()
    hit_idx, hit_z = [], []
    for _ in range(110):
        if len(alive) == 0:
            break
        Pv = np.stack([x[alive], y[alive], zc], 1)
        f = design.field(Pv @ R)
        hit = f < 0.002
        if hit.any():
            hit_idx.append(alive[hit])
            hit_z.append(zc[hit])
        step = np.maximum(f * 0.8, 0.002)
        zc = zc - step
        keep = (~hit) & (zc > zmin)
        alive, zc, zmin = alive[keep], zc[keep], zmin[keep]
    out = np.zeros((n * n, 4), dtype=np.float64)
    if hit_idx:
        idx = np.concatenate(hit_idx)
        z = np.concatenate(hit_z)
        Pv = np.stack([x[idx], y[idx], z], 1)
        Po = Pv @ R
        eps = 0.006
        gr = np.zeros_like(Po)
        for a in range(3):
            e = np.zeros(3)
            e[a] = eps
            gr[:, a] = design.field(Po + e) - design.field(Po - e)
        n_obj = normalize(gr)
        rgb = design.shade(Po, n_obj, R)
        out[idx, :3] = np.clip(rgb, 0, 255)
        out[idx, 3] = 255.0
    out = out.reshape(n, n, 4)
    lo = (n - MASTER) // 2
    crop = out[lo : lo + MASTER, lo : lo + MASTER].copy()
    cut = float((out[..., 3] > 128).sum() - (crop[..., 3] > 128).sum())
    return crop, cut


def shift_mask(m: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """m sampled at (x+dx, y+dy), zero padded. Integer shifts."""
    h, w = m.shape
    ix, iy = int(round(dx)), int(round(dy))
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -iy), min(h, h - iy)
    xs0, xs1 = max(0, -ix), min(w, w - ix)
    out[ys0:ys1, xs0:xs1] = m[ys0 + iy : ys1 + iy, xs0 + ix : xs1 + ix]
    return out


def add_rim(rgba: np.ndarray, strength: float = 0.48) -> np.ndarray:
    """Thin fuchsia rim on the bottom side, drawn in view space."""
    a = (rgba[..., 3] > 128).astype(np.float64)
    offsets = [(4, 1.0), (8, 0.7), (12, 0.35)]
    acc = np.zeros_like(a)
    wsum = 0.0
    for o, w in offsets:
        sm = shift_mask(a, RIM_DIR[0] * o, RIM_DIR[1] * o)
        acc += w * (1 - sm)
        wsum += w
    rim = a * acc / wsum
    img = Image.fromarray((rim * 255).astype(np.uint8), "L").filter(
        __import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(2.0)
    )
    rim = np.asarray(img, dtype=np.float64) / 255 * a * strength
    out = rgba.copy()
    out[..., :3] = rgba[..., :3] * (1 - rim[..., None]) + FUCHSIA * rim[..., None]
    return out


def to_img(a: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "RGBA")


def shrink(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.LANCZOS, reducing_gap=None)


# ---------------------------------------------------------------- outputs
def font(size: int):
    for p in (
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def on_bg(img: Image.Image) -> Image.Image:
    b = Image.new("RGBA", img.size, BG + (255,))
    b.alpha_composite(img)
    return b


def coverage(asset: Image.Image) -> float:
    """Share of pixels whose centre lies inside the hitbox circle r14 with alpha >= 128."""
    a = np.asarray(asset)[..., 3]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    inside = np.hypot(xx + 0.5 - SIZE / 2, yy + 0.5 - SIZE / 2) <= HITBOX_R
    return float((a[inside] >= 128).mean() * 100)


def make_board(frames28, frames20, frames40, path: Path, title: str):
    f = font(11)
    pad = 12
    cell4 = SIZE * 4
    W = FRAMES * (cell4 + 8) + 2 * pad
    H = pad + 16 + 36 + 16 + cell4 + 16 + 46 + 24
    b = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(b)
    col = (190, 196, 220)
    d.text((pad, 4), title + ": 1x on the game background", fill=col, font=f)
    y1 = pad + 16
    for i, im in enumerate(frames28):
        b.alpha_composite(im, (pad + i * (cell4 + 8) + (cell4 - SIZE) // 2, y1))
    y2 = y1 + 36 + 4
    d.text((pad, y2 - 2), "4x, hitbox circle r14 drawn faintly", fill=col, font=f)
    y2 += 14
    for i, im in enumerate(frames28):
        z = on_bg(im.resize((cell4, cell4), Image.NEAREST))
        zd = ImageDraw.Draw(z, "RGBA")
        cc, r = cell4 / 2, HITBOX_R * 4
        zd.ellipse((cc - r, cc - r, cc + r - 1, cc + r - 1), outline=(90, 220, 255, 110), width=1)
        b.paste(z, (pad + i * (cell4 + 8), y2))
    y3 = y2 + cell4 + 6
    d.text((pad, y3), "20 px and 40 px at 1x (small and big variants)", fill=col, font=f)
    y3 += 16
    for i in range(FRAMES):
        x0 = pad + i * (cell4 + 8)
        b.alpha_composite(frames20[i], (x0 + 14, y3 + 10))
        b.alpha_composite(frames40[i], (x0 + 14 + 20 + 14, y3))
    b.convert("RGB").save(path)


def make_gif(frames28, path: Path):
    imgs = []
    for im in frames28:
        z = on_bg(im.resize((SIZE * 4, SIZE * 4), Image.NEAREST)).convert("RGB")
        imgs.append(z)
    # 5 ticks = 83.3 ms; a GIF counts in 10 ms, so 80 / 80 / 90 averages 83.3.
    dur = [80, 90, 80, 80, 90, 80, 80, 90]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=dur, loop=0, disposal=2)


def luminance(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def run(design, name: str, argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    a = ap.parse_args(argv)
    out = a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{name}-r{a.round}"

    design.offset = calibrate(design)
    print(f"{name}: calibration shift {design.offset:+.3f}")
    R0 = design.R0
    master_frames, frames28, frames20, frames40 = [], [], [], []
    stats = []
    for k in range(FRAMES):
        R = rotation(design.axis, STEP_DEG * k) @ R0
        rgba, cut = render_frame(design, R)
        rgba = add_rim(rgba)
        m = to_img(rgba)
        a28 = shrink(m, SIZE)
        master_frames.append(m)
        frames28.append(a28)
        frames20.append(shrink(m, 20))
        frames40.append(shrink(m, 40))
        arr = np.asarray(a28).astype(float)
        op = arr[..., 3] >= 128
        yy, xx = np.mgrid[0:SIZE, 0:SIZE]
        rr = np.hypot(xx + 0.5 - SIZE / 2, yy + 0.5 - SIZE / 2)
        stats.append(
            dict(
                cov=coverage(a28),
                area=op.sum() / (np.pi * HITBOX_R**2),
                rmax=rr[op].max(),
                cut=cut / SCALE**2,
                lum=luminance(arr[..., :3])[op].mean(),
                lum_dark=np.percentile(luminance(arr[..., :3])[op], 10),
                lum_lit=np.percentile(luminance(arr[..., :3])[op], 90),
            )
        )
    strip = Image.new("RGBA", (SIZE * FRAMES, SIZE), (0, 0, 0, 0))
    mstrip = Image.new("RGBA", (MASTER * FRAMES, MASTER), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.paste(frames28[i], (i * SIZE, 0))
        mstrip.paste(master_frames[i], (i * MASTER, 0))
    strip.save(out / f"{stem}.png")
    mstrip.save(out / f"{stem}-master.png")
    make_board(frames28, frames20, frames40, out / f"{stem}-board.png", name)
    make_gif(frames28, out / f"{stem}-preview.gif")
    print(f"strip {strip.size} {strip.mode}, master {mstrip.size}")
    print("frame  cover%  area/circle  rmax_px  cut_px  lum(mean/p10/p90)")
    for i, s in enumerate(stats):
        print(
            f"{i + 1:>4}  {s['cov']:6.1f}  {s['area']:10.3f}  {s['rmax']:7.2f}  {s['cut']:6.1f}"
            f"  {s['lum']:5.0f}/{s['lum_dark']:4.0f}/{s['lum_lit']:4.0f}"
        )
    print(
        f"min cover {min(s['cov'] for s in stats):.1f}%  mean area ratio "
        f"{np.mean([s['area'] for s in stats]):.3f}  rmax range "
        f"{min(s['rmax'] for s in stats):.2f}..{max(s['rmax'] for s in stats):.2f}  "
        f"max cut {max(s['cut'] for s in stats):.1f} px"
    )
    return stats
