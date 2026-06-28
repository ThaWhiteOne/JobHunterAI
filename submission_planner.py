import argparse
import json
from pathlib import Path
from typing import Any

from file_utils import write_text_file


REQUIRED_PACKET_KEYS = [
    "submission_status",
    "automation_allowed",
    "readiness",
    "job",
    "files",
    "guardrails",
]

APPLICATION_FILE_KEYS = [
    ("resume_markdown", "Resume"),
    ("cover_letter_markdown", "Cover letter"),
    ("linkedin_message", "LinkedIn message"),
]

REPORT_FILE_KEYS = [
    ("ready_to_apply_report", "Readiness report"),
    ("recruiter_review", "Recruiter review"),
    ("ai_recruiter_review", "AI recruiter review"),
    ("automation_report", "Automation report"),
    ("manifest", "Application manifest"),
    ("pipeline_report", "Pipeline report"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a non-submitting application submission plan."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or application_packet.json path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write submission_plan.md beside application_packet.json.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when the application packet has readiness warnings.",
    )
    return parser.parse_args()


def resolve_packet_path(path: Path) -> Path:
    if path.suffix.lower() == ".json":
        return path
    return path / "application_packet.json"


def submission_plan_path(packet_path: Path) -> Path:
    return packet_path.parent / "submission_plan.md"


def load_packet(path: Path) -> dict[str, Any]:
    packet_path = resolve_packet_path(path)
    if not packet_path.exists():
        raise FileNotFoundError(f"Missing application packet: {packet_path}")
    if not packet_path.is_file():
        raise FileNotFoundError(f"Expected a file but found something else: {packet_path}")

    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in application packet: {packet_path}") from error

    if not isinstance(packet, dict):
        raise ValueError("Application packet must contain a JSON object.")

    missing_keys = [
        key for key in REQUIRED_PACKET_KEYS if key not in packet
    ]
    if missing_keys:
        raise ValueError(
            "Application packet is missing required keys: "
            + ", ".join(missing_keys)
            + "."
        )
    return packet


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def file_lines(
    files: dict[str, str],
    file_keys: list[tuple[str, str]],
) -> list[str]:
    lines = []
    for key, label in file_keys:
        value = files.get(key)
        if value:
            lines.append(f"- {label}: {value}")
    return lines or ["- None found."]


def readiness_lines(readiness: dict[str, Any]) -> list[str]:
    return [
        f"- Status: {readiness.get('status', 'unknown')}",
        f"- Score: {readiness.get('score', 'unknown')}",
        f"- Ready: {readiness.get('is_ready', False)}",
    ]


def packet_has_blockers(packet: dict[str, Any]) -> bool:
    readiness = packet.get("readiness", {})
    return bool(readiness.get("errors")) or not bool(readiness.get("is_ready"))


def packet_has_warnings(packet: dict[str, Any]) -> bool:
    readiness = packet.get("readiness", {})
    return bool(readiness.get("warnings"))


def build_submission_plan(packet: dict[str, Any], packet_path: Path) -> str:
    readiness = packet.get("readiness", {})
    job = packet.get("job", {})
    files = packet.get("files", {})
    guardrails = packet.get("guardrails", [])
    errors = readiness.get("errors", [])
    warnings = readiness.get("warnings", [])

    lines = [
        "# Submission Plan",
        "",
        "Status: Prepared, not submitted",
        f"Application packet: {packet_path}",
        f"Submission status: {packet.get('submission_status', 'unknown')}",
        f"Automation allowed: {packet.get('automation_allowed', False)}",
        "",
        "This plan prepares the final apply step. It does not submit applications.",
        "",
        "## Job",
        "",
        f"- Detected role: {job.get('detected_role', '')}",
        f"- Role name: {job.get('role_display_name', '')}",
        f"- Job path: {job.get('job_path', '')}",
        f"- Job URL: {job.get('job_url') or 'not provided'}",
        "",
        "## Readiness",
        "",
        *readiness_lines(readiness),
        "",
        "## Blocking Issues",
        "",
        *bullet_lines(errors),
        "",
        "## Warnings",
        "",
        *bullet_lines(warnings),
        "",
        "## Application Files",
        "",
        *file_lines(files, APPLICATION_FILE_KEYS),
        "",
        "## Review Files",
        "",
        *file_lines(files, REPORT_FILE_KEYS),
        "",
        "## Guardrails",
        "",
        *bullet_lines(guardrails),
        "",
        "## Apply Sequence",
        "",
        "- Open the job URL, or locate the job manually if no URL is provided.",
        "- Use the generated resume and cover letter listed above.",
        "- Use the LinkedIn message only for recruiter or LinkedIn outreach.",
        "- Confirm dates, contact details, links, and profile-backed claims.",
        "- Submit only after explicit user approval.",
        "",
        "## Future Automation Contract",
        "",
        "- Browser automation may read this plan and packet in a later phase.",
        "- Browser automation must stop before final submission unless approved.",
        "- The packet currently sets automation_allowed to false.",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    packet_path = resolve_packet_path(args.path)
    try:
        packet = load_packet(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Submission plan failed.\nError: {error}") from error

    plan = build_submission_plan(packet, packet_path)
    print(plan)
    if args.write:
        path = submission_plan_path(packet_path)
        write_text_file(path, plan)
        print("")
        print(f"Submission plan written: {path}")

    if packet_has_blockers(packet) or (args.strict and packet_has_warnings(packet)):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
