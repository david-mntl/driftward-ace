"""Assemble out/perf/FINDINGS.md from the report files and the fixed text in findings_template.md.

Every {{NAME}} in the template is replaced by one piece of a report. The template holds the wording and
this script holds only where each number comes from, so a re-run changes the numbers and leaves the text alone.

usage: python build_findings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the adversary folder: cli, paths

import cli
from paths import OUT_DIR

PERF_DIR = OUT_DIR / "perf"
TEMPLATE = Path(__file__).resolve().parent / "findings_template.md"
FINDINGS = PERF_DIR / "FINDINGS.md"

# {{NAME}}: (report file, the "## " heading whose section is pasted in).
SECTIONS = {
    "LEVELS": ("report_levels.md", "## Per level"),
    "WAVES": ("report_levels.md", "## Per wave"),
    "WORST": ("report_levels.md", "## Worst 15"),
    "PARTS": ("report_levels.md", "## Mean ms per frame"),
    "TYPES": ("report_levels.md", "## Drifter draw cost"),
    "MARG": ("report_levels.md", "## Marginal cost"),
    "TAIL_LEVELS": ("report_tails.md", "## Per level"),
    "TAIL_WAVES": ("report_tails.md", "## Per wave"),
    "TAIL_WORST": ("report_tails.md", "## Worst 15"),
}

# {{NAME}}: a whole file, pasted as it is.
WHOLE_FILES = {
    "TREND": "tail_trend.md",
    "BROWSER": "browser/report.txt",
}

# {{NAME}}: the top-15 profile of one soak run, from prof_<label>/top15.txt.
PROFILES = {
    "PW11": "pw11",
    "PW10": "pw10",
    "PW15": "pw15",
    "PW4": "pw4",
    "SWEEP": "prof",
}

EXTRA = "findings_extra.md"  # optional: findings added by hand after a run


def read_report(name):
    """Return the text of out/perf/<name>, or stop with the script that writes it missing."""
    path = PERF_DIR / name
    if not path.exists():
        sys.exit(f"missing {path}: run the perf reports first (see perf/README.md)")
    return path.read_text()


def section(text, title, source, stop="\n## "):
    """Return the part of `text` from the heading `title` up to the next "## " heading."""
    start = text.find(title)
    if start < 0:
        sys.exit(f"{source} has no '{title}' section: re-run the report that writes it")
    end = text.find(stop, start + len(title))
    return text[start : end if end > 0 else None].rstrip()


def pieces():
    """Return {NAME: text} for every placeholder in the template."""
    found = {name: section(read_report(file), title, file) for name, (file, title) in SECTIONS.items()}
    found.update({name: read_report(file) for name, file in WHOLE_FILES.items()})
    found.update({name: read_report(f"prof_{label}/top15.txt") for name, label in PROFILES.items()})
    found["EXTRA"] = (PERF_DIR / EXTRA).read_text() if (PERF_DIR / EXTRA).exists() else ""
    return found


def main():
    cli.parser(__doc__).parse_args()
    text = TEMPLATE.read_text()
    for name, piece in pieces().items():
        text = text.replace("{{" + name + "}}", piece)
    FINDINGS.write_text(text)
    print("wrote FINDINGS.md", len(text))


if __name__ == "__main__":
    main()
