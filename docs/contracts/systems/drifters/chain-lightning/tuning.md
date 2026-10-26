# Drifters, the chain lightning, tuning
Part of: drifters
Read when: you change the chain lightning's tuning file or its checks.

## Rules

- **The chain lightning's file** (DRA-47). Its own type values (`node_spacing`, `node_size`, `arc_width`, `charge_ticks`, `fire_ticks`, `charge_rays`, `ray_length`, `ray_width`, `entry_warning_icon`) sit next to the shared ones, and each variant gives `nodes`, `arcs` and `invert_mirror` instead of `width`, `height` and `hitbox`. `app.tuning` builds from it: per variant, `ChainLayout` (nodes × `node_spacing`), `VariantTuning(width, height, hitbox, extra=ChainLightningVariantExtra(layout))` with `layout_size` and `chain_hitbox`; for the type, `DrifterTypeTuning.extra = ChainLightningTypeExtra(...)` with `warning_layout` the layout of the variant `entry_warning_icon` names. The file's values are the Layout table and Values at Level 1 above. Every number the chain lightning uses is in this file or in `hazards.json`; none is in code. Source: scope report DRA-47, Limits ("Every value in the tuning file, never hard-coded").
