"""Remembered passes: so a wave that has not changed is not checked again.

A pass is stored under `<wave id>@<level>` with a fingerprint of everything the check reads: the
wave, every tuning file, the config and the suite version. Change any of them and the pass is
stale. Part 2 raises SUITE, so every part 1 pass goes stale when the bot checks arrive.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from app import tuning as tuning_module
from settings import Config

SUITE: str = "part1"
"""Which checks ran. A pass from a smaller suite never counts for a bigger one."""
STORE_FILE: Path = Path(__file__).resolve().parent / "passes.json"


def fingerprint(wave_document: Any, config: Config) -> str:
    """Hash the wave and the values it is checked against. Whitespace does not matter."""
    digest = hashlib.sha256()
    digest.update(SUITE.encode())
    digest.update(_canonical(wave_document))
    digest.update(_canonical(config.raw))
    folder: Path = tuning_module.TUNING_DIR
    for path in sorted(folder.rglob("*.json")):
        if path.name == "debug_spawns.json":
            continue  # the debug spawn list never reaches a wave
        digest.update(path.relative_to(folder).as_posix().encode())
        digest.update(_canonical(json.loads(path.read_text(encoding="utf-8"))))
    return digest.hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _key(wave_id: str, level: int) -> str:
    return f"{wave_id}@{level}"


def read(path: Path | None = None) -> dict[str, str]:
    """The remembered passes. A missing, broken or other-suite file remembers nothing."""
    try:
        data: Any = json.loads((path or STORE_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or data.get("suite") != SUITE:
        return {}
    passes: Any = data.get("passes", {})
    return (
        {k: v for k, v in passes.items() if isinstance(v, str)}
        if isinstance(passes, dict)
        else {}
    )


def is_fresh(passes: dict[str, str], wave_id: str, level: int, print_: str) -> bool:
    return passes.get(_key(wave_id, level)) == print_


def remember(
    passes: dict[str, str], wave_id: str, level: int, print_: str, ok: bool
) -> None:
    """Keep a pass, or drop the old one when the wave now fails."""
    if ok:
        passes[_key(wave_id, level)] = print_
    else:
        passes.pop(_key(wave_id, level), None)


def write(passes: dict[str, str], path: Path | None = None) -> None:
    body: dict[str, Any] = {"suite": SUITE, "passes": dict(sorted(passes.items()))}
    (path or STORE_FILE).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
