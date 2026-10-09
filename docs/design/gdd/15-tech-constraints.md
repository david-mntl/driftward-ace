# Tech constraints
Status: locked
Depends on: [01-vision.md](01-vision.md)

## Summary
The game is Python built for the browser. These limits are hard: breaking one breaks the build or the game in the browser. They are design constraints because they decide what the game can do.

## Values
| Key | Value | Unit | Range | Status | Source |
|---|---|---|---|---|---|
| language | Python | — | — | locked | Director |
| engine | pygame-ce (never classic pygame) | — | — | locked | Director |
| web_build | pygbag 0.9.3, pinned. Never upgrade. | — | — | locked | Director |
| build_output | static `web.zip` from `pygbag --archive` | — | — | locked | Director |
| hosting | static only: itch.io, GitHub Pages as backup | — | — | locked | Director |
| tick_rate | 60 | ticks/s | — | locked | Director |
| audio_format | .ogg only | — | — | locked | Director |

## Rules
1. **Async main loop.** The main loop is `async` and yields every frame with `await asyncio.sleep(0)`. No blocking calls, no threads. A blocking loop freezes the browser page.
2. **Fixed tick.** Every game rule runs on the fixed 60 Hz tick, never on frame time. The browser frame rate can dip; the rules must not change when it does.
3. **Audio.** .ogg only, because MP3 and WAV break the pygbag build. pygbag's own click-to-start screen unlocks browser audio. Never build a custom one.
4. **No server.** No server code, no paid services, no online features.
5. **Browser performance.** Python in WebAssembly is slow. Glow is pre-rendered and particles are capped ([12-art-and-audio.md](12-art-and-audio.md)).
6. **Done means it runs in a real browser.** A desktop run doesn't count.

## Edge cases
- A library or file type not listed here: assume it may not work in pygbag until a browser build proves it does.

## Open
None.

## How to extend
A new constraint goes here with the reason it exists. A change to a locked value needs the Director's go-ahead and a row in [91-decision-log.md](91-decision-log.md).
