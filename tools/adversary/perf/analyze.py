"""Tables from a soak run: per level, per wave, worst frames, drift slope, marginal cost per type, leaks.

Usage: python analyze.py LABEL [--ckpt]   (reads out/perf/soak_LABEL[_ckpt].npz and _meta.json)
Writes out/perf/report_LABEL.md and prints a short summary.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from perfdata import FRAMES_PER_MINUTE, PERF_DIR, load_run


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("label")
    ap.add_argument("--ckpt", action="store_true", help="read the checkpoint file instead of the final one")
    a = ap.parse_args()
    analyze(a.label, "_ckpt" if a.ckpt else "")


def analyze(label, suffix):
    """Write out/perf/report_<label><suffix>.md from the run soak.py saved under that label."""
    d, doc = load_run(label, suffix)
    meta, samples = doc["meta"], doc["samples"]
    wave_names = {v: k for k, v in meta["wave_ids"].items()}
    n = len(d["tick"])
    fl = d["flags"]
    playing = (fl & 8) > 0
    resting = (fl & 1) > 0
    cost = d["tick"] + d["draw"]
    # speed factor from the canary: rolling median over 601 frames, referenced to the quiet 5th percentile
    can = d["canary"].astype(float)
    k = 601
    pad = np.pad(can, (k // 2, k // 2), mode="edge")
    roll = np.median(np.lib.stride_tricks.sliding_window_view(pad, k)[::1], axis=1) if n < 120000 else can
    ref = np.percentile(roll, 5)
    speed = roll / ref  # >1 means the machine was slower than at its quiet moments
    ncost = cost / speed

    def pct(x, p):
        return float(np.percentile(x, p)) if len(x) else float("nan")

    def row(mask):
        x, xn = cost[mask], ncost[mask]
        return dict(
            n=int(mask.sum()),
            p50=pct(x, 50),
            p95=pct(x, 95),
            p99=pct(x, 99),
            mx=float(x.max()) if len(x) else 0,
            p95n=pct(xn, 95),
            peak=int(d["nd"][mask].max()) if len(x) else 0,
            tick50=pct(d["tick"][mask], 50),
            draw50=pct(d["draw"][mask], 50),
            speed=float(np.median(speed[mask])) if len(x) else 0,
            canmed=float(np.median(can[mask])) if len(x) else 1,
        )

    lines = []
    P = lines.append
    P(f"# Soak report: {label}{suffix}\n")
    P(
        f"frames {n}, playing {int(playing.sum())}, hits absorbed {meta['hits']}, canary quiet ref {ref:.2f} ms "
        f"(median {np.median(can):.2f}); speed factor median {np.median(speed):.2f}, p95 {np.percentile(speed, 95):.2f}\n"
    )
    P("cost = tick ms + draw ms, raw. p95n = p95 of cost corrected to the quiet-machine canary speed.\n")
    P("## Per level (all playing frames, rest gaps included)\n")
    P(
        "| level | frames | p50 | p95 | p99 | max | p95n | p50 in canary units | peak drifters | tick p50 | draw p50 | machine speed x |"
    )
    P("|---|---|---|---|---|---|---|---|---|---|---|---|")
    tail = d["tail"] > 0
    groups = []
    for lv in range(1, 9):
        m = playing & (d["level"] == lv) & ~tail
        if m.any():
            groups.append((str(lv), m))
    if (playing & tail).any():
        groups.append(("8 endless tail", playing & tail))
    for name, m in groups:
        r = row(m)
        P(
            f"| {name} | {r['n']} | {r['p50']:.1f} | {r['p95']:.1f} | {r['p99']:.1f} | {r['mx']:.1f} | {r['p95n']:.1f} | {r['p50'] / r['canmed']:.1f} | {r['peak']} | {r['tick50']:.1f} | {r['draw50']:.1f} | {r['speed']:.1f} |"
        )
    P("\n## Per wave (active frames only, all occurrences; sorted by p95)\n")
    P("| wave | level(s) | frames | p50 | p95 | p99 | max | p95n | peak drifters | flag p95>8 (raw / corrected) |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    wrows = []
    for wid, name in wave_names.items():
        m = playing & ~resting & (d["wave"] == wid)
        if not m.any():
            continue
        lv = sorted(set(d["level"][m].tolist()))
        r = row(m)
        wrows.append((r["p95"], name, lv, r))
    for _, name, lv, r in sorted(wrows, key=lambda t: -t[0]):
        P(
            f"| {name} | {','.join(map(str, lv))} | {r['n']} | {r['p50']:.1f} | {r['p95']:.1f} | {r['p99']:.1f} | {r['mx']:.1f} | {r['p95n']:.1f} | {r['peak']} | "
            f"{'YES' if r['p95'] > 8 else 'no'} / {'YES' if r['p95n'] > 8 else 'no'} |"
        )
    # worst frames
    P("\n## Worst 15 frames by cost\n")
    idx = np.argsort(-np.where(playing, cost, 0))[:15]
    pn = [p for p in meta["part_names"] if not p.startswith("d:")]
    P("| frame | level | wave | rest | drifters | tick | draw | gc ms | canary | lvl-up | top parts (ms) |")
    P("|---|---|---|---|---|---|---|---|---|---|---|")
    for i in idx:
        parts = sorted(
            ((float(d["p:" + p][i]), p) for p in pn if p not in ("bg_paint", "bg_river", "bg_swirl", "bg_planets")),
            reverse=True,
        )[:3]
        P(
            f"| {i} | {d['level'][i]}{'t' if tail[i] else ''} | {wave_names[int(d['wave'][i])]} | {int(resting[i])} | {d['nd'][i]} | {d['tick'][i]:.1f} | {d['draw'][i]:.1f} | "
            f"{d['gc'][i]:.1f} | {can[i]:.1f} | {int((fl[i] & 2) > 0)} | {', '.join(f'{p}={v:.1f}' for v, p in parts)} |"
        )
    # mean draw split
    P("\n## Mean ms per frame by part, per level (playing frames)\n")
    cols = [
        "bg",
        "bg_paint",
        "bg_river",
        "star",
        "drift",
        "ship",
        "pop",
        "ring",
        "hud",
        "lub",
        "luf",
        "step_flow",
        "add_drifters",
    ]
    P("| level | " + " | ".join(cols) + " |")
    P("|---|" + "---|" * len(cols))
    for name, m in groups:
        P(f"| {name} | " + " | ".join(f"{d['p:' + c][m].mean():.2f}" for c in cols) + " |")
    P("\n## Drifter draw cost by type (mean ms per frame in which it is on screen / mean count)\n")
    P("| type | frames present | mean draw ms/frame when present | mean count when present |")
    P("|---|---|---|---|")
    for t in meta["type_names"]:
        cnt = d["n:" + t]
        m = playing & (cnt > 0)
        if m.any():
            P(f"| {t} | {int(m.sum())} | {d['p:d:' + t][m].mean():.2f} | {cnt[m].mean():.1f} |")
    # marginal cost per drifter by type: tick and draw regression on counts
    m = playing & ~resting
    X = np.column_stack([np.ones(m.sum())] + [d["n:" + t][m] for t in meta["type_names"]])
    P("\n## Marginal cost per drifter on screen (OLS on corrected ms; const = empty field)\n")
    P("| part | const | " + " | ".join(meta["type_names"]) + " |")
    P("|---|---|" + "---|" * len(meta["type_names"]))
    for nm, y in (("tick", d["tick"] / speed), ("draw", d["draw"] / speed)):
        coef = np.linalg.lstsq(X, y[m], rcond=None)[0]
        P(f"| {nm} | {coef[0]:.2f} | " + " | ".join(f"{c:.3f}" for c in coef[1:]) + " |")
    # drift over time in the tail
    slope = None
    if tail.any():
        mt = playing & tail & ~resting
        t_min = (np.arange(n)[mt] - np.arange(n)[mt][0]) / FRAMES_PER_MINUTE
        Y = ncost[mt]
        Xt = np.column_stack(
            [np.ones(mt.sum()), d["nd"][mt], d["n:" + "ufo"][mt] if "ufo" in meta["type_names"] else 0, t_min]
        )
        coef = np.linalg.lstsq(Xt, Y, rcond=None)[0]
        coef_raw = np.linalg.lstsq(Xt, cost[mt], rcond=None)[0]
        # per-minute bins
        P("\n## Endless tail trend\n")
        P(
            f"OLS cost ~ const + drifters + ufo_count + minutes: corrected slope {coef[3]:+.3f} ms/min, raw slope {coef_raw[3]:+.3f} ms/min, "
            f"drifter coefficient {coef[1]:.3f} ms each ({mt.sum()} frames, {t_min.max():.1f} min)\n"
        )
        P(
            "| tail minute bin (5 min) | frames | median cost raw | median corrected | p95 corrected | mean drifters | median machine speed x |"
        )
        P("|---|---|---|---|---|---|---|")
        for b in range(int(t_min.max() // 5) + 1):
            mb = (t_min >= b * 5) & (t_min < b * 5 + 5)
            if mb.sum() > 100:
                P(
                    f"| {b * 5}-{b * 5 + 5} | {mb.sum()} | {np.median(cost[mt][mb]):.1f} | {np.median(Y[mb]):.1f} | {np.percentile(Y[mb], 95):.1f} | {d['nd'][mt][mb].mean():.1f} | {np.median(speed[mt][mb]):.1f} |"
                )
        # wave-matched early vs late
        P("\nSame wave, early vs late tail instance (median corrected cost, frames with that wave active):\n")
        P("| wave | instances | first | last | delta |")
        P("|---|---|---|---|---|")
        seqs = d["seq"]
        for wid, name in wave_names.items():
            mw = mt & (d["wave"] == wid)
            if not mw.any():
                continue
            useq = sorted(set(seqs[mw].tolist()))
            if len(useq) >= 2:
                a = np.median(ncost[mw & (seqs == useq[0])])
                b = np.median(ncost[mw & (seqs == useq[-1])])
                P(f"| {name} | {len(useq)} | {a:.2f} | {b:.2f} | {b - a:+.2f} |")
        slope = float(coef[3])
    # leaks
    P("\n## Memory samples\n")
    P(
        "| frame | tag | level | tail | RSS MB | RSS minus own arrays MB | alloc blocks | gc objects | cache items total |"
    )
    P("|---|---|---|---|---|---|---|---|---|")
    keep = [s for s in samples if s["tag"] or s["frame"] % 6000 == 0]
    for s in keep:
        P(
            f"| {s['frame']} | {s['tag']} | {s['level']} | {int(s['tail'])} | {s['rss_kb'] / 1024:.0f} | {(s['rss_kb'] - s['arrays_kb']) / 1024:.0f} | {s['blocks']} | {s.get('gc_objects', '')} | {sum(s['census'].values())} |"
        )
    if len(samples) > 3:
        a, b = samples[len(samples) // 4], samples[-1]
        grow = sorted(((b["census"].get(k, 0) - a["census"].get(k, 0), k) for k in b["census"]), reverse=True)[:8]
        P(
            f"\nBiggest container growth between frame {a['frame']} and {b['frame']}: "
            + "; ".join(f"{k} {g:+d}" for g, k in grow if g)
        )
        fr_ = np.array([s["frame"] for s in samples], float) / FRAMES_PER_MINUTE
        rs = np.array([(s["rss_kb"] - s["arrays_kb"]) / 1024 for s in samples])
        bl = np.array([s["blocks"] for s in samples], float)
        tl = np.array([bool(s["tail"]) for s in samples])
        for nm, arr in (("RSS minus arrays MB", rs), ("alloc blocks", bl)):
            P(
                f"- slope of {nm} over whole run: {np.polyfit(fr_, arr, 1)[0]:+.2f} per game-minute"
                + (
                    f"; in the tail only: {np.polyfit(fr_[tl], arr[tl], 1)[0]:+.2f} per game-minute"
                    if tl.sum() > 4
                    else ""
                )
            )
    # GC
    gce = doc["gc"]
    if gce:
        g2 = [e for e in gce if e[1] == 2]
        P(
            f"\nGC: {len(gce)} collections, gen2 {len(g2)}, max gen2 {max([e[2] for e in g2], default=0):.1f} ms, max any {max(e[2] for e in gce):.1f} ms"
        )
    (PERF_DIR / f"report_{label}{suffix}.md").write_text("\n".join(lines))
    print("wrote", PERF_DIR / f"report_{label}{suffix}.md", "tail slope corrected ms/min:", slope)


if __name__ == "__main__":
    main()
