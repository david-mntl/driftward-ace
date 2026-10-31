# Art style and the UI art pipeline

Status: approved by the Director, 2026-10-25. Steps 1–4 done, 2026-10-26. **Next: Step 5, run by the Director.**

## Done in Steps 1–4 (2026-10-26)
- **Step 1.** GDD 12 holds the world brief (new "You" wording, approved), color language, art style, glow, motion and background; no split needed (78 lines). GDD 10: Exo 2, flat UI, hearts, voice, menu hint. GDD 04: ship `look_reference`. Meteorite `looks` and `look_pick`. Electric ball and chain lightning in pale white-cyan. AA-01 and UI-02 closed; AA-02 narrowed to the background numbers; SH-06, UI-01, UI-03 and UI-04 narrowed. Decision log rows 94–102. Sprite finish "smooth" taken as confirmed by the start.
- **Step 2.** Roster row 13 (UI Art Critic), row 9 trigger, the UI art loop lane, the `staging/art-inbox/` rule.
- **Step 3.** `ui-art-critic` created; `art-audio-engineer` revised (Convert, Refine, loop rounds, sources, PixelLab removed).
- **Step 4.** `/ui-art-loop <asset> <sprite|screen|background> <brief>`.
- **Decided in chat.** The Critic judges every kind the art agent sends: sprite, screen, background. Rubric: five criteria per kind, general wording tied to the GDD, Size first with priority (full text in the Critic's definition). Stop rule: average ≥ 8, no criterion under 6, Size ≥ 8; else refine; at most 3 rounds. Pillow and numpy are pinned in `tools/art/requirements.txt` for the dev container only; they never ship.
- **Left for Step 8.** The HUD contract and `game/ui/hud.py` still call UI-02 TBD. They change through the Architect.
Order: Steps 1–7 first. The Scope Guardian (Step 8, and the side panel) waits until the Critic, the art agent's new modes and the loop skill exist and the style is fully defined.
Covers: the game's art style (AA-01, AA-02), the UI Art Critic, the art agent's new modes, the `/ui-art-loop` skill, and the first runs.

## Decisions already made

### World brief (approved, v2)
The player never reads this. It gives the art a feeling to aim at.

> **The collapse.** Two galaxies fell into each other. Dark matter that no one could see or measure fed the collapse. What was left is the largest black hole that has ever existed. It sits far away, in a bottom corner of everything, and it is still eating.
>
> **The anomaly.** The collapse didn't follow physics. It broke it. A wave of magnetism tore loose and now bounces through space with no source, no pattern and no reason. It hits one rock and skips the next. It turns a planet inside out and leaves its moon alone. Nobody can measure it, predict it or explain it. It just happens.
>
> **What it does.** Stars die and are dragged in, still burning. Planets crack into floating islands. Living things mutate into shapes that shouldn't be possible. Metal ships and satellites drift dead, or worse, half alive. Every object the anomaly touches carries its mark: a fuchsia shimmer along its edge, brightest on the side facing the black hole.
>
> **The pull.** Everything moves one way. Rocks, wrecks, planets, auroras, whole galaxies stream in long curved rivers toward the corner where the black hole waits. Up close the pull just feels like down. You feel it as gravity.
>
> **The light.** Light bends here. It reflects and splits, so everything looks glossy and wet. Highlights are hard and white, rims glow fuchsia, and shadows go deep navy, almost black. Colors are more vivid than they should be.
>
> **The new universe.** Some of the anomaly condenses into small crystals with a galaxy turning inside. They are pure fuchsia and purple, the brightest thing on screen. Maybe they are seeds of something new. Collecting them is the only hopeful thing you can do.
>
> **You.** You were on a reconnaissance mission, sent to find out why your planet's physics had turned strange. Then the galaxies collapsed. Your ship came through untouched: no shimmer, no mutation, clean white with an orange flame. No one knows why. Maybe you are the last one left.
>
> **Mood.** Beautiful and doomed. A storm you can't fight, only fly through. Lonely, never horror. The anomaly isn't evil. It isn't anything. It just doesn't make sense.

Note: the "You" paragraph says "clean white with an orange flame", which no longer matches the ship (see Ship). Proposed new wording, for the Director to approve in Step 1: "Your ship came through untouched: no shimmer, no mutation. Pale plating, deep blue lines, a blue flame. No one knows why. Maybe you are the last one left."

### Color language
| Color | Means | Used on |
|---|---|---|
| Navy to near-black | empty space | the deepest background |
| Fuchsia + purple | magnetism, the anomaly | coins at full brightness, dim auroras, the rim light on touched objects |
| Orange / yellow | heat, danger | meteorite tails, lava, fireball, entry warnings |
| Pale white-cyan | electricity | chain lightning, electric ball: a pale white-cyan core with thin purple and fuchsia arcs. Kept away from the ship's blue |
| Deep cobalt blue + pale plating | you, untouched | the ship and the cockpit panel frame: cobalt neon lines, a blue flame, silver-grey and pale plating |

Rules:
- A solid, bright fuchsia shape always means a coin. Hazards may carry fuchsia only as thin accents.
- The background is always dimmer and less saturated than anything the player can touch.
- Every touched object gets a thin fuchsia rim light on the side facing the black hole (the bottom).

### UI pick (from the style lab)
- Base: Neon drift. Font: Exo 2. Pixel size: ×1.
- Glow: hazards, warnings and coins only. The ship and HUD stay flat.
- Lives: hearts (closes UI-02).
- Voice: terse arcade. Exception: the menu hint is plain talk: "Up & Down to choose. Enter to start."
- Locked words stay: PAUSE, RETRY, NEW BEST SCORE, TOP 3, TOP 10, GAME OVER.
- Style lab, for reference: https://claude.ai/artifact/JhZfr9PaVRUDBsvFNzCnA6

### Sprites
- Finish: smooth. Drawn at 4× with gradients and glossy rims, then shrunk. (Recommended. The Director confirms with the plan's start.)
- Movement is visual only. 2 or 3 states per object, frames rendered ahead of time. Examples: meteorite rotation loop (8–12 frames), planet surface turning, coin swirl and glint, electric ball idle / charge / fire, ship idle / thrust flicker / blink.
- Hitboxes never rotate or change with the look.
- Meteorites use a fixed pool of looks, one picked at random on each spawn. Not new art every run.

### Background
- Painted images, made once and loaded by the game. Never drawn shape by shape per frame.
- Far layer: one large still painting. Rivers of stars, gas and debris curve toward a dim, distant black hole at the **bottom left**, mostly off screen.
- The rivers look like they flow: small glowing specks and streaks travel along the curves into the black hole (capped count). A small swirl animation loops around the black hole.
- Middle layer: dark outlines of broken planets, scrolling straight down, slowly.
- Near layer: a few dust streaks, scrolling straight down, faster.
- A faint fuchsia glow along the bottom edge: where the pull comes from, and where falling costs a life.
- It must stay dim. Hazards falling over the black hole corner stay easy to see.

### How the art gets made
- **A. Script (the base).** The art agent writes Python (Pillow or pygame-ce) that draws the sprite. Settings and a random seed give variety. This step keeps every sprite in one world: same palette, rim light, glow and frame layout.
- **B. Photo to sprite.** A public-domain photo (NASA, for example) is cut out, shrunk, fitted to the palette, given the rim light and turned into frames by a script.
- **C. Director's AI images to sprite.** The Director makes images in a tool of their choice and drops them in an inbox folder. The art agent converts them like B. Each tool's license terms are checked and credited.
- **D. CC0 packs:** not used for this world. Too generic.

### Mood references
Kept on the Director's machine in `local/mood-refs/` (gitignored), never committed and not part of the GDD (decided 2026-10-26: the GDD defines the style in words only; outside images bring copyright risk and unknown sources). Inspiration for the Director only; agents don't read them.
| File | Shows | Source |
|---|---|---|
| 01-star-torn-into-river.png | a star torn into a cyan river curling into a bright point | unknown |
| 02-black-hole-disk-and-jet.png | a pink and purple disk swirling into a black hole, with a cyan jet | unknown |
| 03-black-hole-magnetic-cracks.png | a black hole ring with fuchsia and orange cracks of energy | unknown |
| 04-galaxy-river-arms.png | a galaxy with orange outer arms and a cyan core: the "rivers" look for the far layer | NASA: https://www.nasa.gov/general/nasa-images-help-explain-eating-habits-of-massive-black-hole/ |
| 05-cockpit-console-frame.png | the bottom console of an RTS game's HUD: the frame idea for the side panel (see Open) | StarCraft (Blizzard), screenshot. Copyrighted: the idea only, never copied |
| 06-ship-hull-plating.png | a pale, curved alien hull with gold-white plating, round glowing ports and a green-cyan energy shell | StarCraft (Blizzard), Protoss ship. Idea only |
| 07-ship-blue-neon-lights.png | a ship with layered metal fins and bright blue neon lights set into the hull, a blue energy beam | StarCraft (Blizzard), Protoss ship. Idea only |
| 08-ship-form-favorite.png | **the Director's favorite form**: a sharp, swept ship built from long blade-like wings, deep blue panels with glowing cyan-blue lines, silver-grey edges, blue engine glow | StarCraft (Blizzard), Protoss ship. Idea only, adapted to this game |

Ref 04 is a NASA image. NASA images are generally free to use. If it's ever converted (method B), it's treated like any public-domain photo: fetched from its page, credit line confirmed, written in CREDITS.

### Ship (direction from the Director, 2026-10-25, not final)
The ship has never had a defined look (SH-06 is open). Direction so far:
- **Form:** adapted from ref 08. Sharp, swept, built from long blade-like wings, alien and elegant rather than a plain rocket. It points up and never rotates (`04-ship.md` rule 8).
- **Colors:** a blue engine flame instead of orange. Blue neon lines run around the hull. Silver-grey and pale plating between them.
- **Family:** the ship and the cockpit panel share one look: same plating, same neon lines. The panel is the inside of this ship.
- **Replaces** the GDD's current `look_reference` "Small rocket with an orange flame" (`04-ship.md`), once written into the GDD.

Points to settle before drawing it:
1. **Blue ship vs electricity. Decided (Director, 2026-10-26):** the ship takes a deep, saturated cobalt blue. Electricity moves to pale white-cyan with thin purple and fuchsia arcs, away from the ship's blue. The squint test confirms it once the ship is drawn. Gain: with a blue flame, orange means only heat and danger.
2. **Glow rule.** The UI pick says the ship doesn't glow. Neon lines suggest glow. Allow a small, tight glow on the ship's lines only, or keep them bright but without a halo.
3. **Form vs hitbox.** The hitbox is an inverted T, 32 × 32 (`04-ship.md`). The ref 08 form fits it: the body as the bar, the swept wings as the foot. Blade tips may reach past the hitbox (allowed: the hitbox is never bigger than the sprite, and smaller is forgiving). If the form needs more room, `ship_w` and `ship_h` (both `guess`) can change, through the GDD.
4. **SH-06 questions.** Does the flame show only while thrusting, and in the direction of each held arrow? Does the ship tilt when moving sideways (look only)? A blue flame for each direction is one way.
5. **Lore.** The ship is "untouched": no fuchsia on it. Its blue is its own technology, the one light the anomaly didn't bend.

## Steps

One phase per session. `/clear` between steps. Commits go on the branch the Director has checked out.

### Step 1. Write the style into the GDD (main session)
- `12-art-and-audio.md`, all as `guess`:
  - the world brief
  - the color language and its rules
  - the sprite finish and the movement rule
  - the background design
  - ~~a link to `art-refs/` and its table~~ dropped 2026-10-26: the style lives in words only
  - Not the art-making method: the GDD never names tools or roles. The method goes into the art agent's definition in Step 3.
  - If GDD 12 would pass about 150 lines, propose a split (for example, the world brief in its own numbered file) and update `00-index.md`. Ask the Director first.
- `10-ui.md`:
  - lives as hearts (UI-02)
  - the font and glow rule for the HUD
  - the voice rule, with the plain-talk menu hint
- Drifter specs:
  - electric ball and chain lightning `look_reference`: a pale white-cyan core with thin purple and fuchsia arcs
- `04-ship.md`: replace `look_reference` with the ship direction (form from ref 08, cobalt neon lines, blue flame, pale plating). SH-06 stays open for the points still listed under Ship.
- The world brief's "You" paragraph: the new wording, once the Director approves it.
  - meteorite: a `looks` pool picked at random, like the planet's `looks` and `look_pick`
- Close AA-01. Close or narrow AA-02. One row per decision in `91-decision-log.md`.

### Step 2. Roster change (Director)
- Add the **UI Art Critic** row: Evaluator, read-only, writes `docs/reports/ui-art/`.
- Report names: `docs/reports/ui-art/<asset>-r<round>.md`, so the loop skill can find each round.
- Art agent row: add an inbox folder for the Director's images, for example `staging/art-inbox/`.

### Step 3. Trainer
- **Create the UI Art Critic.**
  - It looks at a rendered image and scores it 0–10 against GDD 12: world, colors, rim light, readability, finish.
  - It gives one reason per criterion. No pass or fail.
- **Revise the art agent:**
  - **Refine mode:** takes a Critic report and fixes what it names.
  - **Convert mode:** turns a photo or AI image into a game sprite: cut out, shrink, palette, rim light, frames.
  - **Source rules:** public-domain photos and Director images allowed, each with a CREDITS line. Mood references are never shipped.
  - **PixelLab removed** from its tools.
  - **The art-making method** from "How the art gets made" above: script as the base, fed by photos and Director images. Smooth finish, drawn at 4× and shrunk. Animation frames rendered ahead of time.

### Step 4. The `/ui-art-loop` skill (main session)
- Runs generate, critique, refine, and repeats.
- Stops at a score of 8 or more, or after 3 rounds.
- Keeps each round's image and Critic report so the Director can compare before and after.
- No input from the Director during the run.

### Step 5. First run: the meteorite test
- One meteorite, three ways, each through `/ui-art-loop`:
  - **A:** pure script
  - **B:** a public-domain asteroid photo, converted
  - **C:** one AI image from the Director, converted
- Output: a side-by-side sheet with each round's before and after, plus the rotation frames.
- The Director picks the method. That settles how the art gets made.

### Step 6. Homework demos
- Three UI demos, each with flaws seeded on purpose. Each demo says so.
  - **Color and font:** the HUD
  - **Style and voice:** the game-over screen
  - **Layout and length:** the instructions page

### Step 7. Background test
- The far painting with the bottom-left black hole, the flowing river light and the bottom glow.
- Measure the frame rate in a real browser build before it counts.

### Step 8. The real feature, through the Scope Guardian
- Load sprites and backgrounds into the game, the meteorite looks pool, and the background layers.
- The Architect settles who loads images. Today the UI developer never loads them: an open ownership gap.

## Open, not decided
- **Side panel HUD.** Move the score, best, lives, level and grazes into a panel to the right of the play area. Raised by the Director on 2026-10-25. It changes locked HUD positions in `10-ui.md`, so it goes through the Scope Guardian. Scoping waits until Steps 1–7 are done. The Step 6 HUD demo is a picture, not game code, so it may show the panel as a mockup without scoping it first.
  - **Size.** The play area stays 640 × 480, with the panel about 214 px wide to its right. The whole window is 854 × 480, the shape of a widescreen monitor. The panel's left edge is the visible right wall.
  - **Look: the inside of the ship.** The play area is the cockpit window and the panel is the ship's console. The idea comes from ref 05: a heavy metal frame with curved, beveled trim and rivets, dark glass screens set into it, small glowing readouts and labelled slots.
  - **In this world's colors, not the reference's.** The console is the inside of the ship (see Ship), so the frame uses the ship's look: pale plating with the same blue neon lines, and dark navy glass screens.
  - **Readouts in fuchsia and cyan (the Director's call, 2026-10-25).** One way to fit the lore: the instruments measure the anomaly, so the readouts glow its colors, while the frame itself stays the untouched ship's blue. The coin count may show a fuchsia crystal icon, like cargo in a sealed case.
  - **Calm.** Darker and lower in contrast than the play area. Nothing moves in it except values changing. The eye belongs in the play area.
  - **Stays in the play area:** score popups, the graze ring, warnings, the invulnerability blink, and the main life-lost feedback on the ship (LD-08).
  - **Screens (the Director's call, 2026-10-25):** the pause box and the game-over screen are centered on the whole window, over both the play area and the panel, and both are dimmed. The menu fills the whole window, with no panel. Moving from the menu into a run should feel smooth.
  - **Instructions and leaderboard** fill the whole window, like the menu (the Director's call, 2026-10-25).
  - **Still to decide:** whether name entry fills the window or centers like the pause box (suggested: center, since it follows game over). What the move into a run looks like, and that it never delays control.
