import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_MANIFEST_KEYS = [
    "detected_role",
    "role_display_name",
    "generated_files",
    "automation_guardrails",
    "next_manual_step",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a JobHunterAI application manifest safely."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Validate a generated application manifest.",
    )
    check_parser.add_argument(
        "manifest",
        type=Path,
        help="Path to application_manifest.json.",
    )

    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing manifest file: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Expected a manifest file but found: {path}")

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid manifest JSON: {path}") from error

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must contain a JSON object.")

    return manifest


def missing_required_keys(manifest: dict[str, Any]) -> list[str]:
    return [key for key in REQUIRED_MANIFEST_KEYS if key not in manifest]


def resolve_generated_path(path_text: str, manifest_path: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path

    candidates = [
        Path.cwd() / path,
        manifest_path.parent / path,
        manifest_path.parent.parent / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def missing_generated_files(
    manifest: dict[str, Any],
    manifest_path: Path,
) -> list[str]:
    missing_files = []

    for path_text in manifest.get("generated_files", []):
        path = resolve_generated_path(str(path_text), manifest_path)
        if not path.exists():
            missing_files.append(str(path_text))

    return missing_files


def build_check_report(manifest: dict[str, Any], manifest_path: Path) -> str:
    missing_keys = missing_required_keys(manifest)
    missing_files = missing_generated_files(manifest, manifest_path)
    guardrails = manifest.get("automation_guardrails", [])

    lines = [
        "Automation Unit check complete.",
        f"Manifest: {manifest_path}",
        f"Detected role: {manifest.get('detected_role', 'unknown')}",
        f"Role title: {manifest.get('role_display_name', 'unknown')}",
        f"Tracked job ID: {manifest.get('tracked_job_id') or 'not tracked'}",
        "",
        "Manifest status:",
        f"- Missing required keys: {', '.join(missing_keys) if missing_keys else 'none'}",
        f"- Missing generated files: {', '.join(missing_files) if missing_files else 'none'}",
        "",
        "Automation guardrails:",
    ]

    lines.extend(f"- {guardrail}" for guardrail in guardrails)
    lines.extend(
        [
            "",
            f"Next manual step: {manifest.get('next_manual_step', 'Review generated drafts before applying.')}",
        ]
    )

    return "\n".join(lines)


def run_check(manifest_path: Path) -> str:
    manifest = load_manifest(manifest_path)
    return build_check_report(manifest, manifest_path)


def main() -> None:
    args = parse_args()

    try:
        if args.command == "check":
            print(run_check(args.manifest))
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Automation Unit failed.\nError: {error}") from error


if __name__ == "__main__":
    main()
