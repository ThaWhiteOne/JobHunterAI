import argparse
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from job_intake import DEFAULT_JOBS_DIR, index_path, save_job_description


DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_USER_AGENT = "JobHunterAI/1.0 (+local portfolio job importer)"


@dataclass(frozen=True)
class ImportedJob:
    company: str
    position: str
    url: str
    description: str
    source: str = "url-import"


class JobPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.json_ld_blocks: list[str] = []
        self._current_tag = ""
        self._skip_tag = ""
        self._json_ld_active = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        self._current_tag = tag

        if tag in {"script", "style", "noscript"}:
            self._skip_tag = tag
            script_type = attr_map.get("type", "").lower()
            if tag == "script" and "ld+json" in script_type:
                self._json_ld_active = True
                self._json_ld_parts = []
            return

        if tag == "meta":
            key = (attr_map.get("name") or attr_map.get("property") or "").lower()
            content = attr_map.get("content", "").strip()
            if key and content:
                self.meta[key] = content
            return

        if tag in {"br", "p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == self._skip_tag:
            if self._json_ld_active and self._json_ld_parts:
                self.json_ld_blocks.append("".join(self._json_ld_parts).strip())
            self._skip_tag = ""
            self._json_ld_active = False
            self._json_ld_parts = []
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.text_parts.append("\n")
        self._current_tag = ""

    def handle_data(self, data: str) -> None:
        if self._json_ld_active:
            self._json_ld_parts.append(data)
            return
        if self._skip_tag:
            return
        if self._current_tag == "title":
            self.title_parts.append(data)
        self.text_parts.append(data)

    @property
    def page_title(self) -> str:
        return clean_whitespace(" ".join(self.title_parts))

    @property
    def visible_text(self) -> str:
        return clean_multiline_text(" ".join(self.text_parts))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a public job posting URL into the local JobHunterAI job inbox."
    )
    parser.add_argument("url", help="Public job posting URL to import.")
    parser.add_argument("--company", default="", help="Override detected company name.")
    parser.add_argument("--position", default="", help="Override detected job title.")
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder where imported job descriptions are saved.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Fetch timeout in seconds.",
    )
    return parser.parse_args()


def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()


def clean_multiline_text(text: str) -> str:
    lines = [clean_whitespace(line) for line in re.split(r"[\r\n]+", text)]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines)


def strip_html_fragment(value: str) -> str:
    parser = JobPageParser()
    parser.feed(value)
    return parser.visible_text or clean_whitespace(re.sub(r"<[^>]+>", " ", value))


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be a valid http or https URL.")


def fetch_url_text(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    validate_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                raise ValueError(f"Expected an HTML job page, got: {content_type or 'unknown'}")
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.URLError as error:
        raise ConnectionError(f"Could not fetch job URL: {error}") from error


def find_job_posting_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        raw_type = value.get("@type", "")
        types = raw_type if isinstance(raw_type, list) else [raw_type]
        if any(str(item).lower() == "jobposting" for item in types):
            return value
        for child_key in ("@graph", "itemListElement"):
            found = find_job_posting_json(value.get(child_key))
            if found:
                return found
        for child in value.values():
            found = find_job_posting_json(child)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_job_posting_json(item)
            if found:
                return found
    return {}


def extract_json_ld_job(blocks: list[str]) -> dict[str, Any]:
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        found = find_job_posting_json(data)
        if found:
            return found
    return {}


def extract_hiring_organization(job_posting: dict[str, Any]) -> str:
    organization = job_posting.get("hiringOrganization", {})
    if isinstance(organization, dict):
        return clean_whitespace(str(organization.get("name", "")))
    return clean_whitespace(str(organization))


def title_from_page(parser: JobPageParser) -> str:
    for key in ("og:title", "twitter:title"):
        if parser.meta.get(key):
            return clean_whitespace(parser.meta[key])
    return parser.page_title


def description_from_page(parser: JobPageParser) -> str:
    for key in ("description", "og:description", "twitter:description"):
        if parser.meta.get(key):
            return clean_whitespace(parser.meta[key])
    return parser.visible_text


def extract_imported_job(
    html: str,
    url: str,
    company_override: str = "",
    position_override: str = "",
) -> ImportedJob:
    parser = JobPageParser()
    parser.feed(html)
    job_posting = extract_json_ld_job(parser.json_ld_blocks)

    detected_company = extract_hiring_organization(job_posting)
    detected_position = clean_whitespace(str(job_posting.get("title", "")))
    detected_description = strip_html_fragment(str(job_posting.get("description", "")))

    company = clean_whitespace(company_override) or detected_company or "Unknown Company"
    position = clean_whitespace(position_override) or detected_position or title_from_page(parser)
    description = detected_description or description_from_page(parser)

    if not position:
        position = "Imported Job"
    if not description or len(description) < 40:
        raise ValueError("Could not extract enough job description text from the page.")

    return ImportedJob(
        company=company,
        position=position,
        url=url,
        description=description,
    )


def import_job_url(
    url: str,
    jobs_dir: Path = DEFAULT_JOBS_DIR,
    company: str = "",
    position: str = "",
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> ImportedJob:
    html = fetch_url_text(url, timeout=timeout)
    imported = extract_imported_job(html, url, company, position)
    save_job_description(
        company=imported.company,
        position=imported.position,
        url=imported.url,
        source=imported.source,
        job_text=imported.description,
        jobs_dir=jobs_dir,
    )
    return imported


def main() -> None:
    args = parse_args()
    try:
        imported = import_job_url(
            url=args.url,
            jobs_dir=args.jobs_dir,
            company=args.company,
            position=args.position,
            timeout=args.timeout,
        )
    except (ConnectionError, OSError, ValueError) as error:
        raise SystemExit(f"Job URL import failed.\nError: {error}") from error

    print("Imported job posting.")
    print(f"Company: {imported.company}")
    print(f"Position: {imported.position}")
    print(f"Index file: {index_path(args.jobs_dir)}")


if __name__ == "__main__":
    main()
