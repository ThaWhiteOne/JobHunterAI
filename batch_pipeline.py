import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from config import OUTPUTS_DIR
from file_utils import write_text_file


DEFAULT_JOBS_DIR = Path("jobs")
DEFAULT_BATCH_OUTPUT_ROOT = OUTPUTS_DIR / "batch"


@dataclass(frozen=True)
class BatchJobResult:
    job_path: Path
    output_dir: Path
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run JobHunterAI pipeline for every .txt job file in a folder."
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder containing job description .txt files.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_BATCH_OUTPUT_ROOT,
        help="Folder where per-job output folders should be created.",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate AI drafts and run automatic AI revision for each job.",
    )
    parser.add_argument(
        "--ai-review",
        action="store_true",
        help="Run optional AI recruiter review after the offline review for each job.",
    )
    parser.add_argument(
        "--strict-profile",
        action="store_true",
        help="Stop each pipeline run when profile validation has warnings.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop the batch after the first failed job.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "job"


def discover_job_files(jobs_dir: Path) -> list[Path]:
    if not jobs_dir.exists():
        raise FileNotFoundError(f"Missing jobs folder: {jobs_dir}")
    if not jobs_dir.is_dir():
        raise FileNotFoundError(f"Expected a jobs folder but found: {jobs_dir}")

    return sorted(path for path in jobs_dir.glob("*.txt") if path.is_file())


def output_dir_for_job(output_root: Path, job_path: Path) -> Path:
    return output_root / slugify(job_path.stem)


def build_pipeline_command(
    job_path: Path,
    output_dir: Path,
    ai: bool = False,
    ai_review: bool = False,
    strict_profile: bool = False,
) -> list[str]:
    command = [
        "pipeline.py",
        "--job",
        str(job_path),
        "--output-dir",
        str(output_dir),
    ]
    if ai:
        command.append("--ai")
    if ai_review:
        command.append("--ai-review")
    if strict_profile:
        command.append("--strict-profile")
    return command


def run_job_pipeline(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        capture_output=True,
        text=True,
        check=False,
    )


def process_job(
    job_path: Path,
    output_root: Path,
    ai: bool = False,
    ai_review: bool = False,
    strict_profile: bool = False,
) -> BatchJobResult:
    output_dir = output_dir_for_job(output_root, job_path)
    command = build_pipeline_command(
        job_path,
        output_dir,
        ai=ai,
        ai_review=ai_review,
        strict_profile=strict_profile,
    )
    result = run_job_pipeline(command)
    return BatchJobResult(
        job_path=job_path,
        output_dir=output_dir,
        command=[sys.executable, *command],
        returncode=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def run_batch(args: argparse.Namespace) -> list[BatchJobResult]:
    job_files = discover_job_files(args.jobs_dir)
    if not job_files:
        raise ValueError(f"No .txt job files found in: {args.jobs_dir}")

    results = []
    for job_path in job_files:
        result = process_job(
            job_path,
            args.output_root,
            ai=args.ai,
            ai_review=args.ai_review,
            strict_profile=args.strict_profile,
        )
        results.append(result)
        print(
            f"{job_path.name}: "
            f"{'OK' if result.succeeded else 'FAILED'} -> {result.output_dir}"
        )
        if args.stop_on_error and not result.succeeded:
            break

    return results


def command_line(command: list[str]) -> str:
    return " ".join(command)


def result_lines(result: BatchJobResult) -> list[str]:
    status = "OK" if result.succeeded else "FAILED"
    lines = [
        f"## {result.job_path.name}",
        "",
        f"Status: {status}",
        f"Job file: {result.job_path}",
        f"Output folder: {result.output_dir}",
        f"Command: `{command_line(result.command)}`",
    ]
    if result.stdout:
        lines.extend(["", "Output:", "", "```text", result.stdout, "```"])
    if result.stderr:
        lines.extend(["", "Errors:", "", "```text", result.stderr, "```"])
    return lines


def build_batch_report(results: list[BatchJobResult], output_root: Path) -> str:
    total = len(results)
    succeeded = sum(1 for result in results if result.succeeded)
    failed = total - succeeded
    lines = [
        "# JobHunterAI Batch Pipeline Report",
        "",
        f"Status: {'Complete' if failed == 0 else 'Completed with failures'}",
        f"Output root: {output_root}",
        f"Jobs processed: {total}",
        f"Successful: {succeeded}",
        f"Failed: {failed}",
        "",
        "This batch creates reviewed application packages. It does not submit applications.",
    ]
    for result in results:
        lines.extend(["", *result_lines(result)])
    return "\n".join(lines)


def batch_report_path(output_root: Path) -> Path:
    return output_root / "batch_report.md"


def main() -> None:
    args = parse_args()
    try:
        results = run_batch(args)
        report = build_batch_report(results, args.output_root)
        report_path = batch_report_path(args.output_root)
        write_text_file(report_path, report)
        print(f"Batch report written: {report_path}")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Batch pipeline failed.\nError: {error}") from error

    if any(not result.succeeded for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
