# App, wave loading
Part of: app
Read when: you change how wave files are read and loaded.

## Interface

### game/app/waves.py (Integration Engineer, DRA-76)
The wave files, read once at startup in both modes. The checks are core's (`core.wave_files.build_wave_book`, `docs/contracts/systems/waves.md`); this module only finds, reads and decodes the files.
```python
WAVES_DIR: Path  # the game's wave folder: Path(__file__).resolve().parent.parent / "waves"; read at call time
PLAYLIST_FILE: str = "playlist.json"  # in WAVES_DIR


def load_wave_book(tuning: DrifterTuning) -> WaveBook:
    ...
    # Reads every "*.json" file in WAVES_DIR but PLAYLIST_FILE as a wave (its id: the file name
    # without .json), then PLAYLIST_FILE, decodes them, and returns
    # build_wave_book(<wave documents by id>, <playlist document>, tuning). Raises on any problem.
```
Not a startup module: it imports `core`, so only `app.frame` imports it, inside the guard.

## Rules

Wave files (`app/waves.py`, DRA-76). Source: scope report DRA-76, Limits; game/CONTEXT.md, Error handling (validate at the edge); `docs/contracts/systems/waves.md`, Rules, The wave files:
- **Files.** Every file in `WAVES_DIR` (`game/waves/`) whose name ends in `.json`, other than `PLAYLIST_FILE`, is a wave; its id is its name without `.json`. Files are read in name order. `PLAYLIST_FILE` is read after them. UTF-8, `json.loads`, once, at startup, in both modes. Plain `Path.glob` and `Path.read_text`: small local files, no network, no blocking beyond that. Files of any other kind in the folder are not read. In the browser the folder is listed in pygbag's packed file system; the integration check `waves loaded` proves it works there.
- **Errors.** Invalid JSON: `ValueError("waves/<file name>: not valid JSON: <decoder message>")`, raised `from` the decode error. A missing `PLAYLIST_FILE` or folder: the `FileNotFoundError` rises as it is (it names the path). Never a default for a missing file. Everything else is checked by `core.wave_files.build_wave_book`, which names the file and the problem (`systems/waves.md`). The guard shows the error screen.
- **Log.** One INFO line after a good load: `waves loaded waves=%d pool=%d`, the number of waves and of pool waves in the book. INFO because it is startup. Nothing else.
- The app never reads, picks or steps a wave itself. It holds the book only to start the first run's waves.
