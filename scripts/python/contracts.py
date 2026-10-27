#!/usr/bin/env python3
"""Contracts and close-out tool for docs/contracts/.

Reads the contracts, task files and reports, and prints what is in
progress, what is ready to close out, and what is still open. It writes
only on `close-out --write` and `index`, and only inside docs/contracts/:

- contract `Status:` and `Version:` lines,
- task `Status:` lines,
- an entry appended to docs/contracts/CHANGELOG.md,
- docs/contracts/INDEX.md (generated, one row per system),
- the part table of every split contract's hub, between the `parts:begin` and
  `parts:end` markers (generated from the parts' `Read when:` lines),
- on `close-out --interfaces --write` only: the Interface blocks (`### game/...py`) of the
  contracts it freezes, replaced by an outline generated from the module with `ast`.

Everything else it prints and never stores.

Usage (the wrappers in scripts/ call this):
  contracts.py                        overview: in progress and ready to close out
  contracts.py --brief                one line per feature ready to close out, else nothing
  contracts.py close-out              list features ready to close out
  contracts.py close-out DRA-29       show what close-out would do. Writes nothing.
  contracts.py close-out DRA-29 --write --summary "One line." [--accept-open]
  contracts.py close-out DRA-29 --interfaces    also list the Interface blocks it would regenerate (off by default)
  contracts.py interface game/core/drifters/satellite.py   sample: the current block next to the generated one. Writes nothing.
  contracts.py verify                 check headers, task pointers, hubs, parts and that no split lost a line; exit 1 on problems
  contracts.py index                  rebuild docs/contracts/INDEX.md and the hubs' part tables

Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FEATURE_DIR = re.compile(r"^(DRA|DEMO)-\d+$")
HEADER_LINES = 12
ASSIGNEES = {"gameplay-implementer", "ui-developer", "art-audio-engineer", "qa-engineer"}
FINDING_ROW = re.compile(r"^\|\s*([A-Z]+-\d+-\d+-F\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|\s*$")
ID_LIST = re.compile(r"[A-Z]+-\d+-\d+-F\d+")
DONE_STATUSES = {"fixed", "no action"}
PARTS_BEGIN = "<!-- parts:begin -->"
PARTS_END = "<!-- parts:end -->"
HUB_MAX_BYTES = 7 * 1024
PART_MAX_BYTES = 27 * 1024
TICKET_ID = re.compile(r"\b[A-Z]{2,}-\d+\b")


@dataclass
class Paths:
    root: Path

    @property
    def contracts(self) -> Path:
        return self.root / "docs" / "contracts"

    @property
    def systems(self) -> Path:
        return self.contracts / "systems"

    @property
    def reports(self) -> Path:
        return self.root / "docs" / "reports"


@dataclass
class Contract:
    path: Path
    name: str
    version: int | None
    status: str | None
    features: list[str]
    text: str


@dataclass
class Task:
    path: Path
    base: str
    feature: str
    assignee: str
    contracts: list[str]
    status: str
    linear: str
    text: str


@dataclass
class Finding:
    id: str
    severity: str
    where: str
    status: str
    report: Path


@dataclass
class Feature:
    id: str
    tasks: list[Task] = field(default_factory=list)
    integration: str | None = None
    integration_path: Path | None = None


def header(text: str, key: str) -> str | None:
    for line in text.splitlines()[:HEADER_LINES]:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def first_line_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    first = path.read_text(encoding="utf-8").split("\n", 1)[0]
    return first.split(":", 1)[1].strip() if first.startswith(f"{key}:") else None


def section(text: str, title: str) -> str:
    match = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else ""


def load_contracts(p: Paths) -> list[Contract]:
    out = []
    for path in sorted(p.systems.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        version = header(text, "Version")
        out.append(
            Contract(
                path=path,
                name=path.stem,
                version=int(version) if version and version.isdigit() else None,
                status=header(text, "Status"),
                features=[f.strip() for f in (header(text, "Features") or "").split(",") if f.strip()],
                text=text,
            )
        )
    return out


def load_features(p: Paths) -> dict[str, Feature]:
    features: dict[str, Feature] = {}
    for folder in sorted(p.contracts.iterdir()):
        if not (folder.is_dir() and FEATURE_DIR.match(folder.name)):
            continue
        feature = Feature(id=folder.name)
        for path in sorted((folder / "tasks").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            contracts = [c.strip().split("#", 1)[0] for c in (header(text, "Contract") or "").split(",") if c.strip()]
            feature.tasks.append(
                Task(
                    path=path,
                    base=path.stem,
                    feature=header(text, "Feature") or folder.name,
                    assignee=header(text, "Assignee") or "",
                    contracts=contracts,
                    status=header(text, "Status") or "",
                    linear=header(text, "Linear") or "",
                    text=text,
                )
            )
        report = p.reports / "integration" / f"{folder.name}.md"
        feature.integration = first_line_value(report, "Verdict")
        feature.integration_path = report if report.exists() else None
        features[folder.name] = feature
    return features


def qa_verdict(p: Paths, task: Task) -> str | None:
    return first_line_value(p.reports / "qa" / f"{task.base}.md", "Verdict")


def is_closed(feature: Feature, contracts: list[Contract]) -> bool:
    # Only close-out sets tasks done. A contract reopened later by another
    # feature keeps this feature in its Features line, so drafts can't decide it.
    return bool(feature.tasks) and all(t.status == "done" for t in feature.tasks)


def ready_to_close(feature: Feature, contracts: list[Contract]) -> bool:
    return feature.integration == "pass" and not is_closed(feature, contracts)


def findings_for(p: Paths, feature_id: str) -> tuple[list[Finding], list[Path]]:
    """Every finding in the feature's review reports, with fixes from implementation reports applied.

    Returns the findings and the review reports that have no findings table (old format).
    """
    findings: list[Finding] = []
    old_format: list[Path] = []
    for report in sorted((p.reports / "review").glob(f"{feature_id}-*.md")):
        text = report.read_text(encoding="utf-8")
        body = section(text, "Findings")
        rows = [FINDING_ROW.match(line) for line in body.splitlines()]
        rows = [r for r in rows if r]
        if not rows and body.strip().rstrip(".").lower() != "none":
            old_format.append(report)
        findings += [Finding(r[1], r[2], r[3], r[4].lower(), report) for r in rows]
    fixed: set[str] = set()
    not_fixable: set[str] = set()
    for impl in sorted((p.reports / "implementation").glob(f"*/{feature_id}-*.md")):
        for line in impl.read_text(encoding="utf-8").splitlines():
            if line.startswith("Fixed:"):
                fixed.update(ID_LIST.findall(line))
            elif line.startswith("Not fixable:"):
                not_fixable.update(ID_LIST.findall(line))
    for f in findings:
        if f.status == "open" and f.id in fixed:
            f.status = "fixed"
        elif f.status == "open" and f.id in not_fixable:
            f.status = "not fixable"
    return findings, old_format


def observations(feature: Feature) -> list[str]:
    if not feature.integration_path:
        return []
    body = section(feature.integration_path.read_text(encoding="utf-8"), "Observations")
    if not body or body.rstrip(".").lower() == "none":
        return []
    items = []
    for line in body.splitlines():
        if not line.startswith("- "):
            continue
        text = line[2:].strip()
        bold = re.match(r"\*\*(.+?)\*\*", text)
        head = bold.group(1) if bold else re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
        items.append(head.strip()[:160])
    return items or [body.splitlines()[0][:160]]


def purpose_line(contract: Contract) -> str:
    body = section(contract.text, "Purpose")
    first = body.split("\n\n", 1)[0].replace("\n", " ")
    sentence = re.split(r"(?<=\.)\s", first, maxsplit=1)[0]
    return sentence.replace("|", "\\|")


def render_index(contracts: list[Contract]) -> str:
    lines = [
        "# Contracts index",
        "Generated by `scripts/contracts.sh index`. Don't edit.",
        "",
        "| System | Ver | Status | Purpose |",
        "|---|---|---|---|",
    ]
    for c in contracts:
        lines.append(f"| [{c.name}](systems/{c.path.name}) | {c.version} | {c.status} | {purpose_line(c)} |")
    return "\n".join(lines) + "\n"


def safe_write(p: Paths, path: Path, text: str) -> None:
    resolved = path.resolve()
    if p.contracts.resolve() not in resolved.parents:
        raise SystemExit(f"refused: {path} is outside docs/contracts/")
    resolved.write_text(text, encoding="utf-8")


def fenced_mask(lines: list[str]) -> list[bool]:
    """True for every line inside a code fence, fence lines included."""
    mask, inside = [], False
    for line in lines:
        if line.startswith("```"):
            mask.append(True)
            inside = not inside
        else:
            mask.append(inside)
    return mask


def top_headings(text: str, level: str = "## ") -> list[str]:
    """Titles of the headings of one level that are outside code fences."""
    lines = text.split("\n")
    return [ln[len(level):].strip() for ln, f in zip(lines, fenced_mask(lines)) if not f and ln.startswith(level)]


def part_files(p: Paths, hub_name: str) -> list[Path]:
    """Every part file of a split contract: systems/<name>/**/*.md, shared first."""
    folder = p.systems / hub_name
    if not folder.is_dir():
        return []
    return sorted(folder.rglob("*.md"), key=lambda f: (f.relative_to(folder).parts[0] != "shared", str(f)))


def read_when(text: str) -> str:
    for line in text.splitlines()[:6]:
        if line.startswith("Read when:"):
            return line.split(":", 1)[1].strip()
    return ""


def render_parts_table(hub_name: str, items: list[tuple[str, str]]) -> str:
    """The hub's part table. items: (path under systems/<hub>/, the part's text)."""
    rows = ["| Part | Holds | Read when | Size |", "|---|---|---|---|"]
    for rel_path, text in items:
        holds = ", ".join(top_headings(text))
        size = f"{len(text.encode('utf-8')) / 1024:.1f} KB"
        label = rel_path[:-3] if rel_path.endswith(".md") else rel_path
        when = read_when(text).replace("|", "\\|")
        rows.append(f"| [{label}]({hub_name}/{rel_path}) | {holds} | {when} | {size} |")
    return "\n".join(rows)


def with_parts_table(hub_text: str, table: str) -> str:
    start, end = hub_text.find(PARTS_BEGIN), hub_text.find(PARTS_END)
    if start < 0 or end < start:
        return hub_text
    return hub_text[: start + len(PARTS_BEGIN)] + "\n" + table + "\n" + hub_text[end:]


def refreshed_hub(p: Paths, hub: Path) -> str:
    text = hub.read_text(encoding="utf-8")
    items = [(str(f.relative_to(p.systems / hub.stem)), f.read_text(encoding="utf-8")) for f in part_files(p, hub.stem)]
    return with_parts_table(text, render_parts_table(hub.stem, items)) if items else text


def refresh_hubs(p: Paths) -> list[Path]:
    """Rewrite each split contract's part table. Returns the hubs that changed."""
    changed = []
    for hub in sorted(p.systems.glob("*.md")):
        text = refreshed_hub(p, hub)
        if text != hub.read_text(encoding="utf-8"):
            safe_write(p, hub, text)
            changed.append(hub)
    return changed


