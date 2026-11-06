# Level-up moment: the level-up rest, the banner, the HUD level pop and the `level_up` cue
Version: 0
Status: draft
Features: DRA-148
Created by: architect

## Purpose
When a level rises, the run adds a fixed rest before the next wave, plays a banner in it and pops the HUD's level readout, and names a `level_up` sound cue for the audio feature to hang a jingle on. The rest and the banner's state are core; the banner, the number's flight and the HUD pop are views that read it. The contract is split into parts: open only the one you need.

## Parts
<!-- parts:begin -->
| Part | Holds | Read when | Size |
|---|---|---|---|
| [core](level-up/core.md) | Diagram, Interface, Rules | you build or test the level-up rest, the banner's state in the run, the shown level or the `level_up` cue. | 11.0 KB |
| [rationale](level-up/rationale.md) | Rationale | you ask why the level-up moment works as it does. | 5.5 KB |
| [tuning](level-up/tuning.md) | Interface, Rules | you change `game/tuning/level_up.json`, its schema or how it is loaded and checked. | 4.1 KB |
| [view](level-up/view.md) | Diagram, Interface, Presentation | you build or test the banner, the number's flight, the picture bump or the HUD level pop. | 18.4 KB |
<!-- parts:end -->
