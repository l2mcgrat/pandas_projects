"""Explicit, isolated Tectonic compilation; publishing only reads verified caches.

Run ``python -B -m site_content.pdf --engine /path/to/tectonic``. No compiler is
needed to import this module or copy a verified PDF. Nothing compiles on import.
Only the four public articles are supported, never a raw report or custom class.
The manifest is a content-integrity record, not a cryptographic signature against
an attacker who can replace both the cache and its manifest. Pin the compiler
and its Tectonic resource cache for cross-machine byte reproducibility.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    "work-term-report": "notebook_sources/work-report/work_term_report.tex",
    "basketball-rules": "notebook_sources/sports/basketball_rules.tex",
    "creator-pitch": "notebook_sources/sports/creator_pitch.tex",
    "mental-map-guide": "notebook_sources/guides/mental_map_guide.tex",
}
# Root-relative folder each article's images must come from.
IMAGE_DIRS = {"work-term-report": "", "mental-map-guide": "tex_images/guides/"}
CACHE = "reports/site_content/pdfs"
EPOCH = "946684800"  # Fixed 2000-01-01 UTC; not a document completion date.
FLAGS = ("--untrusted", "--keep-logs", "--keep-intermediates", "--outdir", "output")
IMAGE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^{}]+)\}")
TOKEN = re.compile(r"\\(?:[A-Za-z@]+|[^\r\n])|%[^\r\n]*")
# Deliberately narrow: public articles, not an arbitrary TeX execution service.
# No input/include, file I/O, special, dynamic command construction, catcodes,
# package loading aliases, embedded code, fonts by filesystem path, or shell I/O.
COMMANDS = set("""
@ifstar Big Bigg Delta Omega Phi Psi Theta Tilde Xi addcontentsline arabic author
baselineskip begin beta bfseries big bigg bra caption cdot centering chi circ
clearpage cos date delta documentclass emergencystretch end epsilon equiv exp frac gg hat hbar
hline hspace hyperlink hypertarget includegraphics infty int item kappa ket
label langle leq let lim linewidth ln makeatletter makeatother maketitle mathcal
mu multicolumn nabla neq newcommand nolinkurl normalfont normalsize omega paragraph partial
phi pi prod providecommand rangle ref renewcommand rho rightarrow section
setcounter setlength sigma simeq sin sqrt subsection subsubsection subsubsubsection sum
tableofcontents tau textasciitilde textbackslash textbf textit textsuperscript texttt textwidth thefigure
theparagraph therefore thesection theta thetable tilde times title titleformat
titlespacing url usepackage vec vspace workreportsection workreportstarsection
""".split())
PACKAGES = {"amsmath", "amssymb", "graphicx", "braket", "geometry", "titlesec", "hyperref", "enumitem", "xurl"}


def _failure(key: str, reason: str) -> ValueError:
    # Never interpolate exception text, TeX/log contents, or filesystem paths.
    return ValueError(f"{key}: {reason}. Review inputs and recompile with "
                      f"python -B -m site_content.pdf --engine <tectonic> --document {key}.")


def _key(key: str) -> None:
    if key not in DOCUMENTS:
        raise ValueError("Unknown PDF document key; choose one of: " + ", ".join(DOCUMENTS) + ".")


def _safe_path(path: Path) -> Path:
    """Reject links/junctions in every component, not only an escaping leaf."""
    path = Path(os.path.abspath(path))
    for part in (*reversed(path.parents), path):
        if part.is_symlink() or part.is_junction():
            raise ValueError("Linked paths are not safe PDF inputs or destinations")
        if part.exists() and part.is_file() and part.stat().st_nlink != 1:
            raise ValueError("Hard-linked files are not safe PDF inputs or destinations")
    return path


def _inside(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if (not relative or "\\" in relative or ":" in relative or rel.is_absolute()
            or any(p in ("", ".", "..") for p in relative.split("/"))):
        raise ValueError("Unsafe relative PDF input path")
    path = _safe_path(root.joinpath(*rel.parts))
    if not path.is_relative_to(root):
        raise ValueError("PDF input escapes its allowed directory")
    return path


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _json(data: bytes) -> object:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate manifest field")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def _source_images(data: bytes, key: str) -> list[str]:
    text = data.decode("utf-8-sig")
    active = TOKEN.sub(lambda m: "" if m[0].startswith("%") else m[0], text)
    if "^^" in active or any(ord(c) < 32 and c not in "\t\r\n" for c in active):
        raise ValueError("Encoded or control-character TeX is not supported")
    for token in TOKEN.finditer(active):
        command = token[0][1:]
        if command and (command[0].isalpha() or command.startswith("@")):
            if command not in COMMANDS:
                raise ValueError("Unapproved TeX command; review the standalone source")
            if key != "work-term-report" and command in {
                "let", "newcommand", "renewcommand", "providecommand", "makeatletter", "makeatother",
                "@ifstar", "workreportsection", "workreportstarsection",
            }:
                raise ValueError("Sports articles cannot define or alias commands")
    if re.findall(r"\\documentclass(?:\[[^]]*\])?\{([^{}]+)\}", active) != ["article"]:
        raise ValueError("Only a standalone standard article may be compiled")
    packages = re.findall(r"\\usepackage(?:\[[^]]*\])?\{([^{}]+)\}", active)
    if active.count(r"\usepackage") != len(packages) or active.count(r"\documentclass") != 1:
        raise ValueError("Class/package arguments must be literal")
    for group in packages:
        if not set(group.split(",")) <= PACKAGES:
            raise ValueError("Unapproved TeX package")
    if active.count(r"\begin{document}") != 1 or active.count(r"\end{document}") != 1:
        raise ValueError("Expected one complete public article")
    images = IMAGE.findall(active)
    if active.count(r"\includegraphics") != len(images) or len(images) != len(set(images)):
        raise ValueError("Image references must be explicit and unique")
    prefix = IMAGE_DIRS.get(key, "tex_images/sports/")
    if any(not re.fullmatch(re.escape(prefix) + r"[A-Za-z0-9_-]+\.png", name) for name in images):
        raise ValueError("Only allowlisted PNG paths may be staged")
    return images


def _stage(root: Path, key: str, stage: Path) -> dict:
    """Validate through the existing converters, then stage exact archive paths."""
    from .latex import convert_document
    from .work_report import assemble_public_report, prepare_report, report_result

    source = _inside(root, DOCUMENTS[key])
    if key == "work-term-report":
        # Missing original inputs MUST still fail; never bypass privacy validation.
        for name in ("WKRPT400/main.tex", "WKRPT400/gls.tex", "notebook_sources/work-report/manifest.json"):
            _inside(root, name)
        prepare_report(root)
    data = source.read_bytes()
    if key == "work-term-report":
        # Only the producer's reviewed macro definitions are trusted, never an
        # arbitrary edited preamble paired with a recalculated source hash.
        expected_source, expected_manifest = assemble_public_report(root)
        public_manifest = _json((source.parent / "manifest.json").read_bytes())
        if expected_source.encode("utf-8") != data or public_manifest != expected_manifest:
            raise ValueError("Public report differs from the reviewed sanitized edition")
    images = _source_images(data, key)
    originals = []
    for name in images:
        relative = "WKRPT400/" + name if key == "work-term-report" else name
        path = _inside(root, relative)
        content = path.read_bytes()
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Referenced image is not a PNG")
        originals.append((name, relative, content))
    with tempfile.TemporaryDirectory(prefix="public-pdf-assets-") as temporary:
        assets = Path(temporary)
        if key == "work-term-report":
            report_result(root, assets, "assets")
        else:
            image_dir = IMAGE_DIRS.get(key, "tex_images/sports/").rstrip("/")
            convert_document(source, root / image_dir, assets, "assets", source_root=root)
        manifest = _json((assets / "source-images.json").read_bytes())
        expected = [{"archive": name, "asset": PurePosixPath(name).name} for name in images]
        if manifest != expected or (assets / source.name).read_bytes() != data:
            raise ValueError("Converter source/image inventory mismatch")
        for name, _, content in originals:
            if _inside(assets, PurePosixPath(name).name).read_bytes() != content:
                raise ValueError("Converter image fingerprint mismatch")
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "document.tex").write_bytes(data)
    for name, _, content in originals:
        destination = _inside(stage, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return {"source": {"path": DOCUMENTS[key], "sha256": _digest(data)},
            "images": [{"path": relative, "archive": name, "sha256": _digest(content)}
                       for name, relative, content in originals]}


def _valid_pdf(data: bytes) -> None:
    # Structural envelope checks without imposing a PDF-library build dependency.
    # Full page/text/render inspection is separate from this integrity gate.
    if (not re.match(rb"%PDF-1\.[0-9][\r\n]", data) or len(data) < 100
            or not re.search(rb"startxref\s+\d+\s+%%EOF\s*\Z", data)
            or not re.search(rb"\d+\s+\d+\s+obj\b", data)):
        raise ValueError("Compiler output is not a complete PDF")
    offset = int(re.findall(rb"startxref\s+(\d+)\s+%%EOF", data)[-1])
    if not 0 < offset < len(data) or not re.match(rb"(?:xref\b|\d+\s+\d+\s+obj\b)", data[offset:]):
        raise ValueError("PDF cross-reference offset is invalid")


def _atomic(path: Path, data: bytes) -> None:
    _safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".pdf-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        _safe_path(path)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def copy_verified_pdf(root: Path, key: str, assets: Path) -> str | None:
    """Copy an exact current cache to assets/document.pdf; never invoke TeX.

    None means both cache files are absent. Any partial/stale/unsafe cache raises
    an actionable ValueError; callers must not turn that error into a stale link.
    """
    _key(key)
    try:
        root = _safe_path(root)
        pdf = _inside(root, f"{CACHE}/{key}.pdf")
        manifest_path = _inside(root, f"{CACHE}/{key}.json")
        if not pdf.exists() and not manifest_path.exists():
            return None
        if not pdf.is_file() or not manifest_path.is_file():
            raise ValueError("Incomplete PDF cache")
        manifest = _json(manifest_path.read_bytes())
        if not isinstance(manifest, dict) or set(manifest) != {"schemaVersion", "key", "compiler", "inputs", "pdfSha256"}:
            raise ValueError("Unexpected PDF manifest schema")
        compiler = manifest["compiler"]
        if (type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1 or manifest["key"] != key
                or not isinstance(compiler, dict) or set(compiler) != {"name", "version", "flags", "sourceDateEpoch"}
                or compiler["name"] != "tectonic" or compiler["flags"] != list(FLAGS)
                or compiler["sourceDateEpoch"] != EPOCH
                or not isinstance(compiler["version"], str)
                or not re.fullmatch(r"Tectonic \d+\.\d+\.\d+", compiler["version"])):
            raise ValueError("Invalid PDF compiler provenance")
        data = pdf.read_bytes()
        _valid_pdf(data)
        if _digest(data) != manifest["pdfSha256"]:
            raise ValueError("PDF checksum mismatch")
        with tempfile.TemporaryDirectory(prefix="verify-public-pdf-") as temporary:
            inputs = _stage(root, key, Path(temporary) / "stage")
        if inputs != manifest["inputs"]:
            raise ValueError("Stale PDF source/image inputs")
        destination = _safe_path(assets)
        for protected in ("WKRPT400", "LiamMcGrath_Resume", "notebook_sources", "tex_images", CACHE):
            if destination.is_relative_to(_inside(root, protected)):
                raise ValueError("PDF assets overlap a protected source/cache directory")
        _atomic(destination / "document.pdf", data)
        return "document.pdf"
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        raise _failure(key, "cached PDF is incomplete, stale, corrupt, unsafe, or its source validation failed") from None


def _diagnostics(log: str) -> dict:
    """Value-free diagnostics: never expose TeX source, paths, or log excerpts."""
    return {
        "undefinedCommands": len(re.findall(r"Undefined control sequence", log)),
        "undefinedReferences": len(re.findall(r"(?:Reference .* undefined|There were undefined references)", log)),
        "missingGlyphs": len(re.findall(r"Missing character:", log)),
        "overfullBoxesPt": [float(n) for n in re.findall(r"Overfull \\[hv]box \(([\d.]+)pt too (?:wide|high)\)", log)],
        "overfullSourceLines": [list(map(int, m)) for m in re.findall(
            r"Overfull [^\n]*?at lines (\d+)--(\d+)", log)],
        "underfullBoxes": len(re.findall(r"Underfull \\[hv]box", log)),
        "latexWarnings": len(re.findall(r"LaTeX Warning:", log)),
        "packageWarnings": len(re.findall(r"Package [\w-]+ Warning:", log)),
        "errorLines": sorted({int(n) for n in re.findall(r"(?:^l\.|document\.tex:)(\d+)", log, re.M)}),
    }


def compile_document(root: Path, key: str, engine: Path) -> dict:
    """Explicit compile; failures before replacement leave existing cache intact.

    A filesystem failure between the two atomic replacements can leave a partial
    pair; copy_verified_pdf always refuses that pair instead of linking it.
    """
    _key(key)
    try:
        root = _safe_path(root)
        pdf = _inside(root, f"{CACHE}/{key}.pdf")
        audit = _inside(root, f"{CACHE}/{key}.json")
        engine = Path(engine).resolve(strict=True)
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("TEX", "BIB", "BST"))}
        env.update(SOURCE_DATE_EPOCH=EPOCH, FORCE_SOURCE_DATE="1", TZ="UTC", TECTONIC_UNTRUSTED_MODE="1")
        with tempfile.TemporaryDirectory(prefix="compile-public-pdf-") as temporary:
            stage = Path(temporary) / "stage"
            inputs = _stage(root, key, stage)
            version_result = subprocess.run([str(engine), "--version"], cwd=stage, env=env,
                                            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
            version = version_result.stdout.strip()
            if version_result.returncode or not re.fullmatch(r"Tectonic \d+\.\d+\.\d+", version):
                raise ValueError("Expected a version-identified Tectonic engine")
            (stage / "output").mkdir()
            result = subprocess.run([str(engine), *FLAGS, "document.tex"], cwd=stage, env=env,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
            log_path = stage / "output/document.log"
            # Final-pass log avoids counting resolved first-pass references twice.
            log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else result.stdout + result.stderr
            diagnostics = _diagnostics(log)
            print(key + " diagnostics: " + json.dumps(diagnostics, sort_keys=True))
            if result.returncode:
                raise ValueError("Tectonic failed; use the sanitized diagnostic line numbers")
            if any(diagnostics[field] for field in ("undefinedCommands", "undefinedReferences", "missingGlyphs")):
                raise ValueError("Unresolved TeX commands/references or missing glyphs")
            data = _inside(stage, "output/document.pdf").read_bytes()
            _valid_pdf(data)
            # Revalidate after compilation, so concurrent edits cannot certify old inputs.
            if inputs != _stage(root, key, Path(temporary) / "recheck"):
                raise ValueError("Inputs changed during compilation")
            manifest = {"schemaVersion": 1, "key": key,
                        "compiler": {"name": "tectonic", "version": version, "flags": list(FLAGS), "sourceDateEpoch": EPOCH},
                        "inputs": inputs, "pdfSha256": _digest(data)}
            _atomic(pdf, data)
            # Publishing between these two atomic replaces fails closed on mismatch.
            _atomic(audit, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            return {"key": key, "bytes": len(data), "sha256": _digest(data), "diagnostics": diagnostics}
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        raise _failure(key, "compilation or safe input/output validation failed; no new verified cache was certified") from None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True, help="Explicit path to an installed official Tectonic binary")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--document", choices=tuple(DOCUMENTS))
    args = parser.parse_args(argv)
    failed = False
    for key in (args.document,) if args.document else DOCUMENTS:
        try:
            result = compile_document(args.root, key, args.engine)
            print(f"{key}: compiled and verified, {result['bytes']} bytes, SHA256 {result['sha256']}")
        except ValueError as error:
            failed = True
            print(str(error))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()