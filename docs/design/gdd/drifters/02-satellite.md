# Satellite
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (top sideways speed)

## Summary
A satellite that crosses the screen from a side wall in a straight line. The flat one flies straight across at one height. The angled one sinks gently as it crosses, like a satellite falling out of orbit. It never targets the ship. It's the meteorite's straight, steady path, turned sideways.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Side crosser | — | — | locked | Director |
| enters_from | Sides: the left wall by default, the right wall with `invert` | — | — | locked | Director |
| kind | moving drifter ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-drifters.md |
| variants | flat: straight across, 0° from level. angled: 20° below level | degrees | — | guess | Director |
| default_variant | flat | — | — | guess | Director |
| size | 36 wide, 12 tall: a 12 × 12 body with a 36 × 6 panel bar through its middle | px | — | guess | Director |
| hitbox | two boxes: the body, 12 × 12; the panel bar, 36 × 6, both centered | px | — | guess | Director |
| speed_ratio | 0.375 × the ship's top sideways speed ([../04-ship.md](../04-ship.md), derived values), measured along its path. Its own number; it only starts equal to the meteorite's | — | — | guess | Director |
| speed | ≈ 2.5 at Level 1, along its path, from `speed_ratio` and the current ship guesses. Both variants share it | px/tick | — | guess | derived |
| direction | left to right, unless the placement sets `invert`, which mirrors it: right to left | — | — | guess | Director |
| entry_warning_ticks | the shared value ([../07-drifters.md](../07-drifters.md)) | ticks | — | — | 07-drifters.md |
| telegraph | none. It never strikes; it only flies | — | — | locked | Director |
| specialty | none | — | — | locked | Director |
| graze | yes | — | — | locked | 06-scoring.md |
| look_reference | White body with blue solar panels on both sides. It looks wrecked but still flies: torn panel edges, a scorched, cracked body. Thin fuchsia magnetism rays glow on it and move with the panel swing | — | — | guess | Director |
| placeholder_look | the two hitbox boxes, filled: body white (240, 240, 240), panel bar blue (60, 110, 220), body drawn on top | RGB | — | guess | Director |
| start | just outside the left wall, at its placed y ([../07-drifters.md](../07-drifters.md) rule 14). With `invert`: just outside the right wall | px | — | guess | Director |

At Level 1 the flat one crosses the screen in about 270 ticks (4.5 s). The angled one moves about 2.35 px/tick across and 0.86 px/tick down, so it sinks about 230 px over the full width. Derived from the guesses above; not tuning keys.

## Rules
1. **Appears:** at its start spot, then flies into view. Its entry warning shows first, at its y against the wall it enters from ([../07-drifters.md](../07-drifters.md) rule 9). For the angled variant the warning copy is tilted along its path, so it also shows which way it will fly.
2. **Telegraph:** none. The entry warning is its only warning.
3. **Moves:** in a straight line at `speed` along its path, every tick, away from the wall it entered from. Flat: level. Angled: 20° below level. No targeting, no turning. The scroll doesn't add to it ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
4. **Hits:** touching the body or the panels is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)).
5. **Leaves:** once fully off screen past the far wall or below the floor ([../07-drifters.md](../07-drifters.md) rule 12). It flies through the walls ([../07-drifters.md](../07-drifters.md) rule 15).
6. **Scales:** `speed` × the level's hazard speed, set when it appears ([../08-difficulty.md](../08-difficulty.md)). The angle never scales.
7. **Placing:** its y, its variant and `invert`.
8. **Looks and sounds:** placeholder boxes until the look is drawn. The satellite never rotates, so its boxes stay upright. Its panels swing about 25° to each side, back and forth, while the body stays still. The swing is drawn only. The hitbox panel bar stays flat. Sound: none yet.
9. **wave_check notes:** none beyond the shared rules.

## Edge cases
- The ship is invulnerable when it touches the satellite: no hit, the satellite keeps flying.
- The ship is still inside the satellite that hit it when invulnerability ends: no hit until its re-hit cooldown ends ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 1.5).
- A flat satellite placed above the top line can never reach the ship. Allowed; it's scenery with a warning.
- A satellite meets another drifter or an island: it flies through ([../07-drifters.md](../07-drifters.md) rule 15).

## Open
- None.

## How to extend
A new angle or size is a new variant in Values. A path that curves, patrols back and forth or aims at the ship is a new behavior, so a new drifter.
