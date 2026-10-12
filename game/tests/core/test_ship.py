"""Ship physics tests. Contract: docs/contracts/DRA-6/DRA-6-ship.md, Rules.

Task: docs/contracts/DRA-6/tasks/DRA-6-03-qa-engineer.md. One test per behavior it lists.
Every expected number is computed from the GDD values below, never typed in as a result.
"""

import logging

import pytest

from core.ship import Ship, Thrust, spawn, step

GRAVITY: float = 0.16
"""px/tick². Source: 04-ship.md, Values, gravity (guess)."""

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

THRUST_UP: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_up (guess)."""

THRUST_DOWN: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_down (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

SHIP_W: int = 32
"""px. Source: 04-ship.md, Values, ship_w (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

SCREEN_W: int = 640
"""px. Source: 03-world-and-camera.md, Values, screen_w (guess)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

TOP_LINE_RATIO: float = 0.35
"""Of screen_h, from the top. Source: 03-world-and-camera.md, Values, top_line_ratio (locked)."""

TOP_LINE_Y: int = round(SCREEN_H * TOP_LINE_RATIO)
"""Top line screen y. Source: 03-world-and-camera.md, rule 2; DRA-6-world.md, Interface (round)."""

START_X: float = 320.0
"""Source: 03-world-and-camera.md, ship_start (guess) = 05-lives-and-damage.md, fall_respawn."""

START_Y: float = 240.0
"""Source: 03-world-and-camera.md, ship_start (guess) = 05-lives-and-damage.md, fall_respawn."""

NO_KEY = Thrust()
SHIP_LOGGER = "core.ship"
"""Logger name. Source: DRA-6-ship.md, Rules, Logging."""


def _left_edge(ship: Ship) -> float:
    return ship.x - SHIP_W / 2


def _right_edge(ship: Ship) -> float:
    return ship.x + SHIP_W / 2


def _top_edge(ship: Ship) -> float:
    return ship.y - SHIP_H / 2


def _assert_same_ship(actual: Ship, expected: Ship) -> None:
    """Same position, speed and contact flags. Floats compared with approx."""
    assert actual.x == pytest.approx(expected.x)
    assert actual.y == pytest.approx(expected.y)
    assert actual.vx == pytest.approx(expected.vx)
    assert actual.vy == pytest.approx(expected.vy)
    assert actual.wall == expected.wall
    assert actual.at_top_line == expected.at_top_line


def _lines(caplog: pytest.LogCaptureFixture, prefix: str) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == SHIP_LOGGER and r.getMessage().startswith(prefix)
    ]


def test_ship_falls_with_no_input() -> None:
    ship = step(spawn(), NO_KEY)

    assert ship.vy == pytest.approx(GRAVITY)
    assert ship.y == pytest.approx(START_Y + GRAVITY)
    assert ship.x == pytest.approx(START_X)
    assert ship.vx == pytest.approx(0.0)


def test_up_thrust_beats_gravity() -> None:
    ship = step(spawn(), Thrust(up=True))

    assert ship.vy == pytest.approx(GRAVITY - THRUST_UP)
    assert ship.vy < 0
    assert ship.y < START_Y


def test_drag_slows_vx_only() -> None:
    first = step(spawn(), Thrust(right=True))
    assert first.vx == pytest.approx(THRUST_SIDE * DRAG_X)
    assert first.vy == pytest.approx(GRAVITY)

    second = step(first, NO_KEY)
    assert second.vx == pytest.approx(THRUST_SIDE * DRAG_X * DRAG_X)
    assert second.vy == pytest.approx(GRAVITY + GRAVITY)


def test_opposite_keys_cancel() -> None:
    moving = Ship(x=START_X, y=START_Y, vx=2.0, vy=-1.0)

    _assert_same_ship(step(moving, Thrust(left=True, right=True)), step(moving, NO_KEY))
    _assert_same_ship(step(moving, Thrust(up=True, down=True)), step(moving, NO_KEY))


def test_fall_speed_stops_at_fall_cap() -> None:
    near_cap = Ship(x=START_X, y=START_Y, vx=0.0, vy=FALL_CAP - GRAVITY / 2)

    ship = step(near_cap, Thrust(down=True))

    assert near_cap.vy + THRUST_DOWN + GRAVITY > FALL_CAP
    assert ship.vy == pytest.approx(FALL_CAP)
    assert ship.y == pytest.approx(START_Y + FALL_CAP)


def test_side_walls_stop_without_bounce() -> None:
    to_left = Ship(x=SHIP_W / 2 + 1, y=START_Y, vx=-3.0, vy=0.0)
    left = step(to_left, NO_KEY)
    assert _left_edge(left) == pytest.approx(0.0)
    assert left.vx == pytest.approx(0.0)
    assert left.wall == "left"
    after_left = step(left, NO_KEY)
    assert after_left.x == pytest.approx(left.x)
    assert after_left.vx == pytest.approx(0.0)

    to_right = Ship(x=SCREEN_W - SHIP_W / 2 - 1, y=START_Y, vx=3.0, vy=0.0)
    right = step(to_right, NO_KEY)
    assert _right_edge(right) == pytest.approx(SCREEN_W)
    assert right.vx == pytest.approx(0.0)
    assert right.wall == "right"
    after_right = step(right, NO_KEY)
    assert after_right.x == pytest.approx(right.x)
    assert after_right.vx == pytest.approx(0.0)


@pytest.mark.smoke
def test_top_line_stops_climb() -> None:
    ship = spawn()
    for _ in range(300):
        ship = step(ship, Thrust(up=True))
        assert _top_edge(ship) >= TOP_LINE_Y

    assert _top_edge(ship) == pytest.approx(TOP_LINE_Y)
    assert ship.vy == pytest.approx(0.0)


def test_floor_respawns_at_spawn() -> None:
    # Already at fall_cap, so the next tick moves y by exactly FALL_CAP.
    at_floor_y = SCREEN_H + SHIP_H / 2 - FALL_CAP
    for start_y in (at_floor_y, at_floor_y + 1):
        ship = step(Ship(x=100.0, y=start_y, vx=0.0, vy=FALL_CAP), NO_KEY)
        assert ship == spawn()
        assert (ship.x, ship.y, ship.vx, ship.vy) == pytest.approx((START_X, START_Y, 0.0, 0.0))

    just_above_y = at_floor_y - 0.5
    ship = step(Ship(x=100.0, y=just_above_y, vx=0.0, vy=FALL_CAP), NO_KEY)
    assert _top_edge(ship) < SCREEN_H
    assert ship.x == pytest.approx(100.0)
    assert ship.y == pytest.approx(just_above_y + FALL_CAP)
    assert ship.vy == pytest.approx(FALL_CAP)


def test_events_log_once(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=SHIP_LOGGER)
    on_line_y = TOP_LINE_Y + SHIP_H / 2

    # Up holds the ship at the top line, so it stays against the wall without falling.
    ship = Ship(x=SHIP_W / 2, y=on_line_y, vx=0.0, vy=0.0)
    for _ in range(60):
        ship = step(ship, Thrust(left=True, up=True))
    assert ship.wall == "left"
    assert len(_lines(caplog, "wall hit")) == 1

    caplog.clear()
    ship = Ship(x=START_X, y=on_line_y, vx=0.0, vy=0.0)
    for _ in range(60):
        ship = step(ship, Thrust(up=True))
    assert ship.at_top_line
    assert len(_lines(caplog, "top line stop")) == 1

    caplog.clear()
    ship = step(spawn(), NO_KEY)
    for _ in range(600):
        ship = step(ship, NO_KEY)
        if ship == spawn():
            break
    assert ship == spawn()
    assert len(_lines(caplog, "respawn")) == 1
