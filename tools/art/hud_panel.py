"""Bake the side panel HUD's pictures from game/tuning/hud.json.

Writes these files into game/assets/ (overwrites them):
  hud_frame.png   the cockpit frame and the pillar, glass and panel transparent
  hud_sheen.png   the glass sheen, play-area sized
  hud_panel.png   the panel background: boxes, tile backs, dial rings, footer (opaque)
  hud_ship.png    the hull wireframe with empty heart sockets
  hud_hearts.png  one strip, 5 cells: lit, dim, last life, break white, break hue
  hud_radar.png   one strip, motion.sweep_frames cells: the sweep wedge, one full turn
  hud_ring.png    one strip, motion.ring_frames cells: the graze ring growing
  hud_scan.png    the scan line

Text is not baked: the game draws it at 1x from the fonts. Shapes are drawn at 4x and shrunk with
smoothscale, because pygame.draw has no smooth edges. Colors, sizes and positions all come from
hud.json; the game reads the same file, so run this again after changing a color or the position
or size of a baked part. Parts drawn from fixed shapes (wireframe, hearts, dial, footer) are laid
out on the mock-up's grid and scaled by panel.scale; thin strokes stay 1 px. Needs pygame-ce only. Run from the repo root:
    python3 tools/art/hud_panel.py
"""

import colorsys
import json
import math
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

ASSETS = Path("game/assets")
TUNING = Path("game/tuning/hud.json")
SS = 4
"""Draw size against the shipped size."""

HEART_CELLS = ("lit", "dim", "last", "break_white", "break_hue")
"""Cells of hud_hearts.png, left to right. Must match HEART_CELLS in game/app/assets.py."""

HEART_DIM_ALPHA = 0.16
BREAK_HUE_DEGREES = 60
BREAK_HUE_LIFT = 0.35
"""The dim heart's brightness, and how the break's color shift is made: turn the hue this many
degrees, then move this share of the way to white. From the approved mock-up's CSS filters."""

CHAMFER = 10
BEVEL_GAP = 8
"""The frame's outer bevel line: px outside the glass, and the cut of its corners."""

Color = tuple[int, int, int]
Point = tuple[float, float]


def rgb(text: str) -> Color:
    """#rrggbb to (r, g, b)."""
    return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))


def lerp(a: Color, b: Color, t: float) -> Color:
    """Color a moved the share t of the way to color b."""
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t))


# ---------- 4x drawing helpers. Callers pass 1x coordinates. ----------


def blit_shape(dst: pygame.Surface, pts: list[Point], draw) -> None:
    """Draw into a temporary 4x layer around `pts`, then blend it onto `dst`."""
    sp = [(x * SS, y * SS) for x, y in pts]
    pad = 8 * SS
    x0 = int(max(0, min(p[0] for p in sp) - pad))
    y0 = int(max(0, min(p[1] for p in sp) - pad))
    x1 = int(min(dst.get_width(), max(p[0] for p in sp) + pad))
    y1 = int(min(dst.get_height(), max(p[1] for p in sp) + pad))
    if x1 <= x0 or y1 <= y0:
        return
    tmp = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
    draw(tmp, [(x - x0, y - y0) for x, y in sp])
    dst.blit(tmp, (x0, y0))


def poly(dst, pts, color, alpha=1.0, width=0.0) -> None:
    """A polygon, filled when width is 0, else an outline `width` px wide."""
    col = (*color, round(255 * alpha))
    w = round(width * SS)
    blit_shape(dst, pts, lambda t, p: pygame.draw.polygon(t, col, p, w))


def line(dst, a, b, color, alpha=1.0, width=1.0) -> None:
    """A straight line `width` px wide."""
    col = (*color, round(255 * alpha))
    w = max(1, round(width * SS))
    blit_shape(dst, [a, b], lambda t, p: pygame.draw.line(t, col, p[0], p[1], w))


def circle(dst, c, r, color, alpha=1.0, width=0.0) -> None:
    """A disc, or a ring `width` px wide."""
    col = (*color, round(255 * alpha))
    w = round(width * SS)
    rr = round(r * SS)

    def draw(t, p):
        pygame.draw.circle(t, col, (round((p[0][0] + p[1][0]) / 2), round((p[0][1] + p[1][1]) / 2)), rr, w)

    blit_shape(dst, [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)], draw)


