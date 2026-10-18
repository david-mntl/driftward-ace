"""The score's text: the one home of the SCORE format, shared by the HUD and the Game Over box.

Source: docs/contracts/systems/hud.md, Interface and Presentation, ``score_text``. Pure: no
pygame, nothing logged.
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


def score_text(score: int) -> str:
    """Return ``SCORE`` and the score's digits in groups of three, e.g. ``SCORE 1 234 567``.

    ``score`` is a whole number >= 0 from core, trusted and not checked. No leading zeros and no
    digit limit.
    """
    digits: str = str(score)
    first: int = len(digits) % DIGIT_GROUP or DIGIT_GROUP
    groups: list[str] = [digits[:first]]
    groups.extend(
        digits[start : start + DIGIT_GROUP] for start in range(first, len(digits), DIGIT_GROUP)
    )
    return SCORE_LABEL + GROUP_SEPARATOR + GROUP_SEPARATOR.join(groups)
