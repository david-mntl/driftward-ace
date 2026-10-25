# App, debug spawns, rationale
Part of: app
Read when: you ask why the app's debug spawns works as it does.

## Rationale

- **The debug list fills the default seed itself (DRA-104).** Only the list knows a row's index. The kept placement carries the seed, so each loop replays the same path, as the Director's "Run it twice: same path" asks, with no state in the app.

- **`play` lives in the spawn list file (DRA-76).** 10-ui.md, rule 7 puts the choice in "a debug setting", and the scope report in the debug spawn file. The file is already debug-only, hand-edited, and read once at startup; normal mode never reads it, so the choice can't reach players. Left out, the list plays, so today's file keeps working.

- **The debug list counts `run.scroll.ticks` (DRA-29).** It is the run's own play time: it freezes at game over and restarts at 0 on a retry, so the list does both with no state of its own. `add_drifters` does nothing at game over, so calling it on frozen ticks never adds a drifter twice.
- **The first test meteorite on tick 1 (DRA-29).** The scope gives the order, the spacing and the repeat, not the first tick. Tick 1 is the first tick of play, so the list starts when play starts. It is a debug stand-in; the Director may shift it.
- **The spawn list is a file in `game/tuning/` (DRA-39).** The Director edits it by hand, and the folder is already packed into the build and read through `TUNING_DIR`, so the bad-file checks can point it at a scratch copy. It is still not a tuning value or a wave: only debug mode reads it.
- **Rows carry no time; they are spread evenly over the loop (DRA-39).** The Director asked for rows with only a type and a position, and a loop whose length can be changed. Spreading the rows in play evenly over one loop needs no time field, keeps the DRA-29 meteorite timing exactly (three rows in 180 ticks: 0, 60, 120), and still works when a mode leaves only some rows in play. A row that needs its own time would be a new field for the Director to approve.
- **Every row is spawned once at load (DRA-39).** Only the drifter knows which coordinate it needs, which variants it has and whether it takes `invert`. Spawning each row once through the real spawner checks all of that with core's own rules and fails at startup, naming the row, instead of mid-run. The spawner is pure, so the throw-away drifters change nothing.
- **Rows out of play are checked too (DRA-39).** Switching the mode should never reveal a broken row that was hidden before.
- **Normal mode never reads the list (DRA-39).** Debug mode adds the list and nothing else (15-tech-constraints.md, rule 7). A hand-edited debug file must not be able to stop the game for players.

- **A spawn row may have no position (DRA-56).** The scope gives the fireball a default corner entry, which is a row with neither `x` nor `y`. Only the drifter knows which coordinate it needs, and the load-time spawn already asks it, so the loader's own "x or y" check would only refuse a valid fireball row.
