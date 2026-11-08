#!/usr/bin/env python3
"""Check that a pull request that changes the shipped game also raises the game's version.

The version is the one line in game/VERSION: MAJOR.MINOR.PATCH, such as 1.0.0.
Shipped files are what players get: every file under game/ that pygbag packs
(the excludes in pygbag.ini leave out tests, scripts and dev files), plus
pygbag.ini and web/, which shape the build.

Rules:
- game/VERSION must always hold a valid version.
- The version must never go down.
- If a shipped file changed, the version must go up, unless --skip is given
  (the pull request carries the `no-version-bump` label).

Run from the repo root, with the base branch fetched:

    python .github/scripts/check_version_bump.py --base origin/main [--skip]

Exit codes: 0 pass, 1 the version needs a change, 2 an input is missing or unreadable.
Errors are printed as GitHub Actions annotations, so they show on the PR.
"""

import argparse
import configparser
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

from check_release_package import DEFAULT_INI, load_excludes

VERSION_PATH = "game/VERSION"
GAME_DIR = PurePosixPath("game")
BUILD_PATHS = (PurePosixPath("pygbag.ini"), PurePosixPath("web"))  # shape the build, not in game/
SKIP_LABEL = "no-version-bump"
VERSION_FORMAT = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

type Version = tuple[int, int, int]


def parse_version(text: str, where: str) -> Version:
    """Turn '1.2.3' into (1, 2, 3). Raise ValueError naming `where` on anything else."""
    match = VERSION_FORMAT.fullmatch(text.strip())
    if match is None:
        raise ValueError(f"{where}: {text.strip()!r} is not MAJOR.MINOR.PATCH, such as 1.0.0")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def show(version: Version) -> str:
    """Turn (1, 2, 3) back into '1.2.3'."""
    return ".".join(str(part) for part in version)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run one git command and keep its output. Never raises on a git failure."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def base_version(base: str) -> Version | None:
    """The version on the base branch, or None if the base has no VERSION file yet."""
    result = git("show", f"{base}:{VERSION_PATH}")
    if result.returncode != 0:
        return None
    return parse_version(result.stdout, f"{VERSION_PATH} on {base}")


def changed_files(base: str) -> list[PurePosixPath]:
    """Files the branch changed since it left `base`."""
    result = git("diff", "--name-only", f"{base}...HEAD")
    if result.returncode != 0:
        raise OSError(f"git diff against {base} failed: {result.stderr.strip()}")
    return [PurePosixPath(line) for line in result.stdout.splitlines() if line]


def shipped_files(files: list[PurePosixPath], ini_path: str) -> list[PurePosixPath]:
    """The files among `files` that end up in the browser build."""
    excludes = load_excludes(ini_path)
    shipped: list[PurePosixPath] = []
    for path in files:
        builds = any(path.is_relative_to(build) for build in BUILD_PATHS)
        packed = path.is_relative_to(GAME_DIR) and not excludes.matches(path.relative_to(GAME_DIR))
        if builds or packed:
            shipped.append(path)
    return shipped


def parse_args() -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, help="the base branch, such as origin/main")
    parser.add_argument("--skip", action="store_true", help=f"the PR has the {SKIP_LABEL} label")
    parser.add_argument("--ini", default=DEFAULT_INI, help=f"default: {DEFAULT_INI}")
    return parser.parse_args()


def main() -> int:
    """Run the check and return the exit code."""
    args = parse_args()

    # Bad input is a setup problem (exit 2), not a missing bump (exit 1).
    try:
        head = parse_version(Path(VERSION_PATH).read_text(encoding="utf-8"), VERSION_PATH)
        base = base_version(args.base)
        shipped = shipped_files(changed_files(args.base), args.ini)
    except (OSError, ValueError, SyntaxError, KeyError, configparser.Error) as err:
        print(f"::error::cannot check the version: {err}")
        return 2

    was = show(base) if base is not None else "none"
    print(f"Version: {was} on {args.base}, {show(head)} on this branch.")
    print(f"Shipped files changed: {len(shipped)}")
    print("\n".join(f"  {p}" for p in shipped))

    if base is not None and head < base:
        print(f"::error file={VERSION_PATH}::The version went down: {was} to {show(head)}.")
        return 1
    if not shipped:
        print("OK: no shipped file changed, so the version can stay.")
        return 0
    if base is None or head > base:
        print(f"OK: the version goes up, {was} to {show(head)}.")
        return 0
    if args.skip:
        print(f"OK: shipped files changed, the version stays at {was}: label {SKIP_LABEL}.")
        return 0
    print(
        f"::error file={VERSION_PATH}::Shipped game files changed but the version is still {was}. "
        f"Raise it in {VERSION_PATH} (middle number for a feature, last number for a fix), "
        f"or add the label {SKIP_LABEL} to the pull request to keep it."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
