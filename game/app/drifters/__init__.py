"""The app side of the drifters: the tuning file checks and one loader per drifter with its own.

Importing anything under `app.drifters` imports every drifter's tuning module, so each loader
registers. A new drifter adds one import line here.
"""
