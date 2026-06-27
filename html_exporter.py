from html import escape
from pathlib import Path

from file_utils import write_text_file


HTML_STYLE = """
body {
    background: #f6f7f9;
    color: #1f2933;
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 32px;
}
main {
    background: #ffffff;
    border: 1px solid #d8dee4;
    margin: 0 auto;
    max-width: 840px;
    padding: 40px;
}
h1, h2, h3 {
    color: #111827;
    line-height: 1.25;
}
h1 {
    border-bottom: 2px solid #d8dee4;
    padding-bottom: 12px;
}
h2 {
    border-bottom: 1px solid #e5e7eb;
    margin-top: 32px;
    padding-bottom: 6px;
}
ul {
    padding-left: 24px;
}
"""


def markdown_to_html_document(title: str, content: str) -> str:
    body = "\n".join(markdown_to_html_lines(content))
    page_title = escape(title)

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{page_title}</title>
    <style>
{HTML_STYLE}
    </style>
</head>
<body>
    <main>
{body}
    </main>
</body>
</html>
"""


def markdown_to_html_lines(content: str) -> list[str]:
    html_lines = []
    paragraph_lines = []
    in_list = False

    def close_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            paragraph = "<br>".join(escape(line) for line in paragraph_lines)
            html_lines.append(f"<p>{paragraph}</p>")
            paragraph_lines = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            close_paragraph()
            close_list()
            continue

        if line.startswith("### "):
            close_paragraph()
            close_list()
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("## "):
            close_paragraph()
            close_list()
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("# "):
            close_paragraph()
            close_list()
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("- "):
            close_paragraph()
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{escape(line[2:])}</li>")
        else:
            paragraph_lines.append(line)

    close_paragraph()
    close_list()
    return html_lines


def export_html_files(
    output_dir: Path,
    resume: str,
    cover_letter: str,
    linkedin_message: str,
) -> list[Path]:
    documents = [
        ("resume.html", "Resume", resume),
        ("cover_letter.html", "Cover Letter", cover_letter),
        ("linkedin_message.html", "LinkedIn Message", linkedin_message),
    ]
    exported_paths = []

    for filename, title, content in documents:
        path = output_dir / filename
        write_text_file(path, markdown_to_html_document(title, content))
        exported_paths.append(path)

    return exported_paths