def old_name_rows(text: str) -> list[tuple[list[str], str]]:
    """Rows of a hub's `## Old names` table: (old names, link target)."""
    body = section(text, "Old names")
    rows = []
    for line in body.splitlines():
        m = re.match(r"^\|\s*(.+?)\s*\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|\s*$", line)
        if m and not m[1].startswith(("Old name", "---")):
            rows.append(([n.strip() for n in m[1].split(";") if n.strip()], m[2]))
    return rows


def set_header(text: str, key: str, value: str) -> str:
    lines = text.split("\n")
    for i, line in enumerate(lines[:HEADER_LINES]):
        if line.startswith(f"{key}:"):
            lines[i] = f"{key}: {value}"
            return "\n".join(lines)
    raise SystemExit(f"no {key}: line in the header")


def rel(p: Paths, path: Path) -> str:
    return str(path.relative_to(p.root))


# Commands


# Interface blocks generated from the code (optional, off by default)


def _fmt_args(a: ast.arguments) -> str:
    """The parameter list as written: names, types and defaults."""
    def one(arg: ast.arg, default) -> str:
        text = arg.arg + (f": {ast.unparse(arg.annotation)}" if arg.annotation else "")
        if default is not None:
            text += f" = {ast.unparse(default)}" if arg.annotation else f"={ast.unparse(default)}"
        return text

    positional = [*a.posonlyargs, *a.args]
    defaults = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
    parts = []
    for i, (arg, default) in enumerate(zip(positional, defaults)):
        parts.append(one(arg, default))
        if a.posonlyargs and i == len(a.posonlyargs) - 1:
            parts.append("/")
    if a.vararg:
        parts.append("*" + one(a.vararg, None))
    elif a.kwonlyargs:
        parts.append("*")
    parts += [one(arg, default) for arg, default in zip(a.kwonlyargs, a.kw_defaults)]
    if a.kwarg:
        parts.append("**" + one(a.kwarg, None))
    return ", ".join(parts)


