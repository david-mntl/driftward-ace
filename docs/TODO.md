# TODO

Things to take care of later. Not scheduled yet.

## The top-right corner warning is hidden under the HUD hearts

- **Found:** DRA-56 integration, 2026-10-18. See `docs/reports/integration/DRA-56.md`, Observation 1.
- **What happens:** a fireball that enters at the top-right corner (`invert`, no position) shows its entry warning at (628, 12). The HUD hearts are drawn on top in the box (608, 8) to (632, 32). While the player has lives, only about 2 orange pixels of the warning's copy show, so you can't tell which way it will fly.
- **Why it matters:** Pillar 2, See it before it hits you. GDD `10-ui.md` rule 1 says the HUD must never hide a warning.
- **Blocked on:** UI-01 (HUD margins), still `TBD` in `design/gdd/90-open-questions.md`. Both the HUD and the warning follow their contracts, so the contracts clash. It needs a Director call, then the Architect.
- **Not only the fireball:** any drifter whose warning lands near the top-right corner can hit this.

## The top-left corner warning is drawn under SCORE, GRAZE and BEST

- **Found:** DRA-61 scope, kept in DRA-117 (GRAZE) and DRA-126 (BEST). See those scope reports, Objection 1 or 2.
- **What happens:** the HUD text at the top left is drawn over any entry warning in that corner, such as the default fireball's.
- **Why it matters:** Pillar 2, See it before it hits you. GDD `10-ui.md` rule 1 says the HUD must never hide a warning.
- **Blocked on:** UI-01 (HUD margins) or the HUD redesign. The Director chose the override for now.
