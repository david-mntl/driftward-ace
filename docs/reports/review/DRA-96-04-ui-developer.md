Status: reviewed
Created by: implementation-reviewer

1. **Task:** review task DRA-96-04 (the planet view and its import), from the `/implement` skill. Implementation report: `docs/reports/implementation/ui/DRA-96-04-ui-developer.md`.
2. **Delivered:** `docs/reports/review/DRA-96-04-ui-developer.md` (this file).
3. **Checks:** read `game/ui/drifters/planet_view.py` and `game/ui/drifters/__init__.py` against `docs/contracts/systems/drifters.md` (Interface for `planet_view.py` and `__init__.py`; Presentation table rows, Brightness, Planet, Entry warning Copy, Rules for every view; Rules, Planet: Field rings, Drawn parts; Tuning files, the planet sentence; Rationale DRA-96), `game/core/drifters/planet.py` (`FieldRing`, `inner_rings`, `pull_radius`), `game/ui/drifters/registry.py` (`DrifterView`, `dim_color`), `docs/design/gdd/drifters/08-planet.md` (placeholder_look), `game/CONTEXT.md` and `game/ruff.toml`. Walked the six acceptance lines by hand against the code; all six follow from it. Ran nothing.
4. **Assumptions:** the view's `scale >= 1.0` test is read as the contract's "scale 1.0" full-size case, as the implementer states; `render_drifter` only ever passes 1.0 or the copy's 14 / 64.
5. **Documentation differences:** None.
6. **Next:** UI Developer, Review fix mode, for one should-fix (a report gap, no code change). Open: 0 must-fix, 1 should-fix, 0 notes asking for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-96-04-F1 | should-fix | docs/reports/implementation/ui/DRA-96-04-ui-developer.md:11 | fixed |
| DRA-96-04-F2 | note | game/ui/drifters/planet_view.py:46 | no action |

### DRA-96-04-F1
The Checks don't cover the whole Acceptance check. The task asks for "the command and its output" and for `typecheck`, `core` and `ui` to fail only where the DRA-96 Impact table expects. The report pastes the output but not the command (line 12 says "run exactly as in the task"), and reports `lint` and `typecheck` only: no `game/tests/check.sh core` or `ui` result. `ui` matters here: the Impact table says `game/tests/ui/test_drifter_registry.py` fails until `planet_view.py` and `planet.json` exist, so it is the check that this view registers. Line 26 infers the tuning file and the registry guard from a passing typecheck, which mypy can't show.
Rule: validate before handoff; the task's Acceptance check. Source: `docs/contracts/DRA-96/tasks/DRA-96-04-ui-developer.md`, Acceptance check; `CLAUDE.md`, Rules for every agent ("Validate before handoff", "Don't present a guess as a fact").
Change: in the Review fix section, add the acceptance command, and the `check.sh core` and `check.sh ui` results, naming any failure and the Impact-table row it matches.

### DRA-96-04-F2
`render_planet` names its second parameter `drifter`; the contract's Interface sketch says `obj`. All six earlier views do the same, and `DrifterView` calls views positionally, so no caller sees it. Change: none.

## Checklist
1. Interface matches exactly: F2
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. Report claims match the files: F1

## For QA
- A planet half off a side or the floor: the 303 px layer is clipped by the blit, no error, no ring drawn past the 302 px box.
- Two planets on screen with overlapping fields: each one's inner rings draw only around its own center (the shared layer is cleared between them).
- Take a planet hit: body, outer ring and inner rings dim together, then return to full colors when the cooldown ends.
- Planet in WARNING: the entry warning shows a small purple disc and no ring.
- Watch about 120 ticks: both inner rings slide from the outer ring to the body, fade out, and restart at the outer ring 60 ticks apart.

## Re-check 2026-10-22
1. **Task:** re-check the answer to DRA-96-04-F1, from the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-96-04-ui-developer.md` (line 1, the findings table, this section).
3. **Checks:** read `## Review fix 2026-10-22` in `docs/reports/implementation/ui/DRA-96-04-ui-developer.md` (lines 36-65). Compared its acceptance command with the task's Acceptance check (task file lines 26-66), and its `core` failure with the Impact row at `docs/contracts/systems/drifters.md:1808` and the code at `game/tests/core/test_collision.py:1674-1676` (`raw["hitbox"]` on the plain-file path). No code changed, so no code re-read. Ran nothing.
4. **Assumptions:** the `ui` (46 passed) and `core` (one collection error) results are taken as reported; QA reruns them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Open: 0 must-fix, 0 should-fix, 0 notes asking for a change.
7. **Status:** done.

- DRA-96-04-F1: fixed. The Review fix names the task's command block and its output, adds `check.sh ui` (PASS, `test_drifter_registry.py` 2 passed) and `check.sh core` (FAIL at `test_collision.py:1676`, `KeyError: 'hitbox'`), matches that failure to the Impact row for `test_collision.py` (task DRA-96-06), and corrects the typecheck inference in its Assumptions.
