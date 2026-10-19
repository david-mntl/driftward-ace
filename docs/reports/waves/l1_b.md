Verdict: provisional
Created by: main session, acting as Wave Designer and Wave Critic by the Director's leave

The one pool wave. Pool, `min_level` 1, 1320 px, `game/waves/l1_b.json`. 2 fireballs (small, and big inverted), 3 meteorites and 2 coins. Extra rest 0.

## Checked by hand
- Seam start: no hazard triggers before 120 px (the loader also refuses it).
- Seam end: the last hazard triggers at 680 px. A hazard needs about 365 px of scroll to enter and leave at Level 1 and about 370 px at Level 8 (hand estimate from the tuning speeds). The wave is 1320 px long, so nothing is on screen in its last 120 px.
- Gaps: no two hazards trigger within 100 px of scroll of each other unless they sit more than 200 px apart sideways. Every gap the ship must pass is wider than 80 px.
- Coins: 2 coins, each placed 70 px sideways from a meteorite's column at the same trigger, 45 px from its hitbox.
- No floating islands in the wave.

## Not checked
- The bot path (rule 7.3). `wave_check` does not exist yet.
- Coin distance by a real run: the 96 px check is by hand from the spawn spots, not measured.
- The tiers (DF-01) and the real wave count (WV-03).

## Next
- The Director plays it and hand-tunes it. The wave must pass `wave_check` before the MVP ships.
