"""Game-over screen tests: the glass box, the place message, the score, the name picker, RETRY and
MENU.

Contract: docs/contracts/systems/screens.md, Interface (ui/game_over.py); 10-ui.md,
`game_over_screen`, `game_over_message` and `game_over_look`. Positions and colors are read from the
drawn pixels. The line tops come from the module's own layout, so the tests check what is drawn
where it says, not how the layout is worked out.
"""

import pygame

from core.game_flow import GameOverChoice
from core.saves import GameOverMessage, start_picker, turn_character
from ui.game_over import (
    MESSAGE_TEXTS,
    _layout,
    _score_cells,
    draw_final_score,
    draw_game_over,
    draw_game_over_choices,
    draw_name_picker,
)
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

SIZE: tuple[int, int] = (856, 518)
BLACK: tuple[int, int, int] = (0, 0, 0)


def _surface() -> pygame.Surface:
    return pygame.Surface(SIZE)


def _ink(surface: pygame.Surface) -> pygame.Rect:
    probe = surface.copy()
    probe.set_colorkey(BLACK)
    return probe.get_bounding_rect()


def _light(surface: pygame.Surface, rect: pygame.Rect) -> int:
    """Sum of every channel over ``rect``: how much light is drawn there."""
    area = surface.subsurface(rect.clip(surface.get_rect()))
    return sum(
        sum(area.get_at((x, y))[:3])
        for x in range(area.get_width())
        for y in range(area.get_height())
    )


def _band(box: pygame.Rect, top: int, height: int) -> pygame.Rect:
    return pygame.Rect(box.left + 6, top, box.width - 12, height)


