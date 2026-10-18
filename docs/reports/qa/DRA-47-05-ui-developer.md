Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-47-05-ui-developer (the entry warning drawn from `warning_copy()`, sized on the copy's width), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-05-ui-developer.md
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core ui)`. No failure comes from this task's file (`game/ui/drifters/entry_warning.py`). Each one sits in a file a later DRA-47 task or the integration owns, as the main session said to expect:
     - typecheck: 17 errors, the same 17 as in the DRA-47-04 report: `app/tuning.py` 4 (integration), `tests/core/test_collision.py` 13 (DRA-47-07). None in `game/ui/`, which is this task's acceptance line.
     - core: collection error in `tests/core/test_collision.py`, `KeyError: 'hitbox'` (DRA-47-07).
     - ui: 16 pass, 1 fail, `test_drifter_registry.py::test_drifter_lists_match_everywhere`: registered views lack `chain_lightning` (DRA-47-06, named in the task).
     - env, lint and format pass.
   - Acceptance check, run from `game/` as written in the task (from a scratchpad script, `PYTHONPATH=.`), twice. Both runs identical:
     ```
     [('copy', 80.0, 0.5, 1.0)] True
     [('small', 20.0, 0.5, 1.0)] True
     ```
   - Inline edge runs (nothing saved in `game/tests/`):
     - Real `ChainLightning` built from `game/tuning/drifters/chain_lightning.json` (`app.tuning.load_tuning` still rejects `arc_width`, the integration's job, so the tuning records were built by hand), all 7 variants, `invert` False and True: the warning image is 141 x 141 for each, the view is called once with the `trio_triangle` copy (width 140, nodes (-64, 55.43), (0, -55.43), (64, 55.43), a point-up triangle), scale 0.5, brightness 1.0, whatever the variant or `invert`. Everything drawn stays inside the image. `warning_center()` is (320, 70).
     - Two chains of different variants and uid at once: two cache entries with different pixels (own spikes by uid). `drop_entry_warning` on one leaves the other; a second drop does nothing. A cached chain's second draw calls the view 0 times.
     - Meteorite widths 20, 28, 40: image 21, 29, 41 px (R 10, 14, 20). Satellite, flat and angled 20 deg, `invert` both ways: image 37 px, tilt 0, -20 and 20.
     - Old against new `entry_warning.py` (`git show HEAD:` copy): the image bytes for 13 meteorite and satellite cases (three uids, three widths; flat and angled satellites, both `invert`) are identical. Warnings for them look exactly as before DRA-47.
   - Grep of `entry_warning.py` for sleep, threading, asyncio, display, event, key, image.load, mixer, `random.random(`, fill, flip: no hits.
4. **Assumptions:** `pass` follows the main session's instruction: the failing harness steps come only from files a later DRA-47 task or the integration owns, and this task's own code has no bug. `check.sh` does not print `QA: pass` yet.
5. **Documentation differences:** None.
6. **Next:** No bug for the UI Developer. Integration Engineer queue once the Director or `/implement` accepts the later-task failures. Re-run `check.sh` after DRA-47-06 and 07 and the `app/tuning.py` integration land; it should end `QA: pass`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (17 errors: `app/tuning.py` 4, `tests/core/test_collision.py` 13; none in `game/ui/`) · core FAIL (collection error in `tests/core/test_collision.py`, DRA-47-07) · ui FAIL (16 pass, 1 fail: `test_drifter_lists_match_everywhere`, DRA-47-06)
QA: fail (typecheck core ui)
