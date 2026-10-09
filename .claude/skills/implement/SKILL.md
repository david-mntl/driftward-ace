---
name: implement
description: Build one feature from the Architect's task files. Runs each task's assignee (Gameplay Implementer, UI Developer or QA Engineer), then the Implementation Reviewer, QA Engineer and Integration Engineer. The Director starts it with /implement <feature-id>.
argument-hint: <feature-id>
disable-model-invocation: true
---

Build feature `$ARGUMENTS`. You only start agents and read their reports. Never write or edit a file yourself. Don't touch task files, contracts or Linear.

## 1. Find the tasks
List `docs/contracts/$ARGUMENTS/tasks/$ARGUMENTS-*.md` with `Status: open`. Keep the ones with `Assignee: gameplay-implementer`, `Assignee: ui-developer` or `Assignee: qa-engineer`. Run them in order of `<nn>`.

Skip any other assignee, such as `art-audio-engineer`. List those tasks in the final message.

If no task is left to run, stop and tell the Director.

## 2. Run each task through the chain
For each task file, by its `Assignee:` line. Every report has the same base name as the task file. The QA report is always `docs/reports/qa/<base name>.md`. If it already exists, the task has run before: read its line 1 first and don't start the task's agent again unless the verdict is `fail`:
- `Verdict: pass`: skip the task, next task.
- `Verdict: fail`: run **Fix rounds** below.
- `Verdict: blocked`, or no report: stop.

### Gameplay or UI task
Its implementation report:
- `gameplay-implementer`: `docs/reports/implementation/gameplay/<base name>.md`
- `ui-developer`: `docs/reports/implementation/ui/<base name>.md`

1. **Implement.** Start the task's agent with: "Task mode. Work only on `<task file path>`." Then read line 1 of its implementation report.
   - `Status: ready-for-review`: go on.
   - `Status: blocked`, or no report: stop.
2. **Review.** Start `implementation-reviewer` with the implementation report path. Then read line 1 of `docs/reports/review/<base name>.md`.
   - `Status: reviewed`: go on.
   - `Status: blocked`, or no report: stop.
3. **QA.** Start `qa-engineer` with: "Verify mode. Implementation report: `<path>`." Then read the QA report's line 1.

### QA test task
1. **Test.** Start `qa-engineer` with: "Test task mode. Work only on `<task file path>`." Then read the QA report's line 1.

### Fix rounds
1. Read **Bugs** in the QA report. Each open bug names its owner agent.
2. Start each owner once with: "Fix mode. Bug report: `<QA report path>`." Only `gameplay-implementer` and `ui-developer` run Fix mode. If a bug names any other owner, stop.
3. Start `qa-engineer` with: "Re-test mode. QA report: `<QA report path>`." Then read line 1 again.
4. After 2 failed fix rounds, stop.

## 3. Integrate
When every task has passed QA, start `integration-engineer` once with: "Integrate mode. Feature: `$ARGUMENTS`." Then read line 1 of `docs/reports/integration/$ARGUMENTS.md`. On `Verdict: pass` it starts the Architect's close-out itself. Don't start the Architect yourself.

## When to stop
Stop the chain and tell the Director when:
- an agent reports `blocked`, or a pending documentation difference
- the review report is `Status: blocked`
- the integration report is `Verdict: fail` or `Verdict: blocked`
- QA still fails after 2 fix rounds
- a bug belongs to an agent without a Fix mode

Say which task you stopped on, at which step, and the report path to read.

## Final message
Keep it short:
- each task, and its implementation, review and QA report paths
- the integration report path, its line 1, and how to open the build in the browser
- whether the Architect close-out was started, or is waiting on the Director's answer about an observation
- anything an agent listed as unsure, or any open review finding
