Feature: DRA-29
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/objects.md#rules
Status: done
Linear: DRA-38

## Do
Write two permanent UI-side guards: the object list matches everywhere, and the ship is drawn as exactly its hitbox. The first stops a half-added object (a class with no view, a tuning file with no class) from reaching the browser; the second keeps "what you see is what can be hit" true (Pillar 2).

Needs the tuning files `game/tuning/objects/meteorite.json` and `game/tuning/playtest.json` to exist. The main session writes them (scope report DRA-29, Limits). If they are missing, report it as blocked; don't write them.

`tests/ui/test_object_registry.py`:
1. The four lists are the same set: the values of `ObjectType`; the file names (without `.json`) in `game/tuning/objects/`; `core.objects.registry.available_objects()`; and `ui.objects.registry.registered_views()`. Find the folder from the test file's own place (`Path(__file__)`), not from the working directory. Source: objects.md, Rules, Tuning files ("Every ObjectType has exactly one tuning file, one registered class and one registered view"); scope report DRA-29 (main session: the guard test).
2. `game/tuning/playtest.json` exists and holds exactly the two switches `hazard_speed_scaling` and `timer_scaling`, both booleans. Source: docs/contracts/schemas/playtest-switches.schema.json; 08-difficulty.md, rule 5.

`tests/ui/test_ship_view.py`:
3. `draw_ship` at spawn on a black 640 × 480 surface paints white exactly the bar (x 314 to 325, rows 224 to 255) and the foot (x 304 to 335, rows 244 to 255), and no other pixel: 624 white pixels, both upper corners of the 32 × 32 square black. Read the pixels with `pygame.image.tobytes`, as `tests/ui/test_hud.py` does. Source: 04-ship.md, hitbox and placeholder_look (guess); systems/ship.md, Presentation.
4. At a fractional position (for example x 320.5, y 240.5) the bar and the foot still join with no gap and no overlap past the T: the white pixels are one bar 12 wide and one foot 32 wide, the foot's bottom row is the bar's bottom row. Source: systems/ship.md, Presentation (even offsets round the same way).

Number values used, each copied with its source: ship_w 32, ship_h 32, hitbox bar 12 and foot 12, placeholder white (255, 255, 255) (04-ship.md, guess); spawn (320, 240) (05-lives-and-damage.md, fall_respawn, locked); placeholder_bg black (12-art-and-audio.md, guess). Use the `pygame_headless` fixture. Never import a constant from the code under test to compute an expected value.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `ui` step runs the new tests in `tests/ui/test_object_registry.py` and `tests/ui/test_ship_view.py`.

## Out of scope
- Checking the tuning files' values against the schema field by field (the app's loader does it at startup; checked in integration). Test 2 checks only the switches file's shape.
- The entry warning and meteorite looks (checked by eye and in the browser), and the debug outlines.
- Core tests (tasks DRA-29-07 and DRA-29-08).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, or existing tests.
