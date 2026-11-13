"""Reading what soak.py wrote, and the few numbers the perf reports share."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: paths
from paths import OUT_DIR

PERF_DIR = OUT_DIR / "perf"
FRAMES_PER_MINUTE = 3600  # soak.py plays one tick per frame at 60 frames a second


def load_run(label, suffix=""):
    """The per-frame arrays and the metadata of soak run `label`.

    Returns (arrays, doc). `arrays` is a dict of numpy arrays from soak_<label><suffix>.npz. `doc` is the
    JSON next to it: {"meta": ..., "samples": ..., "gc": ...}.
    """
    arrays = dict(np.load(PERF_DIR / f"soak_{label}{suffix}.npz"))
    doc = json.loads((PERF_DIR / f"soak_{label}{suffix}_meta.json").read_text())
    return arrays, doc


def percentile(values, fraction):
    """The `fraction` (0 to 1) quantile of a list by rank, or 0.0 for an empty list."""
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * fraction))] if ordered else 0.0
