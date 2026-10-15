# Planet
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (tick order, thrust), [../06-scoring.md](../06-scoring.md) (graze)

## Summary
A planet drifts down with the world, wrapped in a gravity field you can see. Inside the field it pulls the ship toward it, gently at the edge and hard near the surface. Touching the planet costs a life. It never strikes and never switches off. The player spends thrust to stay clear, or skims close for a graze.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Gravity well | — | — | locked | Director |
| enters_from | Top: it scrolls in from just above the top edge ([../07-drifters.md](../07-drifters.md) rule 14) | — | — | locked | Director |
| kind | parked drifter: it doesn't move on its own, only with the scroll ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 3 | — | — | guess | 07-drifters.md |
| variants | one: standard. Looks are not variants; see `looks` | — | — | guess | Director |
| default_variant | standard | — | — | guess | Director |
| size | 64, a circle (radius 32) | px | — | guess | Director |
| hitbox | one circle, radius 32 | px | — | guess | Director |
| pull_radius | 150, from the planet's center | px | — | guess | Director |
| pull_max | 0.2, at the planet's surface | px/tick² | — | guess | Director |
| pull_shape | toward the planet's center. 0 at `pull_radius`, rising in a straight line to `pull_max` at the surface (32 px from the center) | — | — | locked | Director |
| entry_warning_ticks | the shared value ([../07-drifters.md](../07-drifters.md)) | ticks | — | — | 07-drifters.md |
| telegraph | none. It never strikes; the field is always on and always shown | — | — | locked | Director |
| specialty | none. The pull is its behavior, always on | — | — | locked | Director |
| graze | yes: the planet's circle grown by `graze_margin` ([../06-scoring.md](../06-scoring.md)) | — | — | locked | 06-scoring.md |
| looks | a list of named skins, filled when the art is drawn. Every skin has the same size and hitbox. Until then: one placeholder look | — | — | guess | Director |
| look_pick | random, each time a planet appears. Looks only; the game plays the same | — | — | locked | Director |
| look_reference | Purple sphere with faint rings showing the pull radius | — | — | guess | Director |
| placeholder_look | planet: filled circle in purple (140, 70, 200). Field: a 1 px ring at `pull_radius` and two faint 1 px rings that drift inward from it and fade, in (180, 120, 255) | RGB | — | guess | Director |

## Rules
1. **Appears:** at its placed x, just above the top edge, then scrolls into view. Its entry warning shows first, at its x against the top edge ([../07-drifters.md](../07-drifters.md) rule 9). Its field is on from the tick it appears.
2. **Telegraph:** none. The field ring is always drawn, so the player sees where the pull starts.
3. **Moves:** never on its own. It moves down with the scroll ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
4. **Pulls:** while the ship's center is inside `pull_radius`, it pulls the ship toward the planet's center by `pull_shape`. The pull is added in the ship's tick order right after gravity ([../04-ship.md](../04-ship.md) rule 2, step 2). It applies every tick gravity applies, so also while the ship is invulnerable, and not during the respawn wait. Pulls from overlapping planets add up. It pulls only the ship, never other drifters.
5. **Always escapable:** `pull_max` + `gravity` must stay below `thrust_up`, and `pull_max` below `thrust_side` ([../04-ship.md](../04-ship.md) rule 5). With the guesses: 0.36 < 0.42.
6. **Hits:** touching the planet is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)). The field never hits.
7. **Leaves:** once the planet is fully below the floor ([../07-drifters.md](../07-drifters.md) rule 12). Its field goes with it.
8. **Scales:** nothing. Pull, size and field never change with level. A faster scroll only brings it sooner.
9. **Placing:** its x, and y if it should start somewhere else. No look field: the look is random (`look_pick`).
10. **Looks and sounds:** placeholder until the art is drawn. Every skin fills the hitbox circle exactly. The field rings are looks only. Sound: none yet.
11. **wave_check notes:** the bot's physics includes the pull. Gaps next to a planet are measured from its body, not its field.

## Edge cases
- The planet hit the ship and the pull holds it inside: no hit until its re-hit cooldown ends ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 1.5). The pull never beats thrust (rule 5), so the player can fly out in time.
- The ship waits to respawn inside a field: no pull until the respawn completes, then the pull starts with gravity.
- A planet sits on the fall respawn point: invulnerability protects the ship; if it still touches the planet when invulnerability ends, it's a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 2.7).
- Two fields overlap: both pull; the ship feels the sum.
- A planet overlaps an island or another drifter: nothing happens ([../07-drifters.md](../07-drifters.md) rule 15).

## Open
- None.

## How to extend
A new skin is a new entry in `looks`, with the same size and hitbox. A new size or pull is a new variant. A pull that pulses, pushes or acts on other drifters is a new behavior, so a new drifter.
