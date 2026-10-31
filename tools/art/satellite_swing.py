"""Panel-swing and magnetism-field frames for the satellite, from a pixel-art source image.

The source is split into four layers by colour, position and connectivity:
left panel, right panel with its strut, body, and arcs. The body stays still.
Both panels turn together as one rigid bar about the body's centre, in the
image plane, on a sine: angle = swing_degrees * sin(2 pi i / swing_frames).
The arcs (the magnetism field) turn round the body along their own ellipse,
one full turn over --field-frames frames. Each moving layer is upscaled 8x
nearest, turned nearest, then shrunk to game scale.

swing_degrees, swing_frames, hitbox and swing_hitbox come from the satellite
tuning file (default variant), so the frames and the hitbox the core turns
always agree. Every frame is square: the strip's frame count is its width
divided by its height.

Outputs (all in --out-dir):
  satellite.png               swing frames, body and panels, one row
  satellite-field.png         field frames, the arcs only, one row
  satellite-swing-board.png   preview board with the hitbox drawn
  satellite-preview.gif       both strips played together at game speed, 4x

Positive angles turn counter-clockwise on screen (left panel down, right
panel up). Frame 1 is level.

Usage: python tools/art/satellite_swing.py [--src PATH] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "staging/art-inbox/satellite-pixellab-a.png"
OUT = ROOT / "staging/assets/sprites"
TUNING = ROOT / "game/tuning/drifters/satellite.json"

FIELD_FRAMES = 48  # one full turn of the field, 7.5 degrees a frame
UP = 8  # nearest upscale factor used for rotation
GAME_SCALE = 36 / 85  # drawn box 85 px wide (panels level) -> 36 px
ALPHA_CUT = 64  # drop alpha below 25 %
SOLID = 128  # alpha that counts as drawn for the hitbox checks
NAVY = (8, 10, 28)
BLACK = (0, 0, 0)
TXT = (200, 205, 225)

# Where to look for each panel (source px). Only the search window is fixed;
# the panel shape itself comes from the pixels.
LEFT_PANEL_MAX_X = 38
RIGHT_PANEL_MIN_X = 73
# Right strut: the short grey bar between the body's right edge and the far
# panel, read off the source at x 72..75, y 24..27.
STRUT_X = (72, 75)
STRUT_Y = (24, 27)
STRUT_EXTEND_TO_X = 56  # hidden part of the strut, under the body


# ---------------------------------------------------------------- masks

def _hsv(rgb: np.ndarray) -> np.ndarray:
    """Per-pixel HSV, each 0..1."""
    flat = rgb.reshape(-1, 3) / 255.0
    out = np.array([colorsys.rgb_to_hsv(*p) for p in flat])
    return out.reshape(rgb.shape)


def panel_colour(src: np.ndarray) -> np.ndarray:
    """Saturated mid/bright blue or light cyan: the solar cell and its frame."""
    hsv = _hsv(src[..., :3])
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    cell = (h > 0.52) & (h < 0.645) & (s > 0.5) & (v > 0.5)
    rim = (h > 0.5) & (h < 0.6) & (v > 0.9) & (s > 0.1)
    return (cell | rim) & (src[..., 3] > 0)


def fuchsia(src: np.ndarray) -> np.ndarray:
    """Magenta/purple hues: the arcs and the lens."""
    hsv = _hsv(src[..., :3])
    h, s = hsv[..., 0], hsv[..., 1]
    return (h > 0.72) & (h < 0.95) & (s > 0.1) & (src[..., 3] > 0)


def components(mask: np.ndarray) -> list[np.ndarray]:
    """8-connected components of a boolean mask, largest first."""
    seen = np.zeros_like(mask)
    out: list[np.ndarray] = []
    hgt, wid = mask.shape
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        comp = np.zeros_like(mask)
        stack = [(y0, x0)]
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            comp[y, x] = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < hgt and 0 <= nx < wid and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        out.append(comp)
    out.sort(key=lambda c: -int(c.sum()))
    return out


def hull_fill(mask: np.ndarray) -> np.ndarray:
    """Pixels whose centre lies inside or on the convex hull of the mask."""
    pts = sorted({(int(x), int(y)) for y, x in zip(*np.nonzero(mask))})

    def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[int, int]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[int, int]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    yy, xx = np.mgrid[0 : mask.shape[0], 0 : mask.shape[1]]
    inside = np.ones_like(mask)
    for i, a in enumerate(hull):
        b = hull[(i + 1) % len(hull)]
        inside &= (b[0] - a[0]) * (yy - a[1]) - (b[1] - a[1]) * (xx - a[0]) >= 0
    return inside


def split_layers(src: np.ndarray) -> dict[str, np.ndarray]:
    """Split the source into RGBA layers: arcs, right, body, left."""
    hgt, wid = src.shape[:2]
    opaque = src[..., 3] > 0
    xx = np.mgrid[0:hgt, 0:wid][1]
    blue = panel_colour(src)

    left_seed = components(blue & (xx <= LEFT_PANEL_MAX_X))[0]
    left = hull_fill(left_seed) & opaque & ~fuchsia(src)
    right_seed = components(blue & (xx >= RIGHT_PANEL_MIN_X))[0]
    right = hull_fill(right_seed) & opaque & ~fuchsia(src)

    yy = np.mgrid[0:hgt, 0:wid][0]
    strut = (
        opaque & ~right
        & (xx >= STRUT_X[0]) & (xx <= STRUT_X[1])
        & (yy >= STRUT_Y[0]) & (yy <= STRUT_Y[1])
    )

    rest = opaque & ~left & ~right & ~strut
    body = components(rest)[0]  # the largest: the octagon with its lens
    leftover = rest & ~body
    arcs = leftover & fuchsia(src)
    right = right | strut
    _assign_by_neighbours(leftover & ~arcs, [left, right, body, arcs])
    strut = strut & right

    def layer(mask: np.ndarray) -> np.ndarray:
        out = np.zeros_like(src)
        out[mask] = src[mask]
        return out

    body_l = layer(body)
    _fill_body_holes(body_l, body, left)

    right_l = layer(right)
    _extend_strut(right_l, src, strut)

    return {"arcs": layer(arcs), "right": right_l, "body": body_l, "left": layer(left)}


def _assign_by_neighbours(todo: np.ndarray, classes: list[np.ndarray]) -> None:
    """Give each pixel in `todo` to the class most of its 8 neighbours belong to.

    Used for the few dark or grey edge pixels just outside a panel's hull. The
    class masks are updated in place; ties go to the earlier class (panels
    first). Pixels that touch no class at all join the last class (arcs).
    """
    todo = todo.copy()
    hgt, wid = todo.shape
    changed = True
    while changed and todo.any():
        changed = False
        for y, x in zip(*np.nonzero(todo)):
            y0, y1, x0, x1 = max(y - 1, 0), min(y + 2, hgt), max(x - 1, 0), min(x + 2, wid)
            counts = [int(c[y0:y1, x0:x1].sum()) for c in classes]
            if max(counts) == 0:
                continue
            classes[int(np.argmax(counts))][y, x] = True
            todo[y, x] = False
            changed = True
    classes[-1] |= todo


def _fill_body_holes(body_l: np.ndarray, body: np.ndarray, left: np.ndarray) -> None:
    """Fill body pixels hidden behind the near (left) panel.

    The hidden region is the part of the body's convex hull that the left
    panel covers. Each row takes the colour of the first visible body pixel to
    its right; the outermost pixel of the row gets the body's outline navy.
    """
    hole = hull_fill(body) & ~body & left
    outline = np.array([16, 27, 88, 255], dtype=np.uint8)
    for y in np.unique(np.nonzero(hole)[0]):
        xs = np.nonzero(hole[y])[0]
        right_px = np.nonzero(body[y, xs.max() + 1 :])[0]
        if right_px.size == 0:
            continue
        fill = body_l[y, xs.max() + 1 + right_px[0]].copy()
        for x in xs:
            body_l[y, x] = fill
        body_l[y, xs.min()] = outline


def _extend_strut(right_l: np.ndarray, src: np.ndarray, strut: np.ndarray) -> None:
    """Extend the right strut inward under the body so it never detaches."""
    x_in = STRUT_X[0]
    for x in range(STRUT_EXTEND_TO_X, x_in):
        for y in range(STRUT_Y[0], STRUT_Y[1] + 1):
            if strut[y, x_in] and right_l[y, x, 3] == 0:
                right_l[y, x] = src[y, x_in]


# ---------------------------------------------------------------- rotation

def pad_centered(arr: np.ndarray, cx: int, cy: int, half_w: int, half_h: int) -> np.ndarray:
    """Canvas of (2*half_w+1, 2*half_h+1) with source pixel (cx, cy) at its centre pixel."""
    out = np.zeros((2 * half_h + 1, 2 * half_w + 1, 4), dtype=np.uint8)
    ox, oy = half_w - cx, half_h - cy
    hgt, wid = arr.shape[:2]
    out[oy : oy + hgt, ox : ox + wid] = arr
    return out


def rotate_big(layer: np.ndarray, angle: float) -> np.ndarray:
    """8x nearest upscale, then nearest rotation about the canvas centre."""
    big = Image.fromarray(layer).resize(
        (layer.shape[1] * UP, layer.shape[0] * UP), Image.Resampling.NEAREST
    )
    if angle == 0:
        return np.array(big)
    centre = (big.width / 2, big.height / 2)
    return np.array(big.rotate(angle, resample=Image.Resampling.NEAREST, center=centre))


def over(dst: np.ndarray, top: np.ndarray) -> np.ndarray:
    """Paste opaque pixels of top over dst (all layers are 0/255 alpha)."""
    out = dst.copy()
    m = top[..., 3] > 0
    out[m] = top[m]
    return out


def swing_big(layers: dict[str, np.ndarray], angle: float) -> np.ndarray:
    """One swing frame at 8x: right panel, body, left panel, back to front. No arcs."""
    frame = rotate_big(layers["right"], angle)
    frame = over(frame, rotate_big(layers["body"], 0))
    return over(frame, rotate_big(layers["left"], angle))


def fit_ellipse(mask: np.ndarray, cx: float, cy: float) -> tuple[float, float]:
    """Semi-axes (a across, b down) of the upright ellipse centred on (cx, cy) that best fits the
    mask's pixel centres, least squares, in the mask's px."""
    ys, xs = np.nonzero(mask)
    rows = np.stack([(xs + 0.5 - cx) ** 2, (ys + 0.5 - cy) ** 2], axis=1)
    p, q = np.linalg.lstsq(rows, np.ones(len(xs)), rcond=None)[0]
    return 1 / math.sqrt(p), 1 / math.sqrt(q)


def field_big(arcs: np.ndarray, turn: float, a: float, b: float) -> np.ndarray:
    """The arcs at 8x, turned `turn` degrees clockwise on screen along their ellipse (a, b).

    Squash the ellipse to a circle, turn, stretch back: one affine map, sampled nearest.
    """
    big = Image.fromarray(rotate_big(arcs, 0))
    cx, cy = big.width / 2, big.height / 2
    r = math.radians(turn)
    co, si = math.cos(r), math.sin(r)
    # Output px -> source px: the inverse turn, S R(-turn) S^-1 with S = diag(a, b).
    m00, m01, m10, m11 = co, si * a / b, -si * b / a, co
    data = (m00, m01, cx - m00 * cx - m01 * cy, m10, m11, cy - m10 * cx - m11 * cy)
    return np.array(big.transform(big.size, Image.Transform.AFFINE, data, Image.Resampling.NEAREST))


# ---------------------------------------------------------------- game scale

def shrink(big: np.ndarray, cx: float, cy: float, out_w: int, out_h: int, scale: float) -> np.ndarray:
    """Lanczos downscale on premultiplied alpha, centred on (cx, cy) (big-canvas px).

    `scale` is output px per big-canvas px. Alpha below 25 % is dropped.
    """
    a = big[..., 3:4].astype(np.float32) / 255.0
    pre = np.concatenate([big[..., :3].astype(np.float32) * a, a * 255.0], axis=-1)
    box = (
        cx - out_w / 2 / scale,
        cy - out_h / 2 / scale,
        cx + out_w / 2 / scale,
        cy + out_h / 2 / scale,
    )
    chans = [
        np.array(
            Image.fromarray(pre[..., c]).resize(
                (out_w, out_h), Image.Resampling.LANCZOS, box=box
            )
        )
        for c in range(4)
    ]
    res = np.clip(np.stack(chans, -1), 0, 255)
    alpha = res[..., 3]
    rgb = np.where(alpha[..., None] > 0, res[..., :3] * 255.0 / np.maximum(alpha[..., None], 1e-6), 0)
    out = np.concatenate([np.clip(rgb, 0, 255), alpha[..., None]], -1).round().astype(np.uint8)
    out[out[..., 3] < ALPHA_CUT] = 0
    return out


def extent(frames: list[np.ndarray], cx: float, cy: float) -> tuple[float, float]:
    """Largest horizontal and vertical reach of alpha from (cx, cy), in frame px."""
    rx = ry = 0.0
    for f in frames:
        ys, xs = np.nonzero(f[..., 3])
        rx = max(rx, cx - xs.min(), xs.max() + 1 - cx)
        ry = max(ry, cy - ys.min(), ys.max() + 1 - cy)
    return rx, ry


# ---------------------------------------------------------------- board

def zoom(arr: np.ndarray, k: int, bg: tuple[int, int, int]) -> Image.Image:
    """Nearest zoom of an RGBA frame over a flat background."""
    base = Image.new("RGBA", (arr.shape[1], arr.shape[0]), bg + (255,))
    base.alpha_composite(Image.fromarray(arr))
    return base.resize((base.width * k, base.height * k), Image.Resampling.NEAREST)


# ---------------------------------------------------------------- hitbox and board

def turn_point(x: float, y: float, angle: float) -> tuple[float, float]:
    """(x, y) turned `angle` degrees counter-clockwise on screen (y down) about (0, 0).

    The same turn the core gives the swing hitbox (core/drifters/satellite.py).
    """
    r = math.radians(angle)
    return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)


def shape_mask(shape: dict, angle: float, side: int, k: int) -> np.ndarray:
    """One tuning shape, turned `angle`, as a mask of a side x side frame sampled k x k per px."""
    g = (np.arange(side * k) + 0.5) / k - side / 2
    x, y = np.meshgrid(g, g)
    lx, ly = turn_point(x, y, -angle)  # sample points back into the shape's level frame
    if shape["shape"] == "circle":
        return (lx - shape["cx"]) ** 2 + (ly - shape["cy"]) ** 2 < shape["r"] ** 2
    return (abs(lx - shape["cx"]) < shape["w"] / 2) & (abs(ly - shape["cy"]) < shape["h"] / 2)


def outline(shape: dict, angle: float, cx: float, cy: float, k: float) -> list[tuple[float, float]]:
    """Outline points of a turned tuning shape, frame px times k, round a centre (cx, cy)."""
    if shape["shape"] == "circle":
        pts = [
            (shape["cx"] + shape["r"] * math.cos(t), shape["cy"] + shape["r"] * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, 33)
        ]
    else:
        hw, hh = shape["w"] / 2, shape["h"] / 2
        pts = [(shape["cx"] + sx * hw, shape["cy"] + sy * hh) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
    out = []
    for px, py in pts:
        tx, ty = turn_point(px, py, angle)
        out.append((cx + tx * k, cy + ty * k))
    return out


SWING_SHAPES: list[dict] = []
"""The tuning's swing_hitbox shapes; set by main, read by outline."""


