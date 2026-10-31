# Art and audio
Status: draft
Depends on: [07-drifters.md](07-drifters.md), [10-ui.md](10-ui.md)

## Summary
A storm you can't fight, only fly through. Space is dark navy. Everything the anomaly touched carries a thin fuchsia rim and drifts toward a black hole far off in the bottom-left corner. Hazards glow hot. Coins glow fuchsia. The ship is the one clean thing left: pale plating and cobalt blue. Sprites are smooth and glossy, not pixel art. The background is painted once and stays dim. Until the background is drawn, it is a black placeholder.

## World brief
The player never reads this. It gives the art a feeling to aim at.

**The collapse.** Two galaxies fell into each other. Dark matter that no one could see or measure fed the collapse. What was left is the largest black hole that has ever existed. It sits far away, in a bottom corner of everything, and it is still eating.

**The anomaly.** The collapse didn't follow physics. It broke it. A wave of magnetism tore loose and now bounces through space with no source, no pattern and no reason. It hits one rock and skips the next. It turns a planet inside out and leaves its moon alone. Nobody can measure it, predict it or explain it. It just happens.

**What it does.** Stars die and are dragged in, still burning. Planets crack into floating islands. Living things mutate into shapes that shouldn't be possible. Metal ships and satellites drift dead, or worse, half alive. Every object the anomaly touches carries its mark: a fuchsia shimmer along its edge, brightest on the side facing the black hole.

**The pull.** Everything moves one way. Rocks, wrecks, planets, auroras, whole galaxies stream in long curved rivers toward the corner where the black hole waits. Up close the pull just feels like down. You feel it as gravity.

**The light.** Light bends here. It reflects and splits, so everything looks glossy and wet. Highlights are hard and white, rims glow fuchsia, and shadows go deep navy, almost black. Colors are more vivid than they should be.

**The new universe.** Some of the anomaly condenses into small crystals with a galaxy turning inside. They are pure fuchsia and purple, the brightest thing on screen. Maybe they are seeds of something new. Collecting them is the only hopeful thing you can do.

**You.** You were on a reconnaissance mission, sent to find out why your planet's physics had turned strange. Then the galaxies collapsed. Your ship came through untouched: no shimmer, no mutation. Pale plating, deep blue lines, a blue flame. No one knows why. Maybe you are the last one left.

**Mood.** Beautiful and doomed. A storm you can't fight, only fly through. Lonely, never horror. The anomaly isn't evil. It isn't anything. It just doesn't make sense.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| placeholder_bg | (0, 0, 0) | RGB | — | guess | starting placeholder |
| art_style | smooth: drawn at 4× the game size with gradients and glossy rims, then shrunk to game size. Not pixel art. Shown at 1× | — | — | guess | Director |
| palette | the color language below. Exact RGB values come with the drawn art | — | — | guess | Director |
| glow | hazards, warnings and coins only. The HUD stays flat. The ship: SH-06 | — | — | guess | Director |
| motion | look only. 2 or 3 states per object (for example idle, charge, fire), each a short loop of frames drawn ahead of time | — | — | guess | Director |
| background | three layers, described below | — | — | guess | Director |
| background_numbers | painting sway loop 900; planets on screen 3; planet speed 0.15; planet size ×1; river light specks 30 at most; river loop 900; river and swirl strength 0.6; swirl specks 8; swirl loop 480; bottom glow 40 tall, strength 0.25. The near layer has no numbers yet: it is not built | ticks; planets; px/tick; ×; specks; ticks; 0..1; specks; ticks; px; 0..1 | see tuning file | guess | AA-02, Director: use guesses, tune later |
| audio_format | see [15-tech-constraints.md](15-tech-constraints.md#values) | — | — | locked | — |
| sound_list | TBD | — | — | TBD | AA-03 |
| particle_cap | TBD | particles | — | TBD | AA-04 |

### Color language
| Color | Means | Used on |
|---|---|---|
| Navy to near-black | empty space | the deepest background |
| Fuchsia and purple | magnetism, the anomaly | coins at full brightness, dim auroras, the rim light on touched objects |
| Orange and yellow | heat, danger | lava, fireball, entry warnings |
| Pale white-cyan | electricity | chain lightning, electric ball: a pale white-cyan core with thin purple and fuchsia arcs. Kept away from the ship's blue |
| Deep cobalt blue with pale plating | you, untouched | the ship and its cockpit: cobalt neon lines, a blue flame, silver-grey and pale plating |

### Background
- **Far layer.** One large painting. Rivers of stars, gas and debris curve toward a dim, distant black hole at the bottom left, mostly off screen. The rays sway very slowly, and a soft patch of light turns along the hole's rim. It is a loop of frames made ahead of time, faded from one to the next, and it keeps the painting's brightness. The sway is slow and small, so it never pulls the eye off the objects.
- **River light.** Small glowing specks and streaks travel along the curves into the black hole, so the rivers look like they flow. Their number is capped. A small swirl loops around the black hole.
- **Middle layer.** Dark outlines of broken planets, scrolling straight down, slowly.
- **Near layer.** A few dust streaks, scrolling straight down, faster.
- **Bottom glow.** A faint fuchsia glow along the bottom edge: where the pull comes from, and where falling costs a life.

## Rules
1. Each drifter's sprite size and look go in its spec in `drifters/`, and the ship's in [04-ship.md](04-ship.md), not here.
2. **Readability first.** Hazards, warnings and coins must stand out from the background at a glance. Source: [01-vision.md](01-vision.md), Pillar 2.
3. Glow is pre-rendered, never computed per frame. Source: Director.
4. Particles have a hard cap (`particle_cap`). Source: Director.
5. Audio format and unlock rules: [15-tech-constraints.md](15-tech-constraints.md).
6. **Coins own solid fuchsia.** A solid, bright fuchsia shape always means a coin. Hazards may carry fuchsia only as thin accents. Source: Director.
7. **The background stays behind.** It is always dimmer and less saturated than anything the player can touch. Hazards falling over the black hole corner stay easy to see. Source: Director; Pillar 2.
8. **Rim light.** Every object the anomaly touched gets a thin fuchsia rim on its bottom side, the side facing the black hole. The ship has none: it is untouched. Source: Director.
9. **Looks never change play.** Animation, rotation frames and random looks are visual only. Hitboxes never rotate, move or resize with the look. Source: Director; [07-drifters.md](07-drifters.md) rule 8.
10. **A fixed pool of looks.** A drifter with several looks picks one from a fixed pool each time it appears. Art is never made new per run. Source: Director.
11. **Painted once.** Background layers are images made ahead of time and loaded by the game, never drawn shape by shape each frame. A layer that moves is a loop of such images. Source: Director.
12. **Words, not pictures.** The style is defined in words in this file. Images from other works are never part of this design and never ship. Only art made for the game, or converted from a source that is free to use and credited, ships. Source: Director.
13. **Motion must show at game size.** A turn smaller than about 20° does not read on a sprite this small. A turning object uses a full turn in steps of 45° or less, so the loop has no back-and-forth. One exception: a part that swings on a fixed body, like the satellite's panels, goes back and forth. The light and the rim stay fixed while the shape turns. Frames sit in one strip, all the same size. Source: Director.

## Edge cases
- Art for a drifter whose spec is still draft: wait, or use a placeholder shape the Director approves.

## Open
- AA-02 (background numbers: still to tune after a frame-rate check in the browser build, and the near layer's), AA-03, AA-04.

## How to extend
A new visual or sound rule that applies to every drifter goes here. Anything specific to one drifter goes in that drifter's spec. A new color meaning is a new row in the color language, with the Director's approval.
