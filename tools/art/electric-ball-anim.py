"""Electric ball animation strips: charge, fire, ring.

Source designs (picked by the Director): electric-ball-d4-r2 (storm core) for
the charge strip, electric-ball-d2-r2 (bright urchin) for the fire strip.
Their scripts are loaded as text and run with a few small substitutions (a
rotation offset, a spike count), so their drawing code is reused as it is and
the design scripts themselves stay untouched. Look rules: docs/design/gdd/12-art-and-audio.md
(rules 3, 6, 8, 9, 13) and docs/design/gdd/drifters/10-electric-ball.md.

Strips (all in staging/assets/sprites/anim/, each with -board.png, -preview.gif, -master.png):
  electric_ball_charge.png   8 frames 24x24, the spiral rays turn 45 deg per frame (loop)
  electric_ball_fire.png     6 frames 24x24, played in random order: spikes and arcs jump
  electric_ball_ring.png     6 frames 128x128, random order: fill + jagged rim, all inside r64

Master scale: 8x for the 24 px balls (192 px frames), 4x for the 128 px ring.
Shared helpers (shrink, board, gif, strips) are imported by chain-lightning-anim.py.

Usage: python3 tools/art/electric-ball-anim.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "staging/assets/sprites/anim"

BG = (10, 13, 31)  # the game's dark background (#0a0d1f)
NAVY = BG
CORE = (244, 254, 255)
CYAN = (150, 235, 255)
PALE_FILL = (175, 228, 255)
PURPLE = (170, 80, 255)
ARC_PURPLE = (205, 145, 255)
FUCHSIA = (255, 70, 205)
WHITE = (255, 255, 255)


# ---------------------------------------------------------------- shared helpers

def load_src(path: Path, subs, glb: dict) -> dict:
    """Run a design script's source with text substitutions; return its globals."""
    text = path.read_text()
    for old, new in subs:
        assert old in text, f"substitution target missing in {path.name}: {old!r}"
        text = text.replace(old, new)
    g = {"__name__": path.stem.replace("-", "_") + "_patched", "__file__": str(path)}
    g.update(glb)
    exec(compile(text, str(path), "exec"), g)
    return g


def to_img(arr) -> Image.Image:
    a = np.clip(arr, 0, 1)
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGBA")


def shrink(master: Image.Image, up: int) -> Image.Image:
    """Shrink by an integer factor with a premultiplied box filter."""
    a = np.asarray(master, np.float32) / 255
    pre = a.copy()
    pre[..., :3] *= a[..., 3:4]
    h, w = a.shape[0] // up, a.shape[1] // up
    pre = pre.reshape(h, up, w, up, 4).mean(axis=(1, 3))
    out = np.zeros_like(pre)
    al = pre[..., 3:4]
    out[..., :3] = np.where(al > 0, pre[..., :3] / np.maximum(al, 1e-6), 0)
    out[..., 3] = pre[..., 3]
    return to_img(out)


def scale_img(img: Image.Image, f: float) -> Image.Image:
    """Resize with premultiplied alpha so transparent pixels do not tint edges."""
    w, h = round(img.width * f), round(img.height * f)
    return img.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")


def layer(color, mask, strength=1.0, shape=None):
    m = np.asarray(mask, dtype=np.float32) / 255.0 * strength
    out = np.zeros((*m.shape, 4), dtype=np.float32)
    out[..., :3] = np.array(color, dtype=np.float32) / 255.0
    out[..., 3] = m
    return out


def over(dst, src):
    sa, da = src[..., 3:4], dst[..., 3:4]
    oa = sa + da * (1 - sa)
    rgb = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    return np.concatenate([rgb, oa], axis=-1)


def strip_of(frames) -> Image.Image:
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


def random_order(n: int, length: int, seed: int):
    """A play order like the game's random pick: never the same frame twice in a row."""
    rng = random.Random(seed)
    out = [rng.randrange(n)]
    while len(out) < length:
        k = rng.randrange(n)
        if k != out[-1]:
            out.append(k)
    return out


