"""A deliberately report-specific, fail-closed public edition of WKRPT400.

Only ``generate_public_report`` (or the explicit ``--write`` CLI) writes the
canonical public source and manifest. ``prepare_report`` and ``report_result``
read that edition; they never regenerate it, compile TeX, or archive originals.
This is an importer for the inspected report, not a general privacy sanitizer.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup, Tag

from .latex import convert_document
from .notebook import normalize_labels


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIRECTORY = Path("notebook_sources/work-report")
SOURCE_NAME = "work_term_report.tex"
MANIFEST_NAME = "manifest.json"
PRIVATE_FIELDS = (
    "studentnumber", "userid", "employerstreetaddress", "employerlocation",
    "authorstreetaddress", "authorlocation", "authorpostalcode",
)
LABEL = re.compile(r"\\label\{([^{}]+)\}")
REFERENCE = re.compile(r"\\(Cref|cref|ref|eqref|autoref)\{([^{}]+)\}")
MATH = re.compile(r"\\begin\{(equation|multline\*|math)\}(.*?)\\end\{\1\}", re.S)
IMAGE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^{}]+)\}")
FLOAT = re.compile(r"\\begin\{(figure|table)\}(?:\[[^]]*\])?(.*?)\\end\{\1\}", re.S)
APPENDIX = re.compile(r"\\section\{([^{}]+)\}\s*\\label\{(app:[^{}]+)\}")

EDITION_NOTE = (
    "This is an undated historical 3B work-term report. The original used an "
    "automatically generated date; no completion date has been inferred. "
    "The author's substantive letter, acknowledgments, contributions, summary, "
    "scientific discussion, mathematical expressions, appendices and eleven "
    "manually written references are retained. Statements about simulation "
    "validation and scientific results are historical claims of the report, "
    "not new verification or assurances of correctness.\n\n"
    "Administrative student identifiers and postal/contact details have been "
    "removed. This standalone article does not distribute the original custom "
    "document class. The student work is not public domain, and no license or "
    "broader reuse permission is asserted. The template's author header is not "
    "a verified license; the absence of a confidentiality flag does not establish "
    "permission to publish or redistribute.\n\n"
    "Repeated equation labels have distinct namespaced identifiers. Missing "
    "or ambiguous historical references remain visible review notes rather than "
    "guessed links. Appendix letters and the original section-prefixed figure "
    "and table numbering are explicit in this edition."
)

FORMAT_CHANGES = [
    "Replace the entire administrative preamble with a standalone article preamble; retain only title, author, program and term metadata.",
    "Remove source comments, letter address/recipient/salutation block, student-number signature line and automatic date; retain every substantive letter paragraph and the author signature.",
    "Expand glossary uses to their supplied display names and retain all nine definitions in a description list at the original glossary position.",
    "Map front matter and the manually formatted References heading to standard sections; preserve all eleven written reference entries and their order, not a fabricated bibliography database.",
    "Replace the unused six-column/siunitx table specification with four standard columns matching the four unchanged cells in each row.",
    "Remove the one hard line break inside inline math; retain all other mathematical payload bytes apart from label normalization and LF line-ending normalization.",
    "Render the bibliography's Unicode author asterisk markers as standard text superscripts; retain their multiplicity.",
    "Normalize labels with site_content.notebook.normalize_labels; expand clever references to ordinary references, and use explicit Appendix A-H hyperlinks with supplemental anchors.",
    "Use starred, explicitly lettered appendix headings in both PDF and HTML; retain fourth-level headings through a paragraph alias, not flattening.",
    "Keep section-prefixed, globally increasing figure/table counters from the original class using standard article commands; the reader adds the matching caption numbers and resolves float references against the parsed DOM.",
    "Remove obsolete class layout commands for lists of figures/tables and the body page reset; no scientific prose is deleted or corrected.",
    "Actual Tectonic compilation exposed margin overflows: use 0.75-inch article margins and 3em emergency paragraph stretch without changing any math payload.",
    "Wrap the six historical web reference addresses with xurl-backed url commands; normalize only their whitespace, hard line breaks and escaped underscores, preserving every URL character and all eleven reference entries.",
]


def _uncomment(text: str) -> str:
    """Consume escaped control symbols before recognizing TeX line comments."""
    return re.sub(r"\\(?:[A-Za-z@]+|[^\r\n])|%[^\r\n]*",
                  lambda m: "" if m[0].startswith("%") else m[0], text)


def _group(text: str, start: int) -> tuple[str, int]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        raise ValueError("Unexpected report argument structure; review the importer before publishing.")
    depth = 0
    for match in re.finditer(r"\\(?:[A-Za-z@]+|[^\r\n])|[{}]", text[start:]):
        if match[0] == "{":
            depth += 1
        elif match[0] == "}":
            depth -= 1
            if not depth:
                end = start + match.end()
                return text[start + 1:end - 1], end
    raise ValueError("Unbalanced report argument; no public output was written.")


def _field(text: str, command: str) -> str:
    matches = list(re.finditer(r"\\" + re.escape(command) + r"(?![A-Za-z@])", text))
    if len(matches) != 1:
        raise ValueError("Unexpected report metadata structure; administrative values are not logged.")
    return _group(text, matches[0].end())[0]


def _document(text: str) -> str:
    if text.count(r"\begin{document}") != 1 or text.count(r"\end{document}") != 1:
        raise ValueError("Expected one complete report document.")
    return text.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]


def _comparable_private(value: str) -> str:
    value = unescape(unquote(value)).replace(r"\\", " ")
    value = re.sub(r"\\([_&%#$])", r"\1", value)
    return " ".join(value.casefold().split())


def _private_values(original: str) -> set[str]:
    """Keep values only in ephemeral memory; never return them in an audit."""
    active = _uncomment(original)
    preamble = active.split(r"\begin{document}", 1)[0]
    values = {_field(preamble, name) for name in PRIVATE_FIELDS}
    # The recipient's postal code is literal, not an author metadata macro.
    values.update(re.findall(r"\b[A-Z]\d[A-Z][ -]?\d[A-Z]\d\b", original, re.I))
    values.update(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", original))
    return {_comparable_private(value) for value in values if value.strip()}


def _assert_public(contents: list[str | bytes], private: set[str]) -> None:
    for content in contents:
        text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
        comparable = _comparable_private(text)
        if any(value in comparable for value in private):
            raise ValueError("Administrative content detected; public output was refused (values withheld).")
        if re.search(r"\\(?:print(?:studentnumber|userid|authorstreetaddress|authorlocation|authorpostalcode)|"
                     r"studentnumber|userid|employerstreetaddress|employerlocation|authorstreetaddress|"
                     r"authorlocation|authorpostalcode|today)\b", text):
            raise ValueError("An administrative command survived; public output was refused.")


def _glossary(text: str) -> list[dict]:
    entries = []
    for match in re.finditer(r"\\newglossaryentry\b", _uncomment(text)):
        active = _uncomment(text)
        key, end = _group(active, match.end())
        fields, _ = _group(active, end)
        values = {}
        for name in ("name", "description"):
            field = re.search(r"\b" + name + r"\s*=", fields)
            if field is None:
                raise ValueError("A glossary definition needs review.")
            values[name] = _group(fields, field.end())[0]
        entries.append({"key": key, **values})
    if len(entries) != 9 or len({item["key"] for item in entries}) != 9:
        raise ValueError("Expected the nine inspected glossary definitions.")
    return entries


def _floats(text: str) -> list[dict]:
    """The original class prefixes the section but does NOT reset float counters."""
    floats = []
    counters: Counter[str] = Counter()
    for match in FLOAT.finditer(text):
        kind, content = match.groups()
        counters[kind] += 1
        section = len(re.findall(r"\\section\{", text[:match.start()]))
        labels = LABEL.findall(content)
        images = IMAGE.findall(content)
        if len(labels) != 1 or (kind == "figure" and len(images) != 1):
            raise ValueError("Unexpected report float structure; no caption or label may be dropped.")
        entry = {"kind": kind, "label": labels[0], "number": f"{section}-{counters[kind]}",
                 "caption": _field(content, "caption")}
        if images:
            entry["image"] = images[0]
        floats.append(entry)
    if counters != {"figure": 7, "table": 1}:
        raise ValueError("Expected seven figures and one table in the inspected report.")
    return floats


def _public_paths(root: Path) -> tuple[Path, Path]:
    root = root.resolve()
    directory = root / PUBLIC_DIRECTORY
    paths = (directory / SOURCE_NAME, directory / MANIFEST_NAME)
    if not directory.resolve().is_relative_to(root) or any(path.is_symlink() for path in paths):
        raise ValueError("The public report destination must stay inside its own repository directory.")
    original = root / "WKRPT400"
    if directory.resolve().is_relative_to(original.resolve()):
        raise ValueError("The public edition must not overwrite original report files.")
    # A hard link is not revealed by resolve(); refuse one rather than mutate it.
    if any(path.exists() and path.stat().st_nlink > 1 for path in paths):
        raise ValueError("Public report files must not be hard-linked to other files.")
    return paths


def _preamble(metadata: dict) -> str:
    return r"""\documentclass[11pt]{article}
