# Drifters, the floating island, tuning
Part of: drifters
Read when: you change the floating island's tuning file or its checks.

## Rules

- **The floating island's file** (DRA-86). `default_variant`, `variants` and its own type value `arm`. Each variant gives `shape` (an `IslandShape` value), `width` and `height`, and no `hitbox`. It has no `speed_ratio` and no `entry_warning_ticks`: a parked blocker has neither. `app.tuning` builds from it: per variant, `VariantTuning(width=float(width), height=float(height), hitbox=island_hitbox(IslandShape(shape), width, height, arm, False), extra=IslandVariantExtra(shape=IslandShape(shape)))`; for the type, `DrifterTypeTuning(..., speed_ratio=0.0, entry_warning_ticks=0, extra=IslandTypeExtra(arm=float(arm)))`, the two zeros never read as tuning (Spawner, step 4; Floating island, Born). The file's values: `default_variant` rectangle; `arm` 40; `rectangle` rectangle 320 × 120; `box` rectangle 120 × 120; `l_shape` l_shape 320 × 120; `t_shape` t_shape 320 × 120; `triangle` triangle 320 × 120. Every size the island uses is in this file; none is in code. Only the look's two colors and its 2 px edge stay in the view (Rationale). Source: drifters/05-floating-islands.md, Values and Shapes; scope report DRA-86, Limits ("Every value in the tuning file, never hard-coded").
