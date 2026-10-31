"""Bake the far painting's slow sway into looping keyframes.

Reads game/assets/background.png (the still painting) and writes game/assets/background_sway_00.png
.. background_sway_<KEYFRAMES-1>.png. Frame `i` is the painting at loop phase i / KEYFRAMES. The
game blends between neighbours over sway_loop_ticks (tuning/background.json), so the last frame
blends back into the first. Each frame keeps the still's mean brightness. Overwrites those files.
Run from the repo root:
    python3 tools/art/background_sway.py
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image

ASSETS = Path("game/assets")
KEYFRAMES = 12
"""Frames in the loop. Must match SWAY_FRAMES in game/app/assets.py."""
SWAY_PX = 10.0
"""Peak sideways swing of the rays, px."""
FLOW_PX = 7.0
"""Peak in-and-out ripple of the rays along their curves, px."""
RIM_GAIN = 0.25
"""Swing of the turning light on the hole's rim, as a share of the rim's own brightness."""
WAVELENGTH = 240.0
"""Distance between ripple crests, px."""
HOLE_CENTER = (5.0, 486.0)
HOLE_RADIUS = 80.0
"""Same as HOLE_CENTER and HOLE_RADIUS in game/ui/background_view.py: both belong to the painting."""
HOLE_EASE = 90.0
"""Distance over which the sway fades in from the hole's edge, px, so the edge itself stays put."""
RIM_CENTER = 25.0
RIM_WIDTH = 55.0
"""The turning rim light is a bell this wide, centered this far outside the hole's edge, px."""
RIM_LOBES = 4
"""Bright patches around a full turn. About one shows in the quarter of the hole on screen."""
RAY_TWIST = 3.0
"""How much the ripple's phase changes around the hole, so the rays do not move in lockstep."""
FLOW_LAG = 1.3
"""Phase gap between the sideways swing and the in-and-out ripple, radians."""


def bake(still: np.ndarray) -> list[np.ndarray]:
    """Return KEYFRAMES uint8 images (h, w, 3) of the loop, from the (h, w, 3) float still."""
    height, width, _ = still.shape
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    dx, dy = xs - HOLE_CENTER[0], ys - HOLE_CENTER[1]
    radius = np.hypot(dx, dy)
    theta = np.arctan2(dy, dx)
    out_x, out_y = dx / np.maximum(radius, 1e-3), dy / np.maximum(radius, 1e-3)
    ease = np.clip((radius - HOLE_RADIUS) / HOLE_EASE, 0, 1)
    ease = ease * ease * (3 - 2 * ease)
    rim = np.exp(-(((radius - HOLE_RADIUS - RIM_CENTER) / RIM_WIDTH) ** 2))
    frames: list[np.ndarray] = []
    for index in range(KEYFRAMES):
        phase = index / KEYFRAMES
        travel = math.tau * phase + math.tau * radius / WAVELENGTH + RAY_TWIST * theta
        sway = SWAY_PX * ease * np.sin(travel)
        flow = FLOW_PX * ease * np.sin(travel + FLOW_LAG)
        moved = _sample(still, xs + sway * out_y - flow * out_x, ys - sway * out_x - flow * out_y)
        light = 1 + RIM_GAIN * rim * np.sin(RIM_LOBES * theta - math.tau * phase)
        image = moved * light[..., None]
        image *= still.mean() / image.mean()
        frames.append(np.rint(np.clip(image, 0, 255)).astype(np.uint8))
    return frames


def _sample(image: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    """Bilinear sample of `image` at (sx, sy), clamped to its edges."""
    height, width, _ = image.shape
    sx = np.clip(sx, 0, width - 1.001)
    sy = np.clip(sy, 0, height - 1.001)
    x0, y0 = sx.astype(np.int32), sy.astype(np.int32)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    top = image[y0, x0] * (1 - fx) + image[y0, x0 + 1] * fx
    bottom = image[y0 + 1, x0] * (1 - fx) + image[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bottom * fy


if __name__ == "__main__":
    painting = np.asarray(Image.open(ASSETS / "background.png").convert("RGB"), dtype=np.float32)
    for number, frame in enumerate(bake(painting)):
        Image.fromarray(frame).save(ASSETS / f"background_sway_{number:02d}.png", optimize=True)
