#!/usr/bin/env python3
"""One-time contract splitter for docs/contracts/systems/.

Cuts a big contract into a hub plus part files, split by reader, and removes
its history blocks (Impact sections, the Purpose "Who builds what" list). It
changes no other word. It reads the contract and the repo's tracked text
files; it writes only with --write, and then only inside docs/contracts/:

- systems/<name>.md becomes the hub: the header, a one-sentence Purpose, the
  part table (kept current by `contracts.py index`) and the old-name map,
- systems/<name>/... are the part files,
- one entry is appended to CHANGELOG.md and INDEX.md is rebuilt.

Version and Status are not touched. It runs only on the Director's go: the
Director and the main session run it, no agent does.

The record. `--write` also appends to docs/contracts/splits.json the git blob
hash of the old file and of every file it wrote. `contracts.py verify` reads it
and runs the no-line-lost proof again from those git objects, so the proof
holds after the parts have been edited. It needs the history, so a CI checkout
must be complete (fetch-depth 0).

Proof, built in. Before it writes, the script checks that every non-blank
line of the old file appears exactly once across the new files, minus the
dropped blocks (listed in the report) and minus the lines it adds itself
(listed in the report): titles, `Part of:` and `Read when:` lines, the hub
tables, and the heading and fence lines it repeats when it cuts inside a
code block. After writing, it reads the files back and checks again. Top-level
`## ` headings are left out of both sides. It refuses to write when the
contract has uncommitted changes, so git always holds the old file.

Usage (scripts/split-contract.sh calls this):
  split_contract.py split drifters             dry-run report: what goes where
  split_contract.py split drifters --detail    the same, with every placement
  split_contract.py split drifters --write     apply it
  split_contract.py drop-impact run ship ...   dry-run: drop only the Impact section
  split_contract.py drop-impact run ship --write

Standard library only.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import contracts as ct

SECTION_ORDER = ["Purpose", "Diagram", "Interface", "Presentation", "Rules", "Rationale"]
TICKET = ct.TICKET_ID

# The drifters: key, name in prose, module in game/core/drifters/, regex that finds it in prose.
DRIFTERS = {
    "meteorite": ("meteorite", "meteorite", r"meteorites?"),
    "satellite": ("satellite", "satellite", r"satellites?"),
    "chain-lightning": ("chain lightning", "chain_lightning", r"chain[ _]lightnings?|ChainLightning"),
    "fireball": ("fireball", "fireball", r"fireballs?"),
    "coin": ("coin", "coin", r"coins?"),
    "floating-island": ("floating island", "floating_island", r"floating[ _]islands?|FloatingIsland|islands?"),
    "planet": ("planet", "planet", r"planets?"),
    "ufo": ("UFO", "ufo", r"ufos?"),
}
DRIFTER_BY_WORD = {name.lower(): key for key, (name, _m, _r) in DRIFTERS.items()} | {"island": "floating-island"}
DRIFTER_BY_MODULE = {module: key for key, (_n, module, _r) in DRIFTERS.items()}
DRIFTER_WORDS = {key: re.compile(rf"\b(?:{rx})\b", re.I) for key, (_n, _m, rx) in DRIFTERS.items()}
DRIFTER_OPENER = r"Meteorite|Satellite|Chain lightning|Fireball|Coin|Floating island|Island|Planet|UFO"

BASE, SPAWN, COLLISION, VIEWS = "shared/base", "shared/spawner-registry-tuning", "shared/collision", "shared/views"
# Beyond the layout the Director gave (the base alone came to 58 KB): the base's Interface gets its
# own shared part, and the Rationale of every owner gets a `rationale` part, so a core part holds
# only what to build. Proposed in the dry-run.
BASE_IFACE, RATIONALE = "shared/base-interface", "shared/rationale"
SHARED_LABEL = {
    BASE_IFACE: "the base, interface",
    RATIONALE: "rationale of the shared rules",
    BASE: "the base",
    SPAWN: "levels, registry, spawner and tuning files",
    COLLISION: "collision",
    VIEWS: "views and the entry warning",
}
SHARED_WHEN = {
    BASE_IFACE: "you write or review code in `game/core/drifters/base.py`.",
    RATIONALE: "you ask why a shared rule is the way it is. A drifter's own why is in its `rationale` part.",
    BASE: "you change what every drifter shares: phases, warning, hitbox, start, re-hit.",
    SPAWN: "you change levels, the registry, the spawner or the shared tuning, or add a drifter.",
    COLLISION: "you change hitbox shapes, the overlap test or the push-out.",
    VIEWS: "you change how drifters are drawn: view registry, brightness, entry warning, shapes.",
}


def drifter_info(key: str) -> tuple[str, str]:
    if key in SHARED_LABEL:
        return SHARED_LABEL[key], SHARED_WHEN[key]
    d, kind = key.split("/")
    name, module, _rx = DRIFTERS[d]
    return f"the {name}, {kind}", {
        "core": f"you change how the {name} behaves (`{module}.py`).",
        "view": f"you change how the {name} looks.",
        "tuning": f"you change the {name}'s tuning file or its checks.",
        "rationale": f"you ask why the {name} is built the way it is.",
    }[kind]


MANIFEST = "docs/contracts/splits.json"


# The record of a split, and the proof read back from git


def git_text(root: Path, *args: str, stdin: str | None = None) -> str | None:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, input=stdin)
    return done.stdout if done.returncode == 0 else None


def blob_sha(root: Path, text: str) -> str:
    return (git_text(root, "hash-object", "--stdin", stdin=text) or "").strip()


def dropped_for(drops: list[str], old_text: str) -> list[str]:
    """The only blocks a split may drop, found again in the old text: Impact sections, and the Purpose task list."""
    doc = parse_doc(old_text)
    lines: list[str] = []
    if "impact" in drops:
        lines += [ln for title, body in doc.sections.items() if title.startswith("Impact") for ln in ["## " + title] + body]
    if "who-builds" in drops:
        lines += cut_who_builds(doc.sections.get("Purpose", []))[1]
    return lines


def record_split(root: Path, name: str, kind: str, old_text: str, new_files: dict[str, Path], drops: list[str]) -> None:
    """Append one record to the manifest. new_files: path in the repo -> file on disk, as written."""
    p = ct.Paths(root)
    path = root / MANIFEST
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    records.append({
        "contract": name,
        "kind": kind,
        "drops": drops,
        "date": datetime.date.today().isoformat(),
        "old": blob_sha(root, old_text),
        "new": {str(f.relative_to(root)): blob_sha(root, f.read_text(encoding="utf-8")) for f in new_files.values()},
    })
    ct.safe_write(p, path, json.dumps(records, indent=2) + "\n")


def check_manifest(root: Path) -> tuple[list[str], list[str]]:
    """Prove again, for every recorded split, that no line was lost. Returns (problems, info lines)."""
    path = root / MANIFEST
    if not path.exists():
        return [], []
    problems, infos = [], []
    for rec in json.loads(path.read_text(encoding="utf-8")):
        name = rec["contract"]
        old = git_text(root, "cat-file", "-p", rec["old"])
        if old is None:
            problems.append(f"{MANIFEST}: the old {name} file ({rec['old'][:10]}) is not in this clone's history, so the no-line-lost proof cannot run (shallow checkout? fetch the full history)")
            continue
        new = collections.Counter()
        missing = False
        for file, sha in rec["new"].items():
            text = git_text(root, "cat-file", "-p", sha)
            if text is None and (root / file).exists() and blob_sha(root, (root / file).read_text(encoding="utf-8")) == sha:
                text = (root / file).read_text(encoding="utf-8")
            if text is None:
                problems.append(f"{MANIFEST}: {file} ({sha[:10]}) is not in this clone, so the proof for {name} cannot run")
                missing = True
                break
            new.update(content_lines(lines_of(text)))
        if missing:
            continue
        want = collections.Counter(content_lines(lines_of(old)))
        drops = rec.get("drops") or (["impact", "who-builds"] if rec["kind"] == "split" else ["impact"])
        want.subtract(collections.Counter(content_lines(dropped_for(drops, old))))
        lost = (+want) - new
        for ln, n in lost.items():
            problems.append(f"{name}: a line of the old file was lost in the {rec['kind']} of {rec['date']}: {ln[:90]!r} x{n}")
        if not lost:
            infos.append(f"split proof, {name}: all {sum((+want).values())} non-dropped lines of the old file are in the split files")
    return problems, infos


# Reading a contract


def lines_of(text: str) -> list[str]:
    return text.split("\n")


def content_lines(lines: list[str]) -> list[str]:
    """Non-blank lines, without top-level `## ` headings: what the proof counts."""
    mask = ct.fenced_mask(lines)
    return [ln for ln, f in zip(lines, mask) if ln.strip() and not (not f and ln.startswith("## "))]


def trim(lines: list[str]) -> list[str]:
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


@dataclass
class Doc:
    head: list[str]
    sections: dict[str, list[str]]


def parse_doc(text: str) -> Doc:
    lines = lines_of(text)
    mask = ct.fenced_mask(lines)
    marks = [(i, ln[3:].strip()) for i, (ln, f) in enumerate(zip(lines, mask)) if not f and ln.startswith("## ")]
    head = lines[: marks[0][0]]
    sections: dict[str, list[str]] = {}
    for n, (i, title) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(lines)
        sections[title] = lines[i + 1 : end]
    return Doc(head=trim(head), sections=sections)


@dataclass
class Unit:
    """A run of lines that start at a top-level line and all go to one place."""

    key: str | None
    name: str
    lines: list[str]


def split_units(body: list[str], classify) -> list[Unit]:
    """Cut at every top-level line (col 0, outside a fence) that `classify` recognizes.

    classify(line) returns (part key, old name) or None. Everything else, blank
    lines, indented lines, fenced lines, stays with the unit before it.
    """
    mask = ct.fenced_mask(body)
    units = [Unit(None, "", [])]
    for ln, f in zip(body, mask):
        hit = None if f or not ln.strip() or ln[0] in " \t" else classify(ln)
        if hit:
            units.append(Unit(hit[0], hit[1], [ln]))
        else:
            units[-1].lines.append(ln)
    return [u for u in units if any(ln.strip() for ln in u.lines)]


def merge_adjacent(units: list[Unit]) -> list[Unit]:
    """Join neighbours that go to the same part, so a list or a run of notes stays together."""
    out: list[Unit] = []
    for u in units:
        if out and out[-1].key == u.key:
            out[-1].lines += u.lines
            if u.name and u.name not in out[-1].name.split("; "):
                out[-1].name += "; " + u.name
        else:
            out.append(Unit(u.key, u.name, list(u.lines)))
    return out


def drifter_in(text: str) -> str | None:
    """The one drifter a text names, or None when it names none or several."""
    hits = [key for key, rx in DRIFTER_WORDS.items() if rx.search(text)]
    return hits[0] if len(hits) == 1 else None


def drifters_named(text: str) -> list[str]:
    return [key for key, rx in DRIFTER_WORDS.items() if rx.search(text)]


def short_name(line: str) -> str:
    m = re.match(r"[^,:(.`]{3,45}", line)
    return (m.group(0) if m else line[:30]).strip()


# The plan: where every block goes


@dataclass
class PartBuf:
    key: str
    blocks: dict[str, list[list[str]]] = field(default_factory=dict)
    names: list[str] = field(default_factory=list)


class Plan:
    def __init__(self, name: str, title: str, info, example: str):
        """info(key) -> (label, when) for a part's title and its `Read when:` line."""
        self.name, self.title, self.info, self.example = name, title, info, example
        self.parts: dict[str, PartBuf] = {}
        self.extra_scaffold: list[str] = []  # lines added while planning (repeated headings and fences)
        self.scaffold: list[str] = []  # every line the script adds, for the proof
        self.dropped: list[tuple[str, list[str]]] = []
        self.unplaced: list[str] = []
        self.placements: list[str] = []  # for --detail
        self.hub_purpose = ""
        self.rationale: list[tuple[str, str, str]] = []  # (part, rule, first line) per Rationale entry
        self.rationale_listed: set[str] = set()  # parts whose Rationale entries the report lists one by one
        self.notes: list[str] = []  # things the Director decides, shown in the report
        self.drops = ["impact"]  # the history blocks this split removes

    def put(self, key: str, section: str, lines: list[str], name: str | list[str] | None = None, why: str = "") -> None:
        lines = trim(lines)
        if not lines:
            return
        buf = self.parts.setdefault(key, PartBuf(key))
        buf.blocks.setdefault(section, []).append(lines)
        names = [name] if isinstance(name, str) else list(name or [])
        for n in names:
            if n not in buf.names:
                buf.names.append(n)
        self.placements.append(f"{section:<12} {(names[0] if names else '(lead)'):<46.46} -> {key}{why}")

    def drop(self, label: str, lines: list[str]) -> None:
        self.dropped.append((label, trim(lines)))

    def part_label(self, key: str) -> str:
        return self.info(key)[0]

    def part_when(self, key: str) -> str:
        return self.info(key)[1]

    def render_part(self, key: str) -> str:
        buf = self.parts[key]
        head = [f"# {self.title}, {self.part_label(key)}", f"Part of: {self.name}", f"Read when: {self.part_when(key)}", ""]
        self.scaffold += head[:3]
        out = list(head)
        for sec in SECTION_ORDER:
            if sec not in buf.blocks:
                continue
            out += [f"## {sec}", ""]
            for block in buf.blocks[sec]:
                out += block + [""]
        return "\n".join(out).rstrip("\n") + "\n"

    def part_order(self) -> list[str]:
        return sorted(self.parts, key=lambda k: (not k.startswith("shared/"), k))

    def build(self, doc: Doc) -> dict[str, str]:
        """Relative path (under systems/) -> text, for every file the split writes."""
        self.scaffold = list(self.extra_scaffold)
        files = {f"{self.name}/{k}.md": self.render_part(k) for k in self.part_order()}
        rows = [f"| {'; '.join(self.parts[k].names)} | [{k}]({k}.md) |" for k in self.part_order() if self.parts[k].names]
        names_part = [
            f"# {self.title}, old names",
            f"Part of: {self.name}",
            f'Read when: a citation names a section of the old single file, such as "{self.example}".',
            "",
            "## Old names",
            "Code and docs cite sections of the old single file. This table says where each one lives now.",
            "",
            "| Old name | Now in |",
            "|---|---|",
            *rows,
            "",
            f"The old Impact sections are gone. `git log --follow docs/contracts/systems/{self.name}.md` shows them.",
        ]
        self.scaffold += content_lines(names_part)
        files[f"{self.name}/old-names.md"] = "\n".join(names_part) + "\n"
        order = sorted((k for k in files if k.startswith(f"{self.name}/")), key=lambda k: (k.split("/")[1] != "shared", k))
        items = [(k.split("/", 1)[1], files[k]) for k in order]
        gen = [
            "## Purpose",
            self.hub_purpose,
            "",
            "## Parts",
            ct.PARTS_BEGIN,
            ct.render_parts_table(self.name, items),
            ct.PARTS_END,
        ]
        gen = "\n".join(gen).split("\n")
        self.scaffold += content_lines(gen)
        files[f"{self.name}.md"] = "\n".join(doc.head + [""] + gen).rstrip("\n") + "\n"
        return files


