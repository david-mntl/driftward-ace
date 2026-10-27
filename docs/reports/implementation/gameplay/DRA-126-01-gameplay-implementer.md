Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-126-01 (Architect): `game/core/saves.py` (new) and the level reached in `game/core/run.py`, from `docs/contracts/systems/saves.md` and `run.md`.
2. **Delivered:**
   - `game/core/saves.py` (new): `TOP_N`, `NICKNAME_LENGTH`, `NICKNAME_CHARACTERS`, `BLANK`, `ScoreEntry`, `Saves` (with `best`), `GameOverMessage`, `place_of`, `message_for`, `add_entry`, `is_valid_nickname`, `NamePicker`, `start_picker`, `turn_character`, `move_cursor`, `picked_name`.
   - `game/core/run.py`: `Run.final_level` (last field, default None), `Run.level_reached`, `final_level` set in `_start_last_life`. `next_run` needed no change: `start_run` builds the new run with `final_level` None.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `py_compile` on `core/saves.py` and `core/run.py`: clean.
   - `game/tests/check.sh lint`: PASS lint, PASS format.
   - `game/tests/check.sh typecheck`: PASS. `check.sh core`: 3288 passed. `check.sh ui`: 89 passed. No existing test changed, none fails (impact.md expects no failure from this task).
   - Smoke script below, run twice: the two outputs are byte-identical (`cmp`).
   - Grep of `core/saves.py` and `core/run.py` for the banned names: the only hits are `.waves` in `run.py` matching the `.wav` pattern. No real hit.
   - Command, from `/workspace/game`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python <script>` with the script and output below.
4. **Assumptions:**
   - `NICKNAME_CHARACTERS` order is the GDD's `nickname_char_order` (guess): blank, A-Z, 0-9, then `. - _ ! ? *`.
   - `add_entry` raises `ValueError` when the entry has no place (off the list). The contract says the caller only adds an entry with a place and names no behavior otherwise; core raises on a broken precondition (`game/CONTEXT.md`).
   - `core.levels` is not imported in `saves.py`: the Interface lists it as an allowed import, but nothing in the module needs `FIRST_LEVEL` or `LEVEL_COUNT`, and ruff would flag an unused import.
   - `final_level` is read from `stepped.level`: at that point of the tick `stepped.waves` is still the one going into the tick (step 9a runs after `_apply_fall`/`_apply_hit`), which is what the contract asks.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-126/tasks/DRA-126-01-gameplay-implementer.md`. Left alone: `core/game_flow.py` (DRA-126-02), ui, tests, app.
7. **Status:** done.

## Decisions
- Place: `1 +` the entries that rank above or tie the run (`score` greater, or equal score and `level_reached` greater or equal); above `TOP_N` is None. One count gives ties-go-under and the tie-with-#10 edge case. Source: saves.md, Rules, Place.
- `add_entry` inserts at `place_of - 1` and cuts to `TOP_N`. A tuple slice, so the input `Saves` is never changed.
- Picker steps use `% len(NICKNAME_CHARACTERS)` and `% NICKNAME_LENGTH`: one wrap rule for both directions.
- `start_picker` is `ljust` on `BLANK`. A `last_nickname` longer than `NICKNAME_LENGTH` is not handled: the app checks loaded data with `is_valid_nickname` at the edge.
- `final_level` is set next to `final_score` in `_start_last_life`, so both fall on the same tick. Waves still step after it, so `level` can rise while `final_level` stays (smoke, tick 1).
- No tuning keys: `TOP_N`, `NICKNAME_LENGTH` and the characters are locked GDD values, constants in code as the contract's Interface gives them (11-save-data.md).
- `_PLACE_NEW_BEST` and `_PLACE_LAST_TOP_3` name the message bands 1 and 2 to 3. Source: 10-ui.md, game_over_message (locked).

## Smoke script
Saved in the scratchpad while checking, not in the repo. Waves in the last block: Wave 0 and `a` are 11 px, so with the scroll at 19 moving ticks (20.9 px) the death tick's waves step raises the level to 2.

