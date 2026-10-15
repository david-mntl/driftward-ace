# Open questions
Every value or behavior the GDD still lacks. Anyone who hits one of these stops and asks the Director. Never fill the gap yourself.

When the Director answers a question: write the answer into the file named, remove its ID from that file's `## Open`, and delete the row here. Log real changes of mind in [91-decision-log.md](91-decision-log.md). IDs are never reused.

Status: `open`, or `blocking` (stops other work now).

## Flow
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| FL-01 | Which key dismisses the control card and starts the run? Controls are arrow keys only. | 02-game-flow.md | Control card | open |
| FL-03 | Saves are deferred, so there is no best score. What does "win" look like until saves ship? | 01-vision.md, 02-game-flow.md, 06-scoring.md, 10-ui.md | Game over screen | open |
| FL-04 | Pause (week 4): which key, and does losing browser focus pause the game? | 02-game-flow.md, 13-scope-and-schedule.md | Pause card | open |

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
| SH-06 | Ship look: sprite style, colors, and animation. Does the flame show only while thrusting, and in the direction of each held arrow key? Does the ship tilt when moving sideways? | 04-ship.md | Ship art | open |

## Lives and damage
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| LD-04 | Blink speed while invulnerable. | 05-lives-and-damage.md | UI | open |
| LD-06 | What happens to the hazard that hit the ship: stays, vanishes, or passes through? If it stays and the ship is still inside it when invulnerability ends, is that a new hit? | 05-lives-and-damage.md | Hit handling | open |
| LD-07 | Fall respawn at screen center lands on a hazard. Is invulnerability enough, or must the spot be cleared? | 05-lives-and-damage.md | Falls | open |
| LD-08 | Life-lost feedback look: flash color and length, how the HUD life breaks, particle count, how long burst and rebuild take (rebuild must end within 30 ticks). Add screen shake too? | 05-lives-and-damage.md, 10-ui.md | UI, art | open |
| LD-09 | On the last life: play the feedback first, then the game-over screen? How long between them? | 05-lives-and-damage.md, 02-game-flow.md | Game over | open |

## Scoring
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| SC-02 | The ship enters a graze zone while invulnerable and leaves after it ends. Does it pay? | 06-scoring.md | Graze | open |
| SC-03 | Graze zone for line-shaped hazards (arcs). Circles and boxes are answered in 06-scoring.md rule 3. | 06-scoring.md | Graze | open |
| SC-04 | A hazard leaves the screen while the ship is still in its zone. Does it pay? | 06-scoring.md | Graze | open |
| SC-05 | Can an invulnerable ship collect coins? | 06-scoring.md | Coins | open |

## Drifters, shared
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| OB-04 | Do hazards collide with each other or with the walls? | 07-drifters.md | Every hazard | open |

## Drifters, one per spec
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| OBJ-02 | Satellite: size, hitbox, speed, telegraph. (1) Pattern shape: straight line across, back and forth, or a wave (sine)? (2) Does it leave the screen after crossing, or keep patrolling? (3) Is the pattern set per satellite in the wave file, or one fixed pattern for all? | drifters/02-satellite.md | Priority 2 drifter | open |
| OBJ-03 | Chain lightning: size, hitbox, speed, telegraph. (1) How many nodes per link (the art shows 2 and 3)? (2) Are the nodes themselves harmful, or only the arc? (3) Charge time and arc duration at Level 1. (4) Does it fire once or repeat? (5) Graze zone for a line-shaped hazard (see SC-03). | drifters/03-chain-lightning.md | Priority 2 drifter | open |
| OBJ-04 | Coin: size, pickup radius, speed. (1) Size and pickup radius. (2) Static in the world, or does it move? (3) Does it disappear if not collected (below the floor)? (4) How near danger counts as 'near' (see WV-07)? | drifters/04-coin.md | Priority 2 drifter | open |
| OBJ-05 | Floating islands: size, hitbox, speed, telegraph. (1) Touching a slab: a hit, or solid ground the ship bumps against like a wall? (2) Slab thickness. (3) Static in the world (moves down with the scroll), or does it also move on its own? (4) How does graze work for a long slab (see SC-03)? | drifters/05-floating-islands.md | Priority 2 drifter | open |
| OBJ-06 | Fireball: size, hitbox, speed, telegraph. (1) Speed at Level 1. (2) Is the angle set per fireball in the wave file, or fixed? (3) How long does its entry warning show before it enters? | drifters/06-fireball.md | Priority 2 drifter | open |
| OBJ-07 | UFO: size, hitbox, speed, telegraph. (1) What patterns can it choose from? (2) What makes it readable: a tell before each move? How long? (3) Is the beam under it a hazard (a heat zone)? (4) Random every run, or seeded so the same wave plays the same way? | drifters/07-ufo.md | Priority 3 drifter | open |
| OBJ-08 | Planet: size, hitbox, speed, telegraph. (1) Is touching the planet's body a hit? (2) Pull radius and pull strength. (3) Is the pull constant inside the radius, or stronger near the center? (4) Is the radius shown on screen (the rings)? (5) Does it move down, or stay static in the world? | drifters/08-planet.md | Priority 3 drifter | open |
| OBJ-09 | Carnivore plant: size, hitbox, speed, telegraph. (1) Trigger range: how near is 'near'? (2) Charge time (the telegraph) and how it looks. (3) Lunge direction: straight out from the wall, or aimed at where the ship was? (4) Does it retract and lunge again? Cooldown? | drifters/09-carnivore-plant.md | Priority 4 drifter | open |
| OBJ-10 | Electric ball: size, hitbox, speed, telegraph. (1) Is the ball harmful between pulses? (2) Pulse period, radius and how long a pulse lasts. (3) The warning before each pulse: how it looks, how long. (4) Float path: straight, wandering, or patrol? | drifters/10-electric-ball.md | Priority 4 drifter | open |
| OBJ-11 | Lava walls: width, hitbox, telegraph. (1) Both walls at once, or one side at a time? The whole screen height? (2) What is random, and in what range: start time, time on, time off, how many times it comes back, chance to stay on the whole wave? (3) Is the range set in each wave file, or one range for all waves? (4) Same random result every time a wave plays (seeded), or new each time? (5) The warning before lava turns on: how it looks and how long. Does it also warn before turning off? (6) Is the wall still solid while it's lava? (7) Does lava take width away from play? | drifters/11-lava-walls.md | Priority 3 drifter | open |

