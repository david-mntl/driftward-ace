"""The app side of the drifters: the tuning file checks and one loader per drifter with its own.

Importing anything under `app.drifters` imports every drifter's tuning module, so each loader
registers. A new drifter adds one import line here.
"""

from app.drifters import chain_lightning_tuning as chain_lightning_tuning
from app.drifters import coin_tuning as coin_tuning
from app.drifters import fireball_tuning as fireball_tuning
from app.drifters import floating_island_tuning as floating_island_tuning
from app.drifters import planet_tuning as planet_tuning
from app.drifters import satellite_tuning as satellite_tuning
from app.drifters import ufo_tuning as ufo_tuning