def prove(old_text: str, plan_dropped: list[tuple[str, list[str]]], scaffold: list[str], files: dict[str, str]) -> list[str]:
    """Return the problems: an empty list is the proof that no line was lost or invented."""
    old = collections.Counter(content_lines(lines_of(old_text)))
    for _label, lines in plan_dropped:
        old.subtract(collections.Counter(content_lines(lines)))
    bad = [f"dropped line not in the old file: {ln[:70]!r}" for ln, n in old.items() if n < 0]
    old = +old
    new = collections.Counter()
    for text in files.values():
        new.update(content_lines(lines_of(text)))
    scaf = collections.Counter(scaffold)
    for ln, n in (scaf - new).items():
        bad.append(f"scaffold line not in the new files: {ln[:70]!r} x{n}")
    for name, text in files.items():
        if sum(1 for ln in lines_of(text) if ln.startswith("```")) % 2:
            bad.append(f"unbalanced code fence in {name}")
    rest = new - scaf
    for ln, n in (old - rest).items():
        bad.append(f"LOST x{n}: {ln[:90]!r}")
    for ln, n in (rest - old).items():
        bad.append(f"INVENTED x{n}: {ln[:90]!r}")
    return bad


# Purpose


def cut_who_builds(purpose: list[str]) -> tuple[list[str], list[str]]:
    """Split Purpose into what stays and the "Who builds what:" list with its bullets."""
    for i, ln in enumerate(purpose):
        if ln.startswith("Who builds what"):
            j = i + 1
            while j < len(purpose) and (purpose[j].startswith("- ") or not purpose[j].strip()):
                j += 1
            return purpose[:i] + purpose[j:], purpose[i:j]
    return purpose, []


