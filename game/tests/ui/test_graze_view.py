"""Graze view tests: the graze popup's color and the graze ring.

Contract: docs/contracts/systems/run.md, Presentation (the rows `popup.kind` and
`run.graze_rings`), Graze popup and Graze ring (DRA-117). Source of the values: 06-scoring.md,
graze_popup, graze_popup_color, graze_ring, graze_ring_color; drifters/04-coin.md, popup_color.

Pixels are read from the drawn surface (`pygame.image.tobytes`), never from the code under test.
The expected look is built in the test with pygame's own font and draw calls.
"""

import pygame

from core.graze import GrazeRing, GrazeRules, graze_popup, graze_ring
from core.popup import PointsPopup, PopupKind
from core.ship import Ship
from ui.graze_view import GRAZE_RING_COLOR, draw_graze_ring
from ui.popup_view import GRAZE_POPUP_COLOR, POPUP_COLOR, draw_points_popup

SURFACE_SIZE: tuple[int, int] = (200, 160)
"""Test surface, smaller than the screen so every pixel read stays quick. Source: the views
clip to the surface they are given (run.md, Graze ring, last bullet)."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Source: 12-art-and-audio.md, placeholder_bg (guess)."""

WHITE: tuple[int, int, int] = (255, 255, 255)

COIN_COLOR: tuple[int, int, int] = (255, 80, 150)
"""Source: drifters/04-coin.md, popup_color (guess)."""

GRAZE_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: 06-scoring.md, graze_popup_color (guess)."""

RING_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: 06-scoring.md, graze_ring_color (guess)."""

POPUP_FONT_SIZE = 16
"""Source: 06-scoring.md, graze_popup ("Same text size as the coin popup"); run.md, Points popup,
Look (16 px default font)."""

# Source: 06-scoring.md, graze_ring: 1 px, grows from 16 px to 32 px across in 15 ticks.
RING_TICKS = 15
RING_START = 16.0
RING_END = 32.0
RING_WIDTH = 1

assert GRAZE_POPUP_COLOR == GRAZE_COLOR
assert POPUP_COLOR == COIN_COLOR
assert GRAZE_RING_COLOR == RING_COLOR

Pixel = tuple[int, int]
Place = tuple[float, float]

PLACES: tuple[Place, ...] = ((100.0, 80.0), (60.4, 120.6), (150.5, 40.49), (30.0, 25.0))
"""Popup places, including ones that round up, down and at x.5 (Python's round)."""


def _blank(fill: tuple[int, int, int] = BLACK) -> pygame.Surface:
    surface = pygame.Surface(SURFACE_SIZE)
    surface.fill(fill)
    return surface


def _data(surface: pygame.Surface) -> bytes:
    return pygame.image.tobytes(surface, "RGB")


def _ink(surface: pygame.Surface) -> set[Pixel]:
    """(x, y) of every non-black pixel."""
    width, height = surface.get_size()
    data = _data(surface)
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if data[(y * width + x) * 3 : (y * width + x) * 3 + 3] != bytes(BLACK)
    }


# The popup, drawn in the color of its kind.


def _popup(kind: PopupKind, place: Place, points: int = 25, age: int = 0) -> PointsPopup:
    return PointsPopup(
        x=place[0],
        start_y=place[1],
        points=points,
        lifetime_ticks=60,
        rise_per_tick=0.5,
        age_ticks=age,
        kind=kind,
    )


def _drawn_popup(popup: PointsPopup) -> pygame.Surface:
    surface = _blank()
    draw_points_popup(surface, popup)
    return surface


def _expected_popup(
    points: int, color: tuple[int, int, int], center: tuple[int, int]
) -> pygame.Surface:
    """`+<points>` in the default font at 16 px, antialiased, centered on `center`."""
    text = pygame.font.Font(None, POPUP_FONT_SIZE).render(f"+{points}", True, color)
    surface = _blank()
    surface.blit(text, text.get_rect(center=center))
    return surface


