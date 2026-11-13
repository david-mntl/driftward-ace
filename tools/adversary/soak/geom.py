"""Independent geometry for the soak oracle. Written from the shape definitions, not from core.collision.

Ship hitbox = list of upright boxes (cx, cy, w, h). Drifter shapes are core.collision shapes (read as data).
`e` > 0 shrinks (a definite overlap), e < 0 grows (a definite miss).
"""

from __future__ import annotations

import math

import paths  # noqa: F401  (puts game/ on sys.path)
from core.collision import Box, Circle, Line, Polygon


def _box_pts(cx, cy, w, h):
    return ((cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2))


def _proj(pts, ax, ay):
    ds = [p[0] * ax + p[1] * ay for p in pts]
    return min(ds), max(ds)


def _normals(pts):
    n = len(pts)
    out = []
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        L = math.hypot(ex, ey)
        if L > 0:
            out.append((-ey / L, ex / L))
    return out


def sat_depth(p, q):
    """Min penetration over all edge normals of two convex polygons (<=0 means apart)."""
    best = math.inf
    for ax, ay in _normals(p) + _normals(q):
        a0, a1 = _proj(p, ax, ay)
        b0, b1 = _proj(q, ax, ay)
        pen = min(a1, b1) - max(a0, b0)
        if pen < best:
            best = pen
    return best


def _pt_box_dist(px, py, b):
    cx, cy, w, h = b
    dx = max(abs(px - cx) - w / 2, 0.0)
    dy = max(abs(py - cy) - h / 2, 0.0)
    return math.hypot(dx, dy)


def _pt_seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _seg_hits_box(ax, ay, bx, by, b):
    cx, cy, w, h = b
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    t0, t1 = 0.0, 1.0
    dx, dy = bx - ax, by - ay
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return True


def _seg_box_dist(ax, ay, bx, by, b):
    if _seg_hits_box(ax, ay, bx, by, b):
        return 0.0
    cx, cy, w, h = b
    ds = [_pt_box_dist(ax, ay, b), _pt_box_dist(bx, by, b)]
    for px, py in _box_pts(cx, cy, w, h):
        ds.append(_pt_seg_dist(px, py, ax, ay, bx, by))
    return min(ds)


def shape_box_overlap(shape, b, e=1e-6) -> bool:
    """True when `shape` and box b=(cx,cy,w,h) overlap by more than e px (e<0: within |e| px)."""
    cx, cy, w, h = b
    if isinstance(shape, Box):
        return (abs(shape.cx - cx) < (shape.w + w) / 2 - e) and (abs(shape.cy - cy) < (shape.h + h) / 2 - e)
    if isinstance(shape, Circle):
        return _pt_box_dist(shape.cx, shape.cy, b) < shape.r - e
    if isinstance(shape, Line):
        return _seg_box_dist(shape.ax, shape.ay, shape.bx, shape.by, b) < shape.thickness / 2 - e
    if isinstance(shape, Polygon):
        return sat_depth(shape.points, _box_pts(cx, cy, w, h)) > e
    raise TypeError(shape)


def shape_bbox(shape):
    if isinstance(shape, Box):
        return (shape.cx - shape.w / 2, shape.cy - shape.h / 2, shape.cx + shape.w / 2, shape.cy + shape.h / 2)
    if isinstance(shape, Circle):
        return (shape.cx - shape.r, shape.cy - shape.r, shape.cx + shape.r, shape.cy + shape.r)
    if isinstance(shape, Line):
        t = shape.thickness / 2
        return (
            min(shape.ax, shape.bx) - t,
            min(shape.ay, shape.by) - t,
            max(shape.ax, shape.bx) + t,
            max(shape.ay, shape.by) + t,
        )
    xs = [p[0] for p in shape.points]
    ys = [p[1] for p in shape.points]
    return (min(xs), min(ys), max(xs), max(ys))


def ship_boxes(x, y):
    """Independent copy of the ship's inverted T from 04-ship.md: bar 12x32, foot 32x12 along the bottom."""
    return [(x, y, 12, 32), (x, y + 16 - 6, 32, 12)]


def hits_ship(hitbox, x, y, e):
    """Any shape of a placed drifter hitbox overlaps the ship T by more than e."""
    sb = ship_boxes(x, y)
    for shape in hitbox:
        bb = shape_bbox(shape)
        for b in sb:
            if (
                bb[2] < b[0] - b[2] / 2 - 2
                or bb[0] > b[0] + b[2] / 2 + 2
                or bb[3] < b[1] - b[3] / 2 - 2
                or bb[1] > b[1] + b[3] / 2 + 2
            ):
                continue
            if shape_box_overlap(shape, b, e):
                return True
    return False


def island_depth(hitbox, x, y):
    """Max penetration depth of the ship T into any island shape (Box or Polygon). 0 if apart."""
    worst = 0.0
    for shape in hitbox:
        if isinstance(shape, Box):
            q = _box_pts(shape.cx, shape.cy, shape.w, shape.h)
        elif isinstance(shape, Polygon):
            q = shape.points
        else:
            continue
        for b in ship_boxes(x, y):
            p = _box_pts(*b)
            d = sat_depth(p, q)
            if d > worst:
                worst = d
    return worst