def first_sentence(purpose: list[str]) -> str:
    first = "\n".join(purpose).strip().split("\n\n", 1)[0].replace("\n", " ")
    return re.split(r"(?<=\.)\s", first, maxsplit=1)[0]


# Drifters


def diagram_classify(line: str):
    if re.match(r"Class shape|Life of one drifter|Re-hit cooldown", line):
        return BASE, short_name(line)
    if line.startswith("Birth"):
        return SPAWN, short_name(line)
    if line.startswith("Views:"):
        return VIEWS, "Views"
    m = re.match(rf"({DRIFTER_OPENER})\b", line)
    if m:
        return f"{DRIFTER_BY_WORD[m.group(1).lower()]}/core", short_name(line)
    return None


RULES_OPENERS = {
    "Values": BASE,
    "Collision": COLLISION,
    "Levels": SPAWN,
    "The base": BASE,
    "Registry": SPAWN,
    "Tuning files": SPAWN,
    "Logging": SPAWN,
}
RULES_RX = re.compile(r"(Collision|Levels|The base|Registry|Meteorite|Satellite|Chain lightning|Fireball|Coin|Floating island|Planet|UFO|Tuning files|Values|Logging)\b")


def rules_classify(line: str):
    m = RULES_RX.match(line)
    if not m:
        return None
    word = m.group(1)
    key = RULES_OPENERS.get(word) or f"{DRIFTER_BY_WORD[word.lower()]}/core"
    return key, word


# Paragraphs that open with their own name inside another opener's block, and that other
# files cite by that name.
ALIASES = ("Push-out", "Spawner", "How to add a drifter")


def lead_names(lines: list[str]) -> list[str]:
    return [a for a in ALIASES if any(ln.startswith(a) for ln in lines[1:])]


