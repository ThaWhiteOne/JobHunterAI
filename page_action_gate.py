import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from file_utils import write_text_file


REQUIRED_PLAN_KEYS = [
    "submission_allowed",
    "stop_before_submit",
    "execute_automatically",
    "ready_steps",
    "needs_review_steps",
    "blocked_steps",
    "stop_steps",
    "steps",
    "guardrails",
]


@dataclass(frozen=True)
class PageActionGateResult:
    plan_path: Path
    errors: list[str]
    warnings: list[str]

    @property
    def is_ready(self) -> bool:
        return not self.errors

    @property
    def status(self) -> str:
        if self.errors:
            return "Not ready"
        if self.warnings:
            return "Ready with warnings"
        return "Ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gate a page action plan before any future browser automation."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or page_action_plan.json path.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write page_action_gate_report.md beside the action plan.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def resolve_page_action_plan_path(path: Path) -> Path:
    if path.suffix.lower() == ".json":
        return path
    return path / "page_action_plan.json"


def page_action_gate_report_path(plan_path: Path) -> Path:
    return plan_path.parent / "page_action_gate_report.md"


def load_page_action_plan(path: Path) -> dict[str, Any]:
    plan_path = resolve_page_action_plan_path(path)
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing page action plan: {plan_path}")
    if not plan_path.is_file():
        raise FileNotFoundError(f"Expected a file but found something else: {plan_path}")
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in page action plan: {plan_path}") from error
    if not isinstance(plan, dict):
        raise ValueError("Page action plan must contain a JSON object.")

    missing_keys = [key for key in REQUIRED_PLAN_KEYS if key not in plan]
    if missing_keys:
        raise ValueError(
            "Page action plan is missing required keys: "
            + ", ".join(missing_keys)
            + "."
        )
    return plan


def validate_guardrails(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    if plan.get("submission_allowed") is not False:
        errors.append("Plan must keep submission_allowed set to false.")
    if plan.get("stop_before_submit") is not True:
        errors.append("Plan must keep stop_before_submit set to true.")
    if plan.get("execute_automatically") is not False:
        errors.append("Plan must keep execute_automatically set to false.")

    guardrails = " ".join(str(item) for item in plan.get("guardrails", []))
    if "submit" not in guardrails.lower():
        warnings.append("No explicit submit guardrail was found.")
    if "execute" not in guardrails.lower():
        warnings.append("No explicit execution guardrail was found.")
    return errors, warnings


def validate_steps(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    steps = plan.get("steps", [])
    if not isinstance(steps, list):
        return ["Page action plan steps must be a list."], warnings

    if plan.get("needs_review_steps", 0):
        errors.append("Plan still has steps that need review.")
    if plan.get("blocked_steps", 0):
        errors.append("Plan still has blocked steps.")
    actual_stop_steps = [
        step
        for step in steps
        if isinstance(step, dict) and str(step.get("status", "")) == "stop"
    ]
    if not actual_stop_steps:
        errors.append("Plan must include at least one stop step.")
    if not steps:
        errors.append("Plan must include at least one action step.")

    for step in steps:
        if not isinstance(step, dict):
            errors.append("Plan contains a non-object step.")
            continue
        status = str(step.get("status", ""))
        target = str(step.get("target", ""))
        selector = str(step.get("selector", ""))
        if step.get("execute_automatically") is not False:
            errors.append(f"Step must not execute automatically: {target}.")
        if status == "ready" and not selector:
            errors.append(f"Ready step is missing a selector: {target}.")
        if status == "stop" and "submit" not in target.lower():
            warnings.append(f"Stop step target should clearly name submit: {target}.")
    return errors, warnings


def check_page_action_plan(path: Path) -> PageActionGateResult:
    plan_path = resolve_page_action_plan_path(path)
    plan = load_page_action_plan(path)
    guardrail_errors, guardrail_warnings = validate_guardrails(plan)
    step_errors, step_warnings = validate_steps(plan)
    return PageActionGateResult(
        plan_path=plan_path,
        errors=[*guardrail_errors, *step_errors],
        warnings=[*guardrail_warnings, *step_warnings],
    )


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def build_page_action_gate_report(result: PageActionGateResult) -> str:
    lines = [
        "# Page Action Gate Report",
        "",
        f"Status: {result.status}",
        f"Page action plan: {result.plan_path}",
        "",
        "This gate checks whether selector-style page actions are safe for a future automation runner.",
        "It does not fill fields, upload files, click apply, or submit applications.",
        "",
        "## Blocking Issues",
        "",
        *bullet_lines(result.errors),
        "",
        "## Warnings",
        "",
        *bullet_lines(result.warnings),
        "",
        "## Final Action",
        "",
    ]
    if result.is_ready:
        lines.append("- Page action plan is ready for manual review of a future automation runner.")
    else:
        lines.append("- Fix blocking issues before any browser automation runner is built.")
    lines.extend(
        [
            "- Do not execute browser actions yet.",
            "- Do not submit applications automatically.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    try:
        result = check_page_action_plan(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Page action gate failed.\nError: {error}") from error

    report = build_page_action_gate_report(result)
    print(report)
    if args.write_report:
        path = page_action_gate_report_path(result.plan_path)
        write_text_file(path, report)
        print("")
        print(f"Page action gate report written: {path}")

    if result.errors or (args.strict and result.warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
