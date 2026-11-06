"""Floating island, design 2: crystal meadow (rectangle, 320 x 120).

Spec: docs/design/gdd/drifters/05-floating-islands.md (look_reference, art_canvas,
shapes, hitbox) and docs/design/gdd/12-art-and-audio.md (rules 2, 6, 8, 9).

The ground fills the whole box, no transparent edge. Green ground with a darker
edge drawn inside the shape. A few small dim purple crystals grow from the
meadow, always well inside the edge. A thin fuchsia rim runs along the bottom.
Drawn at 4x (1280 x 480), then shrunk to game size.

Usage: python3 tools/art/floating-island-d2.py [round]   (default 1)
Writes, in staging/assets/sprites/:
  floating-island-d2-r<n>.png          the asset, 320 x 120
  floating-island-d2-r<n>-master.png   the 1280 x 480 master
  floating-island-d2-r<n>-board.png    the preview board for the UI Art Critic
  floating-island-d2-r<n>.piskel       layers: ground, crystals, tufts, edge, rim
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from piskel_file import write_piskel  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging" / "assets" / "sprites"

GAME_W, GAME_H = 320, 120  # spec: art_canvas, rectangle
SCALE = 4  # spec: GDD 12 art_style, 4x for sprites bigger than 64 px
W, H = GAME_W * SCALE, GAME_H * SCALE
SEED = 20261031

# Colors. Base green and edge green come from the spec's placeholder_look.
GREEN = (70, 160, 80)
EDGE = (35, 90, 45)
FUCHSIA = (255, 0, 174)  # GDD 12 HUD ship_lines value, used here only as a thin rim


def noise(rng: np.random.Generator, cell: int) -> np.ndarray:
    """Smooth value noise, 0..1, size H x W."""
    gh, gw = H // cell + 2, W // cell + 2
    grid = rng.random((gh, gw)).astype(np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:H, :W] / 255.0


def ridge_y(x):
    return 214 + 12 * np.sin(x / 90.0) + 7 * np.sin(x / 37.0 + 1.0) + 3 * np.sin(x / 13.0)


def make_ground(rng: np.random.Generator, prng: random.Random) -> Image.Image:
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    ridge = ridge_y(xs)  # 1 x W
    above = ys < ridge

    # Meadow: bright at the top, easing to the base green at the ridge.
    t_up = np.clip(ys / 230.0, 0, 1)
    meadow = np.stack(
        [
            104 + (78 - 104) * t_up,
            188 + (166 - 188) * t_up,
            98 + (84 - 98) * t_up,
        ],
        axis=-1,
    )  # H x 1 x 3
    # Body below the ridge: deeper green down to the bottom.
    t_dn = np.clip((ys - 214) / (H - 214), 0, 1)
    body = np.stack(
        [
            58 + (22 - 58) * t_dn,
            132 + (66 - 132) * t_dn,
            70 + (62 - 70) * t_dn,
        ],
        axis=-1,
    )
    base = np.where(above[..., None], meadow, body)
    base = np.broadcast_to(base, (H, W, 3)).copy()

    # Mottling: two scales of soft noise, a few brightness points either way.
    mott = (noise(rng, 64) - 0.5) * 16 + (noise(rng, 18) - 0.5) * 9
    base += mott[..., None] * np.array([0.8, 1.0, 0.8])

    # Ridge lip: a lighter line on the ridge, and a soft shadow under it.
    d = ys - ridge
    lip = np.exp(-((d + 3) / 5.0) ** 2) * 0.55
    shade = np.exp(-((d - 16) / 14.0) ** 2) * 0.28 * (d > 0)
    light = np.array([150, 220, 130], dtype=np.float32)
    base = base * (1 - lip[..., None]) + light * lip[..., None]
    navy = np.array([12, 28, 70], dtype=np.float32)
    sh = shade[..., None] * 1.6
    base = base * (1 - sh) + navy * sh
    # Deeper navy toward the bottom of the soil.
    deep = (np.clip((ys - 300) / (H - 300), 0, 1) ** 1.3 * 0.42 * (ys > ridge))[..., None]
    base = base * (1 - deep) + navy * deep
    # Hard bright line on the ridge (the glossy lit edge of the meadow).
    hard = (np.clip(1.0 - np.abs(d + 6) / 2.6, 0, 1) ** 0.5 * 1.0)[..., None]
    base = base * (1 - hard) + np.array([250, 255, 248], dtype=np.float32) * hard

    # Strata in the body: faint darker wavy bands.
    for k, (y0, amp, ph) in enumerate([(310, 7, 0.5), (390, 9, 2.1)]):
        band_y = y0 + amp * np.sin(xs / (70 + 20 * k) + ph)
        band = np.exp(-((ys - band_y) / 5.0) ** 2) * 0.45 * (ys > ridge + 40)
        base = base * (1 - band[..., None]) + np.array([8, 22, 56], dtype=np.float32) * band[..., None]

    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # Underside: jagged rock roots hang into a deep navy base (a chunk torn from the planet).
    under = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ud = ImageDraw.Draw(under)
    base_top = H - 86
    xs1 = np.arange(0, W + 1, 4, dtype=np.float32)
    s_ = 0.5 + 0.5 * np.sin(xs1 / 47.0 + 0.8 * np.sin(xs1 / 130.0) + 1.0)
    prof = base_top + 60 * (1 - (1 - s_) ** 1.6) + 4 * np.sin(xs1 / 11.0)
    ud.rectangle([0, base_top - 4, W, H], fill=(8, 14, 40, 255))
    pts = [(0, 0), (W, 0)] + [(float(x), float(y)) for x, y in zip(xs1[::-1], prof[::-1])]
    soil = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    img = Image.composite(soil, under, mask)
    d = ImageDraw.Draw(img, "RGBA")
    # Wet highlight along the lit lower edge of the roots.
    d.line([(float(x), float(y) - 3) for x, y in zip(xs1, prof)], fill=(190, 240, 240, 140), width=2)

    # Angular rock chunks in the soil: dark facets with a hard white top edge.
    placed = []
    while len(placed) < 13:
        x = prng.uniform(60, W - 60)
        y = prng.uniform(ridge_y(x) + 55, base_top - 30)
        if any(abs(x - px) < 90 and abs(y - py) < 50 for px, py in placed):
            continue
        placed.append((x, y))
        rw, rh = prng.uniform(16, 30), prng.uniform(9, 16)
        poly = [(x - rw, y + rh * 0.4), (x - rw * 0.55, y - rh), (x + rw * 0.35, y - rh * 0.8),
                (x + rw, y + rh * 0.1), (x + rw * 0.5, y + rh), (x - rw * 0.5, y + rh)]
        d.polygon(poly, fill=(12, 36, 52, 255))
        d.polygon([poly[0], poly[1], poly[2], (x, y)], fill=(34, 86, 100, 255))
        d.line([poly[0], poly[1], poly[2]], fill=(236, 252, 250, 235), width=3)

    # Meadow blades: thin triangles pointing up, light and dark.
    for _ in range(520):
        x = prng.uniform(10, W - 10)
        y = prng.uniform(26, ridge_y(x) + 2)
        h = prng.uniform(10, 26)
        lean = prng.uniform(-5, 5)
        w = prng.uniform(1.5, 3.2)
        if prng.random() < 0.5:
            col = (130 + prng.randint(-12, 20), 210 + prng.randint(-12, 10), 120 + prng.randint(-12, 14), 70)
        else:
            col = (50 + prng.randint(-8, 10), 130 + prng.randint(-10, 12), 62 + prng.randint(-8, 10), 60)
        d.polygon([(x - w, y), (x + w, y), (x + lean, y - h)], fill=col)

    # Soft top light: a gentle sheen on the upper meadow (the glossy finish).
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([-200, -150, W + 200, 120], fill=(190, 245, 170, 34))
    sheen = sheen.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, sheen)

    img.putalpha(255)  # the ground fills the whole box
    return img


# Crystal clusters: (center x, [(dx from center, half width, height, lean)]).
CLUSTERS = [
    (150, [(0, 11, 92, -6), (24, 8, 58, 8)]),
    (385, [(0, 9, 70, 5)]),
    (560, [(-20, 8, 54, -7), (0, 12, 104, 3), (22, 8, 66, 9)]),
    (815, [(0, 10, 78, -4), (20, 7, 48, 7)]),
    (1010, [(0, 9, 62, 6)]),
    (1150, [(-10, 8, 86, -5), (14, 8, 56, 6)]),
]

C_LEFT = (112, 66, 196)
C_RIGHT = (62, 36, 124)
C_TIP_L = (168, 124, 240)
C_TIP_R = (104, 70, 176)
C_LINE = (34, 16, 84)


def draw_crystal(d: ImageDraw.ImageDraw, x: float, by: float, hw: float, h: float, lean: float) -> None:
    bl, br = (x - hw, by), (x + hw, by)
    sl = (x - hw + lean * 0.5, by - h * 0.72)
    sr = (x + hw + lean * 0.5, by - h * 0.72)
    tip = (x + lean, by - h)
    c = (x, by)
    m = ((sl[0] + sr[0]) / 2, (sl[1] + sr[1]) / 2)
    d.polygon([bl, sl, tip, c], fill=C_LEFT + (255,))
    d.polygon([c, tip, sr, br], fill=C_RIGHT + (255,))
    d.polygon([sl, tip, m], fill=C_TIP_L + (255,))
    d.polygon([tip, sr, m], fill=C_TIP_R + (255,))
    d.line([bl, sl, tip, sr, br], fill=C_LINE + (255,), width=3, joint="curve")
    d.line([tip, c], fill=C_LINE + (150,), width=2)
    # Hard white highlight on the left edge, kept short and dim.
    p0 = (sl[0] + 4, sl[1] + 6)
    p1 = (tip[0] - 2, tip[1] + 12)
    d.line([p0, p1], fill=(255, 255, 255, 255), width=3)
    q0 = (sr[0] - 5, sr[1] + 10)
    q1 = (sr[0] - 3, by - h * 0.18)
    d.line([q0, q1], fill=(200, 176, 255, 120), width=2)
    d.ellipse([tip[0] - 3, tip[1] + 3, tip[0] + 3, tip[1] + 9], fill=(255, 255, 255, 255))


def make_crystals(prng: random.Random) -> tuple[Image.Image, Image.Image]:
    """Returns (crystals layer with their faint glow, grass tufts in front of the bases)."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    tufts = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tufts)

    for cx, prisms in CLUSTERS:
        by = float(ridge_y(cx)) + 14
        top = by - max(p[2] for p in prisms)
        gd.ellipse([cx - 70, top - 10, cx + 70, by + 30], fill=(130, 80, 220, 30))
        for dx, hw, h, lean in sorted(prisms, key=lambda p: -p[2]):
            draw_crystal(bd, cx + dx, by + prng.uniform(-2, 2), hw, h, lean)
        # Tufts: blades hiding the bases.
        for _ in range(26):
            x = cx + prng.uniform(-48, 48)
            y = by + prng.uniform(2, 14)
            hh = prng.uniform(14, 30)
            lean = prng.uniform(-9, 9)
            w = prng.uniform(2, 3.6)
            col = (
                (116 + prng.randint(-10, 20), 200 + prng.randint(-12, 12), 110 + prng.randint(-8, 14), 255)
                if prng.random() < 0.55
                else (56 + prng.randint(-8, 8), 140 + prng.randint(-10, 12), 66 + prng.randint(-6, 8), 255)
            )
            td.polygon([(x - w, y + 4), (x + w, y + 4), (x + lean, y - hh)], fill=col)

    glow = glow.filter(ImageFilter.GaussianBlur(26))
    crystals = Image.alpha_composite(glow, body)
    return crystals, tufts


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
    # Hard light line just inside the dark edge along the top and the upper sides.
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.line([(24, 11), (W - 24, 11)], fill=(250, 255, 248, 255), width=4)
    hd.line([(9, 24), (9, H * 0.55)], fill=(250, 255, 248, 170), width=3)
    hd.line([(W - 10, 24), (W - 10, H * 0.55)], fill=(250, 255, 248, 170), width=3)
    return Image.alpha_composite(img, hl)


