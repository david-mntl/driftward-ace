# DRA-47 away log

The Director handed DRA-47 to the main session on 2026-10-16 and left: "If something comes up - dont get block. Please note it somewhere but continue." Every call made without the Director is listed here. Review each one when you're back.

## Decisions
1. **Ray length 6 px**, out from the node's edge, one ray per diagonal. Director: "Propose the px of the ray and I accept your value." Written to the GDD (03-chain-lightning.md, decision log row 62).
2. **Ray interval = a quarter of the charge**, so the charge always ends with 4 rays. At Level 1 that's the Director's 0.5 s. At Level 8 (charge 84 ticks) it's 21 ticks.
3. **Architect assumptions accepted as written** (contract `docs/contracts/systems/drifters.md`, Chain lightning): node layouts in units of `node_spacing`, `invert_mirror` per variant, the new tuning fields `ray_width` (1 px) and `entry_warning_icon`, `telegraph_min` read from `hazards.json` (default 45), ties go to the smaller x and then the lower index, view colors stay constants in code as in earlier views.
4. **Data files written by the main session**, as in DRA-29: `game/tuning/drifters/chain_lightning.json` (schema values) and the 8 example rows in `game/tuning/debug_spawns.json`.
5. **Debug list mode switched to `chain_lightning`**, so the feature shows as soon as you open the game in debug mode. Set it back to `all`, `meteorite` or `satellite` in `game/tuning/debug_spawns.json` when you want.

## Things for you to look at
- **Tuning point (from the Architect).** At Level 1, a chain that starts at the top fires only once, for about 80 ticks, from y ≈ 290 down. It never charges a second time, so a ship hovering near the top line is never hit by one. If you want it to threaten the top half, shorten `charge_ticks` or lower `speed_ratio` in `chain_lightning.json`.
- **The GDD says the rays grow "faster" as the charge fills.** The placeholder only shows the count growing (one more every quarter). No flicker speed was set.
- **DRA-39 is still open** (not closed out). DRA-47 is built on top of it on this branch.
- **Stale contract line:** the DRA-39 text in `docs/contracts/systems/app.md` says the committed spawn list mode is `meteorite`; the file said `satellite` (now `chain_lightning`).
6. **Tasks 01 and 02 were re-tested at the end.** QA first marked them `blocked` only because files from later tasks were missing. That's the DRA-39 pattern: keep going and re-check later. Both passed on the re-test.

## What happened
- Architect: 8 tasks, Linear DRA-48 to DRA-55. All eight passed QA; all are now In QA in Linear.
- Task 01, line collision: review asked for one cleanup, and it was fixed. QA found a real bug: a slanted line that exactly touched a shape counted as a hit, from float rounding. It was fixed and fuzzed with 0 mismatches.
- Tasks 02 to 08: no bugs. Tests: 1312 core and 17 UI, all passing. `game/tests/check.sh` ends `QA: pass`.
- Integration: `Verdict: pass` (`docs/reports/integration/DRA-47.md`). Built with pygbag and played in a real browser.

## Integration observations to weigh at close-out
- One charge check (2 rays at about 1.75 s) can't be read as written: other drifters' entry warnings cover the node at that moment. The 1, 3 and 4 ray reads were clean.
- A few green pixels next to one node while it charged: most likely its debug label, not checked pixel by pixel.
- The meteorite and satellite browser checks weren't re-run, because the list is in chain lightning mode. Their code didn't change.
- QA note on task 04: the 1 px debug outline of a line can show a 1 px gap where a side meets a round end. Debug only.

## To see it
`game/scripts/start-driftward-ace.sh --debug`, then open `http://localhost:6060/?debug=1`.

## Your next step
`scripts/close-out.sh DRA-39`, then `scripts/close-out.sh DRA-47`, in a fresh session.