def on_bg(frame: Image.Image, z: int = 1) -> Image.Image:
    bg = Image.new("RGBA", frame.size, BG + (255,))
    bg.alpha_composite(frame)
    if z != 1:
        bg = bg.resize((frame.width * z, frame.height * z), Image.NEAREST)
    return bg


def save_gif(path: Path, frames, order, ticks: int):
    ims = [on_bg(frames[i], 4).convert("RGB") for i in order]
    ms = max(10, round(ticks * 1000 / 60 / 10) * 10)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1)


def make_board(path: Path, title: str, frames, z: int, hit, stack: bool = False, note: str = ""):
    """Frames at 1x on the dark background, then at zoom z with the hitbox drawn faintly."""
    font = ImageFont.load_default()
    n = len(frames)
    fw, fh = frames[0].size
    gap, pad, head = 10, 14, 22
    txt = (200, 205, 225)
    if stack:
        W = pad * 2 + max(fw * z, fw) + 40 + fw
        H = head + pad + n * (fh * z + gap) + 30
        img = Image.new("RGBA", (pad * 2 + fw + 30 + fw * z, head + 40 + n * (fh * z + gap)), BG + (255,))
        d = ImageDraw.Draw(img)
        d.text((pad, 6), title, fill=txt, font=font)
        d.text((pad, head + 4), "1x", fill=txt, font=font)
        d.text((pad + fw + 30, head + 4), f"{z}x, hitbox faint", fill=txt, font=font)
        for i, f in enumerate(frames):
            y = head + 20 + i * (fh * z + gap)
            img.alpha_composite(on_bg(f), (pad, y))
            zi = on_bg(f, z)
            hit(zi, z)
            img.alpha_composite(zi, (pad + fw + 30, y))
        img.convert("RGB").save(path)
        return
    row1 = fh + 28
    row2 = fh * z + 28
    W = pad * 2 + n * (fw * z + gap)
    W = max(W, pad * 2 + n * (fw + gap) + 20)
    H = head + row1 + row2 + 20
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    d.text((pad, 6), title + (("   " + note) if note else ""), fill=txt, font=font)
    d.text((pad, head), "1x, every frame", fill=txt, font=font)
    for i, f in enumerate(frames):
        img.alpha_composite(on_bg(f), (pad + i * (fw + gap), head + 14))
    y2 = head + row1
    d.text((pad, y2), f"{z}x, hitbox / key shape drawn faintly", fill=txt, font=font)
    for i, f in enumerate(frames):
        zi = on_bg(f, z)
        hit(zi, z)
        img.alpha_composite(zi, (pad + i * (fw * z + gap), y2 + 14))
    img.convert("RGB").save(path)


def circle_hit(cx, cy, r, alpha=90):
    def draw(img, z):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([(cx - r) * z, (cy - r) * z, (cx + r) * z - 1, (cy + r) * z - 1],
                                   outline=(255, 255, 255, alpha))
        img.alpha_composite(ov)
    return draw


def jag_bolt(rng, a, r0, r1, kinks, jitter, c):
    """Points (master px) of a jagged bolt along angle a from radius r0 to r1 about (c, c)."""
    nx, ny = -math.sin(a), math.cos(a)
    pts = []
    for i in range(kinks + 1):
        t = i / kinks
        r = r0 + (r1 - r0) * t
        j = 0 if i == kinks else rng.uniform(-1, 1) * jitter * (0.5 + t)
        pts.append((c + math.cos(a) * r + nx * j, c + math.sin(a) * r + ny * j))
    return pts