def board(swing: list[np.ndarray], field: list[np.ndarray], angles: list[float],
          still: list[dict], path: Path) -> None:
    """Preview board: every other frame at 6x with the hitbox drawn, then plain on navy and black."""
    side = swing[0].shape[0]
    picks = list(range(0, len(swing), 2))
    z = 6
    pad = 12
    cell = side * z + pad
    width = pad + len(picks) * cell
    height = pad + 14 + side * z + pad + 14 + 2 * (side * 2 + 6) + pad
    im = Image.new("RGBA", (width, height), (24, 26, 40, 255))
    d = ImageDraw.Draw(im)
    d.text((pad, pad), f"Every other swing frame with a field frame, {side}x{side}, 6x. Hitbox: body still (yellow), panels turned (green).", fill=TXT)
    y = pad + 14
    for j, i in enumerate(picks):
        f = field[(i * len(field)) // len(swing)]
        frame = over(f, swing[i])
        tile = zoom(frame, z, NAVY)
        td = ImageDraw.Draw(tile, "RGBA")
        c = side * z / 2
        for shape in still:
            td.line(outline(shape, 0, c, c, z), fill=(255, 220, 90, 200), width=2)
        for shape in SWING_SHAPES:
            td.line(outline(shape, angles[i], c, c, z), fill=(90, 255, 140, 200), width=2)
        im.paste(tile, (pad + j * cell, y))
        d.text((pad + j * cell, y + side * z - 12), f"{angles[i]:+.1f}", fill=TXT)
    y += side * z + pad
    d.text((pad, y), "Same frames, 2x, navy and black.", fill=TXT)
    y += 14
    for bg in (NAVY, BLACK):
        for j, i in enumerate(picks):
            f = field[(i * len(field)) // len(swing)]
            im.paste(zoom(over(f, swing[i]), 2, bg), (pad + j * (side * 2 + 6), y))
        y += side * 2 + 6
    im.save(path)


def preview_gif(swing: list[np.ndarray], field: list[np.ndarray], swing_tpf: int,
                field_tpf: int, path: Path) -> None:
    """Both strips played together on navy at 4x, one GIF frame every 3 ticks, one full loop."""
    loop = math.lcm(len(swing) * swing_tpf, len(field) * field_tpf)
    frames = []
    for tick in range(0, loop, 3):
        frame = over(field[(tick // field_tpf) % len(field)], swing[(tick // swing_tpf) % len(swing)])
        frames.append(zoom(frame, 4, NAVY).convert("P", palette=Image.Palette.ADAPTIVE))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=50, loop=0)


# ---------------------------------------------------------------- checks

def report(swing: list[np.ndarray], field: list[np.ndarray], angles: list[float],
           still: list[dict]) -> None:
    """Print frame size, clipping, footprint and how well the hitbox matches each swing frame."""
    side = swing[0].shape[0]
    print(f"frame {side}x{side}: {len(swing)} swing frames, {len(field)} field frames")
    clipped = [
        i for i, f in enumerate(swing + field)
        if f[0].any() or f[-1].any() or f[:, 0].any() or f[:, -1].any()
    ]
    print(f"  frames touching the frame edge: {clipped or 'none'}")
    rx = ry = 0.0
    c = side / 2
    for f in swing + field:
        ys, xs = np.nonzero(f[..., 3])
        rx = max(rx, c - xs.min(), xs.max() + 1 - c)
        ry = max(ry, c - ys.min(), ys.max() + 1 - c)
    print(f"  footprint (every drawn px, even): {2 * math.ceil(rx)} x {2 * math.ceil(ry)}")
    k = 4
    worst_out = 0.0
    for i, f in enumerate(swing):
        drawn = np.kron(f[..., 3] >= SOLID, np.ones((k, k), dtype=bool))
        hit = np.zeros_like(drawn)
        for shape in still:
            hit |= shape_mask(shape, 0, side, k)
        for shape in SWING_SHAPES:
            hit |= shape_mask(shape, angles[i], side, k)
        outside = (hit & ~drawn).sum() / k**2
        covered = (hit & drawn).sum() / drawn.sum()
        worst_out = max(worst_out, outside)
        if i % 3 == 0:
            print(f"  swing f{i + 1:2d} ({angles[i]:+5.1f} deg): drawn px covered {covered * 100:3.0f}%, "
                  f"hitbox px outside the drawing {outside:.1f}")
    print(f"  worst hitbox px outside the drawing, any frame: {worst_out:.1f}")


# ---------------------------------------------------------------- main

def main() -> None:
    """Build the swing strip, the field strip, the board and the preview GIF."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--tuning", type=Path, default=TUNING)
    ap.add_argument("--field-frames", type=int, default=FIELD_FRAMES)
    args = ap.parse_args()

    tuning = json.loads(args.tuning.read_text())
    variant = tuning["variants"][tuning["default_variant"]]
    frames = variant["swing_frames"]
    angles = [variant["swing_degrees"] * math.sin(2 * math.pi * i / frames) for i in range(frames)]
    still = variant["hitbox"]
    SWING_SHAPES[:] = variant["swing_hitbox"]

    src = np.array(Image.open(args.src).convert("RGBA"))
    src[src[..., 3] == 0] = 0
    layers = split_layers(src)

    # Body centre: centre pixel of the body layer's bounding box (holes filled).
    ys, xs = np.nonzero(layers["body"][..., 3])
    bcx, bcy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    print(f"body bbox x {xs.min()}..{xs.max()}, y {ys.min()}..{ys.max()}, centre pixel ({bcx}, {bcy})")

    # Work on a generous square canvas centred on the body's centre pixel.
    half = 64
    padded = {k: pad_centered(v, bcx, bcy, half, half) for k, v in layers.items()}
    a, b = fit_ellipse(padded["arcs"][..., 3] > 0, half + 0.5, half + 0.5)
    print(f"field ellipse: {2 * a:.1f} x {2 * b:.1f} source px")

    big_swing = [swing_big(padded, ang) for ang in angles]
    big_field = [field_big(padded["arcs"], 360 * i / args.field_frames, a, b) for i in range(args.field_frames)]

    # Game: square frames, body centre exactly at the frame centre.
    s = GAME_SCALE / UP
    cb = (half + 0.5) * UP
    rbx, rby = extent(big_swing + big_field, cb, cb)
    side = 2 * math.ceil(max(rbx, rby) * s + 1)
    swing = [shrink(f, cb, cb, side, side, s) for f in big_swing]
    field = [shrink(f, cb, cb, side, side, s) for f in big_field]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.concatenate(swing, axis=1)).save(args.out_dir / "satellite.png")
    Image.fromarray(np.concatenate(field, axis=1)).save(args.out_dir / "satellite-field.png")
    board(swing, field, angles, still, args.out_dir / "satellite-swing-board.png")
    preview_gif(swing, field, variant["swing_ticks_per_frame"], variant["field_ticks_per_frame"],
                args.out_dir / "satellite-preview.gif")
    report(swing, field, angles, still)


if __name__ == "__main__":
    main()
