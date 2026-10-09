# Save data
Status: stretch
Depends on: [06-scoring.md](06-scoring.md), [08-difficulty.md](08-difficulty.md), [10-ui.md](10-ui.md)

## Summary
**Stretch goal. Don't build until the Director moves this file to `draft`.** When it ships, the game saves a local top 10 of runs in the browser's localStorage. Each entry is a nickname, a score and the level reached. Nothing else is saved.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| storage | browser localStorage | — | — | locked | [01-vision.md](01-vision.md), Locked decisions |
| entry_fields | nickname, score, level reached | — | — | locked | [01-vision.md](01-vision.md), Locked decisions |
| top_n | 10 | entries | — | locked | Director |
| nickname_rules | TBD | length, characters | — | TBD | SV-01 |
| nickname_input | TBD | — | — | TBD | SV-01 |
| sort_and_ties | TBD | — | — | TBD | SV-02 |

## Rules
1. Save only the fields in `entry_fields`.
2. Keep the 10 best entries by score.
3. BEST on the HUD = the top entry's score.
4. Key names and JSON shape belong to the save schema, not the GDD.
5. If localStorage is empty, missing or broken, the game still runs, with no BEST.

## Edge cases
- A score that doesn't make the top 10: no name entry. See SV-02.
- Controls are arrow keys only, but a nickname needs letters: SV-01.

## Open
- SV-01, SV-02.

## How to extend
A new saved field breaks the locked "nothing else" rule in [01-vision.md](01-vision.md). It needs the Director's explicit go-ahead first.
