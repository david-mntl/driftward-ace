"""Adding a drifter touches only the drifter's own files: a fitness test.

The code outside a drifter's own modules never names one of its `DrifterType` members. It
registers by type (the three `registry` modules), or it asks the drifter for a flag or a hook.
A new drifter then costs one enum line, the import lines in the three `__init__.py` files, its own
modules and its debug spawn rows.

Source: docs/contracts/systems/drifters.md, Rules, Registry; docs/contracts/systems/app.md,
Rules, Tuning loader.
"""

import ast
from pathlib import Path

from core.drifters.base import Drifter, DrifterType
from core.drifters.chain_lightning import (
    ChainLayout,
    ChainLightning,
    ChainLightningTypeExtra,
    InvertMirror,
)
from core.drifters.registry import drifter_class

REPO = Path(__file__).resolve().parents[3]
"""The repository root: game/tests/core/ is three folders down."""

SOURCE_ROOTS: tuple[str, ...] = ("game", "tools")
"""Where the code lives. Tests are not scanned: a test names the member it tests."""


def _own_files(drifter_type: DrifterType) -> set[Path]:
    """The files that may name this drifter: its core, view and tuning modules."""
    module: str = drifter_class(drifter_type).__module__.rsplit(".", 1)[-1]
    return {
        REPO / "game" / "core" / "drifters" / f"{module}.py",
        REPO / "game" / "ui" / "drifters" / f"{module}_view.py",
        REPO / "game" / "app" / "drifters" / f"{module}_tuning.py",
    }


def _source_files() -> list[Path]:
    files: list[Path] = []
    for root in SOURCE_ROOTS:
        files += [
            path
            for path in (REPO / root).rglob("*.py")
            if "tests" not in path.relative_to(REPO).parts and "__pycache__" not in path.parts
        ]
    return sorted(files)


def _named_members(path: Path) -> list[tuple[int, DrifterType]]:
    """Every `DrifterType.<MEMBER>` in the file, with its line. Strings and comments don't count."""
    return [
        (node.lineno, DrifterType[node.attr])
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "DrifterType"
        and node.attr in DrifterType.__members__
    ]


def test_only_a_drifters_own_modules_name_its_type() -> None:
    problems: list[str] = []
    for path in _source_files():
        for line, drifter_type in _named_members(path):
            if path not in _own_files(drifter_type):
                problems.append(
                    f"{path.relative_to(REPO)}:{line} names DrifterType.{drifter_type.name}"
                )
    assert not problems, (
        "Only a drifter's own modules (core/drifters/<name>.py, ui/drifters/<name>_view.py, "
        "app/drifters/<name>_tuning.py) may name its DrifterType member. Register by type, or "
        "ask the drifter for a flag or a hook:\n  " + "\n  ".join(problems)
    )


def test_every_drifter_names_itself_in_its_own_core_module() -> None:
    """The scan finds something: each drifter's core module names its own member."""
    for drifter_type in DrifterType:
        core_file: Path = next(p for p in sorted(_own_files(drifter_type)) if "core" in p.parts)
        assert drifter_type in {t for _line, t in _named_members(core_file)}


def test_only_a_drifter_with_a_telegraph_says_so() -> None:
    """wave_check asks the drifter: the base says none, the chain lightning says its charge."""
    assert Drifter.telegraph_ticks(None) is None
    assert ChainLightning.telegraph_ticks(None) is None
    for drifter_type in DrifterType:
        if drifter_type is not DrifterType.CHAIN_LIGHTNING:
            assert drifter_class(drifter_type).telegraph_ticks(None) is None
    extra: ChainLightningTypeExtra = ChainLightningTypeExtra(
        node_size=12.0,
        arc_width=6.0,
        charge_ticks=90,
        fire_ticks=120,
        charge_rays=4,
        ray_length=16.0,
        ray_width=2.0,
        warning_layout=ChainLayout(
            nodes=((-32.0, 0.0), (32.0, 0.0)), arcs=((0, 1),), invert_mirror=InvertMirror.LEFT_RIGHT
        ),
    )
    assert ChainLightning.telegraph_ticks(extra) == 90
