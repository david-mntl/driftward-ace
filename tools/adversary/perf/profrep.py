"""Top 15 functions by cumulative and own time per .prof file, core vs drawing split.

usage: python profrep.py DIR_WITH_PROF_FILES [--print]
"""

import pstats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: paths
import cli
from paths import GAME_DIR

GAME = f"{GAME_DIR}/"


def kind(fn):
    f = fn[0]
    if f.startswith(GAME):
        rel = f[len(GAME) :]
        if rel.startswith("core/"):
            return "core"
        if rel.startswith("ui/"):
            return "draw"
        if rel.startswith("app/"):
            return "app"
    return "lib"


def report(prof_dir, show):
    """Write top15.txt in `prof_dir` from its .prof files; print the text too when `show`."""
    out = []
    for p in sorted(prof_dir.glob("*.prof")):
        st = pstats.Stats(str(p))
        tot = st.total_tt
        own = {"core": 0.0, "draw": 0.0, "app": 0.0, "lib": 0.0}
        for fn, (_cc, _nc, tt, _ct, _callers) in st.stats.items():
            own[kind(fn)] += tt
        out.append(
            f"### {p.stem}: total {tot:.2f}s (profiled, inflated ~2-3x); own time core {own['core'] / tot:.0%} draw {own['draw'] / tot:.0%} app {own['app'] / tot:.0%} lib/C {own['lib'] / tot:.0%}"
        )
        for title, idx in (("cumulative", 3), ("own", 2)):
            rows = sorted(st.stats.items(), key=lambda kv: -kv[1][idx])
            rows = [
                r
                for r in rows
                if not r[0][0].endswith("soak.py")
                and "thread_time" not in r[0][2]
                and r[0][2] not in ("<module>",)
                and "frame_loop" not in r[0][2]
                and r[0][2] != "run"
            ][:15]
            out.append(f"{title} (calls, own s, cum s):")
            for fn, (_cc, nc, tt, ct, _) in rows:
                name = fn[0].replace(GAME, "") if fn[0].startswith(GAME) else fn[0].split("/")[-1]
                out.append(f"  {kind(fn):4} {name}:{fn[1]}:{fn[2]}  {nc}  {tt:.3f}  {ct:.3f}")
    text = "\n".join(out)
    (prof_dir / "top15.txt").write_text(text)
    print(text if show else f"wrote {prof_dir / 'top15.txt'}")


def main():
    ap = cli.parser(__doc__)
    ap.add_argument("prof_dir", type=Path)
    ap.add_argument("--print", dest="show", action="store_true", help="print the report instead of its file name")
    a = ap.parse_args()
    report(a.prof_dir, a.show)


if __name__ == "__main__":
    main()
