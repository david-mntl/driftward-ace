"""Floating island, design 3: broken plate (rectangle, 320 x 120).

Spec: docs/design/gdd/drifters/05-floating-islands.md (look_reference, art_canvas,
shapes, hitbox) and docs/design/gdd/12-art-and-audio.md (rules 2, 6, 8, 9).

Direction: cracked green-tinted stone slabs fitted together, dark seams. The
slabs are Voronoi cells around jittered seeds. The ground fills the whole box,
no transparent edge. Each slab gets a hard white highlight on its edge facing
the light (top left) and a shaded edge on the far side. A darker green edge is
drawn inside the shape. A thin, soft fuchsia rim runs along the bottom (r2: 1 px, half opaque; r3: broken and faded).
r3: darker jagged underbelly and chipped corners (floating cue), top highlight per slab, softer lip, lighter seams.
Drawn at 4x (1280 x 480), then shrunk to game size.

Usage: python3 tools/art/floating-island-d3.py [round]   (default 1)
Writes, in staging/assets/sprites/:
  floating-island-d3-r<n>.png          the asset, 320 x 120
  floating-island-d3-r<n>-master.png   the 1280 x 480 master
  floating-island-d3-r<n>-board.png    the preview board for the UI Art Critic
  floating-island-d3-r<n>.piskel       layers: slabs, seams, cracks, light, underside, edge, rim
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from piskel_file import write_piskel  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging" / "assets" / "sprites"

GAME_W, GAME_H = 320, 120  # spec: art_canvas, rectangle
SCALE = 4  # spec: GDD 12 art_style, 4x for sprites bigger than 64 px
W, H = GAME_W * SCALE, GAME_H * SCALE
SEED = 20261031

EDGE = (35, 90, 45)  # spec placeholder_look edge green
FUCHSIA = (255, 0, 174)  # GDD 12 HUD ship_lines value, used only as a thin rim
SEAM = (9, 26, 32)
SEAM_HALF = 4  # master px, so a seam is about 2 px in the game (r3: was 2.5, seams were heavy)
LIGHT = np.array([-0.6, -0.8], dtype=np.float32)  # points toward the light, top left

# Slab greens: green-tinted stone, a little grey in each.
SLAB_COLORS = [(90, 146, 100), (86, 143, 98), (93, 148, 100), (88, 144, 104)]  # r2: narrow spread, one ground


def noise(rng: np.random.Generator, cell: int) -> np.ndarray:
    """Smooth value noise, 0..1, size H x W."""
    gh, gw = H // cell + 2, W // cell + 2
    grid = rng.random((gh, gw)).astype(np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:H, :W] / 255.0


def make_seeds(prng: random.Random) -> np.ndarray:
    """Jittered brick grid of slab centers: 3 rows, 7 columns, odd rows shifted half a cell."""
    cols, rows = 7, 3
    cw, ch = W / cols, H / rows
    pts = []
    for r in range(rows):
        for c in range(cols + 1):
            x = (c + (0.5 if r % 2 else 0.0)) * cw + prng.uniform(-0.28, 0.28) * cw
            y = (r + 0.5) * ch + prng.uniform(-0.3, 0.3) * ch
            if -0.2 * cw < x < W + 0.2 * cw:
                pts.append((x, y))
    return np.array(pts, dtype=np.float32)


def voronoi(seeds: np.ndarray):
    """Returns label, edge distance (px to the nearest seam line) and the unit vector
    from the slab's seed to its neighbor across that seam."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.empty((len(seeds), H, W), dtype=np.float32)
    for i, (sx, sy) in enumerate(seeds):
        d[i] = (xx - sx) ** 2 + (yy - sy) ** 2
    i1 = np.argmin(d, axis=0)
    d1 = np.take_along_axis(d, i1[None], 0)[0]
    np.put_along_axis(d, i1[None], np.inf, 0)
    i2 = np.argmin(d, axis=0)
    d2 = np.take_along_axis(d, i2[None], 0)[0]
    p1, p2 = seeds[i1], seeds[i2]
    sep = np.linalg.norm(p2 - p1, axis=-1)
    edge = (d2 - d1) / (2 * sep)
    n = (p2 - p1) / sep[..., None]
    return i1, edge, n, xx, yy


