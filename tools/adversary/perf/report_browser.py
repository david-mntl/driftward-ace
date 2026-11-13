"""Browser run report: frame interval stats and stutters per level and per wave, 10 worst frames.

Usage: python report_browser.py out1.json [out2.json ...]
Record fields: t,iv,sleep,ticks,tick,draw,flip,gc,nd,cues,scr,canary,parts,lu,ctx(level|wave|seq|rest|tail)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
from perfdata import percentile as pct
from collections import defaultdict


def report(path):
    """Print the report for one drive.js output file."""
    d = json.loads(Path(path).read_text())
    rows = []
    for line in d["probe"]:
        f = line.split(",")
        if len(f) < 15:
            continue
        lvl, wid, seq, rest, tail = f[14].split("|")
        rows.append(
            dict(
                t=float(f[0]),
                iv=float(f[1]),
                ticks=int(f[3]),
                tick=float(f[4]),
                draw=float(f[5]),
                flip=float(f[6]),
                gc=float(f[7]),
                nd=int(f[8]),
                scr=f[10],
                can=float(f[11]),
                parts=f[12],
                lu=f[13],
                lvl=int(lvl),
                wave=wid,
                seq=int(seq),
                rest=rest == "1",
                tail=tail == "1",
            )
        )
    rows = [r for r in rows if r["scr"] == "PL" and r["lvl"] > 0][3:]
    print(
        f"== {path.split('/')[-1]}: {len(rows)} playing frames over {(rows[-1]['t'] - rows[0]['t']) / 1000:.0f} s"
        if rows
        else f"== {path}: no frames"
    )
    if not rows:
        return

    def block(name, rs):
        iv = [r["iv"] for r in rs]
        secs = (rs[-1]["t"] - rs[0]["t"]) / 1000 or 1
        work = [r["tick"] + r["draw"] for r in rs]
        cn = pct([r["can"] for r in rs], 0.5)
        ratio = pct(work, 0.5) / max(cn, 0.1)
        print(
            f"  {name:28} n={len(rs):5} fps {len(rs) / secs:5.1f} iv p50 {pct(iv, 0.5):6.1f} p95 {pct(iv, 0.95):6.1f} p99 {pct(iv, 0.99):6.1f} max {max(iv):6.0f} "
            f">33ms {sum(x > 33 for x in iv):4} >50ms {sum(x > 50 for x in iv):4} | py work p50 {pct(work, 0.5):5.1f} p95 {pct(work, 0.95):5.1f} | canary p50 {cn:5.1f} work p50 in canary units {ratio:5.1f} | peak nd {max(r['nd'] for r in rs):2} ticks/frame>1 {sum(r['ticks'] > 1 for r in rs)}"
        )

    by_level = defaultdict(list)
    by_wave = defaultdict(list)
    for r in rows:
        by_level[("8 tail" if r["tail"] else str(r["lvl"]))].append(r)
        if not r["rest"]:
            by_wave[(r["lvl"], r["wave"])].append(r)
    for k in sorted(by_level):
        block(f"level {k}", by_level[k])
    for k in sorted(by_wave):
        block(f"L{k[0]} {k[1]}", by_wave[k])
    worst = sorted(range(1, len(rows)), key=lambda i: -rows[i]["iv"])[:10]
    print("  10 worst frames (interval ms | level wave | prev frame tick/draw/gc/canary | nd | ticks | parts of prev):")
    for i in worst:
        r, p = rows[i], rows[i - 1]
        print(
            f"   {r['iv']:.0f} | L{r['lvl']} {r['wave']}{' rest' if r['rest'] else ''} | {p['tick']:.0f}/{p['draw']:.0f}/{p['gc']:.0f}/{p['can']:.1f} | {r['nd']} | {r['ticks']} | {p['parts'][:70]}"
        )


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("files", nargs="+", help="drive.js output files")
    for path in ap.parse_args().files:
        report(path)


if __name__ == "__main__":
    main()
