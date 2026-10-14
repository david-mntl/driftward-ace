#!/usr/bin/env python3
"""Check that the pygbag release package holds runtime files only.

The excludes are read from pygbag.ini, the same file pygbag builds from, so
they live in one place. The script opens web.zip, lists the game files in the
game.apk inside it, and fails if an excluded file got in or a required file
is missing.

Run from the repo root after `pygbag --archive game`:

    python .github/scripts/check_release_package.py [--zip PATH] [--ini PATH]

Exit codes: 0 pass, 1 the package is wrong, 2 an input is missing or unreadable.
Errors are printed as GitHub Actions annotations, so they show on the PR.
"""

import argparse
import ast
import configparser
import io
import sys
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

DEFAULT_ZIP = "game/build/web.zip"
DEFAULT_INI = "pygbag.ini"

APK_NAME = "game.apk"  # pygbag's inner archive with the game files
APK_ROOT = PurePosixPath("assets")  # game/ is stored under this folder
REQUIRED = (PurePosixPath("main.py"),)  # the browser build can't start without these


@dataclass(frozen=True)
class Excludes:
    """Exclude rules from pygbag.ini, split the way pygbag matches them."""

    root_dirs: tuple[PurePosixPath, ...]  # "/tests": a folder at the game root
    any_dirs: frozenset[str]  # "__pycache__": a folder with that name, at any depth
    files: frozenset[str]  # "ruff.toml": a file with that name, at any depth

    def matches(self, path: PurePosixPath) -> bool:
        """Return True if pygbag should have left this game file out."""
        if path.name in self.files:
            return True
        folder = PurePosixPath("/") / path.parent
        if any(folder.is_relative_to(root) for root in self.root_dirs):
            return True
        return not self.any_dirs.isdisjoint(path.parent.parts)


def read_list(section: configparser.SectionProxy, key: str) -> list[str]:
    """Read one list value. pygbag stores lists as Python literals."""
    value = ast.literal_eval(section.get(key, "[]"))
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} in [{section.name}] must be a list of strings")
    return value


def load_excludes(ini_path: str) -> Excludes:
    """Parse pygbag.ini with the same settings pygbag 0.9.3 uses."""
    parser = configparser.ConfigParser(inline_comment_prefixes=";")
    if not parser.read(ini_path):
        raise FileNotFoundError(f"{ini_path} not found")
    section = parser["DEPENDENCIES"]
    dirs = read_list(section, "ignoreDirs")
    return Excludes(
        root_dirs=tuple(PurePosixPath(d) for d in dirs if d.startswith("/")),
        any_dirs=frozenset(d for d in dirs if not d.startswith("/")),
        files=frozenset(read_list(section, "ignoreFiles")),
    )


def list_game_files(zip_path: str) -> list[PurePosixPath]:
    """Return the game files in web.zip, as paths relative to game/."""
    with zipfile.ZipFile(zip_path) as web_zip:
        # The apk is small. Reading it into memory once is faster than letting
        # ZipFile seek back and forth inside a compressed member.
        apk_bytes = web_zip.read(APK_NAME)
    with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
        paths = (PurePosixPath(info.filename) for info in apk.infolist() if not info.is_dir())
        return sorted(p.relative_to(APK_ROOT) for p in paths if p.is_relative_to(APK_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", default=DEFAULT_ZIP, help=f"default: {DEFAULT_ZIP}")
    parser.add_argument("--ini", default=DEFAULT_INI, help=f"default: {DEFAULT_INI}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Bad input is a setup problem (exit 2), not a bad package (exit 1).
    try:
        excludes = load_excludes(args.ini)
        files = list_game_files(args.zip)
    except (OSError, KeyError, ValueError, SyntaxError, configparser.Error) as err:
        # BadZipFile is a ValueError subclass, KeyError covers a missing
        # game.apk or [DEPENDENCIES] section.
        print(f"::error::cannot check the release package: {err}")
        return 2

    problems = [f"excluded file in package: {p}" for p in files if excludes.matches(p)]
    problems += [f"required file missing: {p}" for p in REQUIRED if p not in files]

    print(f"{APK_NAME} holds {len(files)} game files:")
    print("\n".join(f"  {p}" for p in files))

    for problem in problems:
        print(f"::error::{problem}")
    if problems:
        print(f"FAIL: {len(problems)} problem(s) in {args.zip}")
        return 1

    print(f"OK: {args.zip} holds runtime files only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
