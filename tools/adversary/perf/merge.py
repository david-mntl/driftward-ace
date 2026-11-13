"""Merge several soak runs into one label so analyze.py can tabulate them together.

usage: python merge.py OUT_LABEL LABEL1 LABEL2 ...   (wave ids are remapped by name, seq made unique)
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from perfdata import PERF_DIR, load_run

SEQ_GAP = 1000  # wave sequence numbers of the next run start this far past the last one


def merge(out_label, labels):
    """Write soak_<out_label>.npz and its metadata from the runs `labels`, one after the other."""
    names: dict[str, int] = {}
    arrays: dict[str, list] = {}
    first_meta = None
    seq_offset = 0
    hits = 0
    for label in labels:
        data, doc = load_run(label)
        meta = doc["meta"]
        by_id = {v: k for k, v in meta["wave_ids"].items()}
        data["wave"] = np.array([names.setdefault(by_id[int(w)], len(names)) for w in data["wave"]], dtype=np.int32)
        data["seq"] = np.where(data["seq"] >= 0, data["seq"] + seq_offset, data["seq"]).astype(np.int32)
        seq_offset = int(data["seq"].max()) + SEQ_GAP
        hits += meta["hits"]
        for key, values in data.items():
            arrays.setdefault(key, []).append(values)
        first_meta = first_meta or meta
    np.savez_compressed(PERF_DIR / f"soak_{out_label}.npz", **{k: np.concatenate(v) for k, v in arrays.items()})
    merged = dict(
        first_meta, wave_ids=names, hits=hits, label=out_label, frames=int(sum(len(v) for v in arrays["tick"]))
    )
    (PERF_DIR / f"soak_{out_label}_meta.json").write_text(json.dumps({"meta": merged, "samples": [], "gc": []}))
    print("merged", labels, "->", out_label, merged["frames"], "frames")


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("out_label")
    ap.add_argument("labels", nargs="+")
    a = ap.parse_args()
    merge(a.out_label, a.labels)


if __name__ == "__main__":
    main()
