# App, error handling
Part of: app
Read when: you change the error guard or the error screen.

## Interface

### game/app/guard.py (Integration Engineer)
```python
async def guarded(body: Callable[[], Awaitable[None]], mode: RunMode) -> None:
    ...
    # Awaits body(). Holds the project's only `except Exception`.
    # Module level: stdlib and app.mode only. pygame, core.world and
    # ui.error_screen are imported inside the error step, never at the top.
```

### game/ui/look.py (UI Developer)
```python
BACKGROUND: tuple[int, int, int]  # 12-art-and-audio.md, placeholder_bg
```
The one home of the background color in code. `app/frame.py` and later views import it.

### game/ui/error_screen.py (UI Developer)
```python
def draw_error_screen(surface: pygame.Surface, detail: str | None) -> None: ...
```
`detail` is `None` in normal mode, and the one-line `<ErrorType>: <message>` text in debug mode. The app decides which. The view never reads the run mode.

## Presentation

The app draws nothing itself beyond the background fill. The ship view and the debug overlay have their own Presentation sections in `docs/contracts/systems/ship.md` and `docs/contracts/systems/debug-overlay.md`. The starfield and the HUD have theirs in `docs/contracts/systems/scroll.md` and `docs/contracts/systems/hud.md`. The blink and the Game Over box have theirs in `docs/contracts/systems/run.md` (DRA-23). The drifters and their entry warnings have theirs in `docs/contracts/systems/drifters.md` (DRA-29). The error screen reads no core state, only what the guard passes it.

| Input | Shown as |
|---|---|
| (always) | the whole surface filled with `BACKGROUND`, (0, 0, 0). Source: 12-art-and-audio.md, placeholder_bg (guess) |
| (always) | `Something broke. Reload the page.` in the default font (`pygame.font.Font(None, 24)`), color (255, 255, 255), centered horizontally and vertically on the surface. Source: 10-ui.md, error_screen, error_text_font, error_layout, error_text_color (guess) |
| `detail` is a string | `detail` in the default font at 16 px (`pygame.font.Font(None, 16)`), color (255, 255, 255), centered horizontally. Its top edge sits one line-height below the main line's top (the main font's `get_linesize()`), so it reads as the next line. Source: 10-ui.md, error_layout, debug_text_font, error_text_color (guess) |
| `detail` wider than the surface | cut from the end, one character at a time, until its rendered width fits the surface width. No ellipsis. Source: 10-ui.md, error_debug_line (guess) |
| `detail` is `None` | nothing below the main line |

- Centering uses `surface.get_size()`, never a hard-coded screen size.
- Text is rendered antialiased.
- The view only draws. It never flips the display, never logs per frame, never catches an error. If it fails, it raises.
- Logging: the module has `log = logging.getLogger(__name__)`. It may log one DEBUG line when the detail is cut, with the original and cut lengths. Nothing else.

## Rules

Error guard (`app/guard.py`):
- The only `except Exception` in the game. Source: game/CONTEXT.md, Error handling.
- On an exception from `body`:
  1. `log.exception("unexpected error, showing the error screen")`. That is ERROR level with the full traceback. Source: 15-tech-constraints.md, rule 8.
  2. `detail = None` in normal mode. In debug mode, `detail = f"{type(exc).__name__}: {exc}"` with every newline replaced by a space, so it is one line, and every null character (`\x00`) removed, so the error screen can render it. Source: 10-ui.md, error_screen, error_debug_line. Null characters: scope report DRA-19, item 4; review DRA-5-01-ui-developer, finding 3; 15-tech-constraints.md, rule 8.
  3. Show the error screen, once. Source: 10-ui.md, rule 8. In this order:
     1. Import pygame, `core.world` and `ui.error_screen` here, inside the step. Source: Director decision (DRA-5 close-out).
     2. If `pygame.display.get_surface()` is `None` (the error came before the window existed, such as an import error in `app.frame`), call `pygame.init()` and `pygame.display.set_mode((SCREEN_W, SCREEN_H))` from `core.world`. If a window already exists, reuse it.
     3. `draw_error_screen(surface, detail)`, then `pygame.display.flip()`.
  4. Idle: each frame, drain the event queue and `await asyncio.sleep(0)`. No tick, no redraw. The game doesn't resume, and the player reloads the page. Source: 10-ui.md, rule 8. Leave the idle loop only on `pygame.QUIT` (desktop).
- If any part of step 3 raises, log it with `log.exception("error screen failed")` and return, without idling. That covers pygame missing or broken (an `ImportError`, or an `AttributeError` from an empty `pygame` namespace package as in round 0), `core.world` or `ui.error_screen` failing to import, the window failing to open, and the draw or flip failing. `run()` then returns, so nothing hangs. The page shows whatever was last drawn, and the console holds both tracebacks. Source: Director decision (DRA-5 close-out).
- Both tracebacks reach the console, because logging was set up before the guard started.
- `KeyboardInterrupt`, `SystemExit` and `asyncio.CancelledError` are not `Exception` and are not caught.
- Code outside `game/app/` never catches broadly, never shows an error on screen, and never decides to keep running. Source: game/CONTEXT.md, Error handling.
