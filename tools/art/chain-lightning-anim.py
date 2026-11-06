"""Chain lightning animation strips: two node looks and the arc.

The nodes are the same two looks as the electric ball (storm core while charging,
bright urchin while firing) at node size: ball 12 px in an 18 px frame instead of
16 px in 24 px. They are redrawn from the 192 px masters of electric-ball-anim.py,
scaled to 144 px (0.75), then shrunk 8x. They are not a shrink of the 24 px strips.
The arc is new, in the same electricity palette. Look rules: docs/design/gdd/12-art-and-audio.md
(rules 3, 6, 9, 13) and docs/design/gdd/drifters/03-chain-lightning.md (arc_width 6, rule 9).

Strips (staging/assets/sprites/anim/, each with -board.png, -preview.gif, -master.png):
  chain_node_charge.png   8 frames 18x18, loop (same turn as electric_ball_charge)
  chain_node_fire.png     6 frames 18x18, random order; node circle r6 stays lit
  chain_arc.png           6 frames 181x16, random order; core inside the 6 px band y 5..10

Arc geometry: pixel coordinates, the bolt runs from (0,8) to (180,8). The band is
rows 5..10, centred on y = 8.0. Master scale 4x (724 x 64).

Usage: python3 tools/art/chain-lightning-anim.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites/anim"

_spec = importlib.util.spec_from_file_location("electric_ball_anim", ROOT / "tools/art/electric-ball-anim.py")
eb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eb)

NODE_SCALE = 0.75  # ball 16 px -> 12 px, canvas 24 -> 18
NODE_UP = 8

ARC_W, ARC_H = 181, 16
ARC_UP = 4
ARC_FRAMES = 6
BAND_Y0, BAND_Y1 = 5, 11  # rows 5..10, in continuous y: [5, 11), centre 8.0
CY = 8.0


def node_masters(masters):
    return [eb.scale_img(m, NODE_SCALE) for m in masters]


# ---------------------------------------------------------------- the arc

def arc_master(seed: int) -> Image.Image:
    """724x64 master. Glow fills the band; a jagged core stays inside it; thin side forks."""
    W, H = ARC_W * ARC_UP, ARC_H * ARC_UP
    rng = random.Random(4100 + seed * 37)
    S = ARC_UP
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    yg = (yy + 0.5) / S
    xg = (xx + 0.5) / S
    d = np.abs(yg - CY)

    # soft glow: purple wide, pale cyan in the band. Covers the whole band, fades by the frame edge.
    lam = rng.uniform(30, 70)
    phase = rng.uniform(0, 2 * math.pi)
    mod = 0.93 + 0.07 * np.sin(2 * math.pi * xg / lam + phase)
    purple = 0.55 * np.clip(1 - d / 8.0, 0, 1) ** 1.3 * mod
    cy_a = 0.62 * np.clip(1 - np.clip(d - 2.6, 0, None) / 3.4, 0, 1) ** 1.2 * mod
    canvas = np.zeros((H, W, 4), np.float32)
    for col, a in ((eb.PURPLE, purple), (eb.CYAN, cy_a)):
        lay = np.zeros((H, W, 4), np.float32)
        lay[..., :3] = np.array(col, np.float32) / 255
        lay[..., 3] = a
        canvas = eb.over(canvas, lay)

    # jagged core: centreline within +-2.0 px, segments 2.6..5 px long (survives a 0.7x squeeze)
    pts = []
    x = -3.0
    while x < ARC_W + 3:
        edge = min(1.0, max(0.0, (x + 3) / 8.0), max(0.0, (ARC_W + 3 - x) / 8.0))
        off = rng.uniform(-2.0, 2.0) * max(edge, 0.35)
        if abs(off) < 0.7:  # no lazy bends: every vertex is a real kink
            off = math.copysign(rng.uniform(1.1, 2.0), off or 1)
        pts.append((x, CY + off))
        x += rng.uniform(2.6, 5.0)
    pts.append((ARC_W + 3, CY))
    P = [(px * S, py * S) for px, py in pts]

    # thin side forks, purple and one fuchsia, leaving the core
    forks, fcol = [], []
    nf = rng.randint(4, 6)
    for k in range(nf):
        i = rng.randrange(2, len(pts) - 2)
        x0, y0 = pts[i]
        up = rng.choice((-1, 1))
        length = rng.uniform(4.0, 7.0)
        f = [(x0, y0)]
        steps = 4
        for j in range(1, steps + 1):
            t = j / steps
            fx = x0 + rng.uniform(-1.2, 2.2) * j
            fy = y0 + up * length * t + rng.uniform(-0.6, 0.6)
            f.append((fx, min(max(fy, 0.8), ARC_H - 0.8)))
        forks.append([(a * S, b * S) for a, b in f])
        fcol.append(k == 0)

    size = (W, H)
    pur = [f for f, c in zip(forks, fcol) if not c]
    fuc = [f for f, c in zip(forks, fcol) if c]
    canvas = eb.over(canvas, eb.stroke_layer(size, pur, [3.4] * len(pur), eb.ARC_PURPLE, 0.95, blur=0.3))
    canvas = eb.over(canvas, eb.stroke_layer(size, fuc, [3.4] * len(fuc), eb.FUCHSIA, 0.9, blur=0.3))
    # core: cyan body 1.8 px, white heart 0.85 px (max reach 2.0 + 0.9 = 2.9 < 3 from the centre)
    canvas = eb.over(canvas, eb.stroke_layer(size, [P], [7.2], eb.CYAN, 0.95))
    canvas = eb.over(canvas, eb.stroke_layer(size, [P], [3.4], eb.CORE, 1.0))
    return eb.to_img(canvas)


# ---------------------------------------------------------------- output

def band_hit(img, z):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in (BAND_Y0, BAND_Y1):
        d.line([(0, y * z), (img.width, y * z)], fill=(255, 255, 255, 110), width=1)
    img.alpha_composite(ov)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    eb.write_set(out, "chain_node_charge", node_masters(eb.charge_masters()), NODE_UP, 6, "loop",
                 "chain_node_charge 8x 18x18, loop, 6 to 2 ticks/frame; ball 12 px (no hitbox)", eb.circle_hit(9, 9, 6), z=4)
    eb.write_set(out, "chain_node_fire", node_masters(eb.fire_masters()), NODE_UP, 3, "random",
                 "chain_node_fire 6x 18x18, random order, 3 ticks/frame; node circle r6 = hitbox", eb.circle_hit(9, 9, 6), z=4)
    eb.write_set(out, "chain_arc", [arc_master(k) for k in range(ARC_FRAMES)], ARC_UP, 3, "random",
                 "chain_arc 6x 181x16, random order, 3 ticks/frame; band y 5..10 = hitbox", band_hit, z=4, stack=True)
    print("wrote chain lightning strips to", out)


if __name__ == "__main__":
    main()
