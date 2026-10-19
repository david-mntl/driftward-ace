"""The bench: the game's own sim, run tool-side with a timeline and hot reload. No pygame.

Plays one source on the fixed 60 Hz tick through the game's `step_run` and `add_drifters`, in the
same order as `app.frame`. The source is one wave file or the debug spawn list. Reads the game
read-only. Every tick's thrust is recorded, so a scrub restores the nearest snapshot and replays
to the exact same state.
"""

import tempfile
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import doc as doc_module
from app import tuning as tuning_module
from app.debug_spawns import DebugSpawnList, debug_spawns_due, load_debug_spawns
from app.tuning import load_tuning
from core.drifters.base import Phase, TickContext
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning
from core.levels import FIRST_LEVEL, LEVEL_COUNT
from core.run import Run, add_drifters, start_run, step_run
from core.scroll import SCROLL_START_DELAY, scroll_speed
from core.ship import SPAWN_Y, Ship, Thrust
from core.wave_files import _build_wave
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, start_waves
from doc import Doc

SNAPSHOT_TICKS: int = 60
"""A Run snapshot is kept every this many ticks."""

GHOST_X: dict[str, float] = {"L": 100.0, "C": 320.0, "R": 540.0}
"""Where the ghost stands, by start spot. Screen px."""

LIST_LENGTH_PX: float = 1e12
"""Length of the blank wave under the spawn list. Never reached."""

NO_THRUST: Thrust = Thrust()

PREVIEW_TICKS: int = 1200
"""A path preview stops after this many ticks if the drifter never leaves."""