```python
"""DRA-126-01 smoke. Run from game/: python <this file>."""

import sys
from dataclasses import replace

sys.path.insert(0, ".")

from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.last_life import LastLifeRules
from core.run import Run, next_run, start_run, step_run
from core.saves import (
    NICKNAME_CHARACTERS,
    NICKNAME_LENGTH,
    TOP_N,
    NamePicker,
    Saves,
    ScoreEntry,
    add_entry,
    is_valid_nickname,
    message_for,
    move_cursor,
    picked_name,
    place_of,
    start_picker,
    turn_character,
)
from core.scroll import Scroll
from core.ship import Ship, Thrust
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WavePlacement,
    start_waves,
    step_waves,
)


def e(name: str, score: int, level: int) -> ScoreEntry:
    return ScoreEntry(nickname=name, score=score, level_reached=level)


print("TOP_N", TOP_N, "NICKNAME_LENGTH", NICKNAME_LENGTH, "chars", repr(NICKNAME_CHARACTERS))

# 1. place_of / message_for
table = Saves(entries=(e("A", 1500, 4), e("B", 900, 4), e("C", 900, 3)))
for score, level in [(900, 3), (900, 4), (1500, 4), (2000, 1), (100, 1), (0, 1)]:
    p = place_of(table, score, level)
    print("table", score, level, "->", p, message_for(p).name)
empty = Saves()
p = place_of(empty, 0, 1)
print("empty list, score 0 ->", p, message_for(p).name)
full = Saves(entries=tuple(e(f"N{i}", 1000 - i * 10, 3) for i in range(TOP_N)))
last = full.entries[-1]
for label, score, level in [
    ("ties last", last.score, last.level_reached),
    ("just above last", last.score + 1, last.level_reached),
    ("same score, lower level", last.score, last.level_reached - 1),
    ("same score, higher level", last.score, last.level_reached + 1),
]:
    p = place_of(full, score, level)
    print("full list,", label, "->", p, message_for(p).name)
print("message_for 1,2,3,4,10,None:", [message_for(x).name for x in (1, 2, 3, 4, 10, None)])

# 2. add_entry on a full list
before = full
added = add_entry(full, e("NEW", last.score + 1, 3))
print("add_entry: len", len(added.entries), "last_nickname", added.last_nickname)
print("  names", [x.nickname for x in added.entries])
print("  pushed out", last.nickname, "still in:", last in added.entries)
print("  input unchanged:", full is before and len(full.entries) == TOP_N and full.last_nickname is None)
print("  best", added.best, "empty best", empty.best)

# 3. picker
for start in ("ACE", None):
    pk = start_picker(start)
    print("start_picker", repr(start), "".join(pk.slots).replace(" ", "."), pk.cursor, repr(picked_name(pk)))
    steps = [
        ("up", lambda p: turn_character(p, 1)),
        ("down", lambda p: turn_character(p, -1)),
        ("down", lambda p: turn_character(p, -1)),
        ("left", lambda p: move_cursor(p, -1)),
        ("right", lambda p: move_cursor(p, 1)),
        ("right", lambda p: move_cursor(p, 1)),
        ("up", lambda p: turn_character(p, 1)),
    ]
    for name, fn in steps:
        pk = fn(pk)
        print("  ", name, "".join(pk.slots).replace(" ", "."), "cursor", pk.cursor, "picked", repr(picked_name(pk)))
for text in ("ACE", " A", "A ", "", "ABCDEFGHIJK"):
    print("is_valid_nickname", repr(text), is_valid_nickname(text))

# 4. the level reached
SEED = 7
waves = [
    Wave(wave_id="w0", length_px=11.0, kind=WaveKind.FIXED, min_level=None, placements=()),
    Wave(
        wave_id="a",
        length_px=11.0,
        kind=WaveKind.FIXED,
        min_level=None,
        placements=(
            WavePlacement(at_px=11.0, placement=Placement(DrifterType.METEORITE, x=200.0, y=-20.0)),
        ),
    ),
    Wave(wave_id="long", length_px=10_000.0, kind=WaveKind.FIXED, min_level=None, placements=()),
]
book = WaveBook(
    waves={w.wave_id: w for w in waves},
    wave_zero_id="w0",
    playlists=(LevelPlaylist(fixed=("a",)), *(LevelPlaylist(fixed=("long",)) for _ in range(7))),
)
rules = LastLifeRules(delay_ticks=3, burst_particle_count=4, burst_particle_speed=1.0, burst_particle_size=3)
scroll = Scroll(ticks=100, scrolled_ticks=19)
ready = step_waves(start_waves(book, SEED), scroll.distance_px)
base = start_run(ready, last_life_rules=rules)
run = replace(base, lives=1, scroll=scroll, ship=Ship(x=200.0, y=480 + 16 - 5.5, vx=0.0, vy=5.5))
print("before: level", run.level, "level_reached", run.level_reached, "final_level", run.final_level)
states: list[Run] = []
while not run.game_over:
    run = step_run(run, Thrust())
    states.append(run)
for i, s in enumerate(states, 1):
    print(f"tick {i}: last_life={s.last_life} game_over={s.game_over} level={s.level} "
          f"final_level={s.final_level} level_reached={s.level_reached} score={s.score}")
fresh = next_run(run)
print("next_run: final_level", fresh.final_level, "level", fresh.level, "level_reached", fresh.level_reached)
```

