import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from file_utils import write_text_file


REQUIRED_PLAN_KEYS = [
    "submission_allowed",
    "stop_before_submit",
    "contact_fields",
    "document_uploads",
    "application_answer_fields",
    "guardrails",
]

REQUIRED_CONTACT_FIELDS = ["full_name", "location", "email", "phone"]
OPTIONAL_CONTACT_FIELDS = ["github", "linkedin"]
REQUIRED_DOCUMENTS = ["resume", "cover_letter"]
REQUIRED_ANSWER_KEYS = ["work_authorization", "visa_sponsorship", "start_date"]
OPTIONAL_ANSWER_KEYS = ["salary_expectation", "custom_screening_questions"]


@dataclass(frozen=True)
class ApplyReadinessResult:
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
        description="Check whether a form-fill plan is ready for future browser automation."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or form_fill_plan.json path.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write apply_readiness_report.md beside form_fill_plan.json.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def resolve_form_fill_plan_path(path: Path) -> Path:
    if path.suffix.lower() == ".json":
        return path
    return path / "form_fill_plan.json"


def apply_readiness_report_path(plan_path: Path) -> Path:
    return plan_path.parent / "apply_readiness_report.md"


def load_form_fill_plan(path: Path) -> dict[str, Any]:
    plan_path = resolve_form_fill_plan_path(path)
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing form-fill plan: {plan_path}")
    if not plan_path.is_file():
        raise FileNotFoundError(f"Expected a file but found something else: {plan_path}")

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in form-fill plan: {plan_path}") from error

    if not isinstance(plan, dict):
        raise ValueError("Form-fill plan must contain a JSON object.")

    missing_keys = [key for key in REQUIRED_PLAN_KEYS if key not in plan]
    if missing_keys:
        raise ValueError(
            "Form-fill plan is missing required keys: "
            + ", ".join(missing_keys)
            + "."
        )
    return plan


def fields_by_name(fields: list[dict[str, Any]], key_name: str) -> dict[str, dict[str, Any]]:
    return {
        str(field.get(key_name, "")): field
        for field in fields
        if isinstance(field, dict) and field.get(key_name)
    }


def validate_contact_fields(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    fields = fields_by_name(plan.get("contact_fields", []), "field")

    for field_name in REQUIRED_CONTACT_FIELDS:
        field = fields.get(field_name)
        if not field or field.get("action") != "fill" or not field.get("value"):
            errors.append(f"Required contact field is not ready: {field_name}.")

    for field_name in OPTIONAL_CONTACT_FIELDS:
        field = fields.get(field_name)
        if not field or field.get("action") != "fill":
            warnings.append(f"Optional contact field is not ready: {field_name}.")

    return errors, warnings


def validate_documents(plan: dict[str, Any]) -> list[str]:
    errors = []
    documents = plan.get("document_uploads", {})
    for document_name in REQUIRED_DOCUMENTS:
        document = documents.get(document_name, {})
        if document.get("action") != "upload" or not document.get("path"):
            errors.append(f"Required document upload is not ready: {document_name}.")
    return errors


def validate_answers(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    fields = fields_by_name(plan.get("application_answer_fields", []), "key")

    for answer_key in REQUIRED_ANSWER_KEYS:
        field = fields.get(answer_key)
        if not field or field.get("action") != "fill" or not field.get("value"):
            errors.append(f"Required application answer is not ready: {answer_key}.")

    for answer_key in OPTIONAL_ANSWER_KEYS:
        field = fields.get(answer_key)
        if not field or field.get("action") != "fill":
            warnings.append(f"Optional application answer is not ready: {answer_key}.")

    return errors, warnings


def validate_guardrails(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []

    if plan.get("submission_allowed") is not False:
        errors.append("Plan must keep submission_allowed set to false.")
    if plan.get("stop_before_submit") is not True:
        errors.append("Plan must keep stop_before_submit set to true.")

    guardrails = " ".join(str(item) for item in plan.get("guardrails", []))
    if "submit" not in guardrails.lower():
        warnings.append("No explicit submit guardrail was found.")

    return errors, warnings


def check_apply_readiness(path: Path) -> ApplyReadinessResult:
    plan_path = resolve_form_fill_plan_path(path)
    plan = load_form_fill_plan(path)

    errors = []
    warnings = []

    contact_errors, contact_warnings = validate_contact_fields(plan)
    answer_errors, answer_warnings = validate_answers(plan)
    guardrail_errors, guardrail_warnings = validate_guardrails(plan)

    errors.extend(contact_errors)
    errors.extend(validate_documents(plan))
    errors.extend(answer_errors)
    errors.extend(guardrail_errors)
    warnings.extend(contact_warnings)
    warnings.extend(answer_warnings)
    warnings.extend(guardrail_warnings)

    return ApplyReadinessResult(
        plan_path=plan_path,
        errors=errors,
        warnings=warnings,
    )


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def build_apply_readiness_report(result: ApplyReadinessResult) -> str:
    lines = [
        "# Apply Readiness Report",
        "",
        f"Status: {result.status}",
        f"Form-fill plan: {result.plan_path}",
        "",
        "This gate checks whether future browser form automation has enough source-backed data.",
        "It does not fill forms, click apply, or submit applications.",
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
        lines.append("- Form-fill plan is ready for the next controlled automation phase.")
    else:
        lines.append("- Fix blocking issues before browser automation.")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    try:
        result = check_apply_readiness(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Apply readiness check failed.\nError: {error}") from error

    report = build_apply_readiness_report(result)
    print(report)

    if args.write_report:
        path = apply_readiness_report_path(result.plan_path)
        write_text_file(path, report)
        print("")
        print(f"Apply readiness report written: {path}")

    if result.errors or (args.strict and result.warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