## Difficulty
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| DF-01 | Which drifters are in Tier 1, Tier 2 and Tier 3? | 08-difficulty.md | Waves | open |
| DF-02 | Base rest gap between waves at Level 1, in ticks. | 08-difficulty.md, 09-waves.md | Waves | open |
| DF-03 | What "Cap" means at Level 8. For example: no more levels, Level 8 values forever. | 08-difficulty.md | Levels | open |
| DF-04 | A level change during a wave: apply at once, or at the next wave? | 08-difficulty.md | Levels | open |
| DF-05 | Each level is designed one by one and sets its own start distance. Where does each of Levels 2 to 8 start? | 08-difficulty.md | Levels | open |

## Waves
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| WV-01 | After Wave 0, how is the next wave chosen: fixed order, or random from the waves the current tier allows? | 09-waves.md | Endless mode | open |
| WV-02 | After the last wave, what happens: loop, reshuffle, or something else? | 09-waves.md | Endless mode | open |
| WV-03 | How many waves for the MVP? | 09-waves.md | Wave work | open |
| WV-04 | Are wave coordinates and trigger distances relative to the wave's start, or absolute? | 09-waves.md | Wave schema | open |
| WV-05 | Wave 0: how many meteorites, where, and how long it lasts. | 09-waves.md | Wave 0 | open || WV-06 | Confirm "120 px clear seams": 120 px of empty world between the end of one wave and the start of the next? | 09-waves.md | wave_check | open |
| WV-07 | Coins: how many per wave, and how close to a hazard counts as "near"? | 09-waves.md | Wave work | open |

## UI
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| UI-01 | HUD font, size, colors, margins and max score digits. | 10-ui.md | HUD | open |
| UI-02 | Lives as icons or a number? | 10-ui.md | HUD | open |
| UI-03 | Control card: exact text and look. | 10-ui.md | Control card | open |
| UI-04 | Game-over screen: what it shows and the retry prompt. | 10-ui.md | Game over | open |

## Save data (stretch)
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| SV-01 | Nickname: max length, allowed characters, and how it's typed if controls are arrow keys only (arcade letter picker?). | 11-save-data.md | Saves | open |
| SV-02 | Top 10: tie order, and is name entry shown for a score that doesn't make the list? | 11-save-data.md | Saves | open |

## Art and audio
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| AA-01 | Art style (pixel art, vector, glow) and palette. | 12-art-and-audio.md | All art | open |
| AA-02 | Background: plain, starfield, parallax layers? | 12-art-and-audio.md | Art | open |
| AA-03 | Which sounds and music, and is audio in the MVP? | 12-art-and-audio.md | Audio | open |
| AA-04 | Particle cap. | 12-art-and-audio.md | Effects | open |

## Scope
| ID | Question | File | Blocks | Status |
|---|---|---|---|---|
| SS-01 | What is the week 2 "hallway test"? | 13-scope-and-schedule.md | Week 2 plan | open |
