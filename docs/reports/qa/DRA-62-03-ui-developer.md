Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-62-03-ui-developer (the coin's view `render_coin` and its registration), started by /implement. Verify mode.

2. **Delivered:** `docs/reports/qa/DRA-62-03-ui-developer.md`. Nothing saved in `game/tests/`. Inline scripts ran from the scratchpad (`qa63.py`, `qa63b.py`).

3. **Checks:**
   - `check.sh`: env, lint, format and typecheck PASS. `core` 1342 passed, 1 failed. `ui` 45 passed, 1 failed. The two failures are the two already named in the DRA-62-01 and DRA-62-02 QA reports, and both close when `game/tuning/drifters/coin.json` exists: `core/test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[coin-None]` ("no tuning file for 'coin'") and `ui/test_drifter_registry.py::test_drifter_lists_match_everywhere` (tuning files lack `coin`). The task itself says the registry test passes once the file exists. Neither touches the view. See Assumptions.
   - Acceptance check run verbatim from `game/`, twice, `diff` empty. Output matches the task on every line:
     ```
     (437, 203) (255, 220, 240)
     (436, 210) (200, 30, 90)
     (442, 210) (70, 0, 60)
     (434, 209) (255, 80, 150)
     (445, 209) (255, 80, 150)
     429 450 200 219
     ```
   - Whole pixel map: a common coin at (440, 210) was compared pixel by pixel with the map built from the contract's Diagram, Coin (rows cy-10 to cy+9, lit, shade, rim). The only differences are 40 pixels on rows 206 to 213, columns 429 to 450, all pink (255, 80, 150): the ring. The ring reaches exactly columns 429 to 450 and rows 206 to 213, as the contract says.
   - Glint: a rare coin differs from the common one only in a (255, 220, 240) square, columns 437-438, rows 203-204. The common coin has no glint color anywhere.
   - Fractional centers (x in 100.0, 100.4, 100.49, 100.5, 100.51, 100.6, 439.5, 440.5; y in 100.0, 100.4, 100.5, 100.6, 209.5, 210.5; common and rare): every one is the integer-centered drawing at `(round(x), round(y))`, every pixel inside columns cx-11..cx+10 and rows cy-10..cy+9, and every pixel inside the crystal box or the ring box. 0 bad. (Python rounds .5 to even; the view and the contract both use `round`.)
   - Brightness 1.0, 0.75, 0.5, 0.333, 0.0: glint, lit, shade and rim equal `dim_color` of the contract colors in every case. The coin object's `repr` is the same before and after a draw. The same state drawn twice gives the same pixels. A coin moved 20 px down gives the same ink 20 rows lower.
   - Errors: `scale` 0.5, 1.0000001 and 2.0 raise `ValueError("render_coin draws at full size only")`. A Meteorite raises `TypeError("render_coin draws a Coin")`, also with `scale` 0.5 (the type check comes first).
   - Edges: centers (-50, -50), (700, 500), (320, -20), (320, 500) draw nothing and do not raise. (0, 0), (639, 479), (5, 240), (635, 240) draw clipped without error. A coin stepped by 1.1 px from y -33 to y 572 through `render_drifter` draws all 550 states without error.
   - Other sizes: a 14 x 24 crystal with body 12, ring 26 x 10 and glint offsets 4, 4 stays inside its two boxes, so the sizes come from the coin's fields.
   - Registry: `registered_views()` lists chain_lightning, coin, fireball, meteorite, satellite.
   - Review's For QA lines (rare vs common glint, fractional centers, `scale` and non-Coin errors, brightness 0.75 with the object unchanged): all done above. The last line (coin scrolling off the bottom in `test_drifter_registry.py`) waits for `coin.json`; the scroll-off was done inline instead.

4. **Assumptions:** I count the two `coin.json` failures as not a bug and set `pass`, as the DRA-62-01 and DRA-62-02 reports did, though `check.sh` ends `QA: fail (core ui)`. The task and the contract's DRA-62 Impact table name them. If the Director wants a strict `QA: pass` first, hold this task until `coin.json` and DRA-62-05 land.

5. **Documentation differences:** None.

6. **Next:** Integration Engineer is not due yet: the popup view (DRA-62-04), the coin tuning file and the QA tasks DRA-62-05 and DRA-62-06 are still open. Hand back to the `/implement` skill to continue. Re-check the two failing tests once `coin.json` exists.

7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, expected: no tuning file for coin) · ui FAIL (1, expected: no coin.json)
QA: fail (core ui)
