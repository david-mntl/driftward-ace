Status: reviewed
Created by: implementation-reviewer

1. **Task:** review DRA-158-01 (`SoundCue` and `Run.sound_cues`, filled in the playing tick, the last-life tick and the game-over path), written by the Gameplay Implementer. Asked by the `/implement` skill.
2. **Delivered:** this report, `docs/reports/review/DRA-158-01-gameplay-implementer.md`. Code read: `game/core/sound_cue.py`, `game/core/run.py`.
3. **Checks:** read only, nothing run. Compared the code with `audio.md` (Interface, Rules 1 to 4), `run.md` (Interface DRA-158, Rules Sound cues, steps 5a, 5b, 6, 7, last-life and game-over ticks, `hold_arrows`, `next_run`) and `impact.md`. The smoke script and its output in the implementation report match the code paths: COIN at `run.py:484`, GRAZE at `run.py:508`, HIT at `run.py:527` and `run.py:609`, clears at `run.py:353`, `run.py:406` and `run.py:714`.
4. **Assumptions:** none beyond the implementer's reading of `hold_arrows` (cues kept, `step_run` on a game-over run clears them). I read it the same way: `run.md:661` and `run.md:694` agree with it.
5. **Documentation differences:** None.
6. **Next:** QA Engineer runs `game/tests/check.sh` and DRA-158-02. Nothing is open that asks for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-158-01-F1 | note | game/core/run.py:452 | no action |

### DRA-158-01-F1
`_apply_collect`'s docstring still ends "Nothing else changes" (`run.py:452`), but the function now also appends COIN cues. `_apply_fall` and `_apply_hit` docstrings do not mention the HIT cue either; `_apply_graze` does. Rule: docstrings state what a function does (implementer standards). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F1 (docstring only)
9. pass
10. pass

## For QA
- A tick that collects two coins at once: expect two COIN cues, then any GRAZE, then one HIT, in that order.
- Two hazards touching on one unprotected tick: one HIT. A fall on the same tick as a touch: one HIT.
- The tick after any cue tick with nothing happening: `()`. `hold_arrows` on a run that holds cues keeps them; the next `step_run` clears them.
- Last life by fall with a coin on the same tick: COIN then HIT. The following last-life ticks and the game-over tick: `()`.
- Existing core tests that compare a stepped run field by field after a coin, graze or life lost may now differ in `sound_cues` (`impact.md` expects none).
