Verdict: ship
Created by: scope-guardian
Feature: DRA-47 Chain lightning
Parent: none

## Request
"hey i want to go with chain-lighning drifter - is there anything to be clarified for it? Im gonna leave and I would like to leave everything working"

## Feature
A chain lightning falls straight down from the top. It is one drifter made of 2 or 3 cyan nodes in one of 7 set layouts, 128 px apart. `invert` mirrors the layout. Its entry warning shows first, always with the triangle icon, at the x of the node nearest the ship, against the top edge.

It charges the moment it appears: small blue rays grow around each node, more of them and faster as the charge fills. Then lightning fires between neighbouring nodes for 2 s, then it charges again, until every node is below the floor. Touching a firing arc, or a node while one of its arcs fires, is a hit. Nothing hurts while it charges. An arc fires only while both its nodes are on screen.

After it takes a life, the whole chain dims for the re-hit cooldown, as every hazard does.

In debug mode, the test spawn list can place chain lightnings and play only them.

## Limits
In:
- Chain lightning as in 03-chain-lightning.md: 7 variants, default `pair_flat`, `invert`, the charge and fire cycle, hits, leaving, level scaling (speed × hazard speed; charge × Timer ×, never below `telegraph_min`; fire never scales).
- Entry warning in the shared look with the `trio_triangle` icon, at the nearest node's x.
- The line hitbox shape with round ends (07-drifters.md rule 8), and its collision tests in the DRA-39 structure: every pair of shape kinds, both ways round, and the ship against every chain lightning variant, firing and charging.
- Re-hit cooldown and dim for the whole chain (05-lives-and-damage.md rule 1.5).
- Placeholder look only: cyan nodes, 1 px charge rays, a straight arc band `arc_width` thick.
- Every value in the tuning file, never hard-coded.
- Debug spawn list: chain lightning rows (type, x, optional variant, `invert`, speed) and a chain lightning only mode. Example rows for every variant.

Out:
- Graze scoring. No score exists yet.
- The jagged arc, sprite art, sound.
- The polygon shape. It comes with floating islands.
- The electric ball. Its own feature.
- Waves and wave_check, including rule 10's wave_check notes. wave_check doesn't exist yet.
- Ship-relative placement (Director's to-do list).

## Player sees
In debug mode, with the list set to chain lightning only: a triangle warning at the top, then cyan nodes falling with blue rays growing, then a white-blue band between the nodes for 2 s that costs a life on touch.

## Fit
- Pillar 1, Master the drift: fits. Timed gaps reward reading the cycle and drifting through between strikes. Source: 01-vision.md, Pillars.
- Pillar 2, See it before it hits you: fits by Director decision. The charge shows when; the nodes show where. The guardian's earlier objection was overruled and logged. Not reopened. Source: 91-decision-log.md row 48.
- Pillar 3, Risk brings reward: not touched in this feature. Graze while firing is in the GDD but scoring is out. Source: 06-scoring.md.
- Locked decision 6, hazards defined by archetype: fits. Telegraphed link; variants change layout only. Source: 07-drifters.md rule 10.
- Out-of-scope list: not touched. Source: 01-vision.md, Out of scope.
- Overlap with shipped features: builds on DRA-29 (drifter base) and DRA-39 (re-hit cooldown, debug spawn list, collision test structure). DRA-39 passed integration but is not closed out yet.

## Values needed
From the GDD (03-chain-lightning.md, all guess unless noted):
- archetype, enters_from, kind, cycle, telegraph, entry_warning_icon, specialty, graze: locked.
- 7 variants and their `invert`, default `pair_flat`.
- node_spacing 128 px, node_size 12 px circle, arc_width 6 px.
- speed_ratio 0.375, speed ≈ 2.5 px/tick at Level 1.
- charge_ticks 120, fire_ticks 120.
- placeholder_look: nodes (0, 220, 255), rays (120, 200, 255) 1 px, arc band (220, 240, 255).
- entry_warning_ticks 60 and the shared warning look. 07-drifters.md.
- telegraph_min 45 ticks (locked). 07-drifters.md.
- rehit_cooldown 180 ticks, rehit_dim 0.75. 05-lives-and-damage.md.
- Hazard speed and Timer × per level. 08-difficulty.md.

Approved by the Director in chat, now in the GDD (03-chain-lightning.md, 91-decision-log.md row 62):
- `charge_rays`: one ray per node when the charge starts, one more every quarter of the charge (30 ticks at Level 1), 4 at most. Director's value ("1 every 0.5s").
- `ray_length`: 6 px out from the node's edge, one per diagonal. Proposed by guardian, approved by Director in chat ("Propose the px of the ray and I accept your value").
- `entry_warning_size`: measured on the `trio_triangle` layout for every variant. Director accepted the recommendation.
- Warning x tie: the leftmost of the equally near nodes. Director accepted the proposal.

## Objections
None. The spec has every behavior, and the Pillar 2 debate was settled in row 48. The questions below are gaps, not conflicts.

## Decision log
- Feature shaped from 03-chain-lightning.md and decision log rows 47, 48 and 60. Linear issue DRA-47 created in Backlog.
- Director answered the four questions: rays one every 0.5 s (4 just before firing), ray length left to the guardian (6 px), warning sized from the triangle, leftmost node on a tie.
- The ray interval is a quarter of the charge, so the charge always ends with 4 rays, also at higher levels where Timer × shortens it. At Level 1 that is the Director's 0.5 s.
- Director: proceed with DRA-39 still open (not closed out). DRA-47 builds on the DRA-39 code on this branch.
- Director approved the final feature in chat: "SHIP IT!" Run the whole pipeline while the Director is away; note any issue and keep going.
