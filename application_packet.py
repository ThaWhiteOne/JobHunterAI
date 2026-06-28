import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation_unit import load_manifest
from draft_reviewer import resolve_path
from file_utils import write_text_file
from readiness_checker import check_readiness, resolve_manifest_path


CORE_PACKET_FILES = {
    "resume_markdown": "resume.md",
    "cover_letter_markdown": "cover_letter.md",
    "linkedin_message": "linkedin_message.txt",
    "manifest": "application_manifest.json",
    "automation_report": "automation_report.md",
    "recruiter_review": "recruiter_review.md",
    "ready_to_apply_report": "ready_to_apply_report.md",
}

OPTIONAL_PACKET_FILES = {
    "resume_docx": "resume.docx",
    "cover_letter_docx": "cover_letter.docx",
    "resume_pdf": "resume.pdf",
    "cover_letter_pdf": "cover_letter.pdf",
    "ai_revision_notes": "ai_revision_notes.md",
    "ai_recruiter_review": "ai_recruiter_review.md",
    "pipeline_report": "pipeline_report.md",
    "batch_report": "batch_report.md",
    "job_description": "job_description.txt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a structured application packet for future apply automation."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or application_manifest.json path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write application_packet.json beside the manifest.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when the readiness check has warnings.",
    )
    return parser.parse_args()


def packet_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "application_packet.json"


def existing_file_map(output_dir: Path, candidates: dict[str, str]) -> dict[str, str]:
    files = {}
    for key, filename in candidates.items():
        path = output_dir / filename
        if path.exists():
            files[key] = path.as_posix()
    return files


def read_first_line_value(path: Path, label: str) -> str:
    if not path.exists() or not path.is_file():
        return ""

    prefix = f"{label}:"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith(prefix.lower()):
            return line.split(":", 1)[1].strip()
    return ""


def extract_job_url(manifest: dict[str, Any], manifest_path: Path) -> str:
    output_job_text = manifest_path.parent / "job_description.txt"
    url = read_first_line_value(output_job_text, "URL")
    if url and url != "not provided":
        return url

    job_path_text = manifest.get("job_path")
    if not job_path_text:
        return ""

    job_path = resolve_path(str(job_path_text), manifest_path)
    url = read_first_line_value(job_path, "URL")
    if url and url != "not provided":
        return url
    return ""


def build_application_packet(path: Path) -> dict[str, Any]:
    manifest_path = resolve_manifest_path(path)
    manifest = load_manifest(manifest_path)
    readiness = check_readiness(manifest_path)
    output_dir = manifest_path.parent

    packet = {
        "packet_created_at": datetime.now(timezone.utc).isoformat(),
        "submission_status": "prepared_not_submitted",
        "automation_allowed": False,
        "automation_note": (
            "This packet is for manual review or future automation. "
            "It must not submit applications without explicit user approval."
        ),
        "readiness": {
            "status": readiness.status,
            "score": readiness.score,
            "is_ready": readiness.is_ready,
            "errors": readiness.errors,
            "warnings": readiness.warnings,
        },
        "job": {
            "job_path": str(manifest.get("job_path", "")),
            "job_url": extract_job_url(manifest, manifest_path),
            "detected_role": manifest.get("detected_role", ""),
            "role_display_name": manifest.get("role_display_name", ""),
            "matched_keywords": manifest.get("matched_keywords", []),
            "requirement_lines": manifest.get("requirement_lines", []),
        },
        "tracking": {
            "tracked_job_id": manifest.get("tracked_job_id"),
        },
        "files": {
            **existing_file_map(output_dir, CORE_PACKET_FILES),
            **existing_file_map(output_dir, OPTIONAL_PACKET_FILES),
        },
        "guardrails": manifest.get("automation_guardrails", []),
        "next_action": (
            "Use the listed files for a final user-approved application step. "
            "Do not submit automatically."
        ),
    }
    return packet


def build_packet_report(packet: dict[str, Any]) -> str:
    return json.dumps(packet, indent=2)


def main() -> None:
    args = parse_args()
    try:
        packet = build_application_packet(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Application packet failed.\nError: {error}") from error

    report = build_packet_report(packet)
    print(report)
    if args.write:
        manifest_path = resolve_manifest_path(args.path)
        path = packet_path(manifest_path)
        write_text_file(path, report)
        print("")
        print(f"Application packet written: {path}")

    readiness = packet["readiness"]
    if readiness["errors"] or (args.strict and readiness["warnings"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
