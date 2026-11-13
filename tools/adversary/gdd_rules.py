"""The design numbers the checkers hold the game to, each with its GDD source.

These are copied from the GDD on purpose and are not read from the game: a check that reads its expected
value from the code under test can never fail. When the GDD changes one of these numbers, change it here too,
and a finding will tell you when the game and the GDD disagree.

Anything that only drives the game (bots, planner, scripts) must not use this file. It imports the
geometry from the game (`core.world`, `core.ship`), so there is one source for each fact.
"""

SCREEN_W = 640  # 03-world-and-camera.md
SCREEN_H = 480
TOP_LINE_Y = 84  # 0.175 * SCREEN_H: the ship's top edge never goes above it
SHIP_HALF = 16  # the ship is a 32 px square, so its centre stays this far from an edge
SPAWN_X, SPAWN_Y = 320.0, 240.0  # 05-lives-and-damage.md: where a respawn puts the ship, at rest

LIVES_START = 5  # 05-lives-and-damage.md, lives_start
INVULN_TICKS = 60  # 05-lives-and-damage.md, invuln_ticks: after a hit or a respawn (1 s)

LEVEL_COUNT = 8  # 08-difficulty.md
SCROLL_BASE = 1.1  # 03-world-and-camera.md: px per tick at Level 1
SCROLL_MULT = (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7)  # 08-difficulty.md: per level, Level 1 first
SCROLL_START_DELAY_TICKS = 30  # the world stands still for the first 30 ticks
