# Level-up, tuning file and loader
Part of: level-up
Read when: you change `game/tuning/level_up.json`, its schema or how it is loaded and checked.

## Interface
```python
# game/app/level_up_tuning.py (Integration Engineer). Not a startup module: it imports ui, so only
# app.frame imports it, inside the guard.
LEVEL_UP_FILE: str   # "level_up.json", in app.tuning.TUNING_DIR

def load_level_up(hud_rules: HudRules) -> tuple[LevelUpRules, LevelUpLook]: ...
    # Reads TUNING_DIR / LEVEL_UP_FILE once at startup, in both run modes, after load_hud_rules() (the
    # palette resolves color keys). Checks every rule of docs/contracts/schemas/level-up.schema.json
    # by hand, and the rules below. Builds core.level_up.LevelUpRules from level_up_rest,
    # arrival_tick and banner_ticks, and ui.level_up_rules.LevelUpLook from the sections. Raises on a bad file.

# game/app/assets.py, changed
def load_level_up_fonts(hud_rules: HudRules, look: LevelUpLook) -> LevelUpFonts: ...
    # Exo 2 Bold: the file named by hud_rules.fonts.ui_file, at look.number.font_size.
    # Share Tech Mono: hud_rules.fonts.label_file, at look.label.font_size. A missing file raises FileNotFoundError.
```

## Rules
Source: 10-ui.md, rule 12 (every HUD value is configurable) and rule 11; away log DRA-148, D7 (the look and motion get their own tuning file, not new keys in `hud.json`); scope report DRA-148, Limits ("Every timing, size and color in tuning, never hard-coded"); game/CONTEXT.md, Error handling.

- **One file, two readers.** `level_up_rest`, `arrival_tick` and `banner_ticks` become `LevelUpRules` (`rest_ticks`, `arrival_ticks`, `banner_ticks`); every other section becomes the `LevelUpLook` record of the same name. The look holds no timing core needs; core holds no look. The file is in `game/tuning/`; the main session writes it, from the key list in the schema.
- **Strict.** Unlike the graze and last-life files, every field of every section is required and nothing has a default in code: a missing file raises `FileNotFoundError`, a missing, unknown or badly typed field raises `ValueError` naming `tuning/level_up.json` and the field (`tuning/level_up.json: band.alpha must be an integer from 0 to 255`); invalid JSON raises `ValueError("tuning/level_up.json: not valid JSON: <decoder message>")` from the decode error. A number is an `int` or a `float` as the schema says, never a `bool`.
- **Colors.** A color is `#rrggbb` or a key of `hud_rules.palette`. Else `tuning/level_up.json: colors.glass 'foo' is not a hex color or a HUD palette key`. Source: 12-art-and-audio.md, HUD colors.
- **Rules the schema can't express**, each checked at load, each raising `ValueError` with the file and the fields:
  - Core: `arrival_tick < banner_ticks`. When `level_up_rest > 0`: `banner_ticks <= level_up_rest`. When it is 0 the feature is off and the three numbers are only type-checked.
  - The pop fits the banner's life: `arrival_tick + pop.ticks <= banner_ticks`; and `pop.ticks` is at least `pop.flash_ticks`, `pop.bar_flash_ticks` and `pop.box_flash_ticks`.
  - Band: `open_start < open_end <= close_start < close_end <= arrival_tick`.
  - Number: `fall_start < fall_end`; `fall_end + squash_ticks <= fly.start`.
  - What starts on landing is over before the flight: `fall_end + max(ring.ticks, streaks.ticks, bump.ticks) <= fly.start`.
  - Label and pips: `label.fade_in_start < label.fade_in_end <= hold.fade_out_start < hold.fade_out_end <= arrival_tick`; `pips.start < pips.end <= hold.fade_out_start`; `pips.pop_ticks <= pips.end - pips.start`.
  - Glint: `glint.start < glint.end <= hold.fade_out_start`.
  - Flight: `fly.start < arrival_tick`.
  - `ring.start_diameter < ring.end_diameter` and `streaks.start_radius < streaks.end_radius`.
- Logs one INFO line after a good load: `level up loaded level_up_rest=%d arrival_tick=%d banner_ticks=%d`. Nothing else. Source: game/CONTEXT.md, Logging.
- A bad or missing file raises inside the guard, so the page shows the error screen and the log names the file and the field. Source: 15-tech-constraints.md, rule 8.
- **Debug mode and normal mode** read the same file. Core's behavior never depends on the run mode. Source: 15-tech-constraints.md, rule 7.
