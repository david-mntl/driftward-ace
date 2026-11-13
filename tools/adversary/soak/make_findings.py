"""Assemble out/soak/FINDINGS.md facts (table + end-of-game numbers) from the run JSONs. Prints the dynamic parts."""

import json
from collections import Counter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: paths
from paths import OUT_DIR

OUT = OUT_DIR / "soak"
rows = []
for f in sorted((OUT / "runs").glob("*.json")):
    r = json.loads(f.read_text())
    kinds = Counter()
    for fd in r.get("findings", {}).values():
        kinds[fd["kind"]] += fd["count"]
    rows.append(r)
    print(
        f"| {r['bot']} | {r['seed']} | {r['mode']} | {r['ticks']} | {r['furthest_level']} | {r['result']} | {r['final_score']} | {r['lives_lost']} | {dict(kinds) or 'clean'} |"
    )
print()
for f in sorted(OUT.glob("tail_clock_*.json")):
    r = json.loads(f.read_text())
    print(
        "TAIL",
        f.name,
        {
            k: r[k]
            for k in (
                "seed",
                "ticks",
                "level8_start",
                "tail_waves",
                "tail_counts",
                "banner_ticks",
                "final_score",
                "final_meters",
                "level_rose_ticks",
            )
        },
    )
    print("  level8 playlist", r["level8_playlist"])
    print("  first tail wave", r["first_tail_wave"], "tail head", r["tail_sequence_head"][:12])
    print("  level starts", r["level_by_start"])
    print("  windows", [(w["t"], w["level"], w["score"]) for w in r["windows"][::4]])
    print("  findings", {k: v["count"] for k, v in r["findings"].items()}, "stats", r["stats"])
