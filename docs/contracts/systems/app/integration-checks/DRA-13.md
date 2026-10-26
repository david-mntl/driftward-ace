# App, integration checks, DRA-13
Part of: app
Read when: you run or extend the browser checks for the scroll, the starfield and the HUD (DRA-13).

## Rules

Integration checks for DRA-13, on top of the required browser checks and every DRA-5 and DRA-6 check above (all must still pass). Background: 1.1 px a tick at 60 ticks a second is 66 px, so 6.6 m, a second. The readout gains about 66 m in 10 s.
- **Scroll start, logged once (`?debug=1`):** exactly one `scroll start tick=31` line after the start line. In about 10 s of play no second one appears, including across a fall, its `respawn from` line and the wait. (DRA-23) A retry starts a new run, and the new run logs its own `scroll start tick=31`. Source: systems/scroll.md, Rules, Logging; 03-world-and-camera.md, rule 4.
- **Readout counts up (`/`):** a screenshot right after play starts shows `0 m` at the top-left, with its text top near y 24. Screenshots about 5 s and 10 s later, with no key held (DRA-23: the ship falls once, then waits at the center), show larger whole numbers, the 10 s one about 66 m. Within a run the number never goes down. Source: scope report DRA-13, Player sees; systems/hud.md, Layout.
- **Hovering still earns meters (`/`):** hold ArrowUp for about 5 s so the ship sits on the top line. The readout keeps counting at the same rate as with no key held. Source: 03-world-and-camera.md, Edge cases.
- **Starfield moves (`/`):** the canvas has (90, 100, 140) pixels. Two screenshots about 1 s apart, after the first 0.5 s, show the dots about 66 px lower, with dots that left the bottom back at the top. In the first 0.5 s after play starts they sit still. Source: systems/scroll.md, Presentation.
- **No overlap in debug mode (`?debug=1`):** the four green overlay lines sit at the top-left, and the white readout sits below the last one, with a gap and no shared pixel row. Press F3: the overlay text goes away and the readout stays exactly where it was. F3 again brings the overlay back, still with no overlap. The overlay shows only x, y, vx and vy and its two lines, as in DRA-6. (DRA-23) The white hearts at the top right are not part of this check; read the top-left area only. Source: systems/hud.md, Rules; scope report DRA-13, Decision log.
- **Top line is still a ceiling (`?debug=1`):** the DRA-6 ArrowUp check still ends at `y=184.00`. Source: systems/ship.md, step 7.
- **Package contents:** as for DRA-6, and `core/scroll.py`, `ui/starfield.py` and `ui/hud.py` must be in `game.apk`.
