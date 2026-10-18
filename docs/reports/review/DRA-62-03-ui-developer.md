Status: reviewed
Created by: implementation-reviewer

1. **Task:** review the coin's view (`render_coin`) and its registration, task `docs/contracts/DRA-62/tasks/DRA-62-03-ui-developer.md`, against `docs/contracts/systems/drifters.md` (asked by the `/implement` skill for the Director).
2. **Delivered:** this review, `docs/reports/review/DRA-62-03-ui-developer.md`. Code read: `game/ui/drifters/coin_view.py`, `game/ui/drifters/__init__.py`, with `game/ui/drifters/registry.py`, `game/core/drifters/coin.py` and `game/ruff.toml` for reference.
3. **Checks:** by reading only, nothing run.
   - Interface (drifters.md, `coin_view.py` block): the four colors, `COIN_LINE_WIDTH`, and the `render_coin` signature, registration and both error messages match word for word. The imports are the ones the contract lists (pygame, `core.drifters.base`, `core.drifters.coin`, `ui.drifters.registry`), and none is `app`.
   - Presentation, Coin steps 1 to 5: each polygon corner, the rim's eight corners, the ring rect and the glint position match the contract's formulas, in the contract's order. Every size comes from the coin's fields.
   - The pixel map and the acceptance output (`429 450 200 219`, the five sample colors) agree with the code when I trace it by hand. The report's other claims match the code. The one red test is explained: `coin.json` does not exist yet.
   - Line 117 is exactly 100 columns, the limit in `game/ruff.toml`.
4. **Assumptions:** the lint, typecheck and acceptance results in the implementation report are taken as run by the implementer. I did not rerun them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, report `docs/reports/review/DRA-62-03-ui-developer.md`. `test_drifter_registry.py` stays red until `game/tuning/drifters/coin.json` exists.
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
- Draw a rare coin at (440, 210) and a common one: the glint (255, 220, 240) at columns 437-438, rows 203-204 appears only on the rare one.
- Draw at fractional centers such as (440.4, 210.4) and (440.6, 210.6): every pixel stays inside columns cx-11..cx+10 and rows cy-10..cy+9, with no gap in the rim.
- Call the view with `scale` 0.5 (`ValueError`) and with a non-Coin drifter (`TypeError`).
- Draw at brightness 0.75: all four colors dim through `dim_color`, and the drifter object is unchanged.
- Once `coin.json` exists, run `test_drifter_registry.py` and watch the coin scroll off the bottom.