def hires(w: int, h: int) -> pygame.Surface:
    """A transparent 4x layer for a w x h picture."""
    return pygame.Surface((w * SS, h * SS), pygame.SRCALPHA)


def shrink(s: pygame.Surface, w: int, h: int) -> pygame.Surface:
    """The 4x layer at its shipped size."""
    return pygame.transform.smoothscale(s, (w, h))


def ellipse_pts(cx, cy, rx, ry, n=48) -> list[Point]:
    """Points round an ellipse."""
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def gradient_strip(w: int, h: int, stops: list[tuple[float, Color]], vertical: bool) -> pygame.Surface:
    """An opaque gradient. stops: [(0..1, color)]."""
    n = h if vertical else w
    strip = pygame.Surface((1, n) if vertical else (n, 1))
    for i in range(n):
        t = i / max(1, n - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:], strict=False):
            if t0 <= t <= t1:
                strip.set_at((0, i) if vertical else (i, 0), lerp(c0, c1, (t - t0) / max(1e-9, t1 - t0)))
                break
    return pygame.transform.smoothscale(strip, (w, h))


def heart_pts(n: int = 14) -> list[Point]:
    """The heart, 24 x 22, as points sampled from cubic curves."""
    segs = [
        ((12, 21), (3, 14), (0, 10), (0, 6.5)),
        ((0, 6.5), (0, 3), (2.6, 0.5), (6, 0.5)),
        ((6, 0.5), (8.4, 0.5), (10.6, 1.9), (12, 4.0)),
        ((12, 4.0), (13.4, 1.9), (15.6, 0.5), (18, 0.5)),
        ((18, 0.5), (21.4, 0.5), (24, 3), (24, 6.5)),
        ((24, 6.5), (24, 10), (21, 14), (12, 21)),
    ]
    out: list[Point] = []
    for p0, p1, p2, p3 in segs:
        for i in range(n):
            t = i / n
            u = 1 - t
            out.append(
                (
                    u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
                )
            )
    return out


