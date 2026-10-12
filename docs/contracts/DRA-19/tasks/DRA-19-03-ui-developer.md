Feature: DRA-19
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-13/DRA-13-hud.md#presentation
Status: done
Linear: DRA-22

## Do
Fix one docstring in `game/ui/hud.py`.
- `HUD_FONT_SIZE`'s docstring calls it "HUD layout approved by the Director". The 16 px default font is part of the readout text, which is a temporary stand-in. Say "temporary stand-in (readout text)", the way `HUD_COLOR`'s docstring does. Keep the rest: the unit, the scope report DRA-13 source, and "not in the GDD (UI-01 is TBD)". Source: `docs/contracts/DRA-13/DRA-13-hud.md`, Presentation ("Source: scope report DRA-13, readout text (temporary stand-in)"); scope report DRA-13, Values needed (Meters readout text); scope report DRA-19, item 5; review DRA-13-03-ui-developer, finding 1.
- No other line changes. The other `HUD_*` docstrings are layout values and stay as they are.
- Run `game/tests/check.sh lint` before handoff.

## Acceptance check
From the repo root, run:
`grep -n -A2 "^HUD_FONT_SIZE" game/ui/hud.py`
The docstring under `HUD_FONT_SIZE: int = 16` says "temporary stand-in (readout text)" and no longer says "HUD layout". Put the command and output in the implementation report.

## Out of scope
- Any value, name or drawing change in the HUD.
- The debug overlay (task DRA-19-02).
- Passing fonts in, the `below_overlay` flag, the unused module logger, any other refactor.
- Tests.
