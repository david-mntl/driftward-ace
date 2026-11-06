"""Planet, design 5: ocean world. Deep violet seas and pale continents.

Drawn at 8x the game size (512 x 512 master), then shrunk to 64 x 64. The planet
fills the hitbox circle exactly: radius 32 px at game size (256 px in the master),
centered, so the silhouette touches all four edges of the canvas. The pull-field
rings are not part of the image: the game draws them.

Values come from docs/design/gdd/drifters/08-planet.md (size 64, hitbox radius 32,
art_canvas 64 x 64) and docs/design/gdd/12-art-and-audio.md (art_style 8x master;
rule 6: solid fuchsia stays with coins, so the rim is a thin accent only; rule 8:
thin fuchsia rim on the bottom side; hard white highlight, deep navy shadows).

How it is drawn, in order:
  1. Every pixel is a point on a unit sphere, tilted, so land wraps around it.
  2. Height: many random waves at several scales add up to a height map. Land is
     where the height is above the sea line. Shelf water is the band just under it.
  3. Sea: a deep violet ramp that lightens over the shelf. A pale foam line sits on
     the coast. Pale polar ice caps the top.
  4. Land: pale lilac lowlands rising to near-white highlands, with a soft bump
     from the height map so ridges catch the light.
  5. Light from the upper left: shade, limb roll-off with a violet glaze so the
     edge stays lighter than the background, a thin violet haze at the edge.
  6. A small hard white glint on the sea, then a thin fuchsia rim on the bottom
     side (toward the lower-left black hole), fading out at both ends.

Outputs, for --round n (default 1), in --out-dir (default staging/assets/sprites):
  planet-d5-r<n>.png          the asset, 64 x 64 RGBA
  planet-d5-r<n>-master.png   the 512 x 512 master
  planet-d5-r<n>-board.png    preview board: 1x on the dark background, 4x zoom
                              with the hitbox circle, for the UI Art Critic
  planet-d5-r<n>.piskel       the asset as a one-frame Piskel file, layers
                              sea, land, haze, glint, rim

Usage: python3 tools/art/planet-d5.py [--round N] [--seed S] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"

GAME = 64  # asset size, px (08-planet.md art_canvas)
UP = 8  # master scale (12-art-and-audio.md art_style, sprites up to 64 px)
N = GAME * UP  # 512
R = N / 2  # planet radius in the master: radius 32 at game size
HITBOX_R = 32  # px at game size (08-planet.md hitbox)

NAVY = (8, 10, 28)  # the board's dark background
TXT = (200, 205, 225)

LIGHT = np.array([-0.50, -0.58, 0.64])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HOLE_2D = np.array([-0.40, 0.92])
HOLE_2D = HOLE_2D / np.linalg.norm(HOLE_2D)

# Sea ramp, deepest to shelf. Deep violet; the shelf is a lighter violet.
SEA = np.array([(52, 14, 112), (82, 26, 150), (116, 48, 184), (148, 84, 212), (178, 124, 234)], dtype=np.float32)
# Land ramp, low to high: pale lilac to near-white.
LAND = np.array([(168, 126, 214), (200, 168, 234), (228, 208, 250), (252, 248, 255)], dtype=np.float32)
ICE = np.array([232, 218, 255], dtype=np.float32)
LAND_SH = np.array([70, 36, 130], dtype=np.float32)
SHADOW = np.array([14, 8, 52], dtype=np.float32)
LIMB_LIGHT = np.array([104, 54, 190], dtype=np.float32)
FOAM = np.array([200, 168, 250], dtype=np.float32)
RIM = np.array([240, 60, 190], dtype=np.float32)  # thin fuchsia accent
WHITE = np.array([255, 255, 255], dtype=np.float32)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blur(a, sigma=4.0):
    """Gaussian blur of a float array (separable, edges repeated)."""
    rad = int(sigma * 3) + 1
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sigma) ** 2)
    k = (k / k.sum()).astype(np.float32)
    o = np.pad(a.astype(np.float32), rad, mode="edge")
    o = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 0, o)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 1, o)


def ramp(table, t):
    t = np.clip(t, 0.0, 1.0) * (len(table) - 1)
    i = np.clip(np.floor(t).astype(int), 0, len(table) - 2)
    f = (t - i)[..., None]
    return table[i] * (1 - f) + table[i + 1] * f


def waves(p, rng, count=60, f0=1.5, f1=11.0, falloff=0.70):
    """Seamless 3D height from a sum of random plane waves (p is (h, w, 3))."""
    out = np.zeros(p.shape[:2], dtype=np.float32)
    total = 0.0
    for i in range(count):
        f = f0 * (f1 / f0) ** (i / (count - 1))
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        ph = rng.random() * 6.283
        a = (f0 / f) ** falloff
        out += a * np.sin(f * 3.1 * (p @ d.astype(np.float32)) + ph)
        total += a
    return out / total * 2.2


def render_layers(seed):
    rng = np.random.default_rng(seed)

    c = (np.arange(N, dtype=np.float32) + 0.5 - R) / R
    u, v = np.meshgrid(c, c)
    r = np.sqrt(u * u + v * v)
    rc = np.maximum(r, 1.0)
    uc, vc = u / rc, v / rc
    z = np.sqrt(np.clip(1.0 - uc * uc - vc * vc, 0.0, 1.0))
    sphere_n = np.stack([uc, vc, z], axis=-1)

    tz, tx = np.radians(-20), np.radians(14)
    cz, sz = np.cos(tz), np.sin(tz)
    x1 = uc * cz - vc * sz
    y1 = uc * sz + vc * cz
    cx_, sx_ = np.cos(tx), np.sin(tx)
    y2 = y1 * cx_ - z * sx_
    z2 = y1 * sx_ + z * cx_
    p = np.stack([x1, y2, z2], axis=-1).astype(np.float32)

    # 2. Height and land.
    h = waves(p, rng)
    sea_line = np.quantile(h[r < 0.98], 0.58)  # about 40% land
    d_ = h - sea_line  # >0 land
    land = smoothstep(-0.004, 0.004, d_)
    shelf = smoothstep(-0.20, 0.0, d_) * (1.0 - land)
    deep_var = 0.5 + 0.5 * waves(p, rng, count=18, f0=1.2, f1=4.0)  # slow tone drift in the deep sea

    # 3. Sea.
    st = np.clip(0.10 + 0.25 * deep_var + 0.65 * shelf ** 0.9, 0, 1)
    sea = ramp(SEA, st * 0.95)
    coast = np.exp(-((d_ + 0.012) / 0.014) ** 2) * (1.0 - land)  # pale line just outside the coast
    coast_in = np.exp(-((d_ - 0.0) / 0.012) ** 2)
    # Polar ice: top of the sphere (tilted y), ragged edge from the height map.
    ice_edge = -p[..., 1] + 0.10 * h
    ice = smoothstep(0.86, 0.90, ice_edge)

    # 4. Land: lowland to highland, bump from the height map.
    elev = np.clip(d_ / 0.40, 0, 1)
    landc = ramp(LAND, 0.30 + 0.70 * elev ** 0.7 + 0.10 * (deep_var - 0.5))
    H = blur(np.maximum(d_, 0) * 6.0, sigma=5.0)
    gy, gx = np.gradient(H)
    n = sphere_n + np.stack([-gx * 40.0, -gy * 40.0, np.zeros_like(gx)], axis=-1)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    land_n = np.where(land[..., None] > 0.5, n, sphere_n)

    # 5. Light.
    diff_s = np.clip(sphere_n @ LIGHT, 0, 1)
    diff_l = np.clip(land_n @ LIGHT, 0, 1)
    sea_lit = smoothstep(0.0, 0.75, diff_s)[..., None]
    land_lit = smoothstep(0.0, 0.70, diff_l)[..., None]
    sea_body = SHADOW + (sea - SHADOW) * (0.12 + 0.88 * sea_lit)
    land_body = LAND_SH + (landc - LAND_SH) * (0.22 + 0.78 * land_lit)
    ice_a = ice * (1.0 - 0.0 * land)
    body = sea_body
    body = body + (FOAM * (0.45 + 0.55 * sea_lit) - body) * np.clip(coast * 0.85, 0, 1)[..., None]
    body = body + (land_body - body) * land[..., None]
    body = body + (LAND_SH + (ICE - LAND_SH) * (0.55 + 0.45 * land_lit) - body) * ice_a[..., None]

    # Limb roll-off, then a violet glaze so the edge stays above the background.
    limb = smoothstep(0.50, 1.0, r)[..., None]
    shade = np.clip(1.0 - 0.16 * limb - 0.18 * limb * (1.0 - diff_s[..., None]), 0, 1)
    body = SHADOW + (body - SHADOW) * shade
    bl = (body * np.array([0.3, 0.59, 0.11], dtype=np.float32)).sum(-1, keepdims=True)
    body = np.clip(bl + (body - bl) * 1.2, 0, 255)
    haze_a = smoothstep(0.82, 0.97, r) * (0.10 + 0.30 * (1.0 - diff_s))

    # Glint: hard white, on the sea only (land is matte).
    hvec = LIGHT + np.array([0, 0, 1.0])
    hvec = hvec / np.linalg.norm(hvec)
    spec = np.clip(sphere_n @ hvec, 0.0, 1.0) ** 420
    spec_a = 0.9 * smoothstep(0.30, 0.52, spec) * (1.0 - land) * (1.0 - ice_a)

    # Rim: bottom side, toward the black hole. Thin, fades out at both ends.
    outward = np.stack([u, v], axis=-1) / np.maximum(r, 1e-6)[..., None]
    toward = np.clip((outward * HOLE_2D).sum(axis=-1), 0.0, 1.0)
    bottom = smoothstep(0.02, 0.60, outward[..., 1])
    facing = np.clip(0.55 * bottom + 0.45 * toward, 0.0, 1.0) * bottom ** 0.5
    band = smoothstep(0.950, 0.985, r)
    rim_a = facing * band * 0.85

    alpha = np.clip((1.0 - r) * R / 5.0 + 0.5, 0.0, 1.0)
    return dict(body=body, land=land, ice=ice_a, haze_a=haze_a, spec_a=spec_a, rim_a=rim_a, alpha=alpha,
                sea_body=sea_body, land_body=land_body, coast=coast)


def compose(L, parts=("body", "haze", "spec", "rim")):
    col = L["body"].copy()
    if "haze" in parts:
        col = col + (LIMB_LIGHT - col) * L["haze_a"][..., None]
    if "spec" in parts:
        col = col + (WHITE - col) * L["spec_a"][..., None]
    if "rim" in parts:
        col = col + (RIM - col) * L["rim_a"][..., None]
    return col


def to_image(col, alpha):
    rgb = np.clip(col, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, (alpha * 255 + 0.5).astype(np.uint8)]), "RGBA")


def shrink(master):
    """512 -> 64. Colors weighted by alpha, alpha with a box filter so the circle edge stays clean."""
    m = np.asarray(master).astype(np.float32)
    a = m[..., 3:4] / 255.0
    chans = []
    for i in range(3):
        ch = Image.fromarray((m[..., i] * a[..., 0]).astype(np.float32), mode="F").resize((GAME, GAME), Image.BOX)
        chans.append(np.asarray(ch))
    ach = np.asarray(Image.fromarray(a[..., 0].astype(np.float32), mode="F").resize((GAME, GAME), Image.BOX))
    rgb = np.stack(chans, -1) / np.maximum(ach[..., None], 1e-4)
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(ach * 255.0, 0, 255)])
    return Image.fromarray((out + 0.5).astype(np.uint8), "RGBA")


def board(sprite):
    """1x on the dark background, and a 4x zoom with the hitbox circle drawn faintly."""
    pad, zoom = 20, 4
    zw = GAME * zoom
    w = pad + 96 + pad + zw + pad
    h = pad + 14 + zw + pad
    img = Image.new("RGBA", (w, h), NAVY + (255,))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((pad, pad - 12), "1x", fill=TXT, font=font)
    d.text((pad + 96 + pad, pad - 12), "4x, hitbox r32", fill=TXT, font=font)
    img.alpha_composite(sprite, (pad + (96 - GAME) // 2, pad + 14 + (zw - GAME) // 2))
    big = sprite.resize((zw, zw), Image.NEAREST)
    zx, zy = pad + 96 + pad, pad + 14
    img.alpha_composite(big, (zx, zy))
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    cx, cy = zx + zw / 2, zy + zw / 2
    rr = HITBOX_R * zoom
    for a0 in range(0, 360, 12):  # dashed, neutral grey so it is not read as sprite pixels
        od.arc((cx - rr, cy - rr, cx + rr, cy + rr), a0, a0 + 6, fill=(255, 255, 255, 70), width=1)
    img.alpha_composite(over)
    return img


def piskel(path, name, layers):
    spec = importlib.util.spec_from_file_location("piskel_file", ROOT / "tools/art/piskel_file.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.write_piskel(path, name, layers)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    stem = f"planet-d5-r{args.round}"

    L = render_layers(args.seed)
    alpha = L["alpha"]
    master = to_image(compose(L), alpha)
    sprite = shrink(master)
    master.save(out / f"{stem}-master.png")
    sprite.save(out / f"{stem}.png")
    board(sprite).save(out / f"{stem}-board.png")

    # Piskel layers, bottom first. Each layer is shrunk on its own.
    shape = L["body"].shape
    landmask = np.clip(L["land"] + L["ice"], 0, 1)
    sea = shrink(to_image(L["sea_body"], alpha))
    land = shrink(to_image(np.where(L["ice"][..., None] > 0.5, ICE, L["land_body"]), alpha * landmask))
    haze = shrink(to_image(np.broadcast_to(LIMB_LIGHT, shape), alpha * L["haze_a"]))
    glint = shrink(to_image(np.broadcast_to(WHITE, shape), alpha * L["spec_a"]))
    rim = shrink(to_image(np.broadcast_to(RIM, shape), alpha * L["rim_a"]))
    piskel(out / f"{stem}.piskel", "planet-d5",
           [("sea", [sea]), ("land", [land]), ("haze", [haze]), ("glint", [glint]), ("rim", [rim])])
    print(f"wrote {stem}: master {master.size}, sprite {sprite.size}, seed {args.seed}")


if __name__ == "__main__":
    main()
