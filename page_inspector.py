import argparse
import json
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from file_utils import read_text_file, write_text_file


FIELD_TAGS = {"input", "select", "textarea", "button"}
ACTION_TYPES_TO_MATCH = {
    "fill_contact_field",
    "upload_document",
    "fill_application_answer",
    "stop_before_submit",
}
TARGET_ALIASES = {
    "full_name": ["full name", "name", "candidate name", "legal name"],
    "email": ["email", "email address", "e-mail"],
    "phone": ["phone", "telephone", "mobile"],
    "location": ["location", "city", "address"],
    "github": ["github", "git hub"],
    "linkedin": ["linkedin", "linked in"],
    "resume": ["resume", "cv", "curriculum vitae"],
    "cover_letter": ["cover letter", "covering letter"],
    "work authorization": ["work authorization", "right to work", "work permit"],
    "visa sponsorship": ["visa sponsorship", "sponsorship"],
    "notice period / start date": ["start date", "notice period", "availability"],
    "salary expectation": ["salary", "compensation", "expected pay"],
    "custom screening questions": ["screening", "question"],
    "final_submit_button": ["submit", "submit application", "apply", "send application"],
}


@dataclass
class PageField:
    tag: str
    field_type: str
    name: str
    field_id: str
    label: str
    placeholder: str
    aria_label: str

    @property
    def searchable_text(self) -> str:
        return " ".join(
            part
            for part in [
                self.label,
                self.name,
                self.field_id,
                self.placeholder,
                self.aria_label,
                self.field_type,
                self.tag,
            ]
            if part
        )


class FormFieldParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fields: list[PageField] = []
        self.labels_by_id: dict[str, str] = {}
        self.label_stack: list[dict[str, Any]] = []
        self.text_capture_index: int | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "label":
            self.label_stack.append(
                {"for": attributes.get("for", ""), "texts": [], "field_indexes": []}
            )
            return
        if tag in FIELD_TAGS:
            self._add_field(tag, attributes)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "label" and self.label_stack:
            label = self.label_stack.pop()
            text = clean_text(" ".join(label["texts"]))
            if text:
                target_id = str(label.get("for", ""))
                if target_id:
                    self.labels_by_id[target_id] = text
                    self._apply_label_to_id(target_id, text)
                for index in label["field_indexes"]:
                    if not self.fields[index].label:
                        self.fields[index].label = text
            return
        if tag in {"button", "textarea"}:
            self.text_capture_index = None

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if not text:
            return
        if self.label_stack:
            self.label_stack[-1]["texts"].append(text)
        if self.text_capture_index is not None:
            field = self.fields[self.text_capture_index]
            field.label = clean_text(f"{field.label} {text}")

    def _add_field(self, tag: str, attributes: dict[str, str]) -> None:
        field_type = attributes.get("type", "").lower()
        if tag == "input" and field_type == "hidden":
            return

        field_id = attributes.get("id", "")
        label = (
            attributes.get("aria-label", "")
            or attributes.get("placeholder", "")
            or attributes.get("value", "")
            or self.labels_by_id.get(field_id, "")
        )
        field = PageField(
            tag=tag,
            field_type=field_type,
            name=attributes.get("name", ""),
            field_id=field_id,
            label=clean_text(label),
            placeholder=attributes.get("placeholder", ""),
            aria_label=attributes.get("aria-label", ""),
        )
        self.fields.append(field)
        index = len(self.fields) - 1
        if self.label_stack:
            self.label_stack[-1]["field_indexes"].append(index)
        if tag in {"button", "textarea"}:
            self.text_capture_index = index

    def _apply_label_to_id(self, field_id: str, label: str) -> None:
        for field in self.fields:
            if field.field_id == field_id and not field.label:
                field.label = label


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a job application page against a browser dry-run plan."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Output folder or browser_dry_run.json path.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--html",
        type=Path,
        help="Saved HTML file for the job application page.",
    )
    source.add_argument(
        "--url",
        help="Explicit URL to fetch and inspect with the standard library.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write page_inspection.json and page_inspection.md beside the dry run.",
    )
    return parser.parse_args()


