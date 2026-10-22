"""Wave editor bench: play, rewind and scrub the real game on the desktop, and edit waves.

    python tools/wave_editor/main.py [wave.json]

With no argument it plays the debug spawn list; with a wave file (a game wave or a sandbox file)
it plays that wave, looped. Reads the game read-only: no game code changes, and nothing is
written under game/ except by Promote.
"""

import sys
import time
from itertools import pairwise
from pathlib import Path

GAME_DIR: Path = Path(__file__).resolve().parents[2] / "game"
sys.path.insert(0, str(GAME_DIR))

import pygame
from bench import Bench
from core.run import Run
from core.ship import Thrust
from core.world import SCREEN_H, SCREEN_W
from doc import Doc
from editor import PALETTE_ROWS, TYPES, Editor, Row, place_text
from ui.debug_overlay import draw_debug_hitboxes
from ui.drifters.registry import render_drifter
from ui.look import BACKGROUND
from ui.popup_view import draw_points_popup
from ui.ship_view import draw_ship
from ui.starfield import draw_starfield

WINDOW: tuple[int, int] = (1240, 720)
LEFT_W: int = 300
GAME_POS: tuple[int, int] = (LEFT_W + 10, 10)
GAME_RECT: pygame.Rect = pygame.Rect(GAME_POS, (SCREEN_W, SCREEN_H))
RIGHT_X: int = GAME_POS[0] + SCREEN_W + 10
BAR: pygame.Rect = pygame.Rect(GAME_POS[0], GAME_POS[1] + SCREEN_H + 14, SCREEN_W, 14)
PANEL_BG = (22, 24, 32)
HIGHLIGHT = (50, 56, 80)
TEXT = (210, 214, 224)
DIM = (120, 126, 140)
ACCENT = (240, 200, 90)
BAD = (240, 90, 90)
SUB_HEADING = (160, 168, 190)
TRAIL = (110, 200, 150)
TRAIL_DIM = (60, 100, 80)
TAG_COLORS = {"W": ACCENT, "F": (120, 190, 240), "P": DIM}
TICK_SECONDS: float = 1 / 60
MAX_TICKS_PER_FRAME: int = 30
STEP_KEYS: dict[int, int] = {
    pygame.K_COMMA: -10,
    pygame.K_PERIOD: 10,
    pygame.K_z: -1,
    pygame.K_x: 1,
}
"""Keys that pause and move the playhead, and by how many ticks."""
SPEEDS: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
WAVE_PANEL: pygame.Rect = pygame.Rect(4, 4, LEFT_W, 206)
PALETTE_PANEL: pygame.Rect = pygame.Rect(4, 214, LEFT_W, 140)
VALUES_PANEL: pygame.Rect = pygame.Rect(
    RIGHT_X - 6, 112, WINDOW[0] - RIGHT_X, WINDOW[1] - 116
)
KEYS: tuple[tuple[str, str], ...] = (
    ("PLAY", ""),
    ("Space", "play / pause"),
    (", .", "step 10 ticks back / forward"),
    ("Z X", "step 1 tick back / forward"),
    ("W S", "speed up / down"),
    ("Home", "restart"),
    ("[ ]", "level down / up"),
    ("G", "ghost / fly"),
    ("1 2 3", "start left / centre / right"),
    ("L", "loop on / off"),
    ("F3", "hitboxes"),
    ("T", "path trail on / off"),
    ("EDIT", ""),
    ("Tab", "next panel"),
    ("Click", "panel, row, drifter, or place"),
    ("I", "palette invert on / off"),
    ("Up Down", "pick a row"),
    ("Left Right", "nudge (Shift x10) / palette side"),
    ("Enter", "type a value / add"),
    ("D", "default / drop a layer"),
    ("F", "cycle named file"),
    ("V", "save values as"),
    ("Del", "delete placement"),
    ("FILES", ""),
    ("Ctrl+S", "save"),
    ("Ctrl+Shift+S", "save as"),
    ("Ctrl+N", "new wave"),
    ("Ctrl+O", "open"),
    ("Ctrl+P", "promote"),
    ("Esc", "stop placing / back to game"),
)


