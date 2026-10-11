"""Lossless notebook-assembly contracts; no regeneration or production writes.

Run: python -B -m unittest site_content.tests.test_notebook -v
Expected imports are derived independently from the immutable source archive,
not from import_external/normalize_labels. All mutation fixtures are temporary.
"""

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from bs4 import BeautifulSoup

from site_content.latex import _prepare, convert_document
from site_content.notebook import active_text, assemble, import_external, normalize_labels


ROOT = Path(__file__).resolve().parents[2]
ORIGINALS = ROOT / "notebook_sources/originals"
IMAGE_PREFIX = "tex_images/mental_map/"
LABEL = re.compile(r"\\label\{([^{}]+)\}")
REFERENCE = re.compile(r"\\(ref|eqref|autoref)\{([^{}]+)\}")
IMAGE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")
TIKZ = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", re.S)
HEADING = re.compile(r"\\((?:sub)*section)\{([^{}]+)\}")


def uncomment(text):
    """Test-owned comment lexer, independent of the assembler's active_text."""
    return re.sub(r"\\(?:[A-Za-z@]+|[^\r\n])|%[^\r\n]*",
                  lambda match: "" if match[0].startswith("%") else match[0], text)


def document_body(text):
    return text.split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0]


def chapter_bodies(text):
    matches = list(re.finditer(r"(?m)^\\section\{([^{}]+)\}", document_body(text)))
    body = document_body(text)
    return {m[1]: body[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(body)]
            for i, m in enumerate(matches)}


def fingerprints(directory):
    return {p.relative_to(directory).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file()}


def comparable_import(text):
    """Only explicit editorial exceptions; never discard arbitrary prose/math.

    Reference correctness and math bytes have separate, stricter assertions.
    The three replacement figures are the only permitted removed environments.
    """
    text = TIKZ.sub("", uncomment(text))
    replacement = r"\\begin\{figure\}\[htbp\]\\centering\s*\\includegraphics\[width=0\.85\\linewidth\]\{tex_images/mental_map/external/derivative-(?:line|square|quartic)\.png\}.*?\\end\{figure\}"
    text = re.sub(replacement, "", text, flags=re.S)
    text = LABEL.sub("", text)
    text = REFERENCE.sub("REFERENCE", text)
    text = re.sub(r"\\textit\{\[(?:ambiguous|unresolved) historical reference: [^{}]*\]\}", "REFERENCE", text)
    text = text.replace(IMAGE_PREFIX + "external/", "").replace(IMAGE_PREFIX, "")
    text = text.replace(r"0 & 0 & 1 \i", r"0 & 0 & 1 \\")
    text = text.replace(r'\vspace{0.025cm}', '').replace(r'\veq{q}', r'\vec{q}')
    text = text.replace(r"\say{string}", "``string''")
    text = text.replace("\\cancelto{1}\n", "")  # Orphan command, not a math payload.
    text = re.sub(r"\\(?:newpage|clearpage|maketitle|tableofcontents)\b", "", text)
    return " ".join(text.split())


def math_payloads(text):
    """Slot comparison excludes only labels and the single invalid matrix row."""
    _, slots = _prepare(TIKZ.sub("", uncomment(text)), [])
    return Counter((slot.display, LABEL.sub("", slot.payload).replace(r"0 & 0 & 1 \i", r"0 & 0 & 1 \\").replace(r'\vspace{0.025cm}', '').replace(r'\veq{q}', r'\vec{q}'))
                   for slot in slots.values())


