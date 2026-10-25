# DRA-111 away log

The Director handed DRA-111 to the main session on 2026-10-25 and left: "handle everything for me im not available to hanlde hands out. Start architect and handle implement too." Every call made without the Director is listed here. Review each one when you're back.

## Decisions
1. **"Lightning ball" = the electric ball** (drifters/10-electric-ball.md). It is the only unbuilt drifter that is a ball of lightning.
2. **Shipped without a separate "ship it"**, in away mode. Scope report: docs/reports/scope/DRA-111.md.
3. **Debug rows:** `type` electric_ball, `x` required, optional `speed`; an electric-ball-only mode; example rows for one ball, two far apart, two with overlapping circles. A stand-in, not written to the GDD.
4. **wave_check in scope** as for the planet and UFO: hazard counting and the telegraph floor. The bot stays out.
5. **Architect question 1, accepted:** the charge rays, the outline and the firing circle show only while the ball is on screen. Off screen the cycle keeps counting, but nothing shows. It is the only reading where rules 4 and 6 and the shared leaving rule (07-drifters.md rule 12) all hold. Written to the GDD: drifters/10-electric-ball.md rule 4, decision log row 77.
6. **Architect question 2: `fill_opacity` 0.35**, guess (the Architect's starting point). The GDD only said "translucent". Written to the GDD: drifters/10-electric-ball.md Values, decision log row 77.
7. **Architect question 3: the middle debug row falls slowly (`speed` 1).** At the GDD's speed a ball that starts at the top fires once, from mid-screen, and leaves while it still fires. It never charges again. The slow row shows the whole cycle twice.
8. **Import-order wording fixed in the contracts.** The reviewer, QA and the UI Developer flagged that the contracts said "after `ufo`" while ruff forces sorted order. Approved; two fresh Architect runs changed only that wording (core.md, view.md, shared/views.md).
9. **Data files written by the main session**, as in DRA-47 (no Tuning Engineer agent exists): `game/tuning/drifters/electric_ball.json` from the GDD values, and the five debug rows in `game/tuning/debug_spawns.json`.
10. **Debug list switched to `electric_ball` mode, `loop_ticks` 200**, so the feature shows as soon as you open the game in debug mode. It was `ufo` mode, `loop_ticks` 800. Set it back in `game/tuning/debug_spawns.json` when you want.
11. **wave_check ran after integration, not before.** The skill runs it before integration, but it exited 2 (`charge_rays is not a known field`) because the electric ball's app loader is the Integration Engineer's file. After integration: `--changed` says no wave changed (exit 0), `--all` passes 7 of 7, and wave_check's own tests pass 45 of 45. No wave_check code was needed.

## Things for you to look at
- **Tuning point.** At Level 1 a ball from the top fires only once and leaves while firing, like the chain lightning. A ship near the top line is never hit by a second fire. To make it threaten longer, lower `speed_ratio` or shorten `charge_ticks` in `electric_ball.json` (and the GDD).
- **`fill_opacity` 0.35 and the whole placeholder look are guesses.** Look at the firing circle in the browser and change the GDD value if it's too strong or too faint.
- **Integration observations:** the dimmed ball going back to full color wasn't seen (ball 1 leaves before its 3 s dim ends). The F3 label text wasn't read (canvas text). With no key pressed the run ends at about tick 420, before ball 1 leaves at tick 557; the whole cycle was shown with a script holding the ship clear.
- **Second hit on the next cycle.** A ball that hit you on its first fire hits again on its next fire: the 180-tick re-hit cooldown ends during the charge. That matches the rules; QA asserts it.
- **Small task-text mismatch (DRA-111-03):** the task lists the refusals as "a specialty, a seed", but the spawner refuses the seed first. The test follows the code and the spawner contract.
- **Cost (step 7 of the context diet).** `scripts/tokens.sh --ticket DRA-111`: first Architect design run $5.31, 59 turns, 302k peak context, against DRA-104's $7.56, 74 turns, 383k. All four Architect runs: $6.06. Whole ticket about $15.35 against $20.36. Not a clean comparison: the UFO had more fix rounds, and this drifter reused the chain lightning's cycle.

## What happened
- Scope: report docs/reports/scope/DRA-111.md, `Verdict: ship`. Linear DRA-111 (Todo), related to DRA-47.
- Architect: 5 tasks, Linear DRA-112 to DRA-116, plus one revision run for the answers above.
- Task 01, core: reviewed with no must-fix, QA pass.
- Task 02, view: reviewed with no must-fix, QA pass. QA compared the drawing pixel by pixel against a second renderer written from the contract: 45,612 cases matched.
- Tasks 03 to 05, tests: all pass. `game/tests/check.sh` ends `QA: pass`.
- Integration: `Verdict: pass` (docs/reports/integration/DRA-111.md). Built with pygbag and played in a real browser. The Integration Engineer added `game/app/drifters/electric_ball_tuning.py`.
- All five sub-issues are In QA with a pass comment. Close-out is yours: `scripts/close-out.sh DRA-111`, in a fresh session.
