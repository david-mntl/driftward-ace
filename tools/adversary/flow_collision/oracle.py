"""Independent geometry oracle: exact signed distance fields on a dense grid.

m(A,B) = min over grid points P of max(sdA(P), sdB(P)).  m < 0: the shapes share area
(depth about -2m); m > 0: they are apart (gap about 2m). Independent of core.collision math.
"""

import numpy as np
import paths  # noqa: F401  (puts game/ on sys.path)
from core.collision import Box, Circle, Line, Polygon


def _seg_dist(P, a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ab = b - a
    L2 = float(ab @ ab)
    if L2 == 0:
        return np.hypot(P[:, 0] - a[0], P[:, 1] - a[1])
    t = np.clip(((P - a) @ ab) / L2, 0, 1)
    proj = a + t[:, None] * ab
    return np.hypot(P[:, 0] - proj[:, 0], P[:, 1] - proj[:, 1])


def sd(shape, P, grow=0.0, square_box=True):
    """Signed distance of shape grown by `grow` (Minkowski by disk; boxes grow square per GDD)."""
    if isinstance(shape, Circle):
        return np.hypot(P[:, 0] - shape.cx, P[:, 1] - shape.cy) - shape.r - grow
    if isinstance(shape, Box):
        hw, hh = shape.w / 2 + (grow if square_box else 0), shape.h / 2 + (grow if square_box else 0)
        dx = np.abs(P[:, 0] - shape.cx) - hw
        dy = np.abs(P[:, 1] - shape.cy) - hh
        out = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
        ins = np.minimum(np.maximum(dx, dy), 0)
        d = out + ins
        return d - (0 if square_box else grow)
    if isinstance(shape, Line):
        return _seg_dist(P, (shape.ax, shape.ay), (shape.bx, shape.by)) - shape.thickness / 2 - grow
    if isinstance(shape, Polygon):
        pts = [tuple(p) for p in shape.points]
        n = len(pts)
        d = np.full(len(P), np.inf)
        for i in range(n):
            d = np.minimum(d, _seg_dist(P, pts[i], pts[(i + 1) % n]))
        # inside test by winding / cross signs
        cross_pos = np.ones(len(P), bool)
        cross_neg = np.ones(len(P), bool)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % n]
            c = (b[0] - a[0]) * (P[:, 1] - a[1]) - (b[1] - a[1]) * (P[:, 0] - a[0])
            cross_pos &= c >= 0
            cross_neg &= c <= 0
        inside = cross_pos | cross_neg
        return np.where(inside, -d, d) - grow
    raise TypeError(shape)


def bounds(shape, grow=0.0):
    if isinstance(shape, Circle):
        return (
            shape.cx - shape.r - grow,
            shape.cy - shape.r - grow,
            shape.cx + shape.r + grow,
            shape.cy + shape.r + grow,
        )
    if isinstance(shape, Box):
        return (
            shape.cx - shape.w / 2 - grow,
            shape.cy - shape.h / 2 - grow,
            shape.cx + shape.w / 2 + grow,
            shape.cy + shape.h / 2 + grow,
        )
    if isinstance(shape, Line):
        h = shape.thickness / 2 + grow
        return (
            min(shape.ax, shape.bx) - h,
            min(shape.ay, shape.by) - h,
            max(shape.ax, shape.bx) + h,
            max(shape.ay, shape.by) + h,
        )
    xs = [p[0] for p in shape.points]
    ys = [p[1] for p in shape.points]
    return (min(xs) - grow, min(ys) - grow, max(xs) + grow, max(ys) + grow)


def m_value(hb_a, hb_b, grow_a=0.0, step=0.25):
    """min_P max(sdA, sdB) with sdA = union over A's shapes (min), sdB likewise. inf if empty."""
    if not hb_a or not hb_b:
        return float("inf")
    ba = [bounds(s, grow_a) for s in hb_a]
    bb = [bounds(s) for s in hb_b]
    best = float("inf")
    # evaluate shape pair by pair (union -> min over pairs of the pair m)
    for sa, ra in zip(hb_a, ba, strict=True):
        for sb, rb in zip(hb_b, bb, strict=True):
            x0 = max(ra[0], rb[0]) - 2.0
            x1 = min(ra[2], rb[2]) + 2.0
            y0 = max(ra[1], rb[1]) - 2.0
            y1 = min(ra[3], rb[3]) + 2.0
            if x0 > x1 or y0 > y1:
                # apart by > 2 px in bounds: gap large; exact m >= 1 at least. report 1.0+gap-ish
                gap = max(max(ra[0], rb[0]) - min(ra[2], rb[2]), max(ra[1], rb[1]) - min(ra[3], rb[3]), 0)
                best = min(best, 1.0 + gap / 2)
                continue
            xs = np.arange(x0, x1 + step, step)
            ys = np.arange(y0, y1 + step, step)
            if len(xs) * len(ys) > 400_000:
                step2 = step * 2
                xs = np.arange(x0, x1 + step2, step2)
                ys = np.arange(y0, y1 + step2, step2)
            gx, gy = np.meshgrid(xs, ys)
            P = np.stack([gx.ravel(), gy.ravel()], 1)
            v = np.maximum(sd(sa, P, grow_a), sd(sb, P))
            best = min(best, float(v.min()))
    return best