class Baker:
    """Holds the rules and the palette, and makes each picture."""

    def __init__(self, rules: dict) -> None:
        self.r = rules
        self.c: dict[str, Color] = {k: rgb(v) for k, v in rules["palette"].items()}
        self.win = rules["window"]
        self.panel = rules["panel"]
        self.k: float = rules["panel"]["scale"]
        self.pillar: int = rules["frame"]["pillar_width"]

    # ----- frame -----

    def frame(self) -> pygame.Surface:
        """The cockpit frame and the pillar: one transparent picture, glass cut out.

        The glass is the exact play area, a rectangle. Nothing is drawn on it: every stroke sits
        outside its edge, so the frame never covers a pixel of the play area.
        """
        c, fr = self.c, self.r["frame"]
        w, h = self.panel["x"] + fr["pillar_width"], self.win["height"]
        fx, fy = self.win["field_x"], self.win["field_y"]
        fw, fh = 640, 480
        big = hires(w, h)
        body = gradient_strip(w * SS, h * SS, [(0, c["frame_highlight"]), (0.5, c["frame_metal"]), (1, c["frame_highlight"])], False)
        big.blit(body, (0, 0))
        pygame.draw.rect(big, (0, 0, 0, 0), (fx * SS, fy * SS, fw * SS, fh * SS))
        glass_out = lambda d: [(fx - d, fy - d), (fx + fw + d, fy - d), (fx + fw + d, fy + fh + d), (fx - d, fy + fh + d)]  # noqa: E731
        outer = [
            (fx - BEVEL_GAP + CHAMFER, fy - BEVEL_GAP), (fx + fw + BEVEL_GAP - CHAMFER, fy - BEVEL_GAP),
            (fx + fw + BEVEL_GAP, fy - BEVEL_GAP + CHAMFER), (fx + fw + BEVEL_GAP, fy + fh + BEVEL_GAP - CHAMFER),
            (fx + fw + BEVEL_GAP - CHAMFER, fy + fh + BEVEL_GAP), (fx - BEVEL_GAP + CHAMFER, fy + fh + BEVEL_GAP),
            (fx - BEVEL_GAP, fy + fh + BEVEL_GAP - CHAMFER), (fx - BEVEL_GAP, fy - BEVEL_GAP + CHAMFER),
        ]
        poly(big, outer, c["frame_lights"], 0.45, 1)
        poly(big, glass_out(3), c["plating"], 0.3, 6)
        self._lit_edge(big, glass_out(1), w, h, fr["spill"])
        self._corner_lights(big, fx, fy, fw, fh, fr["spill"])
        for x in range(110, 540, 70):  # top rivets, centred on the glass as in the mock
            circle(big, (x + (fx + fw / 2 - 320), fy - 5), 1.5, c["plating"], 0.45)
        for y in range(110, 351, 60):
            circle(big, (fx - 8, y + (fy + fh / 2 - 231)), 1.5, c["plating"], 0.45)
        line(big, (fx + 400, fy + fh + 10), (fx + 590, fy + fh + 10), c["frame_lights"], 0.3, 1)
        self._pillar(big, h, fr)
        return shrink(big, w, h)

    def _lit_edge(self, big, ring: list[Point], w: int, h: int, spill: float) -> None:
        """The glass's lit edge: spill color at the bottom left to the second line at the top right."""
        c = self.c
        c0, c1, c2 = c["fuchsia_spill"], c["ship_lines"], c["ship_lines_light"]
        closed = [*ring, ring[0]]
        vx, vy = round(0.753 * w), -h
        for a, b in zip(closed, closed[1:], strict=False):
            for i in range(24):
                p = (a[0] + (b[0] - a[0]) * i / 24, a[1] + (b[1] - a[1]) * i / 24)
                q = (a[0] + (b[0] - a[0]) * (i + 1) / 24, a[1] + (b[1] - a[1]) * (i + 1) / 24)
                t = max(0.0, min(1.0, (p[0] * vx + (p[1] - h) * vy) / (vx * vx + vy * vy)))
                if t < 0.5:
                    col, al = lerp(c0, c1, t / 0.5), spill + (1 - spill) * (t / 0.5)
                else:
                    col, al = lerp(c1, c2, (t - 0.5) / 0.5), 1.0
                line(big, p, q, col, al, 2)

    def _corner_lights(self, big, fx: int, fy: int, fw: int, fh: int, spill: float) -> None:
        """Four lights in the ring's corners; the bottom left one takes the spill color."""
        c = self.c
        r = self.r["frame"]["light_radius"]
        for x, y, key, al in (
            (fx - 8, fy - 5, "frame_lights", 1),
            (fx + fw + 8, fy - 5, "frame_lights", 1),
            (fx + fw + 8, fy + fh + 14, "frame_lights", 1),
            (fx - 8, fy + fh + 14, "fuchsia_spill", spill),
        ):
            circle(big, (x, y), r, c[key], al)

    def _pillar(self, big, h: int, fr: dict) -> None:
        """The pillar: seam, dashes, rivets, and two caps."""
        c = self.c
        cx = self.panel["x"] + fr["pillar_width"] / 2
        half = fr["pillar_width"] / 2
        y0, y1 = 90, h - 80
        line(big, (cx, y0), (cx, y1), c["frame_lights"], 0.3, 1)
        y = float(y0)
        while y < y1:
            y2 = min(y1, y + 16)
            t = ((y + y2) / 2 - (y0 - 20)) / (y1 - y0 + 30)
            col = lerp(c["frame_lights"], c["fuchsia_spill"], max(0.0, (t - 0.65) / 0.35))
            line(big, (cx, y), (cx, y2), col, 1.0, 4)
            y += 22
        for yy in (26, 200 + (h - 480) / 2, 280 + (h - 480) / 2, h - 26):
            circle(big, (cx - 7, yy), 1.8, c["plating"], 0.45)
            circle(big, (cx + 7, yy), 1.8, c["plating"], 0.45)
        px = self.panel["x"]
        for pts in (
            [(px, 0), (px + 2 * half, 0), (px + 2 * half, 64), (cx, 80), (px, 64)],
            [(px, h), (px + 2 * half, h), (px + 2 * half, h - 64), (cx, h - 80), (px, h - 64)],
        ):
            poly(big, pts, c["frame_highlight"])
            poly(big, pts, c["frame_lights"], 0.5, 1)

    def sheen(self) -> pygame.Surface:
        """Two faint diagonal bands over the glass, the play area's size."""
        fw, fh = 640, 480
        big = hires(fw, fh)
        th = math.radians(112)
        dx, dy = math.sin(th), -math.cos(th)
        length = fw * abs(dx) + fh * abs(dy)
        cx, cy = fw / 2, fh / 2
        for t0, t1, al in ((0, 0.16, 0.06), (0.22, 0.27, 0.035)):

            def pt(t, s):
                return (cx + (t * length - length / 2) * dx - dy * s, cy + (t * length - length / 2) * dy + dx * s)

            poly(big, [pt(t0, 1000), pt(t1, 1000), pt(t1, -1000), pt(t0, -1000)], (255, 255, 255), al)
        return shrink(big, fw, fh)

    # ----- panel -----

    def bevel(self, dst, x, y, w, h) -> None:
        """A box with a cut top-right and bottom-left corner, edge line and a dark gradient fill."""
        c = self.c
        cut = 10 * self.k
        outer = [(x, y), (x + w - cut, y), (x + w, y + cut), (x + w, y + h), (x + cut, y + h), (x, y + h - cut)]
        poly(dst, outer, lerp(c["panel_body"], c["ship_lines"], 0.6))
        inner = [(x + 1, y + 1), (x + w - cut, y + 1), (x + w - 1, y + cut), (x + w - 1, y + h - 1), (x + cut, y + h - 1), (x + 1, y + h - cut - 0.4)]
        top = tuple(round(v * 0.35) for v in c["panel_body"])
        bottom = tuple(round(v * 0.8) for v in c["panel_body"])
        g = gradient_strip(round(w * SS), round(h * SS), [(0, top), (1, bottom)], True).convert_alpha()
        mask = pygame.Surface(g.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), [((px - x) * SS, (py - y) * SS) for px, py in inner])
        g.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        dst.blit(g, (round(x * SS), round(y * SS)))

    def panel_picture(self) -> pygame.Surface:
        """The panel background, opaque. The content is the mock's, moved down by content_y."""
        c, s, lv, gz = self.c, self.r["score"], self.r["level"], self.r["graze"]
        pw, ph = self.panel["width"], self.win["height"]
        big = hires(pw, ph)
        big.blit(gradient_strip(pw * SS, ph * SS, [(0, tuple(round(v * 0.7) for v in c["panel_body"])), (1, c["panel_body"])], True), (0, 0))
        content = hires(pw, ph)
        self.bevel(content, *s["box"])
        for i in range(s["tile_count"]):
            x = s["tile_x"] + i * s["tile_pitch"]
            y = s["tile_y"]
            poly(content, [(x, y), (x + s["tile_w"], y), (x + s["tile_w"], y + s["tile_h"]), (x, y + s["tile_h"])], c["tile_bg"])
        self.bevel(content, *lv["box"])
        dcx, dcy = gz["center"]
        ring = lerp(c["panel_body"], c["graze"], 0.4)
        ring2 = lerp(c["panel_body"], c["graze"], 0.22)
        circle(content, (dcx, dcy), gz["radius"], ring, 1.0, 1)
        inner = gz["inner_radius"]
        for k in range(0, 360, 12):  # dashed ring
            a0, a1 = math.radians(k), math.radians(k + 5)
            line(content, (dcx + inner * math.cos(a0), dcy + inner * math.sin(a0)), (dcx + inner * math.cos(a1), dcy + inner * math.sin(a1)), ring2, 1.0, 1)
        arm = gz["radius"] - 2 * self.k
        line(content, (dcx, dcy - arm), (dcx, dcy + arm), ring2, 1.0, 1)
        line(content, (dcx - arm, dcy), (dcx + arm, dcy), ring2, 1.0, 1)
        bx, bw = s["box"][0], s["box"][2]
        foot_y, dot = 461.5 * self.k, 4.5 * self.k
        circle(content, (bx + dot, foot_y), dot, c["footer_dot"], 1.0, 1)
        circle(content, (bx + bw - dot, foot_y), dot, c["footer_dot"], 1.0, 1)
        line(content, (bx + 19 * self.k, foot_y), (bx + bw - 19 * self.k, foot_y), c["line"], 1.0, 1)
        big.blit(content, (0, self.panel["content_y"] * SS))
        return shrink(big, pw, ph).convert()

    # ----- wireframe and hearts -----

    SC = 0.85
    """Scale of the wireframe against the HUD's 200 x 228 grid, from the mock-up."""

    def stroke(self, width: float) -> float:
        """A stroke of the mock-up's ``width`` on the wireframe grid, scaled, never under 1 px."""
        return max(1.0, width * self.SC * self.k)

    def _sv(self, dx: float, sy: float) -> Point:
        return (100 + dx * 5, 22 + (sy - 16) * 4.6)

    def _v(self, p: Point) -> Point:
        """A point of the mock-up's wireframe grid to panel space at this scale."""
        x, y = 38 + p[0] * self.SC, 126 + p[1] * self.SC
        return (self.pillar + (x - self.pillar) * self.k, y * self.k)

    def socket_centers(self) -> list[Point]:
        """Where the three heart sockets sit on the wireframe, panel space, from hud.json."""
        return [(float(x), float(y)) for x, y in self.r["hearts"]["slots"]]

    def ship_picture(self) -> pygame.Surface:
        """The wireframe: a hull outline traced from the real ship, with three empty sockets."""
        c, hr = self.c, self.r["hearts"]
        bx, by, bw, bh = hr["ship_box"]
        big = hires(bw, bh)
        sc = self.SC * self.k

        def at(p: Point) -> Point:
            return (p[0] - bx, p[1] - by)

        sv = self._sv
        v = lambda p: at(self._v(p))  # noqa: E731
        right = [(0, 16), (1.6, 21), (2.6, 26), (3.4, 30), (4.6, 33.2), (5.4, 34.8), (7.4, 30.6), (8.8, 24.8), (10.2, 29.4), (13.0, 33.6), (16.0, 38.5), (17.6, 43.5), (18.4, 47.5), (15.6, 43.8), (10.5, 40.6), (6.0, 41.8), (4.8, 44.2), (11.2, 50.6), (6.4, 47.6), (3.8, 48.6), (3.6, 51)]
        outline = [sv(dx, sy) for dx, sy in right] + [sv(-dx, sy) for dx, sy in reversed(right[1:])]
        body = [v(p) for p in outline]
        poly(big, body, c["ship_lines"], 0.12)
        poly(big, body, c["ship_lines_light"], 1.0, self.stroke(1.3))
        for a, b in [((0, 19), (0, 50)), ((6, 37), (15.2, 43)), ((8.4, 33), (14, 40.5)), ((4.8, 44.6), (4.2, 48))]:
            line(big, v(sv(*a)), v(sv(*b)), c["ship_lines"], 1.0, self.stroke(1))
            line(big, v(sv(-a[0], a[1])), v(sv(-b[0], b[1])), c["ship_lines"], 1.0, self.stroke(1))
        poly(big, [v(p) for p in ellipse_pts(*sv(0, 27.5), 7, 13)], c["plating"], 1.0, self.stroke(1.2))
        for jx, tipy, half in ((0, 60, 1.9), (-10.4, 57, 1.1), (10.4, 57, 1.1)):
            by_ = 50.6 if jx == 0 else 50.2
            poly(big, [v(sv(jx - half, by_)), v(sv(jx, tipy)), v(sv(jx + half, by_))], c["ship_lines_light"], 0.85)
        for cx, cy in self.socket_centers():
            ax, ay = cx - bx, cy - by
            circle(big, (ax, ay), 17 * sc, c["panel_body"])
            circle(big, (ax, ay), 17 * sc, c["ship_lines"], 1.0, self.stroke(1))
        return shrink(big, bw, bh)

    def hearts_picture(self) -> pygame.Surface:
        """The five heart cells in one strip."""
        c, hr = self.c, self.r["hearts"]
        cw, ch = hr["cell_w"], hr["cell_h"]
        hue_h, hue_s, hue_v = colorsys.rgb_to_hsv(*(v / 255 for v in c["hearts"]))
        shifted = tuple(round(v * 255) for v in colorsys.hsv_to_rgb((hue_h + BREAK_HUE_DEGREES / 360) % 1, hue_s, hue_v))
        looks = {
            "lit": (c["hearts"], 1.0),
            "dim": (c["hearts"], HEART_DIM_ALPHA),
            "last": (c["last_life"], 1.0),
            "break_white": ((255, 255, 255), 1.0),
            "break_hue": (lerp(shifted, (255, 255, 255), BREAK_HUE_LIFT), 1.0),  # type: ignore[arg-type]
        }
        big = hires(cw * len(HEART_CELLS), ch)
        hp = heart_pts()
        sc = self.SC * self.k
        for i, name in enumerate(HEART_CELLS):
            color, alpha = looks[name]
            cx, cy = i * cw + cw / 2, ch / 2
            pts = [(cx + (px * 1.15 - 14) * sc, cy + (py * 1.15 - 12.7) * sc) for px, py in hp]
            poly(big, pts, color, alpha)
        return shrink(big, cw * len(HEART_CELLS), ch)

    # ----- motion pictures -----

    def radar_picture(self) -> pygame.Surface:
        """The sweep wedge, one cell per step of a full turn. A wedge fading toward its trailing edge."""
        m, gz = self.r["motion"], self.r["graze"]
        n, rad = m["sweep_frames"], gz["wedge_radius"]
        cell = 2 * rad + 2
        strip = pygame.Surface((cell * n, cell), pygame.SRCALPHA)
        graze = self.c["graze"]
        for k in range(n):
            big = hires(cell, cell)
            rot = 360 * k / n
            cx = cy = cell / 2 * SS
            steps = 220
            for i in range(steps):
                a = 250 + 110 * i / steps
                a0, a1 = math.radians(a + rot - 90), math.radians(a + 110 / steps + 0.4 + rot - 90)
                alpha = 0.38 * i / steps
                pts = [(cx, cy), (cx + rad * SS * math.cos(a0), cy + rad * SS * math.sin(a0)), (cx + rad * SS * math.cos(a1), cy + rad * SS * math.sin(a1))]
                pygame.draw.polygon(big, (*graze, round(255 * alpha)), pts)
            strip.blit(shrink(big, cell, cell), (k * cell, 0))
        return strip

    def ring_picture(self) -> pygame.Surface:
        """The graze ring growing from ring_from to ring_to times its radius, fading as it goes."""
        m = self.r["motion"]
        n = m["ring_frames"]
        cell = 2 * math.ceil(m["ring_radius"] * m["ring_to"]) + 2
        strip = pygame.Surface((cell * n, cell), pygame.SRCALPHA)
        for i in range(n):
            u = (i + 0.5) / n
            ease = 1 - (1 - u) ** 2
            scale = m["ring_from"] + (m["ring_to"] - m["ring_from"]) * ease
            big = hires(cell, cell)
            circle(big, (cell / 2, cell / 2), m["ring_radius"] * scale, (255, 255, 255), 1 - ease, 1)
            strip.blit(shrink(big, cell, cell), (i * cell, 0))
        return strip

    def scan_picture(self) -> pygame.Surface:
        """The scan line: soft, 28 percent, the second line color."""
        w = self.r["motion"]["scan_w"]
        big = hires(w, 3)
        line(big, (0, 1.5), (w, 1.5), self.c["ship_lines_light"], 0.28, self.stroke(2))
        return shrink(big, w, 3)


def main() -> None:
    """Read hud.json and write every picture."""
    rules = json.loads(TUNING.read_text(encoding="utf-8"))
    pygame.init()
    pygame.display.set_mode((1, 1))
    baker = Baker(rules)
    pictures = {
        "hud_frame.png": baker.frame(),
        "hud_sheen.png": baker.sheen(),
        "hud_panel.png": baker.panel_picture(),
        "hud_ship.png": baker.ship_picture(),
        "hud_hearts.png": baker.hearts_picture(),
        "hud_radar.png": baker.radar_picture(),
        "hud_ring.png": baker.ring_picture(),
        "hud_scan.png": baker.scan_picture(),
    }
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name, surface in pictures.items():
        pygame.image.save(surface, str(ASSETS / name))
        print("wrote", ASSETS / name, surface.get_size())


if __name__ == "__main__":
    main()
