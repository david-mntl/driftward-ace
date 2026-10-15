# scripts/

Project tools that run outside the game. Nothing here ships, and the pygbag build never sees it.

- Owner: the Director and the main session. No crew agent writes here.
- Layout: short shell wrappers in `scripts/`, the Python behind them in `scripts/python/`.
- Python 3 standard library only. No installs.
- Each script opens with a comment or docstring: what it does, what it reads, what it writes, and how to run it.
- A script is read-only unless its docstring names what it writes.

## Commands
- `scripts/contracts.sh`: what's in progress and ready to close out. `verify` checks headers, task pointers and INDEX.md. `index` rebuilds INDEX.md.
- `scripts/close-out.sh [FEATURE-ID]`: without an id, lists features ready to close out. With one, shows what close-out would do and writes nothing. With `--write --summary "..."`, it freezes the feature's contracts, sets its tasks done, appends the CHANGELOG entry and rebuilds INDEX.md. When open findings or Observations are listed, it also needs `--accept-open`, given only after the Director decides them.
- `scripts/tokens.sh`: token use and cost per ticket and agent. Read-only.

## After a close-out
When `scripts/close-out.sh <id> --write` succeeds, it prints the feature's Linear sub-issue keys. Propose to the Director to set them to Done, then do it with the Linear tools once the Director says yes.
