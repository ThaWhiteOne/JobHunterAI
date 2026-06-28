import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from config import OUTPUTS_DIR, SAMPLE_JOB_PATH
from file_utils import write_text_file


DEFAULT_PIPELINE_OUTPUT_DIR = OUTPUTS_DIR / "automated-application"


@dataclass(frozen=True)
class PipelineStep:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the JobHunterAI application package pipeline."
    )
    parser.add_argument(
        "job_file",
        nargs="?",
        type=Path,
        help="Optional path to a job description file.",
    )
    parser.add_argument(
        "--job",
        dest="job_option",
        type=Path,
        help="Optional path to a job description file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_PIPELINE_OUTPUT_DIR,
        help="Folder where generated files should be written.",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate AI drafts and run automatic AI revision.",
    )
    parser.add_argument(
        "--ai-review",
        action="store_true",
        help="Run optional AI recruiter review after the offline review.",
    )
    parser.add_argument(
        "--strict-profile",
        action="store_true",
        help="Stop when profile validation has warnings.",
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="Save this generated application to the local job tracker.",
    )
    parser.add_argument(
        "--company",
        default="",
        help="Company name for --track.",
    )
    parser.add_argument(
        "--position",
        default="",
        help="Job title for --track.",
    )
    parser.add_argument(
        "--url",
        default="",
        help="Job post URL for --track.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes for --track.",
    )
    return parser.parse_args()


def get_job_path(args: argparse.Namespace) -> Path:
    return args.job_option or args.job_file or SAMPLE_JOB_PATH


def run_step(name: str, command: list[str]) -> PipelineStep:
    result = subprocess.run(
        [sys.executable, *command],
        capture_output=True,
        text=True,
        check=False,
    )
    return PipelineStep(
        name=name,
        command=[sys.executable, *command],
        returncode=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def build_generation_command(args: argparse.Namespace) -> list[str]:
    command = [
        "main.py",
        "--job",
        str(get_job_path(args)),
        "--output-dir",
        str(args.output_dir),
        "--full-package",
    ]
    if args.ai:
        command.extend(["--ai-drafts", "--ai-auto-revise"])
    if args.track:
        command.append("--track")
        command.extend(["--company", args.company])
        command.extend(["--position", args.position])
        if args.url:
            command.extend(["--url", args.url])
        if args.notes:
            command.extend(["--notes", args.notes])
    return command


def build_pipeline_steps(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    manifest_path = args.output_dir / "application_manifest.json"
    profile_command = ["profile_validator.py", "--write-report"]
    if args.strict_profile:
        profile_command.append("--strict")

    review_command = [
        "automation_unit.py",
        "review",
        str(manifest_path),
        "--write-report",
    ]
    if args.ai_review:
        review_command.append("--ai-review")

    return [
        ("Profile validation", profile_command),
        ("Application package generation", build_generation_command(args)),
        (
            "Automation Unit check",
            [
                "automation_unit.py",
                "check",
                str(manifest_path),
                "--write-report",
            ],
        ),
        ("Recruiter review", review_command),
        (
            "Readiness check",
            [
                "readiness_checker.py",
                str(manifest_path),
                "--write-report",
            ],
        ),
    ]


def command_line(command: list[str]) -> str:
    return " ".join(command)


def build_step_report(step: PipelineStep) -> list[str]:
    status = "OK" if step.succeeded else "FAILED"
    lines = [
        f"## {step.name}",
        "",
        f"Status: {status}",
        f"Command: `{command_line(step.command)}`",
    ]
    if step.stdout:
        lines.extend(["", "Output:", "", "```text", step.stdout, "```"])
    if step.stderr:
        lines.extend(["", "Errors:", "", "```text", step.stderr, "```"])
    return lines


def build_pipeline_report(steps: list[PipelineStep], output_dir: Path) -> str:
    succeeded = all(step.succeeded for step in steps)
    lines = [
        "# JobHunterAI Pipeline Report",
        "",
        f"Status: {'Complete' if succeeded else 'Stopped'}",
        f"Output directory: {output_dir}",
        "",
        "This pipeline generates and reviews drafts. It does not submit applications.",
    ]
    for step in steps:
        lines.extend(["", *build_step_report(step)])
    lines.extend(
        [
            "",
            "## Generated Review Files",
            "",
            f"- {output_dir / 'application_manifest.json'}",
            f"- {output_dir / 'automation_report.md'}",
            f"- {output_dir / 'recruiter_review.md'}",
            f"- {output_dir / 'ready_to_apply_report.md'}",
            f"- {output_dir / 'ai_recruiter_review.md'} (only when --ai-review is used and configured)",
        ]
    )
    return "\n".join(lines)


def pipeline_report_path(output_dir: Path) -> Path:
    return output_dir / "pipeline_report.md"


def run_pipeline(args: argparse.Namespace) -> list[PipelineStep]:
    completed_steps = []
    for name, command in build_pipeline_steps(args):
        step = run_step(name, command)
        completed_steps.append(step)
        print(f"{step.name}: {'OK' if step.succeeded else 'FAILED'}")
        if not step.succeeded:
            break
    return completed_steps


def main() -> None:
    args = parse_args()
    steps = run_pipeline(args)
    report = build_pipeline_report(steps, args.output_dir)
    report_path = pipeline_report_path(args.output_dir)
    write_text_file(report_path, report)
    print(f"Pipeline report written: {report_path}")

    if not all(step.succeeded for step in steps):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
