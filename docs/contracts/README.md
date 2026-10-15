# contracts

The Architect's folder. It holds two different things: **specs** for the code, organized by system, and **tasks**, organized by feature.

```
contracts/
  CHANGELOG.md                 every version change, by feature
  systems/                     one spec per part of the code, always current
  schemas/                     JSON schemas for data files
  <feature-id>/tasks/          the tickets for that feature
    <feature-id>-<nn>-<assignee>.md
```

## Specs (`systems/`)

A spec describes one part of the code as it is now: its interface, rules, what the player sees, and why. There is one file per system, never one per feature.

When a later feature changes a system, it edits that system's spec:
1. The Architect sets the spec back to `Status: draft` and lists the files that depend on it under **Impact**.
2. The change goes through build, review, QA and integration like any other.
3. At close-out the spec goes back to `Status: frozen`, with `Version` one higher.

The `Features:` line lists every feature that shaped the spec. "Frozen" doesn't mean it never changes. It means it only changes through those steps.

## Tasks (`<feature-id>/tasks/`)

A task is one ticket: one assignee, one folder it may write to, one check the Director can run. Its `Contract:` line points at the spec section it builds. It is closed at close-out and never edited after that.

The task ID shows its feature and order (`DRA-13-01`). The Linear key is a separate team-wide number (`DRA-14`). The task's `Linear:` line links the two.

## History

- **What changed when:** `CHANGELOG.md` has one entry per feature, with every spec it changed, from which version to which.
- **What a spec said earlier:** `git log --follow docs/contracts/systems/<system>.md` (from the repo root) shows every version, back to the feature that created it.
- **Old paths:** before 2026-10-12, specs lived in the folder of the feature that created them, for example `DRA-6/DRA-6-ship.md`. Closed tasks and reports still use those paths. The CHANGELOG entry "Contracts moved to systems/" maps them to the new ones.
