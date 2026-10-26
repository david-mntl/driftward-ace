Score: 7.0 | Lowest: 4 | Size: 7

Asset: demo-hud
Kind: screen
Round: 1
Image: staging/assets/ui/demo-hud-r1.png
Board: staging/assets/ui/demo-hud-r1-board.png
Measured: 640 × 480 px, 1 frame
GDD: 10-ui.md, 12-art-and-audio.md, 03-world-and-camera.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size & layout | 7 | The image is 640 × 480, the same as `screen_w` × `screen_h` (guess). Positions follow the locked rows: SCORE top-left, LV and GRAZE on the line below it, lives top-right. All of it sits in the top strip, well above the top line at y=168, so it hides no warning space (rule 1). Lives are three solid fuchsia ship icons, but `lives_display` asks for hearts, one per life left, and the layout sketch in 10-ui.md shows ♥. Margins and sizes are TBD (UI-01), so they are not scored. BEST is correctly absent (it only shows once the top 10 has an entry). |
| 2 | Colors | 4 | The three lives icons are solid, bright fuchsia. Rule 6 in 12-art-and-audio.md says a solid bright fuchsia shape always means a coin, so the player can read these as coins. The color language also gives fuchsia to the anomaly and coins, and gives the ship cobalt and pale plating, so a fuchsia ship icon says "touched" about the one untouched thing. The text is pale white-grey on the black placeholder (`placeholder_bg` (0, 0, 0), guess). It is clean and well defined. HUD colors are TBD (UI-01), so only the icon conflict counts here. |
| 3 | Font & glow | 8 | The letters read as Exo 2 (a squared, techno sans), as `ui_font` asks (guess). Text is flat with no glow and no outline, as `ui_glow` (none) and the `glow` row require. The text looks crisp in the 4× crop of the board. The icons are flat too. Font size is TBD (UI-01), so not scored. |
| 4 | Voice & words | 9 | Labels are short and terse: "SCORE 1234", "LV 2", "GRAZE 5". That fits `ui_voice` (terse arcade, few words) and the names used in rule 2. No locked word is changed or misused. No sentences, no filler. |
| 5 | Readability | 7 | At 1× on the board the text is easy to read against black, and the three icons stand out. In the 4× crop the gap between "SCORE" and "1234" is tight, so it reads close to SCORE1234. "GRAZE 5" has uneven letter gaps, with a visible space inside "GRAZE" before the E. The lives icons are small and solid, and their silhouette is a ship, not a heart. Lives cannot be told apart from coins by color alone. |

## Fix first
- Colors: lives icons must not be solid bright fuchsia (rule 6). Use hearts as `lives_display` says, in a color that does not mean a coin.
- Size & layout: swap the ship icons for hearts, one per life left, top-right as in the 10-ui.md sketch. Open the word gap after SCORE and even out the letter gaps in GRAZE.
