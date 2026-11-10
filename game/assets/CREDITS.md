# Asset credits

## Background

- background.png: the far painting, still. Made by the Director in an AI image tool, resized to 640x480. Own work. The game doesn't load it: it's the source for the sway frames.
- background_sway_00.png to background_sway_11.png: the far painting's slow sway, a loop of 12 frames baked from background.png by tools/art/background_sway.py. Own work.
- bg_planet_0.png to bg_planet_5.png: the broken planets of the middle layer. Cut from a sheet the Director made in an AI image tool. Own work.
- bg_item_0.png to bg_item_5.png: the wrecks and debris that take turns with the planets in the middle layer. Cut and shrunk by tools/art/background_items.py from a sheet the Director made in an AI image tool: staging/art-inbox/background-items.png. Own work.

## Audio

The CC BY 4.0 credits below show in the game, on the menu's Credits page (`game/ui/credits.py`). The CC0 game-over sound and the fonts are named there too, as a courtesy.

- audio/music_loop.ogg: "Lo-fi Music Guitar (Loop)" (track 52, "Under the Rain", filtered version) by Migfus20, https://freesound.org/people/Migfus20/sounds/569791/, uploaded 2021-04-28. License: Creative Commons Attribution 4.0 (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/. The author asks: "Feel free to use my music, it would be great if you credit me." The track uses "Rain, sheet roof.wav" by snarcle, https://freesound.org/people/snarcle/sounds/569370/, also CC BY 4.0. Converted from MP3 to Ogg Vorbis (quality 4). Edited for a seamless loop: trimmed to bars 2 to 47 of the original, and the last four bars (6.5 s) crossfaded into the first four, beat-aligned. Nothing else changed. Picked by the Director 2026-11-07.
- audio/sfx_level_up.ogg: "Achievement 2" by sonically_sound, https://freesound.org/people/Sonically_Sound/sounds/625715/, uploaded 2022-03-29. License: Creative Commons Attribution 4.0 (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/. Whole 7 s sound, scaled up 1.7 dB so its peak matches the sound it replaced, a 5 ms fade-in, converted from WAV to Ogg Vorbis (quality 5). Picked by the Director 2026-11-07.
- audio/sfx_game_over.ogg: "Game Over Arcade" by Mountain_Man, https://freesound.org/people/mountain_man/sounds/382310/, uploaded 2017-02-28. License: Creative Commons 0 (CC0), http://creativecommons.org/publicdomain/zero/1.0/. No credit needed. Converted from WAV to Ogg Vorbis (quality 5) and made 9 dB louder, so it sits with the other effects. Picked by the Director 2026-11-07.
- audio/sfx_hit.ogg, audio/sfx_graze.ogg and audio/sfx_coin.ogg: made by the Director in jsfxr. Own work. Converted from WAV to Ogg Vorbis (quality 5), not otherwise changed. Picked by the Director 2026-11-07.

## Satellite

- sprites/satellite.png and sprites/satellite_field.png: the satellite's swing frames and its turning magnetism field. Cut and animated by tools/art/satellite_swing.py from a PixelLab image (trial account) made with the Director's reference: staging/art-inbox/satellite-pixellab-a.png. Commercial use on the PixelLab trial is unconfirmed: playtest only until checked.

## Ship

- sprites/ship.png, sprites/ship_flame.png and sprites/ship_streaks.png: the ship's 3 lean frames, its 8 flame frames (2 flicker frames for each of 4 jets) and its 4 air streak frames. Made by tools/art/ship_final.py (script, Pillow + numpy) from a PixelLab image (trial account, Pro Flash, styled on the Director's ChatGPT image): staging/assets/sprites/ship-glide-src-center-f.png, chosen by the Director 2026-10-30. Lean frames are that image squashed and shaded; flames and air streaks are drawn by the script. Commercial use on the PixelLab trial is unconfirmed: playtest only until checked.

## Side panel HUD

- hud_frame.png, hud_sheen.png, hud_panel.png, hud_ship.png, hud_hearts.png, hud_radar.png, hud_ring.png and hud_scan.png: the side panel's frame, panel, wireframe, hearts and motion frames. Drawn by tools/art/hud_panel.py (pygame-ce) from tuning/hud.json, after the Director's mock-up. Own work.