def main() -> None:
    pygame.init()
    screen: pygame.Surface = pygame.display.set_mode(WINDOW)
    pygame.display.set_caption("Driftward wave editor")
    font: pygame.font.Font = pygame.font.Font(None, 18)
    small: pygame.font.Font = pygame.font.Font(None, 16)
    game: pygame.Surface = screen.subsurface(GAME_RECT)
    try:
        doc: Doc = (
            Doc.open(Path(sys.argv[1]).resolve()) if len(sys.argv) > 1 else Doc(None)
        )
        editor: Editor = Editor(Bench(doc))
    except (ValueError, OSError) as err:
        sys.exit(f"cannot start: {err}")
    bench: Bench = editor.bench
    clock = pygame.time.Clock()
    playing: bool = True
    speed_index: int = SPEEDS.index(1.0)
    hitboxes: bool = False
    scrubbing: bool = False
    accumulator: float = 0.0
    last_poll: float = time.perf_counter()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                scrubbing = route_click(event.pos, editor)
            if event.type == pygame.MOUSEWHEEL:
                editor.wheel_at(pygame.mouse.get_pos(), event.y)
            if event.type == pygame.MOUSEBUTTONUP:
                scrubbing = False
            if event.type == pygame.KEYDOWN and not editor.key(event):
                playing, speed_index, hitboxes = _key(
                    event.key, bench, playing, speed_index, hitboxes
                )
        if scrubbing:
            fraction: float = (pygame.mouse.get_pos()[0] - BAR.x) / BAR.w
            bench.seek(round(min(max(fraction, 0.0), 1.0) * (bench.total_ticks - 1)))
            playing = False
        now: float = time.perf_counter()
        if now - last_poll >= 0.5:
            last_poll = now
            bench.poll()
        accumulator += clock.tick(60) / 1000 * SPEEDS[speed_index]
        if playing:
            steering: bool = (
                not bench.ghost
                and editor.focus == "game"
                and editor.prompt is None
                and editor.promote is None
            )
            thrust: Thrust = _held_thrust() if steering else Thrust()
            ticks: int = 0
            while accumulator >= TICK_SECONDS and ticks < MAX_TICKS_PER_FRAME:
                bench.step(thrust)
                accumulator -= TICK_SECONDS
                ticks += 1
            accumulator = min(accumulator, TICK_SECONDS)
        else:
            accumulator = 0.0
        draw_all(
            screen, game, font, small, editor, playing, SPEEDS[speed_index], hitboxes
        )
        pygame.display.flip()


def draw_all(
    screen: pygame.Surface,
    game: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    editor: Editor,
    playing: bool,
    speed: float,
    hitboxes: bool,
) -> None:
    """One whole frame."""
    bench: Bench = editor.bench
    screen.fill(PANEL_BG)
    editor.hits.clear()
    _draw_game(game, editor, hitboxes)
    _draw_pointer(screen, font, editor)
    _draw_wave(screen, font, editor)
    _draw_palette(screen, font, editor)
    _draw_keys(screen, small)
    _draw_config(screen, font, bench, playing, speed, hitboxes)
    _draw_values(screen, font, editor)
    _draw_bar(screen, font, editor)
    if editor.promote is not None:
        _draw_promote(screen, font, editor)


def route_click(pos: tuple[int, int], editor: Editor) -> bool:
    """Send a left click to where it belongs. True if it grabbed the timeline bar (a scrub)."""
    if BAR.collidepoint(pos):
        return True
    if GAME_RECT.collidepoint(pos):
        editor.click((pos[0] - GAME_RECT.x, pos[1] - GAME_RECT.y))
    else:
        editor.press_at(pos)
    return False


def _key(
    key: int, bench: Bench, playing: bool, speed_index: int, hitboxes: bool
) -> tuple[bool, int, bool]:
    """Handle one bench key. Returns the new (playing, speed_index, hitboxes)."""
    if key == pygame.K_SPACE:
        playing = not playing
    elif key in STEP_KEYS:
        playing = False
        bench.seek(bench.tick + STEP_KEYS[key])
    elif key == pygame.K_w:
        speed_index = min(speed_index + 1, len(SPEEDS) - 1)
    elif key == pygame.K_s:
        speed_index = max(speed_index - 1, 0)
    elif key == pygame.K_HOME:
        bench.restart()
    elif key == pygame.K_LEFTBRACKET:
        bench.set_level(bench.level - 1)
    elif key == pygame.K_RIGHTBRACKET:
        bench.set_level(bench.level + 1)
    elif key == pygame.K_g:
        bench.toggle_ghost()
    elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
        bench.set_spot("LCR"[key - pygame.K_1])
    elif key == pygame.K_l:
        bench.loop = not bench.loop
    elif key == pygame.K_F3:
        hitboxes = not hitboxes
    return playing, speed_index, hitboxes


