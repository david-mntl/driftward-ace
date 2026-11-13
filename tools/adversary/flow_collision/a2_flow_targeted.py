"""Targeted flow scenarios. Prints PASS/FAIL per scenario; failures go to out/flow_collision/a2_targeted.txt."""

import random
from dataclasses import replace

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT, S, th, tick, to_menu_ready, with_lives
from core.game_flow import GameOverChoice, MenuItem, start_flow
from core.saves import NICKNAME_CHARACTERS, Saves, ScoreEntry, is_valid_nickname
from gdd_rules import LIVES_START, SPAWN_X, SPAWN_Y
from scenarios import Suite
from core.saves import GameOverMessage, message_for, place_of, add_entry

SUITE = Suite("a2_targeted.txt")
case = SUITE.case


def play_flow(saves=None, seed=3):
    """Flow in PLAYING, all keys released, fresh run."""
    f = to_menu_ready(seed, saves)
    f = tick(f, confirm=True)
    f = tick(f)
    assert f.screen == S.PLAYING
    return f


def run_n(f, n, **kw):
    for _ in range(n):
        f = tick(f, **kw)
    return f


def to_game_over(f, keys=None):
    """Force lives=1 then fall until GAME_OVER (down held)."""
    f = with_lives(f, 1)
    for _ in range(3000):
        f = tick(f, keys or th(d=1))
        if f.screen == S.GAME_OVER:
            return f
        if f.screen == S.PAUSED:
            f = tick(f)
            f = tick(f, confirm=True)
            f = tick(f)
    raise RuntimeError("no game over")


# ---- pause on every screen
@case("focus_lost on menu/pages/credits does nothing")
def _():
    m = []
    for item, scr in [(0, S.MENU), (1, S.INSTRUCTIONS), (2, S.LEADERBOARD), (3, S.CREDITS)]:
        g = to_menu_ready(1)
        for _ in range(item):
            g = tick(g, th(d=1))
            g = tick(g)
        if item:
            g = tick(g, confirm=True)
            g = tick(g)
        if g.screen != scr:
            m.append(f"could not reach {scr}")
            continue
        before = g
        h = tick(g, focus=True)
        if h.screen != scr or h.run != before.run:
            m.append(f"focus changed {scr}")
    return m


@case("focus_lost on game over (picking and choices) does nothing")
def _():
    m = []
    for saves in (Saves(), None):
        f = to_game_over(play_flow(saves))
        h = tick(f, focus=True)
        if h.screen != S.GAME_OVER or h.run != f.run or h.picking != f.picking:
            m.append(f"changed saves={saves}")
        if f.picking:
            f = tick(f, confirm=True)
            f = tick(f)
            h = tick(f, focus=True)
            if h.screen != S.GAME_OVER:
                m.append("changed after name")
    return m


