"""Public-report preservation/privacy contracts; all mutation outputs are temporary.

Run with the selected interpreter: python -B -m unittest site_content.tests.test_work_report -v
Private-field oracles read values at runtime, never hardcode or print them.
"""

from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
from html import unescape
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote
import zipfile

from bs4 import BeautifulSoup

from site_content.latex import _pandoc, convert_document
from site_content.publishing import source_zip
from site_content.work_report import (
    _reader_floats, assemble_public_report, generate_public_report, main,
    prepare_report, report_result,
)


ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "WKRPT400"
PUBLIC = ROOT / "notebook_sources/work-report"
SOURCE = PUBLIC / "work_term_report.tex"
MANIFEST = PUBLIC / "manifest.json"
LABEL = re.compile(r"\\label\{([^{}]+)\}")
REF = re.compile(r"\\(Cref|cref|ref|eqref|autoref)\{([^{}]+)\}")
MATH = re.compile(r"\\begin\{(equation|multline\*|math)\}(.*?)\\end\{\1\}", re.S)
IMAGE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^{}]+)\}")


def uncomment(text):
    return re.sub(r"\\(?:[A-Za-z@]+|[^\r\n])|%[^\r\n]*",
                  lambda match: "" if match[0].startswith("%") else match[0], text)


def body(text):
    return uncomment(text).split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0]


def fingerprints(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob("*")) if path.is_file()}


def private_values(text):
    """Test-owned metadata oracle, including the literal recipient postal code."""
    fields = (
        "studentnumber", "userid", "employerstreetaddress", "employerlocation",
        "authorstreetaddress", "authorlocation", "authorpostalcode",
    )
    preamble = uncomment(text).split(r"\begin{document}", 1)[0]
    values = [re.search(r"\\" + field + r"\s*\{([^{}]+)\}", preamble)[1] for field in fields]
    values += re.findall(r"\b[A-Z]\d[A-Z][ -]?\d[A-Z]\d\b", text, re.I)
    values += re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return {private_comparable(value) for value in values if value.strip()}


def private_comparable(text):
    text = unescape(unquote(text)).replace(r"\\", " ")
    text = re.sub(r"\\([_&%#$])", r"\1", text)
    return " ".join(text.casefold().split())


def glossary_entries():
    text = uncomment((ORIGINAL / "gls.tex").read_text(encoding="utf-8-sig"))
    return re.findall(r"\\newglossaryentry\{([^{}]+)\}\{name=\{([^{}]+)\},\s*description=\{([^{}]+)\}\}", text)


def comparable_content(text):
    """Only the enumerated adaptations; do not strip arbitrary prose/commands."""
    text = uncomment(text)
    names = {key: name for key, name, _ in glossary_entries()}
    text = re.sub(r"\\gls\{([^{}]+)\}", lambda m: names[m[1]], text)
    text = LABEL.sub("", text)
    text = re.sub(r"\\hypertarget\{wr-appendix-[a-h]\}\{\}", "", text)
    text = re.sub(r"\\section\*\{Appendix [A-H]: ([^{}]+)\}", lambda m: r"\section{" + m[1] + "}", text)
    text = text.replace(r"\summary", r"\section*{Summary}")
    text = re.sub(r"\\(?:listoffigures|listoftables|body)\b", "", text)
    text = text.replace(r"\begin{tabular}{l r c r l S[table-format=5.4]}", r"\begin{tabular}{l r r r}")

    def reference(match):
        command, label = match.groups()
        if command in ("Cref", "cref") and label.startswith(("fig:", "tab:", "eq:")):
            return {"fig": "Figure", "tab": "Table", "eq": "Equation"}[label.split(":")[0]] + "~REFERENCE"
        return "REFERENCE"

    text = REF.sub(reference, text)
    text = re.sub(r"\\hyperlink\{wr-appendix-[a-h]\}\{Appendix [A-H]\}", "REFERENCE", text)
    text = re.sub(r"\\textit\{\[(?:unresolved|ambiguous) historical reference: [^{}]+\]\}", "REFERENCE", text)
    text = MATH.sub(lambda m: (r"\begin{math}" + m[2].replace(r"\\", "") + r"\end{math}") if m[1] == "math" else m[0], text)
    return " ".join(text.split())