## Fonts

- fonts/Exo2-Bold.ttf: Exo 2 Bold, the HUD's numbers. Copyright 2013 The Exo 2 Project Authors (https://github.com/googlefonts/Exo-2.0). A static Bold cut from the variable Exo 2 font, because pygame cannot pick a weight from a variable font. Licensed under the SIL Open Font License, Version 1.1: https://openfontlicense.org
- fonts/ShareTechMono.ttf: Share Tech Mono Regular, the HUD's small labels and the text of every screen. Copyright (c) 2012, Carrois Type Design, Ralph du Carrois, with Reserved Font Name 'Share'. Shipped unchanged. Licensed under the SIL Open Font License, Version 1.1: https://openfontlicense.org

- Exo2-BlackItalic (inlined in web/start.tmpl): Exo 2 Black Italic (Latin subset, as served by Google Fonts), the game's name on the start page. Copyright 2013 The Exo 2 Project Authors (https://github.com/googlefonts/Exo-2.0). Shipped unchanged, inlined in the start page, not inside the game package. Licensed under the SIL Open Font License, Version 1.1: https://openfontlicense.org

## Drifters

All own work, drawn by script (Pillow + numpy) from the designs the Director picked on 2026-11-05. No outside source. The large masters and design stills are not kept in the repo. The scripts that build ufo_broken, ufo_clean and fireball read staged inputs that were removed, so those three cannot be rebuilt as they are.

- sprites/ufo_broken.png: the broken UFO, 8 frames of 40x20, played in random order. tools/art/ufo-broken-anim.py, built on the staged ufo-d2-r2 master.
- sprites/ufo_clean.png: the clean UFO, 8 frames of 40x20, a loop. tools/art/ufo-clean-anim.py, from ufo-d3-r3 (tools/art/ufo-d3.py).
- sprites/planet_marble.png: the marbled planet turning, 24 frames of 64x64. tools/art/planet-marble-anim.py, from planet-d5-r2 (tools/art/planet-d5.py).
- sprites/fireball.png: the dying-star fireball, 6 frames of 64x64. tools/art/fireball-r1-anim.py, converted from the staged fireball-d4-r1 master and piskel.
- sprites/coin_common.png and sprites/coin_rare.png: the crystal coin, 8 frames of 24x24 each. tools/art/coin-anim.py, from coin-d2-r3 (tools/art/coin-d2.py).
- sprites/electric_ball_charge.png (8 frames of 24x24), sprites/electric_ball_fire.png (6 frames of 24x24) and sprites/electric_ball_ring.png (6 frames of 128x128): the electric ball charging, firing, and its firing circle. tools/art/electric-ball-anim.py, from electric-ball-d4-r2 (charge) and electric-ball-d2-r2 (fire).
- sprites/chain_node_charge.png (8 frames of 18x18), sprites/chain_node_fire.png (6 frames of 18x18) and sprites/chain_arc.png (6 frames of 181x16): the chain lightning nodes and arc. tools/art/chain-lightning-anim.py, from the electric ball looks.
- sprites/island_ground_1.png, island_ground_2.png and island_ground_3.png: the three floating-island grounds, 320x120 each, copied unchanged from floating-island-d1-r3, d2-r3 and d3-r3 (tools/art/floating-island-d1.py to d3.py).
- sprites/meteorite_rock_a.png to meteorite_rock_d.png: the meteorite's four rock looks, 32 frames of 36x36 each, the rock turning on a tilted axis. tools/art/meteorite-d11.py --round 2 (3D bodies, style from meteorite-d10.py), own work, style described in words from a Director reference (the reference itself is not used or shipped). Picked by the Director 2026-11-05.
- mute_icon.png: the muted-music icon, a pale violet-white speaker with a fuchsia slash, 24x24, one still picture. tools/art/mute_icon.py (Pillow) from tuning/mute_icon.json, master at 8x (192x192) kept in staging/assets/ui/mute_icon-master.png. Own work. docs/contracts/DRA-159/tasks/DRA-159-01-art-audio-engineer.md, 2026-11-07
