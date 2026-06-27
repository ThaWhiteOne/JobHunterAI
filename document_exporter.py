from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap
from xml.sax.saxutils import escape as escape_xml
from zipfile import ZIP_DEFLATED, ZipFile


APPLICATION_DOCUMENTS = [
    ("resume", "Resume"),
    ("cover_letter", "Cover Letter"),
]


@dataclass(frozen=True)
class DocumentLine:
    kind: str
    text: str


def markdown_to_document_lines(content: str) -> list[DocumentLine]:
    lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append(DocumentLine("blank", ""))
        elif line.startswith("### "):
            lines.append(DocumentLine("heading3", line[4:]))
        elif line.startswith("## "):
            lines.append(DocumentLine("heading2", line[3:]))
        elif line.startswith("# "):
            lines.append(DocumentLine("heading1", line[2:]))
        elif line.startswith("- "):
            lines.append(DocumentLine("bullet", line[2:]))
        else:
            lines.append(DocumentLine("paragraph", line))

    while lines and lines[-1].kind == "blank":
        lines.pop()

    return lines


def markdown_to_lines(content: str) -> list[str]:
    plain_lines = []

    for line in markdown_to_document_lines(content):
        if line.kind == "blank":
            plain_lines.append("")
        elif line.kind == "bullet":
            plain_lines.append(f"- {line.text}")
        else:
            plain_lines.append(line.text)

    return plain_lines


def docx_run_properties(kind: str) -> str:
    if kind == "title":
        return "<w:b/><w:sz w:val=\"32\"/>"
    if kind == "heading1":
        return "<w:b/><w:sz w:val=\"28\"/>"
    if kind == "heading2":
        return "<w:b/><w:sz w:val=\"24\"/>"
    if kind == "heading3":
        return "<w:b/><w:sz w:val=\"22\"/>"
    return "<w:sz w:val=\"21\"/>"


def docx_paragraph_properties(kind: str) -> str:
    if kind == "title":
        return "<w:spacing w:after=\"240\"/>"
    if kind in ("heading1", "heading2", "heading3"):
        return "<w:spacing w:before=\"220\" w:after=\"80\"/>"
    if kind == "bullet":
        return "<w:ind w:left=\"360\" w:hanging=\"180\"/><w:spacing w:after=\"60\"/>"
    return "<w:spacing w:after=\"80\"/>"


def docx_paragraph(line: DocumentLine) -> str:
    text = f"- {line.text}" if line.kind == "bullet" else line.text
    escaped_text = escape_xml(text)
    return (
        "<w:p>"
        "<w:pPr>"
        f"{docx_paragraph_properties(line.kind)}"
        "</w:pPr>"
        "<w:r>"
        "<w:rPr>"
        f"{docx_run_properties(line.kind)}"
        "</w:rPr>"
        "<w:t xml:space=\"preserve\">"
        f"{escaped_text}"
        "</w:t>"
        "</w:r>"
        "</w:p>"
    )


def docx_document_xml(title: str, content: str) -> str:
    document_lines = [
        DocumentLine("title", title),
        DocumentLine("blank", ""),
        *markdown_to_document_lines(content),
    ]
    paragraphs = [docx_paragraph(line) for line in document_lines]

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraphs)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="720" w:right="900" w:bottom="720" w:left="900"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


def write_docx(path: Path, title: str, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(path, "w", ZIP_DEFLATED) as docx:
        docx.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
""",
        )
        docx.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
""",
        )
        docx.writestr("word/document.xml", docx_document_xml(title, content))


def pdf_escape(text: str) -> str:
    replacements = {
        "\\": "\\\\",
        "(": "\\(",
        ")": "\\)",
    }
    return "".join(replacements.get(character, character) for character in text)


def pdf_wrapped_lines(line: DocumentLine) -> list[DocumentLine]:
    if line.kind == "blank":
        return [line]

    text = f"- {line.text}" if line.kind == "bullet" else line.text
    width = 68 if line.kind in ("title", "heading1") else 84
    return [DocumentLine(line.kind, wrapped) for wrapped in wrap(text, width=width)]


def pdf_text_lines(title: str, content: str) -> list[DocumentLine]:
    raw_lines = [
        DocumentLine("title", title),
        DocumentLine("blank", ""),
        *markdown_to_document_lines(content),
    ]
    output_lines = []

    for line in raw_lines:
        output_lines.extend(pdf_wrapped_lines(line))

    return output_lines


def pdf_line_style(kind: str) -> tuple[int, int, int]:
    if kind == "title":
        return 16, 22, 8
    if kind == "heading1":
        return 14, 20, 8
    if kind in ("heading2", "heading3"):
        return 12, 18, 6
    if kind == "blank":
        return 10, 10, 0
    return 10, 14, 0


def pdf_pages(title: str, content: str) -> list[list[tuple[DocumentLine, int]]]:
    lines = pdf_text_lines(title, content)
    pages = [[]]
    y_position = 742

    for line in lines:
        font_size, leading, top_gap = pdf_line_style(line.kind)
        if y_position - top_gap - leading < 72:
            pages.append([])
            y_position = 742
        y_position -= top_gap
        pages[-1].append((line, y_position))
        y_position -= leading

    return pages or [[]]


def pdf_content_stream(lines: list[tuple[DocumentLine, int]]) -> str:
    commands = []

    for line, y_position in lines:
        if line.kind == "blank":
            continue
        font_size, _, _ = pdf_line_style(line.kind)
        commands.append("BT")
        commands.append(f"/F1 {font_size} Tf")
        commands.append(f"72 {y_position} Td")
        commands.append(f"({pdf_escape(line.text)}) Tj")
        commands.append("ET")

    return "\n".join(commands)


def write_pdf(path: Path, title: str, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    pages = pdf_pages(title, content)
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    page_object_numbers = []
    for page in pages:
        content_stream = pdf_content_stream(page)
        content_object_number = len(objects) + 2
        page_object_number = len(objects) + 1
        page_object_numbers.append(page_object_number)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_object_number} 0 R >>"
        )
        objects.append(
            f"<< /Length {len(content_stream.encode('latin-1', errors='replace'))} >>\n"
            "stream\n"
            f"{content_stream}\n"
            "endstream"
        )

    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>"

    pdf = "%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf.encode("latin-1", errors="replace")))
        pdf += f"{index} 0 obj\n{obj}\nendobj\n"

    xref_offset = len(pdf.encode("latin-1", errors="replace"))
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += (
        "trailer\n"
        f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_offset}\n"
        "%%EOF\n"
    )

    path.write_bytes(pdf.encode("latin-1", errors="replace"))


def export_docx_files(
    output_dir: Path,
    resume: str,
    cover_letter: str,
    linkedin_message: str,
) -> list[Path]:
    contents = {
        "resume": resume,
        "cover_letter": cover_letter,
    }
    exported_paths = []

    for document_id, title in APPLICATION_DOCUMENTS:
        path = output_dir / f"{document_id}.docx"
        write_docx(path, title, contents[document_id])
        exported_paths.append(path)

    return exported_paths


def export_pdf_files(
    output_dir: Path,
    resume: str,
    cover_letter: str,
    linkedin_message: str,
) -> list[Path]:
    contents = {
        "resume": resume,
        "cover_letter": cover_letter,
    }
    exported_paths = []

    for document_id, title in APPLICATION_DOCUMENTS:
        path = output_dir / f"{document_id}.pdf"
        write_pdf(path, title, contents[document_id])
        exported_paths.append(path)

    return exported_paths
