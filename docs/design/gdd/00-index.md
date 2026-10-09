# Driftward Ace GDD: Index

The source of truth for every number, behavior and rule in the game. Only the Director edits this folder.

## How to read this GDD
1. Find your question in **Routing** below.
2. Open only that file. Don't read the whole folder.
3. Values sit under `## Values` in every file. Rules sit under `## Rules`.
4. If the value is `TBD`, it is missing. Ask the Director. Never fill it in.
5. If two files disagree, stop and flag it. Don't pick a side.

Not in this GDD:
- Who builds the game and how the work flows. The GDD describes the game only.
- Exact data schemas (wave JSON, tuning file, save data): technical specs, not design.

## Value status
| Status | Meaning | Can it be used? |
|---|---|---|
| locked | Final. Changing it needs the Director. | Yes |
| tuned | Set in a tuning session and copied back here. | Yes |
| guess | A starting value. Expect it to change after playtesting. | Yes. Say in your report that it's a guess. |
| TBD | Missing. Listed in [90-open-questions.md](90-open-questions.md). | No. Ask the Director. |

File status: `draft` (being written), `review` (Director checking), `locked` (done), `stretch` (only if time allows).

## Routing
| Need to know | Read |
|---|---|
| What the game is, pillars, locked decisions, out of scope, win and lose | [01-vision.md](01-vision.md) |
| Screens and states: start, control card, play, game over, retry | [02-game-flow.md](02-game-flow.md) |
| Screen size, coordinates, meters, camera, top line, rising floor, walls | [03-world-and-camera.md](03-world-and-camera.md) |
| Ship size, hitbox, gravity, thrust, drag, fall cap, tick order | [04-ship.md](04-ship.md) |
| Lives, hits, falls, invulnerability, life-lost feedback, respawn | [05-lives-and-damage.md](05-lives-and-damage.md) |
| Score, meters, coins, graze | [06-scoring.md](06-scoring.md) |
| Which objects exist, their priority, rules shared by all hazards | [07-objects.md](07-objects.md) |
| How one object behaves | the file [07-objects.md](07-objects.md) routes to, in `objects/` |
| Levels, speed multipliers, rest gap, tier unlocks | [08-difficulty.md](08-difficulty.md) |
| Waves, Wave 0, wave order, wave_check rules | [09-waves.md](09-waves.md) |
| HUD, control card, game over screen | [10-ui.md](10-ui.md) |
| Saves, nickname, top 10 (stretch) | [11-save-data.md](11-save-data.md) |
| Art style, palette, sprite sizes, sound | [12-art-and-audio.md](12-art-and-audio.md) |
| Schedule, priorities, cut order, stretch goals | [13-scope-and-schedule.md](13-scope-and-schedule.md) |
| What a term means | [14-glossary.md](14-glossary.md) |
| Engine, browser build, audio format, hosting | [15-tech-constraints.md](15-tech-constraints.md) |
| What is still missing | [90-open-questions.md](90-open-questions.md) |
| Why something was decided | [91-decision-log.md](91-decision-log.md) |

## File status
| File | Status |
|---|---|
| 01-vision.md | draft |
| 02-game-flow.md | draft |
| 03-world-and-camera.md | draft |
| 04-ship.md | draft |
| 05-lives-and-damage.md | draft |
| 06-scoring.md | draft |
| 07-objects.md | draft |
| 08-difficulty.md | draft |
| 09-waves.md | draft |
| 10-ui.md | draft |
| 11-save-data.md | stretch |
| 12-art-and-audio.md | draft |
| 13-scope-and-schedule.md | draft |
| 14-glossary.md | draft |
| 15-tech-constraints.md | locked |

## Rules for writing this GDD
- **One fact, one home.** A value lives in one file only. Other files link to it, like `04-ship.md#values`, and never copy it.
- **Stand-alone.** The GDD never depends on files outside this folder. Other project files may point into it, never the other way.
- **Same skeleton everywhere.** Every file except this index and the logs has: `Status`, `Depends on`, then `## Summary`, `## Values`, `## Rules`, `## Edge cases`, `## Open`, `## How to extend`.
- **Values table columns:** `Key | Value | Unit | Range | Status | Source`. Range is the tuning slider's min–max, or `—`.
- **Every TBD has an ID** in [90-open-questions.md](90-open-questions.md), and the file's `## Open` lists it.
- **Every change of mind** goes in [91-decision-log.md](91-decision-log.md).
- **Short files.** Keep each file under about 150 lines. When one grows past that, split it and update this index.
- **Units.** 1 tick = 1/60 s. Distances in px. Speeds in px/tick. Accelerations in px/tick². 10 px = 1 m.
- **Key names** are design names. A technical schema may map them to other names, as long as it says so.
- **Independent of the team.** Never name a team member, role, tool or repo path outside the game itself. The only role is the Director, who owns the design.

## How to extend
- **New object:** copy [objects/_template.md](objects/_template.md), fill it in, then add a row to [07-objects.md](07-objects.md).
- **New system:** add a numbered file using the skeleton above, then add a row to Routing and File status.
- **New gap found:** add a row to [90-open-questions.md](90-open-questions.md) and link its ID from the file's `## Open`.