def clean_text(text: str) -> str:
    return " ".join(text.split())


def normalize(text: str) -> str:
    return clean_text(
        text.lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("/", " ")
    )


def resolve_dry_run_path(path: Path) -> Path:
    if path.suffix.lower() == ".json":
        return path
    return path / "browser_dry_run.json"


def inspection_json_path(dry_run_path: Path) -> Path:
    return dry_run_path.parent / "page_inspection.json"


def inspection_markdown_path(dry_run_path: Path) -> Path:
    return dry_run_path.parent / "page_inspection.md"


def load_dry_run(path: Path) -> dict[str, Any]:
    dry_run_path = resolve_dry_run_path(path)
    if not dry_run_path.exists():
        raise FileNotFoundError(f"Missing browser dry-run file: {dry_run_path}")
    try:
        dry_run = json.loads(dry_run_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in browser dry-run file: {dry_run_path}") from error
    if not isinstance(dry_run, dict):
        raise ValueError("Browser dry-run file must contain a JSON object.")
    if not isinstance(dry_run.get("actions"), list):
        raise ValueError("Browser dry-run file must contain an actions list.")
    return dry_run


def read_page_html(html_path: Path | None = None, url: str | None = None) -> tuple[str, str]:
    if html_path:
        return read_text_file(html_path), str(html_path)
    if not url:
        raise ValueError("Provide either --html or --url.")
    request = Request(url, headers={"User-Agent": "JobHunterAI page inspector"})
    try:
        with urlopen(request, timeout=20) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            content = response.read().decode(charset, errors="replace")
    except URLError as error:
        raise ValueError(f"Could not fetch page URL: {url}") from error
    return content, url


def parse_html_fields(html: str) -> list[PageField]:
    parser = FormFieldParser()
    parser.feed(html)
    return parser.fields


def aliases_for_target(target: str) -> list[str]:
    normalized_target = normalize(target)
    aliases = TARGET_ALIASES.get(normalized_target, [])
    return [normalized_target, *aliases]


def field_matches_target(field: PageField, target: str, action_name: str) -> bool:
    text = normalize(field.searchable_text)
    aliases = [normalize(alias) for alias in aliases_for_target(target)]
    if any(alias and alias in text for alias in aliases):
        return True
    if target == "email" and field.field_type == "email":
        return True
    if target == "phone" and field.field_type in {"tel", "phone"}:
        return True
    if action_name == "upload_document" and field.field_type == "file":
        return any(alias in text for alias in aliases)
    if target == "final_submit_button":
        return field.tag == "button" or field.field_type == "submit"
    return False


def best_field_match(
    fields: list[PageField],
    target: str,
    action_name: str,
) -> PageField | None:
    for field in fields:
        if field_matches_target(field, target, action_name):
            return field
    return None


def match_status(action_item: dict[str, Any], field: PageField | None) -> str:
    action_name = str(action_item.get("action", ""))
    action_status = str(action_item.get("status", ""))
    if action_name == "stop_before_submit":
        return "stop_detected" if field else "stop_not_detected"
    if action_status != "ready":
        return "not_ready_in_dry_run"
    return "matched" if field else "missing_on_page"


def match_actions_to_fields(
    actions: list[dict[str, Any]],
    fields: list[PageField],
) -> list[dict[str, Any]]:
    matches = []
    for action_item in actions:
        action_name = str(action_item.get("action", ""))
        if action_name not in ACTION_TYPES_TO_MATCH:
            continue
        target = str(action_item.get("target", ""))
        field = best_field_match(fields, target, action_name)
        matches.append(
            {
                "step": action_item.get("step", ""),
                "action": action_name,
                "target": target,
                "status": match_status(action_item, field),
                "field": field.searchable_text if field else "",
                "field_details": field_summary(field) if field else {},
                "note": "Inspection only. Do not fill or submit.",
            }
        )
    return matches


def field_summary(field: PageField) -> dict[str, str]:
    return {
        "tag": field.tag,
        "type": field.field_type,
        "name": field.name,
        "id": field.field_id,
        "label": field.label,
        "placeholder": field.placeholder,
        "aria_label": field.aria_label,
    }


def build_inspection(
    dry_run: dict[str, Any],
    html: str,
    source: str,
) -> dict[str, Any]:
    fields = parse_html_fields(html)
    matches = match_actions_to_fields(dry_run.get("actions", []), fields)
    missing = sum(1 for item in matches if item["status"] == "missing_on_page")
    matched = sum(1 for item in matches if item["status"] == "matched")
    stop_detected = any(item["status"] == "stop_detected" for item in matches)
    return {
        "status": "ready_for_manual_review" if missing == 0 else "needs_review",
        "submission_allowed": False,
        "stop_before_submit": True,
        "source": source,
        "detected_fields": len(fields),
        "matched_actions": matched,
        "missing_actions": missing,
        "stop_button_detected": stop_detected,
        "fields": [field_summary(field) for field in fields],
        "matches": matches,
        "guardrails": [
            *dry_run.get("guardrails", []),
            "Page inspection only: do not fill fields.",
            "Stop before final submit.",
        ],
    }


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def match_lines(matches: list[dict[str, Any]]) -> list[str]:
    return [
        f"- {item['step']}. {item['action']} -> {item['target']}: {item['status']}"
        + (f" ({item['field']})" if item.get("field") else "")
        for item in matches
    ] or ["- None."]


def field_lines(fields: list[dict[str, str]]) -> list[str]:
    lines = []
    for index, field in enumerate(fields, start=1):
        label = field.get("label") or field.get("name") or field.get("id") or "unlabeled"
        field_type = field.get("type") or field.get("tag")
        lines.append(f"- {index}. {label} [{field_type}]")
    return lines or ["- None."]


def build_markdown_report(inspection: dict[str, Any]) -> str:
    status = (
        "Ready for manual review"
        if inspection["status"] == "ready_for_manual_review"
        else "Needs review"
    )
    lines = [
        "# Page Inspection Report",
        "",
        f"Status: {status}",
        f"Source: {inspection['source']}",
        f"Submission allowed: {inspection['submission_allowed']}",
        f"Stop before submit: {inspection['stop_before_submit']}",
        "",
        "This report inspects page fields against the browser dry-run plan.",
        "It does not fill fields, click apply, or submit applications.",
        "",
        "## Summary",
        "",
        f"- Detected fields: {inspection['detected_fields']}",
        f"- Matched actions: {inspection['matched_actions']}",
        f"- Missing actions: {inspection['missing_actions']}",
        f"- Stop button detected: {inspection['stop_button_detected']}",
        "",
        "## Matches",
        "",
        *match_lines(inspection["matches"]),
        "",
        "## Detected Fields",
        "",
        *field_lines(inspection["fields"]),
        "",
        "## Guardrails",
        "",
        *bullet_lines(inspection["guardrails"]),
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    dry_run_path = resolve_dry_run_path(args.path)
    try:
        dry_run = load_dry_run(args.path)
        html, source = read_page_html(html_path=args.html, url=args.url)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Page inspection failed.\nError: {error}") from error

    inspection = build_inspection(dry_run, html, source)
    json_report = json.dumps(inspection, indent=2)
    markdown_report = build_markdown_report(inspection)
    print(markdown_report)

    if args.write:
        json_path = inspection_json_path(dry_run_path)
        markdown_path = inspection_markdown_path(dry_run_path)
        write_text_file(json_path, json_report)
        write_text_file(markdown_path, markdown_report)
        print("")
        print(f"Page inspection JSON written: {json_path}")
        print(f"Page inspection report written: {markdown_path}")


if __name__ == "__main__":
    main()
