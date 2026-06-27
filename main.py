import argparse
import re
from pathlib import Path

from ai_prompt_builder import generate_ai_brief
from config import (
    JOB_TRACKER_DB_PATH,
    OUTPUTS_DIR,
    ROLE_DISPLAY_NAMES,
    SAMPLE_JOB_PATH,
)
from file_utils import read_text_file, write_text_file
from generators import (
    generate_cover_letter,
    generate_linkedin_message,
    generate_resume,
)
from html_exporter import export_html_files
from job_analyzer import analyze_job, generate_application_review
from profile_selector import select_profile
from role_detector import detect_role, score_roles
from tracker_db import add_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate tailored job application files from a job description."
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
        "--debug",
        action="store_true",
        help="Print role scores and profile selection details.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Folder where generated files should be written.",
    )
    parser.add_argument(
        "--save-job-text",
        action="store_true",
        help="Save the original job description beside the generated files.",
    )
    parser.add_argument(
        "--export",
        choices=["html"],
        help="Also export generated documents to the selected format.",
    )
    parser.add_argument(
        "--review-notes",
        action="store_true",
        help="Generate application_review.md with matched keywords and checklist.",
    )
    parser.add_argument(
        "--ai-brief",
        action="store_true",
        help="Generate ai_brief.md for a future AI/automation step.",
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


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "job"


def get_output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return args.output_dir
    if args.track and args.company.strip() and args.position.strip():
        return OUTPUTS_DIR / f"{slugify(args.company)}-{slugify(args.position)}"
    return args.output_dir or OUTPUTS_DIR


def validate_tracking_args(args: argparse.Namespace) -> None:
    if not args.track:
        return
    if not args.company.strip():
        raise ValueError("--company is required when using --track.")
    if not args.position.strip():
        raise ValueError("--position is required when using --track.")


def track_generated_application(args: argparse.Namespace, role: str) -> int | None:
    if not args.track:
        return None

    validate_tracking_args(args)
    return add_job(
        JOB_TRACKER_DB_PATH,
        company=args.company,
        position=args.position,
        url=args.url,
        role=role,
        status="generated",
        notes=args.notes,
        output_dir=str(get_output_dir(args)),
    )


def main() -> None:
    args = parse_args()

    try:
        validate_tracking_args(args)
        job_path = get_job_path(args)
        job_description = read_text_file(job_path, required=True)
        role = detect_role(job_description)
        scores = score_roles(job_description)
        role_display_name = ROLE_DISPLAY_NAMES.get(role, role.title())
        job_analysis = analyze_job(job_description, role)

        profile, profile_path, used_fallback = select_profile(role)

        resume = generate_resume(role, role_display_name, profile, job_description)
        cover_letter = generate_cover_letter(
            role,
            role_display_name,
            profile,
            job_description,
        )
        linkedin_message = generate_linkedin_message(role, role_display_name)

        output_dir = get_output_dir(args)
        resume_path = output_dir / "resume.md"
        cover_letter_path = output_dir / "cover_letter.md"
        linkedin_message_path = output_dir / "linkedin_message.txt"
        generated_files = [
            resume_path,
            cover_letter_path,
            linkedin_message_path,
        ]

        write_text_file(resume_path, resume)
        write_text_file(cover_letter_path, cover_letter)
        write_text_file(linkedin_message_path, linkedin_message)
        if args.save_job_text:
            job_description_path = output_dir / "job_description.txt"
            write_text_file(job_description_path, job_description)
            generated_files.append(job_description_path)

        if args.review_notes:
            review_notes_path = output_dir / "application_review.md"
            review_notes = generate_application_review(
                role,
                role_display_name,
                job_description,
                scores,
            )
            write_text_file(review_notes_path, review_notes)
            generated_files.append(review_notes_path)

        if args.ai_brief:
            ai_brief_path = output_dir / "ai_brief.md"
            ai_brief = generate_ai_brief(
                role,
                role_display_name,
                profile,
                job_description,
                scores,
                resume,
                cover_letter,
                linkedin_message,
            )
            write_text_file(ai_brief_path, ai_brief)
            generated_files.append(ai_brief_path)

        if args.export == "html":
            generated_files.extend(
                export_html_files(
                    output_dir,
                    resume,
                    cover_letter,
                    linkedin_message,
                )
            )

        tracked_job_id = track_generated_application(args, role)

        print("JobHunterAI finished successfully.")
        print(f"Detected role: {role} ({role_display_name})")
        if args.debug:
            print(f"Job file: {job_path}")
            print(f"Output directory: {output_dir}")
            print(f"Role scores: {scores}")
            print(f"Matched keywords: {job_analysis.matched_keywords}")
            print(f"Requirement lines: {job_analysis.requirement_lines}")
            print(f"Profile used: {profile_path}")
            if used_fallback:
                print(
                    "Note: role-specific profile was missing/empty. "
                    "Used master profile instead."
                )
        print("Generated files:")
        for generated_file in generated_files:
            print(f"- {generated_file}")
        if tracked_job_id is not None:
            print(f"Tracked job: #{tracked_job_id}")

    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"JobHunterAI failed.\nError: {error}") from error


if __name__ == "__main__":
    main()
