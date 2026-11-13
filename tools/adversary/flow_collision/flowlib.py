"""Shared helpers for the flow and collision scripts: the kit, one app tick, the allowed screen changes, the flow checker."""

from contextlib import contextmanager
from dataclasses import replace

import paths  # noqa: F401  (puts game/ on sys.path)
from simkit import load_kit

from core.game_flow import (
    GameOverChoice,
    MenuItem,
    Screen,
    TickInput,
    add_flow_drifters,
    start_flow,
    step_flow,
)
from core.saves import (
    NICKNAME_CHARACTERS,
    NICKNAME_LENGTH,
    TOP_N,
    is_valid_nickname,
    picked_name,
    place_of,
)
from core.drifters.registry import drifter_class
from core.drifters.spawner import Placement, spawn_drifter
from core.ship import SPAWN_X, SPAWN_Y, Thrust
from gdd_rules import LIVES_START

KIT = load_kit()
S = Screen

ALLOWED = {
    S.MENU: {S.MENU, S.INSTRUCTIONS, S.LEADERBOARD, S.CREDITS, S.PLAYING},
    S.INSTRUCTIONS: {S.INSTRUCTIONS, S.MENU},
    S.LEADERBOARD: {S.LEADERBOARD, S.MENU},
    S.CREDITS: {S.CREDITS, S.MENU},
    S.PLAYING: {S.PLAYING, S.PAUSED, S.GAME_OVER},
    S.PAUSED: {S.PAUSED, S.PLAYING},
    S.GAME_OVER: {S.GAME_OVER, S.PLAYING, S.MENU},
}


def th(u=0, d=0, l=0, r=0):
    return Thrust(up=bool(u), down=bool(d), left=bool(l), right=bool(r))


def tick(flow, thrust=None, confirm=False, focus=False):
    """One app tick, as frame.py _run_ticks does it."""
    flow = step_flow(flow, TickInput(thrust=thrust or Thrust(), confirm=confirm, focus_lost=focus))
    return add_flow_drifters(flow, flow.run.wave_spawns_due, KIT.tuning)


def to_menu_ready(seed, saves=None):
    """A flow on the menu with all keys released."""
    f = start_flow(KIT.new_run(seed), saves)
    return tick(f)


# Placements to try for a drifter: free, x fixed, y fixed, both fixed.
SPAWN_POSITIONS = ((None, None), (SPAWN_X, None), (None, SPAWN_Y), (SPAWN_X, SPAWN_Y))


def spawn_first_valid(dtype, variant, level, seed=None):
    """Spawn one drifter of `dtype` and `variant`, or return None when no placement is accepted.

    The spawner raises ValueError for a coordinate a type refuses, so the four placements in
    SPAWN_POSITIONS are tried in order. `seed` goes to the types that take one.
    """
    seeded = drifter_class(dtype).seeded
    for x, y in SPAWN_POSITIONS:
        try:
            placement = Placement(dtype, x=x, y=y, variant=variant, seed=seed if seeded else None)
            return spawn_drifter(placement, level, KIT.tuning)
        except ValueError:
            continue
    return None


@contextmanager
def patched(module, name, replacement):
    """Swap `module.name` for `replacement` inside a `with` block, and always put the original back."""
    original = getattr(module, name)
    setattr(module, name, replacement)
    try:
        yield
    finally:
        setattr(module, name, original)


def with_lives(flow, lives):
    return replace(flow, run=replace(flow.run, lives=lives))


