"""Screen geometry: the walls, the top line and the floor. Constants only, no imports.

DRA-6 has no camera, so world and screen are the same space. Screen px, x right, y down.
The left wall is x 0, the right wall is x SCREEN_W, the floor is y SCREEN_H.

Source: docs/contracts/DRA-6/DRA-6-world.md, Interface and Rules.
"""

SCREEN_W: int = 640
"""Screen width, px. Source: 03-world-and-camera.md, screen_w (guess)."""

SCREEN_H: int = 480
"""Screen height, px. Source: 03-world-and-camera.md, screen_h (guess)."""

TOP_LINE_RATIO: float = 0.35
"""Top line position as a share of SCREEN_H, from the top.

Source: 03-world-and-camera.md, top_line_ratio (locked).
"""

TOP_LINE_Y: int = round(SCREEN_H * TOP_LINE_RATIO)
"""Top line screen y, px: 168. Computed from the ratio, never a bare number.

Source: 03-world-and-camera.md, rule 2.
"""
