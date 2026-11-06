"""Planet, marbled look, turning: 24 frames of 64 x 64 (strip 1536 x 64).

The picked still is planet-d5 round 2 (seed 7). This script reuses that drawing
unchanged (tools/art/planet-d5.py is loaded, not edited) and only turns the
surface under it.

How the turn works:
  - planet-d5 builds its land and sea from a height map that is a sum of plane
    waves in 3D, sampled at each pixel's point on the sphere. Here that point is
    first rotated about the planet's pole, by 15 deg x frame, before the waves
    are sampled. The surface is a function of longitude, so 24 steps of 15 deg
    are one full turn and frame 24 flows into frame 1. Foreshortening comes
    from the sphere: fast in the middle, slow at the limb.
  - The sea line is fixed at the value frame 1 finds, so coasts do not breathe.
    Frame 1 is the still, pixel for pixel.
  - Shading, limb, haze, glint, rim and the circle edge depend only on the
    sphere normal, so they stay fixed. Only the surface pattern moves. The
    land bump (ridge light) travels with the land.
  - The surface slides left to right at the center (west to east).

Values: 24 frames, 64 x 64, 8 ticks per frame, 15 deg per frame (Director
request 2026-11-05, drifter_looks.json). 8x master (GDD 12 art_style).

Outputs, in --out-dir (default staging/assets/sprites/anim):
  planet_marble.png               strip, 1536 x 64 RGBA
  planet_marble-master.png        master strip, 12288 x 512
  planet_marble-board.png         every frame at 1x, then at 4x with the hitbox
  planet_marble-preview.gif       loop at 4x, 8 ticks (1/60 s) per frame

Usage: python3 tools/art/planet-marble-anim.py [--seed S] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites/anim"

FRAMES = 24
STEP_DEG = 15.0
TICKS = 8
GAME = 64
NAVY = (10, 13, 31)
TXT = (200, 205, 225)


def load_d5():
    spec = importlib.util.spec_from_file_location("planet_d5", ROOT / "tools/art/planet-d5.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _NpShim:
    """numpy, except quantile() returns a fixed sea line once one is set."""

    def __init__(self, real):
        self._real = real
        self.fixed = None
        self.seen = None

    def __getattr__(self, name):
        return getattr(self._real, name)

    def quantile(self, a, q, *args, **kw):
        v = self._real.quantile(a, q, *args, **kw)
        if self.seen is None:
            self.seen = float(v)
        return self.fixed if self.fixed is not None else v


def render_frames(seed):
    d5 = load_d5()
    shim = _NpShim(np)
    d5.np = shim
    orig_waves = d5.waves
    state = {"deg": 0.0}

    def turned_waves(p, rng, *a, **kw):
        t = np.radians(state["deg"])
        c, s = np.cos(t), np.sin(t)
        x, y, z = p[..., 0], p[..., 1], p[..., 2]
        q = np.stack([x * c - z * s, y, x * s + z * c], axis=-1).astype(np.float32)
        return orig_waves(q, rng, *a, **kw)

    d5.waves = turned_waves
    masters, sprites = [], []
    for i in range(FRAMES):
        state["deg"] = STEP_DEG * i
        shim.seen = None
        L = d5.render_layers(seed)
        if i == 0:
            shim.fixed = shim.seen  # the sea line of the still
        m = d5.to_image(d5.compose(L), L["alpha"])
        masters.append(m)
        sprites.append(d5.shrink(m))
        print(f"frame {i + 1}/{FRAMES}")
    return d5, masters, sprites


def strip(frames):
    w, h = frames[0].size
    out = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, (i * w, 0))
    return out


def board(sprites):
    pad, zoom = 16, 4
    n = len(sprites)
    zw = GAME * zoom
    w = pad + n * zw + (n - 1) * 4 + pad
    h = pad + 14 + GAME + pad + 14 + zw + pad
    img = Image.new("RGBA", (w, h), NAVY + (255,))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((pad, pad - 12), "1x, every frame (frame 1 to 24)", fill=TXT, font=font)
    for i, s in enumerate(sprites):  # 1x row, spaced like the 4x row below so frames line up
        img.alpha_composite(s, (pad + i * (zw + 4) + (zw - GAME) // 2, pad + 14))
    y4 = pad + 14 + GAME + pad + 14
    d.text((pad, y4 - 12), "4x, every frame, hitbox r32 drawn faintly", fill=TXT, font=font)
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for i, s in enumerate(sprites):
        x0 = pad + i * (zw + 4)
        img.alpha_composite(s.resize((zw, zw), Image.NEAREST), (x0, y4))
        cx, cy, rr = x0 + zw / 2, y4 + zw / 2, 32 * zoom
        for a0 in range(0, 360, 12):
            od.arc((cx - rr, cy - rr, cx + rr, cy + rr), a0, a0 + 6, fill=(255, 255, 255, 70), width=1)
        d.text((x0 + 3, y4 + 3), str(i + 1), fill=TXT, font=font)
    img.alpha_composite(over)
    return img


def gif(sprites, path):
    zoom = 4
    frames = []
    for s in sprites:
        bg = Image.new("RGBA", (GAME * zoom + 32, GAME * zoom + 32), NAVY + (255,))
        bg.alpha_composite(s.resize((GAME * zoom, GAME * zoom), Image.NEAREST), (16, 16))
        frames.append(bg.convert("RGB"))
    ms = TICKS * 1000 / 60  # 133.3 ms; GIF delays are 10 ms steps, so alternate 130, 130, 140
    durs = [[130, 130, 140][i % 3] for i in range(len(frames))]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)
    return ms


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    d5, masters, sprites = render_frames(args.seed)
    strip(sprites).save(out / "planet_marble.png")
    strip(masters).save(out / "planet_marble-master.png")
    board(sprites).save(out / "planet_marble-board.png")
    gif(sprites, out / "planet_marble-preview.gif")
    print("wrote", out)


if __name__ == "__main__":
    main()
