# Soak harness

Headless bots play the real `core.run` and an independent oracle checks every tick. Run from this folder. Outputs go to `../out/soak/`.

- `python run_matrix.py immortal --seeds 1,2,3 [--ticks N] [--bots a,b]` runs every bot immortal (lives refilled) to reach Level 8 and beyond, in parallel.
- `python run_matrix.py mortal --seeds 1,2,3` runs every bot on the real life flow until game over.
- `python run_matrix.py planner --seeds 1,2` runs the lookahead survival bot, mortal and immortal.
- `python endgame_chunks.py <bot> <seed> 125000 [chunk]` runs one long immortal run in fresh-process chunks (resumable, state in `../out/soak/state_*.pkl`) with the full oracle. `python run_matrix.py endgame` is the older single-process version.
- `python tail_clock.py <seed> [ticks]` runs the real step_run with an empty field for 135,000 ticks: wave clock, level, scroll, score and banner over the endless tail.
- `python run_planner.py <seed> <mortal|immortal> <ticks>` runs the lookahead planner and prints candidates and deaths per wave.
- `python fuzz_islands.py <seed> <ticks> [bot]` runs a synthetic island fuzz (random island pairs, stacks, corners) at Level 8 scroll speed. Not shipped content.
- `python smoke.py <bot> <seed> <immortal|mortal> <ticks>` runs one bot and prints findings.
- `python summarize.py [--examples N]` prints the run table and all findings from `../out/soak/runs/*.json`.
- `bench_planner.py <ticks>` times the planner on one mortal run.
- Modules: `oracle.py` (invariants), `geom.py` (independent geometry), `bots.py`, `planner.py`, `stepper.py` (one game tick, and the running totals of a run), `runner.py` (the run loop, determinism replay, JSON output).
