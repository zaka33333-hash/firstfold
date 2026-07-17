#!/usr/bin/env python3
"""Generate a self-contained FirstFold conversion audit from JSON input.

No third-party packages or network access are required.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path
from string import Template
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = ROOT / "templates" / "report.html"
DEFAULT_CSS = ROOT / "styles" / "report.css"

SEVERITIES = {"critical", "high", "medium", "low"}
EFFORTS = {"small", "medium", "large"}


class InputError(ValueError):
    """A friendly, actionable input-validation error."""


def error(path: str, message: str) -> None:
    raise InputError(f"{path}: {message}")


def need(obj: dict[str, Any], key: str, path: str, kind: type | tuple[type, ...]) -> Any:
    if key not in obj:
        error(path, "is required")
    value = obj[key]
    if not isinstance(value, kind):
        expected = "/".join(t.__name__ for t in kind) if isinstance(kind, tuple) else kind.__name__
        error(path, f"must be a {expected}")
    if isinstance(value, str) and not value.strip():
        error(path, "must not be empty")
    return value


def strings(items: Any, path: str, min_items: int = 0) -> list[str]:
    if not isinstance(items, list):
        error(path, "must be an array")
    if len(items) < min_items:
        error(path, f"must contain at least {min_items} item(s)")
    for index, value in enumerate(items):
        if not isinstance(value, str) or not value.strip():
            error(f"{path}[{index}]", "must be a non-empty string")
    return items


def validate(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        error("$", "must be a JSON object")
    meta = need(data, "meta", "meta", dict)
    for key in ("client_name", "website", "audit_title", "audit_date", "prepared_by"):
        need(meta, key, f"meta.{key}", str)
    if not isinstance(meta.get("fictional", False), bool):
        error("meta.fictional", "must be true or false when supplied")

    summary = need(data, "executive_summary", "executive_summary", dict)
    for key in ("headline", "overview", "opportunity"):
        need(summary, key, f"executive_summary.{key}", str)
    strings(need(summary, "key_findings", "executive_summary.key_findings", list), "executive_summary.key_findings", 1)

    issues = need(data, "issues", "issues", list)
    if not issues:
        error("issues", "must contain at least one issue")
    for i, issue in enumerate(issues):
        prefix = f"issues[{i}]"
        if not isinstance(issue, dict):
            error(prefix, "must be an object")
        for key in ("title", "impact", "effort", "finding", "recommendation"):
            need(issue, key, f"{prefix}.{key}", str)
        severity = need(issue, "severity", f"{prefix}.severity", str).lower()
        if severity not in SEVERITIES:
            error(f"{prefix}.severity", f"must be one of: {', '.join(sorted(SEVERITIES))}")
        effort = issue["effort"].lower()
        if effort not in EFFORTS:
            error(f"{prefix}.effort", f"must be one of: {', '.join(sorted(EFFORTS))}")
        strings(need(issue, "evidence", f"{prefix}.evidence", list), f"{prefix}.evidence", 1)

    hero = need(data, "hero_copy", "hero_copy", dict)
    for key in ("eyebrow", "headline", "subhead", "cta", "supporting_note"):
        need(hero, key, f"hero_copy.{key}", str)

    hypotheses = need(data, "test_hypotheses", "test_hypotheses", list)
    if len(hypotheses) != 5:
        error("test_hypotheses", "must contain exactly 5 hypotheses")
    for i, hypothesis in enumerate(hypotheses):
        prefix = f"test_hypotheses[{i}]"
        if not isinstance(hypothesis, dict):
            error(prefix, "must be an object")
        for key in ("hypothesis", "change", "success_metric"):
            need(hypothesis, key, f"{prefix}.{key}", str)

    plan = need(data, "action_plan", "action_plan", list)
    if len(plan) != 7:
        error("action_plan", "must contain exactly 7 days")
    expected_days = set(range(1, 8))
    actual_days: set[int] = set()
    for i, day in enumerate(plan):
        prefix = f"action_plan[{i}]"
        if not isinstance(day, dict):
            error(prefix, "must be an object")
        number = need(day, "day", f"{prefix}.day", int)
        actual_days.add(number)
        for key in ("focus", "actions", "deliverable"):
            need(day, key, f"{prefix}.{key}", str)
    if actual_days != expected_days:
        error("action_plan", "must include each day number 1 through 7 exactly once")
    return data


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def paragraphs(value: str) -> str:
    return "".join(f"<p>{esc(part)}</p>" for part in value.split("\n") if part.strip())


def list_items(values: list[str]) -> str:
    return "".join(f"<li>{esc(value)}</li>" for value in values)


def render_issues(issues: list[dict[str, Any]]) -> str:
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ordered = sorted(issues, key=lambda issue: (order[issue["severity"].lower()], issue["title"].lower()))
    cards = []
    for position, issue in enumerate(ordered, 1):
        cards.append(
            f'''<article class="issue issue--{esc(issue["severity"].lower())}">
  <div class="issue__topline"><span class="issue__number">{position:02d}</span><span class="badge badge--{esc(issue["severity"].lower())}">{esc(issue["severity"])}</span></div>
  <h3>{esc(issue["title"])}</h3>
  <dl class="issue__meta"><div><dt>Impact</dt><dd>{esc(issue["impact"])}</dd></div><div><dt>Effort</dt><dd>{esc(issue["effort"])}</dd></div></dl>
  <p><strong>What we observed:</strong> {esc(issue["finding"])}</p>
  <p><strong>Recommended move:</strong> {esc(issue["recommendation"])}</p>
  <div class="evidence"><span>Evidence</span><ul>{list_items(issue["evidence"])}</ul></div>
</article>'''
        )
    return "\n".join(cards)


def render_hypotheses(items: list[dict[str, str]]) -> str:
    return "\n".join(
        f'''<article class="hypothesis"><span>{i:02d}</span><div><h3>{esc(item["hypothesis"])}</h3><p><strong>Test:</strong> {esc(item["change"])}</p><p><strong>Win signal:</strong> {esc(item["success_metric"])}</p></div></article>'''
        for i, item in enumerate(items, 1)
    )


def render_plan(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f'''<article class="day"><span class="day__num">Day {item["day"]}</span><div><h3>{esc(item["focus"])}</h3><p>{esc(item["actions"])}</p><p class="deliverable"><strong>Deliverable:</strong> {esc(item["deliverable"])}</p></div></article>'''
        for item in sorted(items, key=lambda item: item["day"])
    )


def generate(data: dict[str, Any], template_path: Path, css_path: Path) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    css = css_path.read_text(encoding="utf-8")
    meta = data["meta"]
    summary = data["executive_summary"]
    hero = data["hero_copy"]
    fiction = '<p class="fiction-label">FICTIONAL DEMONSTRATION REPORT — not based on a real client or performance data.</p>' if meta.get("fictional") else ""
    return template.safe_substitute(
        css=css,
        report_title=esc(meta["audit_title"]),
        client_name=esc(meta["client_name"]),
        website=esc(meta["website"]),
        audit_date=esc(meta["audit_date"]),
        prepared_by=esc(meta["prepared_by"]),
        fictional_label=fiction,
        summary_headline=esc(summary["headline"]),
        summary_overview=paragraphs(summary["overview"]),
        summary_opportunity=esc(summary["opportunity"]),
        key_findings=list_items(summary["key_findings"]),
        issues=render_issues(data["issues"]),
        hero_eyebrow=esc(hero["eyebrow"]),
        hero_headline=esc(hero["headline"]),
        hero_subhead=esc(hero["subhead"]),
        hero_cta=esc(hero["cta"]),
        hero_note=esc(hero["supporting_note"]),
        hypotheses=render_hypotheses(data["test_hypotheses"]),
        plan=render_plan(data["action_plan"]),
        generated_at=dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a self-contained FirstFold HTML audit from JSON.")
    parser.add_argument("input", type=Path, help="Path to structured audit JSON")
    parser.add_argument("output", type=Path, help="Destination HTML file")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="HTML template path")
    parser.add_argument("--css", type=Path, default=DEFAULT_CSS, help="CSS stylesheet path")
    args = parser.parse_args()
    try:
        if not args.input.is_file():
            raise InputError(f"input: file not found: {args.input}")
        if not args.template.is_file() or not args.css.is_file():
            raise InputError("template/css: expected files were not found; pass --template and --css if moved")
        try:
            raw = json.loads(args.input.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InputError(f"input: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
        output = generate(validate(raw), args.template, args.css)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Generated {args.output}")
        return 0
    except (InputError, OSError) as exc:
        print(f"Audit generation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
