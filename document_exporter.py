from pathlib import Path
from textwrap import wrap
from xml.sax.saxutils import escape as escape_xml
from zipfile import ZIP_DEFLATED, ZipFile


DOCUMENTS = [
    ("resume", "Resume"),
    ("cover_letter", "Cover Letter"),
    ("linkedin_message", "LinkedIn Message"),
]


def markdown_to_lines(content: str) -> list[str]:
    lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
        elif line.startswith("### "):
            lines.append(line[4:])
        elif line.startswith("## "):
            lines.append(line[3:])
        elif line.startswith("# "):
            lines.append(line[2:])
        elif line.startswith("- "):
            lines.append(f"- {line[2:]}")
        else:
            lines.append(line)

    while lines and not lines[-1]:
        lines.pop()

    return lines


def docx_paragraph(text: str) -> str:
    escaped_text = escape_xml(text)
    return (
        "<w:p>"
        "<w:r>"
        "<w:t xml:space=\"preserve\">"
        f"{escaped_text}"
        "</w:t>"
        "</w:r>"
        "</w:p>"
    )


def docx_document_xml(title: str, content: str) -> str:
    paragraphs = [docx_paragraph(title), docx_paragraph("")]
    paragraphs.extend(docx_paragraph(line) for line in markdown_to_lines(content))

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraphs)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/>
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


def pdf_text_lines(title: str, content: str) -> list[str]:
    raw_lines = [title, "", *markdown_to_lines(content)]
    output_lines = []

    for line in raw_lines:
        if not line:
            output_lines.append("")
            continue
        output_lines.extend(wrap(line, width=88) or [""])

    return output_lines


def pdf_pages(title: str, content: str, lines_per_page: int = 48) -> list[list[str]]:
    lines = pdf_text_lines(title, content)
    return [
        lines[index : index + lines_per_page]
        for index in range(0, len(lines), lines_per_page)
    ] or [[]]


def pdf_content_stream(lines: list[str]) -> str:
    commands = ["BT", "/F1 10 Tf", "72 740 Td", "14 TL"]

    for line in lines:
        commands.append(f"({pdf_escape(line)}) Tj")
        commands.append("T*")

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
        "linkedin_message": linkedin_message,
    }
    exported_paths = []

    for document_id, title in DOCUMENTS:
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
        "linkedin_message": linkedin_message,
    }
    exported_paths = []

    for document_id, title in DOCUMENTS:
        path = output_dir / f"{document_id}.pdf"
        write_pdf(path, title, contents[document_id])
        exported_paths.append(path)

    return exported_paths
