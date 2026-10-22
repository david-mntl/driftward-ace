"""Promote: turn the sandbox into game files, showing first what would change. No pygame.

`plan(doc)` lists what promote would write: the wave file and one production tuning file per
changed type, each with its value diffs and, for a type, the other waves that use it. Nothing is
written until `write(items)`, and only ticked items are. It never commits.
Production tuning files are patched in place (only the changed numbers), so a diff stays small.
"""

import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import doc as doc_module
from doc import Doc, Leaf, get_leaf, leaves, read_json

MAX_DIFF_LINES: int = 6


@dataclass
class Item:
    """One file promote can write."""

    label: str
    target: Path
    text: str
    lines: list[str] = field(default_factory=list)
    checked: bool = False
    drifter: str | None = None
    """For a tuning file, the type it holds; its sandbox layers are dropped once it is written."""


def spans(text: str) -> dict[Leaf, tuple[int, int]]:
    """Return the (start, end) offsets of every value of the JSON text that sits in objects only.

    Values inside lists are skipped. Used to swap single numbers without reformatting the file.
    """
    found: dict[Leaf, tuple[int, int]] = {}
    pos: int = 0

    def skip() -> None:
        nonlocal pos
        while text[pos] in " \t\r\n":
            pos += 1

    def string() -> str:
        nonlocal pos
        start: int = pos
        pos += 1
        while text[pos] != '"':
            pos += 2 if text[pos] == "\\" else 1
        pos += 1
        return json.loads(text[start:pos])

    def value(path: Leaf | None) -> None:
        nonlocal pos
        skip()
        char: str = text[pos]
        if char == "{":
            pos += 1
            while True:
                skip()
                if text[pos] == "}":
                    pos += 1
                    return
                if text[pos] == ",":
                    pos += 1
                    continue
                key: str = string()
                skip()
                pos += 1  # the colon
                value(None if path is None else (*path, key))
        elif char == "[":
            pos += 1
            while True:
                skip()
                if text[pos] == "]":
                    pos += 1
                    return
                if text[pos] == ",":
                    pos += 1
                    continue
                value(None)
        else:
            start: int = pos
            if char == '"':
                string()
            else:
                while text[pos] not in ",}] \t\r\n":
                    pos += 1
            if path is not None:
                found[path] = (start, pos)

    value(())
    return found


def patch_text(text: str, changes: dict[Leaf, Any]) -> str | None:
    """Return `text` with the changed values swapped in place, or None if a path has no spot."""
    where: dict[Leaf, tuple[int, int]] = spans(text)
    if any(path not in where for path in changes):
        return None
    for path in sorted(changes, key=lambda p: where[p][0], reverse=True):
        start, end = where[path]
        text = text[:start] + json.dumps(changes[path]) + text[end:]
    return text


def format_wave(wave: dict[str, Any]) -> str:
    """The game's wave file style: one placement per line."""
    head: list[str] = [
        f"  {json.dumps(key)}: {json.dumps(value)}"
        for key, value in wave.items()
        if key != "placements"
    ]
    rows: list[str] = [
        "    { "
        + ", ".join(
            f"{json.dumps(key)}: {json.dumps(value)}" for key, value in item.items()
        )
        + " }"
        for item in wave.get("placements", [])
    ]
    body: str = "[\n" + ",\n".join(rows) + "\n  ]" if rows else "[]"
    return "{\n" + ",\n".join([*head, f'  "placements": {body}']) + "\n}\n"


def used_by(drifter: str, own_id: str) -> list[str]:
    """Other game waves that place this drifter type, as 'wave (count)'."""
    users: list[str] = []
    for path in sorted(doc_module.WAVES_DIR.glob("*.json")):
        if path.stem in (own_id, "playlist"):
            continue
        try:
            items: Any = read_json(path).get("placements", [])
        except (ValueError, AttributeError, OSError):
            continue
        count: int = sum(
            1
            for item in items
            if isinstance(item, dict) and item.get("type") == drifter
        )
        if count:
            users.append(f"{path.stem} ({count})")
    return users


def plan(doc: Doc) -> list[Item]:
    """What promote would write, unticked except a changed wave file."""
    items: list[Item] = []
    if doc.wave is not None:
        target: Path = doc_module.WAVES_DIR / f"{doc.wave_id}.json"
        text: str = format_wave(doc.wave)
        old: str | None = (
            target.read_text(encoding="utf-8") if target.exists() else None
        )
        if old is None:
            lines: list[str] = ["new file"]
        else:
            changed: int = sum(
                1
                for row in difflib.ndiff(old.splitlines(), text.splitlines())
                if row[:1] in "+-"
            )
            lines = [f"{changed} lines differ"] if changed else ["no change"]
        lines.append("playlist.json is not changed")
        items.append(
            Item(f"wave  waves/{target.name}", target, text, lines, old != text)
        )
    for drifter in sorted(doc.named.keys() | doc.inline.keys()):
        production: dict[str, Any] = doc.production_values(drifter)
        effective: dict[str, Any] = doc.effective(drifter)
        if effective == production:
            continue
        target = doc_module.production_dir() / "drifters" / f"{drifter}.json"
        changes: dict[Leaf, Any] = {
            path: value
            for path, value in leaves(effective)
            if value != get_leaf(production, path)
        }
        old_text: str = target.read_text(encoding="utf-8")
        patched: str | None = patch_text(old_text, changes)
        if patched is None or read_json_text(patched) != effective:
            patched = json.dumps(effective, indent=2) + "\n"
            lines = ["the whole file is rewritten (format changes)"]
        else:
            lines = []
        shown: list[str] = [
            f"{'.'.join(path)}: {get_leaf(production, path)} -> {value}"
            for path, value in changes.items()
        ]
        lines += shown[:MAX_DIFF_LINES]
        if len(shown) > MAX_DIFF_LINES:
            lines.append(f"... {len(shown) - MAX_DIFF_LINES} more")
        others: list[str] = used_by(drifter, doc.wave_id)
        lines.append(
            "also used by: " + (", ".join(others) if others else "no other wave")
        )
        items.append(
            Item(f"values tuning/drifters/{drifter}.json", target, patched, lines)
        )
    return items


def read_json_text(text: str) -> Any:
    return json.loads(text)


def write(items: list[Item]) -> list[Path]:
    """Write every ticked item. Returns the files written."""
    written: list[Path] = []
    for item in items:
        if item.checked:
            item.target.parent.mkdir(parents=True, exist_ok=True)
            item.target.write_text(item.text, encoding="utf-8")
            written.append(item.target)
    return written
