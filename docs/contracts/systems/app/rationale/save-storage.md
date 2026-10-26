# App, save storage, rationale
Part of: app
Read when: you ask why the app's save storage works as it does.

## Rationale
- **The app owns localStorage.** It is browser I/O, read through pygbag's `platform.window`, like the URL switch and the console log. Core gets checked values and never sees the browser, so the top-10 rules are tested without one.
- **One key, one JSON document.** The list and the last nickname are written together, so a failed write can't leave them out of step, and one read gives everything. The key name is technical; the GDD leaves names and shape to the schema (11-save-data.md, rule 4).
- **Checked at the edge, trusted in core.** game/CONTEXT.md: validate where data comes from the browser. The order check matters because core's place rule assumes an ordered list.
- **Broken data is left alone.** Rule 5 says broken saves save nothing. Overwriting would destroy a list the player might get back (another version, a hand edit). The player gets saves back by clearing browser data, as the GDD's edge cases say.
- **A failed write stops saves for the page.** Rule 5 again: saves that don't work save nothing and show no BEST. Trying again on the next save would show a BEST that the next page load won't have.
- **Read once, at startup.** The list only changes through this page's own saves, which the flow already holds. Two tabs open at once each keep their own copy, and the last write wins; that is a rare case the GDD doesn't cover, and reading every frame would cost time in the browser for nothing.
- **Desktop has no saves.** The GDD's storage is localStorage only, and runtime files outside the browser are not allowed. Desktop runs are for development; done means the browser (15-tech-constraints.md, rule 6).
- **No error screen for saves.** 15-tech-constraints.md rule 8 is for unexpected errors. A blocked or broken storage is expected (rule 5), so it is a WARNING and the game runs on.
