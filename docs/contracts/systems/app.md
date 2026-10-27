# App base: entry point, logging, run mode, loop, error guard, error screen
Version: 18
Status: frozen
Features: DRA-5, DRA-6, DRA-13, DRA-19, DRA-23, DRA-29, DRA-39, DRA-47, DRA-56, DRA-61, DRA-62, DRA-76, DRA-86, DRA-96, DRA-104, DRA-111, DRA-117, DRA-125, DRA-126
Created by: architect

## Purpose
Start the game, set up logging once, read the run mode once, run the async loop on the fixed 60 Hz tick, and catch any unexpected error so the page shows the error screen instead of freezing. The contract is split into parts: open only the one you need.

## Parts
<!-- parts:begin -->
| Part | Holds | Read when | Size |
|---|---|---|---|
| [debug-spawns](app/debug-spawns.md) | Interface, Rules | you change the debug spawn list: its file, checks, rows or timing. | 13.1 KB |
| [error-handling](app/error-handling.md) | Interface, Presentation, Rules | you change the error guard or the error screen. | 5.4 KB |
| [frame-loop](app/frame-loop.md) | Interface, Rules | you change the frame loop: ticks, keys, draw order, the catch-up cap. | 18.5 KB |
| [general](app/general.md) | Purpose, Interface | you want the overview of the app, or a rule that fits no area. | 4.7 KB |
| [integration-checks/DRA-104](app/integration-checks/DRA-104.md) | Rules | you run or extend the browser checks for the UFO (DRA-104). | 7.6 KB |
| [integration-checks/DRA-111](app/integration-checks/DRA-111.md) | Rules | you run or extend the browser checks for the electric ball (DRA-111). | 7.8 KB |
| [integration-checks/DRA-117](app/integration-checks/DRA-117.md) | Rules | you run or extend the browser checks for the graze (DRA-117). | 6.9 KB |
| [integration-checks/DRA-125](app/integration-checks/DRA-125.md) | Rules | you run or extend the browser checks for the screens: menu, instructions, leaderboard, pause, last life and game over (DRA-125). | 11.5 KB |
| [integration-checks/DRA-126](app/integration-checks/DRA-126.md) | Rules | you run or extend the browser checks for the saves: top 10, name entry, game-over messages, BEST and the filled leaderboard (DRA-126). | 7.0 KB |
| [integration-checks/DRA-13](app/integration-checks/DRA-13.md) | Rules | you run or extend the browser checks for the scroll, the starfield and the HUD (DRA-13). | 2.4 KB |
| [integration-checks/DRA-19](app/integration-checks/DRA-19.md) | Rules | you run or extend the browser checks for the review follow-ups (no new gameplay) (DRA-19). | 1.2 KB |
| [integration-checks/DRA-23](app/integration-checks/DRA-23.md) | Rules | you run or extend the browser checks for the run: lives, hits and game over (DRA-23). | 4.9 KB |
| [integration-checks/DRA-29](app/integration-checks/DRA-29.md) | Rules | you run or extend the browser checks for the drifter base, the meteorite and the debug spawn list (DRA-29). | 7.7 KB |
| [integration-checks/DRA-39](app/integration-checks/DRA-39.md) | Rules | you run or extend the browser checks for the satellite, the re-hit cooldown and the editable spawn list (DRA-39). | 6.1 KB |
| [integration-checks/DRA-47](app/integration-checks/DRA-47.md) | Rules | you run or extend the browser checks for the chain lightning (DRA-47). | 7.7 KB |
| [integration-checks/DRA-5](app/integration-checks/DRA-5.md) | Rules | you run or extend the browser checks for the app base (DRA-5). | 1.9 KB |
| [integration-checks/DRA-56](app/integration-checks/DRA-56.md) | Rules | you run or extend the browser checks for the fireball (DRA-56). | 8.0 KB |
| [integration-checks/DRA-6](app/integration-checks/DRA-6.md) | Rules | you run or extend the browser checks for the ship, its view and the debug overlay (DRA-6). | 4.0 KB |
| [integration-checks/DRA-61](app/integration-checks/DRA-61.md) | Rules | you run or extend the browser checks for the score and the game-over score (DRA-61). | 3.6 KB |
| [integration-checks/DRA-62](app/integration-checks/DRA-62.md) | Rules | you run or extend the browser checks for the coin and its popup (DRA-62). | 8.5 KB |
| [integration-checks/DRA-76](app/integration-checks/DRA-76.md) | Rules | you run or extend the browser checks for waves and the playlist (DRA-76). | 7.6 KB |
| [integration-checks/DRA-86](app/integration-checks/DRA-86.md) | Rules | you run or extend the browser checks for the floating island (DRA-86). | 9.8 KB |
| [integration-checks/DRA-96](app/integration-checks/DRA-96.md) | Rules | you run or extend the browser checks for the planet (DRA-96). | 8.0 KB |
| [integration-checks/method](app/integration-checks/method.md) | Rules | you run any browser check: how the checks are done. | 1.1 KB |
| [old-names](app/old-names.md) | Old names | a citation names a section of the old single file, such as "Rules, Frame loop". | 4.7 KB |
| [rationale/debug-spawns](app/rationale/debug-spawns.md) | Rationale | you ask why the app's debug spawns works as it does. | 2.9 KB |
| [rationale/error-handling](app/rationale/error-handling.md) | Rationale | you ask why the app's error handling works as it does. | 2.0 KB |
| [rationale/frame-loop](app/rationale/frame-loop.md) | Rationale | you ask why the app's frame loop works as it does. | 3.9 KB |
| [rationale/integration-checks](app/rationale/integration-checks.md) | Rationale | you ask why the app's integration checks works as it does. | 3.3 KB |
| [rationale/release](app/rationale/release.md) | Rationale | you ask why the app's release works as it does. | 0.7 KB |
| [rationale/save-storage](app/rationale/save-storage.md) | Rationale | you ask why the app's save storage works as it does. | 2.2 KB |
| [rationale/startup](app/rationale/startup.md) | Rationale | you ask why the app's startup works as it does. | 3.1 KB |
| [rationale/tuning-loader](app/rationale/tuning-loader.md) | Rationale | you ask why the app's tuning loader works as it does. | 2.6 KB |
| [rationale/wave-loading](app/rationale/wave-loading.md) | Rationale | you ask why the app's wave loading works as it does. | 1.4 KB |
| [release](app/release.md) | Interface, Rules | you change the launch script, the release package or `pygbag.ini`. | 11.6 KB |
| [save-storage](app/save-storage.md) | Interface, Rules | you change how the saves are read from or written to the browser's localStorage. | 5.1 KB |
| [startup](app/startup.md) | Diagram, Interface, Rules | you change startup, the run mode switch, logging or the import boundary. | 8.6 KB |
| [tuning-loader](app/tuning-loader.md) | Interface, Rules | you change how the tuning files are loaded and checked. | 26.0 KB |
| [wave-loading](app/wave-loading.md) | Interface, Rules | you change how wave files are read and loaded. | 2.4 KB |
<!-- parts:end -->