def plan_rules(plan: Plan, body: list[str]) -> None:
    for u in split_units(body, rules_classify):
        if u.key is None:
            plan.put(BASE, "Rules", u.lines, "Rules (opening lines)", why="  (before the first opener)")
            continue
        names = [f"Rules, {u.name}"] + [f"Rules, {n}" for n in lead_names(u.lines)]
        if u.name == "Tuning files":
            for s in merge_adjacent(split_units(u.lines, tuning_bullet)):
                label = f"Rules, Tuning files, {s.name}" if s.key.endswith("/tuning") else "Rules, Tuning files"
                plan.put(s.key, "Rules", s.lines, label)
            continue
        main, tuning = extract_bullets(u.lines, r"- \*\*Tuning checks")
        plan.put(u.key, "Rules", main, names)
        if tuning:
            d = u.key.split("/")[0]
            plan.put(f"{d}/tuning", "Rules", tuning, f"Rules, {u.name}, Tuning checks")


def tuning_bullet(line: str):
    """In the Tuning files block, every top-level line is its own unit. A drifter's file goes to that drifter.
    Every other line, the shared files and the check on all of them, stays in the shared part."""
    m = re.match(r"- \*\*The (.+?)'s file\*\*", line)
    key = DRIFTER_BY_WORD.get(m.group(1).lower()) if m else None
    return (f"{key}/tuning", f"The {m.group(1)}'s file") if key else (SPAWN, "")


def extract_bullets(lines: list[str], rx: str) -> tuple[list[str], list[str]]:
    """Move top-level lines that match rx, with their indented lines, out of a block."""
    keep, moved, taking = [], [], False
    for ln in lines:
        if re.match(rx, ln):
            taking = True
        elif ln.strip() and ln[0] not in " \t":
            taking = False
        (moved if taking else keep).append(ln)
    return keep, moved


def iface_part(path: str) -> str | None:
    p = path.rstrip("/")
    if p == "game/core/collision.py":
        return COLLISION
    if p == "game/core/drifters/base.py":
        return BASE_IFACE
    if p == "game/ui/shapes.py":
        return VIEWS
    m = re.match(r"game/core/drifters/(\w+)\.py$", p)
    if m:
        d = DRIFTER_BY_MODULE.get(m.group(1))
        return f"{d}/core" if d else (SPAWN if m.group(1) in {"tuning", "registry", "spawner", "__init__"} else None)
    if p == "game/core/levels.py":
        return SPAWN
    return None


def plan_interface(plan: Plan, body: list[str], mapper, lead_key: str, special: dict | None = None) -> None:
    """One Interface block per `### <path>` heading. mapper(path) gives the part key, None when it has no place.
    special: path -> handler for a block that needs cutting inside its code fence."""
    mask = ct.fenced_mask(body)
    cuts = [i for i, (ln, f) in enumerate(zip(body, mask)) if not f and ln.startswith("### ")]
    if not cuts or cuts[0] > 0:
        plan.put(lead_key, "Interface", body[: cuts[0] if cuts else len(body)], "Interface (opening paragraph)")
    for n, i in enumerate(cuts):
        block = body[i : cuts[n + 1] if n + 1 < len(cuts) else len(body)]
        path = re.match(r"### (\S+)", block[0]).group(1)
        name = f"Interface, `{path}`"
        if special and path in special:
            special[path](plan, block, name)
            continue
        key = mapper(path)
        if key is None:
            plan.unplaced.append(f"Interface block {path}: stays in {lead_key}")
            key = lead_key
        plan.put(key, "Interface", block, name)


UI_SEAM = re.compile(r"# game/ui/drifters/(\w+)\.py")


def iface_chunks(plan: Plan, block: list[str], name: str) -> None:
    """The ui/drifters block holds every view module in one code fence. Cut it at the
    `# game/ui/drifters/<file>.py` comments and close and reopen the fence in each part."""
    heading = block[0]
    opens = [i for i, ln in enumerate(block) if ln.startswith("```")]
    if len(opens) != 2:
        raise SystemExit(f"{name}: expected one code fence, found {len(opens) // 2} (the split cannot cut it safely)")
    fence_open, fence_close = block[opens[0]], block[opens[1]]
    inner = block[opens[0] + 1 : opens[1]]
    chunks: list[tuple[str, list[str]]] = []
    for ln in inner:
        m = UI_SEAM.match(ln)
        if m or not chunks:
            module = m.group(1) if m else "registry"
            d = DRIFTER_BY_MODULE.get(module[:-5]) if module.endswith("_view") else None
            chunks.append((f"{d}/view" if d else VIEWS, []))
        chunks[-1][1].append(ln)
    by_part: dict[str, list[str]] = {}
    file_names: dict[str, list[str]] = {}
    for key, lines in chunks:
        by_part.setdefault(key, []).extend(trim(lines) + [""])
        seam = UI_SEAM.match(lines[0])
        file_names.setdefault(key, []).append(f"Interface, `game/ui/drifters/{seam.group(1) if seam else 'registry'}.py`")
    after = trim(block[opens[1] + 1 :])
    for i, (key, lines) in enumerate(by_part.items()):
        piece = [heading, fence_open, *trim(lines), fence_close] + ([""] + after if key == VIEWS and after else [])
        if i:
            plan.extra_scaffold += [heading, fence_open, fence_close]
        plan.put(key, "Interface", piece, ([name] if key == VIEWS else []) + file_names[key])
    if after and VIEWS not in by_part:
        plan.unplaced.append("text after the ui/drifters code fence has no views chunk")


def plan_presentation(plan: Plan, body: list[str]) -> None:
    def classify(line: str):
        m = re.match(r"\*\*(.+?)\*\*", line)
        if m:
            word = m.group(1).strip()
            d = DRIFTER_BY_WORD.get(word.lower())
            return (f"{d}/view", word) if d else (VIEWS, word)
        if line.startswith("Rules for every view"):
            return VIEWS, "Rules for every view"
        return None

    for u in split_units(body, classify):
        if u.key is None:
            plan.put(VIEWS, "Presentation", u.lines, "Presentation, Every fact a view shows")
        else:
            plan.put(u.key, "Presentation", u.lines, f"Presentation, {u.name}")


# The Rationale is a log: a run of entries per feature, each with its DRA id. An entry goes to the
# drifter its feature introduced, unless it explains a shared mechanism. The feature table comes
# from the Interface headings (`### game/core/drifters/ufo.py (DRA-104)`); DRA-39 also made the
# base, so only entries that name the satellite go to it. Titles that start like these explain a
# shared mechanism, whatever feature wrote them.
RATIONALE_FEATURE = {"DRA-104": "ufo", "DRA-96": "planet", "DRA-47": "chain-lightning", "DRA-56": "fireball",
                     "DRA-62": "coin", "DRA-86": "floating-island"}