def _doc_lines(text: str | None, indent: str) -> list[str]:
    if not text:
        return []
    lines = text.split("\n")
    if len(lines) == 1:
        return [f'{indent}"""{lines[0]}"""']
    return [f'{indent}"""{lines[0]}', *[f"{indent}{ln}" if ln else "" for ln in lines[1:]], f'{indent}"""']


def _func_lines(node, indent: str) -> list[str]:
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    out = [f"{indent}@{ast.unparse(d)}" for d in node.decorator_list]
    doc = _doc_lines(ast.get_docstring(node), indent + "    ")
    out.append(f"{indent}{kind} {node.name}({_fmt_args(node.args)}){ret}:" + ("" if doc else " ..."))
    return out + doc


def _is_doc(stmt) -> bool:
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)


def _class_lines(cls: ast.ClassDef) -> list[str]:
    out = [f"@{ast.unparse(d)}" for d in cls.decorator_list]
    bases = ", ".join(ast.unparse(b) for b in [*cls.bases, *cls.keywords])
    out.append(f"class {cls.name}{f'({bases})' if bases else ''}:")
    body = cls.body[1:] if cls.body and _is_doc(cls.body[0]) else cls.body
    out += _doc_lines(ast.get_docstring(cls), "    ")
    for i, stmt in enumerate(body):
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and not stmt.target.id.startswith("_"):
            default = f" = {ast.unparse(stmt.value)}" if stmt.value is not None else ""
            out += ["", f"    {stmt.target.id}: {ast.unparse(stmt.annotation)}{default}"]
            if i + 1 < len(body) and _is_doc(body[i + 1]):
                out += _doc_lines(body[i + 1].value.value.strip(), "    ")
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and not stmt.name.startswith("_"):
            out += [""] + _func_lines(stmt, "    ")
    return out


