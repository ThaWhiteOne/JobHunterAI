import argparse
import json
from pathlib import Path
from typing import Any

from config import MASTER_PROFILE_PATH, PROFILES_DIR
from file_utils import read_text_file, write_text_file
from submission_planner import load_packet, packet_has_blockers, resolve_packet_path


PROFILE_LABELS = {
    "Name": "full_name",
    "Location": "location",
    "Email": "email",
    "Phone": "phone",
    "GitHub": "github",
    "LinkedIn": "linkedin",
}

DOCUMENT_UPLOAD_CHOICES = {
    "resume": ["resume_docx", "resume_pdf", "resume_markdown"],
    "cover_letter": [
        "cover_letter_docx",
        "cover_letter_pdf",
        "cover_letter_markdown",
    ],
}

USER_REVIEW_FIELDS = [
    "Work authorization",
    "Visa sponsorship",
    "Notice period / start date",
    "Salary expectation",
    "Custom screening questions",
    "Voluntary demographic questions",
]

APPLICATION_ANSWER_LABELS = {
    "Work authorization": "work_authorization",
    "Visa sponsorship": "visa_sponsorship",
    "Notice period / start date": "start_date",
    "Salary expectation": "salary_expectation",
    "Custom screening questions": "custom_screening_questions",
}

DEFAULT_APPLICATION_ANSWERS_PATH = PROFILES_DIR / "application_answers.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a safe form-fill plan from an application packet."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or application_packet.json path.",
    )
    parser.add_argument(
        "--profile",
        type=Path,
        default=MASTER_PROFILE_PATH,
        help="Candidate profile file used as the source of truth.",
    )
    parser.add_argument(
        "--answers",
        type=Path,
        default=DEFAULT_APPLICATION_ANSWERS_PATH,
        help="Optional local application answers file.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write form_fill_plan.json and form_fill_plan.md beside the packet.",
    )
    return parser.parse_args()


def parse_labeled_fields(text: str, labels: dict[str, str]) -> dict[str, str]:
    lines = text.splitlines()
    fields = {}
    index = 0
    while index < len(lines):
        line = lines[index].strip().lstrip("\ufeff")
        matched_label = None
        for label in labels:
            if line.lower().startswith(f"{label.lower()}:"):
                matched_label = label
                break

        if not matched_label:
            index += 1
            continue

        value = line.split(":", 1)[1].strip()
        if not value:
            value_lines = []
            lookahead = index + 1
            while lookahead < len(lines):
                next_line = lines[lookahead].strip()
                if not next_line:
                    break
                if any(
                    next_line.lower().startswith(f"{label.lower()}:")
                    for label in labels
                ):
                    break
                value_lines.append(next_line)
                lookahead += 1
            value = " ".join(value_lines).strip()

        fields[labels[matched_label]] = value
        index += 1
    return fields


def parse_profile_fields(profile_text: str) -> dict[str, str]:
    return parse_labeled_fields(profile_text, PROFILE_LABELS)


def parse_application_answers(answers_text: str) -> dict[str, str]:
    return parse_labeled_fields(answers_text, APPLICATION_ANSWER_LABELS)


def field_action(value: str) -> str:
    if not value or value.lower() in {"later", "(later)", "n/a", "na", "todo", "tbd"}:
        return "needs_profile_update"
    return "fill"


def build_contact_fields(profile_fields: dict[str, str]) -> list[dict[str, str]]:
    contact_fields = []
    for field_name in PROFILE_LABELS.values():
        value = profile_fields.get(field_name, "")
        action = field_action(value)
        contact_fields.append(
            {
                "field": field_name,
                "value": value if action == "fill" else "",
                "source": "profiles/master_profile.md",
                "action": action,
            }
        )
    return contact_fields


def select_document(files: dict[str, str], choices: list[str]) -> dict[str, str]:
    for key in choices:
        path = files.get(key)
        if path:
            return {"file_key": key, "path": path, "action": "upload"}
    return {"file_key": "", "path": "", "action": "missing"}


def build_document_uploads(files: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
        name: select_document(files, choices)
        for name, choices in DOCUMENT_UPLOAD_CHOICES.items()
    }


