"""Drifters on the field: the shared base, tuning records, registry, spawner and each drifter.

Importing anything under `core.drifters` imports every drifter module, so each class registers.
A new drifter adds one import line here.
"""

from core.drifters import chain_lightning as chain_lightning
from core.drifters import coin as coin
from core.drifters import fireball as fireball
from core.drifters import floating_island as floating_island
from core.drifters import meteorite as meteorite
from core.drifters import planet as planet
from core.drifters import satellite as satellite
from core.drifters import ufo as ufo
