"""A tiny scenario runner shared by a2_flow_targeted.py and b2_rehit_graze.py.

A scenario is a function that returns a list of messages. A message starting with "INFO" is a note; any
other message is a failure. A scenario that raises counts as a failure too.
"""

import traceback

import cli
from paths import out_dir

EXCEPTION_CHARS = 400  # how much of a traceback a failure keeps


class Suite:
    """Scenarios registered with `@suite.case(name)`, run in order by `main()`."""

    def __init__(self, report_file):
        self.report_file = report_file  # written to out/flow_collision/
        self.cases = []

    def case(self, name):
        """Register a scenario. Nothing runs until `run()`, so importing a module for its helpers is cheap."""

        def register(fn):
            self.cases.append((name, fn))
            return fn

        return register

    def run(self):
        """Run every scenario in order; return [(name, messages)]."""
        results = []
        for name, fn in self.cases:
            try:
                messages = fn() or []
            except Exception:
                messages = ["EXC " + traceback.format_exc()[-EXCEPTION_CHARS:]]
            results.append((name, messages))
        return results

    def main(self, doc):
        """Run, print PASS or FAIL per scenario, and write the failures to the report file."""
        cli.parser(doc).parse_args()
        failed = 0
        lines = []
        for name, messages in self.run():
            problems = [m for m in messages if not m.startswith("INFO")]
            notes = [m for m in messages if m.startswith("INFO")]
            print(("FAIL " if problems else "PASS ") + name + (" | " + "; ".join(notes) if notes else ""))
            if problems:
                failed += 1
                lines.append(name + ":\n  " + "\n  ".join(problems))
        (out_dir("flow_collision") / self.report_file).write_text("\n".join(lines) or "all pass\n")
        print("failures:", failed)
