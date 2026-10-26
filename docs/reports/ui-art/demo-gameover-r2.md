Score: 9.2 | Lowest: 9 | Size: 9

Asset: demo-gameover
Kind: screen
Round: 2
Image: staging/assets/ui/demo-gameover-r2.png
Board: staging/assets/ui/demo-gameover-r2-board.png
Measured: 640 × 480 px, no frames
GDD: 10-ui.md, 12-art-and-audio.md, 03-world-and-camera.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size & layout | 9 | The image is 640 × 480, the same as `screen_w` × `screen_h` (guess). The content now matches `game_over_screen` (locked) exactly: message, score, then RETRY with MENU under it. There is no letter picker, which is right for a score off the top 10. The board's crop labels place the stack from y 157 to y 323, so it is centered top to bottom. The message block runs from x 217 to x 423, so it is centered left to right. RETRY and MENU are centered, and the arrow sits to their left, as `game_over_look` (guess) asks. The gap above RETRY is wider than the gap above SCORE, which fits 40 px against 32 px. I can't measure the 32 / 40 / 12 px gaps by eye, so I don't confirm them. |
| 2 | Colors | 9 | Same as round 1. All the text is one pale silver-white, and the only accent is the cobalt arrow by RETRY, as `game_over_look` asks. Cobalt means "you, untouched" in the color language. There is no fuchsia, orange or white-cyan, so no color says coin, heat or electricity. The background is the black placeholder (`placeholder_bg` (0, 0, 0), guess). The 4× crops show clean, sharp color with no muddy fringe. |
| 3 | Font & glow | 9 | Same as round 1. Every line reads as Exo 2 Regular (see the angular G and R in the 4× message crop), as `ui_font` (guess) and `game_over_look` ask. The text and the arrow are flat, with no glow, halo or outline. That matches `ui_glow` (none, guess) and the `glow` row in 12 ("the HUD stays flat"). |
| 4 | Voice & words | 10 | The message reads GAME OVER, exactly as written and with no "!", which is right for a score off the list (`game_over_message`, rule 10, rule 6). SCORE 1234 follows the `SCORE <n>` format. RETRY and MENU are the locked words. The round 1 filler sentence is gone, so the screen is terse, as `ui_voice` (guess) asks. |
| 5 | Readability | 9 | On the 1× board the stack reads in one look: the large message, then the score, then the two items. The cobalt arrow makes the selected item clear at a glance. RETRY and MENU are the smallest and thinnest text, Regular weight on black, but they are still clear at 1×. |

## Fix first
- Size & layout: check the drawn gaps against `game_over_look`: 32 px from message to score, 40 px from score to RETRY, 12 px between RETRY and MENU. The image itself shows no layout fault.
- Readability: nothing to fix in the image. If RETRY/MENU read thin in play, raise it with the Director. Font weight and size are set in `game_over_look`.

## Since round 1
- Size & layout: 5 → 9. The extra sentence is gone. The content now matches the `game_over_screen` list, and SCORE sits straight under the message.
- Voice & words: 1 → 10. NEW BEST SCORE! became GAME OVER, which is right for a score off the list, and the filler line is gone.
- Readability: 6 → 9. Without the dense second line, the top of the stack is no longer crowded and the score reads at once.
