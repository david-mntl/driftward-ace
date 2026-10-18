"""Views for drifters on the field: the view registry, the entry warning and each drifter's look.

Importing anything under `ui.drifters` imports every view module, so each view registers.
A new drifter adds one import line here.
"""

from ui.drifters import chain_lightning_view as chain_lightning_view
from ui.drifters import fireball_view as fireball_view
from ui.drifters import meteorite_view as meteorite_view
from ui.drifters import satellite_view as satellite_view
