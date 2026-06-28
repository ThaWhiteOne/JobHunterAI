import argparse
import json
from pathlib import Path
from typing import Any

from file_utils import write_text_file


READY_STATUSES = {"matched"}
STOP_STATUSES = {"stop_detected"}
NEEDS_REVIEW_STATUSES = {"missing_on_page", "stop_not_detected"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a non-executing page action plan from page inspection."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or page_inspection.json path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write page_action_plan.json and page_action_plan.md beside inspection.",
    )
    return parser.parse_args()


def resolve_page_inspection_path(path: Path) -> Path:
    if path.suffix.lower() == ".json":
        return path
    return path / "page_inspection.json"


def action_plan_json_path(inspection_path: Path) -> Path:
    return inspection_path.parent / "page_action_plan.json"


def action_plan_markdown_path(inspection_path: Path) -> Path:
    return inspection_path.parent / "page_action_plan.md"


def load_page_inspection(path: Path) -> dict[str, Any]:
    inspection_path = resolve_page_inspection_path(path)
    if not inspection_path.exists():
        raise FileNotFoundError(f"Missing page inspection file: {inspection_path}")
    try:
        inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in page inspection file: {inspection_path}") from error
    if not isinstance(inspection, dict):
        raise ValueError("Page inspection file must contain a JSON object.")
    if not isinstance(inspection.get("matches"), list):
        raise ValueError("Page inspection file must contain a matches list.")
    return inspection


def quote_selector_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def selector_for_field(field: dict[str, Any]) -> str:
    field_id = str(field.get("id", "")).strip()
    name = str(field.get("name", "")).strip()
    aria_label = str(field.get("aria_label", "")).strip()
    if field_id:
        return f"#{field_id}"
    if name:
        return f"[name='{quote_selector_value(name)}']"
    if aria_label:
        return f"[aria-label='{quote_selector_value(aria_label)}']"
    return ""


def status_for_match(match: dict[str, Any]) -> str:
    status = str(match.get("status", ""))
    if status in READY_STATUSES:
        return "ready"
    if status in STOP_STATUSES:
        return "stop"
    if status in NEEDS_REVIEW_STATUSES:
        return "needs_review"
    return "blocked"


def build_plan_step(match: dict[str, Any]) -> dict[str, Any]:
    field = match.get("field_details", {})
    if not isinstance(field, dict):
        field = {}
    step_status = status_for_match(match)
    return {
        "step": match.get("step", ""),
        "action": str(match.get("action", "")),
        "target": str(match.get("target", "")),
        "status": step_status,
        "selector": selector_for_field(field),
        "field": field,
        "execute_automatically": False,
        "note": "Selector plan only. Do not fill, upload, click, or submit.",
    }


def build_page_action_plan(inspection: dict[str, Any]) -> dict[str, Any]:
    steps = [build_plan_step(match) for match in inspection.get("matches", [])]
    ready_steps = sum(1 for step in steps if step["status"] == "ready")
    needs_review_steps = sum(1 for step in steps if step["status"] == "needs_review")
    blocked_steps = sum(1 for step in steps if step["status"] == "blocked")
    stop_steps = sum(1 for step in steps if step["status"] == "stop")
    return {
        "status": "ready_for_review" if needs_review_steps == 0 and blocked_steps == 0 else "needs_review",
        "submission_allowed": False,
        "stop_before_submit": True,
        "execute_automatically": False,
        "source": inspection.get("source", ""),
        "detected_fields": inspection.get("detected_fields", 0),
        "ready_steps": ready_steps,
        "needs_review_steps": needs_review_steps,
        "blocked_steps": blocked_steps,
        "stop_steps": stop_steps,
        "steps": steps,
        "guardrails": [
            *inspection.get("guardrails", []),
            "Page action plan only: do not execute automatically.",
            "Stop before final submit.",
        ],
    }


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def step_lines(steps: list[dict[str, Any]]) -> list[str]:
    lines = []
    for step in steps:
        selector = f" ({step['selector']})" if step.get("selector") else ""
        lines.append(
            f"- {step['step']}. {step['action']} -> {step['target']}: "
            f"{step['status']}{selector}"
        )
    return lines or ["- None."]


def build_markdown_report(plan: dict[str, Any]) -> str:
    status = "Ready for review" if plan["status"] == "ready_for_review" else "Needs review"
    lines = [
        "# Page Action Plan",
        "",
        f"Status: {status}",
        f"Source: {plan['source'] or 'not provided'}",
        f"Submission allowed: {plan['submission_allowed']}",
        f"Stop before submit: {plan['stop_before_submit']}",
        f"Execute automatically: {plan['execute_automatically']}",
        "",
        "This plan prepares selectors for future browser automation.",
        "It does not fill fields, upload files, click apply, or submit applications.",
        "",
        "## Summary",
        "",
        f"- Detected fields: {plan['detected_fields']}",
        f"- Ready steps: {plan['ready_steps']}",
        f"- Needs review steps: {plan['needs_review_steps']}",
        f"- Blocked steps: {plan['blocked_steps']}",
        f"- Stop steps: {plan['stop_steps']}",
        "",
        "## Planned Steps",
        "",
        *step_lines(plan["steps"]),
        "",
        "## Guardrails",
        "",
        *bullet_lines(plan["guardrails"]),
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    inspection_path = resolve_page_inspection_path(args.path)
    try:
        inspection = load_page_inspection(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Page action plan failed.\nError: {error}") from error

    plan = build_page_action_plan(inspection)
    json_report = json.dumps(plan, indent=2)
    markdown_report = build_markdown_report(plan)
    print(markdown_report)

    if args.write:
        json_path = action_plan_json_path(inspection_path)
        markdown_path = action_plan_markdown_path(inspection_path)
        write_text_file(json_path, json_report)
        write_text_file(markdown_path, markdown_report)
        print("")
        print(f"Page action plan JSON written: {json_path}")
        print(f"Page action plan report written: {markdown_path}")


if __name__ == "__main__":
    main()
