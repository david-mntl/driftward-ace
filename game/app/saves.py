"""Read and write the saved top 10 and last nickname in the browser's localStorage.

`load_saves` reads the one key once, at startup, checks it against save-data.schema.json by hand
(pygbag has no schema library) and returns the core `Saves`, or None when saves don't work: on
desktop, when the storage is missing or blocked, or when the stored text is broken. Broken text is
left as it is. `write_saves` stores the whole document after a tick that saved an entry. Neither
lets a storage or data problem reach the error guard: the game runs on without saves. It holds
the game's one `except Exception` outside the guard, around the browser storage calls only.
Not a startup module: it imports core, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app/save-storage.md, Interface and Rules;
docs/contracts/schemas/save-data.schema.json; 11-save-data.md, rules 1, 4 and 5.
"""

import json
import logging
import platform
import sys
from typing import Final, Protocol, TypeGuard

from core.levels import FIRST_LEVEL, LEVEL_COUNT
from core.saves import TOP_N, Saves, ScoreEntry, is_valid_nickname

log = logging.getLogger(__name__)

SAVE_KEY: Final[str] = "driftward-ace.saves"
"""The one localStorage key that holds the save data. A name, not a GDD value."""

_DOCUMENT_KEYS: Final[frozenset[str]] = frozenset({"entries", "last_nickname"})
_ENTRY_KEYS: Final[frozenset[str]] = frozenset({"nickname", "score", "level_reached"})


class _Storage(Protocol):
    """The two calls the game makes on the browser's localStorage."""

    def getItem(self, key: str) -> object:  # noqa: N802 - the browser's method name
        """Return the stored text, or None (JS null) when nothing is stored under `key`."""
        ...

    def setItem(self, key: str, value: str) -> None:  # noqa: N802 - the browser's method name
        """Store `value` under `key`. Raises when the browser refuses it."""
        ...


def load_saves() -> Saves | None:
    """Read and check the stored saves once. An empty Saves when nothing is stored, None when
    saves don't work. Never raises for missing or blocked storage or broken data.

    pygbag 0.9.3 raises a bare Exception when the browser refuses a storage call, so the
    storage read and getItem alone sit inside an `except Exception` (game/CONTEXT.md, Error
    handling, the app/saves.py exception).
    Source: save-storage.md, Rules, load_saves steps 1 to 4, Where saves work and Errors.
    """
    if sys.platform != "emscripten":
        log.info("saves off reason=desktop")
        return None
    try:
        raw: object = _local_storage().getItem(SAVE_KEY)
    except Exception as err:  # noqa: BLE001 - the bridge's only class; logged, saves turn off
        log.warning("saves off reason=storage error=%s", err)
        return None
    if raw is None:
        log.info("saves loaded entries=0 last_nickname=none")
        return Saves()
    try:
        saves: Saves = _parse(str(raw))
    except (ValueError, TypeError) as err:
        log.warning("saves off reason=broken error=%s", err)
        return None
    log.info(
        "saves loaded entries=%d last_nickname=%s",
        len(saves.entries),
        _quoted(saves.last_nickname),
    )
    return saves


def write_saves(saves: Saves) -> bool:
    """Store `saves` whole under SAVE_KEY. True when the browser took it, False when it didn't.

    False when the storage is missing or the browser refuses setItem (full or blocked): pygbag
    0.9.3 raises a bare Exception for that, caught around the storage calls alone. The text is
    built before the `try`, so a bug in it still reaches the guard.
    Source: save-storage.md, Rules, write_saves and Errors.
    """
    text: str = _to_text(saves)
    try:
        _local_storage().setItem(SAVE_KEY, text)
    except Exception as err:  # noqa: BLE001 - the bridge's only class; logged, saves turn off
        log.warning("saves off reason=write error=%s", err)
        return False
    log.debug("saves written entries=%d", len(saves.entries))
    return True


