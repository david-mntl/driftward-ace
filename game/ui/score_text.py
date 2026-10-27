"""The score's text: the one home of the SCORE format, shared by the HUD and the Game Over box.

Source: docs/contracts/systems/hud.md, Interface and Presentation, ``score_text``,
``graze_text``, ``best_text`` and ``group_digits``. Pure: no pygame, nothing logged.
"""

import logging
from typing import Final

log = logging.getLogger(__name__)

SCORE_LABEL: str = "SCORE"
"""Label before the digits. Scope report DRA-61, Limits (format); the label from the 10-ui.md
mockup. Not in the GDD (UI-01 is TBD)."""

DIGIT_GROUP: int = 3
"""Digits per group, counted from the right. Scope report DRA-61, Limits (format)."""

GROUP_SEPARATOR: str = " "
"""Text between two digit groups. Scope report DRA-61, Limits (Director: "Space: 1 234 567")."""

GRAZE_LABEL: str = "GRAZE"
"""Label before the graze count. Scope report DRA-117, Limits ("GRAZE <n>"); the label from the
10-ui.md mockup. Not in the GDD (UI-01 is TBD)."""

BEST_LABEL: Final[str] = "BEST"
"""Label before the best score. Scope report DRA-126, Values needed (BEST: ``BEST 1 234``).
Not in the GDD (UI-01 is TBD)."""


def score_text(score: int) -> str:
    """Return ``SCORE`` and the score's digits in groups of three, e.g. ``SCORE 1 234 567``.

    ``score`` is a whole number >= 0 from core, trusted and not checked. No leading zeros and no
    digit limit.
    """
    return SCORE_LABEL + GROUP_SEPARATOR + group_digits(score)


def graze_text(grazes: int) -> str:
    """Return ``GRAZE`` and the count's digits in groups of three, e.g. ``GRAZE 1 234``.

    ``grazes`` is a whole number >= 0 from core, trusted and not checked. Grouped exactly like
    the score: no leading zeros and no digit limit.
    """
    return GRAZE_LABEL + GROUP_SEPARATOR + group_digits(grazes)


def best_text(best: int) -> str:
    """Return ``BEST`` and the best score's digits in groups of three, e.g. ``BEST 1 234``.

    ``best`` is a whole number >= 0, trusted and not checked. Grouped like the score.
    """
    return BEST_LABEL + GROUP_SEPARATOR + group_digits(best)


def group_digits(number: int) -> str:
    """Return the decimal digits of ``number`` in groups of DIGIT_GROUP from the right.

    ``number`` is a whole number >= 0, trusted and not checked. The one home of the grouping:
    SCORE, GRAZE, BEST and the leaderboard's score all use it. Source: hud.md, Presentation.
    """
    digits: str = str(number)
    first: int = len(digits) % DIGIT_GROUP or DIGIT_GROUP
    groups: list[str] = [digits[:first]]
    groups.extend(
        digits[start : start + DIGIT_GROUP] for start in range(first, len(digits), DIGIT_GROUP)
    )
    return GROUP_SEPARATOR.join(groups)
