# Driftward Ace

Endless arcade dodger, no weapons. Single-player, desktop web browser. Python + pygame-ce, packaged with pygbag.

Gravity always pulls the ship down. Arrow keys add thrust. The player survives by mastering momentum and drift. There are no weapons. It is pure movement skill.

The Director (the human) makes every final call. A crew of AI agents builds the game. A Trainer writes and revises their definitions. Who owns what, and how work moves between agents, is in `docs/crew/roster.md`.

## Where details live

The GDD in `docs/design/gdd/` is the only source of truth for the game. This file holds only what every agent needs on every task, and points into the GDD for the rest.

- Start at `docs/design/gdd/00-index.md`. Open only the file its routing table names.
- Check the GDD before using any number, schema, or object behavior.
- A value marked `guess` may be used; say so in your report. A value marked `TBD` is missing: ask the Director. Never fill it in.
- If the GDD doesn't answer it, ask the Director. Do not guess a value.
- If the GDD contradicts this file, the GDD wins. Stop and flag it anyway.

## Design pillars

Every decision gets checked against the three pillars: **Master the drift**, **See it before it hits you**, **Risk brings reward**. What each one means and rules out is in `docs/design/gdd/01-vision.md`, section Pillars. Read it before any design, scope or review call.

## Locked decisions and out of scope

Listed in `docs/design/gdd/01-vision.md`, sections Locked decisions and Out of scope. Do not reopen them.

## Tech rules

Hard constraints (engine, pygbag build, async loop, audio format, hosting, browser testing) are in `docs/design/gdd/15-tech-constraints.md`. Read it before writing or building any game code.

## Rules for every agent

- **Stay in your lane.** Do your assigned task and nothing else. Write only to the paths the roster gives you. No refactors, extra features or "while I'm here" fixes.
- **Hand off through files.** Your output is a file in the repo, and it moves along the lane in the roster.
- **New ideas go to the Scope Guardian.** Nothing gets built without its approval.
- **No silent schema drift.** The Architect owns every schema. If you produce or change any data file (wave JSON, config, save data), follow its schema exactly. Never add, rename or drop a field on your own. If the schema doesn't fit, stop and report. The change then goes through the structural lane.
- **Leave a result the Director can check.** If you write code or game content, it must be something the Director can run, see or play, not just code that exists.
- **Validate before handoff.** Waves must pass `wave_check` before they count as done.
- **Report what you did, plainly.** Say what changed, what you didn't touch, and what you're unsure about. Don't present a guess as a fact.
- **Ask before irreversible changes.** Deleting files and changing locked decisions need the Director's explicit go-ahead.

## Writing style

Docs and in-game text read in a direct, human voice. Short sentences. No filler, no hype, no AI-sounding phrasing.
