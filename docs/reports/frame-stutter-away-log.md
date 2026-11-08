# Frame stutter: away log, 2026-11-08

Asked by the Director before sleep: find and fix the short freezes in play, with items on screen and sound on. Decide alone, stop if progress stalls. Done in the main session, no pipeline. Nothing committed: the branch is `main`.

## What was found
Measured in a real browser build with a probe (kit in `local/stutter-probe/`, see its README), music on, autopilot, endless lives. Numbers are in the GDD, `12-art-and-audio.md`, Stutter check.

1. **Python's garbage collector froze the game for 33 to 56 ms**, at random moments. It happened in every run of the old loop (5 of 5) and never after the fix. This is the "freeze not always at the same time".
2. **One slow frame snowballed.** A late frame ran up to 5 catch-up ticks, which made it slow too. Every freeze over 70 ms followed a 3-to-5-tick frame.
3. **Frame jitter.** A frame that came a hair early ran no tick and the next ran two: the picture held, then jumped.
4. Not the cause: the JavaScript GC (2 tiny runs in 30 s), the level-up moment, audio (stutters with music off too), the test machine's CPU quota.
5. Still there: every frame spends about 10 ms of its 16.7 on the game. The rest of the stutters in the test come from the test machine's CPU stalls (a canary loop runs 3 to 10× slower in those frames). They can't be fixed in game code.

## Decisions (each needs the Director's OK; all are in decision 149)
| # | Decision | Why | Undo |
|---|---|---|---|
| D1 | Freeze the startup memory out of the GC (`gc.collect(); gc.freeze()` before the first frame), `game/app/frame.py`. New tech rule 10. | Removes the 33 to 56 ms freezes. No effect on rules or look. | Remove `_freeze_startup_heap()` |
| D2 | `max_ticks_per_frame` 5 → 2, `game/app/settings.py`, GDD 15. | Cap 2 had the fewest frames over 40 ms in every batch and no snowball. It keeps full game speed down to 30 fps; below that the game slows a little instead of jumping. Speed in the test: 59.5 ticks/s. | Set it back to 3 or 5 |
| D3 | Tick snap 0.002 s, `game/app/settings.py`, GDD 15. | Standard fix for jitter. Its effect could not be separated from the test machine's noise; it never changes the game speed. | Set it to 0 |
| D4 | River light drawn in one batched call, `game/ui/background_view.py`. | Pixel-identical over 3000 frames, 23% faster on desktop. | `git checkout` the file |

## Not done (needs the Director)
- **Contract backfill.** `docs/contracts/systems/app/startup.md` still says `MAX_TICKS_PER_FRAME: int = 5`, and `frame-loop.md` doesn't mention the snap or the GC freeze. Architect lane.
- **Tests.** No new test for the snap, the cap or the freeze. QA lane.
- **More headroom**, if stutters remain on your PC. In order of gain: the painting cross-fade (about 1.6 ms a frame, a look change), the HUD redraw (about 3 ms), `dataclasses.replace` across core (the biggest cost in a tick, a refactor across many files).
- Unrelated failures seen in `check.sh` from earlier uncommitted work: 3 electric-ball view tests (`test_drifter_views.py`, firing ring) and `test_only_a_drifters_own_modules_name_its_type` (`tools/wave_editor/bench.py:302`).
