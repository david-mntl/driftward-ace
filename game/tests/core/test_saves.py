"""The saves: the top 10's order, place, message, adding, best, the nickname and the picker.

Contract: docs/contracts/systems/saves.md, Diagram (the place table, the letter picker table),
Interface (`core/saves.py`), Rules (Order, Place, Message, Adding, Best, Nickname, Letter picker,
Pure). Task: docs/contracts/DRA-126/tasks/DRA-126-06-qa-engineer.md. One test per behavior it lists.
The values are written here from 11-save-data.md (top_n 10, nickname_length 10, nickname_chars
and, as a guess, nickname_char_order) and none is imported from the code under test.
"""

import logging
from copy import deepcopy
from dataclasses import replace
from random import Random

import pytest

from core.saves import (
    BLANK,
    NICKNAME_CHARACTERS,
    NICKNAME_LENGTH,
    TOP_N,
    GameOverMessage,
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

TOP: int = 10
"""Entries kept. Source: 11-save-data.md, top_n (locked)."""

LENGTH: int = 10
"""Longest nickname and the number of picker slots. Source: 11-save-data.md, nickname_length and
nickname_input (locked)."""

CHARACTERS: str = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_!?*"
"""The blank, A to Z, 0 to 9, then `. - _ ! ? *`. Source: 11-save-data.md, nickname_chars (locked)
and nickname_char_order (guess: the order is a guess)."""

LEVELS: range = range(1, 9)
"""Levels 1 to 8. Source: 08-difficulty.md, rule 1."""

SAVES_LOGGER: str = "core.saves"


def entry(nickname: str, score: int, level: int) -> ScoreEntry:
    """One entry."""
    return ScoreEntry(nickname=nickname, score=score, level_reached=level)


def saves_of(*rows: tuple[str, int, int], last: str | None = None) -> Saves:
    """A list in the order given: (nickname, score, level) rows, #1 first."""
    return Saves(entries=tuple(entry(*row) for row in rows), last_nickname=last)


def full_list() -> Saves:
    """TOP entries on level 3: scores 1000, 900, ... 100, nicknames N1 to N10."""
    return saves_of(*((f"N{i + 1}", 1000 - 100 * i, 3) for i in range(TOP)), last="N10")


def rank_key(item: ScoreEntry) -> tuple[int, int]:
    """Sort key of the contract's order: higher score first, then higher level first."""
    return (-item.score, -item.level_reached)


def test_the_values_are_the_gdds() -> None:
    assert TOP_N == TOP
    assert NICKNAME_LENGTH == LENGTH
    assert NICKNAME_CHARACTERS == CHARACTERS
    assert BLANK == " "


def test_entries_rank_by_score_then_level_and_an_equal_entry_goes_under_the_older() -> None:
    # The Diagram's table: 1 500 LV 4, 900 LV 4, 900 LV 3.
    table: Saves = saves_of(("A", 1500, 4), ("B", 900, 4), ("C", 900, 3))
    assert place_of(table, 900, 3) == 4, "ties on both: the older entry stays above"
    assert place_of(table, 900, 4) == 3, "ties the second on both, beats the third on level"
    assert place_of(table, 900, 5) == 2, "beats the second on level"
    assert place_of(table, 901, 1) == 2, "a higher score beats a higher level"
    assert place_of(table, 899, 8) == 4, "a lower score loses to a higher level"
    assert place_of(table, 1500, 4) == 2, "a tie with #1 goes under it"
    assert place_of(table, 1500, 5) == 1
    assert place_of(table, 1501, 1) == 1

    added: Saves = add_entry(table, entry("D", 900, 3))
    assert [e.nickname for e in added.entries] == ["A", "B", "C", "D"], "older stays above"
    added = add_entry(added, entry("E", 900, 4))
    assert [e.nickname for e in added.entries] == ["A", "B", "E", "C", "D"]

    # Many ties, entries added in a scrambled order: always the stable sort of what was added.
    rng: Random = Random(126)
    for _ in range(20):
        saves: Saves = Saves()
        added_in_order: list[ScoreEntry] = []
        for index in range(TOP):
            new: ScoreEntry = entry(f"P{index}", rng.choice((0, 100, 200)), rng.choice((1, 2, 3)))
            saves = add_entry(saves, new)
            added_in_order.append(new)
            assert list(saves.entries) == sorted(added_in_order, key=rank_key)
    assert len(saves.entries) == TOP


def test_place_of_gives_a_place_on_a_short_list_and_none_off_a_full_one() -> None:
    for score in (0, 1, 5000, 10**9):
        for level in LEVELS:
            assert place_of(Saves(), score, level) == 1, f"empty list, score {score} level {level}"

    for count in range(TOP):
        high: Saves = saves_of(*((f"H{i}", 9000 - i, 8) for i in range(count)))
        assert place_of(high, 0, 1) == count + 1, f"{count} entries: the worst run still places"
        assert place_of(high, 9001, 1) == 1

    full: Saves = full_list()  # #10 is 100 on level 3
    assert place_of(full, 100, 3) is None, "ties #10 on score and level"
    assert place_of(full, 100, 2) is None, "ties #10 on score, lower level"
    assert place_of(full, 100, 1) is None
    assert place_of(full, 99, 8) is None, "ranks below #10"
    assert place_of(full, 0, 8) is None
    assert place_of(full, 100, 4) == TOP, "beats #10 on level"
    assert place_of(full, 101, 1) == TOP, "beats #10 on score"
    assert place_of(full, 1000, 3) == 2, "ties #1 on both"
    assert place_of(full, 1001, 1) == 1
    assert place_of(full, 550, 1) == 6


def test_message_for_gives_the_four_messages_by_place() -> None:
    assert message_for(1) is GameOverMessage.NEW_BEST_SCORE
    assert message_for(2) is GameOverMessage.TOP_3
    assert message_for(3) is GameOverMessage.TOP_3
    for place in range(4, TOP + 1):
        assert message_for(place) is GameOverMessage.TOP_10, f"place {place}"
    assert message_for(None) is GameOverMessage.GAME_OVER
    assert {m.value for m in GameOverMessage} == {"new_best_score", "top_3", "top_10", "game_over"}


def test_add_entry_puts_the_entry_at_its_place_and_drops_the_one_pushed_out() -> None:
    full: Saves = full_list()
    old: tuple[ScoreEntry, ...] = full.entries

    at_five: Saves = add_entry(full, entry("NEW", 650, 1))  # between 700 (#4) and 600 (#5)
    assert at_five.entries[:4] == old[:4]
    assert at_five.entries[4] == entry("NEW", 650, 1)
    assert at_five.entries[5:] == old[4:9], "the ones below move down one"
    assert len(at_five.entries) == TOP
    assert old[9] not in at_five.entries, "the one pushed past the end is dropped"
    assert at_five.last_nickname == "NEW"

    at_one: Saves = add_entry(full, entry("TOP", 5000, 1))
    assert at_one.entries == (entry("TOP", 5000, 1), *old[:9])
    assert at_one.last_nickname == "TOP"

    at_last: Saves = add_entry(full, entry("LAST", 100, 4))
    assert at_last.entries == (*old[:9], entry("LAST", 100, 4))
    assert at_last.last_nickname == "LAST"

    short: Saves = saves_of(("A", 300, 1), ("B", 100, 1), last="B")
    middle: Saves = add_entry(short, entry("C", 200, 1))
    assert [e.nickname for e in middle.entries] == ["A", "C", "B"]
    assert middle.last_nickname == "C"
    assert [e.nickname for e in add_entry(short, entry("D", 0, 1)).entries] == ["A", "B", "D"]

    first: Saves = add_entry(Saves(), entry("ACE", 0, 1))
    assert first == Saves(entries=(entry("ACE", 0, 1),), last_nickname="ACE")

    twice: Saves = add_entry(add_entry(Saves(), entry("ACE", 500, 2)), entry("ACE", 700, 2))
    assert [(e.nickname, e.score) for e in twice.entries] == [("ACE", 700), ("ACE", 500)]
    same_run: Saves = add_entry(twice, entry("ACE", 700, 2))
    assert [e.nickname for e in same_run.entries] == ["ACE", "ACE", "ACE"]


def test_best_is_the_first_entrys_score_and_none_on_an_empty_list() -> None:
    assert Saves().best is None
    assert Saves(last_nickname="ACE").best is None
    assert saves_of(("A", 0, 1)).best == 0, "a best of 0 is a score, not none"
    assert saves_of(("A", 900, 2), ("B", 800, 8)).best == 900

    saves: Saves = saves_of(("A", 900, 2), ("B", 500, 2))
    assert add_entry(saves, entry("C", 700, 1)).best == 900, "an entry at place 2 leaves it"
    assert add_entry(saves, entry("D", 900, 2)).best == 900, "a tie goes under #1"
    assert add_entry(saves, entry("E", 900, 3)).best == 900, "the same score, a higher level"
    assert add_entry(saves, entry("F", 901, 1)).best == 901, "a new #1 changes it"
    assert add_entry(Saves(), entry("G", 0, 1)).best == 0
    assert full_list().best == 1000


@pytest.mark.parametrize(
    "name",
    [
        "A",
        "ACE",
        "ABCDEFGHIJ",
        "0123456789",
        ".-_!?*",
        " A",
        "  A",
        "A B",
        "A  B",
        " A B",
        " " * (LENGTH - 1) + "A",
        "A" + " " * (LENGTH - 2) + "B",
    ],
)
def test_a_nickname_of_one_to_ten_allowed_characters_is_valid(name: str) -> None:
    assert 1 <= len(name) <= LENGTH
    assert is_valid_nickname(name)


def test_every_allowed_character_but_the_blank_is_a_valid_nickname_alone() -> None:
    for char in CHARACTERS[1:]:
        assert is_valid_nickname(char), f"{char!r}"
        assert is_valid_nickname("A" + char)
        assert is_valid_nickname(char * LENGTH)


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        " " * LENGTH,
        "A ",
        "A  ",
        "AB   ",
        " A ",
        "ABCDEFGHI ",
        "ABCDEFGHIJK",
        "A" * (LENGTH + 1),
        " ABCDEFGHIJ",
        "A" * 100,
        "a",
        "Ab",
        "A,B",
        "A/B",
        "A#",
        "@",
        "A\n",
        "A\tB",
        "é",
        "Aé",
        "А",
    ],
)
def test_a_nickname_that_is_empty_ends_in_a_blank_is_too_long_or_has_a_wrong_character_is_not(
    name: str,
) -> None:
    assert not is_valid_nickname(name)


