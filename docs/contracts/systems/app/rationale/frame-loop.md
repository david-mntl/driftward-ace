# App, frame loop, rationale
Part of: app
Read when: you ask why the app's frame loop works as it does.

## Rationale

- **The mode reaches `frame_loop` through `functools.partial`.** `guarded` awaits a body with no arguments, and the loop needs the mode only to set `overlay_visible` and to gate F3. `guarded` keeps its DRA-5 signature.
- **Held keys come from `pygame.key.get_pressed()`, read once per frame.** That is SDL's own key state, so a missed event can't leave a key stuck in a set of our own. Reading it once per frame gives every tick in that frame the same thrust, so a frame with several ticks behaves like several frames with one tick.
- **Key lines log the ship before this frame's ticks.** That is the state the player saw when the key went down or up. The integration check needs only that y changes between the two lines.
- **Ship events are logged in core, key events in the app.** Each side logs what only it knows: the app sees the key events, core sees the wall, the line and the floor. Core logging is by event and doesn't change any rule, so core still behaves the same in both modes.
- **F3 lives in the app.** It is input, and only the app reads input. The overlay view never sees the mode or the key, only whether the app calls it.
- **The catch-up cap drops time instead of saving it.** The Director chose 5 ticks per frame, with owed time beyond that dropped (decision-log row 21). Without it, a long hidden-tab gap would run every missed tick in one frame: the ship would jump ahead unseen, and a slow frame could snowball. Setting the accumulator to 0.0 is the plain reading of "dropped". The fraction of a tick it also drops is under 1/60 s and can't be seen.
- **The cap is in `app/settings.py`, not core.** It is about frames, and only the loop knows about frames. Core sees only whole ticks, so the rules stay the same whatever the frame rate.
- **The scroll starts right after the spawn (DRA-13).** The control card doesn't exist yet, so the Director set play start to the moment the ship first appears at screen center. Calling `start_scroll()` next to `spawn()`, before the first frame, makes tick 0 the state the first frame shows. From DRA-23 `core.run.start_run()` makes both calls.
- **Dropped catch-up time doesn't scroll (DRA-13).** Distance counts ticks the game ran. Time the cap drops is never run, so the world doesn't jump ahead after a hidden tab, the same as the ship.
- **The HUD is drawn last (DRA-13).** 10-ui.md, rule 1 puts the HUD on top of everything. The overlay and the HUD never overlap, so moving the overlay from last to second-to-last changes no pixel today.
- **The cap logs only when it starts.** A slow device can hit the cap every frame. Logging each time would be a line per frame, which the log policy forbids.

- **The app holds one `Run` (DRA-23).** Game over freezes the ship and the scroll together, and a retry resets them together. Those are game rules, so they live in core. The app keeps one state, calls one step per tick, and only decides what to draw from the run's fields.
- **The app skips `draw_ship` while the ship blinks hidden (DRA-23).** `run.ship_visible` is the core fact; the app reads it and doesn't call the view, the same way it calls the overlay only while `overlay_visible`. The ship view stays unchanged.
- **The app passes `run.score` to the Game Over box's score line, a call of its own (DRA-61).** The box stays free of core, as in DRA-23, and the app already reads the run's fields to decide what to draw. A second call, not a new argument, keeps the existing `draw_game_over(surface)` call valid through the build, so QA stays clean before integration (Director, DRA-61 revision: "keep QA clean"). The HUD keeps taking the run, so its call doesn't change.
- **The Game Over box is drawn before the HUD (DRA-23).** 10-ui.md, rule 1 puts the HUD on top of everything. The box is in the middle of the screen and the HUD at the top, so they never overlap, and the HUD stays the last call.
