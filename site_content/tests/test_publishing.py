"""Publishing contracts and read-only checks of both already-built sites.

Fixtures write only to TemporaryDirectory. Real-site checks skip if no manifest
exists; run the documented build first for a complete validation. Regression
failures are intentionally not hidden behind expectedFailure or allowlists.
"""

from collections import Counter
from contextlib import redirect_stdout
import csv
from hashlib import sha256
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock
from urllib.parse import unquote, urljoin, urlsplit
import zipfile

from bs4 import BeautifulSoup
import pypandoc

from site_content.analysis import analyze_code, analyze_music, music_rows
from site_content.latex import convert_document
from site_content.publishing import (
    card, csv_text, header, load_analysis, publish_portfolio, quantum_html,
    safe_json, shell, source_zip, upgrade_existing_pages, write,
)


ROOT = Path(__file__).resolve().parents[2]
NEW_PAGES = {
    "index.html", "About/index.html", "Mental-Map/index.html",
    "Physics/Quantum-Mechanics/index.html", "Language/Vocabulary/index.html",
    "Language/Feelings/index.html", "Miscellaneous/LeetCode/index.html",
    *(f"{name}/index.html" for name in (
        "Gaming", "Economics", "Business", "Physics", "Language", "Miscellaneous",
    )),
}


class PageIndex(HTMLParser):
    """Index large legacy HTML without retaining its embedded Smash JSON."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = Counter()
        self.tags = []
        self.references = []
        self.navigation = []
        self.base = ""
        self.in_header = False
        self.feed(text)

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        self.tags.append((tag, attrs, pairs))
        if attrs.get("id"):
            self.ids[attrs["id"]] += 1
        if tag == "a" and attrs.get("name"):
            self.ids.setdefault(attrs["name"], 1)
        if tag == "base" and not self.base:
            self.base = attrs.get("href", "")
        if tag == "header" and "site-header" in attrs.get("class", "").split():
            self.in_header = True
        for attribute in ("href", "src", "poster"):
            if attrs.get(attribute) and tag != "base":
                self.references.append((tag, attribute, attrs[attribute]))
        if self.in_header and tag == "a" and attrs.get("href"):
            self.navigation.append(attrs["href"])

    def handle_startendtag(self, tag, pairs):
        self.handle_starttag(tag, pairs)

    def handle_endtag(self, tag):
        if tag == "header":
            self.in_header = False


def page_index(path, cache):
    path = path.resolve()
    if path not in cache:
        cache[path] = PageIndex(path.read_text(encoding="utf-8"))
    return cache[path]


def local_target(site, page, href, base=""):
    """Resolve like a browser, including a legacy page's base element."""
    document_url = "https://site.invalid/" + page.relative_to(site).as_posix()
    resolved = urlsplit(urljoin(urljoin(document_url, base), href))
    if resolved.scheme != "https" or resolved.netloc != "site.invalid":
        return None
    target = site / unquote(resolved.path).lstrip("/")
    if resolved.path.endswith("/") or target.is_dir():
        target /= "index.html"
    return target.resolve(), unquote(resolved.fragment)


def link_problems(site, page, references, cache):
    index = page_index(page, cache)
    failures = []
    for href in references:
        target = local_target(site, page, href, index.base)
        if target is None:
            continue
        path, fragment = target
        if not path.is_file():
            failures.append(f"{page.relative_to(site)} -> {href}: missing file")
        elif fragment and path.suffix.lower() == ".html":
            if fragment not in page_index(path, cache).ids:
                failures.append(f"{page.relative_to(site)} -> {href}: missing fragment")
    return failures


class TemporaryTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)


