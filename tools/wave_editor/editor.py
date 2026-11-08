"""Editor state: focus, selection, rows, text prompts and promote. Keys in, state out. No drawing.

Every change goes through `Bench.edit`, so the game's own checks validate it, a refused change is
undone, and the run replays to the current tick.
"""

import copy
import json
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import doc as doc_module
import promote
import pygame
from bench import Bench
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.levels import LEVEL_COUNT
from core.scroll import scroll_speed
from core.wave_files import SEAM_CLEAR_PX, _build_wave
from doc import NAME, Doc, Leaf, get_leaf, leaves
from place import (
    CLICK_FIELDS,
    FROM_TOP_FIELDS,
    Cancelled,
    ScanPool,
    Spot,
    Unreachable,
    place_in_wave,
    placement_item,
)

ROOT: Path = doc_module.TOOL_DIR.parents[1]
FOCUS_ORDER: tuple[str, ...] = ("game", "wave", "palette", "values")
TYPES: tuple[str, ...] = tuple(drifter_type.value for drifter_type in DrifterType)
PALETTE_ROWS: int = 7
NEW_WAVE_LENGTH: int = 1320
"""Length of a new wave, px. The same as the game's first waves (20 s at Level 1)."""
"""Rows the palette lists show at once."""
START_FIELDS: tuple[dict[str, float], ...] = (
    {},
    {"x": 320.0},
    {"y": 240.0},
    {"x": 320.0, "y": 240.0},
)
"""What a new placement tries, in order, until the game accepts it (some types need an x or a y)."""
SNAP_PX: int = 10
"""A new placement triggers at the playhead, rounded to this many px."""
WAVE_FIELDS: tuple[str, ...] = ("length_px", "kind", "min_level", "extra_rest_ticks")
LENGTH_STEP: int = 10
"""px per nudge of the wave length (Shift: x10)."""
WAVE_DEFAULTS: dict[str, int] = {"min_level": 1, "extra_rest_ticks": 0}
FIELDS: tuple[str, ...] = ("at_px", "type", "x", "y", "variant", "invert")
OPTIONAL: frozenset[str] = frozenset({"x", "y", "variant", "invert"})
NUDGE_START: dict[str, float] = {"x": 320.0, "y": 240.0}
"""Where a nudge starts for a placement that has no x or y yet, screen px."""
PICK_RADIUS: float = 40.0
"""A click selects the nearest drifter within this many px."""
FLOAT_STEP: float = 0.01
HAZARD_FIELDS: tuple[str, ...] = ("graze_margin",)
"""The shared hazard values the panel edits, from game/tuning/hazards.json."""
HAZARD_STEP: float = 1.0
"""px per nudge of the graze margin (Shift: x10)."""
REMOVE: object = object()
OPEN_FOLDERS: tuple[Path, ...] = (
    doc_module.SANDBOX_DIR / "drafts",
    doc_module.SANDBOX_DIR,
    doc_module.WAVES_DIR,
    doc_module.WAVES_DIR / "other",
)
"""Where the Open list looks for wave files, in this order. Not their subfolders."""
PLAYLIST_NAME: str = "playlist"
"""The game's playlist file, in the waves folder. Not a wave."""


@dataclass
class Row:
    """One line of the SELECTED panel. `key` is None for a heading."""

    label: str
    text: str
    tag: str = ""
    key: tuple[Any, ...] | None = None
    sub: bool = False
    """A heading inside a group (a variant), drawn quieter than a section heading."""


@dataclass
class Prompt:
    """A line of typed text at the bottom of the window."""

    label: str
    text: str
    submit: Callable[[str], None]

    def __post_init__(self) -> None:
        self.start: str = self.text
        """The text it opened with. A paste replaces it until something else is typed."""


@dataclass
class PromoteView:
    items: list[promote.Item]
    cursor: int = 0


@dataclass
class Job:
    """A slow search running on a worker thread, so the window keeps playing and drawing."""

    label: str
    future: "Future[Any]"
    finish: Callable[[Any], None]
    """Runs on the main thread with the search's result when it is done."""
    revision: int
    """The bench's revision when it started. A result is dropped if the wave changed since."""
    cancelled: bool = False


@dataclass
class OpenView:
    """The Open list: every wave file the editor can open, narrowed by what is typed."""

    files: list[Path]
    text: str = ""
    cursor: int = 0
    top: int = 0
    rows: int = 10
    """Rows the list shows at once, set by the drawing."""

    def shown(self) -> list[Path]:
        """The files whose path, from the repo root, holds the typed text (any case)."""
        words: str = self.text.lower()
        return [path for path in self.files if words in _relative(path).lower()]

    def move(self, step: int) -> None:
        """Move the cursor by `step` rows, kept in the list and in view."""
        count: int = len(self.shown())
        self.cursor = min(max(self.cursor + step, 0), max(count - 1, 0))
        self.top = min(max(self.top, self.cursor - self.rows + 1), self.cursor)


