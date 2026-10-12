Verdict: ship
Created by: scope-guardian
Feature: DRA-5 Game base: logging, run modes, error screen
Parent: none

## Request
"I want to create a first screen where the ship is gonna get the basics of the movement.
- Make sure that the main is isolated and follows good principles.
- Make sure that a logging system is created first of all and used everywhere. A good logging system has to be used everywhere. Make it a rule under game/CONTEXT.md so game developer and ui-developer uses it anytime they do
- Make sure to create a debug mode and a normal mode.
- Make sure to stablish a proper error handling. Make it also a rule."

This report covers the logging, run modes, error handling and entry point. The ship movement is DRA-6.

## Feature
The game starts in normal mode, or in debug mode when launched with a debug switch. It logs its startup and its mode. Every part of the game logs through one shared setup, by event, never every tick. When something unexpected breaks, the game logs the full error and shows an error screen instead of freezing the page. The entry point does nothing but start the app.

## Limits
In:
- Logging setup in one place: level per mode, one line format.
- Run mode, read once at startup from the URL, the desktop environment, or the launch script's debug option.
- A one-line entry point that starts the app.
- The async loop at the fixed 60 Hz tick, with one top-level error guard.
- The error screen, in both modes.
- A `--debug` option on the start script that prints the debug URL.

Out: the ship, the debug overlay (DRA-6), HUD, control card, any game rule.

## Player sees
Run `game/scripts/start-driftward-ace.sh --debug` and open the printed URL. You get a black 640×480 screen, and the browser console shows a startup line with `mode=debug`. Without `--debug`, the line says `mode=normal`.

## Fit
- Pillars 1 to 3: not touched. No game rule changes. Source: 01-vision.md, Pillars.
- Async loop, no blocking, fixed tick: fits. Source: 15-tech-constraints.md, rules 1 and 2.
- Browser performance: fits. Logs are by event only. Source: 15-tech-constraints.md, rules 5 and 9.
- Run modes and error screen: fit. Source: 15-tech-constraints.md, rules 7 and 8.
- Locked decision 8 (control card after click-to-start): not built yet, not contradicted. Source: 01-vision.md, Locked decisions.

## Values needed
- run_mode_default, debug_switch_browser, debug_switch_desktop, debug_switch_launcher: 15-tech-constraints.md, Values. Proposed by guardian, approved by Director in chat.
- log_level_normal INFO, log_level_debug DEBUG, log_format, log_policy: 15-tech-constraints.md, Values. Proposed by guardian, approved by Director in chat.
- error_screen text, error_text_color: 10-ui.md, Values. Proposed by guardian, approved by Director in chat.
- debug_text_font (the error screen's debug line uses it): 10-ui.md, Values. Proposed by guardian, approved by Director in chat.
- screen_w × screen_h 640×480: 03-world-and-camera.md, Values (guess).
- placeholder_bg (0, 0, 0): 12-art-and-audio.md, Values (guess).
- tick_rate 60: 15-tech-constraints.md, Values.

All of these are now in the GDD. None is flagged "not in GDD".

## Objections
1. "Used everywhere" logging clashed with the old `game/CONTEXT.md` rule "No log inside the per-tick step". A line every tick floods the console and slows Python in WebAssembly. Source: 15-tech-constraints.md, rule 5. Alternative: a logger in every module, and per-tick code logs only events. Resolved: the Director chose log by event.

## Decision log
- Director split the request: DRA-5 (this base) ships first, then DRA-6 (ship movement).
- Director chose: debug switch read once at startup (URL `debug=1`, env `DRIFTWARD_DEBUG=1`), plus a `--debug` option on the start script.
- Director chose: log + error screen on an unexpected error. Debug mode adds the error type and message.
- Director chose: log by event, never by tick (objection 1).
- Director chose: startup code lives in `game/app/`, owned by the Integration Engineer, together with `game/scripts/`. Drawing the error screen goes to the UI Developer in `game/ui/`. Roster row 12 updated.
- Director asked that the guardian's proposed values be written into the GDD. Done with the Director's approval.
- Director approved the final feature in chat by approving the plan ("Yes, and use auto mode").
