# driftward-ace

## How to start the game (development, debug mode)

1. Open the project in the dev container.
2. If the workspace didn't load: File > Open Workspace from File, then pick `driftward-ace.code-workspace`.
3. Press **F5**. It builds the game, starts the server and opens `http://localhost:6060/?debug=1` in your browser. Click the canvas to start.
4. Stop with **Shift+F5** (or Ctrl+C in the terminal).

## How to play one wave (debug mode)

Start the server at a wave from the terminal:

```
game/scripts/start-driftward-ace.sh --wave w11
```

- Give the wave's file name from `game/waves/` without `.json`, or just its start: `w11` finds `w11_lvl4_island`, `w4` finds `w4_lvl8_satellite`. A name that matches no wave lists them all.
- Wait for the `Ready:` line at the bottom of the terminal, then open `http://localhost:6060` in your browser. It turns on debug mode and the wave by itself. Click the canvas, then pick Play.
- `--wave` turns on debug mode, so `--debug` isn't needed with it.
- The run starts 3 seconds before the level-up into the wave's level. The banner shows that level, then your wave plays. After it, the rest of that level and the levels after it play as normal. Retry starts at the same place.
- A Level 1 wave (`w1`, `w2`) has no level-up: it starts after the 3 seconds.
- During those 3 seconds the HUD shows Level 1 and the debug overlay shows the wave `debug_lead_in`.

On desktop, without the browser, the full id is needed:

```
cd game && DRIFTWARD_DEBUG=1 DRIFTWARD_WAVE=w11_lvl4_island python main.py
```

## Versioning

The game's version is the one line in `game/VERSION`, such as `1.0.0`. The menu and its pages show it in the bottom-left corner as `v1.0.0`.

Raise it in the pull request that changes the game:
- **Middle number** for a new feature: `1.0.0` to `1.1.0`.
- **Last number** for a fix: `1.1.0` to `1.1.1`.
- **First number** for a big release.

The **Version bump** check fails a pull request that changes a shipped file (anything pygbag packs from `game/`, plus `pygbag.ini` and `web/`) without raising the version. Changes to docs, tests, tools and scripts don't need a bump. To merge a shipped change and keep the version, add the label `no-version-bump` to the pull request. The check runs again by itself.

After a merge to main, the commit is tagged `v<version>` if that tag doesn't exist yet.

Run the check locally: `python .github/scripts/check_version_bump.py --base origin/main`.
