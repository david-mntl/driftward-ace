# flow_collision: adversarial flow fuzz and collision differential

Run from any directory. Outputs go to `../out/flow_collision/`. Set `OMP_NUM_THREADS=1` for the numpy jobs.

- `flowlib.py`: one app tick (`tick`), the allowed-transition table from GDD 02, the per-tick invariant `Checker`, `spawn_first_valid` and `patched`.
- `scenarios.py`: the scenario runner a2 and b2 share (`Suite`).
- `a1_flow_fuzz.py [runs] [ticks]`: random long fuzz of the screen flow (sticky keys, confirm holds, focus bursts, lives=1 shortcuts, 6 save sets incl. none) with the invariant checker.
- `a2_flow_targeted.py`: scripted flow scenarios (pause everywhere, held confirm across screens, arrow held through a fall, retry/menu, name picker, top-10 ties vs a model, menu wrap).
- `a3_bfs_softlock.py [seeds]`: from sampled states, a constructive bot and a bounded BFS over key macros must reach the menu.
- `oracle.py`: independent signed-distance-grid overlap oracle (does not use core.collision math).
- `b1_collision_diff.py [samples] [stride]`: every drifter type, variant and level (1, 4, 8): hit and graze zone vs the ship T, near pre-filter, boundary bisection hunt.
- `b1_mutation_sanity.py`: injects known collision bugs to prove the b1 oracle can see them.
- `b2_rehit_graze.py`: scripted rehit-cooldown and graze scenarios on `step_run`.
- `b3_sprite_coverage.py`: share of each hitbox that lies on opaque pixels of the real drifter view.
- `b4_shape_fuzz.py [n]`: random shape pairs of all kinds (4x4) vs the oracle, plus near and graze zone checks.
- `a1_mutation_sanity.py`: injects three flow bugs to prove the flow checker catches them.
- `a4_fresh_run_probe.py`: a retry's run equals `start_run` with `start_waves` from the derived seed (imports a2, so it re-runs those cases first).
- `a3b_seed_escape.py <seed>`: single-seed version of a3 (the pooled a3 run hung on a worker, so the result comes from 24 single-seed runs, 288 states, 0 without a way back to the menu; log in out/a3b_seed_escape.log).