def build_answer_fields(answers: dict[str, str]) -> list[dict[str, str]]:
    answer_fields = []
    for label in USER_REVIEW_FIELDS:
        key = APPLICATION_ANSWER_LABELS.get(label)
        value = answers.get(key, "") if key else ""
        action = field_action(value) if key else "requires_user_source_value"
        if not key:
            value = ""
        answer_fields.append(
            {
                "field": label,
                "key": key or "",
                "value": value if action == "fill" else "",
                "source": "profiles/application_answers.md" if key else "",
                "action": action if action == "fill" else "requires_user_source_value",
                "note": "Do not guess or invent this value.",
            }
        )
    return answer_fields


def build_form_fill_plan(
    packet: dict[str, Any],
    profile_fields: dict[str, str],
    application_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    files = packet.get("files", {})
    job = packet.get("job", {})
    answers = application_answers or {}
    return {
        "status": "prepared_not_submitted",
        "submission_allowed": False,
        "stop_before_submit": True,
        "job": {
            "detected_role": job.get("detected_role", ""),
            "role_display_name": job.get("role_display_name", ""),
            "job_url": job.get("job_url", ""),
        },
        "contact_fields": build_contact_fields(profile_fields),
        "document_uploads": build_document_uploads(files),
        "outreach": {
            "linkedin_message": {
                "path": files.get("linkedin_message", ""),
                "action": "copy_when_needed" if files.get("linkedin_message") else "missing",
            }
        },
        "application_answer_fields": build_answer_fields(answers),
        "guardrails": [
            *packet.get("guardrails", []),
            "Do not fill protected demographic fields automatically.",
            "Do not submit the application automatically.",
        ],
    }


def json_plan_path(packet_path: Path) -> Path:
    return packet_path.parent / "form_fill_plan.json"


def markdown_plan_path(packet_path: Path) -> Path:
    return packet_path.parent / "form_fill_plan.md"


def markdown_lines_for_fields(fields: list[dict[str, str]]) -> list[str]:
    return [
        f"- {field['field']}: {field['action']}"
        + (f" ({field['value']})" if field["value"] else "")
        for field in fields
    ] or ["- None."]


def markdown_lines_for_documents(documents: dict[str, dict[str, str]]) -> list[str]:
    return [
        f"- {name}: {document['action']}"
        + (f" ({document['path']})" if document["path"] else "")
        for name, document in documents.items()
    ] or ["- None."]


def build_markdown_report(plan: dict[str, Any], packet_path: Path) -> str:
    lines = [
        "# Form Fill Plan",
        "",
        "Status: Prepared, not submitted",
        f"Application packet: {packet_path}",
        f"Submission allowed: {plan['submission_allowed']}",
        f"Stop before submit: {plan['stop_before_submit']}",
        "",
        "This plan prepares future browser form automation. It does not fill forms or submit applications.",
        "",
        "## Contact Fields",
        "",
        *markdown_lines_for_fields(plan["contact_fields"]),
        "",
        "## Document Uploads",
        "",
        *markdown_lines_for_documents(plan["document_uploads"]),
        "",
        "## User Review Fields",
        "",
        *[
            f"- {field['field']}: {field['action']}"
            + (f" ({field['value']})" if field["value"] else "")
            for field in plan["application_answer_fields"]
        ],
        "",
        "## Guardrails",
        "",
        *[f"- {guardrail}" for guardrail in plan["guardrails"]],
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    packet_path = resolve_packet_path(args.path)
    try:
        packet = load_packet(args.path)
        if packet_has_blockers(packet):
            raise ValueError("Application packet is not ready for form-fill planning.")
        profile_text = read_text_file(args.profile)
        answers_text = read_text_file(args.answers, required=False)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Form-fill planning failed.\nError: {error}") from error

    plan = build_form_fill_plan(
        packet,
        parse_profile_fields(profile_text),
        parse_application_answers(answers_text) if answers_text else {},
    )
    json_report = json.dumps(plan, indent=2)
    markdown_report = build_markdown_report(plan, packet_path)
    print(markdown_report)

    if args.write:
        json_path = json_plan_path(packet_path)
        md_path = markdown_plan_path(packet_path)
        write_text_file(json_path, json_report)
        write_text_file(md_path, markdown_report)
        print("")
        print(f"Form-fill JSON plan written: {json_path}")
        print(f"Form-fill Markdown plan written: {md_path}")


if __name__ == "__main__":
    main()