class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "notebook_sources/merged/mental_map.merged.tex").read_bytes()
        cls.text = cls.original.decode("utf-8")
        cls.manifest = json.loads((ROOT / "notebook_sources/merge-manifest.json").read_text(encoding="utf-8"))
        cls.old = (ORIGINALS / "mental_map.pre-merge.tex").read_text(encoding="utf-8-sig")
        cls.external = (ORIGINALS / "External_Brain/main.tex").read_text(encoding="utf-8-sig")
        cls.rotor = (ORIGINALS / "External_Brain/Perturbed Linear Rotor.tex").read_text(encoding="utf-8-sig")

    def test_assembly_reproduces_canonical_bytes_and_complete_manifest_without_writes(self):
        before = {name: fingerprints(ROOT / name) for name in ("notebook_sources", "External_Brain", "tex_images/mental_map")}
        source_bytes = {name: (ROOT / name).read_bytes() for name in ("mental_map.tex", "Quantum_Mechanics.tex")}
        for _ in range(2):
            text, manifest = assemble(ROOT)
            self.assertEqual(text.encode("utf-8"), self.original, "Canonical source is stale; explicit regeneration is required")
            self.assertEqual(manifest, self.manifest, "Merge manifest is stale")
            self.assertEqual(manifest["outputSha256"], sha256(self.original).hexdigest())
        self.assertEqual(before, {name: fingerprints(ROOT / name) for name in before})
        self.assertEqual(source_bytes, {name: (ROOT / name).read_bytes() for name in source_bytes})

    def test_every_original_fingerprint_and_external_asset_is_byte_identical(self):
        expected = {"notebook_sources/originals/" + name: digest for name, digest in fingerprints(ORIGINALS).items()}
        self.assertEqual(self.manifest["sources"], expected)
        self.assertEqual(expected["notebook_sources/originals/mental_map.pre-merge.tex"],
                         "c3b0a62bbc147292006c282d4c6394b80f3d403f3cf9b0bdb2008d56d6772ec3")
        external = ORIGINALS / "External_Brain"
        self.assertEqual(fingerprints(external), fingerprints(ROOT / "External_Brain"))
        for source in external.iterdir():
            if source.suffix.lower() in {".png", ".jpg"}:
                with self.subTest(asset=source.name):
                    self.assertEqual((ROOT / IMAGE_PREFIX / "external" / source.name).read_bytes(), source.read_bytes())

    def test_all_content_bearing_legacy_chapters_and_unique_sections_survive(self):
        merged = chapter_bodies(self.text)
        destinations = {"Introduction": "Introductory Summary", "Sciences": "Sciences", "Psychology": "Psychology",
                        "Machine Learning/Data Science/Artificial Intelligence": "Machine Learning/Data Science/Artificial Intelligence",
                        "Nanotechnology": "Nanotechnology", "Economics": "Economics", "Theology": "Theology",
                        "Job Related Endeavors": "Job Related Endeavors"}
        actual = []
        for title, content in chapter_bodies(self.old).items():
            remainder = HEADING.sub("", uncomment(content))
            remainder = re.sub(r"\\(?:newpage|clearpage|maketitle|tableofcontents)\b", "", remainder)
            if not remainder.strip():
                self.assertIn(title, self.manifest["archivedOutlineSections"])
                continue
            with self.subTest(chapter=title):
                self.assertIn(title, destinations)
                target = destinations[title]
                if title == "Economics":
                    # Only these two known empty headings merge into their
                    # populated imported counterparts; the tables stay exact.
                    content = re.sub(r"\\subsection\{(?:Macroeconomics|Microeconomics)\}", "", content)
                self.assertIn(comparable_import(content), comparable_import(merged[target]))
                actual.append({"sourceSection": title, "destinationSection": target})
        self.assertEqual(actual, self.manifest["retainedEarlierSections"])
        self.assertEqual({entry["sourceSection"] for entry in actual}, set(destinations))
        for title in ("Philosophy", "Business", "History", "Sociology", "YouTube Videos"):
            self.assertIn(title, merged)

    def test_every_imported_heading_and_full_chapter_prose_is_preserved(self):
        merged = chapter_bodies(self.text)
        for title, content in chapter_bodies(self.external).items():
            with self.subTest(chapter=title):
                self.assertIn(title, merged)
                self.assertIn(comparable_import(content), comparable_import(merged[title]))
        expected = Counter(HEADING.findall(uncomment(document_body(self.external))))
        actual = Counter(HEADING.findall(uncomment(document_body(self.text))))
        self.assertFalse(expected - actual, "An imported heading was removed")
        self.assertIn(comparable_import(document_body(self.rotor)), comparable_import(merged["Physics"]))
        corrections = " ".join(self.manifest["externalBrain"]["formatCorrections"])
        for correction in ("pgfplots", "matrix", r"\say{string}", "figure label", "ep:209"):
            self.assertIn(correction, corrections)

    def test_all_study_additions_and_editorial_prose_survive_verbatim(self):
        expected = {"Math": "math", "Physics": "physics", "Chemistry": "chemistry",
                    "Computation": "computation", "Engineering": "control", "Nanotechnology": "nano"}
        self.assertEqual(self.manifest["studyAdditions"], expected)
        chapters = chapter_bodies(self.text)
        for chapter, name in expected.items():
            fragment = (ROOT / "notebook_sources/additions" / (name + ".tex")).read_text(encoding="utf-8")
            with self.subTest(fragment=name):
                self.assertEqual(chapters[chapter].count(fragment), 1)
        editorial = (ROOT / "notebook_sources/editorial.tex").read_text(encoding="utf-8")
        self.assertEqual(chapters["Introductory Summary"].count(editorial), 1)

    def test_all_active_original_math_survives_with_multiplicity(self):
        expected = Counter()
        for name, text, inline_count, display_count in (("legacy", self.old, 70, 5),
                                                       ("external", self.external, 646, 634),
                                                       ("rotor", self.rotor, 20, 30)):
            with self.subTest(source=name):
                stripped = TIKZ.sub("", uncomment(document_body(text)))
                # Independent environment inventory guards the lexical oracle.
                self.assertEqual(len(re.findall(r"\\begin\{math\}", stripped)), inline_count)
                self.assertEqual(len(re.findall(r"\\begin\{equation\}", stripped)), display_count)
                payloads = math_payloads(text)
                self.assertEqual(sum(n for (display, _), n in payloads.items() if display), display_count)
                self.assertEqual(sum(n for (display, _), n in payloads.items() if not display), inline_count)
                expected.update(payloads)
        missing = expected - math_payloads(self.text)
        self.assertEqual(sum(missing.values()), 0, f"Lost/changed original math: {list(missing)[:2]}")

    def test_satellite_equations_retain_their_own_namespace_not_the_main_variant(self):
        equation = re.compile(r"\\begin\{equation\}.*?\\end\{equation\}", re.S)
        original = equation.findall(uncomment(self.rotor))
        imported = [payload for payload in equation.findall(uncomment(self.text)) if r"\label{rotor-" in payload]
        self.assertEqual(len(original), 30)
        self.assertEqual(len(imported), 30)
        self.assertEqual([LABEL.sub("", value) for value in original], [LABEL.sub("", value) for value in imported])
        self.assertEqual([LABEL.search(value)[1] for value in imported], [f"rotor-eq-{n}-1" for n in range(252, 282)])
        self.assertNotIn("\\cancelto{1}\n", document_body(self.text))
        self.assertIn("Historical companion manuscript", self.text)
        self.assertIn("39.62", self.text)  # Incorrect historical claim is annotated, not silently erased.

    def test_images_cover_legacy_study_replacements_and_gallery_without_tikz(self):
        active = uncomment(self.text)
        references = IMAGE.findall(active)
        self.assertEqual(len(references), 79)
        self.assertTrue(all(name.startswith(IMAGE_PREFIX) for name in references))
        for name in references:
            with self.subTest(image=name):
                path = ROOT / name
                self.assertTrue(path.resolve().is_relative_to((ROOT / IMAGE_PREFIX).resolve()))
                self.assertTrue(path.is_file(), name)
                if path.suffix == ".png":
                    self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        study = [name for name in references if name.startswith(IMAGE_PREFIX + "study/")]
        self.assertEqual(len(study), 36)
        self.assertEqual(len(set(study)), 36)
        self.assertEqual(set(study), {path.relative_to(ROOT).as_posix() for path in (ROOT / IMAGE_PREFIX / "study").glob("*.png")})
        legacy = [IMAGE_PREFIX + name for name in IMAGE.findall(uncomment(self.old))]
        self.assertEqual(len(legacy), 35)
        self.assertFalse(Counter(legacy) - Counter(references))
        plots = [IMAGE_PREFIX + "external/derivative-" + name + ".png" for name in ("line", "square", "quartic")]
        self.assertEqual(len(TIKZ.findall(uncomment(self.external))), 3)
        for name in plots:
            self.assertEqual(references.count(name), 1)
        gallery = IMAGE.findall(chapter_bodies(self.text)["Imported image archive"])
        self.assertEqual(gallery, [IMAGE_PREFIX + "external/" + name for name in ("ExternalBrain.jpg", "universe.jpg", "Oblate.jpg", "BADErotvsT.png")])
        self.assertEqual(Counter(references), Counter(legacy + study + plots + gallery + [IMAGE_PREFIX + "external/GOODErotvsT.png"]))
        self.assertNotRegex(active, r"\\begin\{(?:tikzpicture|axis)\}|\\addplot\b")

    def test_labels_are_unique_references_resolve_and_ambiguity_is_never_guessed(self):
        active = uncomment(self.text)
        labels = LABEL.findall(active)
        self.assertEqual(len(labels), len(set(labels)))
        self.assertFalse({m[2] for m in REFERENCE.finditer(active)} - set(labels))
        expected_notes = Counter()
        for namespace, original, key in (("eb", self.external, "externalBrain"), ("rotor", self.rotor, "companionRotor")):
            source = uncomment(document_body(original))
            counts = Counter(LABEL.findall(source))
            expected_mapping = {label: [f'{namespace}-{label.replace(":", "-")}-{i}' for i in range(1, count + 1)]
                                for label, count in counts.items()}
            self.assertEqual(self.manifest[key]["labels"], expected_mapping)
            review = []
            for match in REFERENCE.finditer(source):
                old = match[2]
                lookup = "eq:209" if old == "ep:209" and counts["eq:209"] == 1 else old
                if counts[lookup] == 1:
                    self.assertIn("\\" + match[1] + "{" + expected_mapping[lookup][0] + "}", active)
                else:
                    reason = "ambiguous" if counts[old] > 1 else "unresolved"
                    review.append({"label": old, "reason": reason, "candidates": expected_mapping.get(old, [])})
                    expected_notes[(reason, old)] += 1
                    for candidate in expected_mapping.get(old, []):
                        self.assertNotRegex(active, r"\\(?:ref|eqref|autoref)\{" + re.escape(candidate) + r"\}")
            self.assertEqual(self.manifest[key]["referencesNeedingReview"], review)
        notes = Counter(re.findall(r"\[(ambiguous|unresolved) historical reference: ([^\]]+)\]", active))
        self.assertEqual(notes, expected_notes)
        self.assertGreater(sum(expected_notes.values()), 0)
        self.assertIn(r"\ref{ep:209}", self.external)
        self.assertIn(r"\ref{eb-eq-209-1}", active)
        self.assertNotIn(r"\ref{ep:209}", active)

    def test_manifest_detects_changed_archival_fingerprint_even_when_prose_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "notebook_sources", root / "notebook_sources")
            text, before = assemble(root)
            self.assertEqual(before, self.manifest)
            source = root / "notebook_sources/originals/External_Brain/main.tex"
            source.write_bytes(source.read_bytes() + b"\n% Test-only archive fingerprint change\n")
            output, after = assemble(root)
            key = "notebook_sources/originals/External_Brain/main.tex"
            self.assertEqual(text, output)  # Comment outside document is not prose.
            self.assertNotEqual(before["sources"][key], after["sources"][key])
            self.assertEqual(after["sources"][key], sha256(source.read_bytes()).hexdigest())
            source.write_text(source.read_text(encoding="utf-8").replace(r"\end{document}", "Unique mutation sentinel.\n" + r"\end{document}"), encoding="utf-8")
            changed, changed_manifest = assemble(root)
            self.assertIn("Unique mutation sentinel.", changed)
            self.assertNotEqual(changed_manifest["outputSha256"], before["outputSha256"])
            self.assertEqual(changed_manifest["outputSha256"], sha256(changed.encode()).hexdigest())