def test_a_graze_popup_is_drawn_in_the_graze_color_and_a_coin_popup_in_the_coin_color(
    pygame_headless: None,
) -> None:
    # run.md, Presentation, `popup.kind`; Graze popup, Color: GRAZE_POPUP_COLOR for a graze,
    # POPUP_COLOR for a coin, centered on (round(x), round(y)).
    for place in PLACES:
        center = (round(place[0]), round(place[1]))
        for kind, color in ((PopupKind.GRAZE, GRAZE_COLOR), (PopupKind.COIN, COIN_COLOR)):
            drawn = _drawn_popup(_popup(kind, place))
            expected = _expected_popup(25, color, center)
            assert _ink(expected), "the reference drew nothing"
            assert _data(drawn) == _data(expected), f"{kind=}, {place=}: not +25 in {color}"
    # A popup built without `kind` is a coin's.
    plain = PointsPopup(x=100.0, start_y=80.0, points=50, lifetime_ticks=60, rise_per_tick=0.5)
    assert plain.kind is PopupKind.COIN
    assert _data(_drawn_popup(plain)) == _data(_expected_popup(50, COIN_COLOR, (100, 80)))


def test_a_graze_and_a_coin_popup_have_the_same_text_size_and_place(pygame_headless: None) -> None:
    # Graze popup: "Same text size as the coin popup", centered on the popup's place. Only the
    # color differs, so the ink sits on the same pixels.
    for place in PLACES:
        for points in (25, 50, 100, 1000):
            graze = _drawn_popup(_popup(PopupKind.GRAZE, place, points))
            coin = _drawn_popup(_popup(PopupKind.COIN, place, points))
            assert _ink(graze) == _ink(coin), f"{place=}, {points=}: size or place differs"
            assert _data(graze) != _data(coin), f"{place=}, {points=}: same color for both kinds"
            ink = _ink(graze)
            xs = [x for x, _ in ink]
            ys = [y for _, y in ink]
            center = (round(place[0]), round(place[1]))
            assert abs((min(xs) + max(xs)) / 2 - center[0]) <= 2, f"{place=}: not centered in x"
            assert abs((min(ys) + max(ys)) / 2 - center[1]) <= 2, f"{place=}: not centered in y"


def test_a_graze_popup_is_drawn_where_core_puts_it_and_follows_its_rise(
    pygame_headless: None,
) -> None:
    # run.md, Graze popup, Place: from core, at the ship's center, rising up the screen. The view
    # draws `popup.y` and never moves it.
    ship = Ship(x=100.0, y=90.0, vx=0.0, vy=0.0)
    popup = graze_popup(GrazeRules(), ship)
    assert popup.kind is PopupKind.GRAZE
    first = _drawn_popup(popup)
    assert _data(first) == _data(_expected_popup(25, GRAZE_COLOR, (100, 90)))
    for age in (1, 2, 10, 59):
        aged = _popup(PopupKind.GRAZE, (100.0, 90.0), age=age)
        rise = round(90.0 - age * 0.5)
        assert _data(_drawn_popup(aged)) == _data(_expected_popup(25, GRAZE_COLOR, (100, rise))), (
            f"{age=}: not drawn at the risen place"
        )


# The ring.


def _ring(age: int, **fields: float) -> GrazeRing:
    values: dict[str, float] = {
        "start_diameter": RING_START,
        "end_diameter": RING_END,
        "line_width": RING_WIDTH,
        "lifetime_ticks": RING_TICKS,
    }
    values.update(fields)
    return GrazeRing(
        start_diameter=values["start_diameter"],
        end_diameter=values["end_diameter"],
        line_width=int(values["line_width"]),
        lifetime_ticks=int(values["lifetime_ticks"]),
        age_ticks=age,
    )


