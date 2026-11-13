"""Endless-tail trend: does tick (and draw) cost grow with time at a steady drifter count?

Usage: python tail_trend.py LABEL [LABEL...]   Writes out/perf/tail_trend.md
"""

import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from perfdata import FRAMES_PER_MINUTE, PERF_DIR, load_run


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("labels", nargs="+", help="soak run labels")
    trend(ap.parse_args().labels)


def trend(labels):
    """Write out/perf/tail_trend.md for the given soak runs."""
    lines = []
    P = lines.append
    for lab in labels:
        d, doc = load_run(lab)
        meta, samples = doc["meta"], doc["samples"]
        names = {v: k for k, v in meta["wave_ids"].items()}
        fl = d["flags"]
        mt = ((fl & 8) > 0) & ((fl & 1) == 0) & (d["tail"] > 0)
        n = int(mt.sum())
        if n < 600:
            P(f"## {lab}: only {n} active tail frames, skipped\n")
            continue
        idx = np.where(mt)[0]
        minutes = (idx - idx[0]) / FRAMES_PER_MINUTE
        can = d["canary"].astype(float)
        k = 301
        roll = np.median(
            np.lib.stride_tricks.sliding_window_view(np.pad(can, (k // 2, k // 2), mode="edge"), k), axis=1
        )
        speed = (roll / np.percentile(roll, 5))[idx]
        drawn = d["draw"][idx] > 0
        P(f"## {lab}: {n} active tail frames, {minutes.max():.1f} min of tail, drawn frames {int(drawn.sum())}\n")
        for nm, y, sel in (
            ("tick", d["tick"][idx], np.ones(n, bool)),
            ("draw", d["draw"][idx], drawn),
            ("tick+draw", d["tick"][idx] + d["draw"][idx], drawn),
        ):
            if sel.sum() < 600:
                continue
            yc = y / speed
            ndv = d["nd"][idx]
            X = np.column_stack([np.ones(n), ndv, d["n:floating_island"][idx], minutes])[sel]
            co = np.linalg.lstsq(X, yc[sel], rcond=None)[0]
            co_raw = np.linalg.lstsq(X, y[sel], rcond=None)[0]
            P(
                f"- {nm}: OLS on (const, drifters, islands, minutes): corrected slope {co[3]:+.3f} ms/min; raw {co_raw[3]:+.3f} ms/min; "
                f"drifter {co[1]:.3f} ms each"
            )
        P(
            "\n| tail minutes | frames | tick p50 (corr) | tick p95 (corr) | draw p50 (raw, drawn only) | mean drifters | machine speed x |"
        )
        P("|---|---|---|---|---|---|---|")
        edges = np.linspace(0, minutes.max() + 1e-6, 6)
        for a, b in pairwise(edges):
            mb = (minutes >= a) & (minutes < b)
            if mb.sum() < 50:
                continue
            dr = mb & drawn
            P(
                f"| {a:.1f}-{b:.1f} | {mb.sum()} | {np.median(d['tick'][idx][mb] / speed[mb]):.2f} | {np.percentile(d['tick'][idx][mb] / speed[mb], 95):.2f} | "
                f"{np.median(d['draw'][idx][dr]) if dr.sum() else float('nan'):.2f} | {d['nd'][idx][mb].mean():.1f} | {speed[mb].mean():.2f} |"
            )
        P("\nSame wave id, first vs last instance in the tail (median tick ms, corrected):\n")
        P("| wave | instances | first | last | delta |\n|---|---|---|---|---|")
        seq = d["seq"][idx]
        for wid, nm in names.items():
            mw = d["wave"][idx] == wid
            useq = sorted(set(seq[mw].tolist()))
            if len(useq) >= 2:
                a = np.median((d["tick"][idx] / speed)[mw & (seq == useq[0])])
                b = np.median((d["tick"][idx] / speed)[mw & (seq == useq[-1])])
                P(f"| {nm} | {len(useq)} | {a:.2f} | {b:.2f} | {b - a:+.2f} |")
        if samples:
            P(
                "\nMemory samples (RSS minus own recording arrays):\n\n| frame | tail min | RSS MB | minus arrays MB | alloc blocks | gc objects | container items |\n|---|---|---|---|---|---|---|"
            )
            t0 = meta["tail_start_frame"] or 0
            for s in samples:
                if s["tag"] in ("tail_start", "end") or s["frame"] % 3000 == 0:
                    P(
                        f"| {s['frame']} | {(s['frame'] - t0) / FRAMES_PER_MINUTE:.1f} | {s['rss_kb'] / 1024:.1f} | {(s['rss_kb'] - s['arrays_kb']) / 1024:.1f} | {s['blocks']} | {s.get('gc_objects', '')} | {sum(s['census'].values())} |"
                    )
            sm = [s for s in samples if s["frame"] >= t0]
            if len(sm) > 4:
                fm = np.array([s["frame"] for s in sm]) / FRAMES_PER_MINUTE
                for nm, arr in (
                    ("RSS minus arrays MB", [(s["rss_kb"] - s["arrays_kb"]) / 1024 for s in sm]),
                    ("alloc blocks", [s["blocks"] for s in sm]),
                    ("container items", [sum(s["census"].values()) for s in sm]),
                ):
                    P(
                        f"\n- slope of {nm} in the tail: {np.polyfit(fm, np.array(arr, float), 1)[0]:+.2f} per game-minute"
                    )
                a, b = sm[0], sm[-1]
                grow = sorted(
                    ((b["census"].get(kk, 0) - a["census"].get(kk, 0), kk) for kk in b["census"]), reverse=True
                )[:6]
                h = sm[len(sm) // 2]
                grow2 = sorted(
                    ((b["census"].get(kk, 0) - h["census"].get(kk, 0), kk) for kk in b["census"]), reverse=True
                )[:6]
                P(
                    f"- container growth in the second half (frames {h['frame']}..{b['frame']}): "
                    + ("; ".join(f"{kk} {g:+d}" for g, kk in grow2 if g) or "none")
                )
                P("- biggest container growth, whole tail: " + "; ".join(f"{kk} {g:+d}" for g, kk in grow if g))
        P("")
    (PERF_DIR / "tail_trend.md").write_text("\n".join(lines))
    print("wrote tail_trend.md")


if __name__ == "__main__":
    main()
