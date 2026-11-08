"""Bake the muted-music icon from game/tuning/mute_icon.json.

Writes:
  staging/assets/ui/mute_icon-master.png  the large master, size x 8 px (art_style factor for small sprites)
  staging/assets/ui/mute_icon.png         the master shrunk to size x size px
  game/assets/mute_icon.png               the same picture, only with --ship (after the checks)

A pale violet-white speaker with a fuchsia slash through it, on a transparent background. Still: one
picture, no frames. Size and both colors come from mute_icon.json; the game reads the same file and
refuses a picture of another size, so run this again after changing size or a color. Shapes are laid out
on a 24 unit grid and scaled to the size. Needs Pillow and numpy (tools/art/requirements.txt). Run from the
repo root:
    python3 tools/art/mute_icon.py [--ship]
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TUNING = Path("game/tuning/mute_icon.json")
STAGING = Path("staging/assets/ui")
SHIPPED = Path("game/assets/mute_icon.png")
FACTOR = 8
"""Master size against the shipped size: art_style, 8x for sprites up to 64 px (mute_icon_look)."""
AA = 4
"""Extra supersampling while drawing the master, so its edges are smooth."""
GRID = 24.0
"""The shapes below are laid out on this grid, then scaled to the size."""

BODY = (2.0, 8.5, 7.0, 15.5)
"""Speaker box: left, top, right, bottom."""
CONE = ((6.5, 8.5), (12.5, 3.5), (12.5, 20.5), (6.5, 15.5))
"""Speaker cone, widening to the right."""
ARCS = ((5.0, 1.5), (8.5, 1.5))
"""Sound waves: radius and stroke width, centered on the cone's mouth. Half angle ARC_SPAN degrees."""
ARC_SPAN = 42
ARC_CENTER = (12.5, 12.0)
SLASH = ((3.5, 3.0), (21.0, 21.0))
SLASH_WIDTH = 2.2
SLASH_GAP = 0.9
"""The slash's stroke, and the clear border it cuts out of the speaker on each side so it reads."""


def rgb(text: str) -> tuple[int, int, int]:
    """#rrggbb to (r, g, b)."""
    return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))


def line_mask(px: int, points, width: float) -> Image.Image:
    """A mask with a round-capped line through points (grid units) of the given grid width."""
    k = px / GRID
    mask = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(mask)
    d.line([(x * k, y * k) for x, y in points], fill=255, width=round(width * k))
    r = width * k / 2
    for x, y in points:
        d.ellipse((x * k - r, y * k - r, x * k + r, y * k + r), fill=255)
    return mask


def speaker_mask(px: int) -> Image.Image:
    """The speaker: box, cone and sound waves, with the slash's clear border cut out."""
    k = px / GRID
    mask = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(mask)
    left, top, right, bottom = BODY
    d.rounded_rectangle((left * k, top * k, right * k, bottom * k), radius=0.9 * k, fill=255)
    d.polygon([(x * k, y * k) for x, y in CONE], fill=255)
    cx, cy = ARC_CENTER
    for radius, width in ARCS:
        outer = (radius + width / 2) * k
        inner = (radius - width / 2) * k
        d.arc((cx * k - outer, cy * k - outer, cx * k + outer, cy * k + outer), -ARC_SPAN, ARC_SPAN, fill=255, width=round(outer - inner))
    gap = np.asarray(line_mask(px, SLASH, SLASH_WIDTH + 2 * SLASH_GAP), dtype=np.float32) / 255.0
    cut = np.asarray(mask, dtype=np.float32) * (1.0 - gap)
    return Image.fromarray(cut.astype(np.uint8), "L")


def draw_master(size: int, speaker: tuple, slash: tuple) -> Image.Image:
    """The RGBA master, size x FACTOR px square."""
    px = size * FACTOR * AA
    sp = np.asarray(speaker_mask(px), dtype=np.float32) / 255.0
    sl = np.asarray(line_mask(px, SLASH, SLASH_WIDTH), dtype=np.float32) / 255.0
    # Slash over speaker, premultiplied.
    rgb_p = np.zeros((px, px, 3), dtype=np.float32)
    rgb_p += sp[..., None] * np.array(speaker, dtype=np.float32)
    rgb_p = rgb_p * (1.0 - sl[..., None]) + sl[..., None] * np.array(slash, dtype=np.float32)
    alpha = sl + sp * (1.0 - sl)
    return premul_resize(rgb_p, alpha, size * FACTOR)


def premul_resize(rgb_p: np.ndarray, alpha: np.ndarray, out: int) -> Image.Image:
    """Shrink a premultiplied-color image and its alpha to out x out px, without dark fringes."""
    chans = [Image.fromarray(rgb_p[..., i].astype(np.float32), "F") for i in range(3)]
    a = Image.fromarray(alpha.astype(np.float32), "F")
    chans = [np.asarray(c.resize((out, out), Image.BOX if rgb_p.shape[0] % out == 0 else Image.LANCZOS)) for c in chans]
    a = np.asarray(a.resize((out, out), Image.BOX if rgb_p.shape[0] % out == 0 else Image.LANCZOS))
    safe = np.maximum(a, 1e-6)
    color = np.stack([np.clip(c / safe, 0, 255) for c in chans], axis=-1)
    img = np.dstack([color, np.clip(a, 0, 1) * 255.0])
    return Image.fromarray(np.rint(img).astype(np.uint8), "RGBA")


def shrink(master: Image.Image, size: int) -> Image.Image:
    """Shrink an RGBA master to size x size px, working on premultiplied color."""
    arr = np.asarray(master, dtype=np.float32)
    a = arr[..., 3] / 255.0
    return premul_resize(arr[..., :3] * a[..., None], a, size)


def main() -> None:
    """Read the tuning file, write the master and the picture."""
    tuning = json.loads(TUNING.read_text())
    size = tuning["size"]
    speaker, slash = rgb(tuning["speaker_color"]), rgb(tuning["slash_color"])
    master = draw_master(size, speaker, slash)
    picture = shrink(master, size)
    STAGING.mkdir(parents=True, exist_ok=True)
    master.save(STAGING / "mute_icon-master.png")
    picture.save(STAGING / "mute_icon.png")
    print(f"wrote {STAGING / 'mute_icon-master.png'} ({master.size[0]} px) and {STAGING / 'mute_icon.png'} ({size} px)")
    if "--ship" in sys.argv:
        picture.save(SHIPPED)
        print(f"wrote {SHIPPED}")


if __name__ == "__main__":
    main()
