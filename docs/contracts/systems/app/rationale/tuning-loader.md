# App, tuning loader, rationale
Part of: app
Read when: you ask why the app's tuning loader works as it does.

## Rationale

- **The UFO's weave checks run in the tuning loader (DRA-104).** As for the planet's escape check: the loader refuses a bad tuning file at startup, naming the file and the place; the rules themselves are core's (`systems/drifters.md`, Rules, UFO, Tuning checks).

- **The escape check runs in the tuning loader (DRA-96).** The scope report asks the game to refuse a pull the ship can't escape. The loader is where every tuning file is refused, at startup, with the file and the field named; the rule itself is core's (`systems/ship.md`), so the loader only calls it and adds the place.

- **The tuning is loaded in the app and checked by hand (DRA-29).** The Director decided the app loads and validates the files once and core never reads files. game/CONTEXT.md puts validation at the edge. A JSON Schema library would need packages pygbag can't install, so the loader checks the schema's rules itself and the schema stays the written rule both sides follow.
- **The tuning is loaded in both modes (DRA-29).** Game rules are the same in both modes, and waves will need it in normal mode. A bad file then breaks both modes the same way, before the first frame.
- **`TUNING_DIR` from `__file__` (DRA-29).** pygbag runs the game from its own folder in the browser; a path built from the module's own place works the same on desktop and in the browser. It is a module constant read at call time so the bad-file check can point it at a scratch folder without a code change.

- **`hazards.json` must exist, its fields may be left out (DRA-39).** The scope asks that none of the values be required. A missing file still raises, like every other data file, so a broken package shows at once instead of silently using defaults. `{}` is a valid file.
- **The defaults live in core, not in the loader (DRA-39).** `core.drifters.base` holds `DEFAULT_REHIT_COOLDOWN_TICKS` and `DEFAULT_REHIT_DIM` with their GDD sources. The loader fills left-out fields from them, so the numbers have one home.

- **The loader builds the chain's hitbox with core's functions (DRA-47).** The chain lightning's width, height and hitbox follow from its nodes. Calling `layout_size` and `chain_hitbox` from `core.drifters.chain_lightning` keeps that rule in one place, the same one `born` uses after mirroring, instead of a copy in the app.

- **The loader builds the fireball's hitbox with core's function (DRA-56).** Its tail's place follows from the head, `tail_ratio` and the angle, so `fireball_hitbox` from `core.drifters.fireball` is the one home of that rule, the same one `born` uses with `invert`.
