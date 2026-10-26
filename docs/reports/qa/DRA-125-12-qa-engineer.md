Verdict: pass
Created by: qa-engineer

1. **Task:** test task DRA-125-12 (menu, instructions page and leaderboard page tests), docs/contracts/DRA-125/tasks/DRA-125-12-qa-engineer.md.
2. **Delivered:**
   - game/tests/ui/test_menu.py (5 tests)
   - game/tests/ui/test_instructions.py (4 tests)
   - game/tests/ui/test_leaderboard.py (3 tests)
   - game/tests/CONTEXT.md (one paragraph for the three files)
3. **Checks:** `game/tests/check.sh` ends `QA: pass`, with the three files in the `ui` step (89 ui tests pass, 12 of them new). Mutation runs on a copy of `game/` in the scratchpad (game code untouched): a menu spacing of 41, a marker 2 px off, a marker on every item, an instructions footer one line higher, a section pitch of three lines, an icon outline of 2 px, a leaderboard footer moved, a leaderboard line gap removed, a leaderboard centered 3 px off, a menu block moved 4 px, and `@cache` removed from each view's render: each fails a test by name.
4. **Assumptions:** the one-pixel slack on centers and on the block's middle is the integer halves the contract's formulas use (`width // 2`, `(height - block) // 2`); every other position is exact. Row layout is worked out from `get_linesize()` and `get_height()`, as `test_game_over.py` does, not from a hard-coded size. The render-count check replaces `screen_font` in the view and in `ui.screen_look` with a counting wrapper; it proves no render per frame after the first draws.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer once the other DRA-125 QA reports pass. No open bug.
7. **Status:** done.

## Bugs
None. All new tests pass against `game/ui/menu.py`, `game/ui/instructions.py`, `game/ui/leaderboard.py` and `game/ui/screen_look.py`.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