class Checker:
    """Checks every tick of a flow against the GDD invariants. Collects violations (not raises)."""

    def __init__(self, label):
        self.label = label
        self.viol = []
        self.saves_written = 0
        self.runs_saved = {}
        self.run_id = 0
        self.t = 0

    def bad(self, kind, msg):
        self.viol.append((kind, f"[{self.label} t={self.t}] {msg}"))

    def check(self, prev, keys, new):
        """prev,new: flows around one tick (after add_flow_drifters); keys: TickInput."""
        self.t += 1
        ps, ns = prev.screen, new.screen
        # transition table
        if ns not in ALLOWED[ps]:
            self.bad("transition", f"{ps.value}->{ns.value}")
        confirm_press = keys.confirm and not prev.confirm_held
        # conditions
        if ps != ns:
            if ps == S.MENU and not confirm_press:
                self.bad("transition", "menu left without confirm press")
            if ps in (S.INSTRUCTIONS, S.LEADERBOARD, S.CREDITS) and not confirm_press:
                self.bad("transition", "page left without confirm press")
            if ps == S.PLAYING and ns == S.PAUSED:
                if not (confirm_press or keys.focus_lost):
                    self.bad("transition", "paused without cause")
                if prev.run.last_life:
                    self.bad("transition", "paused during last life")
            if ps == S.PLAYING and ns == S.GAME_OVER:
                if not (prev.run.last_life and new.run.game_over):
                    self.bad("transition", "game over without last life burst finished")
            if ps == S.PAUSED and ns == S.PLAYING and not confirm_press:
                self.bad("transition", "resume without press")
            if ps == S.GAME_OVER:
                if not confirm_press or prev.picking:
                    self.bad("transition", f"left game over confirm={confirm_press} picking={prev.picking}")
                want = S.PLAYING if prev.game_over_selection == GameOverChoice.RETRY else S.MENU
                if ns != want:
                    self.bad("transition", f"game over sel={prev.game_over_selection} -> {ns}")
        # never-happen: pause not entered when it should (confirm press in PLAYING not last life)
        if ps == S.PLAYING and not prev.run.last_life and (confirm_press or keys.focus_lost) and ns != S.PAUSED:
            self.bad("transition", "pause key ignored in playing")
        if ps == S.PLAYING and prev.run.last_life and (confirm_press or keys.focus_lost) and ns == S.PAUSED:
            self.bad("transition", "pause in last life")
        # frozen run
        if ps == S.PAUSED and ns == S.PAUSED:
            if replace(new.run, held=prev.run.held) != replace(prev.run, held=prev.run.held):
                self.bad("frozen", "run changed while paused")
        if ps == S.PAUSED and ns == S.PLAYING:
            if replace(new.run, held=prev.run.held) != replace(prev.run, held=prev.run.held):
                self.bad("frozen", "run changed on resume tick")
        if ps == S.GAME_OVER and ns == S.GAME_OVER and new.run != prev.run:
            self.bad("frozen", "run changed on game over")
        if ps in (S.MENU, S.INSTRUCTIONS, S.LEADERBOARD, S.CREDITS) and ns == ps and new.run != prev.run:
            self.bad("frozen", f"run changed on {ps.value}")
        if ps == S.PAUSED and new.run_stepped:
            self.bad("frozen", "run_stepped on paused")
        # run_stepped correct
        if ps == S.PLAYING and ns in (S.PLAYING, S.GAME_OVER):
            if not new.run_stepped:
                self.bad("stepped", "playing tick did not step")
        elif new.run_stepped:
            self.bad("stepped", f"run_stepped on {ps.value}->{ns.value}")
        # fresh run on new run entry
        if (ps in (S.MENU, S.GAME_OVER)) and ns == S.PLAYING:
            r = new.run
            ok = (
                r.lives == LIVES_START
                and r.score == 0
                and r.level == 1
                and not r.drifters
                and not r.waiting
                and not r.game_over
                and r.burst is None
                and r.final_score is None
                and r.scroll.ticks == 0
                and r.grazes == 0
                and r.coin_points == 0
                and r.invuln_ticks_left == 0
                and not r.popups
                and not r.graze_rings
                and r.level_up is None
                and r.ship.x == 320
                and r.ship.y == 240
                and (r.waves is None or (r.waves.level == 1))
            )
            if not ok:
                self.bad(
                    "fresh", f"new run not fresh lives={r.lives} score={r.score} lvl={r.level} dr={len(r.drifters)}"
                )
            if r.graze_rules != KIT.graze_rules or r.last_life_rules != KIT.last_life_rules:
                self.bad("fresh", "rules lost on new run")
            self.run_id += 1
        # run invariants
        r = new.run
        if not 0 <= r.lives <= LIVES_START:
            self.bad("run", f"lives {r.lives}")
        if r.lives > prev.run.lives and ps in (S.PLAYING, S.PAUSED) and ns != S.PLAYING:
            self.bad("run", "life gained")
        if ps in (S.PLAYING,) and ns in (S.PLAYING, S.GAME_OVER):
            if r.lives > prev.run.lives:
                self.bad("run", "life gained")
            if r.score < prev.run.score:
                self.bad("run", f"score dropped {prev.run.score}->{r.score}")
            if r.level_reached < prev.run.level_reached:
                self.bad("run", "level dropped")
            if prev.run.last_life and r.score != prev.run.score:
                self.bad("run", "score changed during last life")
            if prev.run.last_life and r.level_reached != prev.run.level_reached:
                self.bad("run", "level_reached changed during last life")
        if r.burst is not None and r.lives != 0:
            self.bad("run", "burst with lives")
        if r.lives == 0 and r.burst is None and ns != S.MENU:
            self.bad("run", "0 lives, no burst")
        # game over open
        if ps == S.PLAYING and ns == S.GAME_OVER:
            if new.game_over_selection != GameOverChoice.RETRY:
                self.bad("gameover", "selection not RETRY")
            if new.run.score != new.run.final_score:
                self.bad("gameover", "score != final_score")
            if new.saves is not None:
                place = place_of(new.saves, r.score, r.level_reached)
                if (place is not None) != (new.picker is not None) or new.picking != (new.picker is not None):
                    self.bad("gameover", f"picker/place mismatch place={place} picker={new.picker is not None}")
            elif new.picker is not None or new.picking:
                self.bad("gameover", "picker without saves")
            if new.saves is not None and new.saves.last_nickname is not None and new.picker is not None:
                if "".join(new.picker.slots).rstrip(" ") != new.saves.last_nickname or new.picker.cursor != 0:
                    self.bad("gameover", "picker not prefilled with last_nickname")
        if ps == S.GAME_OVER and ns == S.GAME_OVER:
            if new.game_over_message != prev.game_over_message:
                self.bad("gameover", "message changed")
            if prev.picking and not new.picking and not (confirm_press):
                self.bad("gameover", "picker closed without confirm")
        # picker invariants
        p = new.picker
        if p is not None:
            if (
                len(p.slots) != NICKNAME_LENGTH
                or not 0 <= p.cursor < NICKNAME_LENGTH
                or any(c not in NICKNAME_CHARACTERS for c in p.slots)
            ):
                self.bad("picker", f"bad picker {p}")
        # keys while picking don't reach choices
        if ps == S.GAME_OVER and prev.picking and ns == S.GAME_OVER and new.picking:
            if new.game_over_selection != prev.game_over_selection:
                self.bad("picker", "selection moved while picking")
        # saves
        if new.saves_changed:
            self.runs_saved[self.run_id] = self.runs_saved.get(self.run_id, 0) + 1
            if self.runs_saved[self.run_id] > 1:
                self.bad("saves", "run saved more than once")
            self.saves_written += 1
            if ps != S.GAME_OVER:
                self.bad("saves", "saved outside game over")
            if new.saves is None:
                self.bad("saves", "saves_changed with no saves")
            else:
                if new.saves.last_nickname is None or not is_valid_nickname(new.saves.last_nickname):
                    self.bad("saves", "bad last_nickname")
        if ps == S.GAME_OVER and prev.picking and not new.picking and ns == S.GAME_OVER and confirm_press:
            nm = picked_name(prev.picker)
            if nm and prev.saves is not None and not new.saves_changed:
                self.bad("saves", "name confirmed, nothing saved")
            if not nm and new.saves_changed:
                self.bad("saves", "empty name saved")
            if not nm and new.saves is not None and new.saves.last_nickname != prev.saves.last_nickname:
                self.bad("saves", "empty name changed last_nickname")
        if not new.saves_changed and prev.saves is not None and new.saves is not None and new.saves != prev.saves:
            self.bad("saves", "saves changed without saves_changed")
        if new.saves is not None:
            es = new.saves.entries
            if len(es) > TOP_N:
                self.bad("saves", "more than 10 entries")
            for i, e in enumerate(es):
                if not is_valid_nickname(e.nickname) or e.score < 0 or not 1 <= e.level_reached <= 8:
                    self.bad("saves", f"bad entry {e}")
                if i and not (
                    es[i - 1].score > e.score
                    or (es[i - 1].score == e.score and es[i - 1].level_reached >= e.level_reached)
                ):
                    self.bad("saves", f"unsorted at {i}")
            if es and new.saves.best != es[0].score:
                self.bad("saves", "best != top")
            if new.best != (es[0].score if es else None):
                self.bad("saves", "flow.best mismatch")
        # whole-saves identity outside game over
        if ps != S.GAME_OVER and new.saves != prev.saves:
            self.bad("saves", "saves changed outside game over")
        # confirm held through screen change must not double fire: any tick changes at most one screen (implicit)
        # menu selection reset
        if ns == S.MENU and ps != S.MENU and new.menu_selection != MenuItem.PLAY:
            self.bad("menu", "menu not opened on PLAY")
        # entries of saves for one run saved at most once
        if new.saves_changed and prev.saves is not None:
            if len(new.saves.entries) != min(len(prev.saves.entries) + 1, TOP_N):
                self.bad("saves", "entries count did not grow by 1 (or cap)")