def _ship_at(x: float, y: float) -> Ship:
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def _expected_ring_pixels(center: tuple[int, int], radius: int, width: int) -> set[Pixel]:
    """The pixels of a circle outline of `radius` and `width`, drawn opaque by pygame itself."""
    surface = _blank()
    pygame.draw.circle(surface, RING_COLOR, center, radius, width)
    return _ink(surface)


def _expected_radius(ring: GrazeRing, age: int) -> int:
    """Half the diameter, rounded: start + (end - start) * age / lifetime, from 06-scoring.md."""
    diameter = ring.start_diameter + (ring.end_diameter - ring.start_diameter) * age / (
        ring.lifetime_ticks
    )
    return round(diameter / 2)


def _expected_alpha(ring: GrazeRing, age: int) -> int:
    """Alpha 255 at age 0 falling steadily: round(255 * (1 - age / lifetime))."""
    return round(255 * (1 - age / ring.lifetime_ticks))


def _drawn_ring(ring: GrazeRing, ship: Ship, fill: tuple[int, int, int] = BLACK) -> pygame.Surface:
    surface = _blank(fill)
    draw_graze_ring(surface, ring, ship)
    return surface


def test_a_ring_is_an_opaque_circle_outline_on_the_ships_center_when_it_appears(
    pygame_headless: None,
) -> None:
    # run.md, Graze ring: radius round(diameter / 2) = 8 at age 0, line width 1, fully opaque.
    ship = _ship_at(100.0, 80.0)
    ring = _ring(0)
    drawn = _drawn_ring(ring, ship)
    expected = _blank()
    pygame.draw.circle(expected, RING_COLOR, (100, 80), 8, RING_WIDTH)
    assert _ink(expected), "the reference drew nothing"
    assert _data(drawn) == _data(expected), "the age 0 ring is not the 16 px outline"
    # Nothing is drawn on the center itself: an outline, not a disc.
    assert (100, 80) not in _ink(drawn)


def test_a_ring_grows_and_fades_on_every_state_it_shows(pygame_headless: None) -> None:
    # run.md, Graze ring, Size and Fade: radius round((16 + 16 * age / 15) / 2) and alpha
    # round(255 * (1 - age / 15)), above 0 on every state, so a ring shows on all 15 states.
    ship = _ship_at(100.0, 80.0)
    radii: list[int] = []
    alphas: list[int] = []
    for age in range(RING_TICKS):
        ring = _ring(age)
        radius = _expected_radius(ring, age)
        alpha = _expected_alpha(ring, age)
        assert alpha > 0, f"{age=}: the ring has no opacity on a state it shows"
        drawn = _drawn_ring(ring, ship)
        assert _ink(drawn) == _expected_ring_pixels((100, 80), radius, RING_WIDTH), (
            f"{age=}: not an outline of radius {radius}"
        )
        data = _data(drawn)
        width = SURFACE_SIZE[0]
        reds = {data[(y * width + x) * 3] for (x, y) in _ink(drawn)}
        assert max(reds) - min(reds) <= 1, f"{age=}: the ring's pixels are not one opacity"
        assert abs(max(reds) - alpha) <= 1, f"{age=}: opacity {max(reds)}, expected {alpha}"
        radii.append(radius)
        alphas.append(max(reds))
    assert radii == sorted(radii), f"the ring shrank: {radii}"
    assert radii[-1] > radii[0], f"the ring did not grow: {radii}"
    assert alphas == sorted(alphas, reverse=True), f"the ring got stronger: {alphas}"
    assert alphas[-1] < alphas[0], f"the ring did not fade: {alphas}"
    assert radii[0] == 8, "the ring does not start 16 px across"


