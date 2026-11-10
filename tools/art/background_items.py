"""Cut the middle layer's wrecks and debris out of the Director's sheet.

Reads staging/art-inbox/background-items.png (a 3 x 2 sheet of dark wrecks on transparency) and
writes game/assets/bg_item_0.png .. bg_item_5.png, in reading order (left to right, top row
first). Each item is cropped to its own bounds, then shrunk so its longest side is ITEM_PX, the
size of the shipped planets (bg_planet_*.png, 77 to 105 px). Overwrites those files.
Run from the repo root:
    python3 tools/art/background_items.py
"""

from pathlib import Path

import numpy as np
from PIL import Image

SHEET = Path("staging/art-inbox/background-items.png")
ASSETS = Path("game/assets")
COLUMNS = 3
ROWS = 2
ITEM_PX = 100
"""Longest side of a finished item, px. The shipped planets are about this big."""
INK = 8
"""Alpha at or under this is empty space, 0..255. Keeps faint haze out of the crop."""
GAP_SHARE = 0.05
"""A gap between items is a stretch of empty columns (or rows) at least this share of the sheet."""


def gaps(empty: np.ndarray, count: int) -> list[int]:
    """Return the `count - 1` cut positions, each in the middle of the widest empty stretch."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, is_empty in enumerate(empty):
        if is_empty and start is None:
            start = index
        if not is_empty and start is not None:
            runs.append((index - start, start))
            start = None
    inside: list[tuple[int, int]] = [run for run in runs if run[1] > 0]
    widest: list[tuple[int, int]] = sorted(inside, reverse=True)[: count - 1]
    return sorted(start + length // 2 for length, start in widest)


def main() -> None:
    """Split the sheet, crop and shrink each item, and write the files."""
    sheet: Image.Image = Image.open(SHEET).convert("RGBA")
    ink: np.ndarray = np.asarray(sheet)[:, :, 3] > INK
    cuts_x: list[int] = [0, *gaps(~ink.any(axis=0), COLUMNS), sheet.width]
    cuts_y: list[int] = [0, *gaps(~ink.any(axis=1), ROWS), sheet.height]
    index: int = 0
    for row in range(ROWS):
        for column in range(COLUMNS):
            box: tuple[int, int, int, int] = (
                cuts_x[column],
                cuts_y[row],
                cuts_x[column + 1],
                cuts_y[row + 1],
            )
            cell: Image.Image = sheet.crop(box)
            mask: Image.Image = Image.fromarray(
                (np.asarray(cell)[:, :, 3] > INK).astype(np.uint8) * 255
            )
            bounds: tuple[int, int, int, int] | None = mask.getbbox()
            if bounds is None:
                raise ValueError(f"{SHEET}: cell {row},{column} is empty")
            item: Image.Image = cell.crop(bounds)
            shrink: float = ITEM_PX / max(item.size)
            size: tuple[int, int] = (
                round(item.width * shrink),
                round(item.height * shrink),
            )
            item = item.resize(size, Image.Resampling.LANCZOS)
            item.save(ASSETS / f"bg_item_{index}.png")
            print(f"bg_item_{index}.png {item.size} from {bounds} in cell {box}")
            index += 1


if __name__ == "__main__":
    main()