def _held_thrust() -> Thrust:
    pressed = pygame.key.get_pressed()
    return Thrust(
        up=pressed[pygame.K_UP],
        down=pressed[pygame.K_DOWN],
        left=pressed[pygame.K_LEFT],
        right=pressed[pygame.K_RIGHT],
    )


def _draw_game(surface: pygame.Surface, editor: Editor, hitboxes: bool) -> None:
    """The draw order of app.frame._draw, without the HUD and the overlay text, then a ring
    round the selected placement's drifter."""
    bench: Bench = editor.bench
    run: Run = bench.run
    surface.fill(BACKGROUND)
    draw_starfield(surface, run.scroll)
    for drifter in run.drifters:
        render_drifter(surface, drifter)
    for popup in run.popups:
        draw_points_popup(surface, popup)
    if not bench.ghost and run.ship_visible:
        draw_ship(surface, run.ship)
    if hitboxes:
        draw_debug_hitboxes(surface, run)
    if editor.trail and editor.selected is not None and bench.spawn_list is None:
        _draw_trail(surface, bench.preview_path(editor.selected))
    if editor.selected is not None and bench.spawn_list is None:
        for drifter in run.drifters:
            if drifter.uid == editor.selected + 1:
                pygame.draw.circle(
                    surface, ACCENT, (round(drifter.x), round(drifter.y)), 26, 2
                )


def _draw_trail(
    surface: pygame.Surface, points: tuple[tuple[float, float, bool], ...]
) -> None:
    """The selected drifter's path: a dim line while it warns, a bright one once active, and a
    dot every half second. A ring marks where it starts."""
    if len(points) < 2:
        return
    for (x0, y0, _), (x1, y1, active) in pairwise(points):
        colour = TRAIL if active else TRAIL_DIM
        pygame.draw.line(
            surface, colour, (round(x0), round(y0)), (round(x1), round(y1)), 1
        )
    for tick in range(0, len(points), 30):
        pygame.draw.circle(
            surface, TRAIL, (round(points[tick][0]), round(points[tick][1])), 2
        )
    pygame.draw.circle(surface, TRAIL, (round(points[0][0]), round(points[0][1])), 5, 1)


