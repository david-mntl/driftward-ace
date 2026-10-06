Feature: DEMO-1
Assignee: art-audio-engineer
Writes to: staging/assets/ (sprite and CREDITS entry), tools/art/ (generator script if used)
Contract: docs/contracts/player-ship.md#interface
Status: open
Linear:

## Do
Make one player ship image and stage it at `staging/assets/sprites/player_ship.png`.
- PNG, 100x100 px, alpha channel, fully transparent background.
- A spaceship with its nose pointing up. One still image.
- Art style and palette: the GDD has none. Ask the Director for the style before drawing.
- Add a CREDITS entry in `staging/assets/CREDITS.md` with source, license, size, this task path and date.
- Stop in staging, Status blocked, and wait for the Director's approval.

## Acceptance check
Open `staging/assets/sprites/player_ship.png`: a spaceship, nose up, on a transparent background, 100x100 pixels.

## Out of scope
Animation, extra frames, thrust or damage variants, game code, loading the image in the game, hitbox, any other asset, moving the file to `game/assets/` without the Director's approval.