class Bench:
    """One document, one level, one timeline."""

    def __init__(self, doc: Doc) -> None:
        self.doc: Doc = doc
        self.level: int = FIRST_LEVEL
        self.ghost: bool = True
        self.spot: str = "C"
        self.loop: bool = True
        self.error: str = ""
        self.ended: bool = False
        self._preview: tuple[
            tuple[int, ...] | None, tuple[tuple[float, float, bool], ...]
        ] = (None, ())
        self.tuning: DrifterTuning
        self.wave: Wave
        self.spawn_list: DebugSpawnList | None
        self.tuning, self.wave, self.spawn_list = self._build()
        self._mtimes: dict[Path, float] = self._scan()
        self.restart()

    # ---- source -------------------------------------------------------------------------

    def _build(self) -> tuple[DrifterTuning, Wave, DebugSpawnList | None]:
        """Check the document with the game's own loaders. Raises on any problem."""
        tuning: DrifterTuning = load_merged(self.doc)
        if self.doc.wave is None:
            return tuning, _blank_wave(), load_debug_spawns(tuning)
        return tuning, _build_wave(self.doc.wave_id, self.doc.wave, tuning), None

    def _transaction(self, change: Callable[[], None]) -> bool:
        """Apply `change` to the document and rebuild. On any error the document and the old
        values stay, the message shows, and False comes back."""
        saved = self.doc.snapshot()
        try:
            change()
            self.tuning, self.wave, self.spawn_list = self._build()
        except Exception as err:  # noqa: BLE001 - any bad file or value must not kill the tool
            self.doc.restore(saved)
            self.error = str(err)
            return False
        self.error = ""
        self._mtimes = self._scan()
        self.replay_to(self.pos)
        return True

    def edit(self, change: Callable[[Doc], None]) -> bool:
        """Edit the document, check it, replay to the current tick. False: refused, undone."""
        ok: bool = self._transaction(lambda: change(self.doc))
        if ok:
            self.doc.dirty = True
        return ok

    def load_doc(self, doc: Doc) -> bool:
        """Switch to another document, from tick 0. False: refused, the old one stays."""
        old: Doc = self.doc

        def swap() -> None:
            self.doc = doc

        if not self._transaction(swap):
            self.doc = old
            return False
        self.restart()
        return True

    @property
    def length_px(self) -> float:
        """Length of the loop, px of scroll."""
        if self.spawn_list is not None:
            return self.spawn_list.loop_ticks * scroll_speed(self.level)
        assert self.wave is not None
        return self.wave.length_px

    @property
    def total_ticks(self) -> int:
        """Length of the loop, ticks at the chosen level."""
        if self.spawn_list is not None:
            return self.spawn_list.loop_ticks
        return SCROLL_START_DELAY + max(
            1, round(self.length_px / scroll_speed(self.level))
        )

    # ---- timeline -----------------------------------------------------------------------

    def restart(self) -> None:
        """Back to tick 0 with no recorded input."""
        self.inputs: list[Thrust] = []
        self.pos: int = 0
        self.ended = False
        self.snapshots: dict[int, Run] = {0: self._new_run()}
        self.run: Run = self.snapshots[0]

    def _new_run(self) -> Run:
        assert self.wave is not None
        book: WaveBook = WaveBook(
            waves={
                self.wave.wave_id: replace(self.wave, kind=WaveKind.POOL, min_level=1)
            },
            wave_zero_id=self.wave.wave_id,
            playlists=(LevelPlaylist(),) * LEVEL_COUNT,
        )
        waves = replace(start_waves(book, 0), level=self.level)
        return self._pin(start_run(waves=waves))

    @property
    def tick(self) -> int:
        """Ticks played on the timeline. A retry in fly mode resets the run's own tick count."""
        return self.pos

    def _pin(self, run: Run) -> Run:
        """Ghost: hold the ship at the start spot, invulnerable and alive, every tick."""
        if not self.ghost:
            return run
        ship: Ship = Ship(x=GHOST_X[self.spot], y=SPAWN_Y, vx=0.0, vy=0.0)
        return replace(
            run, ship=ship, lives=3, game_over=False, waiting=False, invuln_ticks_left=2
        )

    def _tick(self, run: Run, thrust: Thrust) -> Run | None:
        """One tick, in app.frame's order. None when the wave ended on this tick."""
        run = step_run(run, thrust)
        waves = run.waves
        assert waves is not None
        if waves.resting or waves.start_px != 0.0 or waves.level != self.level:
            return None
        due: tuple[Placement, ...]
        if self.spawn_list is not None:
            due = debug_spawns_due(self.spawn_list, run.scroll.ticks)
        else:
            due = run.wave_spawns_due
        return self._pin(add_drifters(run, due, self.tuning))

    def step(self, thrust: Thrust = NO_THRUST) -> None:
        """Advance one tick at the head of the timeline, recording the thrust."""
        if self.ended:
            return
        nxt: Run | None = self._tick(self.run, thrust)
        if nxt is None:
            if self.loop:
                self.restart()
            else:
                self.ended = True
            return
        self.inputs.append(thrust)
        self.pos += 1
        self.run = nxt
        if self.pos % SNAPSHOT_TICKS == 0:
            self.snapshots[self.pos] = nxt

    def seek(self, target: int) -> None:
        """Go to `target` ticks: the nearest snapshot at or before it, then replay.

        Past the recorded ticks it plays on with no thrust, recording it.
        """
        target = max(0, target)
        head: int = len(self.inputs)
        base: int = max(t for t in self.snapshots if t <= min(target, head))
        self.run = self.snapshots[base]
        self.pos = base
        self.ended = False
        for index in range(base, min(target, head)):
            nxt = self._tick(self.run, self.inputs[index])
            if nxt is None:
                break
            self.run = nxt
            self.pos = index + 1
        if target > head and self.pos == head:
            self._fill_to(target)

    def _fill_to(self, target: int) -> None:
        """Play ahead with no thrust to `target`, recording it."""
        while self.pos < target and not self.ended:
            before: int = self.pos
            self.step()
            if self.pos < before:
                break

    # ---- path preview -------------------------------------------------------------------

    def preview_path(self, index: int) -> tuple[tuple[float, float, bool], ...]:
        """Where the drifter of wave placement `index` goes, as (x, y, active) per tick.

        Plays that one drifter alone with the ship held where it is now and the world scrolling
        at the chosen level, until it leaves the screen. Drifters that follow the ship follow
        this fixed ship. Empty if the placement does not spawn.
        """
        ship: Ship = self.run.ship
        key: tuple[int, int, int, int, int] = (
            index,
            self.level,
            round(ship.x),
            round(ship.y),
            id(self.wave),
        )
        if self._preview[0] == key:
            return self._preview[1]
        points: list[tuple[float, float, bool]] = []
        try:
            ctx: TickContext = TickContext(
                ship=ship, scroll_step_px=scroll_speed(self.level)
            )
            drifter = spawn_drifter(
                self.wave.placements[index].placement, self.level, self.tuning
            ).settle_warning(ctx)
            points.append((drifter.x, drifter.y, False))
            for _ in range(PREVIEW_TICKS):
                drifter = drifter.update(ctx).mark_entered()
                points.append((drifter.x, drifter.y, drifter.phase is Phase.ACTIVE))
                if drifter.phase is Phase.GONE or (
                    drifter.has_entered and not drifter.is_partly_on_screen()
                ):
                    break
        except (ValueError, IndexError):
            points = []
        self._preview = (key, tuple(points))
        return self._preview[1]

    # ---- config -------------------------------------------------------------------------

    def set_level(self, level: int) -> None:
        self.level = min(max(level, FIRST_LEVEL), LEVEL_COUNT)
        self.restart()

    def toggle_ghost(self) -> None:
        self.ghost = not self.ghost
        self.restart()

    def set_spot(self, spot: str) -> None:
        self.spot = spot
        self.restart()

    # ---- hot reload ---------------------------------------------------------------------

    def _scan(self) -> dict[Path, float]:
        """Modified time of every production tuning file, named tuning file and the source file."""
        files: list[Path] = sorted(tuning_module.TUNING_DIR.rglob("*.json"))
        if doc_module.NAMED_DIR.exists():
            files += sorted(doc_module.NAMED_DIR.glob("*.json"))
        if self.doc.source_file is not None:
            files.append(self.doc.source_file)
        return {path: path.stat().st_mtime for path in files if path.exists()}

    def rescan(self) -> None:
        """Take the files' current modified times as seen, e.g. after the tool saved one."""
        self._mtimes = self._scan()

    def poll(self) -> bool:
        """Reload when a watched file changed. True if the bench reloaded.

        A bad file keeps the old values and shows the error. The document's own file is read
        again only while it has no unsaved edits.
        """
        seen: dict[Path, float] = self._scan()
        if seen == self._mtimes:
            return False
        source: Path | None = self.doc.source_file
        source_changed: bool = source in seen and seen[source] != self._mtimes.get(
            source
        )
        self._mtimes = seen

        def reload() -> None:
            if source_changed and not self.doc.dirty:
                self.doc.reload_from_source()

        return self._transaction(reload)

    def replay_to(self, target: int) -> None:
        """Rebuild the timeline from tick 0 with the recorded inputs, up to `target`."""
        recorded: list[Thrust] = self.inputs
        self.restart()
        for thrust in recorded[:target]:
            before: Run = self.run
            nxt = self._tick(before, thrust)
            if nxt is None:
                break
            self.inputs.append(thrust)
            self.pos += 1
            self.run = nxt
            if self.pos % SNAPSHOT_TICKS == 0:
                self.snapshots[self.pos] = nxt
        self.inputs.extend(recorded[len(self.inputs) :])


def _blank_wave() -> Wave:
    """The wave under the spawn list: no drifters, never ends."""
    return Wave(
        wave_id="bench_blank", length_px=LIST_LENGTH_PX, kind=WaveKind.POOL, min_level=1
    )


def load_merged(doc: Doc) -> DrifterTuning:
    """Load the drifter tuning with the document's layers over production.

    Writes the merged tuning folder to a temp dir and calls the game's `load_tuning()` on it, so
    the game's own checks validate every value.
    """
    production: Path = tuning_module.TUNING_DIR
    with tempfile.TemporaryDirectory() as folder:
        merged: Path = Path(folder) / "tuning"
        doc.write_merged_dir(merged)
        tuning_module.TUNING_DIR = merged
        try:
            return load_tuning()
        finally:
            tuning_module.TUNING_DIR = production