RATIONALE_SHARED = (
    "`seeded` is a class attribute", "`hazard_speed_mult` joins", "`start_size` is a base hook",
    "The line is a capsule", "`DrifterTypeExtra` joins", "`warning_copy()` instead", "`settle_warning(ctx)`",
    "`scale_timer` rounds", "`telegraph_min` is a hazards value", "`drawn_parts()` in the base",
    "The scroll reaches the drifter", "`parked` is a class attribute", "`collect_points` and `collect_popup`",
    "Polygons are convex", "The separating-axis", "A grown polygon", "The push-out measures",
    "`SURFACE_TOLERANCE`", "`BLOCK` is its own touch effect",
)


def rationale_owner(lines: list[str]) -> tuple[str, str]:
    """Where one Rationale entry goes, and the rule that decided it."""
    m = re.match(r"- \*\*(.+?)\*\*", lines[0])
    title = m.group(1) if m else lines[0]
    entry = " ".join(lines)
    if title.startswith(RATIONALE_SHARED):
        return RATIONALE, "explains a shared mechanism"
    named = drifters_named(title)
    if len(named) == 1:
        return f"{named[0]}/rationale", "the title names the drifter"
    ids = re.findall(r"DRA-\d+", title) or re.findall(r"DRA-\d+", entry)
    if title.startswith("No art task") and ids:
        d = RATIONALE_FEATURE.get(ids[0]) or ("satellite" if ids[0] == "DRA-39" else None)
        if d:
            return f"{d}/rationale", "the art note of its feature"
    if ids and ids[0] in RATIONALE_FEATURE:
        return f"{RATIONALE_FEATURE[ids[0]]}/rationale", f"its feature ({ids[0]}) introduced the drifter"
    return RATIONALE, "no drifter feature: shared by default"


def plan_rationale(plan: Plan, body: list[str]) -> None:
    marked = []
    for u in split_units(body, lambda _line: ("", "")):
        key, rule = rationale_owner(u.lines)
        marked.append(Unit(key, "Rationale", u.lines))
        plan.placements.append(f"{'Rationale':<12} {u.lines[0][:50]:<50} -> {key}  [{rule}]")
        plan.rationale.append((key, rule, u.lines[0]))
    for u in merge_adjacent(marked):
        plan.put(u.key, "Rationale", u.lines, "Rationale")


def plan_drifters(old_text: str, drop_who: bool = True) -> tuple[Doc, Plan]:
    doc = parse_doc(old_text)
    plan = Plan("drifters", "Drifters", drifter_info, "Rules, Satellite")
    plan.rationale_listed = {RATIONALE}
    plan.drops = ["impact", "who-builds"]
    keep, who = cut_who_builds(doc.sections["Purpose"])
    plan.drop('Purpose, "Who builds what" list', who)
    plan.put(BASE, "Purpose", keep, "Purpose (all but its first sentence)")
    plan.hub_purpose = f"{first_sentence(keep)} The contract is split into parts: open only the one you need."
    for u in split_units(doc.sections["Diagram"], diagram_classify):
        plan.put(u.key or BASE, "Diagram", u.lines, f"Diagram, {u.name}" if u.name else "Diagram (opening lines)")
    plan_interface(plan, doc.sections["Interface"], iface_part, BASE_IFACE, {"game/ui/drifters/": iface_chunks})
    plan_presentation(plan, doc.sections["Presentation"])
    plan_rules(plan, doc.sections["Rules"])
    plan.drop("Impact section", ["## Impact"] + doc.sections["Impact"])
    plan_rationale(plan, doc.sections["Rationale"])
    extra = set(doc.sections) - set(SECTION_ORDER) - {"Impact"}
    if extra:
        raise SystemExit(f"sections the plan does not place: {sorted(extra)}")
    return doc, plan


# App: by area. Rules has 12 named blocks and one cumulative "Integration checks" block per feature.

