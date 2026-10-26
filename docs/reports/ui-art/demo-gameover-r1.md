Score: 6.0 | Lowest: 1 | Size: 5

Asset: demo-gameover
Kind: screen
Round: 1
Image: staging/assets/ui/demo-gameover-r1.png
Board: staging/assets/ui/demo-gameover-r1-board.png
Measured: 640 × 480 px, no frames
GDD: 10-ui.md, 12-art-and-audio.md, 03-world-and-camera.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size & layout | 5 | The image is 640 × 480, the same as `screen_w` × `screen_h` (guess). The stack is centered both ways, and RETRY sits above MENU with no letter picker, which is right for a score off the top 10 (`game_over_screen`, locked). The problem is a line that is not in the spec. A long sentence sits right under the message and runs almost from edge to edge. `game_over_screen` lists only the message, the score, the letter picker when it applies, then RETRY and MENU. Because of that line, SCORE 1234 hangs under the sentence instead of 32 px under the message, so the spacing in `game_over_look` (guess) is off. Sizes are not checked by eye. The three lines from the spec keep their order: message largest, then score, then the two items. |
| 2 | Colors | 9 | All the text reads as one pale silver-white, and the only accent is a cobalt arrow, as `game_over_look` (guess) asks. Cobalt is the "you, untouched" color in the color language. There is no fuchsia, orange or white-cyan, so no color says coin, heat or electricity. The background is the black placeholder (`placeholder_bg` (0, 0, 0), guess). The colors are clean and sharp in both 4× crops. |
| 3 | Font & glow | 9 | Every line reads as Exo 2 at a regular weight, as `ui_font` (guess) and `game_over_look` ask. The letters are flat, with no glow, halo or outline, which matches `ui_glow` (none, guess) and the `glow` row in 12 ("the HUD stays flat"). The arrow is also a flat fill. The 4× crops show smooth edges with no dark fringe. |
| 4 | Voice & words | 1 | This is the main failure. The run's score is off the top 10, so rule 10 and `game_over_message` (locked) both require GAME OVER. The screen says NEW BEST SCORE, which tells the player something false. A "!" is also added to it, but locked words "stay as written" (rule 6). The extra line, "Oh no! You got smashed by space rocks! Better luck next time, hero!", is filler and hype, which rule 6 and `ui_voice` (terse arcade, guess) rule out. It is also content that `game_over_screen` does not list. SCORE 1234, RETRY and MENU are right. |
| 5 | Readability | 6 | On the 1× board, the message, the score and RETRY/MENU are easy to read on black. The selected item is clear at a glance because of the cobalt arrow. The long small sentence packed right under the headline turns the top of the stack into one dense two-line block. It pulls the eye away from the score, and at 1× it is the hardest text to read. Remove it and the stack would read in one look. |

## Fix first
- Voice & words: for a score off the list, show GAME OVER exactly as written, with no "!" (rule 10, `game_over_message`, rule 6).
- Size & layout: remove the extra sentence so SCORE sits 32 px under the message, as `game_over_look` and the `game_over_screen` content list say.