@case("pause on every run phase")
def _():
    m = []
    # plain playing: focus pauses; confirm pauses; both freeze
    for how in ("focus", "confirm"):
        f = play_flow()
        f = run_n(f, 10)
        g = tick(f, focus=(how == "focus"), confirm=(how == "confirm"))
        if g.screen != S.PAUSED:
            m.append(f"{how} did not pause playing")
        if g.run != f.run and replace(g.run, held=f.run.held) != f.run:
            m.append(f"{how}: run changed on pause tick")
        # frozen for 300 ticks with all inputs
        rng = random.Random(1)
        h = g
        for _i in range(300):
            h = tick(h, th(*[rng.random() < 0.5 for _ in range(4)]), confirm=False, focus=rng.random() < 0.3)
        if h.screen != S.PAUSED or replace(h.run, held=g.run.held) != replace(g.run, held=g.run.held):
            m.append(f"{how}: pause not frozen")
    # invulnerability frozen: invuln_ticks_left unchanged
    f = play_flow()
    f = replace(f, run=replace(f.run, invuln_ticks_left=40))
    g = tick(f, focus=True)
    h = run_n(g, 100)
    if h.run.invuln_ticks_left != 40:
        m.append("invuln moved in pause")
    # respawn wait frozen
    f = play_flow()
    f = with_lives(f, 3)
    f = run_n(f, 400, thrust=None) if False else f
    # fall: down held
    for _ in range(600):
        f = tick(f, th(d=1))
        if f.run.waiting:
            break
    else:
        m.append("no fall wait reached")
    if f.run.waiting:
        g = tick(f, focus=True)
        if g.screen != S.PAUSED:
            m.append("wait: no pause")
        h = run_n(g, 50, thrust=th(l=1))
        if h.run.waiting is not True or h.run.ship != g.run.ship:
            m.append("wait changed in pause")
        # resume with arrow held during pause -> not a press
        h = tick(h, th(l=1), confirm=True)  # resume tick (fresh press needs release before)
    # level-up banner: pause during banner freezes the age
    f = play_flow(seed=7)
    for i in range(20000):
        f = tick(f, th(u=(i // 40) % 2 == 0, l=(i // 90) % 2 == 0))
        if f.screen != S.PLAYING:
            break
        if f.run.level_up is not None:
            break
        if f.run.lives < 3:
            f = with_lives(f, 5)
    if f.screen == S.PLAYING and f.run.level_up is not None:
        g = tick(f, focus=True)
        a = g.run.level_up.age_ticks
        g = run_n(g, 30)
        if g.run.level_up.age_ticks != a:
            m.append("banner aged in pause")
    else:
        m.append("INFO: banner never reached (skipped)")
    return m


@case("last life: focus_lost and confirm do not pause; game over tick with focus")
def _():
    m = []
    f = play_flow()
    f = with_lives(f, 1)
    for _ in range(3000):
        f = tick(f, th(d=1))
        if f.run.last_life:
            break
    if not f.run.last_life:
        return ["no last life"]
    t = 0
    while f.screen == S.PLAYING:
        f = tick(f, focus=(t % 3 == 0), confirm=(t % 2 == 0))
        t += 1
        if t > 400:
            return ["last life never ended"]
    if f.screen != S.GAME_OVER:
        m.append(f"went to {f.screen}")
    if t != 120 and t != 121:
        m.append(f"INFO burst length ticks={t}")
    return m


@case("focus_lost on the exact tick lives reach 0 / tick before / tick of game over")
def _():
    m = []
    # sweep: focus_lost at every offset around the death
    for off in range(-3, 4):
        f = with_lives(play_flow(), 1)
        for _ in range(3000):
            probe = tick(f, th(d=1))
            if probe.run.last_life:
                break
            f = probe
        # f is the tick before the death
        g = f
        for k in range(-3, 4):
            if k == off:
                g = tick(g, th(d=1), focus=True)
            else:
                g = tick(g, th(d=1))
            if g.screen == S.PAUSED:
                g = tick(g)
                g = tick(g, confirm=True)
                g = tick(g)  # resume
        # run on until game over
        for _ in range(400):
            if g.screen == S.GAME_OVER:
                break
            g = tick(g, th(d=1))
        if g.screen != S.GAME_OVER:
            m.append(f"off={off} never game over ({g.screen})")
    return m


# ---- confirm held across a screen change
@case("confirm held across every screen change does not double fire")
def _():
    m = []
    # menu Play held 200 ticks -> PLAYING, no pause
    f = to_menu_ready(2)
    f = tick(f, confirm=True)
    if f.screen != S.PLAYING:
        m.append("play did not start")
    f = run_n(f, 200, confirm=True)
    if f.screen != S.PLAYING:
        m.append("play->pause with key held")
    f = tick(f)
    f = tick(f, confirm=True)
    if f.screen != S.PAUSED:
        m.append("fresh press did not pause")
    f = run_n(f, 100, confirm=True)
    if f.screen != S.PAUSED:
        m.append("resumed with key held")
    # menu -> page -> must not return while held
    for sel in range(1, 4):
        f = to_menu_ready(2)
        for _ in range(sel):
            f = tick(f, th(d=1))
            f = tick(f)
        f = tick(f, confirm=True)
        if f.screen == S.MENU:
            m.append("did not open page")
            continue
        f = run_n(f, 50, confirm=True)
        if f.screen == S.MENU:
            m.append(f"page {sel} closed with key held")
        f = tick(f)
        f = tick(f, confirm=True)
        if f.screen != S.MENU:
            m.append(f"page {sel} did not close on fresh press")
        # menu back: held through, still menu with PLAY selected
        f = run_n(f, 50, confirm=True)
        if f.screen != S.MENU:
            m.append("menu fired with key held after page")
        if f.menu_selection != MenuItem.PLAY:
            m.append("menu not on PLAY after page")
    # game over: name confirm held -> RETRY not fired; retry held -> no pause
    f = to_game_over(play_flow(Saves()))
    if not f.picking:
        return m + ["no picker"]
    f = tick(f)
    f = tick(f, confirm=True)
    if f.picking:
        m.append("name not confirmed")
    f = run_n(f, 100, confirm=True)
    if f.screen != S.GAME_OVER:
        m.append("retry fired with confirm still held from name")
    f = tick(f)
    f = tick(f, confirm=True)
    if f.screen != S.PLAYING:
        m.append("retry not fired on press")
    f = run_n(f, 100, confirm=True)
    if f.screen != S.PLAYING:
        m.append("paused on retry with key held")
    # confirm mashed through the burst: first tick of game over must not act
    g = with_lives(play_flow(Saves()), 1)
    for _ in range(3000):
        g = tick(g, th(d=1), confirm=g.run.last_life and (g.run.burst.age_ticks % 2 == 0))
        if g.screen == S.GAME_OVER:
            break
    if g.screen != S.GAME_OVER:
        m.append("no game over (mash)")
    elif not g.picking:
        m.append("picker auto-confirmed by mash across last life")
    # confirm held from the tick of game over opening
    g = with_lives(play_flow(Saves()), 1)
    for _ in range(3000):
        c = g.run.last_life and g.run.burst.age_ticks >= 100
        g = tick(g, th(d=1), confirm=c)
        if g.screen == S.GAME_OVER:
            break
    if not g.picking:
        m.append("held confirm across game over open acted")
    g2 = run_n(g, 60, confirm=True)
    if not g2.picking:
        m.append("held confirm picked name after game over opened")
    return m


# ---- arrow held through a fall
@case("arrow held through a fall does not end the respawn wait; fresh press does and thrusts")
def _():
    m = []
    for held in ("down", "left", "up+down", "all"):
        f = with_lives(play_flow(seed=4), 3)
        keys = {"down": th(d=1), "left": th(l=1, d=1), "up+down": th(u=1, d=1), "all": th(1, 1, 1, 1)}[held]
        # ship must fall: up+down cancel? do manual: place ship at floor
        f = replace(f, run=replace(f.run, ship=replace(f.run.ship, y=470.0, vy=5.0)))
        for _ in range(100):
            f = tick(f, keys)
            if f.run.waiting:
                break
        if not f.run.waiting:
            m.append(f"{held}: never reached wait")
            continue
        if f.run.lives != 2:
            m.append(f"{held}: lives {f.run.lives}")
        y0, x0 = f.run.ship.y, f.run.ship.x
        if (x0, y0) != (SPAWN_X, SPAWN_Y):
            m.append(f"{held}: respawn at {(x0, y0)}")
        # held on; 300 ticks
        g = run_n(f, 300, thrust=keys)
        if not g.run.waiting:
            m.append(f"{held}: wait ended with key held through fall")
        if (g.run.ship.x, g.run.ship.y) != (SPAWN_X, SPAWN_Y) or g.run.ship.vy != 0:
            m.append(f"{held}: ship moved in wait")
        # release one tick then press: ends and thrusts the same tick
        g = tick(g)
        g2 = tick(g, th(u=1))
        if g2.run.waiting:
            m.append(f"{held}: fresh press did not end wait")
        if not g2.run.ship.vy < 0 - 0.1 and g2.run.ship.vy >= 0:
            m.append(f"{held}: no thrust on press tick vy={g2.run.ship.vy}")
        # waiting past invuln end still waiting: ticks 300 > 60
    # pause in the wait, arrow pressed during pause, resume with it held: not a press
    f = with_lives(play_flow(seed=4), 3)
    f = replace(f, run=replace(f.run, ship=replace(f.run.ship, y=470.0, vy=5.0)))
    for _ in range(100):
        f = tick(f)
        if f.run.waiting:
            break
    f = tick(f, focus=True)
    f = tick(f, th(l=1))
    f = tick(f, th(l=1))
    f = tick(f, th(l=1), confirm=True)  # resume with arrow held
    f = tick(f, th(l=1))
    f = run_n(f, 30, thrust=th(l=1))
    if not f.run.waiting:
        m.append("arrow pressed during pause ended wait on resume")
    # arrow pressed same tick as confirm-pause
    f = with_lives(play_flow(seed=4), 3)
    f = replace(f, run=replace(f.run, ship=replace(f.run.ship, y=470.0, vy=5.0)))
    for _ in range(100):
        f = tick(f)
        if f.run.waiting:
            break
    f = tick(f, th(r=1), confirm=True)  # pause + arrow on same tick
    f = tick(f, th(r=1))  # confirm released
    f = tick(f, th(r=1), confirm=True)  # resume w/ arrow held
    f = run_n(f, 10, thrust=th(r=1))
    if not f.run.waiting:
        m.append("arrow held from pause tick ended wait after resume")
    return m


# ---- retry and menu from game over
@case("retry / menu from game over give a fresh run")
def _():
    m = []
    for saves in (
        None,
        Saves(),
        Saves(entries=tuple(ScoreEntry(nickname="A", score=9999, level_reached=1) for _ in range(10))),
    ):
        f = to_game_over(play_flow(saves))
        # dirty the run to be sure reset happens
        f = replace(f, run=replace(f.run, grazes=7, coin_points=500))
        if f.picking:
            f = tick(f)
            f = tick(f, confirm=True)
        f = tick(f)
        g = tick(f, confirm=True)
        if g.screen != S.PLAYING:
            m.append("retry did not play")
        r = g.run
        if not (
            r.lives == LIVES_START and r.score == 0 and r.level == 1 and not r.drifters and r.waves.wave_index == 0
            if hasattr(r.waves, "wave_index")
            else True
        ):
            m.append(f"retry not fresh: lives={r.lives} score={r.score}")
        # menu path
        f2 = tick(f, th(d=1))
        f2 = tick(f2)
        if f2.game_over_selection != GameOverChoice.MENU:
            m.append("down did not select MENU")
        g2 = tick(f2, confirm=True)
        if g2.screen != S.MENU:
            m.append("menu choice did not go to menu")
        g2 = tick(g2)
        g2 = tick(g2, confirm=True)
        if g2.screen != S.PLAYING:
            m.append("menu->play failed")
        if g2.run.score != 0 or g2.run.lives != 5 or g2.run.drifters:
            m.append("menu->play not fresh")
        # up wraps
        f3 = tick(f, th(u=1))
        if f3.game_over_selection != GameOverChoice.MENU:
            m.append("up did not wrap to MENU")
        # up+down cancel
        f4 = tick(f, th(u=1, d=1))
        if f4.game_over_selection != GameOverChoice.RETRY:
            m.append("up+down moved")
    return m


# ---- name entry
@case("name picker: turn both ways, wrap, cursor past both ends, confirm combos")
def _():
    m = []
    f = to_game_over(play_flow(Saves()))
    if not f.picking:
        return ["no picker"]
    f = tick(f)
    chars = NICKNAME_CHARACTERS
    # down from blank wraps to last char; up wraps to blank
    g = tick(f, th(d=1))
    if g.picker.slots[0] != chars[-1]:
        m.append("down from blank did not wrap to last char")
    g = tick(g)
    g = tick(g, th(u=1))
    if g.picker.slots[0] != chars[0]:
        m.append("up did not return")
    # walk whole alphabet up
    g = f
    seen = []
    for _i in range(len(chars) + 2):
        g = tick(g, th(u=1))
        g = tick(g)
        seen.append(g.picker.slots[0])
    if seen[:3] != [chars[1], chars[2], chars[3]]:
        m.append(f"up order {seen[:3]}")
    if seen[len(chars) - 1] != chars[0]:
        m.append("no wrap after full cycle")
    # cursor left from 0 wraps to 9; right from 9 wraps to 0
    g = tick(f, th(l=1))
    if g.picker.cursor != 9:
        m.append(f"left from 0 -> {g.picker.cursor}")
    g = tick(g)
    g = tick(g, th(r=1))
    if g.picker.cursor != 0:
        m.append("right from 9 did not wrap")
    # up+down same tick: no change; left+right same tick: no change
    g = tick(f, th(u=1, d=1))
    if g.picker != f.picker:
        m.append("up+down changed picker")
    g = tick(f, th(l=1, r=1))
    if g.picker != f.picker:
        m.append("left+right changed picker")
    # up and right same tick: turn old slot, move cursor
    g = tick(f, th(u=1, r=1))
    if g.picker.slots[0] != chars[1] or g.picker.cursor != 1:
        m.append(f"up+right {g.picker}")
    # held up does not repeat
    g = f
    for _ in range(30):
        g = tick(g, th(u=1))
    if g.picker.slots[0] != chars[1]:
        m.append("held arrow repeats")
    # confirm + arrows same tick: confirm wins (name saved, not turned)
    g = f
    g = tick(g, th(u=1))
    g = tick(g)  # slot0 = A
    g = tick(g, th(u=1), confirm=True)
    if g.saves.entries[0].nickname != "A":
        m.append(f"confirm+up saved {g.saves.entries}")
    if g.picking:
        m.append("still picking")
    # then arrows should move RETRY/MENU
    g = tick(g)
    g = tick(g, th(d=1))
    if g.game_over_selection != GameOverChoice.MENU:
        m.append("choices dead after name")
    # blank name: nothing saved; last_nickname unchanged
    f2 = replace(to_game_over(play_flow(Saves(last_nickname=None))), saves=Saves(last_nickname=None))
    f2 = tick(f2)
    g = tick(f2, confirm=True)
    if g.saves.entries or g.saves_changed or g.saves.last_nickname is not None or g.picking:
        m.append("blank name saved or kept picking")
    # last_nickname prefill, spaces inside, leading space kept; trailing dropped
    sv = Saves(last_nickname=" A B")
    f3 = to_game_over(play_flow(sv))
    if "".join(f3.picker.slots) != " A B      ":
        m.append(f"prefill {f3.picker.slots}")
    f3 = tick(f3)
    g = tick(f3, confirm=True)
    if g.saves.entries[0].nickname != " A B":
        m.append(f"saved {g.saves.entries[0].nickname!r}")
    # 10 chars
    sv = Saves(last_nickname="0123456789")
    f3 = to_game_over(play_flow(sv))
    f3 = tick(f3)
    g = tick(f3, confirm=True)
    if g.saves.entries[0].nickname != "0123456789":
        m.append("10 char name")
    # spend whole picker: type with random ops then confirm: the name is always valid or nothing saved
    rng = random.Random(5)
    for i in range(200):
        f4 = tick(to_game_over(play_flow(Saves(), seed=i)))
        for _ in range(rng.randint(0, 60)):
            f4 = tick(f4, th(*[rng.random() < 0.3 for _ in range(4)]))
            f4 = tick(f4)
        g = tick(f4, confirm=True)
        if g.saves.entries:
            if not is_valid_nickname(g.saves.entries[0].nickname):
                m.append(f"invalid name saved {g.saves.entries[0].nickname!r}")
    return m


# ---- top 10 boundary: model comparison
@case("top-10: place_of/add_entry vs independent model; ties; 11th")
def _():
    m = []
    rng = random.Random(9)
    for _n in range(4000):
        k = rng.randint(0, 10)
        ents = []
        for _i in range(k):
            ents.append(
                ScoreEntry(nickname="N", score=rng.choice([0, 5, 10, 10, 20]), level_reached=rng.choice([1, 2, 3]))
            )
        ents.sort(key=lambda e: (-e.score, -e.level_reached))  # stable: keeps list order for ties
        sv = Saves(entries=tuple(ents))
        sc, lv = rng.choice([0, 5, 10, 20]), rng.choice([1, 2, 3])
        # model: sort stable with new entry appended last (older stays above)
        tagged = [(e.score, e.level_reached, i) for i, e in enumerate(ents)] + [(sc, lv, 99)]
        tagged.sort(key=lambda t: (-t[0], -t[1], t[2]))
        mp = next(i for i, t in enumerate(tagged) if t[2] == 99) + 1
        mp = mp if mp <= 10 else None
        got = place_of(sv, sc, lv)
        if got != mp:
            m.append(
                f"place_of {got} != model {mp} entries={[(e.score, e.level_reached) for e in ents]} run={(sc, lv)}"
            )
            break
        if got is not None:
            new = add_entry(sv, ScoreEntry(nickname="NEW", score=sc, level_reached=lv))
            exp = tagged[:10]
            names = ["NEW" if t[2] == 99 else "N" for t in exp]
            if [e.nickname for e in new.entries] != names or len(new.entries) > 10:
                m.append("add_entry order mismatch")
                break
        else:
            try:
                add_entry(sv, ScoreEntry(nickname="NEW", score=sc, level_reached=lv))
                m.append("add_entry accepted offlist")
            except ValueError:
                pass
        # message
        ms = message_for(got)
        want = (
            GameOverMessage.GAME_OVER
            if got is None
            else GameOverMessage.NEW_BEST_SCORE
            if got == 1
            else GameOverMessage.TOP_3
            if got <= 3
            else GameOverMessage.TOP_10
        )
        if ms != want:
            m.append("message mismatch")
            break
    return m


@case("top-10 through the flow: 11th score, tie with #10, same score higher level")
def _():
    m = []
    # run dies at known score/level: score of an immediate fall is deterministic per seed; read it
    base = to_game_over(play_flow(Saves(), seed=11))
    sc, lv = base.run.score, base.run.level_reached

    def mk(score, level, name="X"):
        return ScoreEntry(nickname=name, score=score, level_reached=level)

    # (a) tie with #10 on both: off list, no picker, GAME OVER
    sv = Saves(entries=tuple(mk(sc + 100 + i, 1) for i in range(9)) + (mk(sc, lv),), last_nickname="A")
    f = to_game_over(play_flow(sv, seed=11))
    if f.picker is not None or f.game_over_message != GameOverMessage.GAME_OVER:
        m.append("tie with #10 got a picker/message")
    if f.saves != sv:
        m.append("saves changed on off-list")
    # (b) same score, higher level than #10: place 10 -> picker, TOP_10
    sv = Saves(
        entries=tuple(mk(sc + 100 + i, 1) for i in range(9)) + (mk(sc, max(lv - 1, 0) if lv > 1 else lv),),
        last_nickname="A",
    )
    if lv == 1:
        pass  # can't have lower level than 1; skip
    else:
        f = to_game_over(play_flow(sv, seed=11))
        if f.picker is None or f.game_over_message != GameOverMessage.TOP_10:
            m.append("same score higher level not top 10")
    # (c) one less than #10: off
    sv = Saves(entries=tuple(mk(sc + 100 + i, 1) for i in range(9)) + (mk(sc + 1, 1),), last_nickname="A")
    f = to_game_over(play_flow(sv, seed=11))
    if f.picker is not None:
        m.append("below #10 got picker")
    # (d) 10 entries, run beats #10: after save list is 10, #10 dropped, order
    sv = Saves(
        entries=tuple(mk(sc + 100 + i, 1, f"O{i}") for i in range(9))
        + (mk(sc - 1, 1, "OLD") if sc > 0 else mk(0, 1, "OLD"),),
        last_nickname="A",
    )
    if sc > 0:
        f = to_game_over(play_flow(sv, seed=11))
        f = tick(f)
        g = tick(f, confirm=True)
        names = [e.nickname for e in g.saves.entries]
        if len(names) != 10 or "OLD" in names or names[-1] != "A":
            m.append(f"11th: {names}")
    # (e) empty list score 0 run
    f = to_game_over(play_flow(Saves(), seed=12))
    if f.picker is None or f.game_over_message != GameOverMessage.NEW_BEST_SCORE:
        m.append("first score not NEW BEST")
    return m


@case("menu navigation wraps; up+down cancel; arrows ignored on pages; leaderboard w/ empty & none saves")
def _():
    m = []
    f = to_menu_ready(1)
    order = [MenuItem.PLAY, MenuItem.INSTRUCTIONS, MenuItem.LEADERBOARD, MenuItem.CREDITS]
    g = f
    for i in range(1, 9):
        g = tick(g, th(d=1))
        g = tick(g)
        if g.menu_selection != order[i % 4]:
            m.append(f"down {i}")
    g = to_menu_ready(1)
    g = tick(g, th(u=1))
    if g.menu_selection != MenuItem.CREDITS:
        m.append("up did not wrap")
    g = to_menu_ready(1)
    g = tick(g, th(u=1, d=1))
    if g.menu_selection != MenuItem.PLAY:
        m.append("up+down moved")
    # pages: arrows do nothing
    for sel in (1, 2, 3):
        g = to_menu_ready(1)
        for _ in range(sel):
            g = tick(g, th(d=1))
            g = tick(g)
        g = tick(g, confirm=True)
        scr = g.screen
        g = tick(g)
        g = run_n(g, 20, thrust=th(1, 1, 1, 1))
        g = tick(g)
        for i in range(10):
            g = tick(g, th(u=i % 2 == 0, d=i % 2 == 1))
            g = tick(g)
        if g.screen != scr:
            m.append(f"arrows moved page {scr}")
    # start key held on menu at startup does nothing
    f0 = start_flow(KIT.new_run(1), None)
    f0 = run_n(f0, 50, confirm=True)
    if f0.screen != S.MENU:
        m.append("startup held confirm acted")
    f0 = start_flow(KIT.new_run(1), None)
    f0 = run_n(f0, 50, thrust=th(d=1))
    if f0.menu_selection != MenuItem.PLAY:
        m.append("startup held arrow moved menu")
    # arrows+confirm same tick on menu: confirm picks the old selection
    g = to_menu_ready(1)
    g = tick(g, th(d=1), confirm=True)
    if g.screen != S.PLAYING:
        m.append("confirm+down on PLAY did not play")
    return m


@case("menu reopened from game over starts on PLAY; second run through menu has fresh waves/run")
def _():
    m = []
    f = to_game_over(play_flow(Saves(), seed=21))
    f = tick(f)
    f = tick(f, confirm=True)
    f = tick(f)
    f = tick(f, th(d=1))
    f = tick(f)
    f = tick(f, confirm=True)
    if f.screen != S.MENU:
        return ["not menu"]
    if f.menu_selection != MenuItem.PLAY:
        m.append("menu sel not reset")
    f = tick(f, th(d=1))
    f = tick(f)  # on INSTRUCTIONS
    f = tick(f, confirm=True)
    f = tick(f)
    f = tick(f, confirm=True)
    f = tick(f)
    if f.menu_selection != MenuItem.PLAY:
        m.append("menu sel not reset after page")
    return m


@case("run changes only via add_flow_drifters when stepped; no double spawn on pause")
def _():
    m = []
    f = play_flow(seed=5)
    for i in range(3000):
        f = tick(f, th(u=1) if i % 3 else th(d=1))
        if f.screen != S.PLAYING:
            break
        if f.run.lives < 3:
            f = with_lives(f, 5)
        if f.run.wave_spawns_due:
            n = len(f.run.drifters)
            nu = f.run.next_uid
            # pause on the very next tick: must not add the same spawns again
            g = tick(f, focus=True)
            g2 = run_n(g, 5)
            if g2.run.next_uid != nu or len(g2.run.drifters) != n:
                m.append("spawn re-added around pause")
                break
            break
    return m


if __name__ == "__main__":
    SUITE.main(__doc__)
