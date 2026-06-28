import argparse
from dataclasses import dataclass
from pathlib import Path

from automation_unit import load_manifest, missing_generated_files, missing_required_keys
from draft_reviewer import review_drafts
from file_utils import write_text_file


REQUIRED_OUTPUT_FILES = [
    "resume.md",
    "cover_letter.md",
    "linkedin_message.txt",
    "application_manifest.json",
    "automation_report.md",
    "recruiter_review.md",
]

OPTIONAL_OUTPUT_FILES = [
    "ai_revision_notes.md",
    "ai_recruiter_review.md",
    "pipeline_report.md",
    "resume.docx",
    "cover_letter.docx",
    "resume.pdf",
    "cover_letter.pdf",
]


@dataclass(frozen=True)
class ReadinessResult:
    output_dir: Path
    manifest_path: Path
    errors: list[str]
    warnings: list[str]
    optional_files: list[Path]
    score: int
    status: str

    @property
    def is_ready(self) -> bool:
        return not self.errors and self.score >= 85


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether a generated JobHunterAI package is ready to use."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or application_manifest.json path.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write ready_to_apply_report.md beside the manifest.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def resolve_manifest_path(path: Path) -> Path:
    if path.suffix.lower() == ".json":
        return path
    return path / "application_manifest.json"


def existing_optional_files(output_dir: Path) -> list[Path]:
    return [output_dir / filename for filename in OPTIONAL_OUTPUT_FILES if (output_dir / filename).exists()]


def missing_required_output_files(output_dir: Path) -> list[str]:
    return [filename for filename in REQUIRED_OUTPUT_FILES if not (output_dir / filename).exists()]


def check_readiness(path: Path) -> ReadinessResult:
    manifest_path = resolve_manifest_path(path)
    output_dir = manifest_path.parent
    errors = []
    warnings = []

    missing_required_outputs = missing_required_output_files(output_dir)
    if missing_required_outputs:
        errors.append(
            "Missing required package files: "
            + ", ".join(missing_required_outputs)
            + "."
        )

    manifest = load_manifest(manifest_path)
    missing_keys = missing_required_keys(manifest)
    if missing_keys:
        errors.append(f"Manifest is missing required keys: {', '.join(missing_keys)}.")

    missing_manifest_files = missing_generated_files(manifest, manifest_path)
    if missing_manifest_files:
        errors.append(
            "Manifest references missing generated files: "
            + ", ".join(missing_manifest_files)
            + "."
        )

    draft_review = review_drafts(manifest, manifest_path)
    for finding in draft_review.findings:
        line = f"{finding.title}: {finding.detail}"
        if finding.severity == "high":
            errors.append(line)
        else:
            warnings.append(line)

    if manifest.get("used_fallback_profile"):
        warnings.append(
            "The selected role profile was missing or empty, so the master profile was used."
        )
    if not manifest.get("tracked_job_id"):
        warnings.append("This generated package is not linked to a tracker job ID.")
    if not (output_dir / "ai_recruiter_review.md").exists():
        warnings.append("Optional AI recruiter review was not found.")

    status = "Ready" if not errors and draft_review.score >= 85 else "Not ready"
    if status == "Ready" and warnings:
        status = "Ready with warnings"

    return ReadinessResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        errors=errors,
        warnings=warnings,
        optional_files=existing_optional_files(output_dir),
        score=draft_review.score,
        status=status,
    )


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def path_lines(paths: list[Path]) -> list[str]:
    return [f"- {path}" for path in paths] or ["- None."]


def build_readiness_report(result: ReadinessResult) -> str:
    lines = [
        "# Ready To Apply Report",
        "",
        f"Status: {result.status}",
        f"Review score: {result.score}/100",
        f"Output folder: {result.output_dir}",
        f"Manifest: {result.manifest_path}",
        "",
        "This report is a final package gate. It does not submit applications.",
        "",
        "## Blocking Issues",
        "",
        *bullet_lines(result.errors),
        "",
        "## Warnings",
        "",
        *bullet_lines(result.warnings),
        "",
        "## Optional Files Found",
        "",
        *path_lines(result.optional_files),
        "",
        "## Final Action",
        "",
    ]
    if result.is_ready:
        lines.append("- Package is ready for a final human/apply step.")
    else:
        lines.append("- Fix blocking issues before applying.")
    return "\n".join(lines)


def readiness_report_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "ready_to_apply_report.md"


def main() -> None:
    args = parse_args()
    try:
        result = check_readiness(args.path)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Readiness check failed.\nError: {error}") from error

    report = build_readiness_report(result)
    print(report)
    if args.write_report:
        path = readiness_report_path(result.manifest_path)
        write_text_file(path, report)
        print("")
        print(f"Ready-to-apply report written: {path}")

    if result.errors or (args.strict and result.warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
