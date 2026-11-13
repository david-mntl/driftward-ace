"""A retry and a menu->play must give a run whose waves equal a fresh start_waves from the derived seed."""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import paths  # noqa: F401  (puts game/ on sys.path)
from a2_flow_targeted import play_flow, to_game_over
from flowlib import KIT, S, tick
from core.run import start_run
from core.saves import Saves
from core.waves import SEED_BITS, start_waves

SEEDS = (3, 8, 99)


def main():
    bad = []
    for seed in SEEDS:
        flow = to_game_over(play_flow(Saves(), seed=seed))
        old = flow.run
        flow = tick(flow)
        flow = tick(flow, confirm=True)  # name
        flow = tick(flow)
        retried = tick(flow, confirm=True)  # retry
        expected_waves = start_waves(
            KIT.book, random.Random(old.waves.run_seed).getrandbits(SEED_BITS), KIT.level_up_rules
        )
        if retried.screen != S.PLAYING or retried.run.waves != expected_waves:
            bad.append(f"seed {seed}: retry waves differ from fresh start_waves")
        # a fresh start_run must equal the retry's run in everything except the waves
        reference = start_run(waves=expected_waves, graze_rules=KIT.graze_rules, last_life_rules=KIT.last_life_rules)
        if retried.run != reference:
            bad.append(f"seed {seed}: retry run != start_run(...)")
    print("fresh-run probe:", bad or "OK")


if __name__ == "__main__":
    main()
