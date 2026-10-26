"""Convert .docx files (or a folder of .docx files) to plain UTF-8 .txt files using only the Python standard library."""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _paragraph_text(elem: ET.Element) -> str:
    parts: list[str] = []
    for node in elem.iter():
        if node.tag == f"{W_NS}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W_NS}tab":
            parts.append("\t")
        elif node.tag in (f"{W_NS}br", f"{W_NS}cr"):
            parts.append("\n")
    return "".join(parts)


def docx_to_text(path: Path) -> str:
    """Extract plain text from a .docx file, preserving paragraph and table-row breaks."""
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    body = root.find(f"{W_NS}body")
    if body is None:
        return ""
    lines: list[str] = []
    for child in body:
        if child.tag == f"{W_NS}p":
            lines.append(_paragraph_text(child))
        elif child.tag == f"{W_NS}tbl":
            for row in child.findall(f".//{W_NS}tr"):
                cells = [
                    " ".join(_paragraph_text(p).strip() for p in cell.findall(f".//{W_NS}p")).strip()
                    for cell in row.findall(f"./{W_NS}tc")
                ]
                lines.append("\t".join(cells))
    return "\n".join(lines).rstrip() + "\n"


def convert_path(source: Path, out_dir: Path | None = None, *, recursive: bool = False) -> list[Path]:
    """Convert a single .docx file or all .docx files in a directory to .txt."""
    files = (
        [source]
        if source.is_file()
        else sorted((source.rglob if recursive else source.glob)("*.docx"))
    )
    written: list[Path] = []
    for docx_file in files:
        if docx_file.name.startswith("~$"):
            continue  # Skip temporary Word lock files.
        target_dir = out_dir if out_dir is not None else docx_file.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        txt_file = target_dir / f"{docx_file.stem}.txt"
        txt_file.write_text(docx_to_text(docx_file), encoding="utf-8", newline="\n")
        written.append(txt_file)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, help=".docx file(s) or folder(s) to convert.")
    parser.add_argument("-o", "--out-dir", type=Path, default=None, help="Optional output folder (defaults to next to each .docx).")
    parser.add_argument("-r", "--recursive", action="store_true", help="Search folders recursively for .docx files.")
    args = parser.parse_args()

    inputs = list(args.inputs)
    if not inputs:
        cwd_docx = [p for p in Path.cwd().glob("*.docx") if not p.name.startswith("~$")]
        if cwd_docx:
            inputs = cwd_docx
        else:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                picked = filedialog.askopenfilenames(
                    title="Select .docx files to convert to .txt",
                    filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
                )
                root.destroy()
                inputs = [Path(p) for p in picked]
            except Exception:
                inputs = [Path.cwd()]

    total = 0
    for item in inputs:
        for out_path in convert_path(item, args.out_dir, recursive=args.recursive):
            print(f"Wrote {out_path}")
            total += 1
    print(f"Converted {total} file(s).")


if __name__ == "__main__":
    main()
