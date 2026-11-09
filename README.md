# driftward-ace

## How to start the game (development, debug mode)

1. Open the project in the dev container.
2. If the workspace didn't load: File > Open Workspace from File, then pick `driftward-ace.code-workspace`.
3. Press **F5**. It builds the game, starts the server and opens `http://localhost:6060/?debug=1` in your browser. Click the canvas to start.
4. Stop with **Shift+F5** (or Ctrl+C in the terminal).

## Versioning

The game's version is the one line in `game/VERSION`, such as `1.0.0`. The menu and its pages show it in the bottom-left corner as `v1.0.0`.

Raise it in the pull request that changes the game:
- **Middle number** for a new feature: `1.0.0` to `1.1.0`.
- **Last number** for a fix: `1.1.0` to `1.1.1`.
- **First number** for a big release.

The **Version bump** check fails a pull request that changes a shipped file (anything pygbag packs from `game/`, plus `pygbag.ini` and `web/`) without raising the version. Changes to docs, tests, tools and scripts don't need a bump. To merge a shipped change and keep the version, add the label `no-version-bump` to the pull request. The check runs again by itself.

After a merge to main, the commit is tagged `v<version>` if that tag doesn't exist yet.

Run the check locally: `python .github/scripts/check_version_bump.py --base origin/main`.
