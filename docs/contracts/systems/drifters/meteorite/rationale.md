# Drifters, the meteorite, rationale
Part of: drifters
Read when: you ask why the meteorite is built the way it is.

## Rationale

- **The meteorite refuses `invert` (DRA-39).** Its spec names no invert, and silently ignoring it would hide a mistake in a hand-edited row, as with the specialty switch. A later drifter whose spec says `invert` has no effect (the electric ball) accepts and ignores it in its own `born`.
