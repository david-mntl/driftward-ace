"""wave_check: tests a wave against the GDD's rules by running the game's own physics headless.

    python tools/wave_check/wave_check.py --wave game/waves/l1_a.json
    python tools/wave_check/wave_check.py --changed               # only waves git sees as changed
    python tools/wave_check/wave_check.py --changed --base REF    # only waves changed since REF
    python tools/wave_check/wave_check.py --all

Part 1: placement sanity, telegraph, coin near a hazard, seam. The bot checks (zero-hit path,
gap) are part 2 and show as SKIP, so a pass here is not the full pass yet.
Reads the game, never changes it. The Director owns `config.json`. Exit code: 0 all passed,
1 a check failed, 2 a usage, config or game file error.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_DIR: Path = Path(__file__).resolve().parent
ROOT: Path = TOOL_DIR.parents[1]
sys.path.insert(0, str(ROOT / "game"))
sys.path.insert(0, str(TOOL_DIR))

import store
from app import tuning as tuning_module
from app.waves import PLAYLIST_FILE, WAVES_DIR
from checks import Context, Result, run_checks, ships_at_spots
from core.drifters.tuning import DrifterTuning
from core.ship import spawn
from core.wave_files import _build_wave
from core.waves import Wave
from settings import Config, load_config
from tracks import build_tracks

PART_TWO: str = (
    "bot checks (zero-hit path, gap) are part 2: not run, so this is not the full pass"
)


def main(argv: list[str] | None = None) -> int:
    args: argparse.Namespace = _parser().parse_args(argv)
    if args.base and not args.changed:
        print("wave_check: --base only works with --changed", file=sys.stderr)
        return 2
    try:
        config: Config = load_config(
            Path(args.config) if args.config else TOOL_DIR / "config.json"
        )
        tuning: DrifterTuning = tuning_module.load_tuning()
        paths: list[Path] = _pick(args)
    except (ValueError, OSError) as err:
        print(f"wave_check: {err}", file=sys.stderr)
        return 2
    if args.changed and not paths:
        print(json.dumps([]) if args.json else "no wave changed, nothing to check")
        return 0
    levels: tuple[int, ...] = tuple(args.level) if args.level else config.levels
    passes: dict[str, str] = store.read()
    reports: list[dict[str, Any]] = []
    for path in paths:
        if path.stem in config.skip:
            reports.append(
                {"wave": path.stem, "status": "SKIPPED", "why": "in config skip list"}
            )
            continue
        reports.extend(_check_wave(path, levels, config, tuning, passes, args))
    if not args.no_record:
        store.write(passes)
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        _print(reports)
    return 1 if any(r["status"] == "FAIL" for r in reports) else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wave_check", description=__doc__.split("\n\n")[0]
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--wave", action="append", metavar="FILE", help="check this wave file"
    )
    mode.add_argument(
        "--changed",
        action="store_true",
        help="only the waves git sees as changed or new (always run, nothing else is)",
    )
    mode.add_argument(
        "--all", action="store_true", help="every wave, passes that are fresh skip"
    )
    parser.add_argument(
        "--level", action="append", type=int, help="level to test (default: config)"
    )
    parser.add_argument(
        "--base",
        metavar="REF",
        help="with --changed: waves changed since REF (git diff REF...HEAD), not in the working tree",
    )
    parser.add_argument("--force", action="store_true", help="ignore remembered passes")
    parser.add_argument(
        "--no-record", action="store_true", help="do not write passes.json"
    )
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--config", help="config file (default: next to this script)")
    return parser


def _pick(args: argparse.Namespace) -> list[Path]:
    """The wave files to check, in name order."""
    if args.wave:
        missing: list[str] = [name for name in args.wave if not Path(name).is_file()]
        if missing:
            raise ValueError(f"no such wave file: {', '.join(missing)}")
        return [Path(name) for name in args.wave]
    every: list[Path] = sorted(
        p for p in WAVES_DIR.glob("*.json") if p.name != PLAYLIST_FILE
    )
    if args.changed:
        changed: set[Path] = _changed_waves(args.base)
        return [p for p in every if p.resolve() in changed]
    return every


def _git_lines(*git_args: str) -> list[str]:
    try:
        out: str = subprocess.run(
            ["git", "-C", str(ROOT), *git_args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as err:
        detail: str = getattr(err, "stderr", "") or str(err)
        raise ValueError(f"cannot read the changed waves from git: {detail.strip()}")
    return [line for line in out.splitlines() if line]


def _changed_waves(base: str | None) -> set[Path]:
    """The wave files git sees as changed or new, as absolute paths.

    Without `base`: the working tree against HEAD, new files included. With `base`: what changed
    since that ref. A deleted file is not listed. Raises ValueError if git cannot answer, so a
    broken git never reads as "nothing changed".
    """
    folder: str = WAVES_DIR.resolve().relative_to(ROOT).as_posix()
    if base:
        names: list[str] = _git_lines(
            "diff", "--name-only", "--diff-filter=d", f"{base}...HEAD", "--", folder
        )
    else:
        names = _git_lines(
            "diff", "--name-only", "--diff-filter=d", "HEAD", "--", folder
        )
        names += _git_lines("ls-files", "--others", "--exclude-standard", "--", folder)
    return {(ROOT / name).resolve() for name in names if name.endswith(".json")}


def _check_wave(
    path: Path,
    levels: tuple[int, ...],
    config: Config,
    tuning: DrifterTuning,
    passes: dict[str, str],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    """Check one wave file at each level. One report entry per level."""
    wave_id: str = path.stem
    try:
        document: Any = json.loads(path.read_text(encoding="utf-8"))
        wave: Wave = _build_wave(wave_id, document, tuning)
    except (ValueError, OSError) as err:
        return [_loader_failure(wave_id, err)]
    reports: list[dict[str, Any]] = []
    for level in levels:
        print_: str = store.fingerprint(document, config)
        if not (args.force or args.wave or args.changed) and store.is_fresh(
            passes, wave_id, level, print_
        ):
            reports.append(
                {"wave": wave_id, "level": level, "status": "PASS", "remembered": True}
            )
            continue
        results: list[Result] = _run(wave, level, config, tuning)
        ok: bool = all(r.status != "FAIL" for r in results)
        store.remember(passes, wave_id, level, print_, ok)
        reports.append(
            {
                "wave": wave_id,
                "level": level,
                "status": "PASS" if ok else "FAIL",
                "remembered": False,
                "checks": [_result_dict(r) for r in results],
            }
        )
    return reports


def _run(wave: Wave, level: int, config: Config, tuning: DrifterTuning) -> list[Result]:
    try:
        tracks = build_tracks(wave, level, tuning, spawn(), config.track_ticks_max)
    except ValueError as err:
        failed = Result("spawn", "every placement spawns", "FAIL", note=str(err))
        return [failed]
    ctx = Context(wave, level, tuning, config, tracks, ships_at_spots(config))
    return run_checks(ctx)


def _loader_failure(wave_id: str, err: Exception) -> dict[str, Any]:
    check: dict[str, Any] = {
        "name": "loader",
        "title": "the game's loader accepts the wave",
        "status": "FAIL",
        "note": str(err),
        "findings": [],
    }
    return {
        "wave": wave_id,
        "level": None,
        "status": "FAIL",
        "remembered": False,
        "checks": [check],
    }


def _result_dict(result: Result) -> dict[str, Any]:
    return {
        "name": result.name,
        "title": result.title,
        "status": result.status,
        "note": result.note,
        "findings": [
            {
                "message": f.message,
                "tick": f.tick,
                "px": f.px,
                "pos": list(f.pos) if f.pos else None,
                "drifters": list(f.drifters),
            }
            for f in result.findings
        ],
    }


def _print(reports: list[dict[str, Any]]) -> None:
    passed: int = sum(1 for r in reports if r["status"] == "PASS")
    failed: int = sum(1 for r in reports if r["status"] == "FAIL")
    for report in reports:
        level: str = f"  level {report['level']}" if report.get("level") else ""
        if report["status"] == "SKIPPED":
            print(f"wave {report['wave']}  skipped: {report['why']}")
            continue
        if report.get("remembered"):
            print(
                f"wave {report['wave']}{level}  PASS (unchanged since the last pass, not run)"
            )
            continue
        print(f"wave {report['wave']}{level}  {report['status']}")
        for check in report["checks"]:
            tail: str = f"  ({check['note']})" if check["note"] else ""
            print(f"  {check['status']:<4} {check['title']}{tail}")
            for finding in check["findings"]:
                where: list[str] = []
                if finding["tick"] is not None:
                    where.append(f"tick {finding['tick']}")
                if finding["px"] is not None:
                    where.append(f"{finding['px']:g} px")
                if finding["pos"]:
                    where.append(
                        f"at ({finding['pos'][0]:.0f}, {finding['pos'][1]:.0f})"
                    )
                print(f"       - {finding['message']}  [{', '.join(where)}]")
    print(f"\n{passed} passed, {failed} failed")
    if passed and not failed:
        print(PART_TWO)


if __name__ == "__main__":
    sys.exit(main())
