"""Proves the b1 oracle is sensitive: inject known bugs into core.collision, expect findings."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import paths  # noqa: F401  (puts game/ on sys.path)
import b1_collision_diff
import core.collision as collision
from core.drifters.base import DrifterType as T
from flowlib import patched

# (type, variant, level, seed, samples per tick, tick stride): one shape family each
COMBOS = [
    (T.METEORITE, "small", 1, None, 2, 25),
    (T.SATELLITE, "flat", 1, None, 2, 25),
    (T.CHAIN_LIGHTNING, "pair_flat", 1, None, 2, 25),
    (T.FLOATING_ISLAND, "triangle", 1, None, 2, 25),
]


def count_findings():
    """Findings per drifter type over COMBOS."""
    return {combo[0].value: len(b1_collision_diff.run_combo(combo)[4]) for combo in COMBOS}


def circle_box_with_radius_offset(offset):
    """A circle-box overlap test whose circle is `offset` px bigger (or smaller, when negative) than the real one."""
    return lambda circle, box: collision._point_box_dist_sq((circle.cx, circle.cy), box) < (circle.r + offset) ** 2


def main():
    print("clean", count_findings())
    with patched(collision, "_circle_box_overlap", circle_box_with_radius_offset(-1.5)):
        print("circle-box r-1.5", count_findings())
    with patched(collision, "_circle_box_overlap", circle_box_with_radius_offset(+1.5)):
        print("circle-box r+1.5", count_findings())


if __name__ == "__main__":
    main()
