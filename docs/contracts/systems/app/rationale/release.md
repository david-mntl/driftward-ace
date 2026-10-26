# App, release, rationale
Part of: app
Read when: you ask why the app's release works as it does.

## Rationale

- **The release package is set in `pygbag.ini`.** pygbag packs the whole `game/` folder by default, so tests and tooling shipped in round 1. `pygbag.ini` is pygbag 0.9.3's own way to exclude them, with no flag or template change. It is a build file read on the build machine, not a runtime file, so it may sit at the repo root.

- **`?debug=1` and pygbag.** pygbag's page reads some URL parts for its own options. The Integration Engineer checks that `?debug=1` reaches Python unchanged and doesn't switch pygbag into a mode of its own. If it does, that is a blocked report: the switch value is locked in the GDD.
