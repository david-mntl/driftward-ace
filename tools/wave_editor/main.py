"""Wave editor bench: play, rewind and scrub the real game on the desktop, and edit waves.

    python tools/wave_editor/main.py [wave.json]

With no argument it plays the debug spawn list; with a wave file (a game wave or a sandbox file)
it plays that wave, looped. Reads the game read-only: no game code changes, and nothing is
written under game/ except by Promote.
"""

import sys
import time
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

GAME_DIR: Path = Path(__file__).resolve().parents[2] / "game"
sys.path.insert(0, str(GAME_DIR))

import pygame
from app.drifter_looks_tuning import install_drifter_looks
from bench import Bench
from core.run import Run
from core.ship import Thrust
from core.world import SCREEN_H, SCREEN_W
from doc import Doc
from editor import PALETTE_ROWS, TYPES, Editor, Row, place_text
from ui.debug_overlay import draw_debug_hitboxes
from ui.drifters.registry import render_drifter
from ui.graze_view import draw_graze_ring
from ui.look import BACKGROUND
from ui.popup_view import draw_points_popup
from ui.ship_view import draw_ship
from ui.starfield import draw_starfield

BASE_HEIGHT: int = 720
"""Window height at the smallest screen size. A bigger game view makes it taller."""
LEFT_W: int = 300
RIGHT_W: int = 280
"""Width of the right column, whatever the screen size."""
BELOW_GAME: int = 100
"""Room under the timeline for the readout, the messages and the text prompt."""
SCREEN_SCALES: tuple[float, ...] = (1.0, 1.5, 2.0)
"""The sizes the screen button cycles through (the game view is 640x480 times this). Only the
ones that fit the desktop are offered."""
DESKTOP_MARGIN: int = 70
"""Room kept on the desktop's height for the window's title bar and a task bar."""
PALETTE_H: int = 140
KEYS_LINE: int = 12
"""Height of a line of the key table (the small font)."""


@dataclass(frozen=True)
class Layout:
    """Where everything sits for one screen size. Only the game view and the panels around it
    grow; the text stays the size it is."""

    scale: float
    window: tuple[int, int]
    game_rect: pygame.Rect
    right_x: int
    bar: pygame.Rect
    wave_panel: pygame.Rect
    palette_panel: pygame.Rect
    values_panel: pygame.Rect
    size_button: pygame.Rect


def make_layout(scale: float) -> Layout:
    """The layout with the game view at `scale` times 640x480."""
    game_pos: tuple[int, int] = (LEFT_W + 10, 10)
    game_rect: pygame.Rect = pygame.Rect(
        game_pos, (round(SCREEN_W * scale), round(SCREEN_H * scale))
    )
    right_x: int = game_rect.right + 10
    bar: pygame.Rect = pygame.Rect(game_rect.x, game_rect.bottom + 14, game_rect.w, 14)
    window: tuple[int, int] = (
        right_x + RIGHT_W,
        max(BASE_HEIGHT, bar.bottom + BELOW_GAME),
    )
    # The key table sits at the bottom of the left column, whole. The palette is above it and
    # the WAVE list takes what is left, so a taller window gives the WAVE list more rows.
    palette_y: int = window[1] - KEYS_HEIGHT - PALETTE_H - 6
    return Layout(
        scale=scale,
        window=window,
        game_rect=game_rect,
        right_x=right_x,
        bar=bar,
        wave_panel=pygame.Rect(4, 4, LEFT_W, palette_y - 8),
        palette_panel=pygame.Rect(4, palette_y, LEFT_W, PALETTE_H),
        values_panel=pygame.Rect(right_x - 6, 126, RIGHT_W, window[1] - 130),
        size_button=pygame.Rect(right_x + 132, 6, 136, 15),
    )


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
MAX_FRAME_MS: int = 50
STEP_KEYS: dict[int, int] = {
    pygame.K_COMMA: -10,
    pygame.K_PERIOD: 10,
    pygame.K_z: -1,
    pygame.K_x: 1,
}
"""Keys that pause and move the playhead, and by how many ticks."""
SPEEDS: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
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
    ("F2", "next screen size"),
    ("EDIT", ""),
    ("Tab", "next panel"),
    ("Click", "panel, row, drifter, or place"),
    ("I / P / C", "invert / at spot / coin from top"),
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


