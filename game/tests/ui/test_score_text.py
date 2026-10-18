"""Score text tests. Contract: docs/contracts/systems/hud.md, Presentation, `score_text(score)`.

The format is `SCORE`, one space, then the digits in groups of three counted from the right,
split by one space. No leading zeros, no digit limit. Source: scope report DRA-61, Limits
(format); hud.md, Presentation.
"""

from ui.score_text import score_text


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
