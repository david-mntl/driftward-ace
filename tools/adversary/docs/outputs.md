# Outputs and how to read them

Everything goes to `tools/adversary/out/<engine>/`. Read the `FINDINGS.md` first. Open the other files only to dig into a finding.

Git keeps only each engine's `FINDINGS.md` and the screenshots, as a snapshot of the last hunt (`tools/adversary/.gitignore`). Everything else in `out/` is ignored, because re-running the scripts rebuilds it. Clear `out/` before a new hunt so old files don't mix with new ones.

## FINDINGS.md: the same shape in every engine
1. **Summary.** About five lines: what broke, what was clean, and the limits of the run (for example, "the machine was busy, the planner run was cut short").
2. **Tables.** Runs (soak), frame times (perf), or scenarios (flow).
3. **Findings.** One section each:

```
## S1: island push-out tunnels the ship through the bar
Severity: rule-violation
Confidence: confirmed (reproduced)
What: one or two sentences.
GDD says: drifters/05-floating-islands.md rule 4.4
Repro: python smoke.py floor_skim 1 immortal 10008
Evidence: seed 1, tick 10008, wave w11, ship moved 69 px in one tick
```

The prefix names the engine: `S` soak, `P` perf, `F` flow and collision.

| Severity | Meaning | Blocks a release? |
|---|---|---|
| crash | an exception | yes |
| softlock | the player can't get out | yes |
| rule-violation, collision-miss, collision-false-hit | the game breaks a design rule | yes |
| leak | something grows without bound | yes |
| critical / major / minor (perf) | visible lag / measurable lag / small cost | critical yes, the others are judged case by case |
| suspect | might be a bug, not proven | check it |
| info | a fact worth knowing, not a bug | no |

Confidence: `confirmed` (reproduced on demand), `measured` (perf numbers), `likely`, or `unsure`.

## Soak (`out/soak/`)
| File | What's in it |
|---|---|
| `FINDINGS.md` | Summary, run table, findings, end-of-game facts |
| `runs/*.json` | One file per run, named by bot and seed (fields below) |
| `planner_*.txt` | The planner's deaths per wave and its "no path avoids this hit" moments |
| `endgame_*.txt`, `state_*.pkl` | Progress and saved state of long runs, which can resume |

How to read the run table: `result` is `game_over` (mortal run ended) or `cap` (reached its tick limit). `violations` is `clean` or a count per rule. An immortal run should reach `furthest level` 8.

Main fields in a run JSON:
- `bot`, `seed`, `mode`, `ticks`, `result`, `furthest_level`, `final_score`
- `level_start`: the tick each level began
- `waves_log`: every wave played, with its start tick
- `findings`: each broken rule, with a count and examples (tick, wave, ship, nearby drifters)
- `stats`: peak drifters, popups and rings, deepest island overlap, biggest one-tick push, hits, falls
- `deaths`: each life lost, with its cause and what touched the ship
- `spawn_counts`: drifters spawned by type

Run `python soak/summarize.py` to print the table and findings from all run files.

## Perf (`out/perf/`)
| File | What's in it |
|---|---|
| `FINDINGS.md` | Verdict, method and limits, tables, findings P1, P2... |
| `report_<label>.md` | One run: per level, per wave, worst 15 frames, cost per part and per drifter type |
| `prof_<label>/top15.txt` | The 15 costliest functions, by total and by own time, split into core and drawing |
| `tail_trend.md` | Frame cost and memory over a long endless run |
| `browser/report.txt`, `browser/*.json` | Browser frame intervals per level and wave, stutter counts, raw records |
| `shots/`, `shots_v2/` | Screenshots at Level 4, at the start of Level 8, in the endless tail |
| `soak_<label>.npz`, `*_meta.json` | Raw per-frame data, for re-analysis |

How to read a `report_<label>.md` row:

| Column | Meaning |
|---|---|
| p50 | the typical frame, in ms |
| p95 | 95% of frames were faster. This is the lag a player feels |
| p99, max | rare spikes |
| p95n | p95 corrected for a busy machine (the canary) |
| peak drifters | the most hazards on screen at once |
| tick / draw | game logic vs drawing, ms |

Over 16.7 ms is under 60 fps. On desktop, a p95 over 8 ms means the browser will likely lag.

## Flow and collision (`out/flow_collision/`)
| File | What's in it |
|---|---|
| `FINDINGS.md` | Summary and findings |
| `a1_fuzz.json` | Random flow runs: count, names saved, violations |
| `a2_targeted.txt` | Each scripted scenario: pass or fail |
| `a3_bfs.json`, `a3b_seed_escape.log` | Softlock search: states sampled, how many had no way back to the menu |
| `b1_collision_diff.json` | Comparisons per drifter type, variant and level: misses, false hits, pre-filter skips |
| `b2_rehit_graze.txt` | Re-hit cooldown and graze scenarios |
| `b3_sprite_coverage.json` | Share of each hitbox that sits on drawn pixels, per type |
| `b4_shape_fuzz.json` | Random shape pairs against the pixel check |

A clean result reads `0 violations`, `0 misses, 0 false hits`, and `0 states without a way back`.

## wave_check
Prints to the terminal. One line per wave, `PASS` or `FAIL`, with each check under it. The last line counts passes and fails. The release hunt saved its runs to `out/wave_check_all.txt` and `out/wave_check_bot.txt`.

## The release report
The hunt's conclusions go to `docs/reports/release-hunt/`. `report.md` sums up the run, and each real bug gets its own `bug-NN-<name>.md` with a repro and a fix proposal.