class ShellTests(unittest.TestCase):
    def test_shell_relative_prefixes_and_optional_script_order(self):
        for depth in (0, 1, 2, 4):
            with self.subTest(depth=depth):
                prefix = "../" * depth
                soup = BeautifulSoup(shell("Title", "<main>Body</main>", depth,
                                          "assets/fixture.js", math=True,
                                          music=True, analysis=True), "html.parser")
                self.assertEqual(soup.select_one(".brand")["href"], prefix + "index.html")
                self.assertEqual([a["href"] for a in soup.select("header nav a")], [
                    prefix + name + "/index.html" for name in ("Mental-Map", "Language", "Smash", "About")
                ])
                scripts = [tag["src"] for tag in soup.select("script[src]")]
                self.assertEqual(scripts, [prefix + path for path in (
                    "assets/math-config.js", "assets/vendor/mathjax/tex-chtml.js",
                    "assets/fixture.js", "assets/data/music-analysis.js",
                    "assets/analysis.js", "assets/site.js", "assets/portfolio.js",
                )])
                self.assertTrue(all(tag["href"].startswith(prefix + "assets/") for tag in soup.select("head link")))
                self.assertEqual(len(soup.select("#main-content")), 1)

    def test_optional_assets_absent_and_existing_main_unchanged(self):
        body = '<main id="main-content" data-note="keep"><p>Authored &amp; retained.</p></main>'
        page = shell("Plain", body)
        self.assertIn(body, page)
        self.assertNotIn("math-config", page)
        self.assertNotIn("music-analysis", page)
        self.assertNotIn('src="assets/analysis.js"', page)

    def test_title_and_card_attributes_escape_untrusted_display_text(self):
        payload = '</title><script>alert("x")</script>&'
        soup = BeautifulSoup(shell(payload, "<main>Trusted body</main>"), "html.parser")
        self.assertEqual(soup.title.get_text(), payload + " | Liam McGrath")
        self.assertFalse(soup.select("script:not([src])"))
        fragment = BeautifulSoup(card('path?x=" onmouseover="bad', payload, payload, payload), "html.parser")
        self.assertNotIn("onmouseover", fragment.a.attrs)
        self.assertFalse(fragment.select("script"))
        self.assertEqual(fragment.h3.get_text(), payload)

    def test_safe_json_round_trip_and_script_breakout_protection(self):
        value = {"lyrics": '</script><script>alert("x")</script>&\u2028\u2029', "unicode": "café ψ", "number": -3, "null": None}
        encoded = safe_json(value)
        self.assertEqual(json.loads(encoded), value)
        for forbidden in ("<", "&", "\u2028", "\u2029"):
            self.assertNotIn(forbidden, encoded)
        soup = BeautifulSoup('<script>window.DATA=' + encoded + ';</script>', "html.parser")
        self.assertEqual(len(soup.select("script")), 1)
        self.assertEqual(soup.script.string, "window.DATA=" + encoded + ";")


class CsvTests(unittest.TestCase):
    def test_formula_prefixes_including_leading_whitespace_are_protected(self):
        values = ['=1+1', '+SUM(A1:A2)', '-1+2', '@SUM(A1:A2)', '  =1', '\t=1', '\r+1', '\n@x', '\u00a0-1']
        rows = [{"text": value} for value in values]
        parsed = list(csv.DictReader(io.StringIO(csv_text(rows))))
        self.assertEqual([row["text"] for row in parsed], ["'" + value for value in values])
        self.assertEqual([row["text"] for row in rows], values)

    def test_benign_text_quotes_newlines_unicode_and_numbers_round_trip(self):
        rows = [{"text": 'café, "quote"\nsecond line', "number": -1.25, "null": None},
                {"text": "already 'escaped", "number": 0, "null": None}]
        parsed = list(csv.DictReader(io.StringIO(csv_text(rows))))
        self.assertEqual(parsed[0], {"text": rows[0]["text"], "number": "-1.25", "null": ""})
        self.assertEqual(parsed[1]["text"], rows[1]["text"])

    def test_empty_rows_and_whitespace_only_values(self):
        self.assertEqual(csv_text([]), "")
        for value in ("", " ", "\t", "\r", "\n"):
            with self.subTest(value=repr(value)):
                parsed = list(csv.DictReader(io.StringIO(csv_text([{"text": value}]))))
                self.assertEqual(parsed[0]["text"], value)


class SourceZipTests(TemporaryTest):
    def test_zip_preserves_source_and_nested_image_bytes_and_excludes_other_files(self):
        source = self.root / "notes.tex"
        source.write_bytes(b"source\r\nunchanged\r\n")
        assets = self.root / "assets"
        images = {"plot.png": b"png", "nested/space plot.SVG": b"svg", "same/plot.webp": b"webp"}
        for name, data in images.items():
            destination = assets / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        write(assets / "unrelated.js", "do not archive")
        write(assets / "old.tex", "not the source")
        for _ in range(2):
            source_zip(source, assets)
            with zipfile.ZipFile(assets / "source-bundle.zip") as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), {source.name, *images})
                self.assertEqual(archive.read(source.name), source.read_bytes())
                for name, data in images.items():
                    self.assertEqual(archive.read(name), data)

    def test_zip_recreates_prefixed_includegraphics_paths(self):
        source = self.root / "notes.tex"
        images = self.root / "tex_images" / "notes"
        images.mkdir(parents=True)
        (images / "plot.png").write_bytes(b"image")
        write(source, r"\includegraphics{tex_images/notes/plot.png}")
        assets = self.root / "assets"
        convert_document(source, images, assets, "assets")
        source_zip(source, assets)
        with zipfile.ZipFile(assets / "source-bundle.zip") as archive:
            self.assertIn("tex_images/notes/plot.png", archive.namelist(),
                          "The unchanged TeX must find the same image path after extracting its ZIP")


