# Art and audio
Status: draft
Depends on: [07-objects.md](07-objects.md), [10-ui.md](10-ui.md)

## Summary
The look is not set yet. The direction: a dark navy and purple starfield and glowing hazards. Until the style is set, the background is a black placeholder.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| placeholder_bg | (0, 0, 0) | RGB | — | guess | starting placeholder |
| art_style | TBD | — | — | TBD | AA-01 |
| palette | TBD | — | — | TBD | AA-01 |
| background | TBD | — | — | TBD | AA-02 |
| audio_format | see [15-tech-constraints.md](15-tech-constraints.md#values) | — | — | locked | — |
| sound_list | TBD | — | — | TBD | AA-03 |
| particle_cap | TBD | particles | — | TBD | AA-04 |

## Rules
1. Each object's sprite size and look go in its spec in `objects/`, and the ship's in [04-ship.md](04-ship.md), not here.
2. **Readability first.** Hazards, warnings and coins must stand out from the background at a glance. Source: [01-vision.md](01-vision.md), Pillar 2.
3. Glow is pre-rendered, never computed per frame. Source: Director.
4. Particles have a hard cap (`particle_cap`). Source: Director.
5. Audio format and unlock rules: [15-tech-constraints.md](15-tech-constraints.md).

## Edge cases
- Art for an object whose spec is still draft: wait, or use a placeholder shape the Director approves.

## Open
- AA-01, AA-02, AA-03, AA-04.

## How to extend
A new visual or sound rule that applies to every object goes here. Anything specific to one object goes in that object's spec.
