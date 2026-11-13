"""Summarise a drive.js output: frame pacing, spikes, tick jitter, and what the spike frames did."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from perfdata import percentile as pct


def report(path):
    """Print the report for one drive.js output file."""
    d = json.loads(Path(path).read_text())
    rows = []
    for line in d["probe"]:
        t, iv, sl, ticks, tk, dr, fl, gcm, nd, cues, scr, can, parts, lu = line.split(",")
        rows.append(
            dict(
                t=float(t),
                iv=float(iv),
                sleep=float(sl),
                ticks=int(ticks),
                tick=float(tk),
                draw=float(dr),
                flip=float(fl),
                gc=float(gcm),
                nd=int(nd),
                cues=int(cues),
                scr=scr,
                can=float(can),
                parts=parts,
                lu=lu,
            )
        )
    rows = [r for r in rows if r["scr"] == "PL"]
    iv = [r["iv"] for r in rows][1:]
    raf = d["raf"][5:]
    secs = (rows[-1]["t"] - rows[0]["t"]) / 1000 if rows else 0
    work = [r["tick"] + r["draw"] + r["flip"] for r in rows]
    print(f"== {path.split('/')[-1]}  opts={d['meta']['opts']}  playing {secs:.0f}s  frames {len(rows)}")
    print(
        f"  frame interval ms: p50 {pct(iv, 0.5):.1f} p90 {pct(iv, 0.9):.1f} p99 {pct(iv, 0.99):.1f} max {max(iv):.1f}"
        f" | >25ms {sum(x > 25 for x in iv)}  >40ms {sum(x > 40 for x in iv)}  >70ms {sum(x > 70 for x in iv)}"
    )
    print(
        f"  rAF gaps ms:       p50 {pct(raf, 0.5):.1f} p99 {pct(raf, 0.99):.1f} max {max(raf):.1f} | >25ms {sum(x > 25 for x in raf)} >40ms {sum(x > 40 for x in raf)}"
    )
    print(
        f"  python work ms:    p50 {pct(work, 0.5):.1f} p99 {pct(work, 0.99):.1f} max {max(work):.1f}  (tick p50 {pct([r['tick'] for r in rows], 0.5):.1f}"
        f" draw p50 {pct([r['draw'] for r in rows], 0.5):.1f} flip p50 {pct([r['flip'] for r in rows], 0.5):.1f})"
    )
    print(
        f"  browser time (sleep) ms: p50 {pct([r['sleep'] for r in rows], 0.5):.1f} p99 {pct([r['sleep'] for r in rows], 0.99):.1f} max {max(r['sleep'] for r in rows):.1f}"
    )
    tc = {}
    for r in rows:
        tc[r["ticks"]] = tc.get(r["ticks"], 0) + 1
    print(
        f"  ticks per frame: {dict(sorted(tc.items()))}  ticks/s {sum(r['ticks'] for r in rows) / secs if secs else 0:.1f}"
    )
    cn = [r["can"] for r in rows]
    print(
        f"  canary ms: p50 {pct(cn, 0.5):.2f} p99 {pct(cn, 0.99):.2f} max {max(cn):.2f} | >3x median {sum(x > 3 * pct(cn, 0.5) for x in cn)}"
    )
    gcs = [r["gc"] for r in rows if r["gc"] > 0]
    print(f"  gc: frames with gc {len(gcs)}, max {max(gcs) if gcs else 0:.1f} ms, >5ms {sum(x > 5 for x in gcs)}")
    worst = sorted(range(1, len(rows)), key=lambda i: -rows[i]["iv"])[:10]
    for i in worst:
        r = rows[i]
        p = rows[i - 1]
        print(
            f"   spike {r['iv']:.0f}ms: prev frame tick {p['tick']:.1f} draw {p['draw']:.1f} flip {p['flip']:.1f} gc {p['gc']:.1f} canary {p['can']:.2f}/{r['can']:.2f}"
            f" | this sleep {r['sleep']:.1f} | nd {r['nd']} ticks {r['ticks']} cues {p['cues']} lu {p['lu']} [{p['parts']}]"
        )
    agg = {}
    for r in rows:
        for kv in r["parts"].split(";"):
            if "=" in kv:
                k, v = kv.split("=")
                agg.setdefault(k, []).append(float(v))
    print(
        "  parts p50/p99/max:",
        {k: (round(pct(v, 0.5), 1), round(pct(v, 0.99), 1), round(max(v), 1)) for k, v in agg.items()},
    )
    lu = [r for r in rows if r["lu"] == "1"]
    print(
        f"  level-up frames {len(lu)}, of which draw>20ms {sum(r['draw'] > 20 for r in lu)}; non-lu draw>20ms {sum(r['draw'] > 20 for r in rows if r['lu'] != '1')}"
    )
    if d.get("logs"):
        print("  logs:", d["logs"][:6])
    print("  audio:", d.get("audio"))


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("files", nargs="+", help="drive.js output files")
    for path in ap.parse_args().files:
        report(path)


if __name__ == "__main__":
    main()
