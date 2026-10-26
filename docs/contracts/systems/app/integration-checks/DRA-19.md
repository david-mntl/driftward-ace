# App, integration checks, DRA-19
Part of: app
Read when: you run or extend the browser checks for the review follow-ups (no new gameplay) (DRA-19).

## Rules

Integration checks for DRA-19, on top of the required browser checks and every DRA-5, DRA-6 and DRA-13 check above (all must still pass: DRA-19 changes no gameplay).
- **No `-0.00` in the overlay (`?debug=1`):** hold ArrowUp the whole time, so the ship sits on the top line and never falls to a respawn. While holding it, tap ArrowLeft for about 0.2 s, release it, wait about 3 s, and take a screenshot. The overlay's third line reads `vx 0.00`, not `vx -0.00`. Source: scope report DRA-19, Player sees; systems/debug-overlay.md, Presentation.
- **Null character in debug mode (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change, only a stand-in from the command line. Before calling `run()`, replace `app.loop.start` with an async function that raises `ValueError("bad\x00value")`. The log shows the start line, then ERROR `unexpected error, showing the error screen` with the `ValueError` traceback, and no `error screen failed` line. The error screen is drawn and the process idles until it is stopped. Source: scope report DRA-19, item 4; this contract, Rules, Error guard.
