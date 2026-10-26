# App, error handling, rationale
Part of: app
Read when: you ask why the app's error handling works as it does.

## Rationale

- **The guard imports its error screen late, and opens a window if there is none.** An import error in `app.frame` happens before `pygame.init()`, so there is no surface yet. Opening one in the guard lets that error still show the error screen. If pygame itself is missing, the error screen can't be shown at all, so the guard logs a second traceback and returns instead of idling. Idling would need pygame's event queue and would hang.

- **The error screen takes `detail`, not the mode.** game/CONTEXT.md says only `game/app/` and the debug overlay read the run mode. The guard decides normal or debug content, and the view only draws what it's given. The cut to screen width stays in the view, because only the view knows the font metrics.
- **`ui/look.py` holds `BACKGROUND`.** placeholder_bg is a look value, used by the loop's fill and by the error screen. One home in code avoids two copies of a guess value drifting apart.

- **The guard removes null characters, the view doesn't (DRA-19).** pygame's font render raises on a string with `\x00` in it. Before DRA-19 that made the guard log "error screen failed" and leave the last frame up, so a debug-mode player saw no error screen for that message. The guard already shapes `detail` into one line, so it is the one place that turns an exception into displayable text. Removing the character, not replacing it, keeps the rest of the message as it was. The full message with the null stays in the logged traceback (10-ui.md, error_debug_line).

- **Idle after the error, don't exit.** Ending `run()` hands control back to pygbag in a state we haven't tested. Idling keeps the canvas showing the error screen and keeps the page responsive.
- **The error screen is tested headless.** A browser run can't trigger an unexpected error without a debug-only trigger, and that would be new scope. Task DRA-5-02 proves the screen draws right in both modes.