class Editor:
    def __init__(self, bench: Bench) -> None:
        self.bench: Bench = bench
        self.focus: str = "game"
        self.selected: int | None = 0 if self.placements() else None
        self.cursor: int = 0
        self.prompt: Prompt | None = None
        self.promote: PromoteView | None = None
        self.picker: OpenView | None = None
        self.message: str = ""
        self.invert: bool = False
        """The palette's switch: new drifters are placed inverted (mirrored)."""
        self.at_spot: bool = False
        """Place by position: a click puts the drifter on that spot at the playhead's moment,
        instead of starting there."""
        self.coin_top: bool = False
        """A coin is placed so that it comes in from the top (see FROM_TOP_FIELDS), instead of
        appearing where it is put. It changes nothing for the other drifters."""
        self.armed: tuple[str, str | None] | None = None
        """A (type, variant) waiting for a click in the game view to be placed."""
        self.panels: dict[str, pygame.Rect] = {}
        """The clickable panels, filled by the drawing each frame."""
        self.trail: bool = True
        """Draw the selected drifter's path in the game view."""
        self._held: dict[str, Any] | None = None
        self.palette_type: int = 0
        self.palette_variant: int = 0
        self.palette_side: str = "types"
        self.scroll: dict[str, int] = {"type": 0, "variant": 0}
        self.hits: list[tuple[pygame.Rect, str, int]] = []
        """Clickable rows, filled by the drawing each frame: (area, kind, index)."""
        self.regions: dict[str, pygame.Rect] = {}
        """The palette's two lists, for the mouse wheel."""
        self.job: Job | None = None
        """The search running now, if any. Only one at a time."""
        self._worker: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="wave-editor-search"
        )
        self._scan_pool: ScanPool = ScanPool()
        """Worker processes for a UFO's slow search, started the first time it needs them."""
        self._rows_memo: tuple[tuple[int, int | None, int], list[Row]] | None = None
        self._palette_memo: tuple[tuple[int, int], dict[str, Any] | None] | None = None
        """What the drawing asks for every frame, kept until the document or the selection
        changes (the bench's `revision`), so a frame reads no file."""

    # ---- what is selected ---------------------------------------------------------------

    @property
    def doc(self) -> Doc:
        return self.bench.doc

    def placements(self) -> list[dict[str, Any]]:
        return self.doc.wave["placements"] if self.doc.wave else []

    def current(self) -> dict[str, Any] | None:
        items: list[dict[str, Any]] = self.placements()
        if self.selected is None or not 0 <= self.selected < len(items):
            return None
        return items[self.selected]

    def rows(self) -> list[Row]:
        """The wave's settings, the shared graze values, the selected placement's fields, then
        the values of its drifter type with W/F/P tags. Headings have no key.

        Kept until the document, the selection or the level changes."""
        key: tuple[int, int | None, int] = (
            self.bench.revision,
            self.selected,
            self.bench.level,
        )
        if self._rows_memo is None or self._rows_memo[0] != key:
            self._rows_memo = (key, self._build_rows())
        return self._rows_memo[1]

    def _build_rows(self) -> list[Row]:
        rows: list[Row] = []
        wave: dict[str, Any] | None = self.doc.wave
        if wave is not None:
            seconds: float = (
                float(wave.get("length_px", 0)) / scroll_speed(self.bench.level) / 60
            )
            rows.append(Row("wave", f"{seconds:.1f}s at L{self.bench.level}"))
            rows += [
                Row(name, _wave_show(wave, name), key=("wave", name))
                for name in WAVE_FIELDS
            ]
        rows += self._hazard_rows()
        placement: dict[str, Any] | None = self.current()
        if placement is None:
            return rows
        drifter: str = str(placement.get("type"))
        rows.append(Row(f"placement #{(self.selected or 0) + 1}", ""))
        try:
            effective: dict[str, Any] | None = self.doc.effective(drifter)
        except (OSError, ValueError):
            effective = None
        for name in FIELDS:
            text: str = _show(placement.get(name))
            if name == "at_px":
                text = f"{text}  {self.seconds_at(placement.get(name, 0)):.1f}s"
            elif name == "variant" and effective and name not in placement:
                text = f"default ({effective.get('default_variant', '?')})"
            rows.append(Row(name, text, key=("field", name)))
        if effective is None:
            return rows
        rows.append(Row(f"{drifter} values", self._source_line(drifter)))
        group: tuple[str, ...] = ()
        for path, value in leaves(effective):
            if path[:-1] != group:
                group = path[:-1]
                if group:
                    rows.append(Row(".".join(group), "", sub=True))
            label: str = ("  " if group else "") + path[-1]
            rows.append(
                Row(
                    label,
                    _show(value),
                    self.doc.layer(drifter, path),
                    ("value", drifter, path),
                )
            )
        return rows

    def _hazard_rows(self) -> list[Row]:
        """The graze margin, the same for every hazard, with its W or P tag."""
        try:
            effective: dict[str, Any] = self.doc.effective_hazards()
        except (OSError, ValueError):
            return []
        rows: list[Row] = [
            Row("graze (all hazards)", "production" if not self.doc.hazards else "")
        ]
        rows += [
            Row(
                name,
                _show(effective.get(name)),
                self.doc.hazard_layer(name),
                ("hazard", name),
            )
            for name in HAZARD_FIELDS
        ]
        return rows

    def seconds_at(self, px: float) -> float:
        """Seconds into the wave at which scroll distance `px` is reached, at the chosen level."""
        return float(px) / scroll_speed(self.bench.level) / 60

    def _home(self) -> int:
        """The row the cursor starts on: the placement's at_px, else the first editable row."""
        rows: list[Row] = self.rows()
        for index, row in enumerate(rows):
            if row.key == ("field", "at_px"):
                return index
        return next((i for i, row in enumerate(rows) if row.key is not None), 0)

    def _source_line(self, drifter: str) -> str:
        name: str | None = self.doc.named.get(drifter)
        return f"file {name}" if name else "production"

    def row(self) -> Row | None:
        rows: list[Row] = self.rows()
        return rows[self.cursor] if 0 <= self.cursor < len(rows) else None

    # ---- events -------------------------------------------------------------------------

    def key(self, event: pygame.event.Event) -> bool:
        """Handle a key press. True if the editor used it, so the bench keys must not."""
        if self.prompt is not None:
            self._prompt_key(event)
            return True
        if self.promote is not None:
            self._promote_key(event)
            return True
        if self.picker is not None:
            self._picker_key(event)
            return True
        ctrl: bool = bool(event.mod & pygame.KMOD_CTRL)
        shift: bool = bool(event.mod & pygame.KMOD_SHIFT)
        if ctrl:
            return self._file_key(event.key, shift)
        if event.key == pygame.K_ESCAPE and self.job and not self.job.cancelled:
            self.job.cancelled = True
            self.message = f"stopped {self.job.label}"
            return True
        if event.key == pygame.K_ESCAPE and self.armed is not None:
            self.armed = None
            self.message = "placing stopped"
            return True
        if event.key == pygame.K_ESCAPE and self.focus != "game":
            self.focus = "game"
            return True
        if event.key == pygame.K_i:
            self.toggle_invert()
            return True
        if event.key == pygame.K_t:
            self.trail = not self.trail
            return True
        if event.key == pygame.K_p:
            self.toggle_at_spot()
            return True
        if event.key == pygame.K_c:
            self.toggle_coin_top()
            return True
        if event.key == pygame.K_TAB:
            self._next_focus(-1 if shift else 1)
            return True
        if event.key == pygame.K_v and self.current() is not None:
            self._save_values_as()
            return True
        if self.focus == "palette":
            return self._palette_key(event.key)
        if self.focus == "wave":
            return self._wave_key(event.key)
        if self.focus == "values":
            return self._values_key(event.key, shift)
        return False

    def click(self, local: tuple[int, int]) -> None:
        """A click in the game view. Armed: place the drifter there. Otherwise select the
        placement of the nearest drifter and focus its values, or focus the game."""
        if self.prompt is not None or self.promote is not None:
            return
        if self.armed is not None and self.at_spot:
            self._add_at_spot(self.armed[0], self.armed[1], local)
            return
        if self.armed is not None:
            self._add(self.armed[1], drifter=self.armed[0], at=local)
            return
        count: int = len(self.placements()) if self.bench.spawn_list is None else 0
        best: tuple[float, int] | None = None
        for drifter in self.bench.run.drifters if count else ():
            distance: float = (
                (drifter.x - local[0]) ** 2 + (drifter.y - local[1]) ** 2
            ) ** 0.5
            if distance <= PICK_RADIUS and (best is None or distance < best[0]):
                best = (distance, (drifter.uid - 1) % count)
        if best is None:
            self.focus = "game"
            return
        self.selected = best[1]
        self.focus = "values"
        self.cursor = self._home()

    # ---- palette ------------------------------------------------------------------------

    def _palette_values(self) -> dict[str, Any] | None:
        """The palette's drifter type with the sandbox's layers applied. None if unreadable.
        Kept until the document or the picked type changes."""
        key: tuple[int, int] = (self.bench.revision, self.palette_type)
        if self._palette_memo is None or self._palette_memo[0] != key:
            try:
                values: dict[str, Any] | None = self.doc.effective(
                    TYPES[self.palette_type]
                )
            except (OSError, ValueError):
                values = None
            self._palette_memo = (key, values)
        return self._palette_memo[1]

    def variants(self) -> list[str]:
        """Variant names of the palette's drifter type, from the sandbox's effective values."""
        return list((self._palette_values() or {}).get("variants", {}))

    def default_variant(self) -> str:
        return str((self._palette_values() or {}).get("default_variant", ""))

    def press_at(self, pos: tuple[int, int]) -> bool:
        """A left click outside the game view: a row of a list, or a panel to focus. True if it
        hit something."""
        if self.prompt is not None or self.promote is not None:
            return False
        for area, kind, index in self.hits:
            if not area.collidepoint(pos):
                continue
            if kind == "wave":
                self.selected, self.focus = index, "wave"
                self.cursor = self._home()
            elif kind == "invert":
                self.toggle_invert()
                self.focus = "palette"
            elif kind == "row":
                rows: list[Row] = self.rows()
                if index < len(rows) and rows[index].key is not None:
                    self.cursor = index
                self.focus = "values"
            elif kind == "type":
                self._pick_type(index)
                self.focus, self.palette_side = "palette", "types"
                self._arm(self.default_variant() or None)
            else:
                self.palette_variant = index
                self.focus, self.palette_side = "palette", "variants"
                self._arm(self.variants()[index])
            return True
        for name, area in self.panels.items():
            if area.collidepoint(pos) and self._reachable()[name]:
                self.focus = name
                if name == "values" and (self.row() is None or self.row().key is None):  # type: ignore[union-attr]
                    self.cursor = self._home()
                return True
        return False

    def toggle_invert(self) -> None:
        """Flip the palette's invert switch. It applies to the next drifter placed."""
        self.invert = not self.invert
        self.message = (
            "new drifters are placed inverted" if self.invert else "invert off"
        )

    def toggle_at_spot(self) -> None:
        """Flip place by position. It applies to the next click with an armed drifter."""
        self.at_spot = not self.at_spot
        self.message = (
            "at spot: a click puts the drifter there at this moment"
            if self.at_spot
            else "at spot off: a click starts the drifter there"
        )

    def toggle_coin_top(self) -> None:
        """Flip the coin's from-the-top mode. It applies to the next coin placed."""
        self.coin_top = not self.coin_top
        self.message = (
            "coin from the top: it scrolls in from above, and at spot (P) it is on "
            "the spot at this moment"
            if self.coin_top
            else "coin from the top off: a coin appears where it is placed"
        )

    def from_top(self, drifter: str) -> bool:
        """True if `drifter` is placed from the top now: the mode is on and it has the mode."""
        return self.coin_top and drifter in FROM_TOP_FIELDS

    def _arm(self, variant: str | None) -> None:
        """Wait for a click in the game view to place the palette's drifter."""
        if self.doc.wave is None:
            self.message = "no wave to add to: open one with Ctrl+O first"
            return
        drifter: str = TYPES[self.palette_type]
        self.armed = (drifter, variant)
        self.message = ""

    def wheel_at(self, pos: tuple[int, int], dy: int) -> None:
        """Scroll the palette list under the mouse, or the Open list."""
        if self.picker is not None:
            view: OpenView = self.picker
            bottom: int = max(len(view.shown()) - view.rows, 0)
            view.top = min(max(view.top - dy, 0), bottom)
            return
        for kind, area in self.regions.items():
            if area.collidepoint(pos):
                count: int = len(TYPES) if kind == "type" else len(self.variants())
                top: int = max(count - PALETTE_ROWS, 0)
                self.scroll[kind] = min(max(self.scroll[kind] - dy, 0), top)

    def _pick_type(self, index: int) -> None:
        self.palette_type, self.palette_variant = index, 0
        self.scroll["variant"] = 0

    def _palette_key(self, key: int) -> bool:
        side: str = "type" if self.palette_side == "types" else "variant"
        count: int = len(TYPES) if side == "type" else len(self.variants())
        if key in (pygame.K_UP, pygame.K_DOWN) and count:
            step: int = 1 if key == pygame.K_DOWN else -1
            if side == "type":
                self._pick_type((self.palette_type + step) % count)
                now: int = self.palette_type
            else:
                self.palette_variant = now = (self.palette_variant + step) % count
            top: int = self.scroll[side]
            self.scroll[side] = min(max(top, now - PALETTE_ROWS + 1), now)
        elif key == pygame.K_RIGHT:
            self.palette_side = "variants"
        elif key == pygame.K_LEFT:
            self.palette_side = "types"
        elif key == pygame.K_RETURN:
            names: list[str] = self.variants()
            if self.palette_side == "variants" and names:
                self._add(names[self.palette_variant])
            else:
                self._add(self.default_variant() or None)
        else:
            return False
        return True

    def _add(
        self,
        variant: str | None,
        drifter: str | None = None,
        at: tuple[float, float] | None = None,
    ) -> None:
        """Add a drifter to the wave at the playhead, valid by the game's checks.

        `at` is a click in the game view: the drifter takes the coordinates it uses from it
        (CLICK_FIELDS). Without it the drifter gets the start values of START_FIELDS.
        """
        wave: dict[str, Any] | None = self.doc.wave
        if wave is None:
            self.message = "no wave to add to: open one with Ctrl+O first"
            return
        drifter = drifter or TYPES[self.palette_type]
        length: float = float(wave.get("length_px", SEAM_CLEAR_PX))
        into: float = self.bench.run.scroll.distance_px
        at_px: float = min(max(round(into / SNAP_PX) * SNAP_PX, SEAM_CLEAR_PX), length)
        error: Exception | None = None
        tries: tuple[dict[str, float], ...] = (
            (
                {
                    name: round(at["xy".index(name[0])])
                    for name in (
                        FROM_TOP_FIELDS if self.from_top(drifter) else CLICK_FIELDS
                    ).get(drifter, CLICK_FIELDS[drifter])
                },
            )
            if at is not None
            else START_FIELDS
        )
        # With the invert switch on, every way of placing is tried inverted first, then plain,
        # because a drifter that has no mirror (the game refuses invert) is placed as it is.
        combos: list[tuple[dict[str, float], bool]] = [
            *((extra, True) for extra in tries if self.invert),
            *((extra, False) for extra in tries),
        ]
        for extra, inverted in combos:
            item: dict[str, Any] = {"at_px": _tidy(at_px), "type": drifter, **extra}
            if variant:
                item["variant"] = variant
            if inverted:
                item["invert"] = True
            trial: dict[str, Any] = {
                **wave,
                "placements": [*wave.get("placements", []), item],
            }
            try:
                _build_wave(self.doc.wave_id, trial, self.bench.tuning)
            except ValueError as err:
                error = err
                continue
            break
        else:
            self.message = f"cannot add {drifter}: {error}"
            return

        if self._append(item):
            name: str = f"{drifter} {variant}" if variant else drifter
            if inverted:
                name += " (inverted)"
            elif self.invert:
                name += " (no invert for this drifter)"
            if at is not None:
                where: str = ", ".join(f"{k} {v:g}" for k, v in extra.items())
                self.message = (
                    f"placed {name} at {at_px:g} px, {where}. Esc stops placing"
                )
                return
            self.focus = "values"
            self.cursor = self._home()
            self.message = (
                f"added {name} at {at_px:g} px. Left/Right nudge, Enter types"
            )

    def _append(self, item: dict[str, Any]) -> bool:
        """Add `item` to the wave and select it. False: the game refused it."""

        def change(doc: Doc) -> None:
            assert doc.wave is not None
            doc.wave.setdefault("placements", []).append(item)
            doc.sort()
            self._held = item

        if not self.bench.edit(change):
            return False
        self.selected = next(
            i for i, q in enumerate(self.placements()) if q is self._held
        )
        return True

    def _add_at_spot(
        self, drifter: str, variant: str | None, at: tuple[float, float]
    ) -> None:
        """Add a drifter so that it is on `at` at the playhead's moment (place.py).

        The trigger and the coordinate it takes are worked out from its path, on a worker
        thread: a UFO's search can take seconds, and the window must not freeze meanwhile.
        A spot it can't pass at this moment is refused with the nearest one it can. With the
        invert switch on, a drifter that has no mirror is placed as it is.
        """
        wave: dict[str, Any] | None = self.doc.wave
        if wave is None:
            self.message = "no wave to add to: open one with Ctrl+O first"
            return
        if self.job is not None and not self.job.cancelled:
            self.message = f"still {self.job.label}: wait for it, or Esc to cancel"
            return
        moment: int = self.bench.run.scroll.scrolled_ticks
        if moment * scroll_speed(self.bench.level) > float(wave.get("length_px", 0)):
            self.message = "cannot place at spot: the playhead is past the wave's end"
            return
        placements: list[Any] = copy.deepcopy(list(wave.get("placements", [])))
        level, tuning = self.bench.level, self.bench.tuning
        ship, wave_id, invert = self.bench.run.ship, self.doc.wave_id, self.invert
        from_top: bool = self.from_top(drifter)
        job: Job | None = None

        def search() -> tuple[Placement, Spot] | str:
            """The spot, or the reason there is none. Runs on the worker thread."""
            error: Exception | None = None
            for inverted in (True, False) if invert else (False,):
                what: Placement = Placement(
                    drifter_type=DrifterType(drifter), variant=variant, invert=inverted
                )
                try:
                    return what, place_in_wave(
                        what,
                        at,
                        moment,
                        level,
                        tuning,
                        ship,
                        wave_id,
                        placements,
                        lambda: job is not None and job.cancelled,
                        self._scan_pool,
                        from_top,
                    )
                except Unreachable as err:
                    return f"cannot reach {at[0]:.0f}, {at[1]:.0f} now: {err}"
                except ValueError as err:
                    error = err
            return f"cannot add {drifter}: {error}"

        def finish(found: tuple[Placement, Spot] | str) -> None:
            if isinstance(found, str):
                self.message = found
                return
            what, spot = found
            item: dict[str, Any] = placement_item(what, spot)
            if not self._append(item):
                return
            name: str = f"{drifter} {variant}" if variant else drifter
            if what.invert:
                name += " (inverted)"
            elif self.invert:
                name += " (no invert for this drifter)"
            where: str = ", ".join(f"{k} {v:g}" for k, v in spot.fields.items())
            self.message = (
                f"placed {name} at {spot.at_px} px, {where}: on the spot now, "
                f"{spot.off_px:.1f} px off. Esc stops placing"
            )

        job = Job(
            f"finding a spot for {drifter}",
            self._worker.submit(search),
            finish,
            self.bench.revision,
        )
        self.job = job
        self.message = ""

    def poll_job(self) -> None:
        """Call once a frame: finish the search if it is done, on the main thread."""
        job: Job | None = self.job
        if job is None or not job.future.done():
            return
        self.job = None
        if job.cancelled:
            return
        try:
            found: Any = job.future.result()
        except Cancelled:
            return
        except Exception as err:  # noqa: BLE001 - a failed search must not kill the tool
            self.message = f"cannot place: {err}"
            return
        if job.revision != self.bench.revision:
            self.message = "the wave changed while searching: click the spot again"
            return
        job.finish(found)

    def close(self) -> None:
        """Stop the worker thread. The tool calls it on the way out."""
        if self.job is not None:
            self.job.cancelled = True
        self._worker.shutdown(wait=False, cancel_futures=True)
        self._scan_pool.close()

    def _reachable(self) -> dict[str, bool]:
        """Which panels can take the focus now."""
        return {
            "game": True,
            "wave": bool(self.placements()),
            "palette": self.doc.wave is not None,
            "values": bool(self.rows()),
        }

    def _next_focus(self, step: int) -> None:
        reachable: dict[str, bool] = self._reachable()
        usable: list[str] = [f for f in FOCUS_ORDER if reachable[f]]
        at: int = usable.index(self.focus) if self.focus in usable else 0
        self.focus = usable[(at + step) % len(usable)]
        row: Row | None = self.row()
        if self.focus == "values" and (row is None or row.key is None):
            self.cursor = self._home()

    def _wave_key(self, key: int) -> bool:
        items: list[dict[str, Any]] = self.placements()
        if key in (pygame.K_UP, pygame.K_DOWN) and items and self.selected is not None:
            self.selected = (self.selected + (1 if key == pygame.K_DOWN else -1)) % len(
                items
            )
            self.cursor = self._home()
            return True
        if key == pygame.K_DELETE and self.selected is not None:
            self._delete_placement(self.selected)
            return True
        return key in (pygame.K_LEFT, pygame.K_RIGHT)

    def _values_key(self, key: int, shift: bool) -> bool:
        rows: list[Row] = self.rows()
        if key in (pygame.K_UP, pygame.K_DOWN) and rows:
            step: int = 1 if key == pygame.K_DOWN else -1
            for _ in rows:
                self.cursor = (self.cursor + step) % len(rows)
                if rows[self.cursor].key is not None:
                    break
            return True
        if key in (pygame.K_RIGHT, pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self._nudge(1, shift and key == pygame.K_RIGHT)
        elif key in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
            self._nudge(-1, shift)
        elif key == pygame.K_RETURN:
            self._type_value()
        elif key == pygame.K_d:
            self._default()
        elif key == pygame.K_f:
            self._cycle_named()
        else:
            return False
        return True

    # ---- placements ---------------------------------------------------------------------

    def _set_field(self, name: str, value: object) -> bool:
        """Change one placement field. False if the game refused it (the change is undone)."""
        index: int | None = self.selected
        if index is None:
            return False

        def change(doc: Doc) -> None:
            assert doc.wave is not None
            item: dict[str, Any] = doc.wave["placements"][index]
            if value is REMOVE:
                item.pop(name, None)
            else:
                item[name] = _tidy(value)
            doc.sort()
            self._held = item

        if self.bench.edit(change):
            self.message = ""
            self.selected = next(
                i for i, q in enumerate(self.placements()) if q is self._held
            )
            return True
        return False

    def _set_wave_field(self, name: str, value: object) -> None:
        """Change one wave setting. A pool wave needs a min_level, a fixed wave has none."""

        def change(doc: Doc) -> None:
            assert doc.wave is not None
            if value is REMOVE:
                doc.wave.pop(name, None)
            else:
                doc.wave[name] = _tidy(value)
            if name == "kind":
                if value == "pool":
                    doc.wave.setdefault("min_level", 1)
                else:
                    doc.wave.pop("min_level", None)

        if self.bench.edit(change):
            self.message = ""

    def _delete_placement(self, index: int) -> None:
        if self.bench.edit(lambda doc: doc.wave["placements"].pop(index)):  # type: ignore[index]
            count: int = len(self.placements())
            self.selected = min(index, count - 1) if count else None
            self.cursor = self._home()
            self.message = "placement deleted (Ctrl+S saves the sandbox file)"

    def _set_hazard(self, name: str, value: object) -> None:
        """Change a shared hazard value. The game's loader checks it, and a refusal is undone."""
        if self.bench.edit(lambda doc: doc.set_hazard(name, _tidy(value))):
            self.message = ""

    def _set_value(self, drifter: str, path: Leaf, value: object) -> None:
        if self.bench.edit(lambda doc: doc.set_value(drifter, path, value)):
            self.message = ""

    # ---- editing a row ------------------------------------------------------------------

    def _current_value(self, row: Row) -> Any:
        placement: dict[str, Any] = self.current() or {}
        if row.key is None:
            return None
        if row.key[0] == "wave":
            return (self.doc.wave or {}).get(row.key[1], WAVE_DEFAULTS.get(row.key[1]))
        if row.key[0] == "hazard":
            return self.doc.effective_hazards().get(row.key[1])
        if row.key[0] == "field":
            name: str = row.key[1]
            return placement.get(
                name, NUDGE_START.get(name, False if name == "invert" else None)
            )
        _, drifter, path = row.key
        return get_leaf(self.doc.effective(drifter), path)

    def _nudge(self, direction: int, big: bool) -> None:
        row: Row | None = self.row()
        if row is None or row.key is None:
            return
        mult: int = 10 if big else 1
        value: Any = self._current_value(row)
        if row.key[0] == "wave":
            self._nudge_wave(row.key[1], value, direction, mult)
            return
        if row.key[0] == "hazard":
            self._set_hazard(
                row.key[1], max(float(value) + direction * HAZARD_STEP * mult, 1)
            )
            return
        if row.key[0] == "field":
            name: str = row.key[1]
            if name in ("at_px", "x", "y"):
                new: Any = round(float(value or 0) + direction * mult, 3)
                self._set_field(name, max(new, 0) if name == "at_px" else new)
            elif name == "invert":
                self._set_field(name, not bool(self.current().get("invert", False)))  # type: ignore[union-attr]
            elif name == "variant":
                self._set_field(name, self._next_variant(direction))
            else:
                self.message = "the type is fixed here (the palette comes with C-lite)"
            return
        _, drifter, path = row.key
        if isinstance(value, bool):
            self._set_value(drifter, path, not value)
        elif isinstance(value, int):
            self._set_value(drifter, path, value + direction * mult)
        elif isinstance(value, float):
            self._set_value(
                drifter, path, round(value + direction * FLOAT_STEP * mult, 6)
            )
        else:
            self.message = "press Enter to type this value"

    def _nudge_wave(self, name: str, value: Any, direction: int, mult: int) -> None:
        if name == "length_px":
            self._set_wave_field(
                name, max(float(value) + direction * LENGTH_STEP * mult, 1)
            )
        elif name == "kind":
            self._set_wave_field(name, "fixed" if value == "pool" else "pool")
        elif name == "min_level":
            if (self.doc.wave or {}).get("kind") != "pool":
                self.message = (
                    "min_level is for pool waves only: set kind to pool first"
                )
            else:
                self._set_wave_field(name, min(max(value + direction, 1), LEVEL_COUNT))
        else:
            self._set_wave_field(name, max(value + direction * mult, 0))

    def _next_variant(self, direction: int) -> str:
        placement: dict[str, Any] = self.current() or {}
        values: dict[str, Any] = self.doc.effective(str(placement.get("type")))
        names: list[str] = list(values.get("variants", {}))
        now: str = placement.get("variant") or values.get("default_variant", "")
        at: int = names.index(now) if now in names else 0
        return names[(at + direction) % len(names)]

    def _type_value(self) -> None:
        row: Row | None = self.row()
        if row is None or row.key is None:
            return
        value: Any = self._current_value(row)
        label: str = (
            row.label
            if row.key[0] != "value"
            else f"{row.key[1]}.{'.'.join(row.key[2])}"
        )
        shown: str = (
            ""
            if value is None
            else json.dumps(value)
            if isinstance(value, bool)
            else str(value)
        )

        def submit(text: str) -> None:
            try:
                parsed: Any = _parse(
                    text, value, row.key[1] if row.key[0] != "value" else ""
                )
            except ValueError as err:
                self.message = f"{label}: {err}"
                return
            if row.key[0] == "wave":
                self._set_wave_field(row.key[1], parsed)
            elif row.key[0] == "hazard":
                self._set_hazard(row.key[1], parsed)
            elif row.key[0] == "field":
                self._set_field(row.key[1], parsed)
            else:
                self._set_value(row.key[1], row.key[2], parsed)

        if row.key[0] == "field" and row.key[1] == "type":
            self.message = "the type is fixed here (the palette comes with C-lite)"
            return
        self.prompt = Prompt(f"{label} =", shown, submit)

    def _default(self) -> None:
        """D: put the row back to its default.

        A drifter value goes back to the tuning file (one layer down). A wave setting goes back to
        what a new wave gets. A placement's variant, invert and position go back to what the
        drifter's tuning decides; a position the drifter cannot pick for itself goes back to
        the start value a new placement gets.
        """
        row: Row | None = self.row()
        if row is None or row.key is None:
            return
        if row.key[0] == "wave":
            self._default_wave(row.key[1])
        elif row.key[0] == "hazard":
            result: list[str] = []
            if self.bench.edit(lambda doc: result.append(doc.drop_hazard(row.key[1]))):
                self.message = result[0]
        elif row.key[0] == "field":
            self._default_field(row.key[1])
        else:
            _, drifter, path = row.key
            dropped: list[str] = []
            if self.bench.edit(
                lambda doc: dropped.append(doc.step_down(drifter, path))
            ):
                self.message = dropped[0]

    def _default_wave(self, name: str) -> None:
        defaults: dict[str, object] = {
            "length_px": NEW_WAVE_LENGTH,
            "kind": "fixed",
            "min_level": 1,
            "extra_rest_ticks": REMOVE,
        }
        self._set_wave_field(name, defaults[name])

    def _default_field(self, name: str) -> None:
        drifter: str = str((self.current() or {}).get("type"))
        if name in ("x", "y"):
            if self._set_field(name, REMOVE):
                self.message = f"{name} back to {drifter}'s own start position"
            else:
                self.bench.error = ""
                start: float = NUDGE_START[name]
                if self._set_field(name, start):
                    self.message = (
                        f"{drifter} has no start {name} of its own: reset to {start:g}"
                    )
        elif name in OPTIONAL:
            if self._set_field(name, REMOVE):
                self.message = f"{name} back to the {drifter} tuning default"
        else:
            self.message = (
                f"{name} has no default: it is set by where the drifter should appear"
            )

    def _cycle_named(self) -> None:
        placement: dict[str, Any] | None = self.current()
        if placement is None:
            return
        drifter: str = str(placement.get("type"))
        options: list[str | None] = [None, *self.doc.named_files(drifter)]
        if len(options) == 1:
            self.message = f"no named file for {drifter}: V saves the values as one"
            return
        now: str | None = self.doc.named.get(drifter)
        nxt: str | None = options[
            (options.index(now) + 1) % len(options) if now in options else 1
        ]
        if self.bench.edit(lambda doc: doc.link_named(drifter, nxt)):
            self.message = f"{drifter} values from {nxt or 'production'}"

    def _save_values_as(self) -> None:
        placement: dict[str, Any] | None = self.current()
        if placement is None:
            return
        drifter: str = str(placement.get("type"))

        def submit(name: str) -> None:
            target: Path = doc_module.NAMED_DIR / f"{name}.json"
            if not NAME.fullmatch(name):
                self.message = (
                    "name: lower case letters, digits and _, starting with a letter"
                )
            elif target.exists():
                self.message = f"{name} exists, pick another name"
            else:
                values: dict[str, Any] = self.doc.effective(drifter)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")

                def link(doc: Doc) -> None:
                    doc.inline.pop(drifter, None)
                    doc.link_named(drifter, name)

                if self.bench.edit(link):
                    self.message = (
                        f"saved {drifter} values as sandbox/tuning/{name}.json (F)"
                    )

        self.prompt = Prompt(f"Save {drifter} values as", f"{drifter}_", submit)

    # ---- files --------------------------------------------------------------------------

    def _file_key(self, key: int, shift: bool) -> bool:
        if key == pygame.K_s and shift:
            self.save_as()
        elif key == pygame.K_s:
            self.save()
        elif key == pygame.K_n:
            self._new()
        elif key == pygame.K_o:
            self._open()
        elif key == pygame.K_p:
            self._open_promote()
        else:
            return False
        return True

    def save(self) -> None:
        if self.doc.path is None:
            self.save_as()
            return
        self._write(self.doc.path)

    def save_as(self) -> None:
        start: Path = self.doc.path or doc_module.SANDBOX_DIR / "new_wave.json"
        self.prompt = Prompt(
            "Save as", _relative(start), lambda text: self._write(_resolve(text))
        )

    def _write(self, path: Path) -> None:
        if path.suffix != ".json":
            self.message = "the file name must end in .json"
        elif doc_module.GAME_DIR.resolve() in path.resolve().parents:
            self.message = "this tool never writes under game/: use Promote (Ctrl+P)"
        else:
            self.doc.save(path)
            self.bench.rescan()
            self.message = f"saved {_relative(path)}"

    def _new(self) -> None:
        """Start an empty wave in the sandbox, after asking for its name."""

        def submit(name: str) -> None:
            target: Path = doc_module.SANDBOX_DIR / f"{name}.json"
            if not NAME.fullmatch(name):
                self.message = (
                    "name: lower case letters, digits and _, starting with a letter"
                )
            elif target.exists():
                self.message = f"{name} exists: open it with Ctrl+O"
            else:
                wave: dict[str, Any] = {
                    "length_px": NEW_WAVE_LENGTH,
                    "kind": "fixed",
                    "placements": [],
                }
                fresh: Doc = Doc(wave, path=target, dirty=True)
                if self.bench.load_doc(fresh):
                    self.armed = None
                    self.selected = None
                    self.cursor = self._home()
                    self.focus = "palette"
                    self.message = (
                        f"new wave {name}: pick a drifter and a variant to add it"
                    )

        label: str = (
            "New wave name (unsaved changes are dropped)"
            if self.doc.dirty
            else "New wave name"
        )
        self.prompt = Prompt(label, "new_wave", submit)

    def _open(self) -> None:
        """Show the Open list, the cursor on the file open now."""
        files: list[Path] = wave_files()
        view: OpenView = OpenView(files)
        here: Path | None = self.doc.source_file
        if here is not None and here.resolve() in [f.resolve() for f in files]:
            view.move([f.resolve() for f in files].index(here.resolve()))
        self.picker = view

    def _open_path(self, path: Path) -> None:
        try:
            opened: Doc = Doc.open(path)
        except (OSError, ValueError) as err:
            self.message = f"cannot open: {err}"
            return
        if self.bench.load_doc(opened):
            self.armed = None
            self.selected = 0 if self.placements() else None
            self.cursor = self._home()
            self.message = f"opened {_relative(path)}"

    def pick_at(self, pos: tuple[int, int]) -> None:
        """A click while the Open list shows: open the file of the row under it."""
        for area, kind, index in self.hits:
            if kind == "file" and area.collidepoint(pos) and self.picker is not None:
                path: Path = self.picker.shown()[index]
                self.picker = None
                self._open_path(path)
                return

    def _open_promote(self) -> None:
        try:
            items: list[promote.Item] = promote.plan(self.doc)
        except (OSError, ValueError) as err:
            self.message = f"promote: {err}"
            return
        if not items:
            self.message = "nothing to promote"
            return
        self.promote = PromoteView(items)

    # ---- prompt and promote keys --------------------------------------------------------

    def _prompt_key(self, event: pygame.event.Event) -> None:
        prompt: Prompt = self.prompt  # type: ignore[assignment]
        if event.key == pygame.K_ESCAPE:
            self.prompt = None
        elif event.key == pygame.K_RETURN:
            self.prompt = None
            self.message = ""
            prompt.submit(prompt.text.strip())
        elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_c:
            copy_text(prompt.text)
        elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_v:
            pasted: str = paste_text()
            prompt.text = (
                pasted if prompt.text == prompt.start else prompt.text + pasted
            )
        else:
            prompt.text = _edit_text(prompt.text, event)

    def _picker_key(self, event: pygame.event.Event) -> None:
        """Type to narrow the list, Ctrl+V pastes a name or path, Enter opens."""
        view: OpenView = self.picker  # type: ignore[assignment]
        ctrl: bool = bool(event.mod & pygame.KMOD_CTRL)
        shown: list[Path] = view.shown()
        if event.key == pygame.K_ESCAPE:
            self.picker = None
        elif event.key == pygame.K_RETURN:
            typed: Path = _resolve(view.text)
            path: Path | None = (
                typed
                if view.text and typed.is_file()
                else shown[view.cursor]
                if shown
                else None
            )
            if path is None:
                self.message = f"no wave matches '{view.text}'"
                return
            self.picker = None
            self._open_path(path)
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            view.move(1 if event.key == pygame.K_DOWN else -1)
        elif event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            view.move(view.rows if event.key == pygame.K_PAGEDOWN else -view.rows)
        elif ctrl and event.key == pygame.K_c and shown:
            copy_text(_relative(shown[view.cursor]))
            self.message = f"copied {_relative(shown[view.cursor])}"
        else:
            before: str = view.text
            view.text = _edit_text(view.text, event)
            if view.text != before:
                view.cursor = view.top = 0

    def _promote_key(self, event: pygame.event.Event) -> None:
        view: PromoteView = self.promote  # type: ignore[assignment]
        if event.key == pygame.K_ESCAPE:
            self.promote = None
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            view.cursor = (
                view.cursor + (1 if event.key == pygame.K_DOWN else -1)
            ) % len(view.items)
        elif event.key == pygame.K_SPACE:
            item: promote.Item = view.items[view.cursor]
            item.checked = not item.checked
        elif event.key == pygame.K_RETURN:
            self.promote = None
            self._finish_promote(view.items)

    def _finish_promote(self, items: list[promote.Item]) -> None:
        written: list[Path] = promote.write(items)
        if not written:
            self.message = "promote: nothing ticked, nothing written"
            return
        done: list[str] = [i.drifter for i in items if i.checked and i.drifter]
        hazards_done: bool = any(i.checked and i.hazards for i in items)

        def fold(doc: Doc) -> None:
            for drifter in done:
                doc.named.pop(drifter, None)
                doc.inline.pop(drifter, None)
            if hazards_done:
                doc.hazards.clear()

        self.bench.edit(fold)
        names: str = ", ".join(_relative(path) for path in written)
        self.message = f"promoted: {names}. Nothing is committed."


def _show(value: object) -> str:
    if value is None:
        return "default"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _parse(text: str, like: Any, field: str) -> Any:
    """Turn typed text into a value of the same kind as `like`. Raises ValueError."""
    if field == "invert" or isinstance(like, bool):
        if text.lower() in ("true", "yes", "1", "on"):
            return True
        if text.lower() in ("false", "no", "0", "off"):
            return False
        raise ValueError("type yes or no")
    if field in ("at_px", "x", "y", "length_px", "graze_margin") or isinstance(
        like, float
    ):
        try:
            return float(text)
        except ValueError:
            raise ValueError("not a number") from None
    if isinstance(like, int):
        try:
            return int(text)
        except ValueError:
            raise ValueError("not a whole number") from None
    return text


def wave_files() -> list[Path]:
    """Every wave file the editor can open: drafts, sandbox files, then the game's waves."""
    files: list[Path] = []
    for folder in OPEN_FOLDERS:
        files += sorted(
            path for path in folder.glob("*.json") if path.stem != PLAYLIST_NAME
        )
    return files


def paste_text() -> str:
    """The clipboard's first line, without quotes or a file:// prefix. Empty if none."""
    try:
        text: str = pygame.scrap.get_text()
    except pygame.error:
        return ""
    lines: list[str] = text.strip().splitlines()
    first: str = lines[0].strip().strip("'\"") if lines else ""
    return first.removeprefix("file://")


def copy_text(text: str) -> None:
    """Put `text` on the clipboard. Nothing happens where there is none."""
    try:
        pygame.scrap.put_text(text)
    except pygame.error:
        pass


def _edit_text(text: str, event: pygame.event.Event) -> str:
    """A line of typed text after one key: Backspace, Ctrl+V pastes, a printable adds."""
    if event.key == pygame.K_BACKSPACE:
        return text[:-1]
    if event.mod & pygame.KMOD_CTRL:
        return text + paste_text() if event.key == pygame.K_v else text
    if event.unicode and event.unicode.isprintable():
        return text + str(event.unicode)
    return text


def _resolve(text: str) -> Path:
    path: Path = Path(text).expanduser()
    return path if path.is_absolute() else ROOT / path


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _tidy(value: object) -> object:
    """A whole-number float is written as an integer, as the game's files do."""
    return int(value) if isinstance(value, float) and value.is_integer() else value


def _wave_show(wave: dict[str, Any], name: str) -> str:
    if name == "min_level" and name not in wave:
        return "-"
    return _show(wave.get(name))


def place_text(item: dict[str, Any]) -> str:
    """The coordinates a placement sets, e.g. 'x420' or 'x350 y180'. '-' if it sets none."""
    parts: list[str] = [f"{axis}{item[axis]:g}" for axis in ("x", "y") if axis in item]
    return " ".join(parts) or "-"