KEYS_HEIGHT: int = (
    8 + len(KEYS) * KEYS_LINE + 2 * sum(1 for _, action in KEYS if not action)
)
"""Room the key table needs: the gap under the palette, a line per key, 2 px per heading."""
LAYOUT: Layout = make_layout(SCREEN_SCALES[0])
"""The layout in use. `_resize` replaces it when the screen size changes."""


def main() -> None:
    pygame.init()
    screen: pygame.Surface = _resize(LAYOUT.scale)
    pygame.display.set_caption("Driftward wave editor")
    font: pygame.font.Font = pygame.font.Font(None, 18)
    small: pygame.font.Font = pygame.font.Font(None, 16)
    game: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    """The game view at its own size. It is drawn here, then scaled onto the window."""
    try:
        doc: Doc = (
            Doc.open(Path(sys.argv[1]).resolve()) if len(sys.argv) > 1 else Doc(None)
        )
        editor: Editor = Editor(Bench(doc))
    except (ValueError, OSError) as err:
        sys.exit(f"cannot start: {err}")
    try:
        _run(screen, game, font, small, editor)
    finally:
        editor.close()


def _run(
    screen: pygame.Surface,
    game: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    editor: Editor,
) -> None:
    """The main loop, until the window is closed."""
    bench: Bench = editor.bench
    install_drifter_looks(bench.tuning)
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
                if LAYOUT.size_button.collidepoint(event.pos):
                    screen = _cycle_size(editor)
                else:
                    scrubbing = route_click(event.pos, editor)
            if event.type == pygame.MOUSEWHEEL:
                editor.wheel_at(pygame.mouse.get_pos(), event.y)
            if event.type == pygame.MOUSEBUTTONUP:
                scrubbing = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                screen = _cycle_size(editor)
            elif event.type == pygame.KEYDOWN and not editor.key(event):
                playing, speed_index, hitboxes = _key(
                    event.key, bench, playing, speed_index, hitboxes
                )
        if scrubbing:
            fraction: float = (pygame.mouse.get_pos()[0] - LAYOUT.bar.x) / LAYOUT.bar.w
            bench.seek(round(min(max(fraction, 0.0), 1.0) * (bench.total_ticks - 1)))
            playing = False
        now: float = time.perf_counter()
        if now - last_poll >= 0.5:
            last_poll = now
            bench.poll()
        editor.poll_job()
        # A slow frame must not make the game rush to catch up: at most 50 ms count.
        accumulator += min(clock.tick(60), MAX_FRAME_MS) / 1000 * SPEEDS[speed_index]
        if playing:
            steering: bool = (
                not bench.ghost
                and editor.focus == "game"
                and editor.prompt is None
                and editor.promote is None
                and editor.picker is None
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


def _resize(scale: float) -> pygame.Surface:
    """Use the layout for `scale` and size the window to it. Returns the window's surface."""
    global LAYOUT
    LAYOUT = make_layout(scale)
    return pygame.display.set_mode(LAYOUT.window)


def available_scales() -> list[float]:
    """The screen sizes whose window fits the desktop, smallest first. Always has 1x."""
    try:
        sizes: list[tuple[int, int]] = pygame.display.get_desktop_sizes()
    except pygame.error:
        sizes = []
    width, height = max(sizes, default=(0, 0))
    return [
        scale
        for scale in SCREEN_SCALES
        if scale == SCREEN_SCALES[0]
        or (
            width
            and make_layout(scale).window[0] <= width
            and make_layout(scale).window[1] <= height - DESKTOP_MARGIN
        )
    ]


def _cycle_size(editor: Editor) -> pygame.Surface:
    """Go to the next screen size that fits the desktop (the button and F2)."""
    options: list[float] = available_scales()
    now: int = options.index(LAYOUT.scale) if LAYOUT.scale in options else 0
    scale: float = options[(now + 1) % len(options)]
    editor.message = (
        f"screen size {scale:g}x"
        if len(options) > 1
        else "the desktop has no room for a bigger screen"
    )
    return _resize(scale)


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
    rect: pygame.Rect = LAYOUT.game_rect
    if rect.size == game.get_size():
        screen.blit(game, rect)
    else:
        pygame.transform.scale(game, rect.size, screen.subsurface(rect))
    _draw_pointer(screen, font, editor)
    _draw_wave(screen, font, editor)
    _draw_palette(screen, font, editor)
    _draw_keys(screen, small)
    _draw_config(screen, font, bench, playing, speed, hitboxes)
    _draw_values(screen, font, editor)
    _draw_bar(screen, font, editor)
    if editor.promote is not None:
        _draw_promote(screen, font, editor)
    if editor.picker is not None:
        _draw_open(screen, font, editor)


def route_click(pos: tuple[int, int], editor: Editor) -> bool:
    """Send a left click to where it belongs. True if it grabbed the timeline bar (a scrub)."""
    if editor.picker is not None:
        editor.pick_at(pos)
        return False
    if LAYOUT.bar.collidepoint(pos):
        return True
    if LAYOUT.game_rect.collidepoint(pos):
        editor.click(game_point(pos))
    else:
        editor.press_at(pos)
    return False


def game_point(pos: tuple[int, int]) -> tuple[int, int]:
    """The game pixel under a window position, at any screen size."""
    rect: pygame.Rect = LAYOUT.game_rect
    return (
        min(round((pos[0] - rect.x) / LAYOUT.scale), SCREEN_W),
        min(round((pos[1] - rect.y) / LAYOUT.scale), SCREEN_H),
    )


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
    """The draw order of app.frame._draw (graze rings after the ship), without the HUD and the
    overlay text, then a ring round the selected placement's drifter."""
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
    for ring in run.graze_rings:
        draw_graze_ring(surface, ring, run.ship)
    if hitboxes:
        draw_debug_hitboxes(surface, run)
    if editor.trail and editor.selected is not None and bench.spawn_list is None:
        surface.blit(_trail_layer(bench.preview_path(editor.selected)), (0, 0))
    if editor.selected is not None and bench.spawn_list is None:
        for drifter in run.drifters:
            if drifter.uid == editor.selected + 1:
                pygame.draw.circle(
                    surface, ACCENT, (round(drifter.x), round(drifter.y)), 26, 2
                )


_TRAIL_LAYER: list = [None, None]
"""The path the layer was drawn for, and the layer. A path is the same object while it is cached."""


def _trail_layer(points: tuple[tuple[float, float, bool], ...]) -> pygame.Surface:
    """The selected drifter's path as a see-through layer the size of the game view: a dim line
    while it warns, a bright one once active, a dot every half second, and a ring where it
    starts. Drawn when the path changes, then only blitted: it is hundreds of line segments."""
    if _TRAIL_LAYER[0] is not points:
        layer: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if len(points) >= 2:
            for (x0, y0, _), (x1, y1, active) in pairwise(points):
                pygame.draw.line(
                    layer,
                    TRAIL if active else TRAIL_DIM,
                    (round(x0), round(y0)),
                    (round(x1), round(y1)),
                    1,
                )
            for tick in range(0, len(points), 30):
                pygame.draw.circle(
                    layer, TRAIL, (round(points[tick][0]), round(points[tick][1])), 2
                )
            pygame.draw.circle(
                layer, TRAIL, (round(points[0][0]), round(points[0][1])), 5, 1
            )
        _TRAIL_LAYER[:] = [points, layer]
    return _TRAIL_LAYER[1]


def _draw_pointer(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """Over the game view: the x and y under the mouse, game pixels. While a drifter is armed
    for placing, a crosshair too."""
    mouse: tuple[int, int] = pygame.mouse.get_pos()
    if (
        not LAYOUT.game_rect.collidepoint(mouse)
        or editor.prompt is not None
        or editor.promote
        or editor.picker
    ):
        return
    clip = screen.get_clip()
    screen.set_clip(LAYOUT.game_rect)
    if editor.armed is not None:
        for start, end in (
            ((LAYOUT.game_rect.left, mouse[1]), (LAYOUT.game_rect.right, mouse[1])),
            ((mouse[0], LAYOUT.game_rect.top), (mouse[0], LAYOUT.game_rect.bottom)),
        ):
            pygame.draw.line(screen, TRAIL, start, end, 1)
    at: tuple[int, int] = game_point(mouse)
    label: str = f"x {at[0]}  y {at[1]}"
    width: int = font.size(label)[0]
    at_x: int = min(mouse[0] + 12, LAYOUT.game_rect.right - width - 4)
    at_y: int = min(mouse[1] + 12, LAYOUT.game_rect.bottom - font.get_linesize())
    screen.blit(_text(font, label, TEXT), (at_x, at_y))
    screen.set_clip(clip)


_TEXT_CACHE: dict[tuple[int, str, tuple[int, int, int]], pygame.Surface] = {}
_TEXT_CACHE_MAX: int = 1500
_FIT_CACHE: dict[tuple[int, str, int], str] = {}


def _text(
    font: pygame.font.Font, string: str, color: tuple[int, int, int]
) -> pygame.Surface:
    """`string` rendered in `color`. Most labels are the same every frame, so a render is kept
    and drawn again; drawing 160 labels fresh every frame was a third of the frame's time."""
    key: tuple[int, str, tuple[int, int, int]] = (id(font), string, color)
    surface: pygame.Surface | None = _TEXT_CACHE.get(key)
    if surface is None:
        if len(_TEXT_CACHE) >= _TEXT_CACHE_MAX:
            _TEXT_CACHE.clear()
        surface = _TEXT_CACHE[key] = font.render(string, True, color)
    return surface


def _lines(
    screen: pygame.Surface, font: pygame.font.Font, x: int, y: int, rows: list
) -> None:
    """Draw (text, color) rows, one font line each, from (x, y)."""
    for text, color in rows:
        screen.blit(_text(font, text, color), (x, y))
        y += font.get_linesize()


def _panel(screen: pygame.Surface, rect: pygame.Rect, focused: bool) -> None:
    pygame.draw.rect(screen, ACCENT if focused else (46, 50, 64), rect, 1)


_WAVE_TEXTS: list = [None, []]
"""The WAVE list's lines and the (revision, level) they were made for."""


def _draw_wave(screen: pygame.Surface, font: pygame.font.Font, editor: Editor) -> None:
    """WAVE panel: the placements, the selected row highlighted, spawned rows bright."""
    bench: Bench = editor.bench
    run: Run = bench.run
    assert run.waves is not None
    _panel(screen, LAYOUT.wave_panel, editor.focus == "wave")
    editor.panels["wave"] = LAYOUT.wave_panel
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
        wave_key: tuple[int, int] = (bench.revision, bench.level)
        if _WAVE_TEXTS[0] != wave_key:
            _WAVE_TEXTS[:] = [
                wave_key,
                [
                    f"{item.get('at_px', 0):>5.0f} {editor.seconds_at(item.get('at_px', 0)):>4.1f}s "
                    f"{place_text(item):<10} {item.get('type', '?')} {item.get('variant') or ''}"
                    for item in editor.placements()
                ],
            ]
        texts = _WAVE_TEXTS[1]
        done = run.waves.spawned
    screen.blit(_text(font, title, ACCENT), (10, 10))
    visible: int = (LAYOUT.wave_panel.bottom - 40) // line
    anchor: int = editor.selected if editor.selected is not None else done
    start: int = max(0, min(anchor - visible // 2, len(texts) - visible))
    for row, text in enumerate(texts[start : start + visible], start):
        y: int = 34 + (row - start) * line
        editor.hits.append((pygame.Rect(8, y - 1, LEFT_W - 12, line), "wave", row))
        if row == editor.selected:
            pygame.draw.rect(screen, HIGHLIGHT, (8, y - 1, LEFT_W - 12, line))
        screen.blit(
            _text(font, _fit(font, text, LEFT_W - 24), TEXT if row < done else DIM),
            (14, y),
        )


def _draw_palette(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """DRIFTERS panel: the drifter types on the left, the variants of the chosen type on the
    right. Click a type to choose it, click a variant to add it to the wave."""
    focused: bool = editor.focus == "palette"
    _panel(screen, LAYOUT.palette_panel, focused)
    editor.panels["palette"] = LAYOUT.palette_panel
    title: str = (
        "DRIFTERS  click to place" if editor.doc.wave else "DRIFTERS  open a wave first"
    )
    screen.blit(_text(font, title, ACCENT), (10, LAYOUT.palette_panel.y + 6))
    line: int = font.get_linesize()
    top: int = LAYOUT.palette_panel.y + 26
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
            screen.blit(_text(font, label, colour), (x, y))
        if len(names) > PALETTE_ROWS:
            more: str = (
                f"{start + 1}-{min(start + PALETTE_ROWS, len(names))}/{len(names)}"
            )
            screen.blit(_text(font, more, DIM), (x, top + PALETTE_ROWS * line))


def _draw_switch(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """The invert switch at the top right of the palette: a pill, knob right and lit when on.
    Click it, or press I. It applies to the next drifter placed."""
    on: bool = editor.invert
    label: pygame.Surface = _text(font, "invert", ACCENT if on else DIM)
    pill: pygame.Rect = pygame.Rect(
        LAYOUT.palette_panel.right - 38, LAYOUT.palette_panel.y + 6, 28, 14
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
    y: int = LAYOUT.palette_panel.bottom + 8
    line: int = KEYS_LINE
    for key, action in KEYS:
        if not action:
            y += 2
            screen.blit(_text(font, key, ACCENT), (x, y))
            pygame.draw.line(screen, (46, 50, 64), (x + 44, y + 6), (LEFT_W - 6, y + 6))
        else:
            screen.blit(_text(font, key, TEXT), (x + 4, y))
            screen.blit(_text(font, action, DIM), (x + 104, y))
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
        (
            f"Grazes {run.grazes}   Margin {bench.tuning.hazards.graze_margin:g}px"
            + ("   (ghost: no grazes)" if bench.ghost else ""),
            TEXT,
        ),
        ("END of wave" if bench.ended else "", ACCENT),
    ]
    _lines(screen, font, LAYOUT.right_x, 10, rows)
    _draw_size_button(screen, font)


def _draw_size_button(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """The screen size button on the CONFIG title row: click it, or press F2, for the next
    size. The label shows the size now."""
    area: pygame.Rect = LAYOUT.size_button
    hover: bool = area.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(
        screen, HIGHLIGHT if hover else (36, 40, 54), area, border_radius=4
    )
    pygame.draw.rect(
        screen, ACCENT if hover else (46, 50, 64), area, 1, border_radius=4
    )
    label: pygame.Surface = _text(
        font, f"Screen {LAYOUT.scale:g}x  F2", ACCENT if hover else TEXT
    )
    screen.blit(
        label,
        (area.centerx - label.get_width() // 2, area.centery - label.get_height() // 2),
    )


def _fit(font: pygame.font.Font, text: str, width: int) -> str:
    """Cut `text` with '..' so it is at most `width` px wide."""
    key: tuple[int, str, int] = (id(font), text, width)
    fitted: str | None = _FIT_CACHE.get(key)
    if fitted is None:
        fitted = text
        if font.size(text)[0] > width:
            while fitted and font.size(fitted + "..")[0] > width:
                fitted = fitted[:-1]
            fitted += ".."
        if len(_FIT_CACHE) >= _TEXT_CACHE_MAX:
            _FIT_CACHE.clear()
        _FIT_CACHE[key] = fitted
    return fitted


def _draw_values(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """The wave's settings and the SELECTED placement: its fields, then its drifter type's values
    with W / F / P. Three columns: name, value, layer. Text never leaves its column."""
    _panel(screen, LAYOUT.values_panel, editor.focus == "values")
    editor.panels["values"] = LAYOUT.values_panel
    rows: list[Row] = editor.rows()
    index: str = f"#{editor.selected + 1}" if editor.selected is not None else "none"
    title: str = f"WAVE / SELECTED {index}"
    screen.blit(_text(font, title, ACCENT), (LAYOUT.right_x, LAYOUT.values_panel.y + 6))
    if not rows:
        hint: str = "open a wave first (Ctrl+O)" if editor.doc.wave is None else ""
        screen.blit(
            _text(font, hint, DIM), (LAYOUT.right_x, LAYOUT.values_panel.y + 28)
        )
        return
    line: int = font.get_linesize()
    visible: int = (LAYOUT.values_panel.height - 34) // line
    start: int = max(0, min(editor.cursor - visible // 2, len(rows) - visible))
    name_w, value_x, value_w, tag_x = 160, 168, 90, 262
    for number, row in enumerate(rows[start : start + visible], start):
        y: int = LAYOUT.values_panel.y + 28 + (number - start) * line
        if number == editor.cursor and editor.focus == "values":
            pygame.draw.rect(
                screen,
                HIGHLIGHT,
                (LAYOUT.right_x - 4, y - 1, LAYOUT.values_panel.width - 8, line),
            )
        area = pygame.Rect(
            LAYOUT.right_x - 4, y - 1, LAYOUT.values_panel.width - 8, line
        )
        editor.hits.append((area, "row", number))
        heading: bool = row.key is None
        colour = SUB_HEADING if row.sub else ACCENT if heading else TEXT
        screen.blit(
            _text(font, _fit(font, row.label, name_w), colour), (LAYOUT.right_x, y)
        )
        width: int = value_w if row.tag else 112
        screen.blit(
            _text(font, _fit(font, row.text, width), colour),
            (LAYOUT.right_x + value_x, y),
        )
        if row.tag:
            screen.blit(
                _text(font, row.tag, TAG_COLORS[row.tag]), (LAYOUT.right_x + tag_x, y)
            )


def _draw_bar(screen: pygame.Surface, font: pygame.font.Font, editor: Editor) -> None:
    """The timeline, the time readout, the status line and the text prompt."""
    bench: Bench = editor.bench
    pygame.draw.rect(screen, (40, 44, 58), LAYOUT.bar)
    fraction: float = min(bench.tick / max(bench.total_ticks - 1, 1), 1.0)
    pygame.draw.rect(
        screen,
        ACCENT,
        (LAYOUT.bar.x, LAYOUT.bar.y, round(LAYOUT.bar.w * fraction), LAYOUT.bar.h),
    )
    if bench.spawn_list is None:
        for item in bench.wave.placements:
            x: int = LAYOUT.bar.x + round(
                LAYOUT.bar.w * item.at_px / bench.wave.length_px
            )
            pygame.draw.line(screen, DIM, (x, LAYOUT.bar.y), (x, LAYOUT.bar.y + 4))
    readout: str = (
        f"{bench.tick / 60:.1f}s / {bench.total_ticks / 60:.1f}s    "
        f"{bench.run.scroll.distance_px:.0f}px / {bench.length_px:.0f}px"
    )
    _lines(screen, font, LAYOUT.bar.x, LAYOUT.bar.bottom + 6, [(readout, TEXT)])
    if editor.job is not None and not editor.job.cancelled:
        dots: str = "." * (int(time.perf_counter() * 3) % 4)
        _lines(
            screen,
            font,
            LAYOUT.bar.x,
            LAYOUT.bar.bottom + 26,
            [(f"{editor.job.label}{dots}  Esc stops", TRAIL)],
        )
    elif bench.error:
        _lines(
            screen,
            font,
            LAYOUT.bar.x,
            LAYOUT.bar.bottom + 26,
            [("! " + bench.error[:105], BAD)],
        )
    elif editor.message:
        _lines(
            screen,
            font,
            LAYOUT.bar.x,
            LAYOUT.bar.bottom + 26,
            [(editor.message[:105], ACCENT)],
        )
    if editor.armed is not None:
        kind, variant = editor.armed
        hint: str = (
            f"PLACING {kind} {variant or ''}{' INVERTED' if editor.invert else ''}"
            f"{' FROM TOP' if editor.from_top(kind) else ''}"
            f"{' AT SPOT' if editor.at_spot else ''}: "
            + (
                "click where it should be now, Esc stops"
                if editor.at_spot
                else "click in the game view, Esc stops"
            )
        )
        _lines(screen, font, LAYOUT.bar.x, LAYOUT.bar.bottom + 44, [(hint, TRAIL)])
    if editor.prompt is not None:
        box: pygame.Rect = pygame.Rect(
            LAYOUT.bar.x, LAYOUT.bar.bottom + 52, LAYOUT.bar.w, 24
        )
        pygame.draw.rect(screen, HIGHLIGHT, box)
        text: str = f"{editor.prompt.label}  {editor.prompt.text}_"
        screen.blit(_text(font, text, TEXT), (box.x + 8, box.y + 6))
        _lines(
            screen,
            font,
            LAYOUT.bar.x,
            box.bottom + 4,
            [("Enter ok    Esc cancel", DIM)],
        )


def _draw_promote(
    screen: pygame.Surface, font: pygame.font.Font, editor: Editor
) -> None:
    """What Promote would write, over the game view. Space ticks, Enter writes."""
    view = editor.promote
    assert view is not None
    box: pygame.Rect = LAYOUT.game_rect.inflate(-30, -30)
    pygame.draw.rect(screen, (16, 18, 26), box)
    pygame.draw.rect(screen, ACCENT, box, 1)
    line: int = font.get_linesize()
    screen.blit(
        _text(font, "PROMOTE: write sandbox work into game files", ACCENT),
        (box.x + 12, box.y + 10),
    )
    y: int = box.y + 12 + line * 2
    for number, item in enumerate(view.items):
        if number == view.cursor:
            pygame.draw.rect(
                screen, HIGHLIGHT, (box.x + 6, y - 2, box.w - 12, line + 4)
            )
        mark: str = "[x]" if item.checked else "[ ]"
        screen.blit(_text(font, f"{mark} {item.label}", TEXT), (box.x + 14, y))
        y += line + 2
        for text in item.lines:
            screen.blit(_text(font, text, DIM), (box.x + 44, y))
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


def _draw_open(screen: pygame.Surface, font: pygame.font.Font, editor: Editor) -> None:
    """The Open list over the game view: what is typed, then the files that match it."""
    view = editor.picker
    assert view is not None
    box: pygame.Rect = LAYOUT.game_rect.inflate(-30, -30)
    pygame.draw.rect(screen, (16, 18, 26), box)
    pygame.draw.rect(screen, ACCENT, box, 1)
    line: int = font.get_linesize()
    title: str = "OPEN a wave" + (
        "   (unsaved changes are dropped)" if editor.doc.dirty else ""
    )
    screen.blit(_text(font, title, ACCENT), (box.x + 12, box.y + 10))
    find: pygame.Rect = pygame.Rect(box.x + 10, box.y + 14 + line, box.w - 20, line + 8)
    pygame.draw.rect(screen, HIGHLIGHT, find)
    screen.blit(_text(font, f"Find  {view.text}_", TEXT), (find.x + 6, find.y + 4))
    shown: list[Path] = view.shown()
    top_y: int = find.bottom + 8
    view.rows = max((box.bottom - line * 3 - top_y) // (line + 2), 1)
    here: Path | None = editor.doc.source_file
    for number in range(view.top, min(view.top + view.rows, len(shown))):
        path: Path = shown[number]
        y: int = top_y + (number - view.top) * (line + 2)
        row: pygame.Rect = pygame.Rect(box.x + 6, y - 2, box.w - 12, line + 2)
        if number == view.cursor:
            pygame.draw.rect(screen, HIGHLIGHT, row)
        editor.hits.append((row, "file", number))
        name: str = path.name
        if here is not None and path.resolve() == here.resolve():
            name += "   (open now)"
        screen.blit(_text(font, name, TEXT), (box.x + 14, y))
        folder: str = _relative_dir(path)
        screen.blit(
            _text(font, folder, DIM),
            (box.right - 14 - font.size(folder)[0], y),
        )
    if not shown:
        screen.blit(
            _text(font, "no wave matches. A full path opens with Enter.", DIM),
            (box.x + 14, top_y),
        )
    notes: list = [
        (f"{len(shown)} of {len(view.files)} files", DIM),
        (
            (
                "Type to find   Ctrl+V paste a name or path   Up Down pick   "
                "Enter or click open   Esc cancel"
            ),
            TEXT,
        ),
    ]
    _lines(screen, font, box.x + 12, box.bottom - line * 2 - 6, notes)


def _relative_dir(path: Path) -> str:
    """The file's folder from the repo root, for the Open list's right column."""
    try:
        return str(path.parent.resolve().relative_to(GAME_DIR.parent))
    except ValueError:
        return str(path.parent)


if __name__ == "__main__":
    main()
