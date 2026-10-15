# UFO
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (top sideways speed)

## Summary
A saucer that crosses the screen from one side to the other, weaving up and down. About every 1.3 s it swings toward a new height, so its path looks random and can't be read from one pass. It turns smoothly, though, so where it heads next is always visible from where it is going now. A given wave always flies the same path, so a player who keeps coming back can learn it.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Wildcard mover | — | — | locked | Director |
| enters_from | Sides: left by default, right with `invert` | — | — | locked | Director |
| kind | moving drifter ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 3 | — | — | guess | 07-drifters.md |
| variants | one: standard | — | — | guess | Director |
| default_variant | standard | — | — | guess | Director |
| size | 40 wide: a disc 40 × 10, with a dome on top | px | — | guess | Director |
| hitbox | two shapes: the disc, a box 40 × 10; the dome, a circle of radius 9 centered on the middle of the disc's top edge | px | — | guess | Director |
| speed_ratio | 0.3 × the ship's top sideways speed ([../04-ship.md](../04-ship.md), derived values), forward across the screen | — | — | guess | Director |
| speed | ≈ 2.0 at Level 1, from `speed_ratio` and the current ship guesses | px/tick | — | guess | derived |
| weave_change_ticks | a new height every 60 to 96 ticks (1.0 to 1.6 s, about 1.3 s on average), picked from its seed | ticks | — | guess | Director |
| weave_step | each new height is 40 to 120 px from its current height, picked from its seed. Up and down alternate | px | — | guess | Director |
| weave_speed_max | 1.6, up or down | px/tick at Level 1 | — | guess | Director |
| weave_turn | 0.1: its up-or-down speed changes by at most this much per tick, so a full swing from up to down takes about 0.5 s | px/tick² at Level 1 | — | guess | Director |
| band | its center stays between y 188 and y 440 on screen, inside the ship's zone ([../03-world-and-camera.md](../03-world-and-camera.md) rule 2) | screen px | — | guess | Director |
| seed | fixed per placement: the same wave flies the same path every time. A placement may set `seed` to pick another path. Two UFOs in one wave never share a path | — | — | locked | Director |
| entry_warning_ticks | the shared value ([../07-drifters.md](../07-drifters.md)) | ticks | — | — | 07-drifters.md |
| telegraph | none. It never strikes; it only flies | — | — | locked | Director |
| specialty | none | — | — | locked | Director |
| graze | yes, once per UFO | — | — | locked | 06-scoring.md |
| look_reference | Saucer with a green dome. No beam | — | — | guess | Director |
| placeholder_look | the two hitbox shapes, filled: disc grey (170, 170, 185), dome green (90, 220, 110) | RGB | — | guess | Director |
| start | just outside the left wall, at its placed y ([../07-drifters.md](../07-drifters.md) rule 14). With `invert`: just outside the right wall. The placed y must sit inside `band` | px | — | guess | Director |

At Level 1 it crosses the 640 px screen in about 340 ticks (5.7 s), so it changes height about four times on the way. Derived from the guesses above; not tuning keys.

## Rules
1. **Appears:** at its start spot, then flies into view. Its entry warning shows first, at its y against the wall it enters from ([../07-drifters.md](../07-drifters.md) rule 9).
2. **Telegraph:** none. The entry warning is its only warning. Readability comes from rule 4: it never turns faster than `weave_turn`.
3. **Moves across:** at `speed` on screen, every tick, away from the wall it entered from. It never stops or turns back. The scroll doesn't add to it ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
4. **Weaves:** it flies level at its placed y until it is fully on screen. Then, every `weave_change_ticks`, it picks a new height `weave_step` away, up or down, taking turns. It eases toward that height with its up-or-down speed never above `weave_speed_max` and never changing by more than `weave_turn` per tick, without overshooting. If it gets there early, it flies level until the next change.
5. **Stays in its band:** a new height never leaves `band`. If there's less than 40 px of room in the turn's direction, it goes the other way instead.
6. **No targeting.** Its path comes from its seed only, never from the ship.
7. **Hits:** touching the disc or the dome is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)).
8. **Leaves:** once fully off screen past the far wall ([../07-drifters.md](../07-drifters.md) rule 12). It flies through the walls ([../07-drifters.md](../07-drifters.md) rule 15).
9. **Scales:** `speed`, `weave_speed_max` and `weave_turn` × the level's hazard speed. `weave_change_ticks` × the level's Timer ×. All set when it appears ([../08-difficulty.md](../08-difficulty.md)). `weave_step` and `band` never scale.
10. **Placing:** its y, `invert`, and optionally `seed`.
11. **Looks and sounds:** placeholder shapes until the look is drawn. Sound: none yet.
12. **wave_check notes:** one path per seed, so a wave has one outcome to check, like any other hazard. A placed y outside `band` fails the wave.

## Edge cases
- The ship is invulnerable when it touches the UFO: no hit, the UFO keeps flying.
- The ship is still inside the UFO that hit it when invulnerability ends: no hit until its re-hit cooldown ends ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 1.5).
- The UFO meets another drifter or an island: it flies through ([../07-drifters.md](../07-drifters.md) rule 15).
- The placed y sits outside `band`: the wave is wrong (rule 12).

## Open
- None.

## How to extend
A new size is a new variant in Values. Stopping, turning back, aiming at the ship or a beam that hurts are new behaviors: a specialty or a new drifter, with the Director's approval.