class LabelNormalizationTests(unittest.TestCase):
    def test_unique_forward_references_and_all_reference_forms(self):
        text = r"See \ref{eq:a}, \eqref{eq:a}, \autoref{eq:a}. \label{eq:a} x=1"
        normalized, audit = normalize_labels(text, "fixture")
        self.assertEqual(normalized, r"See \ref{fixture-eq-a-1}, \eqref{fixture-eq-a-1}, \autoref{fixture-eq-a-1}. \label{fixture-eq-a-1} x=1")
        self.assertEqual(audit, {"labels": {"eq:a": ["fixture-eq-a-1"]}, "referencesNeedingReview": []})
        self.assertEqual(normalize_labels(text, "fixture"), (normalized, audit))

    def test_duplicate_and_missing_references_have_explicit_review_notes(self):
        text = r"\label{eq:x}\label{eq:x} \ref{eq:x} \eqref{absent}"
        normalized, audit = normalize_labels(text, "n")
        self.assertEqual(normalized, r"\label{n-eq-x-1}\label{n-eq-x-2} \textit{[ambiguous historical reference: eq:x]} \textit{[unresolved historical reference: absent]}")
        self.assertEqual(audit["referencesNeedingReview"], [
            {"label": "eq:x", "reason": "ambiguous", "candidates": ["n-eq-x-1", "n-eq-x-2"]},
            {"label": "absent", "reason": "unresolved", "candidates": []}])
        self.assertFalse(REFERENCE.search(normalized))

    def test_typo_correction_requires_a_unique_eq209_target(self):
        for count in (0, 1, 2):
            with self.subTest(targets=count):
                normalized, audit = normalize_labels(r"\ref{ep:209}" + r"\label{eq:209}" * count, "n")
                if count == 1:
                    self.assertIn(r"\ref{n-eq-209-1}", normalized)
                    self.assertEqual(audit["referencesNeedingReview"], [])
                else:
                    self.assertFalse(REFERENCE.search(normalized))
                    self.assertIn("historical reference: ep:209", normalized)
                    self.assertEqual(len(audit["referencesNeedingReview"]), 1)

    def test_comments_do_not_create_duplicate_labels_and_escaped_percent_is_prose(self):
        text = "% \\label{x} \\ref{ghost}\n50\\% retained. \\label{x} \\ref{x} % hidden\n"
        normalized, audit = normalize_labels(text, "n")
        self.assertIn(r"50\% retained.", normalized)
        self.assertEqual(audit, {"labels": {"x": ["n-x-1"]}, "referencesNeedingReview": []})
        self.assertNotIn("ghost", normalized)
        self.assertEqual(active_text(text), uncomment(text))

    def test_legitimate_colon_and_hyphen_labels_cannot_collide(self):
        normalized, _ = normalize_labels(r"\label{a:b}\label{a-b} \ref{a:b} \ref{a-b}", "n")
        labels = LABEL.findall(normalized)
        self.assertEqual(len(labels), len(set(labels)), "Colon rebasing must not merge distinct source labels")
        self.assertEqual([m[2] for m in REFERENCE.finditer(normalized)], labels)

    def test_hostile_missing_reference_is_visible_text_not_html_or_a_link(self):
        payload = '<script>alert("x")</script>'
        normalized, audit = normalize_labels(r"Before \ref{" + payload + "} after.", "n")
        self.assertEqual(audit["referencesNeedingReview"], [{"label": payload, "reason": "unresolved", "candidates": []}])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.tex"
            source.write_text(normalized, encoding="utf-8")
            result = convert_document(source, root, root / "assets", "assets")
            soup = BeautifulSoup(result["body"], "html.parser")
            self.assertFalse(soup.select("script, iframe, .tex-reference, a:not([download])"))
            self.assertIn(payload, soup.get_text())
            self.assertIn("unresolved historical reference", soup.get_text())
            self.assertEqual(result["warnings"], [])

    def test_external_import_rejects_changed_pgfplots_inventory(self):
        source = (ORIGINALS / "External_Brain/main.tex").read_text(encoding="utf-8")
        without_one = TIKZ.sub("", source, count=1)
        with self.assertRaisesRegex(ValueError, "exactly three original pgfplots"):
            import_external(without_one)


class EditorialCorrectionTests(unittest.TestCase):
    def test_companion_four_state_internal_energy_is_28_33_not_39_62_kelvin(self):
        editorial = (ROOT / "notebook_sources/editorial.tex").read_text(encoding="utf-8")
        formula = r"U/k_B=3(59.165)e^{-59.165/50}/[1+3e^{-59.165/50}]\simeq28.33\,\mathrm K"
        self.assertIn(formula, editorial)
        self.assertIn(r"U=-\partial\ln Z/\partial\beta", editorial)
        levels = [0, 59.165, 59.165, 59.165]
        weights = [math.exp(-energy / 50) for energy in levels]
        energy = sum(e * w for e, w in zip(levels, weights, strict=True)) / sum(weights)
        self.assertAlmostEqual(energy, 28.33, delta=0.005)
        self.assertGreater(abs(energy - 39.62), 10)
        beta, step = 1 / 50, 1e-7
        log_z = lambda b: math.log(sum(math.exp(-b * level) for level in levels))
        self.assertAlmostEqual(-(log_z(beta + step) - log_z(beta - step)) / (2 * step), energy, places=6)


if __name__ == "__main__":
    unittest.main()