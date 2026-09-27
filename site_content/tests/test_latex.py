"""Focused converter regressions. Run: python -B -m unittest discover -s site_content/tests -v.

No checked-in/generated fixture files: conversion outputs live in temporary
directories. The real-document tests intentionally use the unchanged source.
"""

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote

from bs4 import BeautifulSoup

from site_content.latex import convert_document


ROOT = Path(__file__).resolve().parents[2]


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "fixture.tex"
        self.images = self.root / "images"
        self.images.mkdir()
        self.assets = self.root / "assets"

    def convert(self, body, preamble="", asset_url="../assets/documents/fixture"):
        self.source.write_text("\\documentclass{article}\n" + preamble + "\n\\begin{document}\n" + body + "\n\\end{document}\n", encoding="utf-8", newline="")
        return convert_document(self.source, self.images, self.assets, asset_url)

    def test_custom_fourth_level_survives_paragraph_redefinition(self):
        result = self.convert(r"""
\section{First}\label{sec:first}
\subsection{Second}\subsubsection{Third}
\subsubsubsection{Fourth \textit{level}}\label{sec:fourth}
\subsubsubsection{Fourth \textit{level}}
\section*{Unnumbered}
See \ref{sec:first} and \ref{sec:fourth}.
""", r"""\makeatletter
\renewcommand\paragraph{\@startsection{paragraph}{5}{\z@}{3ex}{-1em}{\normalfont}}
\makeatother
\setcounter{secnumdepth}{4}""")
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertEqual([h["level"] for h in result["headings"]], [1, 2, 3, 4, 4, 1])
        self.assertEqual([h["number"] for h in result["headings"]], ["1", "1.1", "1.1.1", "1.1.1.1", "1.1.1.2", ""])
        self.assertEqual(soup.select_one("h4")["id"], "sec:fourth")
        toc = BeautifulSoup(result["toc"], "html.parser")
        self.assertEqual(len(toc.select("nav > ol > li > ol > li > ol > li > ol > li")), 2)
        for heading, link in zip(result["headings"], toc.select("a"), strict=True):
            self.assertEqual(unquote(link["href"])[1:], heading["id"])
            self.assertIsNotNone(soup.find(id=heading["id"]))
        self.assertEqual([a.get_text() for a in soup.select("a.tex-reference")], ["1", "1.1.1.1"])
        self.assertEqual(result["warnings"], [])

    def test_duplicate_anchors_are_deterministic_even_for_explicit_labels(self):
        body = r"\section{Repeat}\section{Repeat}\section{Other}\label{x}\section{Other}\label{x}"
        first = self.convert(body)
        second = self.convert(body)
        ids = [h["id"] for h in first["headings"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(first, second)
        self.assertTrue(any("Duplicate heading anchor" in warning for warning in first["warnings"]))

    def test_preserves_exact_inline_math_comments_macros_and_escapes(self):
        payloads = [r"  \R + \frac{a}{b}  ", " x % comment $ ignored\n + y ", r"\text{price \$5} + \%", r"  z^2 "]
        body = "$" + payloads[0] + "$ and \\(" + payloads[1] + "\\) and $" + payloads[2] + "$ and \\begin{math}" + payloads[3] + "\\end{math}."
        result = self.convert(body, r"\newcommand{\R}{\mathbb{R}}")
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertEqual([s.get_text()[2:-2] for s in soup.select("span.math.inline")], payloads)
        self.assertEqual(result["equation_count"], 0)
        self.assertEqual(result["warnings"], [])

    def test_crlf_math_payloads_are_preserved_in_returned_html(self):
        inline = " x +\r\n y "
        display = "\\begin{equation}\r\n x=1\r\n\\end{equation}"
        result = self.convert("$" + inline + "$ " + display)
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertEqual(soup.select_one("span.math.inline").get_text(), r"\(" + inline + r"\)")
        self.assertEqual(soup.select_one("span.math.display").get_text(), r"\[" + display + r"\]")

    def test_equation_environments_tags_labels_and_nonnumbering_remain_exact(self):
        equations = [
            r"\begin{equation}a=1\label{eq:a}\end{equation}",
            r"\begin{equation*}b=2\end{equation*}",
            r"\begin{align}x&=1\label{eq:b}\\y&=2\notag\\z&=3\end{align}",
            r"\begin{align*}a&=b\\c&=d\end{align*}",
            r"\begin{gather}c=3\nonumber\\d=4\label{eq:d}\end{gather}",
            r"\begin{multline}a+b\\+c=d\end{multline}",
            r"\begin{alignat}{2}a&=b & c&=d\end{alignat}",
            r"\begin{equation}e=5\tag{A}\label{eq:tag}\end{equation}",
        ]
        result = self.convert("Before " + " mid ".join(equations) + r" after. \[q=0\] $$r=0$$ \begin{displaymath}s=0\end{displaymath} See \ref{eq:a}, \eqref{eq:b}, \eqref{eq:tag}.")
        soup = BeautifulSoup(result["body"], "html.parser")
        displays = soup.select("span.math.display")
        self.assertEqual(result["equation_count"], 11)
        self.assertEqual([s.get_text()[2:-2] for s in displays], equations + ["q=0", "r=0", "s=0"])
        self.assertFalse(soup.select("p span.math.display"))
        self.assertEqual(len(soup.select(".tex-display-math")), 11)
        self.assertEqual([s.get_text() for s in soup.select("span.math.inline")], [r"\(\ref{eq:a}\)", r"\(\eqref{eq:b}\)", r"\(\eqref{eq:tag}\)"])
        self.assertIn("Before", soup.get_text())
        self.assertIn("after.", soup.get_text())
        self.assertEqual(result["warnings"], [])

    def test_images_preserve_subdirectories_and_encode_urls_and_source(self):
        for relative in ("one/same.png", "two/same.png", "space plot.png"):
            path = self.images / relative
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(relative.encode())
        result = self.convert(r"""\includegraphics{one/same.png}
\includegraphics{two/same.png}
\includegraphics{space plot}
\includegraphics{one/same.png}""", asset_url="../document assets/fixture")
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertEqual(result["image_count"], 4)
        self.assertEqual([i["src"] for i in soup.select("img")], [
            "../document%20assets/fixture/one/same.png", "../document%20assets/fixture/two/same.png",
            "../document%20assets/fixture/space%20plot.png", "../document%20assets/fixture/one/same.png"])
        self.assertEqual((self.assets / "one/same.png").read_bytes(), b"one/same.png")
        self.assertEqual((self.assets / "two/same.png").read_bytes(), b"two/same.png")
        self.assertEqual((self.assets / self.source.name).read_bytes(), self.source.read_bytes())
        self.assertEqual(soup.select_one("a[download]")["href"], "../document%20assets/fixture/fixture.tex")
        self.assertEqual(len(list(self.assets.rglob("*.*"))), 5)  # Source, images, archive-path manifest.

    def test_missing_image_fails_before_any_asset_is_written(self):
        (self.images / "exists.png").write_bytes(b"image")
        with self.assertRaisesRegex(FileNotFoundError, "missing.png.*fixture.tex"):
            self.convert(r"\includegraphics{exists.png}\includegraphics{missing.png}")
        self.assertFalse(self.assets.exists())

    def test_non_browser_image_and_unsafe_paths_fail_actionably(self):
        (self.images / "plot.pdf").write_bytes(b"%PDF")
        for reference, message in [("plot.pdf", "browser-displayable"), ("../secret.png", "Unsafe image"), ("https://example.org/plot.png", "local file")]:
            with self.subTest(reference=reference):
                with self.assertRaisesRegex(ValueError, message):
                    self.convert(r"\includegraphics{" + reference + "}")
        with self.assertRaisesRegex(ValueError, "browser-relative"):
            self.convert("text", asset_url="https://example.org/assets")
        self.assertFalse(self.assets.exists())

    def test_unknown_and_malformed_commands_remain_visible_with_warnings(self):
        result = self.convert(r"Before \textbff{important <script>alert</script>} after. \textbf Unbraced. \eqref{missing}")
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertIn(r"\textbff{important <script>alert</script>}", soup.select_one(".tex-unsupported").get_text())
        self.assertFalse(soup.select("script"))
        self.assertTrue(soup.select(".tex-conversion-warnings"))
        self.assertTrue(any("Unsupported" in w for w in result["warnings"]))
        self.assertTrue(any("unbraced" in w for w in result["warnings"]))
        self.assertTrue(any("Unresolved reference" in w for w in result["warnings"]))
        with self.assertRaisesRegex(ValueError, "Pandoc could not convert"):
            self.convert(r"\textbf{unclosed")
        with self.assertRaisesRegex(ValueError, "Unclosed math"):
            self.convert(r"\begin{equation}unclosed")

    def test_comments_and_verbatim_are_not_headings_math_or_images(self):
        result = self.convert(r"""% \subsubsubsection{Ignored} $unclosed \includegraphics{no.png}
\section{Actual}
\begin{verbatim}
\subsubsubsection{Code} $unclosed \includegraphics{no.png}
\end{verbatim}
\verb|$not math| and $x$.
""")
        self.assertEqual([h["title"] for h in result["headings"]], ["Actual"])
        self.assertEqual(result["equation_count"], 0)
        self.assertEqual(result["image_count"], 0)
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertEqual(len(soup.select("span.math.inline")), 1)
        self.assertIn(r"\subsubsubsection{Code}", soup.select_one("pre").get_text())

    def test_heading_math_has_no_placeholder_anchor_and_lists_tables_survive(self):
        result = self.convert(r"""\section{Energy $E=mc^2$}
Prose \emph{italics} and \textbf{bold}.
\begin{itemize}\item First\begin{enumerate}\item Nested\end{enumerate}\item Last\end{itemize}
\begin{tabular}{cc}A & B\\1 & 2\end{tabular}
""")
        soup = BeautifulSoup(result["body"], "html.parser")
        self.assertNotIn("scmath", result["headings"][0]["id"].lower())
        self.assertEqual(len(soup.select("ul > li > ol > li")), 1)
        self.assertEqual(len(soup.select("table tr")), 2)
        self.assertEqual(len(soup.select("table td")), 4)
        self.assertEqual(soup.select_one("em").get_text(), "italics")
        self.assertEqual(soup.select_one("strong").get_text(), "bold")

    def test_source_counter_customizations_fail_instead_of_misnumbering(self):
        for command in [r"\numberwithin{equation}{section}", r"\setcounter{equation}{7}", r"\renewcommand{\theequation}{X}"]:
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    self.convert(r"\begin{equation}a=1\end{equation}", preamble=command)
        self.assertFalse(self.assets.exists())


class MentalMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.source = ROOT / "mental_map.tex"
        cls.original = cls.source.read_bytes()
        cls.assets = Path(cls.temporary.name) / "mental-map"
        cls.result = convert_document(cls.source, ROOT / "tex_images/mental_map", cls.assets, "../assets/documents/mental-map")
        cls.soup = BeautifulSoup(cls.result["body"], "html.parser")

    def test_real_counts_and_all_nested_fourth_level_toc_links(self):
        result = self.result
        self.assertEqual(set(result), {"body", "toc", "headings", "equation_count", "image_count", "warnings", "source_name"})
        self.assertEqual(len(result["headings"]), 110)
        self.assertEqual(Counter(h["level"] for h in result["headings"]), {1: 18, 2: 18, 3: 47, 4: 27})
        toc = BeautifulSoup(result["toc"], "html.parser")
        self.assertEqual(len(toc.select("a")), 110)
        self.assertEqual(len(toc.select("nav > ol > li > ol > li > ol > li > ol > li")), 27)
        for heading, link in zip(result["headings"], toc.select("a"), strict=True):
            self.assertEqual(unquote(link["href"])[1:], heading["id"])
            self.assertIsNotNone(self.soup.find(id=heading["id"]))
        positivism = next(h for h in result["headings"] if h["title"] == "Positivism")
        self.assertEqual(positivism["number"], "3.3.1.1")
        self.assertEqual(len(set(h["id"] for h in result["headings"])), 110)
        self.assertEqual(result["equation_count"], 5)
        self.assertEqual(result["image_count"], 35)
        self.assertEqual(result["warnings"], [])

    def test_real_math_is_byte_for_byte_inside_delimiters(self):
        text = self.original.decode("utf-8")
        inline = re.findall(r"\\begin\{math\}(.*?)\\end\{math\}", text, re.S)
        display = re.findall(r"\\begin\{equation\}.*?\\end\{equation\}", text, re.S)
        self.assertEqual(len(inline), 70)
        self.assertEqual([s.get_text()[2:-2] for s in self.soup.select("span.math.inline")], inline)
        self.assertEqual([s.get_text()[2:-2] for s in self.soup.select("span.math.display")], display)
        self.assertFalse(self.soup.select("p span.math.display"))

    def test_real_tables_lists_prose_and_all_image_copies(self):
        self.assertEqual(len(self.soup.select("table")), 2)
        self.assertEqual(len(self.soup.select("table tr")), 30)
        self.assertEqual(len(self.soup.select("table td, table th")), 90)
        self.assertEqual(len(self.soup.select("ul")), 18)
        self.assertEqual(len(self.soup.select("ol")), 3)
        self.assertEqual(len(self.soup.select("li")), 122)
        text = self.soup.get_text(" ", strip=True)
        for phrase in ["The way we look at the world", "Cost Function", "Construction", "19.34 T", "Use Case Name:", "Document the Use Case Course of Events", "YouTube Videos"]:
            self.assertIn(phrase, text)
        for image in self.soup.select("img"):
            name = unquote(image["src"].split("/mental-map/", 1)[1])
            self.assertEqual((self.assets / name).read_bytes(), (ROOT / "tex_images/mental_map" / name).read_bytes())
        self.assertEqual(len(list(self.assets.rglob("*.*"))), 37)  # Source, 35 images, archive-path manifest.
        self.assertEqual((self.assets / self.source.name).read_bytes(), self.original)
        self.assertEqual(sha256(self.source.read_bytes()).digest(), sha256(self.original).digest())
        self.assertFalse(self.soup.select("html, head, body, script, style"))


if __name__ == "__main__":
    unittest.main()