def make_slabs(rng, prng, label, edge, xx, yy, nslabs) -> Image.Image:
    """Opaque stone: one tone per slab, a soft pillow, mottling, deeper toward the bottom."""
    tone = np.zeros((nslabs, 3), dtype=np.float32)
    for i in range(nslabs):
        tone[i] = np.array(prng.choice(SLAB_COLORS), dtype=np.float32) + prng.uniform(-4, 4)
    base = tone[label]
    # Pillow: slab centers a touch brighter, borders a touch darker.
    pillow = 0.88 + 0.16 * np.clip(edge / 70.0, 0, 1)
    base = base * pillow[..., None]
    # Mottling at two scales, a few points of brightness either way.
    mott = (noise(rng, 70) - 0.5) * 10 + (noise(rng, 20) - 0.5) * 6
    base += mott[..., None] * np.array([0.8, 1.0, 0.8], dtype=np.float32)
    # Fine grain along one diagonal, like cut stone.
    grain = (np.sin((xx * 0.8 + yy * 0.5) / 5.0 + noise(rng, 40) * 9) * 0.5 + 0.5) * 6 - 3
    base += grain[..., None] * 0.7
    # Deeper and cooler toward the bottom, but still green stone.
    t = np.clip(yy / H, 0, 1) ** 1.2
    deep = np.array([26, 70, 66], dtype=np.float32)
    k = (t * 0.5)[..., None]
    base = base * (1 - k) + deep * k
    # Seam floor: dark all the way across, so the plate stays one opaque piece.
    seam_mask = (edge < SEAM_HALF)[..., None]
    base = np.where(seam_mask, np.array(SEAM, dtype=np.float32), base)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def make_seams(edge) -> Image.Image:
    """Seam shading: a soft shadow on both sides of the seam, so it reads as a groove."""
    a = np.where(edge < SEAM_HALF, 1.0, np.exp(-(np.clip(edge - SEAM_HALF, 0, None) / 11.0) ** 1.5) * 0.55)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = SEAM
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def make_cracks(prng, label, nslabs) -> Image.Image:
    """Thin cracks that run inside single slabs, with a faint light line beside each."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    lab = label
    made = 0
    tries = 0
    while made < 6 and tries < 600:
        tries += 1
        x, y = prng.uniform(60, W - 60), prng.uniform(40, H - 40)
        ang = prng.uniform(0, 6.283)
        home = lab[int(y), int(x)]
        pts = [(x, y)]
        for _ in range(prng.randint(8, 13)):
            ang += prng.uniform(-0.8, 0.8)
            x += 12 * np.cos(ang)
            y += 12 * np.sin(ang)
            if not (3 < x < W - 3 and 3 < y < H - 3) or lab[int(y), int(x)] != home:
                break
            pts.append((x, y))
        if len(pts) < 5:
            continue
        made += 1
        ld.line([(px + 3, py + 3) for px, py in pts], fill=(214, 240, 226, 50), width=3, joint="curve")
        ld.line(pts, fill=(14, 40, 40, 200), width=5, joint="curve")
    return layer


def make_light(edge, n, xx, yy, prng) -> Image.Image:
    """Hard white highlight on each slab edge facing the light, shade on the far side,
    and a few short glints on the stone (the glossy, wet finish)."""
    facing = n[..., 0] * LIGHT[0] + n[..., 1] * LIGHT[1]  # > 0: the seam is on the lit side
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    # Lit lip: a hard bright band just outside the seam floor.
    e = edge - SEAM_HALF
    prof = np.clip(1 - np.abs(e - 5.0) / 6.0, 0, 1)
    prof = prof * prof * (3 - 2 * prof)  # smoothstep: no hard step, so diagonals shrink clean
    lip = prof * np.clip(facing * 1.6, 0, 1) * 0.85 * (e > -1)
    rgba[..., :3] += np.array([246, 255, 244], dtype=np.float32) * lip[..., None]
    rgba[..., 3] += lip
    # Soft lift behind the lip.
    soft = np.exp(-(np.clip(e, 0, None) / 16.0) ** 2) * np.clip(facing, 0, 1) * 0.16 * (e > 0)
    rgba[..., :3] += np.array([210, 250, 215], dtype=np.float32) * soft[..., None]
    rgba[..., 3] += soft
    # Far side: a dark rim hugging the seam, away from the light.
    shade = np.exp(-(np.clip(e, 0, None) / 14.0) ** 2) * np.clip(-facing, 0, 1) * 0.5 * (e > 0)
    rgba[..., :3] += np.array([8, 24, 40], dtype=np.float32) * shade[..., None]
    rgba[..., 3] += shade
    a = np.clip(rgba[..., 3], 1e-4, 1)
    out = np.zeros((H, W, 4), dtype=np.uint8)
    out[..., :3] = np.clip(rgba[..., :3] / a[..., None], 0, 255).astype(np.uint8)
    out[..., 3] = (np.clip(rgba[..., 3], 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(1.6))


def make_edge() -> Image.Image:
    """The darker edge, drawn inside the shape: 2 px (8 at master) solid, then a soft fade."""
    solid, fade = 8, 14
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy]).astype(np.float32)
    a = np.where(dist < solid, 1.0, np.clip(1.0 - (dist - solid) / fade, 0, 1) * 0.35)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = EDGE
    rgba[..., 3] = (a * 255).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    return img


def make_top_light(edge, label, nslabs, prng) -> Image.Image:
    """Highlight that follows the top slab edges: a short light line under the dark edge,
    one piece per slab, each with its own strength and tapered ends so it never runs as a bar.
    The same on the left side."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    strength = np.array([prng.uniform(0.0, 0.7) for _ in range(nslabs)], dtype=np.float32)
    s_lab = strength[label]
    seam_gap = np.clip((edge - SEAM_HALF - 10) / 24.0, 0, 1)  # tapers to 0 toward each seam
    top = np.clip(1 - np.abs(yy - 12) / 4.0, 0, 1) ** 1.5 * seam_gap
    left = np.clip(1 - np.abs(xx - 12) / 4.0, 0, 1) ** 1.5 * seam_gap * (yy < H * 0.6)
    a = np.clip(top * s_lab * 0.85 + left * s_lab * 0.6, 0, 1)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = (236, 252, 238)
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA").filter(ImageFilter.GaussianBlur(1.2))


