# Open questions
Every value or behavior the GDD still lacks. Anyone who hits one of these stops and asks the Director. Never fill the gap yourself.

When the Director answers a question: write the answer into the file named, remove its ID from that file's `## Open`, and delete the row here. Log real changes of mind in [91-decision-log.md](91-decision-log.md). IDs are never reused.

Status: `open`, or `blocking` (stops other work now).

## Flow
None open.

## World and camera
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| WC-07 | Is the whole 640×480 window the play area, with HUD and warnings drawn on top? Or is part of it a HUD strip (top) or warning margins (sides)? If so, how big? | 03-world-and-camera.md, 10-ui.md | Walls, top line, wave coordinates, HUD | open |

## Ship
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| SH-02 | Slider min and max for gravity, the three thrusts, drag_x, fall_cap and scroll_base. | 04-ship.md, 03-world-and-camera.md | Tuning tool | open |
| SH-04 | Keep the ship at 32×32 px? | 04-ship.md | Art, wave_check gaps | open |
| SH-05 | Confirm: no vertical drag and no cap on upward speed. | 04-ship.md | Physics | open |
| SH-06 | Ship look, what `look_reference` leaves open. (1) Do the neon lines glow a little, tight to the lines, or stay bright with no halo? (2) Does the flame show only while thrusting, and in the direction of each held arrow key? (3) Does the ship tilt when moving sideways (look only)? | 04-ship.md | Ship art | open |

## Lives and damage
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| LD-04 | Blink speed while invulnerable. | 05-lives-and-damage.md | UI | open |
| LD-08 | Life-lost feedback look: flash color and length, how the HUD life breaks, particle count, how long burst and rebuild take (rebuild must end within 30 ticks). Add screen shake too? | 05-lives-and-damage.md, 10-ui.md | UI, art | open |

## Scoring
None open.

## Drifters, one per spec
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| OBJ-09 | Carnivore plant: size, hitbox, speed, telegraph. (1) Trigger range: how near is 'near'? (2) Charge time (the telegraph) and how it looks. (3) Lunge direction: straight out from the wall, or aimed at where the ship was? (4) Does it retract and lunge again? Cooldown? | drifters/09-carnivore-plant.md | Priority 4 drifter | open |
| OBJ-11 | Lava walls: width, hitbox, telegraph. (1) Both walls at once, or one side at a time? The whole screen height? (2) What is random, and in what range: start time, time on, time off, how many times it comes back, chance to stay on the whole wave? (3) Is the range set in each wave file, or one range for all waves? (4) Same random result every time a wave plays (seeded), or new each time? (5) The warning before lava turns on: how it looks and how long. Does it also warn before turning off? (6) Is the wall still solid while it's lava? (7) Does lava take width away from play? | drifters/11-lava-walls.md | Priority 3 drifter | open |

## Difficulty
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| DF-01 | Which drifters are in Tier 1, Tier 2 and Tier 3? | 08-difficulty.md | Waves | open |
| DF-02 | Base rest gap between waves at Level 1, in ticks. 0 for now (guess). | 08-difficulty.md, 09-waves.md | Waves | open |
| DF-06 | Each level's playlist: which fixed waves, in what order, and `random_count`. | 08-difficulty.md, 09-waves.md | Wave content | open |

## Waves
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| WV-03 | How many waves for the MVP? | 09-waves.md | Wave work | open |
| WV-05 | Wave 0: how many meteorites, where, and how long it lasts. | 09-waves.md | Wave 0 | open |

## UI
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| UI-01 | HUD text size, colors, margins and max score digits. The font is set (`ui_font`). | 10-ui.md | HUD | open |
| UI-03 | Instructions page: exact text, the icon for each section, and layout. Content and font are set in 10-ui.md. | 10-ui.md | Instructions | open |
| UI-04 | Look of the menu, leaderboard, pause box and game-over screen, letter picker included: layout and colors. Content and font are set in 10-ui.md. | 10-ui.md | Screens look | open |

## Save data
None open.

## Art and audio
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| AA-02 | Background numbers (guesses set, 2026-10-29; the near layer has none): how fast the middle and near layers scroll, how many river lights at most, the swirl loop length, how strong the bottom glow is. The design is set in 12-art-and-audio.md. Measure the frame rate in a browser build first. | 12-art-and-audio.md | Background | open |
| AA-03 | Which sounds and music, and is audio in the MVP? | 12-art-and-audio.md | Audio | open |
| AA-04 | Particle cap. | 12-art-and-audio.md | Effects | open |

## Scope
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| SS-01 | What is the week 2 "hallway test"? | 13-scope-and-schedule.md | Week 2 plan | open |
