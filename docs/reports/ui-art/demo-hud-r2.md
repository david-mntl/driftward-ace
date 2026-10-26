Score: 8.4 | Lowest: 8 | Size: 9

Asset: demo-hud
Kind: screen
Round: 2
Image: staging/assets/ui/demo-hud-r2.png
Board: staging/assets/ui/demo-hud-r2-board.png
Measured: 640 × 480 px, 1 frame
GDD: 10-ui.md, 12-art-and-audio.md, 03-world-and-camera.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size & layout | 9 | The image is 640 × 480, the same as `screen_w` × `screen_h` (guess). SCORE is top-left, LV and GRAZE sit on the line below it, and the lives sit top-right, all as the locked rows and the sketch in 10-ui.md say. Lives are now hearts, one per life left, as `lives_display` asks (guess). All of it stays in the top strip, far above the top line at y=168, so no warning space is hidden (rule 1). Margins and sizes are TBD (UI-01), so they are not scored. BEST is correctly absent (it shows only once the top 10 has an entry). The three hearts are tightly grouped at the right edge; the layout matches the sketch. |
| 2 | Colors | 8 | The hearts are now cobalt blue with a pale rim. That is the "you, untouched" color in the color language, so it fits the player's own lives. It no longer clashes with rule 6, since there is no solid fuchsia in the HUD. The blue also stays clear of the pale white-cyan used for electricity. Text is clean pale white-grey on the black placeholder (`placeholder_bg` (0, 0, 0), guess). HUD colors are TBD (UI-01), so only the color-language check counts. The fill is a mid blue, a little dimmer than the text, but still well defined. |
| 3 | Font & glow | 8 | The letters read as Exo 2, as `ui_font` asks (guess). The text is flat with no glow or outline, as `ui_glow` (none) and the `glow` row require. The hearts are flat fills with a thin pale edge and no halo, so they stay inside "the HUD stays flat". Font size is TBD (UI-01), so it is not scored. |
| 4 | Voice & words | 9 | Labels are terse: "SCORE 1234", "LV 2", "GRAZE 5". That fits `ui_voice` (short labels, few words) and the names used in rule 2. No locked word is changed. No sentences, no filler. |
| 5 | Readability | 8 | The round-1 spacing problems are fixed. In the 4× crop there is now a clear gap between "SCORE" and "1234", and the letters in "GRAZE" are evenly spaced. At 1× on the board all text is easy to read on black. The three hearts read as hearts at once and cannot be mistaken for coins. Two small points. The hearts are small and their blue is dimmer than the white text, so they carry less weight than the score. The text edges look slightly soft in the 4× crop. |

## Fix first
- Readability: lift the heart blue a little in brightness, or thicken the pale rim, so the lives stand out as much as the text. Keep it cobalt, not fuchsia or white-cyan.
- Colors: same point. The blue fill is the weakest part of the HUD against black. Keep it away from fuchsia (rule 6) and from pale white-cyan (electricity).

## Since round 1
- Size & layout 7 → 9: ship icons replaced by hearts, one per life left, top-right, as `lives_display` and the 10-ui.md sketch ask.
- Colors 4 → 8: solid fuchsia lives are gone. The hearts are cobalt blue, the "you, untouched" color, so rule 6 no longer conflicts.
- Font & glow 8 → 8: no change. Still Exo 2, flat, no glow.
- Voice & words 9 → 9: no change.
- Readability 7 → 8: word gap after SCORE opened, GRAZE letter gaps evened out, and the lives now read as hearts.
