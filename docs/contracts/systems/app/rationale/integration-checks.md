# App, integration checks, rationale
Part of: app
Read when: you ask why the app's integration checks works as it does.

## Rationale

- **The UFO checks compare two page loads (DRA-104).** A UFO's path depends on its seed, which no one picks by hand for rows 1 and 2, and a waiting ship in the band may be hit by it. With no key held, nothing else enters the run, so the strongest check that holds whatever the path is that two loads log exactly the same lines.

- **The planet checks use a 1200-tick loop and a placed third row (DRA-96).** A planet's field is 302 px tall and takes about 711 ticks to cross the screen. A 1200-tick loop puts the three rows 400 ticks apart, so planet 1 has left before planet 3 appears, and the first two never meet. Row 3's `y` (289) is where planet 2 has scrolled to 400 ticks after it appeared (−151 + 400 × 1.1), so the two show level with each other, their fields overlapping, without a new placement rule. It is a setting of the debug list for the check, not a game value.
- **The first planet row comes down over the respawn point (DRA-96).** With no key, the ship falls before the planet appears and waits at (320, 240), so the field passes over a waiting ship (no pull) and the body hits it, all in the first 7 s, tick for tick.
- **The island checks run with a 1200-tick loop (DRA-86).** An island is 120 px tall. With the committed 180-tick loop, eight rows would be placed 22 ticks (about 25 px) apart and pile into one wall. 1200 ticks put them 165 px of scroll apart, so each island can be seen and met alone. It is a setting of the debug list for the check, like its `mode`, not a game value.
- **The first island row is placed under the ship (DRA-86).** The ship falls onto it from the first tick, so standing, riding and falling off the floor with it are seen in the first 4 s with no key, and the rest of the timeline (carried in the wait, the respawn moved out of an island, an invulnerable ship blocked) follows from it tick for tick.

- **The DRA-6 and DRA-13 checks are reworded, not dropped (DRA-23).** They relied on the ship respawning once a second with no key held. The behavior they check (one line per event, the cap, the readout rate) still holds; only the way to see it changes.

- **The earlier debug checks are reworded, not dropped (DRA-29).** The test spawn list drops a medium meteorite on the respawn column every 3 s, so a waiting ship gets hit in debug mode. The rules the old checks test still hold; only what else shows up in the log, and how long a wait can last before a hit, changes. Normal-mode checks are untouched.

- **One example row per variant, and one that meets the ship (DRA-47).** The scope asks for example rows for every variant. Seven rows sit clear of the ship's column, so the checks can read each one alone; row 1 is the default variant with a slower `speed` so its first fire lands on the waiting ship, which shows in the browser both that a charge never hits and that the fire does. The triangle appears twice to show `invert`.

- **Fireball rows: one meets the ship, five don't (DRA-56).** The scope asks for both variants, both directions and all three entries. Row 1's x 125 puts its path through the foot of a ship waiting at the respawn point and 15 px clear of a ship held on the top line, so one page shows the hit and another shows every row leave untouched. Row 6 carries `speed`, so the debug field is seen working.
