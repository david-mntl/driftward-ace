# Driftward Ace

Endless arcade dodger, no weapons. Single-player, desktop web browser. Python + pygame-ce, packaged with pygbag.

Gravity always pulls the ship down. Arrow keys add thrust. The player survives by mastering momentum and drift. There are no weapons. It is pure movement skill.

The Director (the human) makes every final call. 11 agents build the game. A Trainer writes and revises their definitions. Who owns what, and how work moves between agents, is in `docs/crew/roster.md`.

## Where details live

This file holds only what every agent needs on every task. Numbers, schemas, object behavior, level tables and scoring live in the GDD, in `docs/design/gdd/`.

- Check the GDD before using any number, schema, or object behavior.
- If the GDD doesn't answer it, ask the Director. Do not guess a value.
- If the GDD contradicts this file, stop and flag it. Do not pick a side.

## Design pillars

Every decision gets checked against these three.

1. **Master the drift.** Momentum control and fast reflexes are the core skills. Rules out: weapons, instant stop, set-speed control.
2. **See it before it hits you.** Every hazard warns before it strikes, even side entries. Deaths must feel fair. Rules out: instant hits, spawns on top of the ship.
3. **Risk brings reward.** The best points sit next to danger. Rules out: free safe pickups, score for hiding.

## Locked decisions (do not reopen)

- Controls are arrow keys only.
- The camera follows the ship up and never down. It also rises on its own, so the floor below the player keeps rising. Falling off the floor costs a life.
- Side walls are solid. They stop the ship with no bounce.
- Every game rule runs on a fixed 60 Hz tick. Gravity is always on. Horizontal velocity has drag. Fall speed is capped.
- The ship has 3 lives. A hit or a fall costs one, then brief invulnerability. A hit also stuns.
- Waves are hand-authored JSON. Every run opens with the same fixed meteorites-only Wave 0.
- A control card shows after click-to-start.
- Saves go to browser localStorage: nickname, score and level reached. Nothing else.
- Hazards are defined by behavior archetype, not by visual skin.
- Out of scope: combat, online leaderboard, mobile or touch controls, multiplayer, procedural levels, wave editor.

## Tech rules (hard constraints)

- Use **pygame-ce**. Never classic pygame.
- Package with **pygbag** at the pinned version. Do not upgrade it. Build with `pygbag --archive game` to get a static `web.zip`.
- The game must run in the browser. The main loop must be `async` and yield every frame with `await asyncio.sleep(0)`. No blocking calls, no threads.
- Audio is **.ogg only**. MP3 and WAV break the pygbag build.
- pygbag's click-to-start screen unlocks browser audio. Do not build a custom one.
- Hosting is static only (itch.io or GitHub Pages). No server code, no paid services.
- Test every build in a real browser. A desktop run does not count.

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
