"""Views for drifters on the field: the view registry, the entry warning and each drifter's look.

Importing anything under `ui.drifters` imports every view module, so each view registers.
A new drifter adds one import line here.
"""

from ui.drifters import meteorite_view as meteorite_view
