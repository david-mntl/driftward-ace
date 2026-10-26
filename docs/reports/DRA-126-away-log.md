# DRA-126 away log

The Director asked on 2026-10-26 to "trigger the next open task DRA-126", then, while the Architect ran: "Please handle everything while im gone - like triggering the implementation once the architect finishes." Every call made without the Director is listed here. Review each one when you're back.

## Decisions
1. **"Trigger DRA-126" read as the go.** Scope report docs/reports/scope/DRA-126.md set to `Verdict: ship`, Linear DRA-126 to Todo. DRA-125 set to Done in Linear: all 12 of its sub-issues were Done after close-out, but the feature issue was still Todo.
2. **Architect Q1, rule 5 wording: accepted the Architect's text.** 11-save-data.md rule 5 said saves are off when localStorage is "empty". That clashed with its own edge case (the first score makes #1) and the scope report's Player sees. New rule 5: saves are off only when localStorage is missing, can't be read or written, or the data is broken; an empty list works. Written to the GDD: 11-save-data.md rule 5, decision log row 94. The frozen scope report still says "empty, missing or broken" in Feature; the GDD wins.
3. **Architect Q2, level reached: the level when the last life is lost**, frozen with the score, through a new `Run.final_level`. The score is frozen at that tick too, so both fields describe the same moment. Written to the GDD: 11-save-data.md Edge cases, decision log row 95.
4. **Architect Q3, picker after the save: accepted as proposed.** The slots keep the name; the cursor outline and the hint line hide, and their places stay empty so nothing moves. Underline and outline are 1 px. While the picker is open, RETRY and MENU are grey with no `>`. Stand-ins, not written to the GDD.
5. **Architect Q4, leaderboard rows: accepted as proposed.** Four columns, each as wide as its widest cell, the table centered. Place and score right-aligned, nickname and `LV n` left-aligned, 24 px between columns. Stand-ins, not written to the GDD.
6. **docs/TODO.md: added the top-left corner entry** (SCORE, GRAZE, BEST over corner warnings). hud.md already said TODO.md tracks it, but only the top-right hearts were listed.

## Things for you to look at
- The Architect's FYI list (in its hand-back, repeated here): one localStorage key holding one JSON document; desktop runs have no localStorage, so saves are off there; a score of 0 can make the list; held arrows never repeat in the picker; two open tabs, last write wins; broken stored data keeps saves off and is never overwritten, so only clearing browser data brings saves back; BEST stays at x 200 and a long SCORE would overlap it (UI-01).

## What happened
- Architect design run: contracts written, blocked on Q1 to Q4.
