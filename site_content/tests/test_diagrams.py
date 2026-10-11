"""Study-only checks; all integration output is isolated in temporary folders.

Run with ``python -B -m unittest site_content.tests.test_diagrams -v``.
No parent document, publisher output, or resume is modified.
"""

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET

import matplotlib
import numpy as np
from PIL import Image

from site_content.diagrams import ASSET_DIRECTORY, build_diagrams, closed_loop_poles, euler_decay, grid_path_counts


ROOT = Path(__file__).resolve().parents[2]
FRAGMENTS = ROOT / "notebook_sources/additions"
FIGURE_RE = re.compile(r"\\includegraphics\[width=0\.95\\linewidth\]\{([^}]+)\}")


def prose_word_count(text: str) -> int:
    """Approximate prose count excluding equations, URLs, labels and image paths."""
    text = re.sub(r"\\begin\{(equation\*?|align\*?)\}.*?\\end\{\1\}", " ", text, flags=re.S)
    text = re.sub(r"\\\[.*?\\\]|\$[^$]*\$", " ", text, flags=re.S)
    text = re.sub(r"\\(?:label|ref|eqref)\{[^}]+\}", " ", text)
    text = re.sub(r"\\includegraphics\[[^]]*\]\{[^}]+\}", " ", text)
    text = re.sub(r"\\href\{[^}]+\}", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^}]+\}(?:\[[^]]*\])?", " ", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    return len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", text))


class NumericalExampleTests(unittest.TestCase):
    def test_euler_stability_and_initial_value(self):
        t, y = euler_decay(0.1, 10)
        self.assertEqual(y[0], 1)
        self.assertAlmostEqual(t[-1], 1)
        np.testing.assert_allclose(y, 0.8 ** np.arange(11))
        self.assertGreater(abs(euler_decay(1.1, 5)[1][-1]), 1)
        with self.assertRaises(ValueError):
            euler_decay(0, 3)

    def test_cubic_routh_interval_and_root_residuals(self):
        gains = np.array([0, 0.001, 2, 5.999, 6, 6.001, 20])
        poles = closed_loop_poles(gains)
        for gain, row in zip(gains, poles):
            np.testing.assert_allclose(row ** 3 + 3 * row ** 2 + 2 * row + gain, 0, atol=1e-10)
        self.assertTrue(np.all(poles[1:4].real < 0))
        np.testing.assert_allclose(np.sort_complex(poles[4]),
                                   np.sort_complex(np.array([-3, -1j * np.sqrt(2), 1j * np.sqrt(2)])), atol=1e-10)
        self.assertEqual(sum(poles[5].real > 0), 2)
        self.assertEqual(closed_loop_poles(np.array([])).shape, (0, 3))

    def test_nyquist_clockwise_count_matches_unstable_poles(self):
        frequency = np.concatenate((-np.logspace(5, -5, 10000), [0], np.logspace(-5, 5, 10000)))
        for gain, unstable in ((2, 0), (10, 2)):
            loop = gain / (1 + 1j * frequency) ** 3
            # The closing arc maps to zero; compute clockwise winding around -1.
            argument = np.unwrap(np.angle(np.concatenate((1 + loop, [1 + loop[0]]))))
            clockwise = -(argument[-1] - argument[0]) / (2 * np.pi)
            self.assertAlmostEqual(clockwise, unstable, places=8)
            roots = np.roots([1, 3, 3, 1 + gain])
            self.assertEqual(sum(roots.real > 0), unstable)

    def test_controller_and_observer_examples(self):
        a = np.array([[0, 1], [-2, -3]])
        b = np.array([[0], [1]])
        c = np.array([[1, 0]])
        self.assertEqual(np.linalg.matrix_rank(np.column_stack((b, a @ b))), 2)
        self.assertEqual(np.linalg.matrix_rank(np.vstack((c, c @ a))), 2)
        np.testing.assert_allclose(np.sort(np.linalg.eigvals(a - b @ np.array([[18, 6]]))), [-5, -4])
        np.testing.assert_allclose(np.sort(np.linalg.eigvals(a - np.array([[10], [10]]) @ c)), [-7, -6])

    def test_grid_counts_boundaries_and_large_integers(self):
        table = grid_path_counts(4, 5)
        self.assertEqual(table[-1, -1], 35)
        self.assertTrue(np.all(table[0] == 1))
        self.assertTrue(np.all(table[:, 0] == 1))
        self.assertGreater(grid_path_counts(40, 40)[-1, -1], 2 ** 63)
        with self.assertRaises(ValueError):
            grid_path_counts(0, 3)


class DiagramIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="study-diagrams-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            cls.paths = build_diagrams(cls.root)
        cls.sources = {path.name: path.read_text(encoding="utf-8") for path in sorted(FRAGMENTS.glob("*.tex"))}

    def test_all_png_svg_pairs_decode_and_are_not_blank(self):
        self.assertEqual(matplotlib.get_backend().lower(), "agg")
        self.assertEqual(len(self.paths), 72)
        self.assertEqual(len(set(self.paths)), 72)
        self.assertEqual(Counter(p.suffix for p in self.paths), {".png": 36, ".svg": 36})
        for path in self.paths:
            with self.subTest(path=path.name):
                self.assertEqual(path.parent, self.root / ASSET_DIRECTORY)
                if path.suffix == ".png":
                    with Image.open(path) as image:
                        self.assertEqual(image.width, 1600)
                        self.assertGreaterEqual(image.height, 700)
                        rgb = np.asarray(image.convert("RGB"))
                        self.assertGreater(np.mean(np.min(rgb, axis=2) < 200), 0.025)
                else:
                    svg = ET.parse(path).getroot()
                    self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
                    self.assertGreater(len(list(svg.iter("{http://www.w3.org/2000/svg}text"))), 2)
                    self.assertNotIn("<dc:date>", path.read_text(encoding="utf-8"))

    def test_cli_is_byte_deterministic_and_preserves_unrelated_files(self):
        hashes = {path.name: sha256(path.read_bytes()).hexdigest() for path in self.paths}
        sentinel = self.root / ASSET_DIRECTORY / "unrelated.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", "-W", "error::UserWarning", "-m", "site_content.diagrams",
                                 "--root", str(self.root)], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn("Generated 36 figures (72 PNG/SVG files)", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertEqual(hashes, {path.name: sha256(path.read_bytes()).hexdigest() for path in self.paths})
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_body_fragment_structure_and_source_provenance(self):
        self.assertEqual(set(self.sources), {"math.tex", "physics.tex", "chemistry.tex", "computation.tex", "control.tex", "nano.tex"})
        for name, text in self.sources.items():
            with self.subTest(fragment=name):
                self.assertRegex(text, r"^\\subsection\{[^\n]+ -- study additions\}")
                self.assertIn("AI-assisted editorial study additions", text[:500])
                self.assertIn("not verbatim historical writing nor a transcript", text[:500])
                self.assertNotRegex(text, r"\\(?:section|documentclass|usepackage|input|include)\b")
                self.assertNotRegex(text, r"\\begin\{(?:document|tikzpicture|tabular\*)\}")
                stack = []
                for kind, environment in re.findall(r"\\(begin|end)\{([^}]+)\}", text):
                    if kind == "begin":
                        stack.append(environment)
                    else:
                        self.assertTrue(stack)
                        self.assertEqual(stack.pop(), environment)
                self.assertEqual(stack, [])
        self.assertIn("explicitly recorded as completed", self.sources["control.tex"])
        self.assertIn("explicitly self-taught", self.sources["computation.tex"])
        count = sum(prose_word_count(text) for text in self.sources.values())
        self.assertGreaterEqual(count, 4500)
        self.assertLessEqual(count, 6500)

    def test_figures_have_exact_paths_captions_and_complete_coverage(self):
        references = []
        for name, text in self.sources.items():
            figures = re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", text, flags=re.S)
            self.assertEqual(len(figures), text.count(r"\includegraphics"), name)
            for figure in figures:
                matches = FIGURE_RE.findall(figure)
                self.assertEqual(len(matches), 1, name)
                reference = Path(matches[0])
                self.assertEqual(reference.parent, ASSET_DIRECTORY)
                self.assertEqual(reference.suffix, ".png")
                self.assertIn(self.root / reference, self.paths)
                self.assertRegex(figure, r"\\caption\{.{40,}")
                references.append(reference.stem)
        self.assertEqual(len(references), 36)
        self.assertEqual(len(set(references)), 36)
        self.assertEqual(set(references), {path.stem for path in self.paths})

    def test_labels_are_unique_and_cross_references_resolve(self):
        text = "\n".join(self.sources.values())
        labels = re.findall(r"\\label\{([^}]+)\}", text)
        self.assertEqual(len(labels), len(set(labels)))
        self.assertTrue(all(label.startswith("study-") for label in labels))
        self.assertTrue(set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text)).issubset(labels))

    def test_existing_converter_accepts_all_fragments_without_warnings(self):
        # Exercise the existing converter in isolation, not the build/publisher.
        from site_content.latex import convert_document

        source = self.root / "combined.tex"
        body = "\n".join(self.sources[name] for name in
                         ("math.tex", "physics.tex", "chemistry.tex", "computation.tex", "control.tex", "nano.tex"))
        source.write_text("\\documentclass{article}\n\\begin{document}\n\\section{Temporary study fixture}\n"
                          + body + "\n\\end{document}\n", encoding="utf-8")
        converted = convert_document(source, self.root, self.root / "converted", "./assets")
        self.assertEqual(converted["warnings"], [])
        self.assertEqual(converted["image_count"], 36)
        self.assertEqual(sum(h["level"] == 2 for h in converted["headings"]), 6)
        self.assertNotIn("tex-unsupported", converted["body"])


if __name__ == "__main__":
    unittest.main()