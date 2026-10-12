Verdict: ship
Created by: scope-guardian
Feature: DRA-19 Review follow-ups for DRA-5, DRA-6 and DRA-13
Parent: none

## Request
"Can we check what the reviewers did and address what remains open? Ask me first what from that is worth to be closed." The Director then picked items 1+2, 3, 4 and 6 from the open review findings.

## Feature
No new gameplay. Close the open review findings the Director picked:
1. The ship's state is documented in code with units and sign for each field, as the ship contract already gives them. Source: docs/reports/review/DRA-6-01-gameplay-implementer.md, finding 1 (should-fix).
2. The ship contract's logging rules say "the ship after the clamps, before any respawn" instead of "the returned ship", which matches what the code does. Source: docs/reports/review/DRA-6-01-gameplay-implementer.md, finding 2.
3. The debug overlay never shows `-0.00`. A value that rounds to zero shows `0.00`. Source: docs/reports/review/DRA-6-04-ui-developer.md, finding 1.
4. In debug mode, an error message with a null character still shows the error screen. The guard removes `\x00` from the detail line, as it already does for newlines. Source: docs/reports/review/DRA-5-01-ui-developer.md, finding 3.
5. Python standards polish:
   - core constants are marked `Final`
   - core dataclasses use `slots=True` where it fits
   - the `HUD_FONT_SIZE` docstring calls it a temporary stand-in (readout text)

   Sources: docs/reports/review/DRA-6-01-gameplay-implementer.md, finding 3; docs/reports/review/DRA-13-01-gameplay-implementer.md, finding 1; docs/reports/review/DRA-13-03-ui-developer.md, finding 1.

## Limits
In:
- the five items above
- the contract updates they need

Out:
- any new gameplay or visible change other than item 3
- any GDD change
- the shortened acceptance command in the closed DRA-13-02 report
- removing module loggers (game/CONTEXT.md, Logging, requires them)
- making views into classes
- passing fonts in
- any other refactor

## Player sees
In debug mode, let go of Left and watch the overlay: vx reads `0.00`, never `-0.00`. Everything else plays exactly as before.

## Fit
- Pillars: not touched. No gameplay changes.
- Locked decisions: not touched.
- 10-ui.md, `debug_overlay_layout` (two decimals): fits. `0.00` instead of `-0.00` is still two decimals.
- 15-tech-constraints.md, rule 8 (errors never freeze the page): item 4 supports it.

## Values needed
- None new. Item 3 keeps the two-decimal format from 10-ui.md, `debug_overlay_layout` (guess).

## Objections
None. Every item fixes documentation, code quality or a debug-only display, and none changes game rules.

## Decision log
- The Director asked to check the reviewers' work and close what remains open, after choosing which items.
- The main session listed six open items with a recommendation each. The Director picked 1+2, 3, 4 and 6, and left out 5 (the DRA-13-02 report command).
- The scope step was applied by the main session on the Director's direct choice in chat. The Scope Guardian doesn't accept relayed approvals.
