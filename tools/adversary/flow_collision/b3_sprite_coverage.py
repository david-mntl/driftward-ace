"""Hitbox vs drawn sprite coverage per drifter type (GDD 07 rule 8: hitbox never bigger than what is seen).

For each drifter type/variant, step its life with the ship far away, render each sampled ACTIVE
frame with the real view onto a transparent surface, and report the share of the hitbox area
(pixel centers inside any hitbox shape) that lies on opaque sprite pixels.
"""

import json, random
from dataclasses import replace

import numpy as np
import pygame
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: simkit, paths

import cli
import paths  # noqa: F401  (puts game/ on sys.path)
from flowlib import KIT, spawn_first_valid
from paths import out_dir
from oracle import bounds, sd
from core.drifters.base import Phase, TickContext
from core.ship import spawn
from core.world import SCREEN_H, SCREEN_W

pygame.display.set_mode((SCREEN_W, SCREEN_H))
# The sprite code draws a random salt per process when it is built, and the salt changes the looks.
# Seed it first, so the coverage numbers repeat from run to run.
random.seed(0)
from app.drifter_looks_tuning import install_drifter_looks

install_drifter_looks(KIT.tuning)
import ui.drifters.satellite_view  # noqa: F401  (registers)
from ui.drifters.registry import render_drifter
from ui.drifters.preload import warm_sprites  # noqa: F401

W, H = SCREEN_W, SCREEN_H
CORNER_MARGIN = 20.0  # the ship waits in the bottom-left corner, far from every drifter
DRIFTER_SEED = 7  # any fixed seed: the coverage must not depend on it, and a fixed one makes the run repeat


def hit_mask(hb):
    ys, xs = np.mgrid[0:H, 0:W]
    P = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    inside = np.zeros(len(P), bool)
    for s in hb:
        b = bounds(s)
        sel = (P[:, 0] > b[0] - 1) & (P[:, 0] < b[2] + 1) & (P[:, 1] > b[1] - 1) & (P[:, 1] < b[3] + 1)
        idx = np.nonzero(sel)[0]
        if len(idx):
            inside[idx] |= sd(s, P[idx]) < 0
    return inside.reshape(H, W)


def run():
    rows = []
    for dt, tt in KIT.tuning.drifters.items():
        for vn in tt.variants:
            d = replace(spawn_first_valid(dt, vn, 1, seed=DRIFTER_SEED), uid=5)
            ship = replace(spawn(), x=CORNER_MARGIN, y=H - CORNER_MARGIN)
            covs = []
            extra_px = []
            n = 0
            for t in range(1500):
                d = d.update(TickContext(ship=ship, scroll_step_px=1.0)).mark_entered()
                if d.phase is Phase.GONE or d.is_off_screen():
                    break
                if d.phase is not Phase.ACTIVE or t % 9:
                    continue
                hb = d.current_hitbox()
                if not hb:
                    continue
                bb = [bounds(s) for s in hb]
                if (
                    min(b[0] for b in bb) < 0
                    or min(b[1] for b in bb) < 0
                    or max(b[2] for b in bb) > W
                    or max(b[3] for b in bb) > H
                ):
                    continue
                surf = pygame.Surface((W, H), pygame.SRCALPHA)
                render_drifter(surf, d)
                alpha = pygame.surfarray.array_alpha(surf).T > 8
                hm = hit_mask(hb)
                area = int(hm.sum())
                if area == 0:
                    continue
                covered = int((hm & alpha).sum())
                covs.append(covered / area)
                extra_px.append(area - covered)
                n += 1
            if covs:
                rows.append(
                    dict(
                        type=dt.value,
                        variant=vn,
                        frames=n,
                        min_cov=round(min(covs), 3),
                        mean_cov=round(sum(covs) / len(covs), 3),
                        max_uncovered_px=int(max(extra_px)),
                    )
                )
            else:
                rows.append(dict(type=dt.value, variant=vn, frames=0))
    return rows


if __name__ == "__main__":
    cli.parser(__doc__).parse_args()
    rows = run()
    (out_dir("flow_collision") / "b3_sprite_coverage.json").write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(r)
