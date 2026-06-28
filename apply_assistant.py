import argparse
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from file_utils import write_text_file
from submission_planner import load_packet, packet_has_blockers, resolve_packet_path


APPLICATION_FILE_KEYS = [
    ("resume_markdown", "Resume"),
    ("cover_letter_markdown", "Cover letter"),
    ("linkedin_message", "LinkedIn message"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a controlled browser apply session without submitting."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or application_packet.json path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write apply_session.md beside application_packet.json.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the job URL in the default browser. This does not submit anything.",
    )
    return parser.parse_args()


def apply_session_path(packet_path: Path) -> Path:
    return packet_path.parent / "apply_session.md"


def job_url(packet: dict[str, Any]) -> str:
    job = packet.get("job", {})
    raw_value = job.get("job_url")
    if not raw_value:
        return ""
    value = str(raw_value).strip()
    if value.lower() == "not provided":
        return ""
    return value


def is_supported_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def file_lines(files: dict[str, str]) -> list[str]:
    lines = []
    for key, label in APPLICATION_FILE_KEYS:
        value = files.get(key)
        if value:
            lines.append(f"- {label}: {value}")
    return lines or ["- No application files found in packet."]


def warning_lines(packet: dict[str, Any]) -> list[str]:
    readiness = packet.get("readiness", {})
    warnings = readiness.get("warnings", [])
    return [f"- {warning}" for warning in warnings] or ["- None."]


def build_apply_session_report(
    packet: dict[str, Any],
    packet_path: Path,
    browser_opened: bool,
) -> str:
    readiness = packet.get("readiness", {})
    job = packet.get("job", {})
    files = packet.get("files", {})
    url = job_url(packet)

    lines = [
        "# Apply Session",
        "",
        "Status: Prepared, not submitted",
        f"Application packet: {packet_path}",
        f"Browser opened: {browser_opened}",
        f"Automation allowed: {packet.get('automation_allowed', False)}",
        "",
        "This assistant can open the job page and list the prepared files.",
        "It does not fill forms, click apply, or submit applications.",
        "",
        "## Job",
        "",
        f"- Detected role: {job.get('detected_role', '')}",
        f"- Role name: {job.get('role_display_name', '')}",
        f"- Job URL: {url or 'not provided'}",
        "",
        "## Readiness",
        "",
        f"- Status: {readiness.get('status', 'unknown')}",
        f"- Score: {readiness.get('score', 'unknown')}",
        f"- Ready: {readiness.get('is_ready', False)}",
        "",
        "## Warnings",
        "",
        *warning_lines(packet),
        "",
        "## Files To Use",
        "",
        *file_lines(files),
        "",
        "## Stop Line",
        "",
        "- Stop before any final submit button.",
        "- Submit only after explicit user approval.",
        "- Do not change claims, dates, employers, education, or certifications on the job site.",
    ]
    return "\n".join(lines)


def open_job_url(packet: dict[str, Any]) -> bool:
    url = job_url(packet)
    if not url:
        raise ValueError("Application packet does not contain a job URL.")
    if not is_supported_url(url):
        raise ValueError(f"Unsupported job URL: {url}")
    return bool(webbrowser.open(url))


def main() -> None:
    args = parse_args()
    packet_path = resolve_packet_path(args.path)
    try:
        packet = load_packet(args.path)
        if packet_has_blockers(packet):
            raise ValueError("Application packet is not ready for an apply session.")
        browser_opened = open_job_url(packet) if args.open_browser else False
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Apply assistant failed.\nError: {error}") from error

    report = build_apply_session_report(packet, packet_path, browser_opened)
    print(report)
    if args.write:
        path = apply_session_path(packet_path)
        write_text_file(path, report)
        print("")
        print(f"Apply session written: {path}")


if __name__ == "__main__":
    main()