def _local_storage() -> _Storage:
    """Return the page's localStorage through pygbag's window bridge (browser only).

    Raises AttributeError when the window or its storage is missing. pygbag raises a bare
    Exception when the browser refuses the read.
    """
    # pygbag adds `window` to `platform` in the browser only, so type checkers can't see it.
    storage: _Storage | None = platform.window.localStorage  # type: ignore[attr-defined]
    if storage is None:
        raise AttributeError("window.localStorage is missing")
    return storage


def _to_text(saves: Saves) -> str:
    """Return the save document as JSON text, exactly the schema's shape."""
    entries: list[dict[str, object]] = [
        {"nickname": entry.nickname, "score": entry.score, "level_reached": entry.level_reached}
        for entry in saves.entries
    ]
    return json.dumps({"entries": entries, "last_nickname": saves.last_nickname})


def _parse(text: str) -> Saves:
    """Check the stored text and build the Saves. Raises ValueError naming the first problem.

    Invalid JSON raises ValueError starting "not valid JSON", as the tuning loader names it.
    """
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"not valid JSON: {err}") from err
    if not isinstance(data, dict):
        raise ValueError("save data must be an object")
    _check_keys("save data", data, _DOCUMENT_KEYS)
    raw_entries: object = data["entries"]
    if not isinstance(raw_entries, list):
        raise ValueError("entries must be a list")
    if len(raw_entries) > TOP_N:
        raise ValueError(f"entries must hold at most {TOP_N} entries, got {len(raw_entries)}")
    entries: tuple[ScoreEntry, ...] = tuple(
        _parse_entry(f"entries[{index}]", item) for index, item in enumerate(raw_entries)
    )
    _check_order(entries)
    last_nickname: object = data["last_nickname"]
    if last_nickname is not None and not _is_nickname(last_nickname):
        raise ValueError("last_nickname must be null or a valid nickname")
    return Saves(entries=entries, last_nickname=last_nickname)


def _parse_entry(where: str, item: object) -> ScoreEntry:
    """Check one stored entry and build its ScoreEntry. Raises ValueError naming the field."""
    if not isinstance(item, dict):
        raise ValueError(f"{where} must be an object")
    _check_keys(where, item, _ENTRY_KEYS)
    nickname: object = item["nickname"]
    if not _is_nickname(nickname):
        raise ValueError(f"{where}.nickname must be a valid nickname")
    score: object = item["score"]
    if not _is_int(score) or score < 0:
        raise ValueError(f"{where}.score must be an integer >= 0")
    level: object = item["level_reached"]
    if not _is_int(level) or not FIRST_LEVEL <= level <= LEVEL_COUNT:
        raise ValueError(
            f"{where}.level_reached must be an integer from {FIRST_LEVEL} to {LEVEL_COUNT}"
        )
    return ScoreEntry(nickname=nickname, score=score, level_reached=level)


def _check_keys(where: str, fields: dict[object, object], expected: frozenset[str]) -> None:
    """Raise ValueError when a key is missing or unknown."""
    for key in sorted(expected):
        if key not in fields:
            raise ValueError(f"{where}: {key} is missing")
    for field in fields:
        if field not in expected:
            raise ValueError(f"{where}: unknown key {field!r}")


def _check_order(entries: tuple[ScoreEntry, ...]) -> None:
    """Raise ValueError when two neighbors are out of the top-10 order.

    The upper one's score is higher, or equal with a level reached at least as high.
    Source: systems/saves.md, Rules, Order.
    """
    for index in range(1, len(entries)):
        upper: ScoreEntry = entries[index - 1]
        lower: ScoreEntry = entries[index]
        in_order: bool = upper.score > lower.score or (
            upper.score == lower.score and upper.level_reached >= lower.level_reached
        )
        if not in_order:
            raise ValueError(f"entries[{index}] ranks above entries[{index - 1}]: out of order")


def _is_int(value: object) -> TypeGuard[int]:
    """True for an int that is not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_nickname(value: object) -> TypeGuard[str]:
    """True for a str that passes is_valid_nickname."""
    return isinstance(value, str) and is_valid_nickname(value)


def _quoted(nickname: str | None) -> str:
    """Return the nickname quoted with repr, or "none"."""
    return "none" if nickname is None else repr(nickname)