def math_payloads(text):
    return [(m[1], LABEL.sub("", m[2]).replace(r"\\", "") if m[1] == "math" else LABEL.sub("", m[2]))
            for m in MATH.finditer(body(text))]


def assert_private_absent(test, texts, secrets):
    # assertNotIn(secret, text) would echo both the secret and document on failure.
    for text in texts:
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")
        found = any(secret in private_comparable(text) for secret in secrets)
        test.assertFalse(found, "Administrative content leaked; values deliberately withheld")


class PublicSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ORIGINAL / "main.tex").read_text(encoding="utf-8-sig")
        cls.public = SOURCE.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_actual_source_inventory_and_manifest_counts(self):
        text = uncomment(self.original)
        environments = Counter(re.findall(r"\\begin\{([^{}]+)\}", text))
        self.assertEqual(len(text.splitlines()), 1132)
        self.assertEqual({key: environments[key] for key in ("equation", "multline*", "math", "figure", "table")},
                         {"equation": 94, "multline*": 2, "math": 179, "figure": 7, "table": 1})
        self.assertEqual(len(glossary_entries()), 9)
        self.assertEqual(self.manifest["counts"], {
            "sourceLines": 1132, "activeLines": 1132, "numberedEquations": 94, "unnumberedDisplays": 2,
            "displayMath": 96, "inlineMath": 179, "figures": 7, "tables": 1,
            "glossaryDefinitions": 9, "appendices": 8, "manualReferences": 11, "inlineLayoutBreaksRemoved": 1,
        })
        self.assertEqual(self.manifest["duplicateOriginalLabels"], {"eq:10": 2, "eq:29": 3, "eq:61": 2, "eq:66": 2})

    def test_checked_in_edition_is_deterministically_reproducible_and_pure(self):
        before_original = fingerprints(ORIGINAL)
        before_public = fingerprints(PUBLIC)
        shared = [ROOT / "site_content" / name for name in ("latex.py", "publishing.py", "career.py")]
        before_shared = {path: path.read_bytes() for path in shared}
        for _ in range(2):
            text, manifest = assemble_public_report(ROOT)
            self.assertEqual(text.encode("utf-8"), SOURCE.read_bytes())
            self.assertEqual(manifest, self.manifest)
            self.assertEqual(manifest["outputSha256"], sha256(text.encode("utf-8")).hexdigest())
        self.assertEqual(before_original, fingerprints(ORIGINAL))
        self.assertEqual(before_public, fingerprints(PUBLIC))
        self.assertTrue(all(path.read_bytes() == data for path, data in before_shared.items()), "Shared code was modified")

    def test_every_letter_paragraph_and_acknowledgment_survives(self):
        original_letter = body(self.original).split(r"\letterofsubmittal", 1)[1].split(r"\contributions", 1)[0]
        original_letter = original_letter[original_letter.index("This report, entitled"):].split("Sincerely,", 1)[0]
        public_letter = body(self.public).split(r"\section*{Letter of submittal}", 1)[1].split(r"\section*{Contributions}", 1)[0]
        public_letter = public_letter[public_letter.index("This report, entitled"):].split("Sincerely,", 1)[0]
        term = re.search(r"\\term\{([^{}]+)\}", self.original)[1]
        expected = comparable_content(original_letter.replace(r"\printterm", term))
        self.assertEqual(comparable_content(public_letter), expected)
        self.assertEqual(len([paragraph for paragraph in original_letter.split("\n\n") if paragraph.strip()]), 3)
        for name in ("Professor Roy", "Tapas Sahoo", "Xichen Lou"):
            self.assertIn(name, public_letter)
        self.assertIn("received no further help other than what is mentioned above", public_letter)
        self.assertIn("not been previously submitted for academic credit", public_letter)

    def test_all_contributions_summary_body_paragraphs_tables_and_captions_survive(self):
        original = body(self.original).split(r"\contributions", 1)[1].split(r"\printglossaries", 1)[0]
        public = body(self.public).split(r"\section*{Contributions}", 1)[1].split(r"\section*{Glossary}", 1)[0]
        self.assertEqual(comparable_content(public), comparable_content(original),
                         "Scientific prose/structure changed beyond the documented transformations")

    def test_all_eight_appendices_survive_in_order_without_numeric_misnumbering(self):
        original = body(self.original).split(r"\appendix", 1)[1]
        public = body(self.public).split(r"\hypertarget{wr-appendix-a}{}", 1)[1]
        self.assertEqual(comparable_content(public), comparable_content(original))
        titles = re.findall(r"\\section\{([^{}]+)\}", original)
        self.assertEqual(len(titles), 8)
        self.assertEqual(re.findall(r"\\section\*\{Appendix ([A-H]): ([^{}]+)\}", public),
                         list(zip("ABCDEFGH", titles)))
        self.assertNotIn(r"\appendix", body(self.public))
        for entry in self.manifest["appendices"]:
            self.assertIn(r"\hypertarget{" + entry["anchor"] + "}{}", self.public)
            self.assertIn(r"\label{" + entry["label"] + "}", self.public)

    def test_all_275_math_payloads_survive_in_order_with_only_documented_exceptions(self):
        original = math_payloads(self.original)
        self.assertEqual(Counter(kind for kind, _ in original), {"math": 179, "equation": 94, "multline*": 2})
        self.assertEqual(math_payloads(self.public), original)
        old_inline = [m[2] for m in MATH.finditer(body(self.original)) if m[1] == "math"]
        new_inline = [m[2] for m in MATH.finditer(body(self.public)) if m[1] == "math"]
        self.assertEqual(sum(old != new for old, new in zip(old_inline, new_inline, strict=True)), 1)

    def test_all_glossary_definitions_and_54_uses_survive(self):
        definitions = glossary_entries()
        self.assertEqual(len(re.findall(r"\\gls\{", uncomment(self.original))), 54)
        self.assertNotRegex(body(self.public), r"\\(?:gls|printglossaries|loadglsentries|glsaddall)\b")
        public_glossary = self.public.split(r"\begin{description}", 1)[1].split(r"\end{description}", 1)[0]
        self.assertEqual(re.findall(r"\\item\[([^]]+)\]\s+([^\n]+)", public_glossary),
                         [(name, description) for _, name, description in definitions])
        self.assertEqual(self.manifest["glossary"], [{"key": key, "name": name, "description": description}
                                                    for key, name, description in definitions])

    def test_eleven_manual_references_are_not_replaced_by_a_fake_bibliography(self):
        original = re.search(r"\\normalsize\{\s*(.*?)\n\}", body(self.original), re.S)[1]
        public = body(self.public).split(r"\section*{References}", 1)[1].split(r"\hypertarget{wr-appendix-a}{}", 1)[0]
        public = LABEL.sub("", public)
        public = re.sub(r"\\textsuperscript\{(\*+)\}", lambda m: "∗" * len(m[1]), public)
        # Exact six URL-only layout adaptations, not general prose normalization.
        original, count = re.subn(
            r"(https?://.*?)(\.\s*\[Accessed:)",
            lambda m: re.sub(r"\s+", "", m[1].replace(r"\\", "")).replace(r"\_", "_") + m[2],
            original, flags=re.S,
        )
        self.assertEqual(count, 6)
        self.assertEqual(public.count(r"\url{"), 6)
        public = re.sub(r"\\url\{([^{}]+)\}", lambda m: m[1], public)
        self.assertEqual(" ".join(public.split()), " ".join(original.split()))
        self.assertEqual(re.findall(r"(?m)^\[(\d+)\]", public), [str(n) for n in range(1, 12)])
        self.assertNotRegex(self.public, r"\\(?:addbibresource|bibliography|printbibliography|bibliographystyle)\b")

    def test_standalone_article_only_uses_needed_standard_packages_and_safe_metadata(self):
        self.assertTrue(self.public.startswith(r"\documentclass[11pt]{article}"))
        packages = re.findall(r"\\usepackage(?:\[[^]]*\])?\{([^{}]+)\}", self.public)
        self.assertEqual({name for group in packages for name in group.split(",")},
                         {"amsmath", "amssymb", "graphicx", "braket", "geometry", "titlesec", "hyperref", "xurl"})
        self.assertIn(r"\usepackage[margin=0.75in]{geometry}", self.public)
        self.assertIn(r"\setlength{\emergencystretch}{3em}", self.public)
        self.assertIn(r"\newcommand{\subsubsubsection}{\paragraph}", self.public)
        self.assertIn(r"\setcounter{tocdepth}{4}", self.public)
        self.assertIn(r"\date{Undated historical 3B report}", self.public)
        self.assertIsNone(self.manifest["edition"]["completionDate"])
        self.assertNotRegex(self.public, r"\\(?:today|input|include|loadglsentries|addbibresource|print[A-Za-z]+)\b")
        self.assertNotIn("ece.cls", self.public)
        self.assertIn("not public domain", self.public)
        self.assertIn("not a verified license", self.public)
        self.assertIn("not new verification or assurances", self.public)
        self.assertNotIn("2014-06-28", self.public)
        self.assertEqual(set(self.manifest["edition"]), {"title", "author", "program", "term", "dateStatus", "completionDate"})

    def test_public_source_manifest_and_guide_never_contain_administrative_values(self):
        secrets = private_values(self.original)
        self.assertGreaterEqual(len(secrets), 5)
        assert_private_absent(self, [path.read_bytes() for path in PUBLIC.iterdir() if path.is_file()], secrets)
        self.assertEqual(set(path.name for path in PUBLIC.iterdir()), {"work_term_report.tex", "manifest.json", "README.md"})
        self.assertFalse(any(self.manifest["privacy"][name] for name in
                             ("originalFolderDistributed", "templateClassDistributed", "originalCommentsDistributed")))

    def test_unique_labels_and_all_unambiguous_source_references_have_targets(self):
        public_labels = LABEL.findall(body(self.public))
        self.assertEqual(len(public_labels), len(set(public_labels)))
        old_counts = Counter(LABEL.findall(body(self.original)))
        audit = self.manifest["labelAudit"]
        for label, count in old_counts.items():
            self.assertEqual(audit["labels"][label], [f'wr-{label.replace(":", "-")}-{n}' for n in range(1, count + 1)])
        self.assertFalse({m[2] for m in REF.finditer(body(self.public))} - set(public_labels))
        self.assertEqual(audit["referencesNeedingReview"], [{"label": "eq:59", "reason": "unresolved", "candidates": []}])
        self.assertIn(r"\textit{[unresolved historical reference: eq:59]}", self.public)
        self.assertNotIn(r"\ref{eq:59}", self.public)
        self.assertEqual(len(REF.findall(body(self.original))), 23)
        self.assertEqual(len(REF.findall(body(self.public))), 12)  # 9 float + 3 equation refs; 10 appendix links, 1 note.
        self.assertEqual(len(re.findall(r"\\hyperlink\{wr-appendix-[a-h]\}", self.public)), 10)


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="work-report-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.assets = Path(cls.temporary.name) / "assets"
        cls.original_hashes = fingerprints(ORIGINAL)
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.original = (ORIGINAL / "main.tex").read_text(encoding="utf-8-sig")
        cls.result = report_result(ROOT, cls.assets, "../../assets/documents/work-report")
        cls.soup = BeautifulSoup(cls.result["body"], "html.parser")
        cls.manifest = cls.result["report_manifest"]

    @classmethod
    def tearDownClass(cls):
        if cls.original_hashes != fingerprints(ORIGINAL):
            raise AssertionError("The original report folder was modified")

    def test_real_reader_has_no_warnings_raw_label_artifacts_or_lost_blocks(self):
        self.assertEqual(self.result["warnings"], [])
        self.assertFalse(self.soup.select(".tex-unsupported, .tex-conversion-warnings"))
        self.assertEqual(self.result["equation_count"], 96)
        self.assertEqual(self.result["image_count"], 7)
        self.assertEqual(len(self.soup.select("figure")), 7)
        self.assertEqual(len(self.soup.select("table")), 1)
        self.assertEqual(len(self.result["headings"]), 37)
        self.assertFalse(self.soup.select("html, head, body, script, style"))
        self.assertIn("sanitized public", self.soup.select_one(".tex-source-download").get_text())

    def test_every_public_math_byte_reaches_html_and_equation_refs_resolve(self):
        expected_display = [m[0] for m in MATH.finditer(body(self.source)) if m[1] != "math"]
        expected_inline = [m[2] for m in MATH.finditer(body(self.source)) if m[1] == "math"]
        self.assertEqual([span.get_text()[2:-2] for span in self.soup.select("span.math.display")], expected_display)
        inline = [span.get_text()[2:-2] for span in self.soup.select("span.math.inline")]
        references = [payload for payload in inline if REF.fullmatch(payload)]
        self.assertEqual([payload for payload in inline if not REF.fullmatch(payload)], expected_inline)
        self.assertEqual(references, [r"\ref{wr-eq-15-1}", r"\ref{wr-eq-19-1}", r"\ref{wr-eq-62-1}"])
        labels = LABEL.findall("".join(expected_display))
        self.assertEqual(len(labels), len(set(labels)))
        self.assertTrue(all(REF.fullmatch(ref)[2] in labels for ref in references))
        self.assertFalse(self.soup.select("p span.math.display"))

    def test_complete_prose_reaches_html_not_just_selected_paragraphs(self):
        # Independent Pandoc prose oracle: remove display math, replace inline
        # math/references with tokens before parsing. Then compare ALL remaining
        # reader text, not phrases selected by the implementation.
        oracle = MATH.sub(lambda m: " WRMATH " if m[1] == "math" else "\n\n", body(self.source))
        oracle = REF.sub(" WRREF ", oracle)
        oracle = oracle.replace(r"\subsubsubsection", r"\paragraph")  # Documented fourth-level alias, not discarded headings.
        warnings = []
        expected = BeautifulSoup(_pandoc(oracle, "latex+raw_tex-latex_macros", "html5", warnings), "html.parser")
        self.assertEqual(warnings, [])
        actual = BeautifulSoup(self.result["body"], "html.parser")
        for node in actual.select(".tex-source-download, .work-report-caption-number"):
            node.decompose()
        for node in actual.select("span.math.display"):
            node.decompose()
        for node in actual.select("span.math.inline"):
            node.replace_with(" WRREF " if REF.fullmatch(node.get_text()[2:-2]) else " WRMATH ")
        for node in actual.select("a.tex-reference"):
            node.replace_with(" WRREF ")
        # Pandoc/DOM splitting introduces whitespace at formatting boundaries;
        # source preservation above separately checks word spacing and tokens.
        self.assertEqual(re.sub(r"\s+", "", actual.get_text()), re.sub(r"\s+", "", expected.get_text()))

    def test_all_seven_numbered_captions_and_nine_float_references_match_the_source(self):
        floats = self.manifest["floats"]
        self.assertEqual([entry["number"] for entry in floats], ["1-1", "2-2", "2-3", "4-1", "4-4", "4-5", "4-6", "4-7"])
        self.assertEqual([caption.get_text(" ", strip=True) for caption in self.soup.select("figcaption, caption")],
                         [entry["kind"].title() + " " + entry["number"] + ": " + entry["caption"] for entry in floats])
        lookup = {entry["label"]: entry for entry in floats}
        links = self.soup.select("a.tex-reference")
        self.assertEqual(len(links), 9)
        for link in links:
            target = unquote(link["href"])[1:]
            self.assertIn(target, lookup)
            self.assertIsNotNone(self.soup.find(id=target))
            self.assertEqual(link.get_text(), lookup[target]["number"])
        self.assertEqual(sum(entry["occurrences"] for entry in self.result["reader_repairs"]), 9)
        self.assertEqual(len(self.result["reader_repairs"]), 8)

    def test_all_ids_links_appendix_letters_and_fourth_level_toc_nesting(self):
        ids = [node["id"] for node in self.soup.select("[id]")]
        self.assertEqual(len(ids), len(set(ids)))
        toc = BeautifulSoup(self.result["toc"], "html.parser")
        for link in self.soup.select('a[href^="#"]') + toc.select("a"):
            self.assertIn(unquote(link["href"])[1:], ids)
        self.assertEqual(Counter(heading["level"] for heading in self.result["headings"]), {1: 20, 2: 9, 3: 6, 4: 2})
        fourth = toc.select("nav > ol > li > ol > li > ol > li > ol > li")
        self.assertEqual([li.get_text(" ", strip=True) for li in fourth], ["2.2.2.1 LJ Potential", "2.2.2.2 MBPol Potential"])
        appendices = [heading for heading in self.result["headings"] if heading["title"].startswith("Appendix ")]
        self.assertEqual([heading["title"][9] for heading in appendices], list("ABCDEFGH"))
        self.assertTrue(all(not heading["number"] for heading in appendices))
        for entry in self.manifest["appendices"]:
            self.assertIsNotNone(self.soup.find(id=entry["anchor"]))
            self.assertEqual(self.soup.find(id=entry["label"]).get_text(), "Appendix " + entry["letter"] + ": " + entry["title"])

    def test_four_unchanged_table_columns_and_all_twenty_four_cells(self):
        table = self.soup.select_one("table")
        self.assertEqual(len(table.select("tr")), 6)
        self.assertEqual(len(table.select("th, td")), 24)
        self.assertEqual([[cell.get_text() for cell in row.select("th, td")] for row in table.select("tr")], [
            ["Temperature", "Theoretical Value", "Etrans MMTK Value", "Error"],
            ["10.0 K", "15.0 K", "15.148 K", "0.020 K"],
            ["20.0 K", "30.0 K", "30.104 K", "0.043 K"],
            ["30.0 K", "45.0 K", "44.068 K", "0.063 K"],
            ["50.0 K", "75.0 K", "74.359 K", "0.106 K"],
            ["100.0 K", "150.0 K", "147.904", "0.214 K"],
        ])  # The missing original unit is NOT silently "corrected".

    def test_all_seven_source_images_are_byte_identical_and_manifest_paths_are_simple(self):
        images = IMAGE.findall(body(self.original))
        self.assertEqual(len(images), 7)
        expected = [{"archive": name, "asset": name} for name in images]
        self.assertEqual(json.loads((self.assets / "source-images.json").read_text(encoding="utf-8")), expected)
        self.assertEqual([entry["archive"] for entry in self.manifest["images"]], images)
        for name, node in zip(images, self.soup.select("img"), strict=True):
            self.assertEqual(Path(name).name, name)
            self.assertEqual((self.assets / name).read_bytes(), (ORIGINAL / name).read_bytes())
            self.assertEqual(node["src"], "../../assets/documents/work-report/" + name)
        self.assertEqual((self.assets / "work_term_report.tex").read_bytes(), SOURCE.read_bytes())

    def test_source_html_and_zip_exclude_private_metadata_original_source_and_class(self):
        source_zip(prepare_report(ROOT), self.assets)
        secrets = private_values(self.original)
        with zipfile.ZipFile(self.assets / "source-bundle.zip") as archive:
            names = archive.namelist()
            self.assertEqual(set(names), {"work_term_report.tex", *IMAGE.findall(body(self.original))})
            self.assertEqual(len(names), 8)
            contents = [archive.read(name) for name in names]
            self.assertEqual(archive.read("work_term_report.tex"), SOURCE.read_bytes())
            for name in IMAGE.findall(body(self.original)):
                self.assertEqual(archive.read(name), (ORIGINAL / name).read_bytes())
        assert_private_absent(self, contents + [self.result["body"], self.result["toc"], json.dumps(self.manifest)], secrets)
        self.assertFalse({"main.tex", "ece.cls", "gls.tex"} & set(names))

    def test_reader_and_asset_content_are_deterministic(self):
        other_assets = Path(self.temporary.name) / "second-assets"
        second = report_result(ROOT, other_assets, "../../assets/documents/work-report")
        self.assertEqual(second, self.result)
        for name in ["work_term_report.tex", "source-images.json", *IMAGE.findall(body(self.original))]:
            self.assertEqual((other_assets / name).read_bytes(), (self.assets / name).read_bytes())
        source_zip(SOURCE, self.assets)
        first_zip = (self.assets / "source-bundle.zip").read_bytes()
        source_zip(SOURCE, self.assets)
        self.assertEqual(first_zip, (self.assets / "source-bundle.zip").read_bytes())

    def test_unknown_warnings_and_raw_label_artifacts_are_never_silently_dropped(self):
        assets = Path(self.temporary.name) / "warning-fixture"
        direct = convert_document(SOURCE, ORIGINAL, assets, "../assets", source_root=ORIGINAL)
        self.assertEqual(len(direct["warnings"]), 8)
        unknown = r"Unsupported latex command retained visibly: \label{unrecognized}"
        direct["warnings"].append(unknown)
        direct["body"] += '<p>Keep this prose. <code class="tex-unsupported">\\label{unrecognized}</code></p>'
        adapted = _reader_floats(direct, self.manifest)
        self.assertEqual(adapted["warnings"], [unknown])
        self.assertIn("Keep this prose.", adapted["body"])
        self.assertIn(r"\label{unrecognized}", adapted["body"])

    def test_missing_float_anchor_or_changed_caption_fails_not_a_guessed_repair(self):
        for mutation in ("anchor", "caption"):
            with self.subTest(mutation=mutation):
                changed = deepcopy(self.manifest)
                changed["floats"][0]["label" if mutation == "anchor" else "caption"] = "not-present"
                with self.assertRaisesRegex(ValueError, "float anchor|caption"):
                    _reader_floats(self.result, changed)


class GenerationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="work-report-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ORIGINAL, self.root / "WKRPT400")
        self.main = self.root / "WKRPT400/main.tex"
        self.output = self.root / "notebook_sources/work-report"

    def test_generation_writes_exactly_two_public_files_and_leaves_all_original_hashes_unchanged(self):
        before = fingerprints(self.root)
        original_mtimes = {path.name: path.stat().st_mtime_ns for path in (self.root / "WKRPT400").iterdir()}
        source = generate_public_report(self.root)
        after = fingerprints(self.root)
        self.assertEqual(set(after) - set(before), {"notebook_sources/work-report/work_term_report.tex", "notebook_sources/work-report/manifest.json"})
        self.assertTrue(all(after[name] == digest for name, digest in before.items()), "An original input changed")
        self.assertEqual(original_mtimes, {path.name: path.stat().st_mtime_ns for path in (self.root / "WKRPT400").iterdir()})
        public_mtimes = {path.name: path.stat().st_mtime_ns for path in self.output.iterdir()}
        self.assertEqual(generate_public_report(self.root), source)
        self.assertEqual(fingerprints(self.root), after)
        self.assertEqual(public_mtimes, {path.name: path.stat().st_mtime_ns for path in self.output.iterdir()})
        self.assertEqual(source.read_bytes(), SOURCE.read_bytes())
        self.assertEqual((self.output / "manifest.json").read_bytes(), MANIFEST.read_bytes())

    def test_missing_prepared_output_and_normal_cli_never_regenerate(self):
        before = fingerprints(self.root)
        with self.assertRaisesRegex(FileNotFoundError, "--write"):
            prepare_report(self.root)
        with self.assertRaisesRegex(FileNotFoundError, "--write"):
            report_result(self.root, self.root / "assets", "../assets")
        with self.assertRaises(FileNotFoundError):
            main(["--root", str(self.root)])
        self.assertEqual(fingerprints(self.root), before)
        self.assertFalse(self.output.exists())

    def test_explicit_cli_and_read_only_validation_do_not_print_private_values(self):
        output = io.StringIO()
        with redirect_stdout(output):
            main(["--root", str(self.root), "--write"])
        before = fingerprints(self.root)
        with patch("site_content.work_report.generate_public_report", side_effect=AssertionError("Unexpected regeneration")):
            with redirect_stdout(output):
                main(["--root", str(self.root)])
            self.assertEqual(prepare_report(self.root), self.output / "work_term_report.tex")
        self.assertEqual(before, fingerprints(self.root))
        self.assertIn("96 display blocks", output.getvalue())
        assert_private_absent(self, [output.getvalue()], private_values(self.main.read_text(encoding="utf-8")))

    def test_module_entry_point_runs_with_the_selected_interpreter(self):
        completed = subprocess.run([sys.executable, "-B", "-m", "site_content.work_report", "--root", str(self.root), "--write"],
                                   cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, "Report CLI failed; private diagnostics are withheld")
        self.assertTrue((self.output / "work_term_report.tex").is_file())
        self.assertFalse((self.root / "assets").exists())
        assert_private_absent(self, [completed.stdout, completed.stderr], private_values(self.main.read_text(encoding="utf-8")))

    def test_changed_original_public_source_or_image_requires_review_without_overwriting(self):
        source = generate_public_report(self.root)
        main_bytes = self.main.read_bytes()
        self.main.write_bytes(main_bytes + b"\n% A changed historical input\n")
        before = fingerprints(self.root)
        with self.assertRaisesRegex(ValueError, "Original report changed"):
            prepare_report(self.root)
        self.assertEqual(fingerprints(self.root), before)
        self.main.write_bytes(main_bytes)
        source_bytes = source.read_bytes()
        source.write_bytes(source_bytes + b"\n% Public source changed\n")
        with self.assertRaisesRegex(ValueError, "source/manifest mismatch"):
            prepare_report(self.root)
        source.write_bytes(source_bytes)
        image = self.root / "WKRPT400" / IMAGE.findall(body(self.main.read_text(encoding="utf-8")))[0]
        image.write_bytes(image.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "image changed"):
            report_result(self.root, self.root / "assets", "../assets")
        self.assertFalse((self.root / "assets").exists())

    def test_reintroduced_private_value_is_refused_without_echo_or_asset_writes(self):
        text = self.main.read_text(encoding="utf-8")
        secret = re.search(r"\\studentnumber\{([^{}]+)\}", text)[1]
        self.main.write_text(text.replace(r"\section{Introduction}", r"\section{Introduction}" + "\n" + secret), encoding="utf-8")
        before = fingerprints(self.root)
        with self.assertRaises(ValueError) as caught:
            generate_public_report(self.root)
        self.assertEqual(before, fingerprints(self.root))
        self.assertFalse(self.output.exists())
        assert_private_absent(self, [str(caught.exception)], private_values(text))

    def test_tampered_public_source_and_matching_hash_still_cannot_publish_private_metadata(self):
        source = generate_public_report(self.root)
        original = self.main.read_text(encoding="utf-8")
        secret = re.search(r"\\userid\{([^{}]+)\}", original)[1]
        source.write_text(source.read_text(encoding="utf-8") + "\n% " + secret, encoding="utf-8")
        audit = self.output / "manifest.json"
        manifest = json.loads(audit.read_text(encoding="utf-8"))
        manifest["outputSha256"] = sha256(source.read_bytes()).hexdigest()
        audit.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ValueError) as caught:
            report_result(self.root, self.root / "assets", "../assets")
        self.assertFalse((self.root / "assets").exists())
        assert_private_absent(self, [str(caught.exception)], private_values(original))

    def test_duplicate_reference_becomes_an_explicit_ambiguity_note_not_a_guess(self):
        text = self.main.read_text(encoding="utf-8")
        self.main.write_text(text.replace(r"\section{Introduction}", r"\section{Introduction} See \ref{eq:10}."), encoding="utf-8")
        source, manifest = assemble_public_report(self.root)
        self.assertIn(r"\textit{[ambiguous historical reference: eq:10]}", source)
        self.assertFalse(any(r"\ref{" + label + "}" in source for label in manifest["labelAudit"]["labels"]["eq:10"]))
        note = next(note for note in manifest["labelAudit"]["referencesNeedingReview"] if note["label"] == "eq:10")
        self.assertEqual(note["reason"], "ambiguous")
        self.assertEqual(note["candidates"], ["wr-eq-10-1", "wr-eq-10-2"])

    def test_unknown_layout_missing_images_and_unsafe_destinations_fail_before_writes(self):
        text = self.main.read_text(encoding="utf-8")
        self.main.write_text(text.replace(r"\printstudentnumber", r"\printunknownidentifier"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "signature layout"):
            generate_public_report(self.root)
        self.assertFalse(self.output.exists())
        self.main.write_text(text, encoding="utf-8")
        image = self.root / "WKRPT400" / IMAGE.findall(body(text))[0]
        original_image = image.read_bytes()
        image.unlink()
        with self.assertRaises(FileNotFoundError):
            generate_public_report(self.root)
        self.assertFalse(self.output.exists())
        image.write_bytes(original_image)
        generate_public_report(self.root)
        before = fingerprints(self.root)
        for assets in (self.root, self.root / "WKRPT400", self.output, self.output / "assets"):
            with self.subTest(destination=assets.name):
                with self.assertRaisesRegex(ValueError, "separate"):
                    report_result(self.root, assets, "../assets")
        self.assertEqual(fingerprints(self.root), before)

    def test_parent_archive_honors_manifest_instead_of_collecting_extra_files(self):
        source = generate_public_report(self.root)
        assets = self.root / "assets"
        report_result(self.root, assets, "../assets")
        (assets / "unrelated.png").write_bytes(b"not a report image")
        (assets / "unrelated.txt").write_text("Do not include unrelated assets", encoding="utf-8")
        source_zip(source, assets)
        with zipfile.ZipFile(assets / "source-bundle.zip") as archive:
            self.assertEqual(set(archive.namelist()), {source.name, *IMAGE.findall(body(source.read_text(encoding="utf-8")))})
            self.assertNotIn("unrelated.png", archive.namelist())
            self.assertNotIn("unrelated.txt", archive.namelist())


if __name__ == "__main__":
    unittest.main()