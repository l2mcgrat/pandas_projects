"""Convert a trusted, single-file LaTeX document into embeddable reader fragments.

Public API: convert_document(source, image_dir, asset_dir, asset_url) -> dict.
The result has body, toc, headings ({id, title, level, number}), equation_count,
image_count, warnings, and source_name. Counts mean display-math blocks (not
numbered rows of an align) and image occurrences, respectively. Unnumbered
headings have number=""; levels are h1 through h6, with subsubsubsection at h4.

Requires pypandoc_binary and beautifulsoup4. No TeX engine, shell, network,
stylesheet, script, page shell, or publishing step is invoked. Put body inside
article.tex-paper, toc in the sidebar, and display warnings to the publisher.
Warnings also appear visibly in body; unsupported raw TeX is shown as code.

The parent must load MathJax with tags='ams', processEnvironments=True, the
ams/braket/cancel packages and the source's custom math definitions. Typeset
only this article, once, with a fresh equation counter (texReset(0) before a
dynamic replacement). Original math payloads, environments, labels, tags and
notag/nonumber commands are preserved, not renumbered by this module. TeX
equation-counter customizations are rejected rather than silently misnumbered.
Pandoc macro expansion is disabled: it otherwise expands this document's
paragraph redefinition and loses every fourth-level heading.

All referenced browser-displayable images are validated before any copying.
They are copied relative to image_dir; the byte-identical source is copied as
asset_dir/source.name and linked in body. A parent may offer a ZIP, recreating
the original includegraphics paths; this module deliberately does not zip or
edit the source. Physical page spacing is discarded, not prose/list/table
structure. This is a document converter, not a general TeX compiler/sanitizer.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import re
import shutil
import subprocess
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from bs4 import BeautifulSoup, Tag
import pypandoc


_TOKEN = re.compile(r"\\(?:[A-Za-z@]+|[^\r\n])|[$%]")
_GROUP = re.compile(r"\s*\{([^{}]+)\}")
_ENVIRONMENTS = {
    "math", "displaymath", "equation", "equation*", "align", "align*",
    "alignat", "alignat*", "flalign", "flalign*", "gather", "gather*",
    "multline", "multline*", "eqnarray", "eqnarray*",
}
_VERBATIM = {"verbatim", "verbatim*", "lstlisting", "minted", "comment"}
_LAYOUT = re.compile(
    r"\\(?:maketitle|tableofcontents|newpage|clearpage|cleardoublepage|"
    r"centering|raggedright|raggedleft|noindent|normalsize|small|footnotesize|"
    r"scriptsize|tiny|large|Large|LARGE|huge|Huge|medskip|smallskip|bigskip)\s*"
    r"|\\(?:hspace|vspace)\*?\s*\{[^{}]*\}\s*"
    r"|\\(?:pagebreak|nopagebreak)\s*(?:\[[0-4]\])?\s*"
)
_REFERENCE = re.compile(r"\\(ref|eqref|autoref)\s*\{([^{}]+)\}\s*")
_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".avif")


@dataclass(frozen=True)
class _Math:
    original: str
    payload: str
    display: bool
    line: int
    placeholder: str


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _tokens(text: str, start: int = 0) -> Iterator[re.Match[str]]:
    """Lex control sequences; escaped dollars/percent signs are single tokens."""
    while match := _TOKEN.search(text, start):
        if match[0] == "%":
            newline = text.find("\n", match.end())
            start = len(text) if newline < 0 else newline + 1
            continue
        yield match
        start = match.end()


def _math_end(text: str, start: int, closing: str, environment: str = "") -> int:
    depth = 1
    for token in _tokens(text, start):
        if environment and token[0] in (r"\begin", r"\end"):
            group = _GROUP.match(text, token.end())
            if group and group[1] == environment:
                depth += 1 if token[0] == r"\begin" else -1
                if depth == 0:
                    return group.end()
        elif not environment and token[0] == closing:
            if closing != "$$":
                return token.end()
        elif not environment and closing == "$$" and token[0] == "$":
            if text.startswith("$$", token.start()):
                return token.start() + 2
    raise ValueError(f"Unclosed math: expected {closing!r} after line {text.count(chr(10), 0, start) + 1}.")


def _prepare(text: str, warnings: list[str]) -> tuple[str, dict[str, _Math]]:
    """Shield exact math bytes from Pandoc; map only body heading commands.

    This is a small lexical pass, NOT an HTML or general LaTeX parser. Pandoc
    still parses headings, prose, lists, tables, images and other structure.
    """
    document = next((m for m in _tokens(text) if m[0] == r"\begin"
                     and (g := _GROUP.match(text, m.end())) and g[1] == "document"), None)
    in_body = document is None
    pieces: list[str] = []
    slots: dict[str, _Math] = {}
    prefix = "SCMATH" + sha256(text.encode("utf-8")).hexdigest()[:16]
    position = 0
    while match := _TOKEN.search(text, position):
        pieces.append(text[position:match.start()])
        token = match[0]
        end = match.end()
        replacement = token
        group = _GROUP.match(text, end) if token in (r"\begin", r"\end") else None
        environment = group[1] if group else ""
        line = text.count("\n", 0, match.start()) + 1
        if token == "%":
            newline = text.find("\n", end)
            end = len(text) if newline < 0 else newline + 1
            replacement = text[match.start():end]
        elif token == r"\verb":
            delimiter = end + (text[end:end + 1] == "*")
            if delimiter < len(text):
                closing = text.find(text[delimiter], delimiter + 1)
                if closing < 0:
                    raise ValueError(f"Unclosed \\verb on line {line}.")
                end = closing + 1
                replacement = text[match.start():end]
        elif token == r"\begin" and environment in _VERBATIM:
            closing = text.find(r"\end{" + environment + "}", end)
            if closing < 0:
                raise ValueError(f"Unclosed {environment} environment on line {line}.")
            end = closing + len(environment) + 6
            replacement = text[match.start():end]
        elif environment == "document":
            in_body = token == r"\begin"
            # With macro expansion disabled Pandoc emits preamble definitions
            # as raw body blocks. They belong to the parent MathJax config, not
            # the reader. Parse just the body, retaining original line tracking.
            if in_body:
                pieces.clear()
                replacement = ""
                end = group.end() if group else end
            else:
                position = len(text)
                break
        elif token in (r"\numberwithin", r"\counterwithin", r"\counterwithout"):
            first = _GROUP.match(text, end)
            if first and first[1] == "equation":
                raise ValueError(f"Equation counter customization {token} on line {line} is unsupported; use explicit \\tag{{...}} values or configure a dedicated converter.")
        elif token in (r"\setcounter", r"\addtocounter"):
            first = _GROUP.match(text, end)
            if first and first[1] == "equation":
                raise ValueError(f"Equation counter customization {token} on line {line} is unsupported; use explicit \\tag{{...}} values.")
        elif token == r"\theequation":
            raise ValueError(f"Custom \\theequation on line {line} is unsupported; use explicit \\tag{{...}} values.")
        elif in_body:
            display = True
            payload = None
            if token == r"\begin" and environment in _ENVIRONMENTS and group:
                end = _math_end(text, group.end(), r"\end{" + environment + "}", environment)
                display = environment != "math"
                if environment in ("math", "displaymath"):
                    close = text.rfind(r"\end", group.end(), end)
                    payload = text[group.end():close]
                else:
                    payload = text[match.start():end]
            elif token in ("$", r"\(", r"\["):
                opening = "$$" if text.startswith("$$", match.start()) else token
                closing = {"$": "$", "$$": "$$", r"\(": r"\)", r"\[": r"\]"}[opening]
                display = opening in ("$$", r"\[")
                end = _math_end(text, match.start() + len(opening), closing)
                payload = text[match.start() + len(opening):end - len(closing)]
            elif token == r"\subsubsubsection":
                replacement = r"\paragraph"
            elif token in (r"\textbf", r"\textit", r"\texttt", r"\emph"):
                if not text[end:].lstrip().startswith("{"):
                    warnings.append(f"Line {line}: unbraced {token}; check the source formatting command.")
            if payload is not None:
                key = prefix + str(len(slots))
                replacement = (r"\[" + key + r"\]") if display else (r"\(" + key + r"\)")
                slots[key] = _Math(text[match.start():end], payload, display, line, replacement)
        pieces.append(replacement)
        position = end
    pieces.append(text[position:])
    return "".join(pieces), slots


def _pandoc(text: str, source_format: str, target: str, warnings: list[str]) -> str:
    try:
        executable = pypandoc.get_pandoc_path()
    except OSError as exc:
        raise RuntimeError("Pandoc is unavailable. Install pypandoc_binary in the selected Python interpreter.") from exc
    command = [executable, "--from=" + source_format, "--to=" + target,
               "--sandbox", "--wrap=none"]
    if target == "html5":
        command.extend(["--mathjax", "--number-sections"])
    result = subprocess.run(command, input=text, encoding="utf-8", capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"Pandoc could not convert this LaTeX document. Check the indicated source command:\n{result.stderr.strip()}")
    if result.stderr.strip():
        warnings.append("Pandoc: " + result.stderr.strip())
    return result.stdout


def _transform(value: Any, slots: dict[str, _Math], warnings: list[str], seen: Counter[str]) -> Any:
    if isinstance(value, list):
        output = []
        for child in value:
            converted = _transform(child, slots, warnings, seen)
            # JSON null is meaningful in Pandoc tuples (e.g. short captions).
            # Only a removed AST node, not an original null, should disappear.
            if converted is not None or child is None:
                if isinstance(child, dict) and isinstance(converted, list):
                    output.extend(converted)
                else:
                    output.append(converted)
        return output
    if not isinstance(value, dict):
        return value
    node = {key: _transform(child, slots, warnings, seen) for key, child in value.items()}
    kind = node.get("t")
    if kind == "Math" and node["c"][1] in slots:
        key = node["c"][1]
        seen[key] += 1
        node["c"] = [{"t": "DisplayMath" if slots[key].display else "InlineMath"}, slots[key].payload]
        node["source_key"] = key
    elif kind in ("RawInline", "RawBlock"):
        raw_format, raw = node["c"]
        if raw_format in ("tex", "latex") and _LAYOUT.fullmatch(raw):
            return None
        if raw_format in ("tex", "latex") and _REFERENCE.fullmatch(raw):
            # Pandoc's writer correctly emits these as MathJax inline references.
            return node
        for key, math in slots.items():
            if math.placeholder in raw:
                seen[key] += raw.count(math.placeholder)
                raw = raw.replace(math.placeholder, math.original)
        warnings.append(f"Unsupported {raw_format} command retained visibly: {raw}")
        return {"t": "CodeBlock" if kind == "RawBlock" else "Code",
                "c": [["", ["tex-unsupported"], []], raw]}
    if kind in ("Para", "Plain"):
        blocks: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []

        def flush() -> None:
            while pending and pending[0]["t"] in ("Space", "SoftBreak"):
                pending.pop(0)
            while pending and pending[-1]["t"] in ("Space", "SoftBreak"):
                pending.pop()
            if pending:
                blocks.append({"t": kind, "c": pending.copy()})
                pending.clear()

        for inline in node["c"]:
            if inline["t"] == "Math" and inline["c"][0]["t"] == "DisplayMath":
                flush()
                blocks.append({"t": "Div", "c": [["", ["tex-display-math"], []],
                                                     [{"t": "Plain", "c": [inline]}]]})
            else:
                pending.append(inline)
        flush()
        return blocks
    return node


def _inline_text(value: Any) -> str:
    if isinstance(value, list):
        return "".join(_inline_text(child) for child in value)
    if not isinstance(value, dict):
        return ""
    kind = value.get("t")
    if kind == "Str":
        return value["c"]
    if kind in ("Math", "Code"):
        return value["c"][1]
    if kind in ("Space", "SoftBreak", "LineBreak"):
        return " "
    if kind in ("Link", "Image", "Span"):
        return _inline_text(value["c"][1])
    return _inline_text(value.get("c", []))


def _heading_ids(ast: dict[str, Any], slots: dict[str, _Math], warnings: list[str]) -> None:
    used: set[str] = set()
    for node in _walk(ast):
        if node.get("t") != "Header":
            continue
        attr = node["c"][1]
        base = attr[0]
        if not base or any(key.lower() in base.lower() for key in slots):
            base = re.sub(r"[^\w\s-]", "", _inline_text(node["c"][2]).lower())
            base = re.sub(r"[\s_]+", "-", base).strip("-") or "section"
        identifier = base
        suffix = 1
        while identifier in used:
            identifier = f"{base}-{suffix}"
            suffix += 1
        if identifier != base:
            warnings.append(f"Duplicate heading anchor {base!r} disambiguated as {identifier!r}; references use the first occurrence.")
        used.add(identifier)
        attr[0] = identifier


def _image_path(reference: str, source: Path, image_dir: Path) -> Path:
    url = urlsplit(reference)
    if url.scheme or url.netloc or url.query or url.fragment:
        raise ValueError(f"Image {reference!r} must be a local file under {image_dir}.")
    relative = Path(unquote(url.path))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe image path {reference!r}; use a path inside {image_dir}.")
    candidates = [image_dir / relative, source.parent / relative]
    if not relative.suffix:
        candidates = [path.with_suffix(suffix) for path in candidates for suffix in _IMAGE_SUFFIXES]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_relative_to(image_dir) and resolved.is_file():
            if resolved.suffix.lower() not in _IMAGE_SUFFIXES:
                raise ValueError(f"Image {reference!r} is not browser-displayable; export it to PNG or SVG and update a working copy of the source.")
            return resolved
    raise FileNotFoundError(f"Missing referenced image {reference!r} in {source.name}. Looked under {image_dir} and {source.parent}; supply the original image in image_dir (or its referenced subdirectory).")


def _toc_and_headings(body: BeautifulSoup) -> tuple[str, list[dict[str, Any]]]:
    toc = BeautifulSoup("", "html.parser")
    nav = toc.new_tag("nav", attrs={"class": "tex-toc", "aria-label": "Table of contents"})
    root = toc.new_tag("ol")
    nav.append(root)
    toc.append(nav)
    parents: list[tuple[int, Tag]] = []
    headings: list[dict[str, Any]] = []
    for heading in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        title = BeautifulSoup(str(heading), "html.parser")
        for number_span in title.select(".header-section-number"):
            number_span.decompose()
        level = int(heading.name[1])
        item = {"id": str(heading["id"]), "title": title.get_text(" ", strip=True),
                "level": level, "number": str(heading.get("data-number", ""))}
        headings.append(item)
        while parents and parents[-1][0] >= level:
            parents.pop()
        container = root
        if parents:
            parent = parents[-1][1]
            nested = parent.find("ol", recursive=False)
            if not isinstance(nested, Tag):
                nested = toc.new_tag("ol")
                parent.append(nested)
            container = nested
        li = toc.new_tag("li", attrs={"data-level": str(level)})
        link = toc.new_tag("a", href="#" + quote(item["id"], safe="-._~:"))
        link.string = (item["number"] + " " + item["title"]).strip()
        li.append(link)
        container.append(li)
        parents.append((level, li))
    return str(toc), headings


def convert_document(source: Path, image_dir: Path, asset_dir: Path, asset_url: str) -> dict:
    """Return body/TOC fragments and metadata; copy source and referenced images.

    Raises FileNotFoundError for absent inputs/images, ValueError for malformed
    TeX, unsupported numbering, or unsafe paths, and RuntimeError for a missing
    Pandoc binary. No output is copied until parsing and image preflight pass.
    asset_url must be a browser-relative directory URL, e.g.
    '../assets/documents/mental-map'. Image extensions may be omitted in TeX.
    """
    source, image_dir, asset_dir = source.resolve(), image_dir.resolve(), asset_dir.resolve()
    prefix = urlsplit(asset_url)
    if not asset_url or prefix.scheme or prefix.netloc or prefix.query or prefix.fragment or asset_url.startswith(("/", "\\")) or "\\" in asset_url:
        raise ValueError("asset_url must be a browser-relative directory URL without a query or fragment.")
    base_url = quote(unquote(prefix.path).rstrip("/"), safe="/-._~")
    warnings: list[str] = []
    text = source.read_bytes().decode("utf-8-sig")
    prepared, slots = _prepare(text, warnings)
    ast = json.loads(_pandoc(prepared, "latex+raw_tex-latex_macros", "json", warnings))
    seen: Counter[str] = Counter()
    ast = _transform(ast, slots, warnings, seen)
    for key, math in slots.items():
        if seen[key] != 1:
            raise ValueError(f"Pandoc lost or duplicated math from {source.name}, line {math.line}; simplify the surrounding unsupported command.")
    _heading_ids(ast, slots, warnings)
    images = [node for node in _walk(ast) if node.get("t") == "Image"]
    copies: dict[Path, Path] = {}
    image_manifest = []
    for image in images:
        original = _image_path(image["c"][2][0], source, image_dir)
        relative = original.relative_to(image_dir)
        reference = Path(unquote(image["c"][2][0]))
        if not reference.suffix:
            reference = reference.with_suffix(original.suffix)
        image_manifest.append({"archive": reference.as_posix(), "asset": relative.as_posix()})
        copies[original] = asset_dir / relative
        image["c"][2][0] = base_url + "/" + quote(relative.as_posix(), safe="/-._~")
    # Pandoc and text-mode subprocess pipes normalize CRLF. Emit empty marked
    # spans through its writer, then fill them with the original text via the
    # HTML DOM. The AST has already determined inline vs standalone placement.
    for node in _walk(ast):
        if node.get("t") == "Math" and "source_key" in node:
            key = node.pop("source_key")
            mode = "display" if slots[key].display else "inline"
            node.update(t="RawInline", c=["html", f'<span class="math {mode}" data-tex-key="{key}"></span>'])
    body = BeautifulSoup(_pandoc(json.dumps(ast), "json", "html5", warnings), "html.parser")
    for span in body.select("span[data-tex-key]"):
        math = slots[str(span["data-tex-key"])]
        span.string = (r"\[" + math.payload + r"\]") if math.display else (r"\(" + math.payload + r"\)")
        del span["data-tex-key"]
    toc, headings = _toc_and_headings(body)
    by_id = {heading["id"]: heading for heading in headings}
    labels = Counter()
    for math in slots.values():
        for token in _tokens(math.payload):
            if token[0] == r"\label" and (group := _GROUP.match(math.payload, token.end())):
                labels[group[1]] += 1
    for label, count in labels.items():
        if count > 1:
            warnings.append(f"Duplicate equation label {label!r}; fix the source before relying on references.")
    for span in body.select("span.math.inline"):
        content = span.get_text()
        ref = _REFERENCE.fullmatch(content[2:-2]) if content.startswith(r"\(") and content.endswith(r"\)") else None
        if not ref:
            continue
        command, label = ref.groups()
        if label in by_id:
            heading = by_id[label]
            link = body.new_tag("a", href="#" + quote(label, safe="-._~:"), attrs={"class": "tex-reference"})
            number = heading["number"] or heading["title"]
            link.string = f"({number})" if command == "eqref" else ("Section " + number if command == "autoref" else number)
            span.replace_with(link)
        elif label not in labels:
            warnings.append(f"Unresolved reference {label!r}; the source has no matching heading or equation label.")
    warnings = list(dict.fromkeys(warnings))
    if warnings:
        note = body.new_tag("aside", attrs={"class": "tex-conversion-warnings", "role": "note"})
        title = body.new_tag("p")
        title.string = "LaTeX conversion notes"
        note.append(title)
        entries = body.new_tag("ul")
        for warning in warnings:
            entry = body.new_tag("li")
            entry.string = warning
            entries.append(entry)
        note.append(entries)
        body.insert(0, note)
    download = body.new_tag("p", attrs={"class": "tex-source-download"})
    link = body.new_tag("a", href=base_url + "/" + quote(source.name, safe="-._~"), attrs={"download": ""})
    link.string = "Download original LaTeX source"
    download.append(link)
    body.append(download)
    copies[source] = asset_dir / source.name
    for original, destination in copies.items():
        if not destination.resolve().is_relative_to(asset_dir):
            raise ValueError(f"Asset destination escapes asset_dir: {destination}")
    for original, destination in copies.items():
        if original != destination.resolve():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
    (asset_dir / "source-images.json").write_text(json.dumps(image_manifest, ensure_ascii=False), encoding="utf-8")
    return {"body": str(body), "toc": toc, "headings": headings,
            "equation_count": len(body.select("span.math.display")),
            "image_count": len(images), "warnings": warnings, "source_name": source.name}