def _constant_line(stmt) -> str | None:
    """`NAME: type` for a module constant. The value is never shown."""
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.target.id.isupper():
        return f"{stmt.target.id}: {ast.unparse(stmt.annotation)}"
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id.isupper():
        kind = type(stmt.value.value).__name__ if isinstance(stmt.value, ast.Constant) else type(stmt.value).__name__.lower()
        return f"{stmt.targets[0].id}: {kind}"
    return None


def module_interface(root: Path, rel_path: str) -> str:
    """The Interface block of one module, generated with `ast`: a pointer, the Source: line from the
    module docstring, class and function signatures with their docstrings, fields with their types
    and defaults, and the module constants by name and type only (their values stay in the code and
    the GDD)."""
    tree = ast.parse((root / rel_path).read_text(encoding="utf-8"))
    doc = ast.get_docstring(tree) or ""
    summary = doc.split("\n", 1)[0].strip()
    source = next((ln.strip() for ln in doc.split("\n") if ln.startswith("Source:")), "")
    stdlib, project = set(), set()
    for stmt in tree.body:
        names = [a.name for a in stmt.names] if isinstance(stmt, ast.Import) else ([stmt.module or ""] if isinstance(stmt, ast.ImportFrom) and not stmt.level else [])
        for name in names:
            if name and name != "__future__":
                (stdlib if name.split(".")[0] in sys.stdlib_module_names else project).add(name)
    imports = ", ".join([f"stdlib ({', '.join(sorted(stdlib))})"] * bool(stdlib) + sorted(project))
    code = [f"# Imports: {imports}."] if imports else []
    for stmt in tree.body:
        if (const := _constant_line(stmt)):
            code.append(const)
        elif isinstance(stmt, ast.ClassDef) and not stmt.name.startswith("_"):
            code += ["", *_class_lines(stmt)]
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and not stmt.name.startswith("_"):
            code += ["", *_func_lines(stmt, "")]
    head = [f"### {rel_path}", "Generated from the module at close-out. The code is the source of truth."]
    head += [summary] if summary else []
    head += [source] if source else []
    return "\n".join([*head, "```python", *code, "```"]).replace("\n\n\n", "\n\n")