def test_the_plain_box_is_the_size_in_the_tuning_file(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _surface()
    draw_game_over(surface, look)
    box = pygame.Rect(0, 0, screen_rules.game_over.w, screen_rules.game_over.h)
    box.center = (SIZE[0] // 2, SIZE[1] // 2)
    cyan = screen_rules.palette["frame_lights"]
    assert tuple(surface.get_at((box.left - 1, box.top - 1))[:3]) == cyan
    assert tuple(surface.get_at((box.right, box.bottom))[:3]) == cyan


def test_the_picker_box_is_bigger_and_still_centered(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _surface()
    draw_game_over(surface, look, GameOverMessage.TOP_3, picker_shown=True)
    rules = screen_rules.game_over
    box = pygame.Rect(0, 0, rules.picker_w, rules.picker_h)
    box.center = (SIZE[0] // 2, SIZE[1] // 2)
    cyan = screen_rules.palette["frame_lights"]
    assert tuple(surface.get_at((box.left - 1, box.top - 1))[:3]) == cyan
    assert tuple(surface.get_at((box.right, box.bottom))[:3]) == cyan


def test_every_message_draws_its_own_words_centered(look: ScreenLook) -> None:
    drawn: dict[GameOverMessage, bytes] = {}
    for message in GameOverMessage:
        surface = _surface()
        draw_game_over(surface, look, message)
        layout = _layout(look, SIZE, False)
        row = pygame.Rect(layout.box.left + 4, layout.message_top, layout.box.width - 8, 28)
        text = surface.subsurface(row)
        bright = text.copy()
        bright.set_colorkey(BLACK)
        # the glass is dark navy, not black: threshold at light text only
        mask = pygame.mask.from_threshold(text, (255, 255, 255), (90, 90, 90, 255))
        rects = mask.get_bounding_rects()
        left = min(r.left for r in rects)
        right = max(r.right for r in rects)
        assert abs((left + right) / 2 - row.width / 2) <= 2
        drawn[message] = pygame.image.tobytes(text, "RGB")
    assert len(set(drawn.values())) == len(GameOverMessage)
    assert set(MESSAGE_TEXTS.values()) == {"NEW BEST SCORE", "TOP 3", "TOP 10", "GAME OVER"}


def test_the_score_draws_lit_digits_between_the_message_and_the_choices(look: ScreenLook) -> None:
    surface = _surface()
    draw_game_over(surface, look)
    before = surface.copy()
    draw_final_score(surface, look, 61250)
    layout = _layout(look, SIZE, False)
    changed = _band(layout.box, layout.score_top, look.text_size("0", "digit")[1])
    assert _light(surface, changed) > _light(before, changed)
    assert layout.message_top < layout.score_top < layout.choices_top


def test_leading_zeros_are_dim_and_the_last_digit_never_is() -> None:
    cells = _score_cells(61250, 7)
    digits = [(char, dim) for char, dim in cells if char != " "]
    assert [char for char, _ in digits] == list("0061250")
    assert [dim for _, dim in digits] == [True, True, False, False, False, False, False]
    assert _score_cells(0, 7)[-1][1] is False
    assert [char for char, _ in _score_cells(7, 7) if char != " "][-1] == "7"


def test_digits_group_by_threes_from_the_right() -> None:
    assert "".join(char for char, _ in _score_cells(1312640, 7)) == "1 312 640"
    assert "".join(char for char, _ in _score_cells(61250, 7)) == "0 061 250"


def test_a_score_longer_than_the_digit_count_shows_in_full() -> None:
    assert "".join(char for char, _ in _score_cells(12345678, 7)) == "12 345 678"


def test_the_score_line_is_centered_on_the_box(look: ScreenLook) -> None:
    surface = _surface()
    draw_final_score(surface, look, 1312640)
    layout = _layout(look, SIZE, False)
    ink = _ink(surface)
    assert abs(ink.centerx - layout.box.centerx) <= 2


def test_the_slot_row_shows_ten_slots_and_the_picked_letters(look: ScreenLook) -> None:
    picker = start_picker("DAVID")
    surface = _surface()
    draw_name_picker(surface, look, picker, picking=True)
    layout = _layout(look, SIZE, True)
    rules = look.rules.game_over
    row = pygame.Rect(
        layout.box.left, layout.slots_top + rules.slot_pad_y, layout.box.width, rules.slot_h
    )
    lines = 0
    for x in range(row.left, row.right):
        if max(surface.get_at((x, row.bottom - 1))[:3]) > 40:
            lines += 1
    assert lines >= len(picker.slots) * (rules.slot_w - 2)
    assert (
        abs(
            _ink(surface.subsurface(pygame.Rect(0, row.top - 2, SIZE[0], rules.slot_h + 4))).centerx
            - SIZE[0] // 2
        )
        <= 3
    )


def test_the_cursor_slot_is_lit_and_has_an_arrow_above_and_below(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    picker = start_picker("DAVID")
    surface = _surface()
    draw_name_picker(surface, look, picker, picking=True)
    layout = _layout(look, SIZE, True)
    rules = screen_rules.game_over
    left = layout.box.centerx - (10 * rules.slot_w + 9 * rules.slot_gap) // 2
    top = layout.slots_top + rules.slot_pad_y
    cyan = screen_rules.palette["frame_lights"]
    above = (left + rules.slot_w // 2, top - rules.arrow_gap - 2)
    below = (left + rules.slot_w // 2, top + rules.slot_h + rules.arrow_gap + 2)
    assert tuple(surface.get_at(above)[:3]) == cyan
    assert tuple(surface.get_at(below)[:3]) == cyan
    other = (left + rules.slot_w + rules.slot_gap + rules.slot_w // 2, top - rules.arrow_gap - 2)
    assert tuple(surface.get_at(other)[:3]) == BLACK


def test_the_cursor_moves_with_the_picker(look: ScreenLook, screen_rules: ScreenRules) -> None:
    picker = turn_character(start_picker("DAVID"), 1)
    moved = picker.__class__(slots=picker.slots, cursor=3)
    first, second = _surface(), _surface()
    draw_name_picker(first, look, picker, picking=True)
    draw_name_picker(second, look, moved, picking=True)
    assert pygame.image.tobytes(first, "RGB") != pygame.image.tobytes(second, "RGB")


def test_the_hint_shows_five_key_caps_only_while_picking(look: ScreenLook) -> None:
    picker = start_picker("DAVID")
    picking, saved = _surface(), _surface()
    draw_name_picker(picking, look, picker, picking=True)
    draw_name_picker(saved, look, picker, picking=False)
    layout = _layout(look, SIZE, True)
    hint = pygame.Rect(layout.box.left, layout.hint_top, layout.box.width, look.rules.keycap.h)
    assert _light(picking, hint) > 0
    assert _light(saved, hint) == 0


def test_a_saved_name_has_no_cursor(look: ScreenLook) -> None:
    picker = start_picker("DAVID")
    saved = _surface()
    draw_name_picker(saved, look, picker, picking=False)
    layout = _layout(look, SIZE, True)
    rules = look.rules.game_over
    cell_top = layout.slots_top + rules.slot_pad_y
    above = pygame.Rect(
        layout.box.left, cell_top - rules.slot_pad_y, layout.box.width, rules.slot_pad_y - 1
    )
    assert _light(saved, above) == 0


def test_the_choices_move_their_light_with_the_selection(look: ScreenLook) -> None:
    retry, menu = _surface(), _surface()
    draw_game_over_choices(retry, look, GameOverChoice.RETRY)
    draw_game_over_choices(menu, look, GameOverChoice.MENU)
    layout = _layout(look, SIZE, False)
    rules = look.rules.game_over
    first = pygame.Rect(layout.box.left, layout.choices_top, layout.box.width, rules.choice_h)
    second = first.move(0, rules.choice_h + rules.choice_gap)
    assert _light(retry, first) > _light(menu, first)
    assert _light(menu, second) > _light(retry, second)


def test_choices_that_cannot_be_picked_yet_are_faint_and_unframed(look: ScreenLook) -> None:
    active, waiting = _surface(), _surface()
    draw_game_over_choices(active, look, GameOverChoice.RETRY, True, True)
    draw_game_over_choices(waiting, look, GameOverChoice.RETRY, True, False)
    layout = _layout(look, SIZE, True)
    rules = look.rules.game_over
    both = pygame.Rect(
        layout.box.left, layout.choices_top, layout.box.width, 2 * rules.choice_h + rules.choice_gap
    )
    assert _light(waiting, both) < _light(active, both)
    waiting_again = _surface()
    draw_game_over_choices(waiting_again, look, GameOverChoice.MENU, True, False)
    assert pygame.image.tobytes(waiting, "RGB") == pygame.image.tobytes(waiting_again, "RGB")


def test_the_lines_keep_their_order_in_both_boxes(look: ScreenLook) -> None:
    for picker_shown in (False, True):
        layout = _layout(look, SIZE, picker_shown)
        tops = [
            layout.message_top,
            layout.score_top,
            layout.slots_top,
            layout.hint_top,
            layout.choices_top,
        ]
        assert tops == sorted(tops)
        assert layout.box.top < layout.message_top
        assert layout.choices_top + 2 * look.rules.game_over.choice_h < layout.box.bottom


def test_drawing_twice_gives_the_same_pixels(look: ScreenLook) -> None:
    first, second = _surface(), _surface()
    picker = start_picker("DAVID")
    for surface in (first, second):
        draw_game_over(surface, look, GameOverMessage.NEW_BEST_SCORE, True)
        draw_final_score(surface, look, 1312640, True)
        draw_name_picker(surface, look, picker, True)
        draw_game_over_choices(surface, look, GameOverChoice.RETRY, True, False)
    assert pygame.image.tobytes(first, "RGB") == pygame.image.tobytes(second, "RGB")


def test_it_draws_on_another_surface_size(look: ScreenLook) -> None:
    surface = pygame.Surface((640, 480))
    draw_game_over(surface, look)
    draw_final_score(surface, look, 5)
    draw_game_over_choices(surface, look, GameOverChoice.MENU)
    assert abs(_ink(surface).centerx - 320) <= 2
    assert abs(_ink(surface).centery - 240) <= 2


def test_scores_from_zero_to_eight_digits_stay_inside_the_box(look: ScreenLook) -> None:
    layout = _layout(look, SIZE, False)
    for score in (0, 9_999_999, 99_999_999):
        surface = _surface()
        draw_final_score(surface, look, score)
        ink = _ink(surface)
        assert ink.width > 0
        assert layout.box.contains(ink), score
