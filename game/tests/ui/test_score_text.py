"""Score text tests. Contract: docs/contracts/systems/hud.md, Presentation, `score_text(score)`,
from DRA-117 `graze_text(grazes)` and from DRA-126 `group_digits(number)` and `best_text(best)`.

The format is `SCORE`, one space, then the digits in groups of three counted from the right,
split by one space. No leading zeros, no digit limit. Source: scope report DRA-61, Limits
(format); hud.md, Presentation.
"""

from ui.score_text import best_text, graze_text, group_digits, score_text


def test_score_text_groups_digits_in_threes() -> None:
    # The scope report's four examples (DRA-61, Limits, format).
    assert score_text(0) == "SCORE 0"
    assert score_text(999) == "SCORE 999"
    assert score_text(1234) == "SCORE 1 234"
    assert score_text(1234567) == "SCORE 1 234 567"


def test_score_text_keeps_a_group_of_zeros_inside_the_number() -> None:
    # hud.md, Presentation: `SCORE 1 000` and `SCORE 1 000 007`.
    assert score_text(1000) == "SCORE 1 000"
    assert score_text(1000007) == "SCORE 1 000 007"
    assert score_text(1000000) == "SCORE 1 000 000"
    assert score_text(10000) == "SCORE 10 000"
    assert score_text(100000) == "SCORE 100 000"


def test_score_text_has_no_digit_limit() -> None:
    # hud.md, Presentation: "No digit limit: every whole number gets all its digits".
    assert score_text(123456789012345678901234567890) == (
        "SCORE 123 456 789 012 345 678 901 234 567 890"
    )
    assert score_text(10**30) == "SCORE 1" + " 000" * 10


# graze_text, from DRA-117. Contract: hud.md, Presentation, `graze_text(grazes)`: `GRAZE`, one
# space, the digits in groups of three, no leading zeros, no digit limit, grouped exactly like
# `score_text`. Source: scope report DRA-117, Limits ("GRAZE <n>", digits grouped like SCORE);
# 06-scoring.md, graze_cap (no limit).


def test_graze_text_is_the_label_a_space_and_the_grouped_digits() -> None:
    # hud.md, Presentation: `GRAZE 0`, `GRAZE 5`, `GRAZE 999`, `GRAZE 1 000`, `GRAZE 1 234`.
    assert graze_text(0) == "GRAZE 0"
    assert graze_text(5) == "GRAZE 5"
    assert graze_text(999) == "GRAZE 999"
    assert graze_text(1000) == "GRAZE 1 000"
    assert graze_text(1234) == "GRAZE 1 234"
    assert graze_text(1000007) == "GRAZE 1 000 007"
    assert graze_text(1234567) == "GRAZE 1 234 567"


def test_graze_text_has_no_digit_limit() -> None:
    # hud.md, Presentation: "No leading zeros, no digit limit".
    assert graze_text(123456789012345678901234567890) == (
        "GRAZE 123 456 789 012 345 678 901 234 567 890"
    )
    assert graze_text(10**30) == "GRAZE 1" + " 000" * 10


def test_graze_text_groups_exactly_like_score_text() -> None:
    # hud.md: "grouped exactly as `score_text` groups the score". Only the label differs.
    numbers = [0, 1, 9, 10, 99, 100, 999, 1000, 1001, 9999, 10000, 99999, 100000, 999999, 1000000]
    numbers += [10**n + n for n in range(7, 40)]
    for number in numbers:
        assert graze_text(number).removeprefix("GRAZE ") == score_text(number).removeprefix(
            "SCORE "
        ), f"{number}: grouped differently"
        assert graze_text(number).startswith("GRAZE ")
        assert score_text(number).startswith("SCORE ")


def test_graze_text_is_pure() -> None:
    # hud.md: "Pure, like `score_text`": the same number gives the same text.
    assert graze_text(1234) == graze_text(1234)
    assert graze_text(5) == "GRAZE 5"
    assert graze_text(1234) == "GRAZE 1 234"


# group_digits and best_text, from DRA-126. Contract: hud.md, Presentation, `group_digits(number)`
# and `best_text(best)`: `group_digits(0)` is `0`, `group_digits(1234)` is `1 234`,
# `group_digits(1000007)` is `1 000 007`; `best_text` is `BEST`, one space, then the grouped digits
# (`BEST 0`, `BEST 999`, `BEST 1 234`), no digit limit; `score_text`, `graze_text` and `best_text`
# are each their label, one space, then `group_digits`. Source: scope report DRA-126, Values
# needed (BEST: `BEST 1 234`, digits grouped like SCORE).


def _grouped(number: int) -> str:
    """The digits in groups of three from the right, split by a space, worked out here."""
    return f"{number:,}".replace(",", " ")


def test_group_digits_groups_in_threes_from_the_right_with_no_label() -> None:
    # The contract's three examples, then every length from one to ten digits and a group of zeros.
    assert group_digits(0) == "0"
    assert group_digits(1234) == "1 234"
    assert group_digits(1000007) == "1 000 007"
    expected = {
        5: "5",
        42: "42",
        999: "999",
        1000: "1 000",
        12345: "12 345",
        123456: "123 456",
        1234567: "1 234 567",
        12345678: "12 345 678",
        123456789: "123 456 789",
        1234567890: "1 234 567 890",
        1000000: "1 000 000",
    }
    for number, text in expected.items():
        assert group_digits(number) == text, f"{number}"
    # No label, no leading zeros, and no digit limit.
    assert group_digits(10**30) == "1" + " 000" * 10
    assert group_digits(123456789012345678901234567890) == (
        "123 456 789 012 345 678 901 234 567 890"
    )
    for number in (0, 7, 999, 1000, 987654321):
        assert group_digits(number).replace(" ", "").isdigit(), f"{number}: not digits alone"
        assert not group_digits(number).startswith("0 ")
    # Every number from 0 to 2000 against the grouping worked out in this file.
    for number in range(2001):
        assert group_digits(number) == _grouped(number), f"{number}"


def test_best_text_is_the_label_a_space_and_the_grouped_digits() -> None:
    # hud.md, Presentation: `BEST 0`, `BEST 999`, `BEST 1 234`.
    assert best_text(0) == "BEST 0"
    assert best_text(999) == "BEST 999"
    assert best_text(1234) == "BEST 1 234"
    assert best_text(5) == "BEST 5"
    assert best_text(1000) == "BEST 1 000"
    assert best_text(1000007) == "BEST 1 000 007"
    assert best_text(1234567) == "BEST 1 234 567"
    # "No digit limit".
    assert best_text(10**30) == "BEST 1" + " 000" * 10
    assert best_text(123456789012345678901234567890) == (
        "BEST 123 456 789 012 345 678 901 234 567 890"
    )
    # Pure: the same number gives the same text.
    assert best_text(1234) == best_text(1234)


def test_score_graze_and_best_text_are_each_their_label_and_group_digits() -> None:
    # hud.md: each is its label, one space, then `group_digits`, so the grouping has one home.
    numbers = [0, 1, 9, 10, 99, 100, 999, 1000, 1001, 9999, 10000, 99999, 100000, 999999, 1000000]
    numbers += [10**n + n for n in range(7, 40)]
    assert len(numbers) == 48
    for number in numbers:
        digits = group_digits(number)
        assert digits == _grouped(number), f"{number}"
        assert score_text(number) == "SCORE " + digits, f"{number}: SCORE"
        assert graze_text(number) == "GRAZE " + digits, f"{number}: GRAZE"
        assert best_text(number) == "BEST " + digits, f"{number}: BEST"
