# Asset credits

## Background

- background.png: the far painting, still. Made by the Director in an AI image tool, resized to 640x480. Own work. The game doesn't load it: it's the source for the sway frames.
- background_sway_00.png to background_sway_11.png: the far painting's slow sway, a loop of 12 frames baked from background.png by tools/art/background_sway.py. Own work.
- bg_planet_0.png to bg_planet_5.png: the broken planets of the middle layer. Cut from a sheet the Director made in an AI image tool. Own work.

## Satellite

- sprites/satellite.png and sprites/satellite_field.png: the satellite's swing frames and its turning magnetism field. Cut and animated by tools/art/satellite_swing.py from a PixelLab image (trial account) made with the Director's reference: staging/art-inbox/satellite-pixellab-a.png. Commercial use on the PixelLab trial is unconfirmed: playtest only until checked.

## Ship

- sprites/ship.png, sprites/ship_flame.png and sprites/ship_streaks.png: the ship's 3 lean frames, its 8 flame frames (2 flicker frames for each of 4 jets) and its 4 air streak frames. Made by tools/art/ship_final.py (script, Pillow + numpy) from a PixelLab image (trial account, Pro Flash, styled on the Director's ChatGPT image): staging/assets/sprites/ship-glide-src-center-f.png, chosen by the Director 2026-10-30. Lean frames are that image squashed and shaded; flames and air streaks are drawn by the script. Commercial use on the PixelLab trial is unconfirmed: playtest only until checked.

## Side panel HUD

- hud_frame.png, hud_sheen.png, hud_panel.png, hud_ship.png, hud_hearts.png, hud_radar.png, hud_ring.png, hud_scan.png and hud_lamp.png: the side panel's frame, panel, wireframe, hearts and motion frames. Drawn by tools/art/hud_panel.py (pygame-ce) from tuning/hud.json, after the Director's mock-up. Own work.

## Fonts

- fonts/Exo2-Bold.ttf: Exo 2 Bold, the HUD's numbers and the text of every screen. Copyright 2013 The Exo 2 Project Authors (https://github.com/googlefonts/Exo-2.0). A static Bold cut from the variable Exo 2 font, because pygame cannot pick a weight from a variable font. Licensed under the SIL Open Font License, Version 1.1: https://openfontlicense.org
- fonts/ShareTechMono.ttf: Share Tech Mono Regular, the HUD's small labels. Copyright (c) 2012, Carrois Type Design, Ralph du Carrois, with Reserved Font Name 'Share'. Shipped unchanged. Licensed under the SIL Open Font License, Version 1.1: https://openfontlicense.org