def _draw_pointer(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """Over the game view: the x and y under the mouse, game pixels. While a drifter is armed
    for placing, a crosshair too."""
    mouse: tuple[int, int] = pygame.mouse.get_pos()
    if not GAME_RECT.collidepoint(mouse) or editor.prompt is not None or editor.promote:
        return
    clip = screen.get_clip()
    screen.set_clip(GAME_RECT)
    if editor.armed is not None:
        for start, end in (
            ((GAME_RECT.left, mouse[1]), (GAME_RECT.right, mouse[1])),
            ((mouse[0], GAME_RECT.top), (mouse[0], GAME_RECT.bottom)),
        ):
            pygame.draw.line(screen, TRAIL, start, end, 1)
    label: str = f"x {mouse[0] - GAME_RECT.x}  y {mouse[1] - GAME_RECT.y}"
    width: int = font.size(label)[0]
    at_x: int = min(mouse[0] + 12, GAME_RECT.right - width - 4)
    at_y: int = min(mouse[1] + 12, GAME_RECT.bottom - font.get_linesize())
    screen.blit(font.render(label, True, TEXT), (at_x, at_y))
    screen.set_clip(clip)


def _lines(
    screen: pygame.Surface, font: pygame.font.Font, x: int, y: int, rows: list
) -> None:
    """Draw (text, color) rows, one font line each, from (x, y)."""
    for text, color in rows:
        screen.blit(font.render(text, True, color), (x, y))
        y += font.get_linesize()


def _panel(screen: pygame.Surface, rect: pygame.Rect, focused: bool) -> None:
    pygame.draw.rect(screen, ACCENT if focused else (46, 50, 64), rect, 1)


def _draw_wave(screen: pygame.Surface, font: pygame.font.Font, editor: Editor) -> None:
    """WAVE panel: the placements, the selected row highlighted, spawned rows bright."""
    bench: Bench = editor.bench
    run: Run = bench.run
    assert run.waves is not None
    _panel(screen, WAVE_PANEL, editor.focus == "wave")
    editor.panels["wave"] = WAVE_PANEL
    line: int = font.get_linesize()
    if bench.spawn_list is not None:
        title: str = f"SPAWN LIST  loop {bench.spawn_list.loop_ticks} ticks"
        texts: list[str] = [
            f"{due:>4}t  {p.drifter_type.value} {p.variant or ''}"
            for due, p in bench.spawn_list.schedule
        ]
        done: int = sum(
            1
            for due, _ in bench.spawn_list.schedule
            if due <= (bench.tick - 1) % bench.spawn_list.loop_ticks
        )
    else:
        title = f"WAVE {bench.doc.title}  {bench.wave.kind.value}  {bench.wave.length_px:.0f}px"
        texts = [
            f"{item.get('at_px', 0):>5.0f} {editor.seconds_at(item.get('at_px', 0)):>4.1f}s "
            f"{place_text(item):<10} {item.get('type', '?')} {item.get('variant') or ''}"
            for item in editor.placements()
        ]
        done = run.waves.spawned
    screen.blit(font.render(title, True, ACCENT), (10, 10))
    visible: int = (WAVE_PANEL.bottom - 40) // line
    anchor: int = editor.selected if editor.selected is not None else done
    start: int = max(0, min(anchor - visible // 2, len(texts) - visible))
    for row, text in enumerate(texts[start : start + visible], start):
        y: int = 34 + (row - start) * line
        editor.hits.append((pygame.Rect(8, y - 1, LEFT_W - 12, line), "wave", row))
        if row == editor.selected:
            pygame.draw.rect(screen, HIGHLIGHT, (8, y - 1, LEFT_W - 12, line))
        screen.blit(
            font.render(
                _fit(font, text, LEFT_W - 24), True, TEXT if row < done else DIM
            ),
            (14, y),
        )


def _draw_palette(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """DRIFTERS panel: the drifter types on the left, the variants of the chosen type on the
    right. Click a type to choose it, click a variant to add it to the wave."""
    focused: bool = editor.focus == "palette"
    _panel(screen, PALETTE_PANEL, focused)
    editor.panels["palette"] = PALETTE_PANEL
    title: str = (
        "DRIFTERS  click to place" if editor.doc.wave else "DRIFTERS  open a wave first"
    )
    screen.blit(font.render(title, True, ACCENT), (10, PALETTE_PANEL.y + 6))
    line: int = font.get_linesize()
    top: int = PALETTE_PANEL.y + 26
    variants: list[str] = editor.variants()
    default: str = editor.default_variant()
    columns = (
        (
            "type",
            10,
            128,
            list(TYPES),
            editor.palette_type,
            editor.palette_side == "types",
        ),
        (
            "variant",
            146,
            150,
            variants,
            editor.palette_variant,
            editor.palette_side == "variants",
        ),
    )
    _draw_switch(screen, font, editor)
    for kind, x, width, names, chosen, active in columns:
        editor.regions[kind] = pygame.Rect(x - 2, top, width, PALETTE_ROWS * line)
        start: int = min(editor.scroll[kind], max(len(names) - PALETTE_ROWS, 0))
        for number, name in enumerate(names[start : start + PALETTE_ROWS], start):
            y: int = top + (number - start) * line
            editor.hits.append((pygame.Rect(x - 2, y - 1, width, line), kind, number))
            if number == chosen:
                colour = HIGHLIGHT if focused and active else (36, 40, 54)
                pygame.draw.rect(screen, colour, (x - 2, y - 1, width, line))
            label: str = name + (" *" if kind == "variant" and name == default else "")
            armed: bool = kind == "variant" and editor.armed == (
                TYPES[editor.palette_type],
                name,
            )
            colour = ACCENT if armed else TEXT if number == chosen else DIM
            screen.blit(font.render(label, True, colour), (x, y))
        if len(names) > PALETTE_ROWS:
            more: str = (
                f"{start + 1}-{min(start + PALETTE_ROWS, len(names))}/{len(names)}"
            )
            screen.blit(font.render(more, True, DIM), (x, top + PALETTE_ROWS * line))


def _draw_switch(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """The invert switch at the top right of the palette: a pill, knob right and lit when on.
    Click it, or press I. It applies to the next drifter placed."""
    on: bool = editor.invert
    label: pygame.Surface = font.render("invert", True, ACCENT if on else DIM)
    pill: pygame.Rect = pygame.Rect(
        PALETTE_PANEL.right - 38, PALETTE_PANEL.y + 6, 28, 14
    )
    text_at: tuple[int, int] = (pill.x - label.get_width() - 8, pill.y)
    area: pygame.Rect = pygame.Rect(
        text_at[0] - 4, pill.y - 2, pill.right - text_at[0] + 8, 18
    )
    editor.hits.append((area, "invert", 0))
    pygame.draw.rect(screen, ACCENT if on else (46, 50, 64), pill, border_radius=7)
    knob_x: int = pill.right - 7 if on else pill.x + 7
    pygame.draw.circle(screen, (22, 24, 32) if on else DIM, (knob_x, pill.centery), 5)
    screen.blit(label, text_at)


def _draw_keys(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """The key table: the key, then what it does, in three groups."""
    x: int = 10
    y: int = PALETTE_PANEL.bottom + 8
    line: int = font.get_linesize()
    for key, action in KEYS:
        if not action:
            y += 2
            screen.blit(font.render(key, True, ACCENT), (x, y))
            pygame.draw.line(screen, (46, 50, 64), (x + 44, y + 6), (LEFT_W - 6, y + 6))
        else:
            screen.blit(font.render(key, True, TEXT), (x + 4, y))
            screen.blit(font.render(action, True, DIM), (x + 104, y))
        y += line


def _draw_config(
    screen: pygame.Surface,
    font: pygame.font.Font,
    bench: Bench,
    playing: bool,
    speed: float,
    hitboxes: bool,
) -> None:
    """CONFIG panel: the settings and the live numbers."""
    run: Run = bench.run
    rows: list = [
        ("CONFIG", ACCENT),
        (
            f"Level {bench.level}    Speed {speed:g}x {'playing' if playing else 'paused'}",
            TEXT,
        ),
        (f"Ship {'ghost' if bench.ghost else 'fly'}    Start {bench.spot}", TEXT),
        (
            f"Loop {'on' if bench.loop else 'off'}    Boxes {'on' if hitboxes else 'off'}",
            TEXT,
        ),
        (
            f"Tick {bench.tick}  {bench.tick / 60:.1f}s    Dist {run.scroll.distance_px:.0f}px",
            TEXT,
        ),
        (f"Drifters {len(run.drifters)}   Lives {run.lives}   Score {run.score}", TEXT),
        ("END of wave" if bench.ended else "", ACCENT),
    ]
    _lines(screen, font, RIGHT_X, 10, rows)


def _fit(font: pygame.font.Font, text: str, width: int) -> str:
    """Cut `text` with '..' so it is at most `width` px wide."""
    if font.size(text)[0] <= width:
        return text
    while text and font.size(text + "..")[0] > width:
        text = text[:-1]
    return text + ".."


def _draw_values(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """The wave's settings and the SELECTED placement: its fields, then its drifter type's values
    with W / F / P. Three columns: name, value, layer. Text never leaves its column."""
    _panel(screen, VALUES_PANEL, editor.focus == "values")
    editor.panels["values"] = VALUES_PANEL
    rows: list[Row] = editor.rows()
    index: str = f"#{editor.selected + 1}" if editor.selected is not None else "none"
    title: str = f"WAVE / SELECTED {index}"
    screen.blit(font.render(title, True, ACCENT), (RIGHT_X, VALUES_PANEL.y + 6))
    if not rows:
        hint: str = "open a wave first (Ctrl+O)" if editor.doc.wave is None else ""
        screen.blit(font.render(hint, True, DIM), (RIGHT_X, VALUES_PANEL.y + 28))
        return
    line: int = font.get_linesize()
    visible: int = (VALUES_PANEL.height - 34) // line
    start: int = max(0, min(editor.cursor - visible // 2, len(rows) - visible))
    name_w, value_x, value_w, tag_x = 160, 168, 90, 262
    for number, row in enumerate(rows[start : start + visible], start):
        y: int = VALUES_PANEL.y + 28 + (number - start) * line
        if number == editor.cursor and editor.focus == "values":
            pygame.draw.rect(
                screen, HIGHLIGHT, (RIGHT_X - 4, y - 1, VALUES_PANEL.width - 8, line)
            )
        area = pygame.Rect(RIGHT_X - 4, y - 1, VALUES_PANEL.width - 8, line)
        editor.hits.append((area, "row", number))
        heading: bool = row.key is None
        colour = SUB_HEADING if row.sub else ACCENT if heading else TEXT
        screen.blit(
            font.render(_fit(font, row.label, name_w), True, colour), (RIGHT_X, y)
        )
        width: int = value_w if row.tag else 112
        screen.blit(
            font.render(_fit(font, row.text, width), True, colour),
            (RIGHT_X + value_x, y),
        )
        if row.tag:
            screen.blit(
                font.render(row.tag, True, TAG_COLORS[row.tag]), (RIGHT_X + tag_x, y)
            )


def _draw_bar(screen: pygame.Surface, font: pygame.font.Font, editor: Editor) -> None:
    """The timeline, the time readout, the status line and the text prompt."""
    bench: Bench = editor.bench
    pygame.draw.rect(screen, (40, 44, 58), BAR)
    fraction: float = min(bench.tick / max(bench.total_ticks - 1, 1), 1.0)
    pygame.draw.rect(screen, ACCENT, (BAR.x, BAR.y, round(BAR.w * fraction), BAR.h))
    if bench.spawn_list is None:
        for item in bench.wave.placements:
            x: int = BAR.x + round(BAR.w * item.at_px / bench.wave.length_px)
            pygame.draw.line(screen, DIM, (x, BAR.y), (x, BAR.y + 4))
    readout: str = (
        f"{bench.tick / 60:.1f}s / {bench.total_ticks / 60:.1f}s    "
        f"{bench.run.scroll.distance_px:.0f}px / {bench.length_px:.0f}px"
    )
    _lines(screen, font, BAR.x, BAR.bottom + 6, [(readout, TEXT)])
    if bench.error:
        _lines(screen, font, BAR.x, BAR.bottom + 26, [("! " + bench.error[:105], BAD)])
    elif editor.message:
        _lines(screen, font, BAR.x, BAR.bottom + 26, [(editor.message[:105], ACCENT)])
    if editor.armed is not None:
        kind, variant = editor.armed
        hint: str = (
            f"PLACING {kind} {variant or ''}{' INVERTED' if editor.invert else ''}: "
            "click in the game view, Esc stops"
        )
        _lines(screen, font, BAR.x, BAR.bottom + 44, [(hint, TRAIL)])
    if editor.prompt is not None:
        box: pygame.Rect = pygame.Rect(BAR.x, BAR.bottom + 52, BAR.w, 24)
        pygame.draw.rect(screen, HIGHLIGHT, box)
        text: str = f"{editor.prompt.label}  {editor.prompt.text}_"
        screen.blit(font.render(text, True, TEXT), (box.x + 8, box.y + 6))
        _lines(screen, font, BAR.x, box.bottom + 4, [("Enter ok    Esc cancel", DIM)])


def _draw_promote(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """What Promote would write, over the game view. Space ticks, Enter writes."""
    view = editor.promote
    assert view is not None
    box: pygame.Rect = GAME_RECT.inflate(-30, -30)
    pygame.draw.rect(screen, (16, 18, 26), box)
    pygame.draw.rect(screen, ACCENT, box, 1)
    line: int = font.get_linesize()
    screen.blit(
        font.render("PROMOTE: write sandbox work into game files", True, ACCENT),
        (box.x + 12, box.y + 10),
    )
    y: int = box.y + 12 + line * 2
    for number, item in enumerate(view.items):
        if number == view.cursor:
            pygame.draw.rect(
                screen, HIGHLIGHT, (box.x + 6, y - 2, box.w - 12, line + 4)
            )
        mark: str = "[x]" if item.checked else "[ ]"
        screen.blit(font.render(f"{mark} {item.label}", True, TEXT), (box.x + 14, y))
        y += line + 2
        for text in item.lines:
            screen.blit(font.render(text, True, DIM), (box.x + 44, y))
            y += line
        y += 8
    notes: list = [
        ("wave_check: not built yet, nothing to run.", DIM),
        (
            "Space tick    Up Down pick    Enter write the ticked files    Esc cancel",
            TEXT,
        ),
        ("Nothing is committed.", DIM),
    ]
    _lines(screen, font, box.x + 12, box.bottom - line * 4, notes)


if __name__ == "__main__":
    main()