def make_underside(rng, prng) -> Image.Image:
    """Floating cue inside the box: a darker, cooler rocky underbelly along the bottom with a
    jagged upper boundary, and chipped dark corners. The box stays opaque and full."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Jagged boundary: sum of a few sines and noise, hanging lower in places like stalactites.
    ph = [prng.uniform(0, 6.28) for _ in range(4)]
    prof = (np.sin(xx / 58 + ph[0]) * 14 + np.sin(xx / 23 + ph[1]) * 8
            + np.abs(np.sin(xx / 41 + ph[2])) * 26 + np.sin(xx / 9 + ph[3]) * 3)
    boundary = H * 0.74 + prof - 20
    d = (yy - boundary)  # > 0 below the boundary
    belly = np.clip(d / 26.0, 0, 1)
    belly = belly * belly * (3 - 2 * belly)
    deepen = np.clip((yy - H * 0.8) / (H * 0.2), 0, 1)
    a = np.clip(belly * 0.62 + deepen * 0.2, 0, 0.8)
    # A faint cool lit lip on the boundary, light from the top.
    lip = np.clip(1 - np.abs(d - 2) / 4.0, 0, 1) * 0.14
    # Chipped corners: dark wedges at the four corners, inside the box.
    def corner(cx, cy, r):
        dd = np.hypot(xx - cx, yy - cy)
        wob = 1 + 0.25 * np.sin(np.arctan2(yy - cy, xx - cx) * 7 + cx)
        return np.clip(1 - dd / (r * wob), 0, 1)
    ch = (corner(0, H - 1, 80) + corner(W - 1, H - 1, 100) + corner(0, 0, 36) + corner(W - 1, 0, 44))
    ch = np.clip(ch * 1.6, 0, 1) * 0.55
    dark = np.array([10, 30, 38], dtype=np.float32)
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    ca = np.clip(a + ch - a * ch, 0, 1)
    rgba[..., :3] = dark
    rgba[..., 3] = ca * 255
    # add the lip as a light tint where there is no dark
    l = lip[..., None] * np.array([160, 210, 190], dtype=np.float32)
    tot = np.clip(ca + lip * (1 - ca), 0, 1)
    rgba[..., :3] = (dark * ca[..., None] + l * (1 - ca[..., None])) / np.clip(tot, 1e-4, 1)[..., None]
    rgba[..., 3] = tot * 255
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")


def make_rim() -> Image.Image:
    """Thin fuchsia rim on the bottom side (GDD 12 rule 8): a soft 1 px accent, half opaque,
    over a dark shadow band so it fades into the slab shadows instead of standing as a bar."""
    yy, xx = np.mgrid[0:H, 0:W]
    from_bottom = (H - 1 - yy).astype(np.float32) - 8  # sits just inside the 2 px edge
    line = np.clip(1 - np.abs(from_bottom - 2) / 3.0, 0, 1) * 0.68
    shadow = np.exp(-(np.clip(from_bottom - 5, 0, None) / 12.0) ** 2) * 0.35 * (from_bottom >= 5)
    ends = np.clip(np.minimum(xx, W - 1 - xx) / 60.0, 0, 1)
    wob = 0.75 + 0.25 * np.sin(xx / 37.0 + np.sin(xx / 91.0) * 2)
    # Broken run: noise-like gaps and faded stretches, so it is never one bright unbroken line.
    brk = 0.5 + 0.5 * np.sin(xx / 53.0 + 1.3) * np.sin(xx / 17.0 + 0.4) + 0.25 * np.sin(xx / 131.0)
    brk = np.clip((brk - 0.15) / 0.55, 0, 1)
    a_line = line * (0.5 + 0.5 * ends) * wob * (0.35 + 0.65 * brk)
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    # shadow first (dark teal), then rim colour on top
    sh_a = np.clip(shadow, 0, 1)
    out_a = a_line + sh_a * (1 - a_line)
    col = (np.array(FUCHSIA, dtype=np.float32) * a_line[..., None]
           + np.array([6, 20, 30], dtype=np.float32) * (sh_a * (1 - a_line))[..., None]) / np.clip(out_a, 1e-4, 1)[..., None]
    rgba[..., :3] = col
    rgba[..., 3] = out_a * 255
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")


def shrink(img: Image.Image) -> Image.Image:
    return img.resize((GAME_W, GAME_H), Image.LANCZOS)


def make_board(asset: Image.Image) -> Image.Image:
    bg = Image.open(ROOT / "game" / "assets" / "background.png").convert("RGB")
    dark = bg.getpixel((bg.width // 2, bg.height // 2))
    pad = 24
    bw = SCALE * GAME_W + pad * 2
    top_h = GAME_H + pad * 2 + 16
    bh = top_h + SCALE * GAME_H + pad * 2 + 16
    board = Image.new("RGBA", (bw, bh), dark + (255,))
    d = ImageDraw.Draw(board, "RGBA")
    font = ImageFont.load_default()
    d.text((pad, 6), "1x on the game background (320 x 120)", fill=(180, 190, 220, 255), font=font)
    board.alpha_composite(asset, (pad, pad + 8))
    d.text((pad, top_h + 4), "4x zoom, hitbox outline = the whole box (320 x 120)", fill=(180, 190, 220, 255), font=font)
    zoom = asset.resize((SCALE * GAME_W, SCALE * GAME_H), Image.NEAREST)
    x2, y2 = pad, top_h + pad
    board.alpha_composite(zoom, (x2, y2))
    d.rectangle([x2 - 1, y2 - 1, x2 + SCALE * GAME_W, y2 + SCALE * GAME_H], outline=(139, 233, 255, 120), width=1)
    return board


def main(argv) -> None:
    rnd = int(argv[1]) if len(argv) > 1 else 1
    rng = np.random.default_rng(SEED)
    prng = random.Random(SEED)

    seeds = make_seeds(prng)
    label, edge, n, xx, yy = voronoi(seeds)
    slabs = make_slabs(rng, prng, label, edge, xx, yy, len(seeds))
    seams = make_seams(edge)
    cracks = make_cracks(prng, label, len(seeds))
    light = make_light(edge, n, xx, yy, prng)
    edge_l = make_edge()
    top_l = make_top_light(edge, label, len(seeds), prng)
    under = make_underside(rng, prng)
    rim = make_rim()

    master = slabs
    for layer in (seams, cracks, light, under, edge_l, top_l, rim):
        master = Image.alpha_composite(master, layer)
    master.putalpha(255)

    asset = shrink(master)
    asset.putalpha(255)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / f"floating-island-d3-r{rnd}"
    asset.save(f"{stem}.png")
    master.save(f"{stem}-master.png")
    make_board(asset).save(f"{stem}-board.png")
    write_piskel(
        f"{stem}.piskel",
        f"floating-island-d3-r{rnd}",
        [
            ("slabs", [shrink(slabs)]),
            ("seams", [shrink(seams)]),
            ("cracks", [shrink(cracks)]),
            ("light", [shrink(light)]),
            ("underside", [shrink(under)]),
            ("edge", [shrink(Image.alpha_composite(edge_l, top_l))]),
            ("rim", [shrink(rim)]),
        ],
    )
    print("wrote", stem)


if __name__ == "__main__":
    main(sys.argv)
