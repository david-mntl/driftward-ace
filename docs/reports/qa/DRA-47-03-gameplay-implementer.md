Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-47-03-gameplay-implementer (the chain lightning drifter, `DrifterType.CHAIN_LIGHTNING`, its registration), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-03-gameplay-implementer.md
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core ui)`. No failure comes from this task's files (`core/drifters/chain_lightning.py`, `base.py`, `__init__.py`). Each one sits in a file a later DRA-47 task or the integration owns, as the main session said to expect:
     - typecheck: 18 errors, same as the DRA-47-01 and 02 reports: `app/tuning.py` 4 (integration), `tests/core/test_collision.py` 13 (DRA-47-07), `ui/shapes.py` 1 (DRA-47-04). None in `core/`.
     - core: collection error in `tests/core/test_collision.py:383`, `KeyError: 'hitbox'` (`load_variant_cases` reads `chain_lightning.json`, which has no per-variant hitbox). DRA-47-07 owns it; the contract's Impact table predicts it. `check.sh core --ignore=tests/core/test_collision.py`: `QA: pass`.
     - ui: 16 pass, 1 fail, `test_drifter_registry.py::test_drifter_lists_match_everywhere`: registered views lack `chain_lightning` (DRA-47-04 to 06).
     - lint and format pass.
   - Task wording: the Acceptance line "`core -k "not collision"` passes" cannot hold (`-k` filters after collection). The review already notes it (F2). Not a code bug.
   - Acceptance check, run from `game/` as written in the task, twice, byte-identical, and equal to the six expected lines:
     ```
     ['chain_lightning', 'meteorite', 'satellite']
     pair_flat -6.0 140.0 12.0 (256.0, 70.0) 140.0 ()
     [(60, -6, False, 1, (), 0), (90, 68, False, 2, (), 0), (120, 142, False, 3, (), 0), (150, 216, False, 4, (), 0), (179, 288, False, 4, (), 0), (180, 290, True, 0, (0,), 3), (259, 485, True, 0, (0,), 3)]
     True
     [(-64.0, -55.43), (0.0, 55.43), (64.0, -55.43)] 84 120 3.5
     chain_lightning placement needs x
     ```
   - Inline edge runs (all inline, nothing saved in `game/tests/`), using the real `game/tuning/drifters/chain_lightning.json` values for all seven layouts:
     - Sizes match the contract table (140 x 12, 102.51 x 102.51, 12 x 140, 268 x 12, 193.02 x 193.02, 140 x 140, 140 x 122.85). `layout_size` matches the node spread plus `node_size` for every variant, inverted or not.
     - Cycle, levels 1 to 8 (charge 120, 113, 107, 102, 98, 93, 89, 84; fire 120): every cycle tick matched `1 + k * 4 // charge` while charging, 0 while firing, `is_charging` and `is_firing` exact complements in ACTIVE. Rays never pass 4 and the last charge tick shows 4. The tick `charge + fire` wraps to charging with 1 ray. Level 1 steps: ticks 0, 29 give 1; 30, 59 give 2; 60, 89 give 3; 90, 119 give 4.
     - WARNING lasts 60 ticks, then ACTIVE at `ticks_in_phase` 0 with y unchanged. Born: no hitbox, no rays, not charging or firing. GONE: `update` returns the same object, hitbox (), both flags False.
     - Errors: `specialty_enabled=True` raises "chain_lightning has no specialty" (False is accepted); variant without a layout raises "chain_lightning variant 'pair_flat' has no layout"; type extra None raises "chain_lightning tuning has no type values"; no x raises "chain_lightning placement needs x".
     - Start: no y gives `-height / 2` (pair_flat -6, pair_vertical -70). Explicit y kept. `speed=5.0` override kept. `timer_scaling` off: charge 120 at Level 8.
     - Invert on every layout: left_right negates x, top_bottom negates y, width and height unchanged, `warning_copy()` is the triangle (140 wide) for every variant, inverted or not.
     - On-screen strictness: pair_flat at x 58.0 has the left node off (arc off, hitbox 0), at 58.0001 both on (arc 0, 3 shapes); right side the same at 582.0 and 581.9999. pair_vertical top edge y 58.0 off, 58.0001 on; bottom y 421.9999 on, 422.0 off.
     - Partial chains: trio_line with the right node off fires only arc 0 with its two nodes (Line, Circle, Circle); with the left node off fires only arc 1. trio_triangle at y -60 (apex off) fires only arc 2 (the base) with its two nodes. Inverted triangle at y -40 with one node on screen: no arc, hitbox ().
     - Hitbox order: lines in arc order, then circles in node order (triangle: 3 lines, 3 circles). Charging tick 119: (). Fire tick 239: 3 shapes. Tick 240: () and charging. Tick 360: 3 shapes.
     - Warning node (through `add_drifters`): tie goes to the smaller x (node 0, (256, 70)); ship at 330 picks the right node; ship at 310 the left. Inverted pair_flat, tie goes to index 1 (x 256). Equal x and equal distance (pair_vertical, ship between) goes to index 0. Warning center clamps: x 10 gives 74 (node at 74, above 70); x 630 gives 566 (below 570); y 600 gives 410; unsettled node would use the chain's center.
     - Run integration with the ship pinned: charging nodes passing over the ship give no hit (ticks 178 and 179). The hit lands on tick 180 (fire start), or when the arc or a node reaches the ship (tick 189 node, 191 arc). After the hit: lives 3 to 2, invulnerability 30, `rehit_ticks_left` 180, `brightness()` 0.75, the chain keeps falling and firing (cycle unchanged), dropped on tick 298 at y 487 for a start at y -100. With 290 ticks of invulnerability at fire start: no hit, no cooldown started, arc keeps firing (3 shapes) for 40 more ticks checked.
     - Triangle start (no y): dropped on the first state where its top edge is at or past 480 (n = 245, top edge 481.69; n = 244 is 479.2).
     - Determinism: two runs, 400 ticks, a hand-made thrust pattern, two chains (inverted triangle, trio_l) added at once: ship, lives and drifters equal on every tick. The chain is frozen (`FrozenInstanceError` on assignment).
   - Review "For QA" lines: all five checked (high-placed chain partial arcs, ticks 259 and 260, Level 8 inverted triangle, hit during a fire with dim and a running cycle, `hitbox` built with `chain_hitbox` for direct builds).
   - `game/core/` grep for pygame, sleep, threading, asyncio, wall clock and `random`: none in the new module.
4. **Assumptions:** `pass` follows the main session's instruction: the failing steps come only from files a later DRA-47 task or the integration owns, and this task's own code has no bug. `check.sh` itself does not print `QA: pass` yet.
5. **Documentation differences:** None.
6. **Next:** No bug for the Gameplay Implementer. Integration Engineer queue once the Director or `/implement` accepts the later-task failures. Re-run `check.sh` after DRA-47-04 to 07 and the `app/tuning.py` integration land; it should end `QA: pass`. The Architect may fix the task's Acceptance wording about `core -k "not collision"` (review F2).
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors: `app/tuning.py` 4, `tests/core/test_collision.py` 13, `ui/shapes.py` 1; none in `core/`) · core FAIL (collection error in `tests/core/test_collision.py:383`, DRA-47-07; with that file ignored: PASS) · ui FAIL (16 pass, 1 fail: `test_drifter_lists_match_everywhere`, DRA-47-04 to 06)
QA: fail (typecheck core ui)
