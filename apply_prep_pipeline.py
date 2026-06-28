import argparse
from pathlib import Path

from config import OUTPUTS_DIR, SAMPLE_JOB_PATH
from file_utils import write_text_file
from pipeline import PipelineStep, build_step_report, run_step


DEFAULT_APPLY_PREP_OUTPUT_DIR = OUTPUTS_DIR / "apply-prep"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the safe JobHunterAI apply-preparation workflow."
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
        default=DEFAULT_APPLY_PREP_OUTPUT_DIR,
        help="Folder where generated files should be written.",
    )
    parser.add_argument(
        "--answers",
        type=Path,
        help="Optional local application answers file.",
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
        "--open-browser",
        action="store_true",
        help="Open the job URL only after the apply readiness gate passes.",
    )
    return parser.parse_args()


def get_job_path(args: argparse.Namespace) -> Path:
    return args.job_option or args.job_file or SAMPLE_JOB_PATH


def build_package_command(args: argparse.Namespace) -> list[str]:
    command = [
        "pipeline.py",
        "--job",
        str(get_job_path(args)),
        "--output-dir",
        str(args.output_dir),
    ]
    if args.ai:
        command.append("--ai")
    if args.ai_review:
        command.append("--ai-review")
    if args.strict_profile:
        command.append("--strict-profile")
    return command


def build_form_fill_command(args: argparse.Namespace) -> list[str]:
    command = [
        "form_fill_planner.py",
        str(args.output_dir),
        "--write",
    ]
    if args.answers:
        command.extend(["--answers", str(args.answers)])
    return command


def build_apply_assistant_command(args: argparse.Namespace) -> list[str]:
    command = [
        "apply_assistant.py",
        str(args.output_dir),
        "--write",
    ]
    if args.open_browser:
        command.append("--open-browser")
    return command


def build_apply_prep_steps(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    return [
        ("Application package pipeline", build_package_command(args)),
        ("Form-fill plan", build_form_fill_command(args)),
        (
            "Apply readiness gate",
            [
                "apply_readiness_gate.py",
                str(args.output_dir),
                "--write-report",
            ],
        ),
        ("Controlled apply session", build_apply_assistant_command(args)),
    ]


def build_apply_prep_report(steps: list[PipelineStep], output_dir: Path) -> str:
    succeeded = all(step.succeeded for step in steps)
    lines = [
        "# Apply Prep Pipeline Report",
        "",
        f"Status: {'Complete' if succeeded else 'Stopped'}",
        f"Output directory: {output_dir}",
        "",
        "This workflow prepares application files and gates future browser automation.",
        "It does not fill forms, click apply, or submit applications.",
    ]
    for step in steps:
        lines.extend(["", *build_step_report(step)])
    lines.extend(
        [
            "",
            "## Generated Apply Prep Files",
            "",
            f"- {output_dir / 'application_packet.json'}",
            f"- {output_dir / 'submission_plan.md'}",
            f"- {output_dir / 'form_fill_plan.json'}",
            f"- {output_dir / 'form_fill_plan.md'}",
            f"- {output_dir / 'apply_readiness_report.md'}",
            f"- {output_dir / 'apply_session.md'} (only when readiness passes)",
        ]
    )
    return "\n".join(lines)


def apply_prep_report_path(output_dir: Path) -> Path:
    return output_dir / "apply_prep_report.md"


def run_apply_prep(args: argparse.Namespace) -> list[PipelineStep]:
    completed_steps = []
    for name, command in build_apply_prep_steps(args):
        step = run_step(name, command)
        completed_steps.append(step)
        print(f"{step.name}: {'OK' if step.succeeded else 'FAILED'}")
        if not step.succeeded:
            break
    return completed_steps


def main() -> None:
    args = parse_args()
    steps = run_apply_prep(args)
    report = build_apply_prep_report(steps, args.output_dir)
    report_path = apply_prep_report_path(args.output_dir)
    write_text_file(report_path, report)
    print(f"Apply prep report written: {report_path}")

    if not all(step.succeeded for step in steps):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