APP_AREAS = {  # part key -> (label, read when)
    "general": ("overview", "you want the overview of the app, or a rule that fits no area."),
    "startup": ("startup", "you change startup, the run mode switch, logging or the import boundary."),
    "error-handling": ("error handling", "you change the error guard or the error screen."),
    "release": ("release", "you change the launch script, the release package or `pygbag.ini`."),
    "frame-loop": ("frame loop", "you change the frame loop: ticks, keys, draw order, the catch-up cap."),
    "tuning-loader": ("tuning loader", "you change how the tuning files are loaded and checked."),
    "debug-spawns": ("debug spawns", "you change the debug spawn list: its file, checks, rows or timing."),
    "wave-loading": ("wave loading", "you change how wave files are read and loaded."),
    "integration-checks/method": ("integration checks, method", "you run any browser check: how the checks are done."),
}
APP_FEATURES = {  # what each feature's integration checks cover
    "DRA-5": "the app base", "DRA-6": "the ship, its view and the debug overlay",
    "DRA-13": "the scroll, the starfield and the HUD", "DRA-19": "the review follow-ups (no new gameplay)",
    "DRA-23": "the run: lives, hits and game over", "DRA-29": "the drifter base, the meteorite and the debug spawn list",
    "DRA-39": "the satellite, the re-hit cooldown and the editable spawn list", "DRA-47": "the chain lightning",
    "DRA-56": "the fireball", "DRA-61": "the score and the game-over score", "DRA-62": "the coin and its popup",
    "DRA-76": "waves and the playlist", "DRA-86": "the floating island", "DRA-96": "the planet", "DRA-104": "the UFO",
}
APP_RULE_OPENERS = [  # (opener regex, part key; None = integration checks of the feature in the match)
    (r"Startup\b", "startup"), (r"Import boundary", "startup"), (r"Run mode", "startup"), (r"Logging\b", "startup"),
    (r"Frame loop", "frame-loop"), (r"Tuning loader", "tuning-loader"), (r"Debug test spawn list", "debug-spawns"),
    (r"Wave files", "wave-loading"), (r"Error guard", "error-handling"), (r"Launch script", "release"),
    (r"Release package", "release"), (r"How the browser checks", "integration-checks/method"),
    (r"Integration checks for (DRA-\d+)", None),
]
APP_IFACE = {
    "game/main.py": "startup", "game/app/mode.py": "startup", "game/app/log.py": "startup", "game/app/settings.py": "startup",
    "game/app/guard.py": "error-handling", "game/ui/look.py": "error-handling", "game/ui/error_screen.py": "error-handling",
    "game/app/loop.py": "frame-loop", "game/app/frame.py": "frame-loop", "game/app/tuning.py": "tuning-loader",
    "game/app/debug_spawns.py": "debug-spawns", "game/app/waves.py": "wave-loading",
    "pygbag.ini": "release", "game/scripts/start-driftward-ace.sh": "release",
}
# Rationale entries by the start of their bold title. Each area's why is its own part.
APP_RATIONALE = {
    "integration-checks": (
        "The UFO checks compare two page loads", "The planet checks use", "The first planet row", "The island checks run",
        "The first island row", "The DRA-6 and DRA-13 checks are reworded", "The earlier debug checks are reworded",
        "One example row per variant", "Fireball rows: one meets the ship"),
    "tuning-loader": (
        "The UFO's weave checks run in the tuning loader", "The escape check runs in the tuning loader",
        "The tuning is loaded in the app", "The tuning is loaded in both modes", "`TUNING_DIR` from", "`hazards.json` must exist",
        "The defaults live in core", "The loader builds the chain's hitbox", "The loader builds the fireball's hitbox"),
    "debug-spawns": (
        "The debug list fills the default seed", "`play` lives in the spawn list file", "The debug list counts",
        "The first test meteorite", "The spawn list is a file", "Rows carry no time", "Every row is spawned once",
        "Rows out of play", "Normal mode never reads the list", "A spawn row may have no position"),
    "wave-loading": (
        "Wave files are read in the app", "The wave folder is listed", "Waves load in both modes", "One seed per page load",
        "Both sources go through one"),
    "startup": (
        "`choose_mode` is pure", "`read_switch` runs before logging", "Heavy imports inside the guard", "`app/settings.py` holds",
        "The screen size moved to", "`TICK_RATE` stays in", "Browser logs go to", "The PEP 723 block", "Run-mode parsing has no permanent test"),
    "release": ("The release package is set in", "`?debug=1` and pygbag"),
    "error-handling": (
        "The guard imports its error screen late", "The error screen takes", "`ui/look.py` holds", "The guard removes null characters",
        "Idle after the error", "The error screen is tested headless"),
    "frame-loop": (
        "The mode reaches `frame_loop`", "Held keys come from", "Key lines log the ship", "Ship events are logged in core",
        "F3 lives in the app", "The catch-up cap drops time", "The cap is in `app/settings.py`", "The scroll starts right after the spawn",
        "Dropped catch-up time", "The HUD is drawn last", "The cap logs only when it starts", "The app holds one `Run`",
        "The app skips `draw_ship`", "The app passes `run.score`", "The Game Over box is drawn before the HUD"),
}


def bullet_names(lines: list[str]) -> list[str]:
    """Bold names that open a bullet inside a Rules block ("Tick", "Draw"): other files cite them."""
    out = []
    for ln in lines[1:]:
        m = re.match(r"- \*\*(.+?)\*\*", ln)
        if m:
            name = re.split(r"[,(.]", m.group(1))[0].strip(" `")
            if name and f"Rules, {name}" not in out:
                out.append(f"Rules, {name}")
    return out


def app_info(key: str) -> tuple[str, str]:
    if key in APP_AREAS:
        return APP_AREAS[key]
    kind, _, name = key.partition("/")
    if kind == "integration-checks":
        return f"integration checks, {name}", f"you run or extend the browser checks for {APP_FEATURES[name]} ({name})."
    label = "integration checks" if name == "integration-checks" else APP_AREAS[name][0]
    return f"{label}, rationale", f"you ask why the app's {label} works as it does."


def app_rules_classify(line: str):
    for rx, key in APP_RULE_OPENERS:
        m = re.match(rx, line)
        if m:
            return (key or f"integration-checks/{m.group(1)}"), m.group(0)
    return None


def plan_app(old_text: str, drop_who: bool = False) -> tuple[Doc, Plan]:
    doc = parse_doc(old_text)
    plan = Plan("app", "App", app_info, "Rules, Frame loop")
    purpose = doc.sections["Purpose"]
    keep, who = cut_who_builds(purpose)
    if drop_who:
        plan.drop('Purpose, "Who builds what" list', who)
        plan.drops = ["impact", "who-builds"]
    else:
        keep = purpose
        size = len("\n".join(who).encode())
        plan.notes.append(f'The Purpose "Who builds what" list ({len(who)} lines, {kb(size)}) is kept in general.md: dropping it was approved only for drifters. Add --drop-who-builds to drop it.')
    plan.put("general", "Purpose", keep, "Purpose (all but its first sentence)")
    plan.hub_purpose = f"{first_sentence(purpose)} The contract is split into parts: open only the one you need."
    plan.put("startup", "Diagram", doc.sections["Diagram"], "Diagram (all of it)")
    plan_interface(plan, doc.sections["Interface"], lambda path: APP_IFACE.get(path), "general")
    plan.put("error-handling", "Presentation", doc.sections["Presentation"], "Presentation (all of it)")
    for u in split_units(doc.sections["Rules"], app_rules_classify):
        if u.key is None:
            plan.put("general", "Rules", u.lines, "Rules (opening lines)")
        else:
            plan.put(u.key, "Rules", u.lines, [f"Rules, {u.name}"] + ([] if u.key.startswith("integration-checks") else bullet_names(u.lines)))
    plan.drop("Impact section", ["## Impact"] + doc.sections["Impact"])
    plan.rationale_listed = {"general"}
    marked = []
    for u in split_units(doc.sections["Rationale"], lambda _line: ("", "")):
        m = re.match(r"- \*\*(.+?)\*\*", u.lines[0])
        title = m.group(1) if m else u.lines[0]
        areas = [a for a, prefixes in APP_RATIONALE.items() if title.startswith(prefixes)]
        key = f"rationale/{areas[0]}" if len(areas) == 1 else "general"
        rule = "its area" if len(areas) == 1 else ("fits no area" if not areas else "fits several areas")
        marked.append(Unit(key, "Rationale", u.lines))
        plan.rationale.append((key, rule, u.lines[0]))
        plan.placements.append(f"{'Rationale':<12} {title[:50]:<50} -> {key}  [{rule}]")
    for u in merge_adjacent(marked):
        plan.put(u.key, "Rationale", u.lines, "Rationale")
    extra = set(doc.sections) - set(SECTION_ORDER) - {"Impact"}
    if extra:
        raise SystemExit(f"sections the plan does not place: {sorted(extra)}")
    return doc, plan


