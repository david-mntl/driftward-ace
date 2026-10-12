# World: screen geometry
Version: 1
Status: frozen
Features: DRA-6
Created by: architect

## Purpose
Give every system one home for the screen's size and the lines the rules use: the side walls, the top line and the floor. DRA-6 has no camera, so world and screen are the same space. The camera (auto-rise, follow) is out of scope and will extend this contract later.

Who builds what:
- `game/core/world.py`: the Gameplay Implementer, task `DRA-6-01-gameplay-implementer`.
- Read by `core/ship.py`, `ui/debug_overlay.py`, `app/frame.py` and the error step in `app/guard.py`.

## Diagram
```
 x=0                              x=640  (SCREEN_W)
  +--------------------------------+  y=0
  |                                |
  |- - - - - - TOP LINE - - - - - -|  y=168  (TOP_LINE_Y)
  |                                |
  |               ship             |
  |                                |
  +--------------------------------+  y=480  (SCREEN_H, the floor)
  wall                          wall
```
```mermaid
flowchart LR
  W["core.world<br/>(constants only)"] --> S["core.ship"]
  W --> O["ui.debug_overlay"]
  W --> F["app.frame"]
  W -. "error step only" .-> G["app.guard"]
```

## Interface
```python
# game/core/world.py  (constants only, no imports, no logger)
SCREEN_W: int = 640            # 03-world-and-camera.md, screen_w
SCREEN_H: int = 480            # 03-world-and-camera.md, screen_h
TOP_LINE_RATIO: float = 0.35   # 03-world-and-camera.md, top_line_ratio
TOP_LINE_Y: int                # = round(SCREEN_H * TOP_LINE_RATIO) -> 168
```
Screen coordinates, pygame style: x to the right, y down, in pixels. The left wall is x 0, the right wall is x `SCREEN_W`, the floor is y `SCREEN_H`.

## Rules
- Screen is 640×480. Source: 03-world-and-camera.md, screen_w, screen_h (guess).
- The top line sits at `screen_h × top_line_ratio` = 168. It is computed from the ratio, never written as a bare 168. Source: 03-world-and-camera.md, rule 2 and How to extend.
- The side walls are at x 0 and x `SCREEN_W`. Source: 03-world-and-camera.md, rule 6.
- The floor is the bottom edge of the screen, y `SCREEN_H`. Source: 03-world-and-camera.md, rule 5.
- The whole window is the play area. Source: 03-world-and-camera.md, Edge cases (WC-07 still open).
- Constants only: no imports, no logger, no code. Source: game/CONTEXT.md, Logging (a constants-only module has no logger).

## Rationale
- **`TOP_LINE_Y` uses `round(...)`.** `480 * 0.35` in floating point is not exactly 168. Rounding gives the int 168 that the GDD names, and keeps the ratio as the source.
- **Screen size moves from `app/settings.py` to `core/world.py`.** Core needs the walls and the floor, and core may not import `app`. One home avoids two copies of a guess value drifting apart. The DRA-5 contract left this choice to DRA-6. The change to the app is listed under Impact in `docs/contracts/DRA-5/DRA-5-app.md`.
- **No camera fields.** Camera and auto-rise are out of DRA-6. The camera feature adds them here.