def test_start_picker_fills_the_slots_from_the_last_nickname_with_the_cursor_on_slot_zero() -> None:
    blank: NamePicker = start_picker(None)
    assert blank.slots == (BLANK,) * LENGTH
    assert blank.cursor == 0
    assert start_picker("").slots == (BLANK,) * LENGTH

    ace: NamePicker = start_picker("ACE")
    assert ace.slots == ("A", "C", "E") + (BLANK,) * (LENGTH - 3)
    assert ace.cursor == 0
    assert len(ace.slots) == LENGTH

    full: NamePicker = start_picker("ABCDEFGHIJ")
    assert full.slots == tuple("ABCDEFGHIJ")
    assert full.cursor == 0

    leading: NamePicker = start_picker(" A B")
    assert leading.slots == (" ", "A", " ", "B") + (BLANK,) * (LENGTH - 4)

    for text in ("A", "ZZ9", "A-B"):
        assert picked_name(start_picker(text)) == text, "the name comes back whole"


def test_turn_character_steps_through_the_characters_both_ways_and_wraps() -> None:
    picker: NamePicker = replace(start_picker("ACE"), cursor=1)  # on the C

    up: NamePicker = turn_character(picker, 1)
    assert up.slots == ("A", "D", "E") + (BLANK,) * (LENGTH - 3)
    assert up.cursor == 1
    down: NamePicker = turn_character(picker, -1)
    assert down.slots == ("A", "B", "E") + (BLANK,) * (LENGTH - 3)
    assert down.cursor == 1

    # Forward from the blank visits every character in order and comes back to the blank.
    forward: NamePicker = start_picker(None)
    seen: list[str] = []
    for _ in range(len(CHARACTERS)):
        forward = turn_character(forward, 1)
        seen.append(forward.slots[0])
    assert "".join(seen) == CHARACTERS[1:] + CHARACTERS[0], "up wraps from the last to the blank"

    # Back from the blank visits them in reverse, the last character first.
    backward: NamePicker = start_picker(None)
    seen = []
    for _ in range(len(CHARACTERS)):
        backward = turn_character(backward, -1)
        seen.append(backward.slots[0])
    assert "".join(seen) == "".join(reversed(CHARACTERS[1:])) + CHARACTERS[0]
    assert turn_character(start_picker(None), -1).slots[0] == CHARACTERS[-1], "down on a blank"
    assert turn_character(start_picker("*"), 1).slots[0] == BLANK, "up on the last character"
    assert turn_character(start_picker("A"), -1).slots[0] == BLANK
    assert turn_character(start_picker(None), 1).slots[0] == "A"

    # Only the cursor's slot changes, on every slot.
    for cursor in range(LENGTH):
        base: NamePicker = replace(start_picker("ABCDEFGHIJ"), cursor=cursor)
        for step in (1, -1):
            turned: NamePicker = turn_character(base, step)
            assert turned.cursor == cursor
            others_before: tuple[str, ...] = base.slots[:cursor] + base.slots[cursor + 1 :]
            others_after: tuple[str, ...] = turned.slots[:cursor] + turned.slots[cursor + 1 :]
            assert others_after == others_before
            assert turned.slots[cursor] != base.slots[cursor]
            assert len(turned.slots) == LENGTH


