import argparse
import json
from pathlib import Path
from typing import Any

from apply_readiness_gate import (
    ApplyReadinessResult,
    check_apply_readiness,
    load_form_fill_plan,
    resolve_form_fill_plan_path,
)
from file_utils import write_text_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a non-submitting browser automation dry run."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or form_fill_plan.json path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write browser_dry_run.json and browser_dry_run.md beside the plan.",
    )
    return parser.parse_args()


def browser_dry_run_json_path(plan_path: Path) -> Path:
    return plan_path.parent / "browser_dry_run.json"


def browser_dry_run_markdown_path(plan_path: Path) -> Path:
    return plan_path.parent / "browser_dry_run.md"


def plan_job_url(plan: dict[str, Any]) -> str:
    value = str(plan.get("job", {}).get("job_url", "")).strip()
    if value.lower() == "not provided":
        return ""
    return value


def action(
    step: int,
    name: str,
    target: str,
    status: str,
    note: str,
    value: str = "",
    source: str = "",
) -> dict[str, Any]:
    return {
        "step": step,
        "action": name,
        "target": target,
        "status": status,
        "value": value,
        "source": source,
        "note": note,
    }


def contact_actions(plan: dict[str, Any], start_step: int) -> list[dict[str, Any]]:
    actions = []
    step = start_step
    for field in plan.get("contact_fields", []):
        field_name = str(field.get("field", ""))
        field_action = str(field.get("action", ""))
        value = str(field.get("value", ""))
        source = str(field.get("source", ""))
        status = "ready" if field_action == "fill" and value else "needs_source_value"
        actions.append(
            action(
                step,
                "fill_contact_field",
                field_name,
                status,
                "Use only the value from the candidate profile.",
                value=value if status == "ready" else "",
                source=source,
            )
        )
        step += 1
    return actions


def document_actions(plan: dict[str, Any], start_step: int) -> list[dict[str, Any]]:
    actions = []
    step = start_step
    for document_name, document in plan.get("document_uploads", {}).items():
        document_action = str(document.get("action", ""))
        path = str(document.get("path", ""))
        status = "ready" if document_action == "upload" and path else "missing"
        actions.append(
            action(
                step,
                "upload_document",
                str(document_name),
                status,
                "Upload the prepared local document only.",
                value=path if status == "ready" else "",
                source=str(document.get("file_key", "")),
            )
        )
        step += 1
    return actions


def answer_actions(plan: dict[str, Any], start_step: int) -> list[dict[str, Any]]:
    actions = []
    step = start_step
    for field in plan.get("application_answer_fields", []):
        field_name = str(field.get("field", ""))
        field_action = str(field.get("action", ""))
        value = str(field.get("value", ""))
        status = "ready" if field_action == "fill" and value else "needs_source_value"
        actions.append(
            action(
                step,
                "fill_application_answer",
                field_name,
                status,
                "Do not guess screening-question answers.",
                value=value if status == "ready" else "",
                source=str(field.get("source", "")),
            )
        )
        step += 1
    return actions


def build_browser_actions(plan: dict[str, Any]) -> list[dict[str, Any]]:
    actions = [
        action(
            1,
            "verify_guardrails",
            "form_fill_plan",
            "ready",
            "Confirm submission is disabled and stop-before-submit is enabled.",
        )
    ]
    url = plan_job_url(plan)
    actions.append(
        action(
            2,
            "open_job_page",
            "job_url",
            "ready" if url else "needs_manual_location",
            "Open the job page, or locate it manually if no URL is saved.",
            value=url,
            source="form_fill_plan.job.job_url",
        )
    )

    next_step = len(actions) + 1
    actions.extend(contact_actions(plan, next_step))
    next_step = len(actions) + 1
    actions.extend(document_actions(plan, next_step))
    next_step = len(actions) + 1
    actions.extend(answer_actions(plan, next_step))

    outreach = plan.get("outreach", {}).get("linkedin_message", {})
    linkedin_path = str(outreach.get("path", ""))
    actions.append(
        action(
            len(actions) + 1,
            "prepare_outreach_message",
            "linkedin_message",
            "ready" if linkedin_path else "missing",
            "Use only for recruiter or LinkedIn outreach when needed.",
            value=linkedin_path,
            source="form_fill_plan.outreach.linkedin_message",
        )
    )
    actions.append(
        action(
            len(actions) + 1,
            "stop_before_submit",
            "final_submit_button",
            "stop",
            "Do not click final submit in this dry run.",
        )
    )
    return actions


def build_browser_dry_run(
    plan: dict[str, Any],
    readiness: ApplyReadinessResult,
) -> dict[str, Any]:
    return {
        "status": "ready" if readiness.is_ready else "blocked",
        "submission_allowed": False,
        "stop_before_submit": True,
        "job": plan.get("job", {}),
        "readiness": {
            "status": readiness.status,
            "errors": readiness.errors,
            "warnings": readiness.warnings,
        },
        "actions": build_browser_actions(plan),
        "guardrails": [
            *plan.get("guardrails", []),
            "Dry run only: do not click final submit.",
        ],
    }


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def markdown_lines_for_actions(actions: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in actions:
        value = f" ({item['value']})" if item.get("value") else ""
        lines.append(
            f"- {item['step']}. {item['action']} -> {item['target']}: "
            f"{item['status']}{value}"
        )
    return lines or ["- None."]


def build_markdown_report(dry_run: dict[str, Any], plan_path: Path) -> str:
    status = "Ready" if dry_run["status"] == "ready" else "Blocked"
    job = dry_run.get("job", {})
    readiness = dry_run.get("readiness", {})
    lines = [
        "# Browser Automation Dry Run",
        "",
        f"Status: {status}",
        f"Form-fill plan: {plan_path}",
        f"Submission allowed: {dry_run['submission_allowed']}",
        f"Stop before submit: {dry_run['stop_before_submit']}",
        "",
        "This report prepares future browser automation actions.",
        "It does not open browsers, fill forms, click apply, or submit applications.",
        "",
        "## Job",
        "",
        f"- Detected role: {job.get('detected_role', '')}",
        f"- Role name: {job.get('role_display_name', '')}",
        f"- Job URL: {plan_job_url(dry_run) or 'not provided'}",
        "",
        "## Readiness",
        "",
        f"- Status: {readiness.get('status', 'unknown')}",
        "",
        "## Blocking Issues",
        "",
        *bullet_lines(readiness.get("errors", [])),
        "",
        "## Warnings",
        "",
        *bullet_lines(readiness.get("warnings", [])),
        "",
        "## Dry Run Actions",
        "",
        *markdown_lines_for_actions(dry_run.get("actions", [])),
        "",
        "## Guardrails",
        "",
        *bullet_lines(dry_run.get("guardrails", [])),
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    plan_path = resolve_form_fill_plan_path(args.path)
    try:
        plan = load_form_fill_plan(args.path)
        readiness = check_apply_readiness(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Browser dry run failed.\nError: {error}") from error

    dry_run = build_browser_dry_run(plan, readiness)
    json_report = json.dumps(dry_run, indent=2)
    markdown_report = build_markdown_report(dry_run, plan_path)
    print(markdown_report)

    if args.write:
        json_path = browser_dry_run_json_path(plan_path)
        markdown_path = browser_dry_run_markdown_path(plan_path)
        write_text_file(json_path, json_report)
        write_text_file(markdown_path, markdown_report)
        print("")
        print(f"Browser dry-run JSON written: {json_path}")
        print(f"Browser dry-run report written: {markdown_path}")

    if not readiness.is_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
