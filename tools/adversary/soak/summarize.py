"""Aggregate out/soak/runs/*.json into a table and a findings digest.  usage: python summarize.py [--examples N]"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: paths
from paths import OUT_DIR

RUNS = OUT_DIR / "soak" / "runs"


def main():
    ap = argparse.ArgumentParser(description="Table and findings digest of out/soak/runs/*.json")
    ap.add_argument("--examples", type=int, default=1, help="examples to show per finding kind")
    nex = ap.parse_args().examples
    rows, agg = [], defaultdict(lambda: dict(count=0, runs=set(), examples=[]))
    for f in sorted(RUNS.glob("*.json")):
        r = json.loads(f.read_text())
        rows.append(r)
        for k, fd in r.get("findings", {}).items():
            a = agg[k]
            a["count"] += fd["count"]
            a["runs"].add(f.stem)
            if len(a["examples"]) < nex:
                a["examples"].append(fd["examples"][0])
    print("| bot | seed | mode | ticks | level | result | score | lives lost | secs |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| {r['bot']} | {r['seed']} | {r['mode']} | {r['ticks']} | {r['furthest_level']} | {r['result']} | {r['final_score']} | {r['lives_lost']} | {r['secs']} |"
        )
    print()
    for k, a in sorted(agg.items()):
        print(f"{k}: total={a['count']} runs={len(a['runs'])}")
        for e in a["examples"]:
            print("   ", json.dumps(e, default=str)[:700])


if __name__ == "__main__":
    main()