class SnapshotTests(TemporaryTest):
    def test_existing_repository_refreshes_snapshot(self):
        repo = self.root / "repo"
        repo.mkdir()
        function = Mock(return_value={"text": "</script>café"})
        result = load_analysis(self.root, "fixture", function, repo)
        function.assert_called_once_with(repo)
        snapshot = self.root / "records/site_content/fixture.json"
        self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8")), result)

    def test_missing_repository_uses_snapshot_without_calling_analyzer(self):
        snapshot = self.root / "records/site_content/fixture.json"
        write(snapshot, '{"saved":true}')
        function = Mock(side_effect=AssertionError("must not analyze"))
        log = io.StringIO()
        with redirect_stdout(log):
            result = load_analysis(self.root, "fixture", function, self.root / "absent")
        self.assertEqual(result, {"saved": True})
        self.assertIn("using saved analysis snapshot", log.getvalue())
        function.assert_not_called()

    def test_missing_repository_and_snapshot_fail_actionably(self):
        with self.assertRaisesRegex(FileNotFoundError, "no fixture snapshot"):
            load_analysis(self.root, "fixture", Mock(), self.root / "absent")

    def test_analyzer_failure_does_not_silently_use_old_snapshot(self):
        snapshot = self.root / "records/site_content/fixture.json"
        write(snapshot, '{"saved":true}')
        original = snapshot.read_bytes()
        with self.assertRaisesRegex(ValueError, "invalid input"):
            load_analysis(self.root, "fixture", Mock(side_effect=ValueError("invalid input")), self.root)
        self.assertEqual(snapshot.read_bytes(), original)


