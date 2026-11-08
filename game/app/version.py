"""Read the game's version once, at startup.

The version lives in one place, the plain-text file `VERSION` at the game's root, which ships in
the browser build. It holds MAJOR.MINOR.PATCH, such as `1.0.0`, with no `v` in front. A missing
file raises FileNotFoundError; any other text raises ValueError naming the file. Only app.frame
imports this module, inside the guard.

Source: docs/contracts/systems/screens.md, Interface (app/version.py); 10-ui.md, `version_label`.
"""

import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

VERSION_FILE: Path = Path(__file__).resolve().parent.parent / "VERSION"
"""The version file at the game's root. Read at call time, so a check can point it elsewhere."""

VERSION_FORMAT: re.Pattern[str] = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
"""Three whole numbers joined by dots, no leading zeros."""


def load_version() -> str:
    """Return the version, such as `1.0.0`. Logs one INFO line."""
    text: str = VERSION_FILE.read_text(encoding="utf-8").strip()
    if VERSION_FORMAT.fullmatch(text) is None:
        raise ValueError(f"VERSION: {text!r} is not MAJOR.MINOR.PATCH, such as 1.0.0")
    log.info("version %s", text)
    return text