def interface_blocks(text: str) -> dict[str, tuple[int, int]]:
    """`### <path>` blocks of a contract text: path -> (first line, line after the last). Fence-aware."""
    lines = text.split("\n")
    mask = fenced_mask(lines)
    heads = [i for i, (ln, f) in enumerate(zip(lines, mask)) if not f and (ln.startswith("### ") or ln.startswith("## "))]
    out = {}
    for n, i in enumerate(heads):
        m = re.match(r"### (\S+)", lines[i])
        if m:
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)
            while end > i and not lines[end - 1].strip():
                end -= 1
            out[m.group(1)] = (i, end)
    return out


def regenerate_interfaces(root: Path, text: str) -> tuple[str, list[tuple[str, int, int]]]:
    """Replace every `### game/...py` block whose module exists. Returns the new text and (path, old lines, new lines)."""
    lines = text.split("\n")
    changes = []
    for path, (start, end) in sorted(interface_blocks(text).items(), key=lambda kv: -kv[1][0]):
        if path.endswith(".py") and (root / path).is_file():
            new = module_interface(root, path).split("\n")
            changes.append((path, end - start, len(new)))
            lines[start:end] = new
    return "\n".join(lines), list(reversed(changes))


def contract_files(p: Paths, contract: Contract) -> list[Path]:
    return [contract.path, *part_files(p, contract.name)]


