# Ship
Status: draft
Depends on: [03-world-and-camera.md](03-world-and-camera.md), [05-lives-and-damage.md](05-lives-and-damage.md)

## Summary
The ship has no weapon and no brake. Arrow keys add thrust, gravity always pulls down, sideways speed bleeds off through drag, and fall speed is capped. All physics values are tuning keys: the GDD holds the starting value and slider range, the live tuning file holds the live value, and the Director copies tuned values back here.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| ship_w | 32 | px | — | guess | starting placeholder |
| ship_h | 32 | px | — | guess | starting placeholder |
| hitbox | TBD | — | — | TBD | SH-03 |
| look | TBD | sprite, colors, animation | — | TBD | SH-06 |
| look_reference | Small rocket with an orange flame | — | — | guess | Director |
| placeholder_look | white (255, 255, 255) filled rectangle, `ship_w` × `ship_h` | RGB | — | guess | starting placeholder |
| gravity | 0.16 | px/tick² | TBD | guess | Director tuning guess |
| thrust_side | 0.42 | px/tick² | TBD | guess | Director tuning guess |
| thrust_up | 0.42 | px/tick² | TBD | guess | Director tuning guess |
| thrust_down | 0.42 | px/tick² | TBD | guess | Director tuning guess |
| drag_x | 0.94 | × per tick | TBD | guess | Director tuning guess |
| fall_cap | TBD | px/tick | TBD | TBD | SH-01 |
| min_fall_ticks | 54 | ticks (0.9 s) | — | locked | Director |

All Range cells: SH-02.

Derived from the guesses above. Recompute when a value changes:
- Net climb with up held: 0.42 − 0.16 = 0.26 px/tick².
- Net dive with down held: 0.42 + 0.16 = 0.58 px/tick², until `fall_cap`.
- Top sideways speed with a side key held: `thrust_side × drag_x / (1 − drag_x)` ≈ 6.6 px/tick (about 400 px/s).

## Rules
1. **Fixed tick.** One physics step per 60 Hz tick. Never a variable dt. Source: [01-vision.md](01-vision.md), Locked decisions; [15-tech-constraints.md](15-tech-constraints.md).
2. **Tick order:**
   1. Thrust: left subtracts `thrust_side` from vx, right adds it, up subtracts `thrust_up` from vy, down adds `thrust_down`. Opposite keys cancel. (Screen y is down, so +vy is falling.)
   2. Gravity: add `gravity` to vy.
   3. Drag: `vx *= drag_x`.
   4. Fall cap: if `vy > fall_cap`, set `vy = fall_cap`.
   5. Move: `x += vx`, `y += vy`.
   6. Side walls: clamp, `vx = 0`, no bounce ([03-world-and-camera.md](03-world-and-camera.md) rule 6).
   7. Top line: camera follow ([03-world-and-camera.md](03-world-and-camera.md) rule 2).
   8. Floor check: fall ([05-lives-and-damage.md](05-lives-and-damage.md)).
3. **Every tick runs every step.** No hit or fall ever pauses the physics or the input. Source: [01-vision.md](01-vision.md), Pillar 1; [05-lives-and-damage.md](05-lives-and-damage.md).
4. **Input only changes acceleration.** No key sets a speed or stops the ship. Source: [01-vision.md](01-vision.md), Pillar 1.
5. **Up beats gravity.** `thrust_up` must stay greater than `gravity`, or the ship can't climb. Every slider range must keep this true.
6. **Fall cap bound.** A fall from the top line (y 168) to the floor (y 480) is 312 px and must take at least `min_fall_ticks`. So `fall_cap` must be ≤ 312 / 54 ≈ 5.77 px/tick.
7. **No vertical drag and no upward speed cap**, unless SH-05 says otherwise.
8. **Looks.** The ship's look lives in this file, like every object's look lives in its spec. Until `look` is set, draw `placeholder_look`. Thrust flame, blink and burst-and-rebuild must all stay readable at `ship_w` × `ship_h`. Blink and burst: [05-lives-and-damage.md](05-lives-and-damage.md). Global style and palette: [12-art-and-audio.md](12-art-and-audio.md).

## Edge cases
- Left and right held together: they cancel, and drag still slows the ship.
- Up and down held together: they cancel, and gravity still pulls.

## Open
- SH-01, SH-02, SH-03, SH-04, SH-05, SH-06.

## How to extend
A new physics value: add a row with unit, range and status, and place it in the tick order. If it's live-tunable, the tuning file needs a matching key, which is a schema change.
