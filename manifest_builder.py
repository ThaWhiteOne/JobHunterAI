import json
from datetime import datetime, timezone
from pathlib import Path

from job_analyzer import JobAnalysis


AUTOMATION_GUARDRAILS = [
    "Generated files are drafts and must be reviewed before applying.",
    "Do not submit applications automatically without user confirmation.",
    "Do not invent experience, dates, certifications, employers, or education.",
    "Use profile files as the source of truth.",
    "Keep offline generation available even if future AI features fail.",
]


def path_strings(paths: list[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


def generate_manifest(
    job_path: Path,
    output_dir: Path,
    role: str,
    role_display_name: str,
    scores: dict[str, int],
    profile_path: Path,
    used_fallback_profile: bool,
    job_analysis: JobAnalysis,
    generated_files: list[Path],
    manifest_path: Path,
    tracked_job_id: int | None = None,
) -> str:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job_path": job_path.as_posix(),
        "output_dir": output_dir.as_posix(),
        "detected_role": role,
        "role_display_name": role_display_name,
        "role_scores": scores,
        "profile_path": profile_path.as_posix(),
        "used_fallback_profile": used_fallback_profile,
        "matched_keywords": job_analysis.matched_keywords,
        "requirement_lines": job_analysis.requirement_lines,
        "generated_files": path_strings([*generated_files, manifest_path]),
        "tracked_job_id": tracked_job_id,
        "automation_guardrails": AUTOMATION_GUARDRAILS,
        "next_manual_step": "Review generated drafts before applying.",
    }

    return json.dumps(manifest, indent=2)
