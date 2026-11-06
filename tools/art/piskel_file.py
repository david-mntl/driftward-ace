"""Write a Piskel file (.piskel, model version 2) from PIL frames.

Format taken from the Piskel source (Serializer.js, Deserializer.js): one JSON
object, {"modelVersion": 2, "piskel": {...}}. Each layer is a JSON string
inside piskel.layers, with name, opacity, frameCount and one chunk. The chunk
holds a layout, [[0], [1], ...], and base64PNG, a data URL of the layer's
frames side by side in one row. Every frame in every layer has the same size.

Usage: python3 tools/art/piskel_file.py <out.piskel> <name> <layer_name>=<png>[:<frame_count>] ...

A PNG with :<n> is a horizontal strip cut into n equal frames. Without it the
PNG is one frame. Layers are listed bottom first, as Piskel stores them.
"""

from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

MODEL_VERSION = 2


def _data_url(strip: Image.Image) -> str:
    buf = io.BytesIO()
    strip.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def write_piskel(path, name, layers, fps=12):
    """Write a Piskel file at path.

    layers is a list of (layer_name, [PIL.Image frames]), bottom layer first.
    All frames in all layers must be the same size. Returns the path written.
    """
    if not layers:
        raise ValueError("write_piskel needs at least one layer")
    width, height = layers[0][1][0].size
    count = len(layers[0][1])

    serialized = []
    for layer_name, frames in layers:
        if len(frames) != count:
            raise ValueError(f"layer {layer_name!r} has {len(frames)} frames, expected {count}")
        strip = Image.new("RGBA", (width * count, height), (0, 0, 0, 0))
        for i, frame in enumerate(frames):
            if frame.size != (width, height):
                raise ValueError(
                    f"layer {layer_name!r} frame {i} is {frame.size}, expected {(width, height)}"
                )
            strip.paste(frame.convert("RGBA"), (width * i, 0))
        serialized.append(
            json.dumps(
                {
                    "name": layer_name,
                    "opacity": 1,
                    "frameCount": count,
                    "chunks": [
                        {
                            "layout": [[i] for i in range(count)],
                            "base64PNG": _data_url(strip),
                        }
                    ],
                }
            )
        )

    doc = {
        "modelVersion": MODEL_VERSION,
        "piskel": {
            "name": name,
            "description": "",
            "fps": fps,
            "height": height,
            "width": width,
            "layers": serialized,
            "hiddenFrames": [],
        },
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc))
    return out


def _load_layer(spec: str):
    layer_name, _, rest = spec.partition("=")
    if not layer_name or not rest:
        raise SystemExit(f"bad layer spec {spec!r}, want <layer_name>=<png>[:<frame_count>]")
    png, sep, n = rest.rpartition(":")
    if not sep or not n.isdigit():
        png, n = rest, "1"
    sheet = Image.open(png).convert("RGBA")
    count = int(n)
    if count < 1 or sheet.width % count:
        raise SystemExit(f"{png}: width {sheet.width} does not split into {count} frames")
    fw = sheet.width // count
    return layer_name, [sheet.crop((fw * i, 0, fw * (i + 1), sheet.height)) for i in range(count)]


def main(argv):
    if len(argv) < 4:
        raise SystemExit(__doc__.split("Usage: ")[1].splitlines()[0])
    out, name, specs = argv[1], argv[2], argv[3:]
    path = write_piskel(out, name, [_load_layer(s) for s in specs])
    print(f"wrote {path}")


if __name__ == "__main__":
    main(sys.argv)
