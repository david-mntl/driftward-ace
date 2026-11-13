"""Proves the flow checker can see bugs: inject three flow bugs, expect violations from a1_flow_fuzz.fuzz_one."""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import paths  # noqa: F401  (puts game/ on sys.path)
import a1_flow_fuzz
import core.game_flow as game_flow
from flowlib import patched

SAVE_KINDS = ["none", "empty", "full_tiny"]


def count_violations(label):
    """Fuzz six seeds and print how many invariant violations the checker found."""
    total = 0
    for seed in range(1000, 1006):
        total += len(a1_flow_fuzz.fuzz_one((seed, 2500, SAVE_KINDS[seed % 3]))[2])
    print(label, "violations:", total)


def main():
    count_violations("clean")

    original_paused = game_flow._step_paused
    with patched(
        game_flow,
        "_step_paused",
        lambda flow, keys, presses: (
            replace(game_flow._enter(flow, game_flow.Screen.PLAYING))
            if keys.focus_lost
            else original_paused(flow, keys, presses)
        ),
    ):
        count_violations("bug: focus_lost resumes pause")

    original_confirm = game_flow._confirm_name
    with patched(
        game_flow,
        "_confirm_name",
        lambda flow, picker: (
            replace(original_confirm(flow, picker), picking=True)
            if flow.saves is not None and flow.run.score % 2
            else original_confirm(flow, picker)
        ),
    ):
        count_violations("bug: name confirm keeps picking on odd scores")

    original_choices = game_flow._step_choices
    with patched(
        game_flow,
        "_step_choices",
        lambda flow, presses: original_choices(replace(flow, run=replace(flow.run, lives=4)), presses),
    ):
        count_violations("bug: choices tamper with the run")


if __name__ == "__main__":
    main()
