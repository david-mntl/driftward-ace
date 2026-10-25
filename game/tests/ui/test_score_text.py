"""Score text tests. Contract: docs/contracts/systems/hud.md, Presentation, `score_text(score)`
and, from DRA-117, `graze_text(grazes)`.

The format is `SCORE`, one space, then the digits in groups of three counted from the right,
split by one space. No leading zeros, no digit limit. Source: scope report DRA-61, Limits
(format); hud.md, Presentation.
"""

from ui.score_text import graze_text, score_text


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
