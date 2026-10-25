# Drifters, the coin, rationale
Part of: drifters
Read when: you ask why the coin is built the way it is.

## Rationale

- **The coin is born ACTIVE (DRA-62).** "No warning of any kind" means no WARNING state at all: `tick_warning` with 0 ticks would still leave one drawn state in WARNING, and the entry warning would show for a frame. Overriding `born` keeps the base rule ("every drifter is born in WARNING") true for every hazard, and the coin says in one line that it has none. It never logs `drifter active`, because it never turns from WARNING to ACTIVE.

- **The popup's values ride on the coin (DRA-62).** Its length and rise are coin values in the coin's file, which only the app reads. Copying them onto the coin at birth, like the chain lightning's timers, lets the coin build its own popup with no tuning in `step_run`.
- **The coin's drawn parts need no margin (DRA-62).** The fireball needed `DRAW_MARGIN` because its radii are fractions. The coin's sizes are even whole numbers and its view draws on whole pixels around the rounded center, so each pixel edge sits on a whole px within 0.5 px of the box edge. A box edge at or past 480 then puts the pixel edge at 480 or past too. So the plain boxes are exact, and the drop points in Diagram land clear of the line (y 490.50 against 490). The schema asks for even sizes to keep this true after tuning.
- **The coin's 12 × 20 is drawn on exactly 12 columns and 20 rows (DRA-62).** An even width has no middle pixel, so each point ends in a 2-px tip and the sides run at 45°. That keeps the two halves 6 columns each ("split down the middle"), the body 10 rows, each point 5 rows, and the glint the Director approved, at (3, 3), one pixel clear of the rim.
- **The rim and ring line width and the colors stay in the view (DRA-62).** The scope report asks for every value in the tuning file, and every size, point value and timing is there. Colors are placeholder look values kept in views, as for every drifter. The 1 px line width is part of the same look, and a wider rim would draw outside the boxes `drawn_parts` promises, so it isn't a free knob. The popup's font is the HUD's look, kept in its view like the HUD's own font size.
- **No art task (DRA-62).** The galaxy, the cloud, the shine, the glint animation and sound are out of scope (scope report DRA-62, Out). The look is a placeholder drawn in code.
