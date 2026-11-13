"""Random shape-pair fuzz of core.collision against the SDF oracle (all 4x4 kinds, any size/angle)."""

import json, math, random, sys
from collections import defaultdict

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT  # noqa
from paths import out_dir
from oracle import m_value
from core.collision import Box, Circle, Line, Polygon, grow_hitbox, hitboxes_near, hitboxes_overlap

rng = random.Random(42)


def rnd_shape(kind, cx, cy):
    if kind == "Circle":
        return Circle(cx, cy, rng.choice([0.5, 1, 3, 8, 20, 40]) * rng.uniform(0.8, 1.2))
    if kind == "Box":
        return Box(
            cx,
            cy,
            rng.choice([1, 4, 12, 32, 60]) * rng.uniform(0.8, 1.2),
            rng.choice([1, 4, 12, 32, 60]) * rng.uniform(0.8, 1.2),
        )
    if kind == "Line":
        L = rng.choice([0, 2, 10, 40, 90])
        a = rng.uniform(0, 6.28)
        return Line(
            cx - L / 2 * math.cos(a),
            cy - L / 2 * math.sin(a),
            cx + L / 2 * math.cos(a),
            cy + L / 2 * math.sin(a),
            rng.choice([1, 3, 8, 20]),
        )
    n = rng.choice([3, 3, 4, 5, 6])
    R = rng.choice([4, 12, 30, 50])
    angs = sorted(rng.uniform(0, 6.28) for _ in range(n))
    # convex: points on a circle, ensure min separation
    angs = [2 * math.pi * i / n + rng.uniform(-0.3, 0.3) / n * 2 for i in range(n)]
    sx = rng.uniform(0.5, 1.5)
    pts = tuple((cx + R * sx * math.cos(a), cy + R * math.sin(a)) for a in angs)
    if rng.random() < 0.5:
        pts = pts[::-1]
    return Polygon(pts)


def main(N):
    kinds = ["Circle", "Box", "Line", "Polygon"]
    bad = defaultdict(list)
    count = defaultdict(int)
    for ka in kinds:
        for kb in kinds:
            for _i in range(N):
                a = rnd_shape(ka, 0.0, 0.0)
                off = rng.uniform(0, 90)
                ang = rng.uniform(0, 6.28)
                b = rnd_shape(kb, off * math.cos(ang), off * math.sin(ang))
                code = hitboxes_overlap((a,), (b,))
                m = m_value((a,), (b,))
                count[(ka, kb)] += 1
                if code and m > 0.6:
                    bad[(ka, kb, "false_hit")].append((round(m, 3), a, b))
                if not code and m < -0.5:
                    bad[(ka, kb, "miss")].append((round(m, 3), a, b))
                # symmetry
                if hitboxes_overlap((b,), (a,)) != code:
                    bad[(ka, kb, "asymmetric")].append((m, a, b))
                # near
                for mg in (0.0, 5.0, 14.0):
                    if code and not hitboxes_near((a,), (b,), mg):
                        bad[(ka, kb, "near_skip")].append((mg, a, b))
                # grown-zone vs oracle (box zone square corners per GDD)
                zone = grow_hitbox((a,), 14.0)
                zc = hitboxes_overlap(zone, (b,))
                zm = m_value((a,), (b,), grow_a=14.0)
                if zc and zm > 0.6:
                    bad[(ka, kb, "zone_false_hit")].append((round(zm, 3), a, b))
                if not zc and zm < -0.5:
                    bad[(ka, kb, "zone_miss")].append((round(zm, 3), a, b))
                if zc is False and code:
                    bad[(ka, kb, "zone_smaller_than_hit")].append((a, b))
                if not hitboxes_near((a,), (b,), 14.0) and zc:
                    bad[(ka, kb, "near_skip_zone")].append((a, b))
    print("pairs", sum(count.values()))
    for k, v in bad.items():
        print(k, len(v), v[0])
    if not bad:
        print("no disagreements")
    (out_dir("flow_collision") / "b4_shape_fuzz.json").write_text(
        json.dumps(
            {
                "pairs": sum(count.values()),
                "bad": {
                    "|".join(k): [str(x) for x in v[:3]] | {} if False else [str(x) for x in v[:3]]
                    for k, v in bad.items()
                },
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    ap = cli.parser(__doc__)
    ap.add_argument("n", type=int, nargs="?", default=250, help="shape pairs per kind pair")
    main(ap.parse_args().n)
