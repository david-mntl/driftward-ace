Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-47-06-ui-developer (the chain lightning view and its registration), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-06-ui-developer.md
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core)`. No failure comes from this task's files (`game/ui/drifters/chain_lightning_view.py`, `game/ui/drifters/__init__.py`). Each one sits in a file a later DRA-47 task or the integration owns, as the main session said to expect:
     - typecheck: 17 errors, the same 17 as in the DRA-47-05 report: `app/tuning.py` 4 (integration), `tests/core/test_collision.py` 13 (DRA-47-07). None in `game/ui/`.
     - core: collection error in `tests/core/test_collision.py`, `KeyError: 'hitbox'` (DRA-47-07).
     - ui: 17 pass, including `test_drifter_registry.py`, which failed in the DRA-47-05 round and now passes because the chain lightning view is registered.
     - env, lint and format pass.
   - Acceptance check, run from `game/` as written in the task (from a scratchpad script, `PYTHONPATH=.`), twice. Both runs identical, and they match the four expected lines:
     ```
     (0, 220, 255) (0, 0, 0) True False
     True True
     (220, 240, 255) (0, 0, 0) False
     (165, 180, 191) (0, 165, 191)
     ```
   - Inline edge runs (nothing saved in `game/tests/`), on a real `ChainLightning` with the `trio_triangle` layout (nodes (-64, 55.4), (0, -110.9), (64, 55.4), three arcs) and a diagonal pair:
     - Every tick of a cycle: ticks 0, 29, 30, 59, 60, 89, 90, 119 give 1, 1, 2, 2, 3, 3, 4, 4 rays and only node and ray colors. Ticks 120, 121, 239 give 0 rays and only node and arc colors. First and last tick of each phase are right.
     - Ray angles: at ticks 0, 30, 60, 90 the rays grow in the order up right, up left, down left, down right on every node of the trio. At scale 0.5 all four quadrants show a ray.
     - Band against hitbox: every pixel of the band color lies within 3.95 px of an arc's hitbox line (half thickness 3; the extra under 1 px comes from `pygame.draw.polygon` truncating float corners in `ui/shapes.py`, DRA-47-04, and keeps the band at least as big as the hitbox). Samples along every hitbox line are covered by the band or a node disc: 0 gaps. The diagonal pair: 0 pixels outside the hitbox.
     - Nodes off screen: the pair at x -100 (both off) draws nothing and fires no arc; at x -50 and x -58 (one node on) it fires no arc and draws only the one cyan node. The view follows `firing_arcs()`, so band and hitbox match (rule 9).
     - Brightness: 0.0 draws nothing; 0.75 gives nodes (0, 165, 191), rays (90, 150, 191), band (165, 180, 191), as the contract lists. Through `render_drifter` with `rehit_ticks_left` 10, the brightness is 0.75 and the band and nodes dim together; with 0 it is 1.0.
     - Warning phase through `render_drifter`: 2 colors only (glow and cyan nodes), no band, no ray color. GONE draws nothing.
     - Sizes: scale 0.5 draws radius 3 nodes, 1 px rays; a ray_width of 0.3 at half size still draws (min 1 px). `charge_rays` 1, 3 and 6 give 1, 3 and 6 rays on the last tick.
     - Off-surface positions (-1000, 5000, y -30, y 600), charging and firing: no crash.
     - Non-chain drifter (a meteorite) raises `TypeError("render_chain_lightning draws a ChainLightning")`.
     - Same chain drawn twice: identical bytes. `repr(chain)` is unchanged by a draw.
   - Review "For QA" lines: rays 1 to 4 then band with no rays, off-screen node, re-hit dim, warning copy as plain discs, all checked above. The debug overlay line outlines were not run (the overlay is out of this task's scope); the band-to-hitbox distance check covers that fit.
4. **Assumptions:** `pass` follows the main session's instruction: the failing harness steps come only from files a later DRA-47 task or the integration owns, and this task's own code has no bug. `check.sh` does not print `QA: pass` yet. The tuning file lacks `hitbox`/`nodes` keys that `test_collision.py` reads, so I built the chains by hand from the contract's `chain_hitbox`.
5. **Documentation differences:** None.
6. **Next:** No bug for the UI Developer. Integration Engineer queue once the Director or `/implement` accepts the later-task failures. Re-run `check.sh` after DRA-47-07 and 08 and the `app/tuning.py` integration land; it should end `QA: pass`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (17 errors: `app/tuning.py` 4, `tests/core/test_collision.py` 13; none in `game/ui/`) · core FAIL (collection error in `tests/core/test_collision.py`, DRA-47-07) · ui PASS (17 passed)
QA: fail (typecheck core)
