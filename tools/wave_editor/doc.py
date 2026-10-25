"""The sandbox document: one wave plus the drifter values layered over production. No pygame.

Each drifter value resolves top-down, the first layer that has it wins:
  W  inline changes in this document (`inline`, only the values touched)
  F  a named tuning file the document points to (`named`), a full copy in sandbox/tuning/
  P  production, game/tuning/drifters/<type>.json
The shared hazard values (the graze margin) have the W and P layers only: `hazards` holds the
touched ones over production, game/tuning/hazards.json.
The game's own loaders check the merged result (see bench.load_merged). This module never writes
under game/. Only promote.py does, and only what the Director ticks.
"""

import copy
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app import tuning as tuning_module

TOOL_DIR: Path = Path(__file__).resolve().parent
GAME_DIR: Path = TOOL_DIR.parents[1] / "game"
WAVES_DIR: Path = GAME_DIR / "waves"
SANDBOX_DIR: Path = TOOL_DIR / "sandbox"
NAMED_DIR: Path = SANDBOX_DIR / "tuning"
NAME: re.Pattern[str] = re.compile(r"^[a-z][a-z0-9_]*$")

Leaf = tuple[str, ...]
"""Keys from a type file's root to one value, e.g. ("variants", "big", "width")."""


def production_dir() -> Path:
    """The game's tuning folder, read at call time (a check can point it elsewhere)."""
    return tuning_module.TUNING_DIR


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"{path.name}: not valid JSON: {err}") from err


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `base` with every value of `patch` laid over it."""
    merged: dict[str, Any] = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def leaves(obj: dict[str, Any], prefix: Leaf = ()) -> list[tuple[Leaf, Any]]:
    """Every editable value (number, text, flag) under `obj`, in file order. Lists are skipped."""
    found: list[tuple[Leaf, Any]] = []
    for key, value in obj.items():
        if isinstance(value, dict):
            found.extend(leaves(value, (*prefix, key)))
        elif not isinstance(value, list) and value is not None:
            found.append(((*prefix, key), value))
    return found


def get_leaf(obj: dict[str, Any], path: Leaf) -> Any:
    """The value at `path`, or None if a key is missing."""
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj


def has_leaf(obj: dict[str, Any], path: Leaf) -> bool:
    node: Any = obj
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return True


def set_leaf(obj: dict[str, Any], path: Leaf, value: Any) -> None:
    for key in path[:-1]:
        obj = obj.setdefault(key, {})
    obj[path[-1]] = value


def remove_leaf(obj: dict[str, Any], path: Leaf) -> None:
    """Delete the value at `path` and any parent left empty."""
    parents: list[dict[str, Any]] = [obj]
    for key in path[:-1]:
        parents.append(parents[-1][key])
    del parents[-1][path[-1]]
    for parent, key in zip(reversed(parents[:-1]), reversed(path[:-1]), strict=True):
        if not parent[key]:
            del parent[key]


@dataclass
class Doc:
    """One wave (None: the spawn list plays) and its value layers."""

    wave: dict[str, Any] | None
    path: Path | None = None
    """Where Save writes. Always outside game/."""
    source_file: Path | None = None
    """The file read last, watched for outside edits."""
    origin: str | None = None
    """The game wave id this was opened from. Promote writes there."""
    named: dict[str, str] = field(default_factory=dict)
    inline: dict[str, dict[str, Any]] = field(default_factory=dict)
    hazards: dict[str, Any] = field(default_factory=dict)
    """Shared hazard values touched in this document (layer W), over production's hazards.json."""
    dirty: bool = False

    # ---- files --------------------------------------------------------------------------

    @classmethod
    def open(cls, path: Path) -> "Doc":
        """Read a sandbox document, or a plain game wave file (opened as a copy)."""
        data: Any = read_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"{path.name}: must be a JSON object")  # noqa: TRY004
        if {"wave", "named", "inline"} & data.keys():
            doc: Doc = cls(None, path=path, source_file=path)
            doc._take(data)
        else:
            in_waves: bool = path.resolve().parent == WAVES_DIR.resolve()
            doc = cls(
                data,
                path=SANDBOX_DIR / f"{path.stem}.json",
                source_file=path,
                origin=path.stem if in_waves else None,
            )
        doc.sort()
        return doc

    def _take(self, data: dict[str, Any]) -> None:
        self.wave = data.get("wave")
        self.origin = data.get("origin")
        self.named = dict(data.get("named", {}))
        self.inline = dict(data.get("inline", {}))
        self.hazards = dict(data.get("hazards", {}))

    def reload_from_source(self) -> None:
        """Read the source file again. A plain wave file replaces only the wave."""
        assert self.source_file is not None
        data: Any = read_json(self.source_file)
        if {"wave", "named", "inline"} & data.keys():
            self._take(data)
        else:
            self.wave = data
        self.dirty = False
        self.sort()

    def save(self, path: Path | None = None) -> Path:
        target: Path | None = path or self.path
        if target is None:
            raise ValueError("no file name yet")
        data: dict[str, Any] = {}
        if self.origin:
            data["origin"] = self.origin
        if self.wave is not None:
            data["wave"] = self.wave
        data["named"] = self.named
        data["inline"] = self.inline
        if self.hazards:
            data["hazards"] = self.hazards
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.path = self.source_file = target
        self.dirty = False
        return target

    def snapshot(self) -> Any:
        return copy.deepcopy(
            (
                self.wave,
                self.path,
                self.source_file,
                self.origin,
                self.named,
                self.inline,
                self.hazards,
                self.dirty,
            )
        )

    def restore(self, saved: Any) -> None:
        (
            self.wave,
            self.path,
            self.source_file,
            self.origin,
            self.named,
            self.inline,
            self.hazards,
            self.dirty,
        ) = saved

    # ---- names --------------------------------------------------------------------------

    @property
    def wave_id(self) -> str:
        stem: str = self.origin or (self.path.stem if self.path else "sandbox")
        return stem if NAME.fullmatch(stem) else "sandbox"

    @property
    def title(self) -> str:
        if self.wave is None:
            name: str = "spawn list"
        else:
            name = self.path.name if self.path else f"{self.wave_id}.json"
        return name + ("*" if self.dirty else "")

    # ---- placements ---------------------------------------------------------------------

    def sort(self) -> None:
        """Keep the placements in trigger order, ties in file order, as the game sorts them."""
        if self.wave is None or not isinstance(self.wave.get("placements"), list):
            return

        def trigger(item: Any) -> float:
            value: Any = item.get("at_px", 0) if isinstance(item, dict) else 0
            return value if isinstance(value, int | float) else 0

        self.wave["placements"].sort(key=trigger)

    # ---- drifter values -----------------------------------------------------------------

    def production_values(self, drifter: str) -> dict[str, Any]:
        return read_json(production_dir() / "drifters" / f"{drifter}.json")

    def base_values(self, drifter: str) -> dict[str, Any]:
        """Layer F if the document names a file for this type, else layer P."""
        if drifter in self.named:
            return read_json(NAMED_DIR / f"{self.named[drifter]}.json")
        return self.production_values(drifter)

    def effective(self, drifter: str) -> dict[str, Any]:
        """The type's values with every layer applied."""
        return deep_merge(self.base_values(drifter), self.inline.get(drifter, {}))

    def layer(self, drifter: str, path: Leaf) -> str:
        """ "W", "F" or "P": the layer the value at `path` comes from."""
        if has_leaf(self.inline.get(drifter, {}), path):
            return "W"
        return "F" if drifter in self.named else "P"

    def set_value(self, drifter: str, path: Leaf, value: Any) -> None:
        set_leaf(self.inline.setdefault(drifter, {}), path, value)
        self.dirty = True

    def step_down(self, drifter: str, path: Leaf) -> str:
        """Drop one layer: W goes back to F or P; F unlinks the named file. Returns what happened."""
        self.dirty = True
        if has_leaf(self.inline.get(drifter, {}), path):
            remove_leaf(self.inline[drifter], path)
            if not self.inline[drifter]:
                del self.inline[drifter]
            return "back to " + (
                "the named file" if drifter in self.named else "production"
            )
        if drifter in self.named:
            del self.named[drifter]
            return "named file unlinked, all its values back to production"
        self.dirty = False
        return "already production"

    def link_named(self, drifter: str, name: str | None) -> None:
        if name is None:
            self.named.pop(drifter, None)
        else:
            self.named[drifter] = name
        self.dirty = True

    def named_files(self, drifter: str) -> list[str]:
        """Named tuning files for this type: sandbox/tuning/<type>.json and <type>_*.json."""
        if not NAMED_DIR.exists():
            return []
        stems: list[str] = sorted(p.stem for p in NAMED_DIR.glob("*.json"))
        return [s for s in stems if s == drifter or s.startswith(drifter + "_")]

    # ---- shared hazard values -----------------------------------------------------------

    def production_hazards(self) -> dict[str, Any]:
        return read_json(production_dir() / "hazards.json")

    def effective_hazards(self) -> dict[str, Any]:
        """The hazard values with this document's changes laid over production."""
        return deep_merge(self.production_hazards(), self.hazards)

    def hazard_layer(self, name: str) -> str:
        """ "W" if this document changed the hazard value, else "P"."""
        return "W" if name in self.hazards else "P"

    def set_hazard(self, name: str, value: Any) -> None:
        self.hazards[name] = value
        self.dirty = True

    def drop_hazard(self, name: str) -> str:
        """Back to production. Returns what happened."""
        if name not in self.hazards:
            return "already production"
        del self.hazards[name]
        self.dirty = True
        return "back to production"

    def write_merged_dir(self, dest: Path) -> None:
        """Copy the production tuning folder to `dest` with the layered type files and hazard
        values laid over it."""
        shutil.copytree(production_dir(), dest, dirs_exist_ok=True)
        if self.hazards:
            (dest / "hazards.json").write_text(
                json.dumps(self.effective_hazards(), indent=2), encoding="utf-8"
            )
        for drifter in sorted(self.named.keys() | self.inline.keys()):
            target: Path = dest / "drifters" / f"{drifter}.json"
            target.write_text(
                json.dumps(self.effective(drifter), indent=2), encoding="utf-8"
            )
