#!/usr/bin/env python3
"""Token and cost report for Claude Code sessions in this project.

Reads the session transcripts Claude Code keeps under
~/.claude/projects/<project>/ and reports, per ticket and agent: turns,
peak context, cache writes and reads, output, thinking, cold turns and
an estimated cost in USD.

A run is one main session (agent "main") or one subagent transcript
(agent = its agentType). Each subagent run is credited to the first
ticket id in its spawn prompt. Main-session turns are credited to the
last ticket id seen before that turn, in what the user typed or in an agent
the session spawned, so one main session can span several tickets.
Turns before the first ticket id go to the session's first ticket.

A cold turn is a turn after the first whose cache write is over half of
its context: the prompt cache had expired or was invalidated, and the
whole context was written again.

Standard library only. Read-only: it never writes a file.

Usage:
  python3 scripts/token_report.py                    # by ticket and agent
  python3 scripts/token_report.py --ticket DRA-29
  python3 scripts/token_report.py --by run --since 2026-10-01
  python3 scripts/token_report.py --json
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# USD per million tokens. Cache writes are priced from input: 1.25x for the
# 5-minute cache, 2x for the 1-hour cache. Source: Anthropic pricing as of
# 2026-10-06. Update this table when prices or models change.
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.20},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_read": 0.01},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00, "cache_read": 0.10},
}
WRITE_5M = 1.25
WRITE_1H = 2.0

TICKET = re.compile(r"\b(?:DRA|DEMO)-\d+\b")
MODE = re.compile(r"\b((?:[A-Z][a-z-]+)(?: [a-z-]+)?) (?:mode|run)\b")
NOISE = re.compile(r"<(system-reminder|local-command-stdout|local-command-caveat)>.*?</\1>", re.S)
RESUME = re.compile(r"The coordinator sent a message")
SPAWN_TOOLS = {"Agent", "Task", "Skill", "SendMessage"}
COLD_SHARE = 0.5
COLD_MIN_CONTEXT = 20_000


@dataclass
class Turn:
    model: str
    input: int = 0
    write_5m: int = 0
    write_1h: int = 0
    read: int = 0
    output: int = 0
    thinking: int = 0
    visible_chars: int = 0
    ticket: str = "-"

    @property
    def context(self) -> int:
        return self.input + self.write_5m + self.write_1h + self.read

    @property
    def output_est(self) -> int:
        # Early log lines of a message carry partial output counts; the
        # visible content gives a floor when the final count is missing.
        return max(self.output, self.visible_chars // 4)

    def cost(self) -> float:
        p = price_for(self.model)
        return (
            self.input * p["input"]
            + self.write_5m * p["input"] * WRITE_5M
            + self.write_1h * p["input"] * WRITE_1H
            + self.read * p["cache_read"]
            + self.output_est * p["output"]
        ) / 1e6


@dataclass
class Run:
    path: Path
    agent: str
    session: str
    description: str = ""
    mode: str = "-"
    ticket: str = "-"
    start: str = ""
    resumes: int = 0
    tool_result_chars: int = 0
    turns: list[Turn] = field(default_factory=list)


_unknown_models: set[str] = set()


def price_for(model: str) -> dict[str, float]:
    for key, p in PRICES.items():
        if model.startswith(key):
            return p
    if model != "<synthetic>":
        _unknown_models.add(model)
    return PRICES["claude-opus-5-5"]


def user_text(content: object) -> str:
    """Text a person or a spawn prompt typed, without tool results or reminders."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    else:
        return ""
    return NOISE.sub("", text).strip()


def tool_result_chars(content: object) -> int:
    if not isinstance(content, list):
        return 0
    total = 0
    for c in content:
        if isinstance(c, dict) and c.get("type") == "tool_result":
            inner = c.get("content")
            total += len(inner) if isinstance(inner, str) else len(json.dumps(inner or ""))
    return total


def main_ticket(text: str) -> str | None:
    found = TICKET.findall(text)
    if not found:
        return None
    return collections.Counter(found).most_common(1)[0][0]


