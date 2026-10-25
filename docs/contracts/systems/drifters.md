# Drifters: base, hitboxes, levels, spawner, every drifter and their views
Version: 10
Status: frozen
Features: DRA-29, DRA-39, DRA-47, DRA-56, DRA-62, DRA-76, DRA-86, DRA-96, DRA-104, DRA-111, DRA-117
Created by: architect

## Purpose
Every drifter in the game, hazards, pickups and blockers, is built on one shared base. The contract is split into parts: open only the one you need.

## Parts
<!-- parts:begin -->
| Part | Holds | Read when | Size |
|---|---|---|---|
| [shared/base-interface](drifters/shared/base-interface.md) | Interface | you write or review code in `game/core/drifters/base.py`. | 15.5 KB |
| [shared/base](drifters/shared/base.md) | Purpose, Diagram, Rules | you change what every drifter shares: phases, warning, hitbox, start, re-hit. | 25.9 KB |
| [shared/collision](drifters/shared/collision.md) | Interface, Rules | you change hitbox shapes, the overlap test or the push-out. | 12.0 KB |
| [shared/rationale](drifters/shared/rationale.md) | Rationale | you ask why a shared rule is the way it is. A drifter's own why is in its `rationale` part. | 13.8 KB |
| [shared/spawner-registry-tuning](drifters/shared/spawner-registry-tuning.md) | Diagram, Interface, Rules | you change levels, the registry, the spawner or the shared tuning, or add a drifter. | 19.2 KB |
| [shared/views](drifters/shared/views.md) | Diagram, Interface, Presentation | you change how drifters are drawn: view registry, brightness, entry warning, shapes. | 17.6 KB |
| [chain-lightning/core](drifters/chain-lightning/core.md) | Diagram, Interface, Rules | you change how the chain lightning behaves (`chain_lightning.py`). | 17.8 KB |
| [chain-lightning/rationale](drifters/chain-lightning/rationale.md) | Rationale | you ask why the chain lightning is built the way it is. | 4.1 KB |
| [chain-lightning/tuning](drifters/chain-lightning/tuning.md) | Rules | you change the chain lightning's tuning file or its checks. | 1.0 KB |
| [chain-lightning/view](drifters/chain-lightning/view.md) | Interface, Presentation | you change how the chain lightning looks. | 3.5 KB |
| [coin/core](drifters/coin/core.md) | Diagram, Interface, Rules | you change how the coin behaves (`coin.py`). | 11.2 KB |
| [coin/rationale](drifters/coin/rationale.md) | Rationale | you ask why the coin is built the way it is. | 2.3 KB |
| [coin/tuning](drifters/coin/tuning.md) | Rules | you change the coin's tuning file or its checks. | 1.4 KB |
| [coin/view](drifters/coin/view.md) | Interface, Presentation | you change how the coin looks. | 4.4 KB |
| [electric-ball/core](drifters/electric-ball/core.md) | Diagram, Interface, Rules | you change how the electric ball behaves (`electric_ball.py`) or its tuning file. | 19.3 KB |
| [electric-ball/rationale](drifters/electric-ball/rationale.md) | Rationale | you ask why the electric ball is built the way it is. | 4.5 KB |
| [electric-ball/view](drifters/electric-ball/view.md) | Interface, Presentation | you change how the electric ball looks. | 5.9 KB |
| [fireball/core](drifters/fireball/core.md) | Diagram, Interface, Rules | you change how the fireball behaves (`fireball.py`). | 11.2 KB |
| [fireball/rationale](drifters/fireball/rationale.md) | Rationale | you ask why the fireball is built the way it is. | 3.2 KB |
| [fireball/tuning](drifters/fireball/tuning.md) | Rules | you change the fireball's tuning file or its checks. | 0.9 KB |
| [fireball/view](drifters/fireball/view.md) | Interface, Presentation | you change how the fireball looks. | 2.5 KB |
| [floating-island/core](drifters/floating-island/core.md) | Diagram, Interface, Rules | you change how the floating island behaves (`floating_island.py`). | 12.5 KB |
| [floating-island/rationale](drifters/floating-island/rationale.md) | Rationale | you ask why the floating island is built the way it is. | 2.1 KB |
| [floating-island/tuning](drifters/floating-island/tuning.md) | Rules | you change the floating island's tuning file or its checks. | 1.3 KB |
| [floating-island/view](drifters/floating-island/view.md) | Interface, Presentation | you change how the floating island looks. | 4.3 KB |
| [meteorite/core](drifters/meteorite/core.md) | Diagram, Interface, Rules | you change how the meteorite behaves (`meteorite.py`). | 3.2 KB |
| [meteorite/rationale](drifters/meteorite/rationale.md) | Rationale | you ask why the meteorite is built the way it is. | 0.4 KB |
| [meteorite/view](drifters/meteorite/view.md) | Interface, Presentation | you change how the meteorite looks. | 1.0 KB |
| [old-names](drifters/old-names.md) | Old names | a citation names a section of the old single file, such as "Rules, Satellite". | 4.7 KB |
| [planet/core](drifters/planet/core.md) | Diagram, Interface, Rules | you change how the planet behaves (`planet.py`). | 14.9 KB |
| [planet/rationale](drifters/planet/rationale.md) | Rationale | you ask why the planet is built the way it is. | 3.5 KB |
| [planet/tuning](drifters/planet/tuning.md) | Rules | you change the planet's tuning file or its checks. | 1.5 KB |
| [planet/view](drifters/planet/view.md) | Interface, Presentation | you change how the planet looks. | 3.9 KB |
| [satellite/core](drifters/satellite/core.md) | Diagram, Interface, Rules | you change how the satellite behaves (`satellite.py`). | 6.3 KB |
| [satellite/rationale](drifters/satellite/rationale.md) | Rationale | you ask why the satellite is built the way it is. | 1.3 KB |
| [satellite/view](drifters/satellite/view.md) | Interface, Presentation | you change how the satellite looks. | 1.7 KB |
| [ufo/core](drifters/ufo/core.md) | Diagram, Interface, Rules | you change how the UFO behaves (`ufo.py`). | 20.5 KB |
| [ufo/rationale](drifters/ufo/rationale.md) | Rationale | you ask why the UFO is built the way it is. | 5.7 KB |
| [ufo/tuning](drifters/ufo/tuning.md) | Rules | you change the UFO's tuning file or its checks. | 2.8 KB |
| [ufo/view](drifters/ufo/view.md) | Interface, Presentation | you change how the UFO looks. | 2.3 KB |
<!-- parts:end -->
