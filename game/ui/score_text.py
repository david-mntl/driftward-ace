"""The score's text: the one home of the SCORE format, shared by the HUD and the Game Over box.

Source: docs/contracts/systems/hud.md, Interface and Presentation, ``score_text`` and
``graze_text``. Pure: no pygame, nothing logged.
"""

import logging

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


def score_text(score: int) -> str:
    """Return ``SCORE`` and the score's digits in groups of three, e.g. ``SCORE 1 234 567``.

    ``score`` is a whole number >= 0 from core, trusted and not checked. No leading zeros and no
    digit limit.
    """
    return SCORE_LABEL + GROUP_SEPARATOR + _grouped(score)


def graze_text(grazes: int) -> str:
    """Return ``GRAZE`` and the count's digits in groups of three, e.g. ``GRAZE 1 234``.

    ``grazes`` is a whole number >= 0 from core, trusted and not checked. Grouped exactly like
    the score: no leading zeros and no digit limit.
    """
    return GRAZE_LABEL + GROUP_SEPARATOR + _grouped(grazes)


def _grouped(number: int) -> str:
    """Return the decimal digits of ``number`` in groups of DIGIT_GROUP from the right."""
    digits: str = str(number)
    first: int = len(digits) % DIGIT_GROUP or DIGIT_GROUP
    groups: list[str] = [digits[:first]]
    groups.extend(
        digits[start : start + DIGIT_GROUP] for start in range(first, len(digits), DIGIT_GROUP)
    )
    return GROUP_SEPARATOR.join(groups)