def test_move_cursor_moves_one_slot_both_ways_and_wraps_without_changing_a_slot() -> None:
    picker: NamePicker = start_picker("ACE")
    assert move_cursor(picker, 1).cursor == 1
    assert move_cursor(picker, -1).cursor == LENGTH - 1, "left on slot 0 wraps to the last"
    last: NamePicker = replace(picker, cursor=LENGTH - 1)
    assert move_cursor(last, 1).cursor == 0, "right on the last slot wraps to slot 0"
    assert move_cursor(last, -1).cursor == LENGTH - 2
    assert move_cursor(replace(picker, cursor=5), 1).cursor == 6
    assert move_cursor(replace(picker, cursor=5), -1).cursor == 4

    walker: NamePicker = picker
    visited: list[int] = []
    for _ in range(LENGTH):
        walker = move_cursor(walker, 1)
        visited.append(walker.cursor)
        assert walker.slots == picker.slots
    assert visited == [*range(1, LENGTH), 0], "one lap right comes back to slot 0"
    for _ in range(LENGTH):
        walker = move_cursor(walker, -1)
        assert walker.slots == picker.slots
    assert walker.cursor == 0


def test_picked_name_drops_only_trailing_blanks_and_is_empty_when_all_are_blank() -> None:
    blanks: tuple[str, ...] = (BLANK,) * LENGTH
    assert picked_name(start_picker(None)) == ""
    assert picked_name(NamePicker(slots=blanks, cursor=3)) == ""

    assert picked_name(start_picker("ACE")) == "ACE"
    assert picked_name(turn_character(start_picker("ACE"), 1)) == "BCE", "the Diagram's example"
    assert picked_name(NamePicker(slots=(" ", "A", *blanks[2:]), cursor=0)) == " A", "leading kept"
    assert picked_name(NamePicker(slots=("A", " ", "B", *blanks[3:]), cursor=0)) == "A B"
    assert picked_name(NamePicker(slots=("A", " ", " ", "B", *blanks[4:]), cursor=0)) == "A  B"
    assert picked_name(start_picker("ABCDEFGHIJ")) == "ABCDEFGHIJ"
    assert picked_name(NamePicker(slots=("A", *blanks[1:]), cursor=9)) == "A"
    assert picked_name(NamePicker(slots=(*blanks[:9], "A"), cursor=0)) == " " * 9 + "A"

    # A name the picker makes is valid, unless it is empty.
    for slots in (("A", " ", "B", *blanks[3:]), (" ", "Z", *blanks[2:]), ("0", *blanks[1:])):
        assert is_valid_nickname(picked_name(NamePicker(slots=slots, cursor=0)))
    assert not is_valid_nickname(picked_name(start_picker(None)))


