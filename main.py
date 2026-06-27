import argparse
import re
from pathlib import Path

from ai_draft_generator import run_ai_draft_generation
from ai_reviewer import AIReviewNotConfiguredError
from ai_prompt_builder import generate_ai_brief
from config import (
    JOB_TRACKER_DB_PATH,
    OUTPUTS_DIR,
    RESUME_TEMPLATE_PATH,
    ROLE_DISPLAY_NAMES,
    SAMPLE_JOB_PATH,
)
from document_exporter import export_docx_files, export_pdf_files
from file_utils import read_text_file, write_text_file
from generators import (
    generate_cover_letter,
    generate_linkedin_message,
    generate_resume,
)
from html_exporter import export_html_files
from job_analyzer import analyze_job, generate_application_review
from manifest_builder import generate_manifest
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
        "--full-package",
        action="store_true",
        help=(
            "Generate the full offline package: drafts, job text, review notes, "
            "AI brief, manifest, and document exports."
        ),
    )
    parser.add_argument(
        "--save-job-text",
        action="store_true",
        help="Save the original job description beside the generated files.",
    )
    parser.add_argument(
        "--export",
        choices=["html", "docx", "pdf", "all"],
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
        "--ai-drafts",
        action="store_true",
        help="Use OpenAI to generate tailored drafts from the selected profile.",
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Generate application_manifest.json for automation handoff.",
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


def should_save_job_text(args: argparse.Namespace) -> bool:
    return args.save_job_text or args.full_package


def should_generate_review_notes(args: argparse.Namespace) -> bool:
    return args.review_notes or args.full_package


def should_generate_ai_brief(args: argparse.Namespace) -> bool:
    return args.ai_brief or args.full_package


def should_export_html(args: argparse.Namespace) -> bool:
    return args.export in ("html", "all") or args.full_package


def should_export_docx(args: argparse.Namespace) -> bool:
    return args.export in ("docx", "all") or args.full_package


def should_export_pdf(args: argparse.Namespace) -> bool:
    return args.export in ("pdf", "all") or args.full_package


def should_generate_manifest(args: argparse.Namespace) -> bool:
    return args.manifest or args.full_package


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
        if args.ai_drafts:
            try:
                ai_drafts = run_ai_draft_generation(
                    role_display_name,
                    profile,
                    job_description,
                    read_text_file(RESUME_TEMPLATE_PATH, required=True),
                )
            except AIReviewNotConfiguredError as error:
                raise ValueError(f"--ai-drafts requires AI configuration. {error}") from error

            resume = ai_drafts["resume_md"]
            cover_letter = ai_drafts["cover_letter_md"]
            linkedin_message = ai_drafts["linkedin_message_txt"]

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
        if should_save_job_text(args):
            job_description_path = output_dir / "job_description.txt"
            write_text_file(job_description_path, job_description)
            generated_files.append(job_description_path)

        if should_generate_review_notes(args):
            review_notes_path = output_dir / "application_review.md"
            review_notes = generate_application_review(
                role,
                role_display_name,
                job_description,
                scores,
            )
            write_text_file(review_notes_path, review_notes)
            generated_files.append(review_notes_path)

        if should_generate_ai_brief(args):
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

        if should_export_html(args):
            generated_files.extend(
                export_html_files(
                    output_dir,
                    resume,
                    cover_letter,
                    linkedin_message,
                )
            )
        if should_export_docx(args):
            generated_files.extend(
                export_docx_files(
                    output_dir,
                    resume,
                    cover_letter,
                    linkedin_message,
                )
            )
        if should_export_pdf(args):
            generated_files.extend(
                export_pdf_files(
                    output_dir,
                    resume,
                    cover_letter,
                    linkedin_message,
                )
            )

        tracked_job_id = track_generated_application(args, role)
        if should_generate_manifest(args):
            manifest_path = output_dir / "application_manifest.json"
            manifest = generate_manifest(
                job_path,
                output_dir,
                role,
                role_display_name,
                scores,
                profile_path,
                used_fallback,
                job_analysis,
                generated_files,
                manifest_path,
                tracked_job_id,
            )
            write_text_file(manifest_path, manifest)
            generated_files.append(manifest_path)

        print("JobHunterAI finished successfully.")
        print(f"Detected role: {role} ({role_display_name})")
        if args.debug:
            print(f"Job file: {job_path}")
            print(f"Output directory: {output_dir}")
            print(f"Role scores: {scores}")
            print(f"Matched keywords: {job_analysis.matched_keywords}")
            print(f"Requirement lines: {job_analysis.requirement_lines}")
            print(f"Profile used: {profile_path}")
            print(f"AI drafts: {'enabled' if args.ai_drafts else 'disabled'}")
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