# Repo access


def run_git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


def is_dirty(root: Path, paths: list[str]) -> list[str]:
    out = run_git(root, "status", "--porcelain", "--", *paths)
    return [ln for ln in out.splitlines() if ln.strip()]


CITE_SECTION = re.compile(r"[`)\]:, ]*(Interface and Rules|Interface|Rules|Presentation|Rationale|Impact|Purpose|Diagram)\b(?P<phrase>.*)")


def citations(root: Path, name: str) -> list[tuple[str, str, str]]:
    """(file, section, phrase) for every citation of the old file that names a section."""
    out = []
    own = {f"docs/contracts/systems/{name}.md"}
    for f in run_git(root, "ls-files").split("\n"):
        if not f or f in own or f.startswith(f"docs/contracts/systems/{name}/"):
            continue
        try:
            text = (root / f).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in re.finditer(rf"(?<![\w-])(?:systems/)?{name}\.md(?P<tail>[^\n]{{0,90}})", text):
            s = CITE_SECTION.match(m.group("tail"))
            if s:
                out.append((f, s.group(1), s.group("phrase")))
    return out


def resolves(plan: Plan, section: str, phrase: str) -> bool:
    if section in {"Rationale", "Impact", "Purpose"}:
        return True
    wanted = {"Interface and Rules": ("Interface", "Rules")}.get(section, (section,))
    keys = [n.split(", ", 1)[1].rsplit(", ", 1)[-1].strip("` ").lower() for b in plan.parts.values() for n in b.names
            if n.split(", ", 1)[0] in wanted and ", " in n]
    low = phrase.replace("`", "").lower().strip(" ,:;().")
    if not low:
        return True  # names only the section; the hub says where each section went
    head = low.split(",")[0].split("(")[0].strip()
    return any(k and (k in low or (len(head) >= 5 and head in k)) for k in keys)


# Reports


def kb(n: int) -> str:
    return f"{n / 1024:.1f} KB"


def section_sizes(text: str) -> str:
    doc = parse_doc(text)
    return ", ".join(f"{title} {kb(len(chr(10).join(body).encode()))}" for title, body in doc.sections.items())


def report_split(root: Path, old_text: str, doc: Doc, plan: Plan, files: dict[str, str], problems: list[str], detail: bool) -> str:
    out = [f"Split of systems/{plan.name}.md: old file {kb(len(old_text.encode()))}, {len(lines_of(old_text))} lines", ""]
    out.append("Files (size, lines, sections):")
    for rel_path, text in sorted(files.items(), key=lambda kv: (kv[0] != f"{plan.name}.md", kv[0])):
        budget = ct.HUB_MAX_BYTES if rel_path == f"{plan.name}.md" else ct.PART_MAX_BYTES
        size = len(text.encode())
        flag = "  OVER BUDGET" if size > budget else ""
        out.append(f"  {rel_path:<52} {kb(size):>9} {len(lines_of(text)):>5} lines  {', '.join(ct.top_headings(text))}{flag}")
        if flag:
            out.append(f"      by section: {section_sizes(text)}")
    out.append(f"  budgets: hub {kb(ct.HUB_MAX_BYTES)}, part {kb(ct.PART_MAX_BYTES)}")
    out += ["", "Dropped (history, listed in full by the proof):"]
    for label, lines in plan.dropped:
        size = len("\n".join(lines).encode())
        out.append(f"  {label}: {len(lines)} lines, {kb(size)}")
    out += ["", f"Unplaced ({len(plan.unplaced)}):"] + ([f"  {u}" for u in plan.unplaced] or ["  none"])
    by_owner = collections.Counter(k for k, _r, _l in plan.rationale)
    out += ["", f"Rationale: {len(plan.rationale)} entries. Per part: " + ", ".join(f"{k.replace('/rationale', '')} {n}" for k, n in sorted(by_owner.items()))]
    for listed in sorted(plan.rationale_listed):
        out += [f"  in {listed} ({by_owner[listed]}):"] + [f"    {line[:100]}" for k, _r, line in plan.rationale if k == listed]
    for note in plan.notes:
        out += ["", "For the Director: " + note]
    out += ["", "Lines the script adds (not in the old file):"]
    for ln, n in collections.Counter(plan.scaffold).most_common(14):
        out.append(f"  x{n:<3} {ln[:110]}")
    out.append(f"  ({len(plan.scaffold)} lines in all)")
    cites = citations(root, plan.name)
    bad = collections.Counter((s, ph.strip(' ,:;()`.')[:50]) for _f, s, ph in cites if not resolves(plan, s, ph))
    files_citing = len({f for f, _s, _p in cites})
    out += ["", f"Citations of the old file that name a section: {len(cites)} in {files_citing} files. "
            f"{len(cites) - sum(bad.values())} resolve through the old-name map."]
    for (s, ph), n in bad.most_common():
        out.append(f"  does not resolve x{n}: {s}, {ph}")
    out += ["", "Proof (every non-blank line of the old file, once, minus dropped and added lines): "
            + ("OK" if not problems else f"FAILED, {len(problems)} problem(s)")]
    out += [f"  {p}" for p in problems[:20]]
    if detail:
        out += ["", "Placements:"] + [f"  {p}" for p in plan.placements]
    return "\n".join(out)


# Writing


def write_split(root: Path, name: str, files: dict[str, str], summary: str, old_text: str, plan: Plan) -> list[str]:
    p = ct.Paths(root)
    dirty = is_dirty(root, ["docs/contracts"])
    if dirty:
        raise SystemExit("refused: docs/contracts has uncommitted changes, so git would not hold the old file:\n  " + "\n  ".join(dirty[:8]))
    for rel_path, text in files.items():
        target = p.systems / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        ct.safe_write(p, target, text)
    changelog = p.contracts / "CHANGELOG.md"
    entry = f"\n## Contract split: {name}, {datetime.date.today().isoformat()}\n- `systems/{name}.md`: {summary}"
    ct.safe_write(p, changelog, changelog.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry + "\n")
    ct.refresh_hubs(p)
    ct.safe_write(p, p.contracts / "INDEX.md", ct.render_index(ct.load_contracts(p)))
    record_split(root, name, "split", old_text, {rel_path: p.systems / rel_path for rel_path in files}, plan.drops)
    disk = {rel_path: (p.systems / rel_path).read_text(encoding="utf-8") for rel_path in files}
    return prove(old_text, plan.dropped, plan.scaffold, {k: v for k, v in disk.items()})