def make_rim() -> Image.Image:
    """Thin fuchsia rim on the bottom side (GDD 12 rule 8): 1 px line plus a faint lift above it."""
    yy, xx = np.mgrid[0:H, 0:W]
    from_bottom = (H - 1 - yy).astype(np.float32) - 8  # sits just inside the 2 px edge
    line = np.clip((6 - from_bottom) / 2.0, 0, 1) * np.clip(from_bottom + 1, 0, 1) * 0.9
    lift = np.exp(-((from_bottom - 2) / 9.0) ** 2) * 0.28 * (from_bottom >= 0)
    a = np.clip(line + lift, 0, 1)
    # Fade out toward both ends so the rim stays a bottom accent.
    ends = np.clip(np.minimum(xx, W - 1 - xx) / 40.0, 0, 1)
    a = a * (0.55 + 0.45 * ends)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = FUCHSIA
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def shrink(img: Image.Image) -> Image.Image:
    return img.resize((GAME_W, GAME_H), Image.LANCZOS)


def make_board(asset: Image.Image, master_comp: Image.Image) -> Image.Image:
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
    x1, y1 = pad, pad + 8
    board.alpha_composite(asset, (x1, y1))

    d.text((pad, top_h + 4), "4x zoom, hitbox outline = the whole box (320 x 120)", fill=(180, 190, 220, 255), font=font)
    zoom = asset.resize((SCALE * GAME_W, SCALE * GAME_H), Image.NEAREST)
    x2, y2 = pad, top_h + pad
    board.alpha_composite(zoom, (x2, y2))
    d.rectangle(
        [x2 - 1, y2 - 1, x2 + SCALE * GAME_W, y2 + SCALE * GAME_H],
        outline=(139, 233, 255, 120),
        width=1,
    )
    return board


def main(argv) -> None:
    rnd = int(argv[1]) if len(argv) > 1 else 1
    rng = np.random.default_rng(SEED)
    prng = random.Random(SEED)

    ground = make_ground(rng, prng)
    crystals, tufts = make_crystals(prng)
    edge = make_edge()
    rim = make_rim()

    master = ground
    for layer in (crystals, tufts, edge, rim):
        master = Image.alpha_composite(master, layer)

    asset = shrink(master)
    asset.putalpha(255)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / f"floating-island-d2-r{rnd}"
    asset.save(f"{stem}.png")
    master.save(f"{stem}-master.png")
    make_board(asset, master).save(f"{stem}-board.png")
    write_piskel(
        f"{stem}.piskel",
        f"floating-island-d2-r{rnd}",
        [
            ("ground", [shrink(ground)]),
            ("crystals", [shrink(crystals)]),
            ("tufts", [shrink(tufts)]),
            ("edge", [shrink(edge)]),
            ("rim", [shrink(rim)]),
        ],
    )
    print("wrote", stem)


if __name__ == "__main__":
    main(sys.argv)
