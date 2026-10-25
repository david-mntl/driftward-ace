Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-117-03 (UI Developer): the graze popup color in `draw_points_popup` and the new `draw_graze_ring` view. Asked by the `/implement` skill. Implementation report: `docs/reports/implementation/ui/DRA-117-03-ui-developer.md`.
2. **Delivered:** `docs/reports/review/DRA-117-03-ui-developer.md` (this file).
3. **Checks:** Read `game/ui/popup_view.py` (68 lines) and `game/ui/graze_view.py` (52 lines) against `docs/contracts/systems/run.md` (Interface "DRA-117: what graze adds and changes", the popup_view and graze_view blocks; Presentation rows `popup.kind` and `run.graze_rings`; Points popup, Graze popup, Graze ring; the three Rationale entries the task names), `docs/design/gdd/06-scoring.md` (graze_popup, graze_popup_color, graze_ring, graze_ring_color), `game/CONTEXT.md` and `game/ruff.toml`. Confirmed `GrazeRing.diameter`, `.opacity`, `.line_width` and `PopupKind` exist in `game/core/graze.py` and `game/core/popup.py`. Checked the one failing core test the report names against `docs/contracts/DRA-117/impact.md`, line 45. Ran nothing.
4. **Assumptions:** The render caches (`functools.cache` on `_popup_surface` and `_ring_image`) are draw caches the contract asks for, not module-level game state. The failing `test_ufo.py` test counts as an expected failure: `impact.md` line 45 says a core test that compares a whole drifter and fails from DRA-117-02 is reported by QA and fixed in DRA-117-05.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: no findings. The failing core test `tests/core/test_ufo.py::test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds` comes from DRA-117-02 (`graze_state` SPENT), not from this task. Per `impact.md` line 45, QA reports it and DRA-117-05 fixes it.
7. **Status:** done.

## Findings
None.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- A coin popup and a graze popup of the same points: the same 16 px font and size, the coin's pink (255, 80, 150), the graze's white (255, 255, 255).
- The ring stays centered on the ship while the ship moves during its 15 states, and still draws on frames the ship blinks off (app draw order, Integration Engineer).
- The ring fades on every state (alpha 255 down to 17) and is gone on the state core drops it; no last faint frame left on screen.
- A ring and a popup near a screen edge clip without error.
- `test_ufo.py::test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds` fails from DRA-117-02; report it against `impact.md` for DRA-117-05.