# Impact only


def plan_drop_impact(text: str, drop_who: bool = False) -> tuple[str, list[tuple[str, list[str]]], int]:
    doc = parse_doc(text)
    lines = lines_of(text)
    mask = ct.fenced_mask(lines)
    marks = [i for i, (ln, f) in enumerate(zip(lines, mask)) if not f and ln.startswith("## ")]
    dropped, kept = [], list(lines)
    for n, i in enumerate(marks):
        if lines[i][3:].strip().startswith("Impact"):
            end = marks[n + 1] if n + 1 < len(marks) else len(lines)
            dropped = [("Impact section", lines[i:end])]
            kept = lines[:i] + lines[end:]
    who_lines = cut_who_builds(doc.sections.get("Purpose", []))[1]
    if drop_who and who_lines:
        for i in range(len(kept) - len(who_lines) + 1):
            if kept[i : i + len(who_lines)] == who_lines:
                kept = kept[:i] + kept[i + len(who_lines) :]
                dropped.append(('Purpose, "Who builds what" list', who_lines))
                break
    return "\n".join(kept), dropped, len(who_lines)


def cmd_drop_impact(root: Path, names: list[str], write: bool, drop_who: bool = False) -> int:
    p = ct.Paths(root)
    status = 0
    for name in names:
        path = p.systems / f"{name}.md"
        if not path.is_file():
            print(f"{name}: no such contract")
            status = 1
            continue
        old = path.read_text(encoding="utf-8")
        new, dropped, who = plan_drop_impact(old, drop_who)
        problems = prove(old, dropped, [], {name: new})
        size = sum(len("\n".join(ls).encode()) for _l, ls in dropped)
        what = " and ".join(label for label, _l in dropped)
        print(f"{name}: dropped {what}: {kb(size)} ({sum(len(ls) for _l, ls in dropped)} lines). {kb(len(old.encode()))} -> {kb(len(new.encode()))}. "
              f"Proof {'OK' if not problems else 'FAILED'}. "
              + ("" if drop_who else f"The Purpose 'Who builds what' list ({who} lines) is kept."))
        for pr in problems[:10]:
            print(f"  {pr}")
        if problems:
            status = 1
            continue
        if write:
            if is_dirty(root, [f"docs/contracts/systems/{name}.md", "docs/contracts/CHANGELOG.md", "docs/contracts/INDEX.md", MANIFEST]):
                raise SystemExit(f"refused: {name}.md or the changelog has uncommitted changes")
            ct.safe_write(p, path, new)
            after = prove(old, dropped, [], {name: path.read_text(encoding="utf-8")})
            print(f"  written. Read back: proof {'OK' if not after else 'FAILED ' + str(after[:3])}")
            changelog = p.contracts / "CHANGELOG.md"
            gone = "Impact section and the Purpose task list" if drop_who else "Impact section"
            entry = f"\n## Contract split: {name} Impact, {datetime.date.today().isoformat()}\n- `systems/{name}.md`: {gone} removed (history is in git), no other change."
            ct.safe_write(p, changelog, changelog.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry + "\n")
            record_split(root, name, "impact", old, {name: path}, ["impact"] + (["who-builds"] if drop_who else []))
    if write and status == 0:
        ct.safe_write(p, p.contracts / "INDEX.md", ct.render_index(ct.load_contracts(p)))
    elif not write:
        print("\nNothing written. Add --write after the Director approves.")
    return status


# Command line


PLANNERS = {"drifters": plan_drifters, "app": plan_app}


def summary_for(plan: Plan) -> str:
    gone = "The Impact section and the Purpose task list are" if "who-builds" in plan.drops else "The Impact section is"
    return f"restructured into a hub and parts, no content change. {gone} removed (history is in git)."


def cmd_split(root: Path, target: str, write: bool, detail: bool, drop_who: bool) -> int:
    p = ct.Paths(root)
    source = p.systems / f"{target}.md"
    old_text = source.read_text(encoding="utf-8")
    if (p.systems / target).is_dir() or ct.PARTS_BEGIN in old_text:
        print(f"{target} is already split: systems/{target}/ exists. Nothing to do.")
        return 0
    doc, plan = PLANNERS[target](old_text, drop_who)
    files = plan.build(doc)
    problems = prove(old_text, plan.dropped, plan.scaffold, files)
    print(report_split(root, old_text, doc, plan, files, problems, detail))
    if problems:
        return 1
    if not write:
        print("\nNothing written. Add --write after the Director approves.")
        return 0
    after = write_split(root, target, files, summary_for(plan), old_text, plan)
    print("\nWritten. Read back from disk: proof " + ("OK" if not after else f"FAILED, {len(after)} problem(s): {after[:5]}"))
    return 1 if after else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="One-time contract splitter. Dry-run unless --write is given.")
    ap.add_argument("--root", type=Path, default=ct.REPO, help="repo root (default: this repo)")
    sub = ap.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("split", help="cut a contract into a hub and parts")
    sp.add_argument("target", choices=sorted(PLANNERS))
    sp.add_argument("--write", action="store_true", help="apply the split. Without it nothing is written")
    sp.add_argument("--detail", action="store_true", help="list every placement")
    sp.add_argument("--drop-who-builds", action="store_true", help="also drop the Purpose task list (app; drifters always does)")
    di = sub.add_parser("drop-impact", help="remove only the Impact section from contracts that are not split")
    di.add_argument("names", nargs="+", help="contract names, such as run ship scroll")
    di.add_argument("--write", action="store_true", help="apply. Without it nothing is written")
    di.add_argument("--drop-who-builds", action="store_true", help="also drop the Purpose task list")
    args = ap.parse_args()
    root = args.root.resolve()
    if args.command == "split":
        return cmd_split(root, args.target, args.write, args.detail, args.drop_who_builds)
    return cmd_drop_impact(root, args.names, args.write, args.drop_who_builds)


if __name__ == "__main__":
    sys.exit(main())
