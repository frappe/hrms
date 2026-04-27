"""Convert PRD markdown to PDF via HTML + Chrome headless."""
import sys
import subprocess
from pathlib import Path

import markdown

sys.stdout.reconfigure(encoding="utf-8")

DOC_DIR = Path(__file__).parent
MD_PATH = DOC_DIR / "PRD-korea-hrms-integration.md"
HTML_PATH = DOC_DIR / "PRD-korea-hrms-integration.html"
PDF_PATH = DOC_DIR / "PRD-korea-hrms-integration.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body {
    font-family: 'Segoe UI', 'Malgun Gothic', '맑은 고딕', 'Noto Sans CJK KR', sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1f2328;
    max-width: 100%;
    margin: 0;
    padding: 0;
}
h1 { font-size: 22pt; border-bottom: 2px solid #1f2328; padding-bottom: 6pt; margin-top: 0; }
h2 { font-size: 16pt; border-bottom: 1px solid #cbd2d9; padding-bottom: 4pt; margin-top: 20pt; }
h3 { font-size: 13pt; color: #324b62; margin-top: 14pt; }
h4 { font-size: 11pt; color: #4a5d6f; margin-top: 12pt; }
h1, h2, h3, h4 { page-break-after: avoid; }
p, li { margin: 4pt 0; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 8pt 0 12pt 0;
    page-break-inside: avoid;
    font-size: 10pt;
}
th, td {
    border: 1px solid #d0d7de;
    padding: 5pt 7pt;
    text-align: left;
    vertical-align: top;
}
th { background-color: #f0f3f6; font-weight: 600; }
code {
    background-color: #f4f5f7;
    padding: 1pt 4pt;
    border-radius: 3pt;
    font-family: 'Consolas', 'D2Coding', monospace;
    font-size: 9.5pt;
}
pre {
    background-color: #f4f5f7;
    padding: 8pt 10pt;
    border-radius: 4pt;
    overflow-x: auto;
    page-break-inside: avoid;
    font-size: 9.5pt;
    line-height: 1.4;
}
pre code { background: none; padding: 0; }
blockquote {
    border-left: 3pt solid #4a90e2;
    padding-left: 10pt;
    color: #4a5d6f;
    margin: 6pt 0;
    background: #f7faff;
    padding: 6pt 10pt;
}
hr { border: 0; border-top: 1px solid #d0d7de; margin: 16pt 0; }
ul, ol { padding-left: 22pt; }
strong { color: #0a0a0a; }
.cover-meta { color: #6c7681; font-size: 10pt; }
"""


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError("Chrome/Edge not found. Install or update CHROME_CANDIDATES.")


def main() -> None:
    md_text = MD_PATH.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "sane_lists",
            "nl2br",
        ],
        output_format="html5",
    )
    html_full = (
        "<!DOCTYPE html><html lang=\"ko\"><head>"
        "<meta charset=\"utf-8\">"
        "<title>PRD - Korea HRMS Integration</title>"
        f"<style>{CSS}</style>"
        "</head><body>"
        f"{html_body}"
        "</body></html>"
    )
    HTML_PATH.write_text(html_full, encoding="utf-8")
    print(f"[1/2] HTML written: {HTML_PATH} ({len(html_full)} bytes)")

    chrome = find_chrome()
    file_url = HTML_PATH.absolute().as_uri()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        file_url,
    ]
    print(f"[2/2] Running: {' '.join(cmd[:1])} headless ... -> {PDF_PATH}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise RuntimeError(f"Chrome failed: exit {result.returncode}")
    if not PDF_PATH.exists():
        raise RuntimeError("PDF was not created.")
    size_kb = PDF_PATH.stat().st_size / 1024
    print(f"PDF created: {PDF_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