@pytest.mark.determinism
def test_every_function_leaves_its_input_unchanged_and_gives_the_same_output_twice(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    saves_cases: list[Saves] = [
        Saves(),
        saves_of(("A", 900, 2), ("B", 900, 1), last="B"),
        full_list(),
    ]
    picker_cases: list[NamePicker] = [
        start_picker(None),
        start_picker("ACE"),
        replace(start_picker("ABCDEFGHIJ"), cursor=9),
    ]
    new: ScoreEntry = entry("NEW", 900, 2)

    for saves in saves_cases:
        snapshot: Saves = deepcopy(saves)
        assert saves.best == saves.best
        assert place_of(saves, 900, 2) == place_of(saves, 900, 2)
        for score, level in ((0, 1), (900, 2), (5000, 8)):
            assert place_of(saves, score, level) == place_of(snapshot, score, level)
        assert saves == snapshot
        if place_of(saves, new.score, new.level_reached) is not None:
            first: Saves = add_entry(saves, new)
            second: Saves = add_entry(saves, new)
            assert first == second
            assert first is not saves
            assert saves == snapshot, "add_entry never edits the list it was given"
            assert saves.entries == snapshot.entries
            assert saves.last_nickname == snapshot.last_nickname
    assert new == entry("NEW", 900, 2)

    for place in (None, *range(1, TOP + 1)):
        assert message_for(place) is message_for(place)

    for text in ("", "A", "A ", "ABCDEFGHIJK", "a"):
        assert is_valid_nickname(text) == is_valid_nickname(text)

    for last in (None, "", "ACE", "ABCDEFGHIJ"):
        assert start_picker(last) == start_picker(last)
    for picker in picker_cases:
        snapshot_picker: NamePicker = deepcopy(picker)
        for step in (1, -1):
            assert turn_character(picker, step) == turn_character(picker, step)
            assert move_cursor(picker, step) == move_cursor(picker, step)
            assert turn_character(picker, step) is not picker
            assert move_cursor(picker, step) is not picker
            assert picker == snapshot_picker
        assert picked_name(picker) == picked_name(picker)
        assert picker == snapshot_picker

    assert [r for r in caplog.records if r.name == SAVES_LOGGER] == [], "saves logs nothing"
