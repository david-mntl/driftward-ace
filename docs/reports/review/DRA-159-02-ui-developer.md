Status: reviewed
Created by: implementation-reviewer

1. **Task:** review the UI Developer's `MuteIconLook` and `MuteIconView` (task DRA-159-02, contract `docs/contracts/systems/mute-icon.md`), asked by the `/implement` skill.

2. **Delivered:** this report, `docs/reports/review/DRA-159-02-ui-developer.md`. Code reviewed: `game/ui/mute_icon.py`.

3. **Checks:** read by eye, nothing run.
   - `MuteIconLook(margin, size)` is a frozen dataclass. `MuteIconView.__init__(look, image)` and `draw(window, muted)` match the contract Interface name for name, type for type, and in return value.
   - `draw` returns early on `muted` False. Otherwise it makes one blit at `(window_w - margin - size, window_h - margin - size)`. That puts the picture's bottom-right corner `margin` px from the right and bottom edges (rules 6 and 18).
   - The module imports only `logging`, `dataclasses` and `pygame`. It imports no `app` or `core`, reads no key or file, holds no state, does no scaling, and has no literal number, color or text. The only change to anything is the blit onto the passed-in surface.
   - The implementer's claims match the file. The acceptance script is one the code can pass. The `log` line follows the `game/ui/` module habit (40 of 40 modules have it).

4. **Assumptions:** none of mine. I took the implementer's `lint` and `typecheck` results as claimed. QA runs them.

5. **Documentation differences:** None.

6. **Next:** QA Engineer, on this report. The view is not wired anywhere yet. The loader, the picture and the frame-loop draw call belong to DRA-159-01 and the Integration Engineer.

7. **Status:** done.

## Findings
None.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- `draw(window, False)` leaves every window pixel unchanged.
- `draw(window, True)` changes only the `size` x `size` rect that sits `margin` px from the right and bottom edges. Try a window size other than 856 x 518.
- A stand-in picture with a transparent region keeps the window pixels under that region. A second `draw(window, True)` gives the same pixels.
- Once wired, the icon should be drawn before the dim, so pause and game over darken it.