def cmd_interface(p: Paths, module: str) -> int:
    """A sample, writes nothing: the block now in the contracts next to the one that would replace it."""
    found = []
    for path in sorted(p.systems.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        block = interface_blocks(text).get(module)
        if block:
            found.append((path, "\n".join(text.split("\n")[block[0] : block[1]])))
    if not (p.root / module).is_file():
        print(f"{module}: no such module")
        return 1
    new = module_interface(p.root, module)
    for path, current in found:
        print(f"=== CURRENT: {rel(p, path)}: {len(current.splitlines())} lines, {len(current.encode()) / 1024:.1f} KB\n{current}\n")
    print(f"=== GENERATED: {len(new.splitlines())} lines, {len(new.encode()) / 1024:.1f} KB\n{new}\n")
    if found:
        cur = found[0][1].split("\n")
        mask = fenced_mask(cur)
        notes = [ln.strip() for ln, f in zip(cur, mask) if (ln.strip().startswith("#") and f and not ln.startswith("###")) or (not f and ln.strip())]
        notes = [n for n in notes if not n.startswith("### ")]
        lost = [n for n in notes if n.lstrip("# ").strip() not in new]
        print(f"=== Comments and prose in the contract block that the generated block does not repeat word for word: {len(lost)} of {len(notes)}")
        for n in lost[:40]:
            print("  " + n[:160])
        print("(Module constants are listed by name and type only. Field and parameter defaults are kept.)")
    print("\nNothing written.")
    return 0


def cmd_overview(p: Paths, brief: bool) -> int:
    contracts = load_contracts(p)
    features = load_features(p)
    ready = [f for f in features.values() if ready_to_close(f, contracts)]
    if brief:
        for f in ready:
            print(f"{f.id} is ready to close out: scripts/close-out.sh {f.id}")
        return 0
    building = [f for f in features.values() if not is_closed(f, contracts) and f not in ready]
    if not ready and not building:
        print("Nothing in progress. Every feature is closed.")
    for f in building:
        runnable = [t for t in f.tasks if t.assignee != "art-audio-engineer"]
        passed = sum(1 for t in runnable if qa_verdict(p, t) == "pass")
        verdict = f", integration {f.integration}" if f.integration else ""
        print(f"In progress:        {f.id} (QA pass {passed}/{len(runnable)} tasks{verdict})")
    for f in ready:
        drafts = [c.name for c in contracts if c.status == "draft" and f.id in c.features]
        print(f"Ready to close out: {f.id} (integration pass, draft: {', '.join(drafts) or 'none'})")
    orphans = [c.name for c in contracts if c.status == "draft" and not any(
        fid in c.features and not is_closed(features[fid], contracts) for fid in features)]
    if orphans:
        print(f"Draft with no open feature: {', '.join(orphans)}")
    return 0


def cmd_close_out(p: Paths, feature_id: str | None, write: bool, summary: str | None, accept_open: bool, interfaces: bool = False) -> int:
    contracts = load_contracts(p)
    features = load_features(p)
    if not feature_id:
        ready = [f.id for f in features.values() if ready_to_close(f, contracts)]
        print("Ready to close out: " + (", ".join(ready) if ready else "none"))
        return 0
    feature = features.get(feature_id)
    if feature is None:
        print(f"{feature_id}: no task folder in docs/contracts/. Known: {', '.join(features) or 'none'}")
        return 1
    if is_closed(feature, contracts):
        print(f"{feature_id} is already closed: its tasks are done.")
        return 0
    if feature.integration != "pass":
        print(f"{feature_id} is not ready: the integration report says {feature.integration or 'nothing (no report)'}.")
        return 1

    drafts = [c for c in contracts if c.status == "draft" and feature_id in c.features]
    pointed = {Path(c).name for t in feature.tasks for c in t.contracts}
    open_tasks = [t for t in feature.tasks if t.status != "done"]
    findings, old_format = findings_for(p, feature_id)
    still_open = [f for f in findings if f.status not in DONE_STATUSES]
    notes = observations(feature)
    keys = [t.linear for t in feature.tasks if t.linear]

    iface_plan: list[tuple[Path, str, list[tuple[str, int, int]]]] = []
    if interfaces:  # off by default: only when the Director asks for it
        for c in drafts:
            for f in contract_files(p, c):
                new_text, changes = regenerate_interfaces(p.root, f.read_text(encoding="utf-8"))
                if changes:
                    iface_plan.append((f, new_text, changes))

    print(f"Close-out {feature_id}")
    for c in drafts:
        print(f"  Freeze:   systems/{c.path.name} {c.version} -> {(c.version or 0) + 1}")
    for f, _text, changes in iface_plan:
        for path, old_n, new_n in changes:
            print(f"  Interface: {rel(p, f)}: {path} regenerated from the code, {old_n} -> {new_n} lines")
    for name in sorted(pointed - {c.path.name for c in drafts}):
        print(f"  Note:     a task points at {name}, which is not a draft contract of {feature_id}")
    print(f"  Tasks to done: {len(open_tasks)}")
    print(f"  Open findings: {len(still_open)}")
    for f in still_open:
        print(f"    {f.id} {f.severity} {f.where} [{f.status}]  ({rel(p, f.report)})")
    for path in old_format:
        print(f"    Old-format review report, check it by hand: {rel(p, path)}")
    print(f"  Observations: {len(notes) or 'none'}")
    for note in notes:
        print(f"    - {note}")
    if notes and feature.integration_path:
        print(f"    Full text: {rel(p, feature.integration_path)}, ## Observations")

    needs_decision = bool(still_open or notes or old_format)
    if not write:
        print("\nNothing written.")
        flag = " --accept-open" if needs_decision else ""
        print(f'Next: decide the open items, then: scripts/close-out.sh {feature_id} --write --summary "<one line>"{flag}')
        return 0
    if not summary:
        print("refused: --write needs --summary \"<one line on what changed>\"")
        return 1
    if needs_decision and not accept_open:
        print("refused: open findings or observations are listed above. Decide them, then add --accept-open.")
        return 1

    for f, new_text, _changes in iface_plan:
        if f not in {c.path for c in drafts}:
            safe_write(p, f, new_text)
    for c in drafts:
        base = next((new_text for f, new_text, _c in iface_plan if f == c.path), c.text)
        text = set_header(base, "Status", "frozen")
        text = set_header(text, "Version", str((c.version or 0) + 1))
        safe_write(p, c.path, text)
    for t in open_tasks:
        safe_write(p, t.path, set_header(t.text, "Status", "done"))
    today = datetime.date.today().isoformat()
    entry = [f"\n## {feature_id}, {today}"]
    entry += [f"- `systems/{c.path.name}`: {c.version} to {(c.version or 0) + 1}, frozen." for c in drafts]
    entry.append(f"- {summary}")
    if still_open:
        entry.append(f"- Accepted open findings: {', '.join(f.id for f in still_open)}.")
    changelog = p.contracts / "CHANGELOG.md"
    safe_write(p, changelog, changelog.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(entry) + "\n")
    refresh_hubs(p)
    safe_write(p, p.contracts / "INDEX.md", render_index(load_contracts(p)))

    print(f"\nWritten: {len(drafts)} contracts frozen, {len(open_tasks)} tasks done, CHANGELOG entry, INDEX.md.")
    if keys:
        print(f"Next: set these Linear sub-issues to Done (main session, Linear tools): {', '.join(keys)}")
    return 0


def table_without_sizes(text: str) -> str:
    start, end = text.find(PARTS_BEGIN), text.find(PARTS_END)
    region = text[start:end] if 0 <= start < end else ""
    return re.sub(r"\| [\d.]+ KB \|[ \t]*$", "|", region, flags=re.M)


def check_split(p: Paths, c: Contract, problems: list[str]) -> None:
    """A split contract: a hub that links every part, parts in budget, old names that resolve."""
    parts = part_files(p, c.name)
    if not parts:
        return
    hub_bytes = len(c.text.encode("utf-8"))
    if hub_bytes > HUB_MAX_BYTES:
        problems.append(f"{rel(p, c.path)}: the hub is {hub_bytes} bytes, over its {HUB_MAX_BYTES} budget")
    ids = sorted(set(TICKET_ID.findall(section(c.text, "Purpose"))))
    if ids:
        problems.append(f"{rel(p, c.path)}: Purpose names ticket ids ({', '.join(ids)}). A hub's Purpose is the system as it is now")
    folder = p.systems / c.name
    texts: dict[str, str] = {}
    for f in parts:
        text = f.read_text(encoding="utf-8")
        name = f.relative_to(folder).as_posix()
        texts[name] = text
        if f"({c.name}/{name})" not in c.text:
            problems.append(f"{rel(p, f)}: not linked from its hub")
        if len(text.encode("utf-8")) > PART_MAX_BYTES:
            problems.append(f"{rel(p, f)}: {len(text.encode('utf-8'))} bytes, over the {PART_MAX_BYTES} part budget")
        if f"Part of: {c.name}" not in text.splitlines()[:4] or not read_when(text):
            problems.append(f"{rel(p, f)}: must open with a `Part of: {c.name}` line and a `Read when:` line")
    if table_without_sizes(c.text) != table_without_sizes(refreshed_hub(p, c.path)):
        problems.append(f"{rel(p, c.path)}: the part table is out of date: run scripts/contracts.sh index")
    for holder, text in [(c.path, c.text)] + [(f, t) for f, t in ((f, f.read_text(encoding="utf-8")) for f in parts) if "Old names" in top_headings(t)]:
        for names, target in old_name_rows(text):
            target_path = (holder.parent / target).resolve()
            if not target_path.is_file():
                problems.append(f"{rel(p, holder)}: old-name map points at {target}, which does not exist")
                continue
            text = target_path.read_text(encoding="utf-8")
            for name in names:
                if ", " not in name:
                    continue
                sec, key = name.split(", ", 1)[0], name.rsplit(", ", 1)[-1].strip("` ")
                body = section(text, sec) or text
                # a section name opens a line of that section (after a heading, bullet, bold or comment mark)
                if not re.search(rf"^[#>*\-\s`]*{re.escape(key)}", body, re.M | re.I):
                    problems.append(f"{rel(p, holder)}: old name {name!r} does not resolve: no line of its {sec} opens with {key!r} in {target}")


CONTRACT_PATH = re.compile(r"(?:docs/contracts/)?systems/[A-Za-z0-9_\-/]+\.md")


def task_path_problems(p: Paths, task: Task) -> list[str]:
    """The paths an open task points at must exist: its `Impact:` file and every contract file or
    part its `Read in the contract` names. A wrong path would only show when an implementer stops on it."""
    problems = []
    impact = (header(task.text, "Impact") or "").split()[:1]
    if impact and not (p.root / impact[0]).exists():
        problems.append(f"{rel(p, task.path)}: Impact {impact[0]} does not exist")
    for match in sorted(set(CONTRACT_PATH.findall(section(task.text, "Read in the contract")))):
        if not (p.root / "docs" / "contracts" / match.removeprefix("docs/contracts/")).exists():
            problems.append(f"{rel(p, task.path)}: Read in the contract names {match}, which does not exist")
    return problems


def cmd_verify(p: Paths) -> int:
    problems: list[str] = []
    contracts = load_contracts(p)
    for c in contracts:
        if c.version is None:
            problems.append(f"{rel(p, c.path)}: no numeric Version: line")
        if c.status not in {"draft", "frozen"}:
            problems.append(f"{rel(p, c.path)}: Status is {c.status!r}, not draft or frozen")
        if not c.features:
            problems.append(f"{rel(p, c.path)}: no Features: line")
        check_split(p, c, problems)
        for f in [c.path, *part_files(p, c.name)]:
            if any(h.startswith("Impact") for h in top_headings(f.read_text(encoding="utf-8"))):
                problems.append(f"{rel(p, f)}: has an Impact section. Impact lives in docs/contracts/<feature-id>/impact.md")
    for feature in load_features(p).values():
        for t in feature.tasks:
            if t.status not in {"open", "done"}:
                problems.append(f"{rel(p, t.path)}: Status is {t.status!r}, not open or done")
            if t.status == "done":
                continue  # done tasks are history; their pointers are left as they were
            if t.assignee not in ASSIGNEES:
                problems.append(f"{rel(p, t.path)}: Assignee {t.assignee!r} is not a task assignee")
            problems += task_path_problems(p, t)
            texts = []
            for c in t.contracts:
                target = p.root / c
                if not target.exists():
                    problems.append(f"{rel(p, t.path)}: Contract {c} does not exist")
                else:
                    texts.append(target.read_text(encoding="utf-8").lower())
                    texts += [f.read_text(encoding="utf-8").lower() for f in part_files(p, target.stem)]
            for line in section(t.text, "Read in the contract").splitlines():
                names = line.lstrip("- ").split(":", 1)[-1]
                for name in (n.strip(" `.") for n in names.split(",")):
                    if name and texts and not any(name.lower() in text for text in texts):
                        problems.append(f"{rel(p, t.path)}: Read in the contract names {name!r}, not found in its contract")
    index = p.contracts / "INDEX.md"
    if not index.exists() or index.read_text(encoding="utf-8") != render_index(contracts):
        problems.append("docs/contracts/INDEX.md is missing or out of date: run scripts/contracts.sh index")
    from split_contract import check_manifest  # the proof that a split lost no line, read from git

    proof_problems, proof_info = check_manifest(p.root)
    problems += proof_problems
    for line in proof_info + problems:
        print(line)
    print("verify: ok" if not problems else f"verify: {len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_index(p: Paths) -> int:
    for hub in refresh_hubs(p):
        print(f"Written: {rel(p, hub)} (part table)")
    safe_write(p, p.contracts / "INDEX.md", render_index(load_contracts(p)))
    print("Written: docs/contracts/INDEX.md")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Contracts and close-out tool. Run with no command for the overview.")
    ap.add_argument("--root", type=Path, default=REPO, help="repo root (default: this repo)")
    ap.add_argument("--brief", action="store_true", help="overview: only features ready to close out")
    sub = ap.add_subparsers(dest="command")
    co = sub.add_parser("close-out", help="show or write a feature's close-out")
    co.add_argument("feature_id", nargs="?", help="e.g. DRA-29. Without it, list features ready to close out")
    co.add_argument("--write", action="store_true", help="write the close-out. Without it, nothing is written")
    co.add_argument("--summary", help="one line on what changed, for the CHANGELOG")
    co.add_argument("--accept-open", action="store_true", help="the Director accepted the open findings and observations")
    co.add_argument("--interfaces", action="store_true", help="also regenerate the Interface blocks of the frozen contracts from the code (off by default)")
    ifc = sub.add_parser("interface", help="sample: a module's current Interface block next to the generated one. Writes nothing")
    ifc.add_argument("module", help="e.g. game/core/drifters/satellite.py")
    sub.add_parser("verify", help="check headers, task pointers, INDEX.md, hubs and parts")
    sub.add_parser("index", help="rebuild docs/contracts/INDEX.md and the hubs' part tables")
    args = ap.parse_args()

    p = Paths(args.root.resolve())
    if args.command == "close-out":
        return cmd_close_out(p, args.feature_id, args.write, args.summary, args.accept_open, args.interfaces)
    if args.command == "interface":
        return cmd_interface(p, args.module)
    if args.command == "verify":
        return cmd_verify(p)
    if args.command == "index":
        return cmd_index(p)
    return cmd_overview(p, args.brief)


if __name__ == "__main__":
    sys.exit(main())
