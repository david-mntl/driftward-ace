# App, wave loading, rationale
Part of: app
Read when: you ask why the app's wave loading works as it does.

## Rationale

- **Wave files are read in the app and checked in core (DRA-76).** Reading files is the app's edge work, as for the tuning. The checks are wave rules (the seam, the pool) and must have permanent tests, which `check.sh` runs only for `core` and `ui`. So `app.waves` lists, reads and decodes; `core.wave_files` checks and builds.
- **The wave folder is listed, not indexed (DRA-76).** Wave ids are content: the Wave Designer adds a wave by adding a file. A list of files to keep in step would be one more thing to forget. The ids are sorted, so the order never depends on the file system.
- **Waves load in both modes (DRA-76).** The scope report asks for it, and it keeps one rule: a bad wave file stops the game the same way whatever plays, before the first frame.
- **One seed per page load, from Python's `random` (DRA-76).** Core can't draw entropy and must stay replayable. The interpreter seeds `random` from the OS when it starts, in the browser too, so one draw makes each page load's picks new, and core makes each retry's picks new from it. No clock read, no extra code.

- **Both sources go through one `add_drifters` call (DRA-76).** The tick has one line that adds drifters, whichever source plays, so the two can never both add, and the run's order of log lines is the same for both.