\usepackage{amsmath,amssymb,graphicx,braket}
\usepackage[margin=0.75in]{geometry}
\setlength{\emergencystretch}{3em}
\usepackage{titlesec}
\usepackage{xurl}
\usepackage[hidelinks]{hyperref}
\providecommand{\Tilde}{\tilde}
\newcommand{\subsubsubsection}{\paragraph}
\titleformat{\paragraph}[block]{\normalfont\normalsize\bfseries}{\theparagraph}{1em}{}
\titlespacing*{\paragraph}{0pt}{3.25ex plus 1ex minus .2ex}{1.5ex plus .2ex}
\setcounter{secnumdepth}{4}
\setcounter{tocdepth}{4}
\renewcommand{\thefigure}{\thesection-\arabic{figure}}
\renewcommand{\thetable}{\thesection-\arabic{table}}
% Starred front matter and explicitly lettered appendices also enter the PDF TOC.
% Pandoc reads the standard body headings with macro expansion disabled.
\makeatletter
\let\workreportsection\section
\renewcommand{\section}{\@ifstar{\workreportstarsection}{\workreportsection}}
\newcommand{\workreportstarsection}[1]{\workreportsection*{#1}\addcontentsline{toc}{section}{#1}}
\makeatother
""" + ("\\title{" + metadata["title"] + "}\n\\author{" + metadata["author"] +
       r"\\" + metadata["program"] + "}\n\\date{Undated historical " + metadata["term"] + " report}\n")


def assemble_public_report(root: Path = ROOT) -> tuple[str, dict]:
    """Return sanitized source and a value-free provenance audit; never write."""
    root = root.resolve()
    main = root / "WKRPT400/main.tex"
    glossary_source = root / "WKRPT400/gls.tex"
    original = main.read_text(encoding="utf-8-sig")
    active = _uncomment(original)
    preamble = active.split(r"\begin{document}", 1)[0]
    metadata = {key: _field(preamble, command) for key, command in (
        ("title", "reporttitle"), ("author", "authorname"), ("program", "program"), ("term", "term"))}
    if any(re.search(r"[\\{}@]", value) for value in metadata.values()):
        raise ValueError("Allowlisted public metadata must be plain text; review changes before publishing.")
    private = _private_values(original)
    glossary = _glossary(glossary_source.read_text(encoding="utf-8-sig"))
    document = _document(active)

    if document.count(r"\letterofsubmittal") != 1 or document.count(r"\contributions") != 1:
        raise ValueError("The inspected report front matter has changed; review sanitization boundaries.")
    letter, remainder = document.split(r"\letterofsubmittal", 1)[1].split(r"\contributions", 1)
    start = re.search(r'(?m)^This report, entitled ', letter)
    if start is None:
        raise ValueError("The substantive letter boundary needs review; no public output was written.")
    letter = letter[start.start():]
    letter, removed = re.subn(r"(?m)^[ \t]*\\printstudentnumber[ \t]*$", "", letter)
    if removed != 1:
        raise ValueError("The administrative signature layout has changed; review before publishing.")
    letter = letter.replace(r"\vspace{\baselineskip}", "").replace(r"\printauthorname\\", r"\printauthorname")
    content = ("\\section*{Letter of submittal}\n\\label{front:letter}\n\n" + letter.strip() +
               "\n\n\\section*{Contributions}\n\\label{front:contributions}\n" + remainder)
    for command, replacement in (
        ("summary", r"\section*{Summary}" + "\n" + r"\label{front:summary}"),
        ("tableofcontents", r"\tableofcontents"), ("listoffigures", ""), ("listoftables", ""), ("body", ""),
    ):
        content, count = re.subn(r"\\" + command + r"\b", lambda _: replacement, content)
        if count != 1:
            raise ValueError("A report front-matter boundary has changed.")
    for key in ("author", "program", "term"):
        command = "authorname" if key == "author" else key
        content = re.sub(r"\\print" + command + r"\b", lambda _, key=key: metadata[key], content)

    names = {entry["key"]: entry["name"] for entry in glossary}

    def glossary_use(match: re.Match[str]) -> str:
        if match[1] not in names:
            raise ValueError("An unknown glossary use needs review.")
        return names[match[1]]

    content = re.sub(r"\\gls\{([^{}]+)\}", glossary_use, content)
    definitions = "\n".join(r"\item[" + entry["name"] + "] " + entry["description"] for entry in glossary)
    content, count = re.subn(r"\\printglossaries\b", lambda _: (
        "\\section*{Glossary}\n\\label{front:glossary}\n\\begin{description}\n" + definitions +
        "\n\\end{description}"), content)
    if count != 1:
        raise ValueError("The glossary location needs review.")

    bibliography_heading = re.search(r"\\LARGE\{\\textbf\{References\}\}\s*\\\\\s*\\normalsize", content)
    if bibliography_heading is None:
        raise ValueError("The manually written bibliography boundary needs review.")
    bibliography, end = _group(content, bibliography_heading.end())
    reference_numbers = re.findall(r"(?m)^\[(\d+)\]", bibliography)
    if reference_numbers != [str(number) for number in range(1, 12)]:
        raise ValueError("Expected eleven ordered, manually written reference entries.")
    bibliography = re.sub("∗+", lambda m: r"\textsuperscript{" + "*" * len(m[0]) + "}", bibliography)
    bibliography, url_count = re.subn(
        r"(https?://.*?)(\.\s*\[Accessed:)",
        lambda m: r"\url{" + re.sub(r"\s+", "", m[1].replace(r"\\", "")).replace(r"\_", "_") + "}" + m[2],
        bibliography, flags=re.S,
    )
    if url_count != 6:
        raise ValueError("The six inspected bibliography URLs changed; review line wrapping.")
    content = (content[:bibliography_heading.start()] + "\\section*{References}\n\\label{front:references}\n" +
               bibliography + content[end:])
    content = content.replace(r"\vspace{13cm}", "")
    content, count = re.subn(r"\\begin\{tabular\}\{l r c r l S\[table-format=5\.4\]\}",
                             lambda _: r"\begin{tabular}{l r r r}", content)
    if count != 1:
        raise ValueError("The inspected four-column table layout has changed.")

    inline_breaks = 0

    def inline_layout(match: re.Match[str]) -> str:
        nonlocal inline_breaks
        if match[1] != "math":
            return match[0]
        inline_breaks += match[2].count(r"\\")
        return r"\begin{math}" + match[2].replace(r"\\", "") + r"\end{math}"

    content = MATH.sub(inline_layout, content)
    appendices = []

    def appendix_heading(match: re.Match[str]) -> str:
        letter = chr(ord("A") + len(appendices))
        anchor = "wr-appendix-" + letter.lower()
        appendices.append({"letter": letter, "title": match[1], "originalLabel": match[2], "anchor": anchor})
        return (r"\hypertarget{" + anchor + "}{}\n\\section*{Appendix " + letter + ": " + match[1] +
                "}\n\\label{" + match[2] + "}")

    content, count = re.subn(r"\\appendix\b", "", content)
    if count != 1:
        raise ValueError("The appendix boundary has changed.")
    content = APPENDIX.sub(appendix_heading, content)
    if len(appendices) != 8:
        raise ValueError("Expected all eight inspected appendices.")
    by_appendix = {entry["originalLabel"]: entry for entry in appendices}

    def reference(match: re.Match[str]) -> str:
        command, label = match.groups()
        if label in by_appendix:
            entry = by_appendix[label]
            title = ("Appendix " if command in ("Cref", "cref", "autoref") else "") + entry["letter"]
            return r"\hyperlink{" + entry["anchor"] + "}{" + title + "}"
        if command in ("Cref", "cref"):
            prefix = {"fig": "Figure", "tab": "Table", "eq": "Equation"}.get(label.split(":", 1)[0])
            if prefix is None:
                raise ValueError("An unrecognized clever-reference type needs review.")
            return prefix + r"~\ref{" + label + "}"
        return match[0]

    content = REFERENCE.sub(reference, content)
    content, label_audit = normalize_labels(content, "wr")
    for entry in appendices:
        entry["label"] = label_audit["labels"][entry["originalLabel"]][0]
    if re.search(r"\\(?:print[A-Za-z]+|gls|Cref|cref|letterofsubmittal|contributions|summary|body)\b", content):
        raise ValueError("An unexpanded report-specific command needs review.")

    output = (_preamble(metadata) + "\n\\begin{document}\n\\maketitle\n\n"
              "\\section*{Public edition note}\n\\label{work-report-edition}\n\n" + EDITION_NOTE +
              "\n\n" + content.strip() + "\n\n\\end{document}\n")
    floats = _floats(content)
    images = []
    for name in IMAGE.findall(content):
        if Path(name).name != name or not re.fullmatch(r"[A-Za-z0-9_-]+\.png", name):
            raise ValueError("Report images must use the inspected simple PNG filenames.")
        image = root / "WKRPT400" / name
        if not image.resolve().is_relative_to((root / "WKRPT400").resolve()):
            raise ValueError("A report image escapes the original image directory.")
        data = image.read_bytes()
        _assert_public([data], private)
        images.append({"archive": name, "asset": name, "sha256": sha256(data).hexdigest()})
    math_counts = Counter(match[1] for match in MATH.finditer(document))
    # Check preservation before writing, not just after Pandoc's math shielding.
    def math_signature(text: str) -> list[tuple[str, str]]:
        return [(m[1], LABEL.sub("", m[2]).replace(r"\\", "") if m[1] == "math" else LABEL.sub("", m[2]))
                for m in MATH.finditer(text)]

    if math_signature(document) != math_signature(_document(output)):
        raise ValueError("A mathematical payload changed beyond the documented label/layout adaptations.")
    counts = {
        "sourceLines": len(original.splitlines()), "activeLines": len(active.splitlines()),
        "numberedEquations": math_counts["equation"], "unnumberedDisplays": math_counts["multline*"],
        "displayMath": math_counts["equation"] + math_counts["multline*"], "inlineMath": math_counts["math"],
        "figures": 7, "tables": 1, "glossaryDefinitions": len(glossary), "appendices": len(appendices),
        "manualReferences": len(reference_numbers), "inlineLayoutBreaksRemoved": inline_breaks,
    }
    original_labels = Counter(LABEL.findall(document))
    manifest = {
        "schemaVersion": 1, "edition": {**metadata, "dateStatus": "undated historical 3B report", "completionDate": None},
        "inputs": {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest() for path in (main, glossary_source)},
        "counts": counts, "labelAudit": label_audit,
        "duplicateOriginalLabels": {key: value for key, value in original_labels.items() if value > 1},
        "floats": floats, "images": images, "appendices": appendices, "glossary": glossary,
        "privacy": {"removedAdministrativeFields": list(PRIVATE_FIELDS), "originalFolderDistributed": False,
                    "templateClassDistributed": False, "originalCommentsDistributed": False},
        "editorialNote": EDITION_NOTE, "formatChanges": FORMAT_CHANGES,
        "outputSha256": sha256(output.encode("utf-8")).hexdigest(),
    }
    _assert_public([output, json.dumps(manifest, ensure_ascii=False)], private)
    return output, manifest


def generate_public_report(root: Path = ROOT) -> Path:
    """Explicitly write only the sanitized source and deterministic manifest."""
    source, audit_path = _public_paths(root)
    text, manifest = assemble_public_report(root)
    source.parent.mkdir(parents=True, exist_ok=True)
    for path, content in ((source, text), (audit_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")):
        data = content.encode("utf-8")
        # An identical regeneration should not even change filesystem mtimes.
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
    return source


def prepare_report(root: Path = ROOT) -> Path:
    """Validate and read the expected edition; missing/stale output never rebuilds."""
    source, audit_path = _public_paths(root)
    if not source.is_file() or not audit_path.is_file():
        raise FileNotFoundError("Public report not generated. Explicitly run python -B -m site_content.work_report --write.")
    manifest = json.loads(audit_path.read_text(encoding="utf-8"))
    if manifest.get("schemaVersion") != 1 or manifest.get("outputSha256") != sha256(source.read_bytes()).hexdigest():
        raise ValueError("Public report source/manifest mismatch; review and explicitly regenerate.")
    # Do not use arbitrary manifest paths to read files outside the known inputs.
    expected_inputs = {"WKRPT400/main.tex", "WKRPT400/gls.tex"}
    if set(manifest.get("inputs", {})) != expected_inputs:
        raise ValueError("Public report input inventory mismatch.")
    for name in sorted(expected_inputs):
        if sha256((root / name).read_bytes()).hexdigest() != manifest["inputs"][name]:
            raise ValueError("Original report changed; review and explicitly regenerate the public edition.")
    private = _private_values((root / "WKRPT400/main.tex").read_text(encoding="utf-8-sig"))
    _assert_public([source.read_bytes(), audit_path.read_bytes()], private)
    return source


def _reader_floats(result: dict, manifest: dict) -> dict:
    """Resolve only proven float references; never suppress unrelated warnings.

    Observed Pandoc AST: Figure carries its label; a labelled table is a Div
    containing Table. The shared converter leaves float refs as inline Math and
    reports them unresolved because it only indexes headings/equation labels.
    """
    body = BeautifulSoup(result["body"], "html.parser")
    floats = {entry["label"]: entry for entry in manifest["floats"]}
    repairs = []
    for label, entry in floats.items():
        target = body.find(id=label)
        if not isinstance(target, Tag):
            raise ValueError("Pandoc lost a report float anchor; conversion needs review.")
        if entry["kind"] == "figure":
            caption = target.find("figcaption") if target.name == "figure" else None
            image = target.find("img")
            if isinstance(image, Tag):
                image["alt"] = entry["caption"]
        else:
            table = target if target.name == "table" else target.find("table")
            caption = table.find("caption") if isinstance(table, Tag) else None
        if not isinstance(caption, Tag) or caption.get_text(" ", strip=True) != entry["caption"]:
            raise ValueError("Pandoc changed or lost a report caption; conversion needs review.")
        prefix = body.new_tag("span", attrs={"class": "work-report-caption-number"})
        prefix.string = entry["kind"].title() + " " + entry["number"] + ": "
        caption.insert(0, prefix)

    resolved: Counter[str] = Counter()
    for span in body.select("span.math.inline"):
        text = span.get_text()
        match = REFERENCE.fullmatch(text[2:-2]) if text.startswith(r"\(") and text.endswith(r"\)") else None
        if match is None or match[2] not in floats:
            continue
        command, label = match.groups()
        entry = floats[label]
        number = entry["number"]
        link = body.new_tag("a", href="#" + quote(label, safe="-._~:"), attrs={"class": "tex-reference"})
        link.string = f"({number})" if command == "eqref" else (entry["kind"].title() + " " + number if command == "autoref" else number)
        span.replace_with(link)
        resolved[label] += 1
    consumed = set()
    for label, count in resolved.items():
        warning = f"Unresolved reference {label!r}; the source has no matching heading or equation label."
        consumed.add(warning)
        repairs.append({"kind": "float-reference", "label": label, "number": floats[label]["number"],
                        "occurrences": count, "evidence": "Parsed float anchor and unchanged caption"})
    warnings = [warning for warning in result["warnings"] if warning not in consumed]
    for item in body.select(".tex-conversion-warnings li"):
        if item.get_text() in consumed:
            item.decompose()
    for note in body.select(".tex-conversion-warnings"):
        if not note.select("li"):
            note.decompose()
    for link in body.select(".tex-source-download a"):
        link.string = "Download sanitized public LaTeX source"
    ids = [str(tag["id"]) for tag in body.select("[id]")]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate reader IDs; public report conversion needs review.")
    for link in body.select('a[href^="#"]'):
        if unquote(str(link["href"])[1:]) not in ids:
            raise ValueError("Broken local report link; public report conversion needs review.")
    return {**result, "body": str(body), "warnings": warnings, "reader_repairs": repairs}


def report_result(root: Path, assets: Path, asset_url: str) -> dict:
    """Return the normal converter fragments plus the public audit and repairs.

    The parent can call source_zip(prepare_report(root), assets) afterwards.
    Never pass an original source/class/directory to that archive operation.
    """
    root = root.resolve()
    source = prepare_report(root)
    images = root / "WKRPT400"
    asset_directory = assets.resolve()
    for protected in (images.resolve(), source.parent.resolve()):
        if asset_directory.is_relative_to(protected) or protected.is_relative_to(asset_directory):
            raise ValueError("Reader assets must be separate from original and canonical report files.")
    manifest = json.loads((source.parent / MANIFEST_NAME).read_text(encoding="utf-8"))
    private = _private_values((images / "main.tex").read_text(encoding="utf-8-sig"))
    for entry in manifest["images"]:
        name = entry["asset"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+\.png", name):
            raise ValueError("Unsafe public report image inventory.")
        data = (images / name).read_bytes()
        if sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Original report image changed; review and explicitly regenerate.")
        _assert_public([data], private)
    result = convert_document(source, images, assets, asset_url, source_root=images)
    result = _reader_floats(result, manifest)
    _assert_public([result["body"], result["toc"]], private)
    result["report_manifest"] = manifest
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Explicitly regenerate only the public report source and manifest")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root (also useful for isolated tests)")
    args = parser.parse_args(argv)
    source = generate_public_report(args.root) if args.write else prepare_report(args.root)
    manifest = json.loads((source.parent / MANIFEST_NAME).read_text(encoding="utf-8"))
    counts = manifest["counts"]
    print(f'Public historical report: {counts["displayMath"]} display blocks, {counts["inlineMath"]} inline math, '
          f'{counts["figures"]} figures, {counts["tables"]} table; write={args.write}')


if __name__ == "__main__":
    main()