## Smoke output

```
TOP_N 10 NICKNAME_LENGTH 10 chars ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_!?*'
table 900 3 -> 4 TOP_10
table 900 4 -> 3 TOP_3
table 1500 4 -> 2 TOP_3
table 2000 1 -> 1 NEW_BEST_SCORE
table 100 1 -> 4 TOP_10
table 0 1 -> 4 TOP_10
empty list, score 0 -> 1 NEW_BEST_SCORE
full list, ties last -> None GAME_OVER
full list, just above last -> 10 TOP_10
full list, same score, lower level -> None GAME_OVER
full list, same score, higher level -> 10 TOP_10
message_for 1,2,3,4,10,None: ['NEW_BEST_SCORE', 'TOP_3', 'TOP_3', 'TOP_10', 'TOP_10', 'GAME_OVER']
add_entry: len 10 last_nickname NEW
  names ['N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'NEW']
  pushed out N9 still in: False
  input unchanged: True
  best 1000 empty best None
start_picker 'ACE' ACE....... 0 'ACE'
   up BCE....... cursor 0 picked 'BCE'
   down ACE....... cursor 0 picked 'ACE'
   down .CE....... cursor 0 picked ' CE'
   left .CE....... cursor 9 picked ' CE'
   right .CE....... cursor 0 picked ' CE'
   right .CE....... cursor 1 picked ' CE'
   up .DE....... cursor 1 picked ' DE'
start_picker None .......... 0 ''
   up A......... cursor 0 picked 'A'
   down .......... cursor 0 picked ''
   down *......... cursor 0 picked '*'
   left *......... cursor 9 picked '*'
   right *......... cursor 0 picked '*'
   right *......... cursor 1 picked '*'
   up *A........ cursor 1 picked '*A'
is_valid_nickname 'ACE' True
is_valid_nickname ' A' True
is_valid_nickname 'A ' False
is_valid_nickname '' False
is_valid_nickname 'ABCDEFGHIJK' False
before: level 1 level_reached 1 final_level None
tick 1: last_life=True game_over=False level=2 final_level=1 level_reached=1 score=2
tick 2: last_life=True game_over=False level=2 final_level=1 level_reached=1 score=2
tick 3: last_life=True game_over=False level=2 final_level=1 level_reached=1 score=2
tick 4: last_life=False game_over=True level=2 final_level=1 level_reached=1 score=2
next_run: final_level None level 1 level_reached 1
```