def stroke_layer(size, pts_list, widths, color, strength, ss=2, blur=0.0):
    """RGBA layer with every polyline in pts_list stroked at width w (master px), supersampled."""
    from PIL import ImageFilter
    big = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    d = ImageDraw.Draw(big)
    for pts, w in zip(pts_list, widths):
        p = [(x * ss, y * ss) for x, y in pts]
        d.line(p, fill=255, width=max(1, int(round(w * ss))), joint="curve")
        r = w * ss / 2
        for x, y in (p[0], p[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    m = big.resize(size, Image.LANCZOS)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return layer(color, m, strength)


# ---------------------------------------------------------------- charge (storm core)

CHARGE_FRAMES = 8
D4_SEED = 7


def d4_module():
    subs = [
        ("base = rng.uniform(0, 2 * math.pi)\n", "base = rng.uniform(0, 2 * math.pi) + ROT\n"),
        ("sa0 = rng.uniform(0, 2 * math.pi)\n", "sa0 = rng.uniform(0, 2 * math.pi) + ROT\n"),
        ("ns = 6\n", "ns = NSPIKE\n"),
        ("np.sin(ang * 3 - rad * 0.13)", "np.sin((ang - ROT) * 3 - rad * 0.13)"),
        # keep the thin fuchsia arm where the picked round-2 image has it (top and bottom)
        ("    afd.rectangle([0, 0, BIG, (C + 8) * SS], fill=0)  # rule 8: fuchsia only on the bottom side\n", ""),
    ]
    return load_src(ROOT / "tools/art/electric-ball-d4.py", subs, {"ROT": 0.0, "NSPIKE": 7})


def charge_masters():
    """8 master frames, 192x192. Rays, spikes, fuchsia arm and swirl turn 45 deg per frame;
    the glow, core and the fuchsia bottom rim stay put. A few small arcs crackle per frame."""
    g = d4_module()
    C, UPS = g["C"], g["MASTER"]
    out = []
    static = dict(g["draw_layers"](D4_SEED))  # glow, core and rim: the same on every frame
    for k in range(CHARGE_FRAMES):
        g["ROT"] = -2 * math.pi * k / CHARGE_FRAMES  # counter-clockwise: arms trail
        lay = dict(g["draw_layers"](D4_SEED))
        canvas = None
        for name in ("glow", "disc", "arms", "fuchsia", "core", "rim"):
            src = static[name] if name in ("glow", "core", "rim") else lay[name]
            canvas = src if canvas is None else over(canvas, src)
        rng = random.Random(500 + k * 17)
        bolts = []
        for _ in range(2):
            a = rng.uniform(0, 2 * math.pi)
            bolts.append(jag_bolt(rng, a, 56, rng.uniform(88, 94), 5, 5, C))
        canvas = over(canvas, stroke_layer((UPS, UPS), bolts, [7] * len(bolts), ARC_PURPLE, 0.6, blur=0.6))
        canvas = over(canvas, stroke_layer((UPS, UPS), bolts, [3] * len(bolts), CORE, 0.9))
        out.append(to_img(canvas))
    return out


# ---------------------------------------------------------------- fire (urchin)

FIRE_FRAMES = 6
FIRE_SEEDS = [7, 19, 31, 43, 55, 67]
FIRE_NSP = [7, 6, 8, 7, 6, 8]
FIRE_FLICKER = [1.0, 0.82, 1.18, 0.9, 1.12, 0.78]  # halo strength
FIRE_BODY = [1.0, 0.93, 1.0, 0.96, 1.0, 0.92]  # body brightness (1 = full white-cyan)


def d2_module():
    subs = [
        ("a = 2 * math.pi * (i + rng.uniform(-0.12, 0.12)) / n + 0.35",
         "a = 2 * math.pi * (i + rng.uniform(-0.12, 0.12)) / n + 0.35 + ROT"),
        ("    n = 7\n", "    n = NSP\n"),
    ]
    return load_src(ROOT / "tools/art/electric-ball-d2.py", subs, {"ROT": 0.0, "NSP": 7})


def fire_masters():
    """6 master frames, 192x192, each a different state: spikes turned and recounted, arcs
    redrawn, extra thin bolts, halo and body brightness flicker. Frame 0 is round 2 exactly."""
    g = d2_module()
    C, M = g["C"], g["MASTER"]
    rng0 = random.Random(2026)
    out = []
    for k in range(FIRE_FRAMES):
        g["ROT"] = 0.0 if k == 0 else rng0.uniform(0, 2 * math.pi)
        g["NSP"] = FIRE_NSP[k]
        lay = dict(g["draw_layers"](FIRE_SEEDS[k]))
        glow = lay["glow"].copy()
        glow[..., 3] = np.clip(glow[..., 3] * FIRE_FLICKER[k], 0, 1)
        body = lay["body"].copy()
        f = FIRE_BODY[k]
        body[..., :3] = body[..., :3] * f + (1 - f) * np.array(CYAN, np.float32) / 255 * 0.8
        canvas = glow
        for name, src in (("arcs", lay["arcs"]), ("spikes", lay["spikes"]), ("body", body), ("rim", lay["rim"])):
            canvas = over(canvas, src)
        rng = random.Random(900 + k * 13)
        bolts, fbolt = [], []
        for _ in range(4):
            a = rng.uniform(0, 2 * math.pi)
            bolts.append(jag_bolt(rng, a, 62, rng.uniform(86, 95), 4, 3.5, C))
        fbolt.append(jag_bolt(rng, rng.uniform(0, 2 * math.pi), 66, rng.uniform(80, 90), 4, 3, C))
        # behind the body: draw them, then the body again would hide the roots; simply start outside
        canvas = over(canvas, stroke_layer((M, M), bolts, [8] * len(bolts), ARC_PURPLE, 0.8, blur=0.5))
        canvas = over(canvas, stroke_layer((M, M), fbolt, [5], FUCHSIA, 0.8, blur=0.5))
        canvas = over(canvas, stroke_layer((M, M), bolts, [3.5] * len(bolts), CORE, 1.0))
        out.append(to_img(canvas))
    return out


# ---------------------------------------------------------------- ring (firing circle)

RING_FRAMES = 6
RING_SIZE = 128
RING_UP = 4
RING_R = 64
FILL_OPACITY = 0.35  # GDD 10-electric-ball fill_opacity


def ring_master(seed: int) -> Image.Image:
    """512x512 master (4x) of one ring frame. Everything is clipped to the circle r = 256."""
    M = RING_SIZE * RING_UP
    c = M / 2.0
    R = RING_R * RING_UP  # 256
    rng = random.Random(7000 + seed * 101)
    yy, xx = np.mgrid[0:M, 0:M].astype(np.float32)
    dist = np.hypot(xx + 0.5 - c, yy + 0.5 - c)
    disc = np.clip(R - dist + 0.5, 0, 1).astype(np.float32)  # anti-aliased circle, r = 256 exactly

    canvas = np.zeros((M, M, 4), np.float32)
    # 1. the fill: pale, flat 0.35, all the way to the rim
    fill = np.zeros((M, M, 4), np.float32)
    fill[..., :3] = np.array(PALE_FILL, np.float32) / 255
    fill[..., 3] = FILL_OPACITY
    canvas = over(canvas, fill)

    # 1b. a soft cyan lift toward the rim, so the whole circle reads lit
    ramp = np.clip((dist - 140) / 100, 0, 1) ** 1.5
    lift = np.zeros((M, M, 4), np.float32)
    lift[..., :3] = np.array(CYAN, np.float32) / 255
    lift[..., 3] = ramp * 0.22
    canvas = over(canvas, lift)

    # 2. faint inner filaments, from the rim inward
    fil = []
    for _ in range(5):
        a = rng.uniform(0, 2 * math.pi)
        fil.append(jag_bolt(rng, a, 226, 226 - rng.uniform(40, 110), 5, 9, c))
    canvas = over(canvas, stroke_layer((M, M), fil, [9] * len(fil), ARC_PURPLE, 0.45, blur=1.2))
    canvas = over(canvas, stroke_layer((M, M), fil, [3.5] * len(fil), CORE, 0.6))

    # 3. the jagged rim just inside r64: a closed zig-zag band
    pts = []
    th = rng.uniform(0, 2 * math.pi)
    th0 = th
    r_prev = 229.0
    while th < th0 + 2 * math.pi - 0.03:
        # irregular lightning: uneven steps, uneven jumps, now and then a long sharp kick
        step = rng.uniform(0.035, 0.085)
        target = 229 + rng.uniform(-9, 9)
        if rng.random() < 0.18:
            target += rng.uniform(5, 10)
        r_prev = r_prev * 0.2 + target * 0.8
        r = min(r_prev, 240)
        pts.append((c + math.cos(th) * r, c + math.sin(th) * r))
        th += step
    pts.append(pts[0])
    canvas = over(canvas, stroke_layer((M, M), [pts], [34], PURPLE, 0.45, blur=5))
    canvas = over(canvas, stroke_layer((M, M), [pts], [22], ARC_PURPLE, 0.8, blur=1.0))
    canvas = over(canvas, stroke_layer((M, M), [pts], [13], CYAN, 0.95))
    canvas = over(canvas, stroke_layer((M, M), [pts], [6], CORE, 1.0))

    # 4. thin fuchsia accents: three short jagged strands inside the rim (rule 6: thin only)
    fu = []
    for _ in range(3):
        a0 = rng.uniform(0, 2 * math.pi)
        span = rng.uniform(0.4, 0.8)
        strand = []
        steps = 9
        for j in range(steps + 1):
            a = a0 + span * j / steps
            r = 209 + rng.uniform(-5, 5)
            strand.append((c + math.cos(a) * r, c + math.sin(a) * r))
        fu.append(strand)
    canvas = over(canvas, stroke_layer((M, M), fu, [4] * len(fu), FUCHSIA, 0.85, blur=0.4))

    canvas[..., 3] *= disc  # nothing outside the hitbox circle
    return to_img(canvas)


def ring_trim(frame: Image.Image) -> Image.Image:
    """Zero every pixel whose centre lies outside the circle r64: the look never passes the hitbox."""
    a = np.asarray(frame).copy()
    yy, xx = np.mgrid[0:RING_SIZE, 0:RING_SIZE]
    a[np.hypot(xx + 0.5 - RING_SIZE / 2, yy + 0.5 - RING_SIZE / 2) > RING_R] = 0
    return Image.fromarray(a, "RGBA")


def ring_masters():
    return [ring_master(k) for k in range(RING_FRAMES)]


# ---------------------------------------------------------------- output

def write_set(out: Path, stem: str, masters, up: int, ticks: int, order: str, title: str, hit, z=4, stack=False, note="", post=None):
    frames = [shrink(m, up) for m in masters]
    if post:
        frames = [post(f) for f in frames]
    strip_of(frames).save(out / f"{stem}.png")
    strip_of(masters).save(out / f"{stem}-master.png")
    make_board(out / f"{stem}-board.png", title, frames, z, hit, stack, note)
    seq = list(range(len(frames))) if order == "loop" else random_order(len(frames), 48, 3)
    save_gif(out / f"{stem}-preview.gif", frames, seq, ticks)
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    write_set(out, "electric_ball_charge", charge_masters(), 8, 6, "loop",
              "electric_ball_charge 8x 24x24, loop, 6 to 2 ticks/frame; ball 16 px (no hitbox)", circle_hit(12, 12, 8))
    write_set(out, "electric_ball_fire", fire_masters(), 8, 3, "random",
              "electric_ball_fire 6x 24x24, random order, 3 ticks/frame; ball 16 px", circle_hit(12, 12, 8))
    write_set(out, "electric_ball_ring", ring_masters(), RING_UP, 3, "random",
              "electric_ball_ring 6x 128x128, random order, 3 ticks/frame; circle r64 = hitbox", circle_hit(64, 64, 64, 120),
              z=2, note="(zoom 2x, not 4x, to keep the board readable)", post=ring_trim)
    print("wrote electric ball strips to", out)


if __name__ == "__main__":
    main()
