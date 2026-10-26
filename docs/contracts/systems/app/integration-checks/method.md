# App, integration checks, method
Part of: app
Read when: you run any browser check: how the checks are done.

## Rules

How the browser checks below are done. These methods are the checks as written, not stand-ins, so using them is never an observation on its own. Source: Director decision (DRA-19 close-out).
- **Screenshot** means reading the canvas pixels and comparing them with the expected color or text, for example text drawn in the same page with the game's own font. A pixel match counts as the screenshot.
- **Hide the tab** means freezing the page's main thread for the stated time, then letting it run again. For the game this is the same thing: one long gap between frames.
- **Real browser behavior** (pygbag's click screen, a truly hidden tab) can only be seen in a desktop browser. The Director checks it by hand when the frame loop or start-up changes, and before a release. The click-to-start checks below still record what they ask for, in Browser run. They go under Observations only when the result differs from the earlier runs (the game starting before any click, in the test browser, is the known result).
