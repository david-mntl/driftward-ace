"""Final ship sprites from the chosen PixelLab pose: lean frames and flame jets.

The chosen pose is staging/assets/sprites/ship-glide-src-center-f.png (Director, chat,
2026-10-30). No image service is called here: lean frames are the pose squashed and shaded by
script, and the flames are drawn at 4x and shrunk, both with Pillow and numpy.

Three strips, one row of equal frames each, the frame centre being the ship's centre (the
hitbox centre, 04-ship.md). The game blits every frame centered on the ship. Streaks and
flames go first, behind the body.

  ship.png         3 lean frames: left, centre, right. The art is shrunk once, from the centre
                   pose's width, so a lean frame is narrower, not smaller.
  ship_flame.png   8 flame frames (FRAME_W x FRAME_H), 2 flicker frames for each of 4 jets, in
                   the order up, left, right, down. A jet is named for the arrow that fires it:
                   "left" is the puff at the right wing tip, pushing the ship left.
  ship_streaks.png 4 air streak frames (STREAK_W x FRAME_H): short and long, 2 flicker frames
                   each. They trail to the left, for a ship moving right; the game mirrors
                   them for the other way.

Frame, drawn width and the jets are a test proposal from the Director (chat, 2026-10-30), not
GDD values. The lean strengths and the flame sizes are guesses to tune by eye.

Outputs (in --out-dir):
  ship.png, ship_flame.png, ship_streaks.png   the strips
  ship-final-board.png            preview board: 1x on navy, 4x zoom with the hitbox

Usage: python tools/art/ship_final.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites"
SOURCE = OUT / "ship-glide-src-center-f.png"

SHIP_W = 38  # drawn width of the centre pose at game size, px
FRAME_W, FRAME_H = 48, 64
SUPER = 4  # flames are drawn at 4x then shrunk (12-art-and-audio.md, art_style)
CX = FRAME_W / 2  # the ship's axis in the frame, px
TOP_Y = 16.0  # nose tip row in the centre frame, px
BOTTOM_Y = 51.0  # row after the last body row in the centre frame, px

# Lean: the scale of the side the ship leans to (near) and the other (far), and how much the
# far side is lit and the near side shaded. One lean, strong enough to read at once. Guesses,
# tuned by eye.
LEAN_NEAR = 0.82
LEAN_FAR = 0.66
LEAN_SHADE = 0.16

# Air streaks: one row each of (start y in the frame, length short, length long), px. They start
# under the wing tip (the wing tip is 19 px from the ship's axis) and fade out. Guesses.
STREAKS = [(35.0, 10.0, 22.0), (40.5, 7.0, 16.0), (46.0, 5.0, 11.0)]
STREAK_W = 96  # streak frame width, px: room to trail past the wing tips
STREAK_START = 14.0  # px left of the ship's axis where a streak starts, under the wing
STREAK_ALPHA = 0.55  # opacity at the root: always dimmer than a hazard (12-art-and-audio.md)
STREAK_THICK = 1.3  # px
STREAK_COLOR = np.array([165, 208, 255], np.float32)  # pale cobalt blue, never white-cyan

# A jet: where it starts (frame px), the way it points, its length at full size, its half
# width at the start. All guesses.
JETS = {
    "up": [((24.0, 48.0), (0.0, 1.0), 15.0, 4.0), ((14.5, 49.0), (0.0, 1.0), 10.0, 2.2),
           ((33.5, 49.0), (0.0, 1.0), 10.0, 2.2)],
    "left": [((39.0, 45.0), (1.0, 0.0), 9.0, 2.4)],
    "right": [((9.0, 45.0), (-1.0, 0.0), 9.0, 2.4)],
    "down": [((17.5, 27.0), (0.0, -1.0), 10.0, 2.0), ((30.5, 27.0), (0.0, -1.0), 10.0, 2.0)],
}
FLICKER = (1.0, 0.78)  # a flicker frame's length against full size
ZOOM = 4
NAVY = (10, 14, 32)
TXT = (200, 205, 225)
HITBOX = (255, 255, 255, 90)
SHIP_SIZE = 32  # ship_w and ship_h, 04-ship.md (guess)
BAR_W, FOOT_H = 12, 12  # hitbox bar width and foot height, 04-ship.md (guess)

CORE = np.array([235, 252, 255], np.float32)
MID = np.array([90, 215, 255], np.float32)
EDGE = np.array([30, 95, 235], np.float32)


def premultiplied(img: Image.Image) -> np.ndarray:
    """RGBA image as float 0..1 with colour multiplied by alpha, so resizing keeps clean edges."""
    arr = np.asarray(img).astype(np.float32) / 255
    arr[..., :3] *= arr[..., 3:4]
    return arr


def straight(arr: np.ndarray) -> Image.Image:
    """Undo `premultiplied` and return an RGBA image."""
    alpha = arr[..., 3:4]
    rgb = np.where(alpha > 0, arr[..., :3] / np.maximum(alpha, 1e-6), 0)
    out = np.concatenate([np.clip(rgb, 0, 1), np.clip(alpha, 0, 1)], axis=-1)
    return Image.fromarray((out * 255).round().astype(np.uint8), "RGBA")


def shrink(arr: np.ndarray, size: tuple[int, int]) -> Image.Image:
    """Resize a premultiplied array to `size` (w, h) with Lanczos, per channel."""
    chans = [
        np.asarray(Image.fromarray(arr[..., c]).resize(size, Image.LANCZOS)) for c in range(4)
    ]
    return straight(np.stack(chans, axis=-1))


def lean(arr: np.ndarray, side: int) -> np.ndarray:
    """Lean the premultiplied art towards `side` (-1 left, +1 right, 0 none).

    Each half is squashed sideways about the axis, the near half less than the far one, and the
    near half is shaded and the far half lit. The canvas keeps its size and its axis.
    """
    if side == 0:
        return arr
    height, width = arr.shape[:2]
    mid = (width - 1) / 2
    out = np.zeros_like(arr)
    xs = np.arange(width, dtype=np.float32)
    for x_out in range(width):
        offset = x_out - mid
        near = offset * side >= 0
        scale = LEAN_NEAR if near else LEAN_FAR
        x_in = mid + offset / scale
        if x_in < 0 or x_in > width - 1:
            continue
        lo = int(np.floor(x_in))
        hi = min(lo + 1, width - 1)
        t = x_in - lo
        out[:, x_out] = arr[:, lo] * (1 - t) + arr[:, hi] * t
    shade = 1 - LEAN_SHADE * (xs - mid) / mid * side
    out[..., :3] *= np.clip(shade, 0, 1.15)[None, :, None]
    out[..., :3] = np.minimum(out[..., :3], out[..., 3:4])
    return out


def body_frames() -> list[Image.Image]:
    """The three lean frames, left, centre, right, each FRAME_W x FRAME_H."""
    src = Image.open(SOURCE).convert("RGBA")
    box = src.getbbox()
    art = premultiplied(src.crop(box))
    width = SHIP_W
    height = round(art.shape[0] * SHIP_W / art.shape[1])
    left = (FRAME_W - width) // 2
    top = round(BOTTOM_Y) - height
    frames = []
    for side in (-1, 0, 1):
        small = shrink(lean(art, side), (width, height))
        out = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        out.alpha_composite(small, (left, top))
        frames.append(out)
    return frames


def jet_layer(start: tuple[float, float], way: tuple[float, float], length: float,
              half: float) -> np.ndarray:
    """One jet at 4x: a teardrop from `start` along `way`, white-hot at the root to cobalt at the rim.

    Returns a premultiplied float array the size of a frame at 4x.
    """
    h, w = FRAME_H * SUPER, FRAME_W * SUPER
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    px = (xx + 0.5) / SUPER - start[0]
    py = (yy + 0.5) / SUPER - start[1]
    along = px * way[0] + py * way[1]
    across = -px * way[1] + py * way[0]
    t = np.clip(along / length, 0, 1)
    width_here = half * (1 - t) ** 0.6 + 1e-4
    u = np.abs(across) / width_here
    inside = (along >= -0.5) & (along <= length)
    shape = np.clip(1 - u ** 3, 0, 1) * inside
    fade = np.clip(1 - t ** 2.2, 0, 1)
    alpha = shape * fade
    heat = np.clip(1 - np.maximum(u * 1.15, t * 0.9), 0, 1)
    rim = np.clip(1 - u, 0, 1)
    color = EDGE[None, None] * (1 - rim[..., None]) + MID[None, None] * rim[..., None]
    color = color * (1 - heat[..., None] ** 1.5) + CORE[None, None] * heat[..., None] ** 1.5
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = color / 255 * alpha[..., None]
    out[..., 3] = alpha
    return out


def over(under: np.ndarray, top: np.ndarray) -> np.ndarray:
    """Premultiplied 'over' of two float arrays."""
    return top + under * (1 - top[..., 3:4])


def flame_frames() -> list[Image.Image]:
    """The eight flame frames: 2 flicker frames for each of up, left, right, down."""
    frames = []
    for name in ("up", "left", "right", "down"):
        for scale in FLICKER:
            layer = np.zeros((FRAME_H * SUPER, FRAME_W * SUPER, 4), np.float32)
            for start, way, length, half in JETS[name]:
                layer = over(layer, jet_layer(start, way, length * scale, half))
            frames.append(shrink(layer, (FRAME_W, FRAME_H)))
    return frames


def streak_frames() -> list[Image.Image]:
    """The four streak frames: short then long, each with 2 flicker frames, STREAK_W x FRAME_H.

    Streaks trail left from under the left wing tip. Drawn at 4x: thin lines fading to nothing.
    """
    h, w = FRAME_H * SUPER, STREAK_W * SUPER
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    px = (xx + 0.5) / SUPER
    py = (yy + 0.5) / SUPER
    root = STREAK_W / 2 - STREAK_START
    frames = []
    for column in (1, 2):
        for scale in FLICKER:
            layer = np.zeros((h, w, 4), np.float32)
            for row in STREAKS:
                length = row[column] * scale
                t = np.clip((root - px) / length, 0, 1)
                inside = (px <= root) & (px >= root - length)
                across = np.clip(1 - np.abs(py - row[0]) / (STREAK_THICK / 2), 0, 1)
                alpha = STREAK_ALPHA * across * (1 - t) ** 1.4 * inside
                streak = np.zeros_like(layer)
                streak[..., :3] = STREAK_COLOR / 255 * alpha[..., None]
                streak[..., 3] = alpha
                layer = over(layer, streak)
            frames.append(shrink(layer, (STREAK_W, FRAME_H)))
    return frames


def strip(frames: list[Image.Image]) -> Image.Image:
    """Lay frames in one row."""
    width = frames[0].width
    out = Image.new("RGBA", (width * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * width, 0))
    return out


def hitbox_boxes(cx: float, cy: float, k: int) -> list[tuple[float, float, float, float]]:
    """The inverted T of 04-ship.md scaled by k around (cx, cy)."""
    half = SHIP_SIZE * k / 2
    bar = (cx - BAR_W * k / 2, cy - half, cx + BAR_W * k / 2, cy + half)
    foot = (cx - half, cy + half - FOOT_H * k, cx + half, cy + half)
    return [bar, foot]


def board(body: list[Image.Image], flame: list[Image.Image],
          streaks: list[Image.Image]) -> Image.Image:
    """Row 1: the three lean frames at 1x. Row 2: the same at 4x with the hitbox. Row 3: each jet
    with the centre body, 4x. Row 4: each streak frame with the right-lean body, 3x."""
    gap = 12
    zw, zh = FRAME_W * ZOOM, FRAME_H * ZOOM
    sz = 3
    cols = len(flame)
    height = 20 + FRAME_H + 20 + zh + 20 + zh + 20 + FRAME_H * sz + gap
    img = Image.new("RGBA", (gap + cols * (zw + gap), height), NAVY + (255,))
    draw = ImageDraw.Draw(img)
    names = ["left", "centre", "right"]
    y1, y2 = 20, 20 + FRAME_H + 20
    for i, (f, name) in enumerate(zip(body, names)):
        x = gap + i * (zw + gap)
        draw.text((x, 4), f"{name} 1x", fill=TXT)
        img.alpha_composite(f, (x + (zw - FRAME_W) // 2, y1))
        img.alpha_composite(f.resize((zw, zh), Image.NEAREST), (x, y2))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for b in hitbox_boxes(x + zw / 2, y2 + zh / 2, ZOOM):
            od.rectangle(b, outline=HITBOX)
        img.alpha_composite(overlay)
    y3 = y2 + zh + 20
    jet_names = [f"{n} {i}" for n in ("up", "left", "right", "down") for i in (0, 1)]
    for i, (f, name) in enumerate(zip(flame, jet_names)):
        x = gap + i * (zw + gap)
        draw.text((x, y3 - 14), name, fill=TXT)
        both = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        both.alpha_composite(f)
        both.alpha_composite(body[1])
        img.alpha_composite(both.resize((zw, zh), Image.NEAREST), (x, y3))
    y4 = y3 + zh + 20
    for i, (f, name) in enumerate(zip(streaks, ["short 0", "short 1", "long 0", "long 1"])):
        x = gap + i * (STREAK_W * sz + gap)
        draw.text((x, y4 - 14), f"streaks {name}, moving right", fill=TXT)
        both = Image.new("RGBA", f.size, (0, 0, 0, 0))
        both.alpha_composite(f)
        both.alpha_composite(body[2], ((STREAK_W - FRAME_W) // 2, 0))
        img.alpha_composite(both.resize((STREAK_W * sz, FRAME_H * sz), Image.NEAREST), (x, y4))
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()
    body = body_frames()
    flame = flame_frames()
    streaks = streak_frames()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    strip(body).save(args.out_dir / "ship.png")
    strip(flame).save(args.out_dir / "ship_flame.png")
    strip(streaks).save(args.out_dir / "ship_streaks.png")
    board(body, flame, streaks).save(args.out_dir / "ship-final-board.png")
    print("ship.png", strip(body).size, "ship_flame.png", strip(flame).size,
          "ship_streaks.png", strip(streaks).size)
    for name, f in zip(("l", "c", "r"), body):
        print(name, "box", f.getbbox())


if __name__ == "__main__":
    main()
