import argparse
import json
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from file_utils import write_text_file
from page_inspector import (
    build_inspection,
    build_markdown_report,
    inspection_json_path,
    inspection_markdown_path,
    load_dry_run,
    read_page_html,
    resolve_dry_run_path,
)


REVIEW_ACTIONS = {
    "fill_contact_field",
    "upload_document",
    "fill_application_answer",
    "prepare_outreach_message",
    "stop_before_submit",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a controlled live browser review session."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or browser_dry_run.json path.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the job URL in the default browser. This does not fill or submit.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Optional saved HTML file to inspect during the session.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write browser_review_session.md beside browser_dry_run.json.",
    )
    return parser.parse_args()


def browser_review_session_path(dry_run_path: Path) -> Path:
    return dry_run_path.parent / "browser_review_session.md"


def dry_run_job_url(dry_run: dict[str, Any]) -> str:
    value = str(dry_run.get("job", {}).get("job_url", "")).strip()
    if value.lower() == "not provided":
        return ""
    return value


def is_supported_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def open_dry_run_job_url(dry_run: dict[str, Any]) -> bool:
    url = dry_run_job_url(dry_run)
    if not url:
        raise ValueError("Browser dry run does not contain a job URL.")
    if not is_supported_url(url):
        raise ValueError(f"Unsupported job URL: {url}")
    return bool(webbrowser.open(url))


def review_action_lines(actions: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in actions:
        action_name = str(item.get("action", ""))
        if action_name not in REVIEW_ACTIONS:
            continue
        target = str(item.get("target", ""))
        status = str(item.get("status", ""))
        value = str(item.get("value", ""))
        value_text = f" ({value})" if value and action_name != "fill_contact_field" else ""
        lines.append(f"- {action_name} -> {target}: {status}{value_text}")
    return lines or ["- None."]


def build_browser_review_session_report(
    dry_run: dict[str, Any],
    dry_run_path: Path,
    browser_opened: bool,
    inspection_written: bool,
    html_source: str,
) -> str:
    readiness = dry_run.get("readiness", {})
    lines = [
        "# Browser Review Session",
        "",
        "Status: Prepared, not submitted",
        f"Browser dry run: {dry_run_path}",
        f"Browser opened: {browser_opened}",
        f"Page inspection written: {inspection_written}",
        f"HTML source: {html_source or 'not provided'}",
        f"Submission allowed: {dry_run.get('submission_allowed', False)}",
        f"Stop before submit: {dry_run.get('stop_before_submit', True)}",
        "",
        "This session can open the job page and inspect saved HTML.",
        "It does not fill fields, click apply, or submit applications.",
        "",
        "## Job",
        "",
        f"- Job URL: {dry_run_job_url(dry_run) or 'not provided'}",
        "",
        "## Readiness",
        "",
        f"- Status: {readiness.get('status', 'unknown')}",
        "",
        "## Review Actions",
        "",
        *review_action_lines(dry_run.get("actions", [])),
        "",
        "## Live Browser Rules",
        "",
        "- Open the page only when `--open-browser` is used.",
        "- Do not type into fields during review.",
        "- Do not upload files during review.",
        "- Do not click apply, continue, send, or submit buttons.",
        "- Save page HTML and run page inspection before future automation.",
        "",
        "## Next Command",
        "",
    ]
    if html_source:
        lines.append(f"- `python page_inspector.py {dry_run_path.parent} --html {html_source} --write`")
    else:
        lines.append("- Save the application page HTML, then run `page_inspector.py --html`.")
    return "\n".join(lines)


def write_page_inspection(
    dry_run: dict[str, Any],
    dry_run_path: Path,
    html_path: Path,
) -> str:
    html, source = read_page_html(html_path=html_path)
    inspection = build_inspection(dry_run, html, source)
    write_text_file(inspection_json_path(dry_run_path), json.dumps(inspection, indent=2))
    write_text_file(inspection_markdown_path(dry_run_path), build_markdown_report(inspection))
    return source


def main() -> None:
    args = parse_args()
    dry_run_path = resolve_dry_run_path(args.path)
    try:
        dry_run = load_dry_run(args.path)
        browser_opened = open_dry_run_job_url(dry_run) if args.open_browser else False
        html_source = write_page_inspection(dry_run, dry_run_path, args.html) if args.html else ""
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Browser review session failed.\nError: {error}") from error

    report = build_browser_review_session_report(
        dry_run,
        dry_run_path,
        browser_opened=browser_opened,
        inspection_written=bool(args.html),
        html_source=html_source,
    )
    print(report)

    if args.write:
        path = browser_review_session_path(dry_run_path)
        write_text_file(path, report)
        print("")
        print(f"Browser review session written: {path}")


if __name__ == "__main__":
    main()
