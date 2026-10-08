# Tests

Lint, format and tests for Driftward Ace. One script runs all of it.

```sh
game/tests/check.sh          # everything
game/tests/check.sh lint     # ruff check + format check
game/tests/check.sh core     # tests for game/core
game/tests/check.sh ui       # tests for game/ui
game/tests/check.sh fix      # auto-fix lint and format
```

The last line is `QA: pass` or `QA: fail (<steps>)`. It needs the packages in `game/requirements.txt` (the devcontainer has them). Set `PYTHON=/path/to/python` to use another interpreter.

Agents: read `CONTEXT.md`.
