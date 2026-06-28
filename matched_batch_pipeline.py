import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from batch_pipeline import (
    BatchJobResult,
    build_pipeline_command,
    command_line,
    output_dir_for_job,
    run_job_pipeline,
)
from config import OUTPUTS_DIR
from file_utils import write_text_file
from job_intake import DEFAULT_JOBS_DIR
from job_matcher import JobMatch, match_saved_jobs


DEFAULT_MATCHED_OUTPUT_ROOT = OUTPUTS_DIR / "matched-batch"
DEFAULT_MIN_SCORE = 70


@dataclass(frozen=True)
class MatchedBatchResult:
    match: JobMatch
    pipeline_result: BatchJobResult

    @property
    def succeeded(self) -> bool:
        return self.pipeline_result.succeeded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the package pipeline only for saved jobs above a match score."
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder containing saved job descriptions and job_index.json.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_MATCHED_OUTPUT_ROOT,
        help="Folder where per-job output folders should be created.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=DEFAULT_MIN_SCORE,
        help="Only process saved jobs with this match score or higher.",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=0,
        help="Optional maximum number of matched jobs to process. 0 means no limit.",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate AI drafts and run automatic AI revision for each matched job.",
    )
    parser.add_argument(
        "--ai-review",
        action="store_true",
        help="Run optional AI recruiter review after the offline review for each matched job.",
    )
    parser.add_argument(
        "--strict-profile",
        action="store_true",
        help="Stop each pipeline run when profile validation has warnings.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop the batch after the first failed matched job.",
    )
    return parser.parse_args()


def eligible_matches(
    matches: list[JobMatch],
    min_score: int = DEFAULT_MIN_SCORE,
    max_jobs: int = 0,
) -> list[JobMatch]:
    selected = [
        match
        for match in matches
        if match.score >= min_score and match.recommendation != "error"
    ]
    if max_jobs > 0:
        return selected[:max_jobs]
    return selected


def process_matched_job(
    match: JobMatch,
    output_root: Path,
    ai: bool = False,
    ai_review: bool = False,
    strict_profile: bool = False,
) -> MatchedBatchResult:
    output_dir = output_dir_for_job(output_root, match.job_file)
    command = build_pipeline_command(
        match.job_file,
        output_dir,
        ai=ai,
        ai_review=ai_review,
        strict_profile=strict_profile,
    )
    completed = run_job_pipeline(command)
    pipeline_result = BatchJobResult(
        job_path=match.job_file,
        output_dir=output_dir,
        command=[sys.executable, *command],
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )
    return MatchedBatchResult(match=match, pipeline_result=pipeline_result)


def run_matched_batch(args: argparse.Namespace) -> list[MatchedBatchResult]:
    matches = eligible_matches(
        match_saved_jobs(args.jobs_dir),
        min_score=args.min_score,
        max_jobs=args.max_jobs,
    )
    if not matches:
        raise ValueError(
            f"No saved jobs met the minimum match score of {args.min_score}."
        )

    results: list[MatchedBatchResult] = []
    for match in matches:
        result = process_matched_job(
            match,
            args.output_root,
            ai=args.ai,
            ai_review=args.ai_review,
            strict_profile=args.strict_profile,
        )
        results.append(result)
        print(
            f"{match.score} {match.company} - {match.position}: "
            f"{'OK' if result.succeeded else 'FAILED'} -> "
            f"{result.pipeline_result.output_dir}"
        )
        if args.stop_on_error and not result.succeeded:
            break
    return results


def result_lines(result: MatchedBatchResult) -> list[str]:
    status = "OK" if result.succeeded else "FAILED"
    pipeline = result.pipeline_result
    match = result.match
    lines = [
        f"## {match.company} - {match.position}",
        "",
        f"Status: {status}",
        f"Match score: {match.score}/100",
        f"Recommendation: {match.recommendation}",
        f"Detected role: {match.role}",
        f"Job file: {pipeline.job_path}",
        f"Output folder: {pipeline.output_dir}",
        f"Command: `{command_line(pipeline.command)}`",
    ]
    if match.url:
        lines.append(f"URL: {match.url}")
    if pipeline.stdout:
        lines.extend(["", "Output:", "", "```text", pipeline.stdout, "```"])
    if pipeline.stderr:
        lines.extend(["", "Errors:", "", "```text", pipeline.stderr, "```"])
    return lines


def build_matched_batch_report(
    results: list[MatchedBatchResult],
    output_root: Path,
    min_score: int,
) -> str:
    total = len(results)
    succeeded = sum(1 for result in results if result.succeeded)
    failed = total - succeeded
    lines = [
        "# JobHunterAI Matched Batch Pipeline Report",
        "",
        f"Status: {'Complete' if failed == 0 else 'Completed with failures'}",
        f"Minimum match score: {min_score}",
        f"Output root: {output_root}",
        f"Jobs processed: {total}",
        f"Successful: {succeeded}",
        f"Failed: {failed}",
        "",
        "This batch only processes saved jobs that passed offline match scoring. It does not submit applications.",
    ]
    for result in results:
        lines.extend(["", *result_lines(result)])
    return "\n".join(lines)


def matched_batch_report_path(output_root: Path) -> Path:
    return output_root / "matched_batch_report.md"


def main() -> None:
    args = parse_args()
    try:
        results = run_matched_batch(args)
        report = build_matched_batch_report(results, args.output_root, args.min_score)
        report_path = matched_batch_report_path(args.output_root)
        write_text_file(report_path, report)
        print(f"Matched batch report written: {report_path}")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Matched batch pipeline failed.\nError: {error}") from error

    if any(not result.succeeded for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
