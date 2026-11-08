import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL.parents[1] / "game"))
sys.path.insert(0, str(TOOL))
