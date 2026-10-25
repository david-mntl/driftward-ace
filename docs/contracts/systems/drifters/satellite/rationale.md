# Drifters, the satellite, rationale
Part of: drifters
Read when: you ask why the satellite is built the way it is.

## Rationale

- **The satellite's angle is a per-variant extra (DRA-39).** Variants change values only, and the angle is the only value that tells flat from angled. `VariantExtra` lets each drifter type its own per-variant values in its own module, checked by the app against that drifter's own schema. Core stays typed: `born` checks the subclass.
- **The satellite stores velocities, not the angle alone (DRA-39).** A drifter carries final numbers only. `angle_degrees` and `invert` stay on it for the warning tilt.
- **The warning copy is turned, the satellite is not (DRA-39).** 02-satellite.md, rule 8: "The satellite never rotates, so its boxes stay upright." Rule 1 tilts only the warning copy. `warning_tilt_degrees()` is a base hook so the fireball's tilted warning reuses it.
- **The satellite's look reads its hitbox boxes (DRA-39).** Its placeholder look is "the two hitbox boxes, filled". Drawing exactly those boxes with `draw_shape` keeps the look and the hitbox the same, as the ship view does. The order (body first) is fixed in its schema so the view knows which box is white.

- **No art task.** Sprite art is out of scope (scope report DRA-39, Out). Every look is a placeholder drawn in code.
