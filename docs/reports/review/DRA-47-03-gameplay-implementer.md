Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of `docs/reports/implementation/gameplay/DRA-47-03-gameplay-implementer.md` (the chain lightning drifter, its `DrifterType` member and registration), run by `/implement`.
2. **Delivered:** `docs/reports/review/DRA-47-03-gameplay-implementer.md` (this file).
3. **Checks:** Read only, nothing run. I compared `game/core/drifters/chain_lightning.py`, `game/core/drifters/base.py` and `game/core/drifters/__init__.py` with `docs/contracts/systems/drifters.md` (Interface for `chain_lightning.py`, `base.py` and `__init__.py`; Rules for the chain lightning and the base; the two chain lightning diagrams; the DRA-47 Rationale), with `docs/design/gdd/drifters/03-chain-lightning.md`, `CLAUDE.md`, `game/CONTEXT.md` and `game/ruff.toml`. I worked through the acceptance output by hand against the code: ticks 60 to 260, the warning at (256, 70), the inverted triangle at Level 8 (charge 84, speed ≈ 3.50). All of it matches. The claim that `test_collision.py` errors at collection holds: `game/tests/core/test_collision.py:383` reads `raw["hitbox"]`, and `game/tuning/drifters/chain_lightning.json` exists.
4. **Assumptions:** I took the PEP 695 `type` aliases with string docstrings to be within the contract's "every module-level constant is `typing.Final`" rule, since they are type aliases, not constants. I also took the `update` and `start_position` code shared with the meteorite as the contract's choice ("`update` stays the meteorite's"), not as a smell.
5. **Documentation differences:** None. The task file's acceptance line asks for a check that can't pass. That is a task-wording issue, not a contract or locked-decision break. See F2.
6. **Next:** QA Engineer, task DRA-47-03. Open findings: must-fix 0, should-fix 0, note 2 (both no action). For the Director/Architect: `docs/contracts/DRA-47/tasks/DRA-47-03-gameplay-implementer.md:75` says `core -k "not collision"` passes. The contract's own Impact table says `test_collision.py` errors at collection once `chain_lightning.json` exists. Task DRA-47-07 fixes that.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-47-03-F1 | note | game/core/drifters/chain_lightning.py:286 | no action |
| DRA-47-03-F2 | note | docs/contracts/DRA-47/tasks/DRA-47-03-gameplay-implementer.md:75 | no action |

### DRA-47-03-F1
`current_hitbox()` gets its shapes by index from `self.hitbox`: arc `i` is shape `i`, node `n` is shape `len(arcs) + n`. It does not rebuild them from `nodes` and `arcs`. This is correct for every chain built by `born` or `warning_copy`, and the implementer states it under Assumptions. A chain built by hand, or by a `replace` that changes `nodes` without `hitbox`, would read stale shapes or raise IndexError. Rule: Rules, Chain lightning, Hitbox (contract, drifters.md) defines the shapes from the nodes. Change: none.

### DRA-47-03-F2
The task's acceptance check says `core -k "not collision"` passes. It can't: `-k` deselects tests after collection, and `game/tests/core/test_collision.py:383` errors at collection on `chain_lightning.json`. The contract's Impact table (drifters.md, row for `game/tests/core/test_collision.py`) predicts exactly this. The implementer reported it and did not claim a pass. Source: task file, Acceptance check. Change: none to the code. The Architect may fix the task wording.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F1
9. pass
10. F2

## For QA
- A chain placed high through the debug list (for example `pair_vertical` or `trio_diagonal` with a small y): the upper node can come on screen during a fire, and its arc switches on that tick. Check it reads fairly.
- The tick 259/260 edge: the arc still hits with the nodes' top edges at 479.03, and the chain is dropped at 481.50.
- At Level 8 with `trio_triangle` and `invert`: the point is down, the charge is 84 ticks and the fire is 120.
- A hit during a fire: the whole chain dims and can't hit for the cooldown, and its cycle keeps running.
- Test code that builds a `ChainLightning` directly must set `hitbox = chain_hitbox(nodes, arcs, ...)` (F1).
