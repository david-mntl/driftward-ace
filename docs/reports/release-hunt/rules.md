# Release hunt: the rules

What the adversarial test bots check before a release, and why. Written 2026-11-08 for the first full hunt. The scripts live in `tools/adversary/`. This file is the checklist; the scripts are how it runs.

## Approach in one paragraph

The game core is pure and deterministic: `step_run(run, thrust)` returns a new run and changes nothing else. That makes it ideal for automated play. Bots play the real core thousands of times faster than a human, and an independent checker (the "oracle") watches every tick for anything the GDD forbids. This is the standard toolkit from game QA and testing research: monkey testing (random input), scripted adversaries that try to break one rule, a planning bot that plays to survive, invariant checks every tick, differential testing (two ways of computing the same answer must agree), soak tests (play for a long time and watch for drift), and replay determinism (same seed and inputs give the same result). Performance is measured in two places: the desktop build with the real drawing, and the real browser build, because WebAssembly Python runs about 3 to 5 times slower.

## The bots

| Bot | What it does | What it hunts |
|---|---|---|
| idle | Presses nothing | Falls, the respawn wait, last life, game over |
| random | Holds random key combos for random lengths | Anything a careless player can trigger |
| hover | Stays mid-screen, steers off walls | Long runs, coverage of every wave |
| wall / top-line / floor huggers | Lives on one edge | Clamp bugs, edge collisions |
| island seeker | Pushes into floating islands, corners and squeezes | Stuck ship, ship pushed through walls or islands |
| hazard seeker | Flies into hazards | Missed hits, double hits |
| planner | Looks ahead with the real physics and plays to survive | Unavoidable hits (unfair waves), how far a good player gets |
| flow fuzzer | Random and scripted key presses on every screen | Crashes, softlocks, wrong screen changes |

Each bot runs immortal (lives refilled, to reach Level 8 and the endless tail) and mortal (the real flow).

## The rules (invariants)

A release needs zero violations of these. Each one cites where the GDD sets it.

### Never crash, never freeze
1. No exception in any run, on any screen, at any tick.
2. Every screen can reach the menu again with some key sequence. No softlock (02-game-flow).
3. The wave clock always moves on. No wave plays longer than its length at the slowest scroll, plus its rest, plus a margin (09-waves).
4. The respawn wait ends on the first fresh arrow press, and only then. An arrow held through the fall does not count (05 rule 2.5).

### The ship
5. The ship's numbers stay finite. It stays between the side walls and never goes above the top line (03, 04 rule 2).
6. The ship never ends a tick inside a floating island. A squeeze (island pushing it into a wall or the top line) never pushes it through anything (drifters/05).
7. The ship never sits still for 2 s while the player thrusts in a free direction. That is "stuck".
8. A fall respawn never lands inside an island (05 rule 2.3).

### Hits and lives
9. A touch is a hit: not protected, not waiting, no fall, touching an active hazard that can hit, means exactly one life lost (05 rule 1).
10. No hit without a touch. Every life lost comes from a touch or a fall.
11. Two hazards in one tick cost one life (05 edge cases). A hazard that hit can't hit again during its cooldown (05 rule 1.5).
12. A fall while invulnerable costs no life and doesn't wait (05 rule 2.6).
13. Lives never go up in a run and never below 0. Last life ends in game over after the burst (05 rule 5).

### Score
14. The score never goes down in a run. It freezes on the last life (06, 02 rule 8).
15. No graze is paid while protected or waiting (06).

### Collision geometry
16. The collision code and an independent pixel check agree on every shape pair, within 1 px.
17. The fast pre-filter (`hitboxes_near`) never skips a real overlap.
18. A hitbox is never bigger than the drawn sprite (07 rule 8). Known exceptions are listed in the report.

### Flow and saves
19. Every screen change is one the GDD allows. Pause and game over freeze the run (02 rules 7 and 10).
20. Retry gives a fresh run: 5 lives, score 0, Level 1, Wave 0, no drifters.
21. The top 10 stays sorted, at most 10, names valid, each run saved at most once (11).

### Long play
22. Drifters, popups and rings stay bounded. Every drifter leaves the field in bounded time.
23. Same seed and same inputs give the same run (determinism).
24. Frame cost doesn't creep up over a long endless run. Memory doesn't grow without bound.

### Performance budget
25. Desktop: a frame (ticks + draw) stays under 8 ms at p95 in every wave. That leaves room for the browser slowdown.
26. Browser: 60 fps target. Flag any wave with p95 frame interval over 20 ms or any stutter over 50 ms that the game causes (not the machine).

## How to run it

See `tools/adversary/README.md`. One command per area. Each writes `FINDINGS.md` under `tools/adversary/out/<area>/`.
