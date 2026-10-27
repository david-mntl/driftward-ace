# Save data
Status: draft
Depends on: [02-game-flow.md](02-game-flow.md), [06-scoring.md](06-scoring.md), [08-difficulty.md](08-difficulty.md), [10-ui.md](10-ui.md)

## Summary
The game saves a local top 10 of runs in the browser's localStorage. Each entry is a nickname, a score and the level reached. It also remembers the last nickname entered, so a returning player just confirms it. Nothing else is saved. The list lives in one browser on one computer; there is no online board.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| storage | browser localStorage | — | — | locked | [01-vision.md](01-vision.md), Locked decisions |
| entry_fields | nickname, score, level reached | — | — | locked | [01-vision.md](01-vision.md), Locked decisions |
| last_nickname | the last nickname saved from the letter picker, saved on its own | — | — | locked | Director |
| top_n | 10 | entries | — | locked | Director |
| nickname_length | 1 to 10 | characters | — | locked | Director |
| nickname_chars | A–Z, 0–9, space, and the symbols `. - _ ! ? *` | — | — | locked | Director |
| nickname_input | arcade letter picker with 10 slots, on the game-over screen. The cursor starts on the first slot. Up and down change the character in the current slot, left and right move between slots, and both wrap around at the ends. A confirm key saves | — | — | locked | Director |
| nickname_char_order | blank, A–Z, 0–9, then `. - _ ! ? *`. Up moves forward through the list, down moves back | — | — | guess | Director |
| sort_and_ties | score, high first. Same score: level reached, high first. Same score and level: the older entry stays above | — | — | locked | Director |

## Rules
1. Save only the fields in `entry_fields`, plus `last_nickname`.
2. Keep the 10 best entries, ordered by `sort_and_ties`.
3. **Best** = the score of the #1 entry. BEST on the HUD shows it.
4. Key names and JSON shape belong to the save schema, not the GDD.
5. If localStorage is missing or can't be read or written, or the saved data is broken, the game still runs. No BEST, no letter picker, nothing saved, and the game-over screen shows GAME OVER and the score. Nothing saved yet is not broken: the list is empty and works.
6. **Name entry** is the letter picker on the game-over screen. It shows only when the run's score makes the top 10 ([02-game-flow.md](02-game-flow.md) rule 9). A score off the list gets no picker and nothing is saved.
7. The picker starts filled with `last_nickname`, so a returning player just confirms. With no `last_nickname` it starts blank.
8. Blank slots at the end are dropped. A name of only blanks is empty. An empty name is not valid: confirming it saves nothing, and `last_nickname` stays as it was. RETRY and MENU then take over.
9. A confirmed name saves the entry and becomes the new `last_nickname`. RETRY and MENU then take over; the picker takes no more keys.
10. The run's place on the list (#1, #2–3, #4–10, or off the list) picks the game-over message ([10-ui.md](10-ui.md)).

## Edge cases
- A score equal to #10's on score and level: the older entry stays above, so the new score is off the list. No letter picker.
- The list is empty: the first score makes #1 and shows NEW BEST SCORE.
- The level reached is the level when the last life is lost, frozen with the score. The waves running on during the last life don't change it.
- The same nickname can hold several entries.
- A different browser or computer has its own list. Clearing browser data clears it.

## Open
- None.

## How to extend
A new saved field breaks the locked "nothing else" rule in [01-vision.md](01-vision.md). It needs the Director's explicit go-ahead first.
