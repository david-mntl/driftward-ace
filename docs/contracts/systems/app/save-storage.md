# App, save storage
Part of: app
Read when: you change how the saves are read from or written to the browser's localStorage.

## Interface

### game/app/saves.py (Integration Engineer, new)
```python
SAVE_KEY: Final[str]   # the one localStorage key that holds the save data. A name, not a GDD value

def load_saves() -> Saves | None: ...
    # Read and check the stored save data once. Saves when saves work (an empty Saves when nothing is
    # stored yet), None when they don't. Never raises for storage or data problems.
def write_saves(saves: Saves) -> bool: ...
    # Store saves whole under SAVE_KEY. True when the browser took it, False when it didn't.
    # Never raises for storage problems.
```
Imports: stdlib (`json`, `sys`, `platform`, `logging`), `core.saves`, `core.levels`. Never pygame or `ui`. Imported by `app.frame`, inside the guard. `Saves`, `ScoreEntry` and `is_valid_nickname` are in `docs/contracts/systems/saves.md`. The stored text follows `docs/contracts/schemas/save-data.schema.json`.

## Rules

Where saves work. Source: 11-save-data.md, storage (locked) and rule 5; 15-tech-constraints.md, rule 4 (no server).
- **Browser** (`sys.platform == "emscripten"`): through `platform.window.localStorage`, `getItem(SAVE_KEY)` and `setItem(SAVE_KEY, text)`. pygbag adds `window` to `platform` in the browser only, as `app/log.py` and `app/mode.py` already use it.
- **Desktop**: there is no localStorage, so saves don't work: `load_saves()` returns None and logs INFO `saves off reason=desktop`. Nothing is written anywhere: no file, in `game/` or outside it. Source: 11-save-data.md, rule 5 ("If localStorage is missing"); 15-tech-constraints.md, rule 6 (done means a real browser).

`load_saves()`, once, before the first frame, in both modes. Each failure returns None, saves don't work for the page's life, and the game runs on:
1. **Storage missing or unreadable.** `platform.window.localStorage` is absent, or reading it fails (the browser blocks storage): WARNING `saves off reason=storage error=%s`, None.
2. **Nothing stored** (`getItem` gives JS null): INFO `saves loaded entries=0 last_nickname=none`, return `Saves()`: an empty top 10 that works, so the first score makes #1. Source: 11-save-data.md, rule 5 ("Nothing saved yet is not broken: the list is empty and works") and Edge cases (the list is empty); 91-decision-log.md, row 94.
3. **Broken data.** The text is not JSON, or doesn't follow `save-data.schema.json`, or its entries are not in the top-10 order (`systems/saves.md`, Rules, Order: for each pair of neighbors, the upper one's score is higher, or equal with a level reached at least as high): WARNING `saves off reason=broken error=%s` naming the first problem found (the field and what was wrong, as the tuning loader names them), None. The stored text is left as it is: never overwritten, never removed. Source: 11-save-data.md, rule 5; game/CONTEXT.md, Error handling (validate at the edge).
4. **Good data**: the `Saves` it holds, entries in stored order. INFO `saves loaded entries=%d last_nickname=%s` (`%s` is the nickname quoted with `%r`, or `none`).
- Checks done here, not in core: every type, bool never an integer, `0 <= score`, `FIRST_LEVEL <= level_reached <= LEVEL_COUNT`, at most `TOP_N` entries, every nickname and the last nickname passing `is_valid_nickname`, no unknown key, both keys present. Core trusts what it gets. Source: game/CONTEXT.md, Error handling.

`write_saves(saves)`, called by the frame loop after every tick with `flow.saves_changed` (`frame-loop.md`, Tick):
- The text is `json.dumps` of `{"entries": [{"nickname", "score", "level_reached"} for each entry, in order], "last_nickname": <str or null>}`, exactly the schema's shape and nothing else. Source: 11-save-data.md, rules 1 and 4; 01-vision.md, locked decision 9.
- Success: DEBUG `saves written entries=%d`, True.
- `setItem` fails (storage full or blocked): WARNING `saves off reason=write error=%s`, False. The frame loop then calls `stop_saves(flow)`: saves don't work from then on. Source: 11-save-data.md, rule 5.
- The whole document is written each time, so the list and the last nickname never disagree.

Errors:
- Data errors: catch only `json.JSONDecodeError` and the `ValueError`/`TypeError` the checks raise.
- Storage errors: pygbag 0.9.3 raises a bare `Exception` for a refused storage call. `app/saves.py` catches `Exception` around the `platform.window.localStorage` read and the one `getItem` or `setItem` call only, and logs the WARNING line of step 1 or of the write. No other code sits inside those `try` blocks. Source: game/CONTEXT.md, Error handling (the `app/saves.py` exception).
- Neither function lets a storage or data problem reach the guard: a save problem never shows the error screen. Source: 11-save-data.md, rule 5 ("the game still runs").

Same in both modes. Debug mode loads and writes the same key, the same way. Source: 91-decision-log.md, row 93; 15-tech-constraints.md, rule 7.

No blocking. `getItem` and `setItem` are synchronous browser calls that return at once; the loop still yields every frame. No thread, no wait for the storage. Source: 15-tech-constraints.md, rule 1.

Log by event: one line at load, one per write. Never per tick. Source: 15-tech-constraints.md, rule 9.
