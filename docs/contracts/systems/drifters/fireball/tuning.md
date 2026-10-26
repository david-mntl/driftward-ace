# Drifters, the fireball, tuning
Part of: drifters
Read when: you change the fireball's tuning file or its checks.

## Rules

- **The fireball's file** (DRA-56). Its own type values (`angle_degrees`, `tail_ratio`) sit next to the shared ones, and each variant gives `head_width` only, instead of `width`, `height` and `hitbox`. `app.tuning` builds from it: per variant, `VariantTuning(width=head_width, height=head_width, hitbox=fireball_hitbox(head_width, tail_ratio, angle_degrees, False), extra=None)`; for the type, `DrifterTypeTuning.extra = FireballTypeExtra(angle_degrees=..., tail_ratio=...)`. The file's values: `default_variant` small; `small` 21 and `big` 32; `speed_ratio` 0.47; `entry_warning_ticks` 60; `angle_degrees` 35; `tail_ratio` 0.5. Every number the fireball uses is in this file or in `hazards.json`; none is in code. Source: drifters/06-fireball.md, Values (guess); scope report DRA-56, Limits ("Every value in the tuning file, never hard-coded").