def load_run(path: Path, agent: str, session: str, description: str = "") -> Run:
    run = Run(path=path, agent=agent, session=session, description=description)
    by_id: dict[str, Turn] = {}
    order: list[str] = []
    current_ticket = "-"
    prompts = 0
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = d.get("type")
        msg = d.get("message") or {}
        if kind == "user":
            content = msg.get("content")
            run.tool_result_chars += tool_result_chars(content)
            text = user_text(content)
            if RESUME.match(text):
                run.resumes += 1
                continue
            if not text or d.get("isMeta"):
                continue
            if not run.start:
                run.start = d.get("timestamp", "")
            prompts += 1
            if agent == "main":
                current_ticket = main_ticket(text) or current_ticket
            elif prompts == 1:
                m = TICKET.search(text) or TICKET.search(description)
                run.ticket = m.group(0) if m else "-"
                mm = MODE.search(text)
                run.mode = mm.group(1) if mm else "-"
                current_ticket = run.ticket
            continue
        if kind != "assistant" or not msg.get("usage"):
            continue
        mid = msg.get("id") or d.get("requestId") or str(len(order))
        u = msg["usage"]
        turn = by_id.get(mid)
        if turn is None:
            turn = Turn(model=msg.get("model") or "?", ticket=current_ticket)
            by_id[mid] = turn
            order.append(mid)
            if not run.start:
                run.start = d.get("timestamp", "")
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
        w5m = cc.get("ephemeral_5m_input_tokens")
        if w5m is None:
            w5m = (u.get("cache_creation_input_tokens", 0) or 0) - w1h
        turn.input = max(turn.input, u.get("input_tokens", 0) or 0)
        turn.write_5m = max(turn.write_5m, w5m or 0)
        turn.write_1h = max(turn.write_1h, w1h)
        turn.read = max(turn.read, u.get("cache_read_input_tokens", 0) or 0)
        turn.output = max(turn.output, u.get("output_tokens", 0) or 0)
        turn.thinking = max(turn.thinking, (u.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0)
        for c in msg.get("content") or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text":
                turn.visible_chars += len(c.get("text", ""))
            elif c.get("type") == "tool_use":
                turn.visible_chars += len(json.dumps(c.get("input", {})))
                if agent == "main" and c.get("name") in SPAWN_TOOLS:
                    current_ticket = main_ticket(json.dumps(c.get("input", {}))) or current_ticket
    run.turns = [by_id[i] for i in order]
    if agent == "main":
        # Turns before the first ticket id (the planning talk) go to the
        # session's first ticket.
        first = next((t.ticket for t in run.turns if t.ticket != "-"), "-")
        for t in run.turns:
            if t.ticket != "-":
                break
            t.ticket = first
    return run


def load_runs(project_dir: Path) -> list[Run]:
    runs = []
    for top in sorted(project_dir.glob("*.jsonl")):
        runs.append(load_run(top, "main", top.stem))
    for sub in sorted(project_dir.glob("*/subagents/*.jsonl")):
        meta_path = sub.with_suffix(".meta.json")
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                pass
        runs.append(load_run(sub, meta.get("agentType", "?"), sub.parent.parent.name, meta.get("description", "")))
    return [r for r in runs if r.turns]


def cold_turns(turns: list[Turn]) -> int:
    return sum(
        1
        for t in turns[1:]
        if t.context >= COLD_MIN_CONTEXT and (t.write_5m + t.write_1h) > COLD_SHARE * t.context
    )


def summarize(turns: list[Turn]) -> dict[str, float]:
    return {
        "turns": len(turns),
        "peak_ctx": max((t.context for t in turns), default=0),
        "write": sum(t.write_5m + t.write_1h for t in turns),
        "read": sum(t.read for t in turns),
        "output": sum(t.output_est for t in turns),
        "thinking": sum(t.thinking for t in turns),
        "cold": cold_turns(turns),
        "usd": sum(t.cost() for t in turns),
    }


def fmt_k(n: float) -> str:
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}k"
    return f"{n:.0f}"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))


def main() -> int:
    default_dir = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(Path.cwd()))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project-dir", type=Path, default=default_dir, help=f"transcripts folder (default: {default_dir})")
    ap.add_argument("--ticket", help="only this ticket id, e.g. DRA-29")
    ap.add_argument("--since", help="only runs that started on or after this date, YYYY-MM-DD")
    ap.add_argument("--by", choices=["ticket", "run"], default="ticket", help="group by ticket and agent, or list each run")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if not args.project_dir.is_dir():
        print(f"no transcripts folder: {args.project_dir}", file=sys.stderr)
        return 1
    runs = load_runs(args.project_dir)
    if args.since:
        runs = [r for r in runs if r.start[:10] >= args.since]

    if args.by == "run":
        rows, out = [], []
        for r in sorted(runs, key=lambda r: r.start):
            turns = [t for t in r.turns if not args.ticket or t.ticket == args.ticket]
            if not turns:
                continue
            s = summarize(turns)
            label = r.description or r.session[:8]
            out.append({"start": r.start, "agent": r.agent, "mode": r.mode, "ticket": r.ticket if r.agent != "main" else "*",
                        "resumes": r.resumes, "reads_tok": r.tool_result_chars // 4, "label": label, **s})
            rows.append([r.start[:16].replace("T", " "), r.agent, r.mode, out[-1]["ticket"], str(s["turns"]), fmt_k(s["peak_ctx"]),
                         fmt_k(s["write"]), fmt_k(s["read"]), fmt_k(s["output"]), fmt_k(s["thinking"]), str(s["cold"]),
                         str(r.resumes), f"{s['usd']:.2f}", label[:40]])
        if args.json:
            print(json.dumps(out, indent=1))
        else:
            print_table(["start", "agent", "mode", "ticket", "turns", "peak", "c.write", "c.read", "out", "think",
                         "cold", "resumes", "usd", "label"], rows)
    else:
        groups: dict[tuple[str, str], list[Turn]] = collections.defaultdict(list)
        run_count: collections.Counter[tuple[str, str]] = collections.Counter()
        for r in runs:
            seen = set()
            for t in r.turns:
                if args.ticket and t.ticket != args.ticket:
                    continue
                key = (t.ticket, r.agent if r.agent != "main" else "main")
                groups[key].append(t)
                seen.add(key)
            for key in seen:
                run_count[key] += 1
        rows, out = [], []
        total = 0.0
        for key in sorted(groups, key=lambda k: (k[0], -summarize(groups[k])["usd"])):
            s = summarize(groups[key])
            total += s["usd"]
            out.append({"ticket": key[0], "agent": key[1], "runs": run_count[key], **s})
            rows.append([key[0], key[1], str(run_count[key]), str(s["turns"]), fmt_k(s["peak_ctx"]), fmt_k(s["write"]),
                         fmt_k(s["read"]), fmt_k(s["output"]), fmt_k(s["thinking"]), str(s["cold"]), f"{s['usd']:.2f}"])
        if args.json:
            print(json.dumps(out, indent=1))
        else:
            print_table(["ticket", "agent", "runs", "turns", "peak", "c.write", "c.read", "out", "think", "cold", "usd"], rows)
            print(f"\ntotal usd: {total:.2f}")
    if _unknown_models:
        print(f"\nwarning: no price for {sorted(_unknown_models)}; priced as Opus 5.5", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
