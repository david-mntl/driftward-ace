# Scope and schedule
Status: draft
Depends on: [07-objects.md](07-objects.md), [11-save-data.md](11-save-data.md)

## Summary
Five weeks. Weeks 1–3 build the MVP, with feature freeze at the end of week 3. Weeks 3–5 polish: tuning, playtests, stretch goals, then submit. Objects are built in priority order ([07-objects.md](07-objects.md)).

## Values
| Week | Goal | Done when |
|---|---|---|
| 1 | Rules spec (camera, edges, difficulty, score). Agent files. Browser build. Physics and debug overlay. Priority 1 objects. Lives. Restart. | The ship feels controllable in the browser and can die. |
| 2 | Priority 2 objects. Graze. Wave loader and wave_check. Wave 0. Endless mode. HUD. Hallway test. | An endless run plays to game over. All waves pass wave_check. |
| 3 | Priority 3 and 4 objects. Levels. Menus and control card. First tuning pass. **Feature freeze.** | All MVP objects in waves. Full loop in the browser. |
| 4 | Difficulty tuning. Pause card. Glow and audio pass. Outside playtests. Stretch goals. | Outside players finish runs and want to retry. |
| 5 | Final tuning. Bug fixes. Publish the HTML5 page. Submit. | Public link plays in a browser. Repo delivered. |

Source: Director.

## Rules
1. **Stretch goals**, in the order they drop if time runs short:
   1. Lore: text only, an intro line and object names, no cutscenes. First to drop. Source: Director.
   2. Saves and local top 10 ([11-save-data.md](11-save-data.md)).
2. **Cut order** if the MVP runs late: top 10 → electric ball → carnivore plant → waves 7–8. Source: Director.
3. Nothing enters the backlog without the Director's approval. No new features after the freeze.
4. Out of scope: see [01-vision.md](01-vision.md).

## Edge cases
- The "hallway test" in week 2 is not defined: SS-01.
- The pause card in week 4 needs a key: FL-04.

## Open
- SS-01, FL-04.

## How to extend
A new milestone or stretch goal needs the Director's approval, then goes into the table or the stretch list here, with a note in [91-decision-log.md](91-decision-log.md).
