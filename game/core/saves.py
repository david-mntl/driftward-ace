"""The saved top 10, the place and message of a run, and the letter picker.

Everything here is pure: no logging, no clock, no randomness, no I/O, and no input is mutated.
The browser's localStorage is the app's; core only holds the `Saves` state. Stdlib only.

Source: docs/contracts/systems/saves.md, Interface and Rules; 11-save-data.md.
"""

import logging
from dataclasses import dataclass, replace
from enum import Enum
from typing import Final

log = logging.getLogger(__name__)

TOP_N: Final[int] = 10
"""Entries on the top list. Source: 11-save-data.md, top_n (locked)."""

NICKNAME_LENGTH: Final[int] = 10
"""Longest nickname, and the number of picker slots. Source: 11-save-data.md, nickname_length and
nickname_input (locked)."""

NICKNAME_CHARACTERS: Final[str] = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_!?*"
"""Allowed characters in picker order, the blank first. Source: 11-save-data.md, nickname_chars
(locked), nickname_char_order (guess)."""

BLANK: Final[str] = NICKNAME_CHARACTERS[0]
"""A blank slot, the space. Source: systems/saves.md, Interface."""

_PLACE_NEW_BEST: Final[int] = 1
_PLACE_LAST_TOP_3: Final[int] = 3


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreEntry:
    """One run on the top 10."""

    nickname: str
    """A valid nickname (`is_valid_nickname`)."""

    score: int
    """The run's final score, 0 or more."""

    level_reached: int
    """The level reached, FIRST_LEVEL to LEVEL_COUNT."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Saves:
    """Everything the game saves."""

    entries: tuple[ScoreEntry, ...] = ()
    """Place order, #1 first, 0 to TOP_N entries."""

    last_nickname: str | None = None
    """The last name saved, None before the first."""

    @property
    def best(self) -> int | None:
        """The score of #1, or None while the list is empty. Source: 11-save-data.md, rule 3."""
        if not self.entries:
            return None
        return self.entries[0].score


class GameOverMessage(Enum):
    """The game-over screen's message, by the run's place. Source: 10-ui.md, game_over_message."""

    NEW_BEST_SCORE = "new_best_score"
    TOP_3 = "top_3"
    TOP_10 = "top_10"
    GAME_OVER = "game_over"


def _ranks_above_or_ties(entry: ScoreEntry, score: int, level_reached: int) -> bool:
    """True when `entry` beats or equals a run of `score` and `level_reached`."""
    if entry.score != score:
        return entry.score > score
    return entry.level_reached >= level_reached


def place_of(saves: Saves, score: int, level_reached: int) -> int | None:
    """Return the place, 1 to TOP_N, a run would take on `saves`, or None when it is off the list.

    A new run goes under every entry that ranks above it or ties it on score and level. Source:
    systems/saves.md, Rules, Place; 11-save-data.md, sort_and_ties (locked).
    """
    ahead: int = sum(_ranks_above_or_ties(e, score, level_reached) for e in saves.entries)
    place: int = ahead + 1
    if place > TOP_N:
        return None
    return place


def message_for(place: int | None) -> GameOverMessage:
    """Return the game-over message of `place`: 1 best, 2 to 3 top 3, 4 to TOP_N top 10, else none.

    Source: systems/saves.md, Rules, Message; 10-ui.md, game_over_message (locked).
    """
    if place is None:
        return GameOverMessage.GAME_OVER
    if place == _PLACE_NEW_BEST:
        return GameOverMessage.NEW_BEST_SCORE
    if place <= _PLACE_LAST_TOP_3:
        return GameOverMessage.TOP_3
    return GameOverMessage.TOP_10


def add_entry(saves: Saves, entry: ScoreEntry) -> Saves:
    """Return `saves` with `entry` at its place, the list cut to TOP_N, and its nickname last.

    The caller only adds an entry that has a place. Source: systems/saves.md, Rules, Adding.
    """
    place: int | None = place_of(saves, entry.score, entry.level_reached)
    if place is None:
        raise ValueError(f"entry score={entry.score} level={entry.level_reached} has no place")
    index: int = place - 1
    entries: tuple[ScoreEntry, ...] = (*saves.entries[:index], entry, *saves.entries[index:])
    return replace(saves, entries=entries[:TOP_N], last_nickname=entry.nickname)


def is_valid_nickname(text: str) -> bool:
    """True when `text` is 1 to NICKNAME_LENGTH allowed characters and does not end in a blank.

    Source: systems/saves.md, Rules, Nickname; 11-save-data.md, rule 8.
    """
    if not 1 <= len(text) <= NICKNAME_LENGTH:
        return False
    if text[-1] == BLANK:
        return False
    return all(char in NICKNAME_CHARACTERS for char in text)


@dataclass(frozen=True, slots=True, kw_only=True)
class NamePicker:
    """The letter picker: one character per slot and the slot the cursor is on."""

    slots: tuple[str, ...]
    """NICKNAME_LENGTH characters, each in NICKNAME_CHARACTERS."""

    cursor: int
    """The slot the cursor is on, 0 to NICKNAME_LENGTH - 1."""


def start_picker(last_nickname: str | None) -> NamePicker:
    """Return a picker filled with `last_nickname` from slot 0, blank after, cursor on slot 0.

    Source: systems/saves.md, Rules, Letter picker; 11-save-data.md, rule 7.
    """
    name: str = "" if last_nickname is None else last_nickname
    slots: tuple[str, ...] = tuple(name.ljust(NICKNAME_LENGTH, BLANK))
    return NamePicker(slots=slots, cursor=0)


def turn_character(picker: NamePicker, step: int) -> NamePicker:
    """Return `picker` with the cursor's slot turned `step` (+1 or -1) through the characters.

    Wraps at both ends. Source: systems/saves.md, Rules, Letter picker.
    """
    current: int = NICKNAME_CHARACTERS.index(picker.slots[picker.cursor])
    turned: str = NICKNAME_CHARACTERS[(current + step) % len(NICKNAME_CHARACTERS)]
    slots: tuple[str, ...] = (
        *picker.slots[: picker.cursor],
        turned,
        *picker.slots[picker.cursor + 1 :],
    )
    return replace(picker, slots=slots)


def move_cursor(picker: NamePicker, step: int) -> NamePicker:
    """Return `picker` with the cursor moved `step` (+1 right, -1 left) slots, wrapping.

    Source: systems/saves.md, Rules, Letter picker.
    """
    return replace(picker, cursor=(picker.cursor + step) % NICKNAME_LENGTH)


def picked_name(picker: NamePicker) -> str:
    """Return the slots joined with the blanks at the end dropped, "" when all are blank.

    Source: systems/saves.md, Rules, Letter picker; 11-save-data.md, rule 8.
    """
    return "".join(picker.slots).rstrip(BLANK)
