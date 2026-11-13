# Perf adversary scripts

Run from `tools/adversary/perf`. Outputs go to `tools/adversary/out/perf`, created on first use. Nothing here edits game/ or docs/.

- `perfdata.py`: reads a soak run (`load_run`) and holds the numbers the reports share. Not run directly.
- `soak.py`: desktop full-loop soak (real drawing, dummy SDL, fake clock, 1 tick/frame, immortal autopilot). `python soak.py --label main --seed 1 --tail-minutes 21 --shots ../out/perf/shots --checkpoint 9000`. Flags: `--jump tail|N` (start waves at that level), `--lean --tracemalloc` (leak run), `--profile-levels N` / `--profile-waves id,id` (cProfile), `--nodraw-until-profile` (fast-forward), `kill -USR1 PID` (graceful stop, writes everything).
- `analyze.py`: `python analyze.py LABEL [--ckpt]` makes per-level/per-wave tables, worst frames, tail slope, marginal cost per drifter type, memory samples into out/perf/report_LABEL.md.
- `profrep.py`: `python profrep.py DIR` prints top 15 functions (cumulative and own) per .prof file, core vs drawing split.
- `start-probe.sh`: builds a probed copy of the game with pygbag into out/perf/webbuild and serves it on :6081 (stop with `kill $(cat server.pid)`).
- `probe.py`: goes into the probed copy; records one line per frame to window.__probe incl. level|wave|seq|resting|tail; URL `?jump=4|8|tail` starts the waves at that level.
- `drive.js`: `node drive.js "?jump=4" SECONDS out.json` drives Chromium through the start page and saves the records.
- `report_browser.py`: `python report_browser.py out/perf/browser/jump_4.json ...` per-level/per-wave interval stats and stutter counts, 10 worst frames.
- `report.py`: `python report.py out/perf/browser/jump_4.json` frame pacing, spikes and tick jitter of one drive.js output, and what the spike frames did. `report_browser.py` is the per-level version.
- `merge.py`: `python merge.py levels seg1 seg2 ...` merges soak runs (wave ids remapped) into one label for analyze.py.
- `tail_trend.py`: `python tail_trend.py tailC tailA tailB` tail slope (OLS with drifter count), per-5-bin medians, same-wave first vs last, memory samples, container growth; writes out/perf/tail_trend.md.
- `build_findings.py` + `findings_template.md`: assemble out/perf/FINDINGS.md from the report files.
Typical order: `python soak.py --label seg4 --jump 4 --stop-level 4`, `python analyze.py seg4`; tail: `python soak.py --label tailA --seed 2 --jump tail --tail-minutes 4 --shots ../out/perf/shots`; leak: `--lean` (no per-frame arrays), `--tracemalloc`.