class UpgradeTests(TemporaryTest):
    def legacy(self, main='<main data-preserve="yes">Keep this body</main>', body='<body>', head='<header class="site-header">Old</header>'):
        page = self.root / "Smash/Fighter/index.html"
        text = ('<!doctype html><html><head><title>Keep title</title>'
                '<link href="../../assets/styles.css" rel="stylesheet"></head>'
                + body + head + '<!-- KEEP COMMENT -->' + main
                + '<script id="saved-data" type="application/json">{"value":"<>&", "score":1.234}</script>'
                + '<script>const unchanged = "original";</script></body></html>')
        write(page, text)
        return page, text

    def test_standard_chrome_idempotence_preserves_arbitrary_main_and_data_bytes(self):
        main = '<main id="main-content" data-note="&quot;keep&quot;"><svg><path d="M0 0"/></svg><table><tr><td>1.234</td></tr></table></main>'
        page, original = self.legacy(main=main)
        data = self.root / "assets/untouched.json"
        write(data, '{"scores":[3,1,2]}')
        data_bytes = data.read_bytes()
        upgrade_existing_pages(self.root)
        updated = page.read_text(encoding="utf-8")
        self.assertIn(main, updated)
        self.assertIn(original[original.index('<!-- KEEP COMMENT -->'):original.index('</body>')], updated)
        self.assertIn(header("../../"), updated)
        self.assertEqual(data.read_bytes(), data_bytes)
        before = page.read_bytes(), page.stat().st_mtime_ns
        upgrade_existing_pages(self.root)
        self.assertEqual((page.read_bytes(), page.stat().st_mtime_ns), before)

    def test_main_id_inserted_once_for_standard_legacy_markup(self):
        page, _ = self.legacy()
        upgrade_existing_pages(self.root)
        upgrade_existing_pages(self.root)
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(len(soup.select("main#main-content")), 1)
        self.assertEqual(len(soup.select(".skip-link")), 1)
        self.assertEqual(soup.select_one("main")["data-preserve"], "yes")
        self.assertEqual(len(soup.select('link[href$="portfolio.css"]')), 1)
        self.assertEqual(len(soup.select('script[src$="portfolio.js"]')), 1)

    def test_existing_main_id_is_preserved_without_duplicate_id_attributes(self):
        page, _ = self.legacy(main='<main id="custom-main" data-preserve="yes">Keep</main>')
        upgrade_existing_pages(self.root)
        index = PageIndex(page.read_text(encoding="utf-8"))
        main = next(item for item in index.tags if item[0] == "main")
        self.assertEqual([value for key, value in main[2] if key == "id"], ["custom-main"])
        self.assertFalse(link_problems(self.root, page, [href for _, _, href in index.references if href.startswith("#")], {}))

    def test_body_attributes_retained_and_skip_link_is_added(self):
        page, _ = self.legacy(body='<body class="legacy" data-layout="original">')
        upgrade_existing_pages(self.root)
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(soup.body["data-layout"], "original")
        self.assertEqual(soup.body["class"], ["legacy"])
        self.assertIsNotNone(soup.select_one(".skip-link"))

    def test_header_with_additional_attributes_receives_shared_navigation(self):
        page, _ = self.legacy(head='<header class="site-header" data-layout="legacy">Old</header>')
        upgrade_existing_pages(self.root)
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(len(soup.select('header nav[aria-label="Primary navigation"] a')), 4)

    def test_unrelated_html_and_git_metadata_untouched(self):
        unrelated = self.root / "Other/index.html"
        git_page = self.root / ".git/fixture.html"
        write(unrelated, '<html><body><main>Unrelated</main></body></html>')
        write(git_page, shell("Private metadata", "<main>Keep</main>"))
        before = {path: path.read_bytes() for path in (unrelated, git_page)}
        upgrade_existing_pages(self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in before})


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        cls.site = cls.root / "site"
        cls.music_repo = cls.root / "music"
        cls.code_repo = cls.root / "code"
        write(cls.music_repo / "song.txt", 'happy & grateful\n</script><script>alert("x")</script>\n=1+1\n')
        write(cls.code_repo / "fixture.py", 'raise RuntimeError("never execute")\ndef example():\n    pass\n')
        cls.music = analyze_music(cls.music_repo)
        cls.code = analyze_code(cls.code_repo)
        for name in ("styles.css", "site.js"):
            write(cls.site / "assets" / name, "/* existing asset */")
        for relative in ("Smash/index.html", "Physics/Dipole-Atlas/index.html"):
            depth = len(Path(relative).parts) - 1
            write(cls.site / relative, shell("Existing", '<main id="main-content">Existing body</main>', depth))
        cls.original = (ROOT / "mental_map.tex").read_bytes()
        with redirect_stdout(io.StringIO()):
            cls.manifest = publish_portfolio(ROOT, cls.site, cls.music, cls.code)
        # read_text() applies universal newline conversion; decode bytes so the
        # exact original CRLF inside protected math remains observable.
        cls.paper = BeautifulSoup((cls.site / "Mental-Map/index.html").read_bytes().decode("utf-8"), "html.parser")

    def test_thirteen_pages_and_all_local_links_fragments_assets(self):
        self.assertEqual(set(self.manifest["pages"]), NEW_PAGES)
        cache = {}
        failures = []
        for relative in sorted(NEW_PAGES):
            page = self.site / relative
            index = page_index(page, cache)
            failures.extend(link_problems(self.site, page, [href for _, _, href in index.references], cache))
        self.assertEqual(failures, [])

    def test_document_heading_levels_numbering_toc_and_unique_ids(self):
        headings = self.paper.select(".tex-paper h1, .tex-paper h2, .tex-paper h3, .tex-paper h4, .tex-paper h5, .tex-paper h6")
        links = self.paper.select("#reader-toc a")
        source_body = self.original.decode("utf-8").split(r"\begin{document}", 1)[1]
        commands = re.findall(r"\\(section|subsection|subsubsection|subsubsubsection)\*?\{", source_body)
        self.assertEqual(len(headings), len(commands))
        self.assertEqual(len(headings), 110)
        self.assertEqual(Counter(h.name for h in headings), {"h1": 18, "h2": 18, "h3": 47, "h4": 27})
        self.assertEqual([unquote(link["href"])[1:] for link in links], [h["id"] for h in headings])
        self.assertEqual([name for name, count in Counter(t["id"] for t in self.paper.select("[id]")).items() if count > 1], [])
        self.assertEqual(self.paper.find(id="positivism")["data-number"], "3.3.1.1")
        for anchor in ("physics", "quantum-mechanics", "business", "economics"):
            self.assertIsNotNone(self.paper.find(id=anchor), anchor)
        self.assertEqual(self.manifest["document"]["warnings"], [])

    def test_original_math_payloads_and_block_counts_match_source(self):
        source = self.original.decode("utf-8")
        inline = re.findall(r"\\begin\{math\}(.*?)\\end\{math\}", source, re.S)
        display = re.findall(r"\\begin\{equation\}.*?\\end\{equation\}", source, re.S)
        self.assertEqual((len(inline), len(display)), (70, 5))
        self.assertEqual([span.get_text()[2:-2] for span in self.paper.select(".tex-paper .math.inline")], inline)
        self.assertEqual([span.get_text()[2:-2] for span in self.paper.select(".tex-paper .math.display")], display)
        self.assertEqual(self.manifest["document"]["equation_count"], len(display))
        self.assertFalse(self.paper.select("p .math.display"))

    def test_all_source_images_verified_independently_by_pandoc_and_bytes(self):
        source = self.original.decode("utf-8")
        ast = json.loads(pypandoc.convert_text(source, "json", format="latex+raw_tex-latex_macros", extra_args=["--sandbox"]))

        def images(value):
            if isinstance(value, dict):
                if value.get("t") == "Image":
                    yield value["c"][2][0]
                for child in value.values():
                    yield from images(child)
            elif isinstance(value, list):
                for child in value:
                    yield from images(child)

        parsed = list(images(ast))
        raw = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", source)
        rendered = [unquote(image["src"].split("/mental-map/", 1)[1]) for image in self.paper.select(".tex-paper img")]
        self.assertEqual(len(raw), 35)
        self.assertEqual(raw, parsed)
        self.assertEqual(parsed, rendered)
        self.assertEqual(self.manifest["document"]["image_count"], len(parsed))
        assets = self.site / "assets/documents/mental-map"
        with zipfile.ZipFile(assets / "source-bundle.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {"mental_map.tex", *raw})
            self.assertEqual(archive.read("mental_map.tex"), self.original)
            for name in raw:
                expected = (ROOT / "tex_images/mental_map" / name).read_bytes()
                self.assertEqual((assets / name).read_bytes(), expected)
                self.assertEqual(archive.read(name), expected)
        self.assertEqual((assets / "mental_map.tex").read_bytes(), self.original)
        self.assertEqual((ROOT / "mental_map.tex").read_bytes(), self.original)

    def test_downloads_are_complete_json_is_lossless_and_csv_is_protected(self):
        data = self.site / "assets/data"
        self.assertEqual(json.loads((data / "music-analysis.json").read_text(encoding="utf-8")), self.music)
        script = (data / "music-analysis.js").read_text(encoding="utf-8")
        self.assertNotIn("</script>", script)
        self.assertEqual(json.loads(script.removeprefix("window.MUSIC_ANALYSIS=").removesuffix(";")), self.music)
        for table, rows in music_rows(self.music).items():
            with self.subTest(table=table):
                # DictWriter emits CRLF; write(newline="\n") preserves it.
                self.assertEqual((data / f"music-{table}.csv").read_bytes(), csv_text(rows).encode("utf-8"))
        with (data / "music-lines.csv").open(encoding="utf-8", newline="") as handle:
            exported = list(csv.DictReader(handle))
        self.assertEqual(exported[-1]["text"], "'=1+1")
        feelings = BeautifulSoup((self.site / "Language/Feelings/index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual([line.get_text() for line in feelings.select(".lyric-text")], [line["text"] for line in self.music["songs"][0]["lines"]])
        self.assertFalse(feelings.select("script:not([src])"))

    def test_rebuild_preserves_existing_pages_and_stable_content_hashes(self):
        paths = [self.site / path for path in NEW_PAGES]
        paths += [self.site / "Smash/index.html", self.site / "Physics/Dipole-Atlas/index.html"]
        before = {path: sha256(path.read_bytes()).digest() for path in paths}
        with redirect_stdout(io.StringIO()):
            manifest = publish_portfolio(ROOT, self.site, self.music, self.code)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(before, {path: sha256(path.read_bytes()).digest() for path in paths})

    def test_optional_quantum_manuscript_uses_local_math_toc_and_source_zip(self):
        root = self.root / "quantum-source"
        source = root / "quantum_mechanics.tex"
        write(source, r"\section{Fixture}\label{fixture} $x$ \begin{equation}E=1\tag{Q}\end{equation}")
        site = self.root / "quantum-site"
        soup = BeautifulSoup(quantum_html(root, site), "html.parser")
        self.assertEqual(soup.select_one("#reader-toc a")["href"], "#fixture")
        self.assertIsNotNone(soup.select_one(".tex-paper #fixture"))
        self.assertEqual(soup.select_one(".math.display").get_text()[2:-2], r"\begin{equation}E=1\tag{Q}\end{equation}")
        self.assertEqual(soup.select_one("#MathJax-script")["src"], "../../assets/vendor/mathjax/tex-chtml.js")
        with zipfile.ZipFile(site / "assets/documents/quantum-mechanics/source-bundle.zip") as archive:
            self.assertEqual(archive.read(source.name), source.read_bytes())


class PublishedSiteTests(unittest.TestCase):
    """Read only; validate current build outputs, not an old Git baseline."""

    @classmethod
    def setUpClass(cls):
        cls.sites = [site.resolve() for site in (
            ROOT / "LiamMs_PandasProjects", ROOT.parent / "liammspandasprojects",
        ) if (site / "assets/data/portfolio-build.json").is_file()]
        if not cls.sites:
            raise unittest.SkipTest("Build the portfolio first to check published sites")
        cls.cache = {}

    def test_new_pages_all_local_links_fragments_and_asset_references(self):
        for site in self.sites:
            with self.subTest(site=site.name):
                manifest = json.loads((site / "assets/data/portfolio-build.json").read_text(encoding="utf-8"))
                self.assertEqual(set(manifest["pages"]), NEW_PAGES)
                failures = []
                for relative in sorted(NEW_PAGES):
                    page = site / relative
                    index = page_index(page, self.cache)
                    failures.extend(link_problems(site, page, [href for _, _, href in index.references], self.cache))
                self.assertEqual(failures, [])

    def test_shared_navigation_targets_on_every_upgraded_shell_page(self):
        expected = {"index.html", "Mental-Map/index.html", "Language/index.html", "Smash/index.html", "About/index.html"}
        for site in self.sites:
            failures = []
            for page in sorted(site.rglob("*.html")):
                if ".git" in page.parts or page.relative_to(site).as_posix() in NEW_PAGES:
                    continue
                index = page_index(page, self.cache)
                # Phase viewers have their own shell and <base> routing. The
                # portfolio intentionally preserves them, including their data.
                if not any(tag == 'link' and attrs.get('href', '').endswith('assets/styles.css') for tag, attrs, _ in index.tags):
                    continue
                resolved = [local_target(site, page, href, index.base) for href in index.navigation]
                actual = {target[0].relative_to(site).as_posix() for target in resolved if target is not None and target[0].is_relative_to(site)}
                if actual != expected:
                    failures.append(f"{page.relative_to(site)}: navigation {sorted(actual)}")
                failures.extend(link_problems(site, page, index.navigation, self.cache))
            with self.subTest(site=site.name):
                self.assertEqual(failures, [])

    def test_static_duplicate_ids_and_toc_targets_on_portfolio_shell_pages(self):
        for site in self.sites:
            failures = []
            for page in sorted(site.rglob("*.html")):
                if ".git" in page.parts:
                    continue
                index = page_index(page, self.cache)
                # Existing standalone Phase SVGs are outside this publisher's
                # ownership; validate new and upgraded shared-shell HTML only.
                if not any(tag == 'link' and attrs.get('href', '').endswith('assets/styles.css') for tag, attrs, _ in index.tags):
                    continue
                duplicates = [name for name, count in index.ids.items() if count > 1]
                if duplicates:
                    failures.append(f"{page.relative_to(site)}: duplicate IDs {duplicates}")
                for tag, _, pairs in index.tags:
                    if sum(key == "id" for key, _ in pairs) > 1:
                        failures.append(f"{page.relative_to(site)}: duplicate id attributes on {tag}")
            document = site / "Mental-Map/index.html"
            soup = BeautifulSoup(document.read_text(encoding="utf-8"), "html.parser")
            failures.extend(link_problems(site, document, [link["href"] for link in soup.select("#reader-toc a")], self.cache))
            with self.subTest(site=site.name):
                self.assertEqual(failures, [])

    def test_stylesheet_urls_resolve_including_local_math_fonts(self):
        for site in self.sites:
            failures = []
            for stylesheet in sorted((site / "assets").rglob("*.css")):
                # Vendor JS module IDs are not browser URLs; only real CSS URLs.
                content = stylesheet.read_text(encoding="utf-8")
                urls = re.findall(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", content)
                for href in urls:
                    target = local_target(site, stylesheet, href.strip())
                    if target is not None and not target[0].is_file():
                        failures.append(f"{stylesheet.relative_to(site)} -> {href}")
            with self.subTest(site=site.name):
                self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()