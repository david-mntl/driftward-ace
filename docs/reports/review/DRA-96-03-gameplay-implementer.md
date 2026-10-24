Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-96-03 (`gravity_wells` and step 4 passing the wells to the ship step in `game/core/run.py`), asked by the `/implement` skill. Implementation report: `docs/reports/implementation/gameplay/DRA-96-03-gameplay-implementer.md`.
2. **Delivered:** `docs/reports/review/DRA-96-03-gameplay-implementer.md` (this file).
3. **Checks:** By reading only, nothing run. Compared `game/core/run.py` (`gravity_wells` at 211-217, `_step_playing` at 250-287, imports at 24-36) with `docs/contracts/systems/run.md` (Purpose, Diagram step 4, Interface `gravity_wells` and the paragraph after it, Rules step 4, Other rules Planets, Logging, Impact DRA-96, Rationale DRA-96) and `docs/contracts/systems/ship.md` (`GravityWell`, `NO_WELLS`, `step`'s `wells` argument, Rules, Planet pull, When it applies). Checked the hook it calls (`game/core/drifters/base.py:373`, `game/core/drifters/planet.py:182`), the `step` signature (`game/core/ship.py:261`), `docs/design/gdd/drifters/08-planet.md` rule 4 and Edge cases, `game/CONTEXT.md` and `game/ruff.toml`. All 10 checklist items pass.
4. **Assumptions:** The acceptance output's numbers (0.26, -0.16) depend on `well_pull` in `core.ship`, task DRA-96-01. I checked only that the run hands the wells to `step` as the contract says, not the pull formula.
5. **Documentation differences:** None. The contract, the GDD (08-planet.md rule 4: the pull applies while invulnerable, not during the respawn wait) and `CLAUDE.md` agree.
6. **Next:** QA Engineer. No open findings: 0 must-fix, 0 should-fix, 0 note.
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
- Ship standing in the respawn wait inside a planet's field: y and vy don't change until the press; on the press tick vy is thrust + gravity + pull.
- Invulnerable ship inside a field is pulled the same as a vulnerable one.
- A planet still in WARNING gives no well, so no pull until it turns ACTIVE.
- Two overlapping planets: `gravity_wells` returns both, in drifter order, and the pulls add up.
- A run with no planet: `gravity_wells` returns `()`, and every existing run test passes unchanged.