def test_a_ring_follows_the_ship(pygame_headless: None) -> None:
    # run.md, Graze ring, Center: (round(ship.x), round(ship.y)) on this state.
    ring = _ring(6)
    radius = _expected_radius(ring, 6)
    for x, y in ((100.0, 80.0), (60.4, 120.6), (150.6, 40.4), (40.0, 100.0)):
        center = (round(x), round(y))
        drawn = _drawn_ring(ring, _ship_at(x, y))
        assert _ink(drawn) == _expected_ring_pixels(center, radius, RING_WIDTH), (
            f"ship at {(x, y)}: ring not centered on {center}"
        )
    # The same ring at two ship places is the same shape shifted.
    first = _ink(_drawn_ring(ring, _ship_at(80.0, 70.0)))
    second = _ink(_drawn_ring(ring, _ship_at(110.0, 90.0)))
    assert {(x + 30, y + 20) for (x, y) in first} == second


def test_a_ring_takes_its_size_and_width_from_the_ring(pygame_headless: None) -> None:
    # run.md, Graze ring, Size: line width `ring.line_width`, radius from the ring's own
    # diameters (a rule value from the app, not only the GDD's).
    ship = _ship_at(100.0, 80.0)
    for width in (1, 2, 3, 5):
        ring = _ring(0, line_width=width, start_diameter=40.0, end_diameter=60.0)
        assert _ink(_drawn_ring(ring, ship)) == _expected_ring_pixels((100, 80), 20, width), (
            f"{width=}: not an outline of that width"
        )
    wide = _ring(10, start_diameter=20.0, end_diameter=80.0, lifetime_ticks=20)
    radius = _expected_radius(wide, 10)
    assert radius == 25
    assert _ink(_drawn_ring(wide, ship)) == _expected_ring_pixels((100, 80), radius, RING_WIDTH)
    alpha = _expected_alpha(wide, 10)
    drawn = _drawn_ring(wide, ship)
    data = _data(drawn)
    reds = {data[(y * SURFACE_SIZE[0] + x) * 3] for (x, y) in _ink(drawn)}
    assert max(reds) - min(reds) <= 1, "the ring's pixels are not one opacity"
    assert abs(max(reds) - alpha) <= 1, f"opacity {max(reds)}, expected {alpha}"


def test_a_ring_draws_nothing_else_and_leaves_the_ship_untouched(pygame_headless: None) -> None:
    # run.md, Graze ring, Nothing else: no fill, no flash, no blink, no change to the ship.
    fill = (40, 40, 40)
    ship = _ship_at(100.0, 80.0)
    before = ship
    for age in (0, 7, 14):
        ring = _ring(age)
        background = _data(_blank(fill))
        drawn = _data(_drawn_ring(ring, ship, fill))
        ring_pixels = _expected_ring_pixels((100, 80), _expected_radius(ring, age), RING_WIDTH)
        width = SURFACE_SIZE[0]
        changed = {
            (i // 3 % width, i // 3 // width)
            for i in range(0, len(drawn), 3)
            if drawn[i : i + 3] != background[i : i + 3]
        }
        assert changed == ring_pixels, f"{age=}: pixels changed beyond the outline"
        assert ring == _ring(age), "the ring was changed"
    assert ship == before, "the ship was changed"
    # Drawing is repeatable: the same call gives the same pixels.
    ring = _ring(3)
    assert _data(_drawn_ring(ring, ship)) == _data(_drawn_ring(ring, ship))


def test_the_ring_from_core_is_drawn_as_the_gdd_ring(pygame_headless: None) -> None:
    # The ring `graze_ring` builds from the GDD's values is the 16 px, 1 px outline, white.
    ship = _ship_at(100.0, 80.0)
    ring = graze_ring(GrazeRules())
    assert (ring.start_diameter, ring.end_diameter) == (RING_START, RING_END)
    assert (ring.line_width, ring.lifetime_ticks, ring.age_ticks) == (RING_WIDTH, RING_TICKS, 0)
    expected = _blank()
    pygame.draw.circle(expected, RING_COLOR, (100, 80), 8, RING_WIDTH)
    assert _data(_drawn_ring(ring, ship)) == _data(expected)
