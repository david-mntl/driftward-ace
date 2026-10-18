# Chain lightning
Status: draft
Depends on: [../07-drifters.md](../07-drifters.md) (shared hazard rules), [../04-ship.md](../04-ship.md) (top sideways speed), [../06-scoring.md](../06-scoring.md) (graze)

## Summary
Two or three glowing nodes fall from the top in a fixed layout. They charge with growing blue rays, then blue lightning fires from node to node, then they charge again, until they leave. Nothing hurts while it charges. While the lightning fires, the arcs and their nodes hurt. The charge shows when the strike comes. Where it lands is for the player to read from the nodes: the lightning always joins them.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| archetype | Telegraphed link | — | — | locked | Director |
| enters_from | Top, at the x the placement sets | — | — | locked | Director |
| kind | moving drifter ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9) | — | — | locked | Director |
| priority | 2 | — | — | guess | 07-drifters.md |
| variants | see the layout table below | — | — | guess | Director |
| default_variant | pair_flat | — | — | guess | Director |
| node_spacing | 128 between neighbouring nodes, center to center | px | — | guess | Director |
| node_size | 12, a circle | px | — | guess | Director |
| arc_width | 6. Each arc is a straight line from node center to node center; its length comes from the layout | px | — | guess | Director |
| hitbox | each firing arc: a line 6 px thick with round ends ([../07-drifters.md](../07-drifters.md) rule 8). Each node while one of its arcs fires: a circle as big as the node. Nothing while charging | px | — | guess | Director |
| speed_ratio | 0.375 × the ship's top sideways speed ([../04-ship.md](../04-ship.md), derived values), straight down. Its own number; it only starts equal to the meteorite's | — | — | guess | Director |
| speed | ≈ 2.5 at Level 1, from `speed_ratio` and the current ship guesses | px/tick | — | guess | derived |
| charge_ticks | 120 (2 s) | ticks | — | guess | Director |
| fire_ticks | 120 (2 s). Timer × never shortens it. A set value per level may come later | ticks | — | guess | Director |
| cycle | charge, fire, charge, fire… until it leaves. No pause besides the charge | — | — | locked | Director |
| entry_warning_ticks | the shared value ([../07-drifters.md](../07-drifters.md)) | ticks | — | — | 07-drifters.md |
| entry_warning_icon | always the `trio_triangle` layout, whatever the variant. The real layout is a surprise | — | — | locked | Director |
| entry_warning_size | the shared size rule ([../07-drifters.md](../07-drifters.md), Values): the same fixed size as every warning. The `trio_triangle` icon is scaled to fit, for every variant, so the size doesn't give the layout away | px | — | guess | Director |
| telegraph | the charge: small blue rays around each node, more of them and faster as the charge fills; at the end they become the lightning between the nodes | — | — | locked | Director |
| charge_rays | 4 per node at most. The first ray shows when the charge starts, and one more every quarter of the charge: every 30 ticks (0.5 s) at Level 1. All 4 show for the last quarter, just before it fires | rays | — | guess | Director |
| ray_length | 6, out from the node's edge, one per diagonal (45°, 135°, 225°, 315°), in that order | px | — | guess | Director (value proposed in chat) |
| specialty | none | — | — | locked | Director |
| graze | yes, only while an arc fires, and once per chain lightning | — | — | locked | Director |
| look_reference | Blue electricity, very powerful lightning: cyan glowing nodes, a jagged white-blue arc, blue rays while charging | — | — | guess | Director |
| placeholder_look | nodes: filled cyan circles (0, 220, 255), 12 px. Charge: 1 px rays (120, 200, 255), `ray_length` long, `charge_rays` of them. Arc: a band (220, 240, 255) `arc_width` thick, node to node | RGB | — | guess | Director |

**Layouts.** Arcs join neighbouring nodes along the shape: left to middle to right. The triangle also joins its two ends, so all three sides fire. `invert` (a placement field) mirrors the layout exactly.

| Variant | Nodes | Layout | Arcs | With `invert` |
|---|---|---|---|---|
| pair_flat | 2 | side by side, flat | 1 | the same |
| pair_diagonal | 2 | at 45°, the left node higher | 1 | mirrored left to right |
| pair_vertical | 2 | one above the other | 1 | the same |
| trio_line | 3 | flat, left to right | 2 | the same |
| trio_diagonal | 3 | at 45°, the left node highest | 2 | mirrored left to right |
| trio_l | 3 | top, corner, right: the letter L | 2 | mirrored left to right |
| trio_triangle | 3 | equal sides, point up | 3 | upside down, point down |

## Rules
1. **One drifter.** The nodes are parts of one chain lightning, never drifters of their own. Its position is the center of the box around all its nodes; the variant and `invert` set where each node sits around it. All nodes move together.
2. **Appears:** at its placed x, just above the top edge ([../07-drifters.md](../07-drifters.md) rule 14), then falls into view. Its entry warning shows first, in the shared look ([../07-drifters.md](../07-drifters.md), Values) with the triangle icon, at the x of the node nearest the ship when the warning starts, against the top edge. If two nodes are equally near, the leftmost one. The warning stays there.
3. **Telegraph:** the charge starts the moment it appears and lasts `charge_ticks`. It shows when the strike comes, not which nodes connect. That is part of this hazard on purpose: the player learns that the lightning always joins the nodes.
4. **Moves:** straight down at `speed` on screen, every tick. No targeting. The scroll doesn't add to it ([../03-world-and-camera.md](../03-world-and-camera.md) rule 9).
5. **Fires:** after the charge, every arc fires for `fire_ticks`, then the next charge starts. An arc fires only while both its nodes are on screen (any part visible). A node that has left takes its arcs with it; the other arcs keep working while their own nodes are on screen.
6. **Hits:** touching a firing arc, or a node while one of its arcs fires, is a hit ([../05-lives-and-damage.md](../05-lives-and-damage.md)). Nothing hits while charging.
7. **Leaves:** once every node is fully below the floor ([../07-drifters.md](../07-drifters.md) rule 12).
8. **Scales:** `speed` × the level's hazard speed; `charge_ticks` × the level's Timer ×, never below `telegraph_min` ([../08-difficulty.md](../08-difficulty.md)). `fire_ticks` never scales.
9. **Looks and sounds:** placeholder until the look is drawn. The jagged arc stays inside its `arc_width` band, so the hitbox is never bigger than what the player sees. Sound: none yet.
10. **wave_check notes:** the charge at Level 8 (120 × 0.70 = 84 ticks) must stay ≥ `telegraph_min`. Arcs count as hazards for the bot's path only while firing.

## Edge cases
- The ship touches a firing arc while invulnerable: no hit, the arc keeps firing.
- The ship is still inside the arc that hit it when invulnerability ends: no hit until its re-hit cooldown ends ([../05-lives-and-damage.md](../05-lives-and-damage.md) rule 1.5).
- A node leaves while its arc fires: that arc stops at once.
- An arc passes over a coin or another drifter: nothing happens ([../07-drifters.md](../07-drifters.md) rule 15).

## Open
- None.

## How to extend
A new layout is a new variant in the table: nodes, layout, arcs, and what `invert` does. More than three nodes, moving nodes or aiming at the ship is a new behavior, so a new drifter.
