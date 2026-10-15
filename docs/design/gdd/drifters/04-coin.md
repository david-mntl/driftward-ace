# Coin
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared drifter rules), [../06-scoring.md](../06-scoring.md), [../09-waves.md](../09-waves.md)

## Summary
A fragment of the galaxy: a tiny swirling galaxy held in a transparent crystal, with a cloud and a ring around it. Unusual and beautiful. It sits still in the world, always near danger, and pays when touched. A common one pays 50, a rare one 100 and shines more. Going for it is a risk on purpose (Pillar 3).

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Pickup | — | — | locked | Director |
| enters_from | Top: it scrolls in from just above the top edge ([../07-drifters.md](../07-drifters.md) rule 14) | — | — | locked | Director |
| kind | parked drifter: it doesn't move on its own, only with the scroll ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-drifters.md |
| variants | common 50 points, rare 100 points. Same size and hitbox; the rare one shines more | points | — | common 50: locked; rare 100: guess | Director |
| default_variant | common | — | — | guess | Director |
| crystal_size | 12 wide, 20 tall: a 12 × 10 rectangle with a 5 px tall triangle on top and one below | px | — | guess | Director (size picked by guardian on request) |
| hitbox | one box, the crystal's rectangle only: 12 × 10, centered. The triangle points, the cloud and the ring don't count, so the ship must really touch the crystal | px | — | guess | Director |
| entry_warning | none. Pickups have no entry warning ([../07-drifters.md](../07-drifters.md) rule 9) | — | — | locked | Director |
| graze | no | — | — | locked | 06-scoring.md (coins never pay) |
| popup | its points ("+50", "+100") show where it was collected, drift up slowly, and are gone after 60 ticks (1 s) | ticks | — | guess | Director |
| popup_color | (255, 80, 150) | RGB | — | guess | Director (picked by guardian on request) |
| look_reference | A tiny swirling galaxy inside a transparent crystal, with a cloud and a ring around it. A fusion of red, black and purple. The crystal stays upright; the galaxy swirls inside and the crystal glints. The rare one shines more | — | — | guess | Director |
| palette | crystal lit side (200, 30, 90) crimson; crystal shade side (70, 0, 60) black-purple; galaxy core (15, 0, 20) near black; ring and rim (255, 80, 150) bright red-pink; rare glint (255, 220, 240) | RGB | — | guess | Director (picked by guardian on request) |
| placeholder_look | the crystal shape split down the middle: left half lit side, right half shade side, with a 1 px rim. A 1 px ring, an ellipse 22 × 8, across the crystal's middle. Rare: a small glint at the upper left of the crystal. No cloud, no animation | px, RGB from `palette` | — | guess | Director (picked by guardian on request) |
| sound | a pickup sound: AA-03 | — | — | TBD | AA-03 |

## Rules
1. **Appears:** at its placed x, just above the top edge, then scrolls into view. No entry warning: it can't hurt.
2. **Telegraph:** none.
3. **Moves:** never on its own. It moves down with the scroll, like the world under it. Hazard speed and Timer × don't touch it.
4. **Collected:** when the ship's hitbox touches the coin's hitbox, the coin pays its variant's points ([../06-scoring.md](../06-scoring.md) rule 2), disappears, shows its popup and plays its sound. An invulnerable ship collects it too: the ship already paid a life. A ship in the respawn wait never collects ([../05-lives-and-damage.md](../05-lives-and-damage.md)).
5. **Leaves:** a coin not collected is removed once fully below the floor ([../07-drifters.md](../07-drifters.md) rule 12). It is lost.
6. **Scales:** nothing. Its points never change with level.
7. **Looks and sounds:** placeholder until the look is drawn. The rotation and shine are looks only; the hitbox never turns.
8. **wave_check notes:** every coin must be near a hazard ([../09-waves.md](../09-waves.md) rule 6, `coin_near_max`).

## Edge cases
- The ship touches a coin and a hazard on the same tick: the coin pays and the hit counts.
- A hazard passes over a coin: nothing happens. Drifters pass through each other ([../07-drifters.md](../07-drifters.md) rule 15).
- The ship sits in the respawn wait over a coin: no collect. The coin stays and keeps scrolling; the ship can take it once the wait ends.

## Open
- AA-03 (sound).

## How to extend
A new point value is a new variant in Values. A coin that moves, chases or vanishes on a timer is a new behavior, so a new drifter.
