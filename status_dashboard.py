import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from file_utils import write_text_file


STATUS_FILES = {
    "pipeline": "pipeline_report.md",
    "readiness": "ready_to_apply_report.md",
    "apply_readiness": "apply_readiness_report.md",
    "apply_prep": "apply_prep_report.md",
    "batch": "batch_report.md",
    "batch_apply_prep": "batch_apply_prep_report.md",
}


@dataclass(frozen=True)
class OutputSummary:
    output_dir: Path
    detected_role: str
    role_display_name: str
    statuses: dict[str, str]
    key_files: dict[str, bool]

    @property
    def overall_status(self) -> str:
        if any(status == "Not ready" for status in self.statuses.values()):
            return "Blocked"
        attention_statuses = {"Stopped", "FAILED", "Completed with failures"}
        if any(status in attention_statuses for status in self.statuses.values()):
            return "Attention needed"
        if any(status == "Ready with warnings" for status in self.statuses.values()):
            return "Ready with warnings"
        if self.statuses:
            return "Ready"
        return "Unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize generated JobHunterAI output folders."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Generated output folder or batch output root.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write status_dashboard.md in the selected folder.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def first_status_line(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return ""


def summarize_output_dir(output_dir: Path) -> OutputSummary:
    manifest = read_json(output_dir / "application_manifest.json")
    statuses = {
        name: status
        for name, filename in STATUS_FILES.items()
        if (status := first_status_line(output_dir / filename))
    }
    key_files = {
        "resume": (output_dir / "resume.md").exists(),
        "cover_letter": (output_dir / "cover_letter.md").exists(),
        "linkedin_message": (output_dir / "linkedin_message.txt").exists(),
        "application_packet": (output_dir / "application_packet.json").exists(),
        "form_fill_plan": (output_dir / "form_fill_plan.json").exists(),
        "apply_session": (output_dir / "apply_session.md").exists(),
    }
    return OutputSummary(
        output_dir=output_dir,
        detected_role=str(manifest.get("detected_role", "")),
        role_display_name=str(manifest.get("role_display_name", "")),
        statuses=statuses,
        key_files=key_files,
    )


def discover_output_dirs(path: Path) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(f"Missing output path: {path}")
    if not path.is_dir():
        raise FileNotFoundError(f"Expected an output folder but found: {path}")

    if (path / "application_manifest.json").exists() or (path / "apply_prep_report.md").exists():
        return [path]

    output_dirs = [
        child
        for child in sorted(path.iterdir())
        if child.is_dir()
        and (
            (child / "application_manifest.json").exists()
            or (child / "apply_prep_report.md").exists()
        )
    ]
    if output_dirs:
        return output_dirs
    return [path]


def status_lines(statuses: dict[str, str]) -> list[str]:
    return [f"- {name}: {status}" for name, status in statuses.items()] or ["- None found."]


def file_lines(files: dict[str, bool]) -> list[str]:
    return [
        f"- {name}: {'found' if exists else 'missing'}"
        for name, exists in files.items()
    ]


def summary_lines(summary: OutputSummary) -> list[str]:
    lines = [
        f"## {summary.output_dir.name}",
        "",
        f"Overall status: {summary.overall_status}",
        f"Output folder: {summary.output_dir}",
    ]
    if summary.detected_role:
        lines.append(f"Detected role: {summary.detected_role}")
    if summary.role_display_name:
        lines.append(f"Role name: {summary.role_display_name}")
    lines.extend(
        [
            "",
            "Statuses:",
            "",
            *status_lines(summary.statuses),
            "",
            "Key files:",
            "",
            *file_lines(summary.key_files),
        ]
    )
    return lines


def build_status_dashboard(path: Path) -> str:
    output_dirs = discover_output_dirs(path)
    summaries = [summarize_output_dir(output_dir) for output_dir in output_dirs]
    ready = sum(1 for summary in summaries if summary.overall_status.startswith("Ready"))
    blocked = sum(1 for summary in summaries if summary.overall_status == "Blocked")
    attention = sum(
        1 for summary in summaries if summary.overall_status == "Attention needed"
    )
    lines = [
        "# JobHunterAI Status Dashboard",
        "",
        f"Scanned path: {path}",
        f"Output folders: {len(summaries)}",
        f"Ready: {ready}",
        f"Blocked: {blocked}",
        f"Attention needed: {attention}",
        "",
        "This dashboard only summarizes local generated files. It does not submit applications.",
    ]
    for summary in summaries:
        lines.extend(["", *summary_lines(summary)])
    return "\n".join(lines)


def dashboard_path(path: Path) -> Path:
    return path / "status_dashboard.md"


def main() -> None:
    args = parse_args()
    try:
        dashboard = build_status_dashboard(args.path)
    except FileNotFoundError as error:
        raise SystemExit(f"Status dashboard failed.\nError: {error}") from error

    print(dashboard)
    if args.write:
        path = dashboard_path(args.path)
        write_text_file(path, dashboard)
        print("")
        print(f"Status dashboard written: {path}")


if __name__ == "__main__":
    main()
