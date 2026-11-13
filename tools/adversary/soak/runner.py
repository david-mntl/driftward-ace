"""Run one bot on the real game core with the oracle attached."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import paths  # noqa: F401  (puts game/ on sys.path)
from simkit import load_kit
from bots import BOT_NAMES, make_bot
from core.ship import Thrust
from oracle import Checker
from paths import out_dir
from planner import Planner
from stepper import Progress, advance, record_crash

BOT_AND_PLANNER_NAMES = (*BOT_NAMES, "planner")
MODES = ("immortal", "mortal")  # immortal refills the lives to reach the end; mortal plays the real life flow
CHECKPOINT_TICKS = 500  # how often a state fingerprint is kept for the determinism replay


def bot_for_run(bot_name, seed):
    """The bot `bot_name` for a run with `seed`. Each bot gets its own random stream derived from the seed."""
    if bot_name == "planner":
        return Planner(seed * 31 + 5)
    return make_bot(bot_name, seed * 7919 + 13)


def fingerprint(run) -> str:
    """A short hash of the whole run state, without the wave book (which is shared and large)."""
    w = run.waves
    r = replace(run, waves=replace(w, book=None) if w else None)
    return hashlib.sha1(repr(r).encode()).hexdigest()[:16]


def enc(th: Thrust) -> int:
    return th.up | (th.down << 1) | (th.left << 2) | (th.right << 3)


def dec(m: int) -> Thrust:
    return Thrust(up=bool(m & 1), down=bool(m & 2), left=bool(m & 4), right=bool(m & 8))


def run_one(
    bot_name,
    seed,
    mode,
    max_ticks,
    bot=None,
    record=True,
    check=True,
    stop_after_level8_ticks=None,
    run0=None,
    inject=None,
):
    """Play one bot for up to `max_ticks` and return a result dict (see `finish` to replay and save it).

    `bot` overrides the bot named by `bot_name`; `run0` overrides the start state; `inject(run, tick)` may add
    drifters each tick; `record` keeps the inputs and fingerprints; `check` attaches the oracle.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, not {mode!r}")
    kit = load_kit()
    if bot is None:
        bot = bot_for_run(bot_name, seed)
    run = run0 if run0 is not None else kit.new_run(seed)
    checker = Checker(dict(bot=bot_name, seed=seed, mode=mode), kit.last_life_rules.delay_ticks) if check else None
    res = dict(bot=bot_name, seed=seed, mode=mode, max_ticks=max_ticks, result="cap", exception=None)
    inputs: list[int] = []
    fingerprints: dict[int, str] = {}
    progress = Progress()
    started = time.time()
    try:
        while progress.ticks < max_ticks:
            thrust = bot(run)
            if record:
                inputs.append(enc(thrust))
            try:
                run, lives_lost = advance(
                    kit, run, thrust, checker=checker, inject=inject, tick=progress.ticks, immortal=mode == "immortal"
                )
            except Exception:
                res["result"] = "exception"
                res["exception"] = record_crash(checker, run, progress.ticks)
                break
            progress.observe(run, lives_lost)
            if record and progress.ticks % CHECKPOINT_TICKS == 0:
                fingerprints[progress.ticks] = fingerprint(run)
            if run.game_over:
                res["result"] = "game_over"
                break
            level8 = progress.level8_tick
            if (
                stop_after_level8_ticks is not None
                and level8 is not None
                and progress.ticks - level8 >= stop_after_level8_ticks
            ):
                res["result"] = "cap_after_level8"
                break
    except KeyboardInterrupt:
        res["result"] = "interrupted"
    res.update(
        ticks=progress.ticks,
        furthest_level=progress.furthest_level,
        level8_tick=progress.level8_tick,
        final_score=run.score,
        meters=run.scroll.meters,
        lives_lost=progress.lives_lost,
        lives_left=run.lives,
        grazes=run.grazes,
        secs=round(time.time() - started, 1),
        windows=progress.windows,
    )
    if hasattr(bot, "report"):
        res["bot_report"] = bot.report()
    if checker is not None:
        res.update(checker.report(), fall_wait_log=checker.fall_wait_log[:20])
    if record:
        res["fingerprints"] = fingerprints
        res["final_fp"] = fingerprint(run)
        res["_inputs"] = inputs
    return res


def replay_hash(seed, mode, inputs, checkpoints, run0=None, make_inject=None):
    """Replay recorded inputs and return {tick: fingerprint} at the checkpoint ticks, and "final".

    Pass the same `run0` and a `make_inject()` that builds a fresh injector when the run had them.
    """
    kit = load_kit()
    run = run0 if run0 is not None else kit.new_run(seed)
    inject = make_inject() if make_inject is not None else None
    out = {}
    for tick, code in enumerate(inputs):
        run, _ = advance(kit, run, dec(code), inject=inject, tick=tick, immortal=mode == "immortal")
        if tick + 1 in checkpoints:
            out[tick + 1] = fingerprint(run)
    out["final"] = fingerprint(run)
    return out


def finish(res, determinism=True, run0=None, make_inject=None):
    """Replay the run to prove it is deterministic, strip the inputs and write the JSON.

    `run0` and `make_inject` must be the ones given to `run_one`, so the replay starts the same way.
    """
    inputs = res.pop("_inputs", None)
    if inputs is not None and determinism:
        rp = replay_hash(res["seed"], res["mode"], inputs, set(res["fingerprints"]), run0, make_inject)
        bad = [t for t, fp in res["fingerprints"].items() if rp.get(t) != fp]
        if rp["final"] != res["final_fp"]:
            bad.append("final")
        res["determinism_ok"] = not bad
        if bad:
            res.setdefault("findings", {})["determinism"] = dict(
                kind="determinism",
                key=None,
                count=len(bad),
                examples=[dict(bad_checkpoints=bad[:5], bot=res["bot"], seed=res["seed"], mode=res["mode"])],
            )
    name = f"{res['bot']}_{res['seed']}_{res['mode']}"
    (out_dir("soak", "runs") / f"{name}.json").write_text(json.dumps(res, default=str))
    return res


def print_planner_report(result, show_candidates=5):
    """Print what the planner reports: its counters, and the first few candidate unfair spots."""
    report = result["bot_report"]
    print({k: v for k, v in report.items() if k != "candidates"}, "candidates", len(report["candidates"]))
    for candidate in report["candidates"][:show_candidates]:
        print(candidate)


def finding_counts(res):
    """{finding kind: how many times} for a result dict."""
    counts = {}
    for finding in res.get("findings", {}).values():
        counts[finding["kind"]] = counts.get(finding["kind"], 0) + finding["count"]
    return counts


def summary_line(res):
    """One line for the terminal: bot, seed, mode, how far it got, and the finding counts."""
    return (
        f"{res['bot']:14s} s={res['seed']:<3d} {res['mode']:8s} ticks={res['ticks']:6d} lvl={res['furthest_level']} "
        f"{res['result']:10s} score={res['final_score']} lost={res['lives_lost']} {res['secs']}s viol={finding_counts(res)}"
    )
