Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-62-04-ui-developer (the points popup's view, `popup_view.py`), started by /implement. Verify mode.

2. **Delivered:** `docs/reports/qa/DRA-62-04-ui-developer.md`. Nothing saved in `game/tests/`. The inline script ran from the scratchpad (`/tmp/claude-1000/-workspace/2ed55dfa-e270-4172-9576-04172b5396cf/scratchpad/qa64.py`, run with `PYTHONPATH=/workspace/game`).

3. **Checks:**
   - `check.sh`: env, lint, format and typecheck PASS. `core` 1342 passed, 1 failed. `ui` 45 passed, 1 failed. They are the same two failures the DRA-62-01 to DRA-62-03 reports name, and both close when `game/tuning/drifters/coin.json` exists: `core/test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[coin-None]` ("no tuning file for 'coin'") and `ui/test_drifter_registry.py::test_drifter_lists_match_everywhere` (tuning files lack `coin`). The contract's DRA-62 Impact table (`systems/drifters.md`) names both. Neither touches this view. See Assumptions.
   - Acceptance check run verbatim from `game/`. Output: `+50 +100 True`. The script gives the same output on three runs (md5 of the whole output identical on two repeat runs).
   - Follows the state: a `+100` popup at age 0 has its ink on rows 159 to 166. At age 20 the same ink is on rows 149 to 156, so it rose exactly 10 px (20 x 0.5). The ink's columns stay 308 to 332.
   - Every age 0 to 59: the drawing is byte-identical to a fresh `Font(None, 16)` render blitted with its rect centered on `(round(x), round(y))`. 0 differences out of 60.
   - End: `step_popups` run from age 0 keeps the popup for exactly 60 states, then it is gone, so the view has nothing to draw after.
   - Rounding: x 100.4, 100.5, 101.5, 100.6 land on `round(x)` 100, 100, 102, 101 (the ink's columns move by 0, 2 and 1 px as the rounding says).
   - Text: `+0`, `+5`, `+99999` and `+1000000000000` draw without error, with no grouping and no space.
   - Edges: centers (-50, -50), (700, 500), (0, 0), (639, 479), (320, -5), (635, 240), (1, 1) draw clipped, nothing raises.
   - Cache: after drawing 100, 50, 100, 50, 100 the text cache has 2 entries, 2 misses, 3 hits; the font cache has 1 entry (built once, 7 hits).
   - Draws only: `repr(popup)` is the same before and after a draw. A surface filled (10, 20, 30) keeps that color at its corners after the blit (no fill). The same popup drawn twice gives the same bytes.
   - Colors: the drawn pixels include `POPUP_COLOR` (255, 80, 150) and antialiased blends of it only.
   - Grep of `game/ui/popup_view.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav|import app|from app`: no hits. It imports only `pygame` and `core.popup`.
   - Review's For QA lines: age 0 against age 20 (done), same popup twice and two surfaces after 50 and 100 (done), a popup near the top or right edge clipped with no error (done). The last line (the popup over the drifters and under the ship, vanishing after 60 ticks) waits for the Integration Engineer wiring `game/app/frame.py`. The 60-state end was checked through core.

4. **Assumptions:** I count the two `coin.json` failures as not a bug and set `pass`, as the DRA-62-01 to DRA-62-03 reports did, though `check.sh` ends `QA: fail (core ui)`. The contract's Impact table names both. If the Director wants a strict `QA: pass` first, hold this task until `coin.json` and DRA-62-05 land. The ink of a drawn popup sits 1.5 px above its rect's center (the font's own padding); the contract centers the rect, not the ink, so this is correct.

5. **Documentation differences:** None.

6. **Next:** Integration Engineer is not due yet: the coin tuning file, QA tasks DRA-62-05 and DRA-62-06 and the app wiring are still open. Hand back to the `/implement` skill to continue. Re-check the two failing tests once `coin.json` exists.

7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, expected: no tuning file for coin) · ui FAIL (1, expected: no coin.json)
QA: fail (core ui)
