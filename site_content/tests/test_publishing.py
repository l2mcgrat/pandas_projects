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
from unittest.mock import Mock, patch
from urllib.parse import unquote, urljoin, urlsplit
import zipfile

from bs4 import BeautifulSoup
import pypandoc

from site_content import atlas
from site_content.analysis import analyze_code, analyze_music, music_rows
from site_content.catalog import leetcode_catalog, rap_catalog
from site_content.latex import _prepare, convert_document
from site_content.publishing import (
    REDIRECTS, csv_text, header, load_analysis, publish_portfolio, quantum_html, redirect_html,
    safe_json, shell, source_zip, upgrade_existing_pages, write,
)


ROOT = Path(__file__).resolve().parents[2]
# Literal on purpose: these hosted readers are contracts, not derived values.
CONTROL = "Science-and-Engineering/Physics/Classical-Mechanics/Control-Systems/index.html"
ALGORITHMS = "Science-and-Engineering/Computer-Science/Data-Structures-and-Algorithms/index.html"
FEELINGS = "Language-and-Programming/Text-Analysis/Sentiment/index.html"
NEW_PAGES = {
    "index.html", "About/index.html", "Mental-Map/index.html", "About/Resume/index.html",
    "Atlas/index.html", "Workbench/index.html", "Updates/index.html", "Completion/index.html", "Traffic/index.html",
    CONTROL, "Language-and-Programming/LeetCode/Source-Index/index.html",
    "Mental-Map/Guide/index.html",
    "Business-and-Economics/Macroeconomics/Economic-Growth/Paper/index.html",
    "Business-and-Economics/Law-and-Policy/Public-Policy/Paper/index.html",
    "Business-and-Economics/Microeconomics/Game-Theory/Gas-Price-Collusion/index.html",
    "Business-and-Economics/Microeconomics/Game-Theory/Paper/index.html",
    "Science-and-Engineering/Chemistry/Electrochemistry/Sodium-Battery-Technology/index.html",
    "Science-and-Engineering/Chemistry/Electrochemistry/Paper/index.html",
    "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/AI-Cost-Study/index.html",
    "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/Paper/index.html",
    "Language-and-Programming/Coding-Projects/Website-Changes/Change-Log/index.html",
    "Language-and-Programming/Coding-Projects/Website-Changes/Upcoming-Changes/index.html",
    "Sports-and-Entertainment/Sports-Analytics/Predictions-and-Results/UFC-Predictions-vs-Outcomes/index.html",
    "Sports-and-Entertainment/Sports-Analytics/Predictions-and-Results/NBA-Predictions-vs-Outcomes/index.html",
    *(f"Gaming-and-Performance-Log/Athletics/{name}/Overview/index.html" for name in ("Running", "Swimming", "Weightlifting")),
    *(node.url for node in atlas.NODES.values() if node.depth),
}
NAVIGATION = ("Mental-Map/index.html", "Atlas/index.html", "Workbench/index.html", "Updates/index.html",
              "index.html#creator-owen", "Smash/index.html", "Completion/index.html", "Traffic/index.html", "About/index.html")


def active_tex(text):
    """Independent comment lexer: consume escaped control symbols before %."""
    return re.sub(r"\\(?:[A-Za-z@]+|[^\r\n])|%[^\r\n]*",
                  lambda match: "" if match[0].startswith("%") else match[0], text)


def source_heading_numbers(text):
    """Count source heading commands, not converter metadata or rendered HTML."""
    body = active_tex(text).split(r"\begin{document}", 1)[-1].split(r"\end{document}", 1)[0]
    levels = {"section": 1, "subsection": 2, "subsubsection": 3, "subsubsubsection": 4, "subparagraph": 5}
    counters = [0] * 5
    result = []
    for command, star in re.findall(r"\\(section|subsection|subsubsection|subsubsubsection|subparagraph)(\*?)\{", body):
        level = levels[command]
        number = ""
        if not star:
            counters[level - 1] += 1
            counters[level:] = [0] * (5 - level)
            number = ".".join(map(str, counters[:level]))
        result.append((f"h{level}", number))
    return result


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
                    prefix + route for route in NAVIGATION
                ])
                scripts = [tag["src"] for tag in soup.select("script[src]")]
                self.assertEqual(scripts, [prefix + path for path in (
                    "assets/math-config.js", "assets/vendor/mathjax/tex-chtml.js",
                    "assets/fixture.js", "assets/data/music-analysis.js",
                    "assets/analysis.js", "assets/site.js", "assets/portfolio.js",
                )])
                self.assertTrue(all(tag["href"].startswith(prefix + "assets/") for tag in soup.select("head link")))
                stylesheets = [tag["href"] for tag in soup.select('link[rel="stylesheet"]')]
                self.assertEqual(stylesheets[:2], [prefix + "assets/styles.css", prefix + "assets/portfolio.css"])
                self.assertIn(prefix + "assets/atlas-icons.css", stylesheets)
                if prefix + "assets/career.css" in stylesheets:
                    self.assertGreater(stylesheets.index(prefix + "assets/career.css"),
                                       stylesheets.index(prefix + "assets/portfolio.css"))
                self.assertEqual(len(soup.select("#main-content")), 1)

    def test_optional_assets_absent_and_existing_main_unchanged(self):
        body = '<main id="main-content" data-note="keep"><p>Authored &amp; retained.</p></main>'
        page = shell("Plain", body)
        self.assertIn(body, page)
        self.assertNotIn("math-config", page)
        self.assertNotIn("music-analysis", page)
        self.assertNotIn('src="assets/analysis.js"', page)

    def test_title_and_redirect_targets_escape_untrusted_text(self):
        payload = '</title><script>alert("x")</script>&'
        soup = BeautifulSoup(shell(payload, "<main>Trusted body</main>"), "html.parser")
        self.assertEqual(soup.title.get_text(), payload + " | Liam McGrath")
        self.assertFalse(soup.select("script:not([src])"))
        moved = BeautifulSoup(redirect_html("Old/index.html", 'x" onmouseover="bad<script>'), "html.parser")
        self.assertFalse(any("onmouseover" in tag.attrs for tag in moved.find_all(True)))
        self.assertFalse(moved.select("script:not([src])"))
        self.assertEqual(moved.select_one('link[rel="canonical"]')["href"], '../x" onmouseover="bad<script>')

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
        (images / "nested").mkdir()
        (images / "nested/space plot.png").write_bytes(b"nested image")
        write(source, r"\includegraphics{tex_images/notes/plot.png}" * 2
              + r"\includegraphics{tex_images/notes/nested/space plot.png}")
        assets = self.root / "assets"
        converted = convert_document(source, images, assets, "assets")
        soup = BeautifulSoup(converted["body"], "html.parser")
        self.assertEqual([image["src"] for image in soup.select("img")],
                         ["assets/plot.png", "assets/plot.png", "assets/nested/space%20plot.png"])
        # A prior build's unused image must not leak into a manifest-backed ZIP.
        (assets / "unused.png").write_bytes(b"not referenced")
        write(assets / "unrelated.js", "not referenced")
        source_zip(source, assets)
        with zipfile.ZipFile(assets / "source-bundle.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertCountEqual(archive.namelist(), [source.name, "tex_images/notes/plot.png",
                                                     "tex_images/notes/nested/space plot.png"])
            self.assertEqual(archive.read(source.name), source.read_bytes())
            self.assertEqual(archive.read("tex_images/notes/plot.png"), b"image")
            self.assertEqual(archive.read("tex_images/notes/nested/space plot.png"), b"nested image")

    def test_manifest_archive_traversal_and_asset_escape_are_rejected(self):
        source = self.root / "notes.tex"
        write(source, "source")
        assets = self.root / "assets"
        write(assets / "plot.png", "image")
        write(self.root / "outside.png", "private")
        for entry in ({"asset": "plot.png", "archive": "../outside.png"},
                      {"asset": "../outside.png", "archive": "plot.png"}):
            with self.subTest(entry=entry):
                write(assets / "source-images.json", json.dumps([entry]))
                with self.assertRaisesRegex(ValueError, "Unsafe source image archive path"):
                    source_zip(source, assets)


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
        self.assertEqual(len(soup.select('header nav[aria-label="Primary navigation"] a')), len(NAVIGATION))

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
        cls.catalogs = {"leetcode": leetcode_catalog(cls.code_repo), "rap": rap_catalog(cls.music_repo)}
        for name in ("styles.css", "site.js"):
            write(cls.site / "assets" / name, "/* existing asset */")
        for relative in ("Smash/index.html", "Physics/Dipole-Atlas/index.html"):
            depth = len(Path(relative).parts) - 1
            write(cls.site / relative, shell("Existing", '<main id="main-content">Existing body</main>', depth))
        cls.original = (ROOT / "mental_map.tex").read_bytes()
        with redirect_stdout(io.StringIO()):
            cls.manifest = publish_portfolio(ROOT, cls.site, cls.music, cls.code, **cls.catalogs)
        # read_text() applies universal newline conversion; decode bytes so the
        # exact original CRLF inside protected math remains observable.
        cls.paper = BeautifulSoup((cls.site / "Mental-Map/index.html").read_bytes().decode("utf-8"), "html.parser")

    def test_every_atlas_page_and_all_local_links_fragments_assets(self):
        self.assertEqual(len(NEW_PAGES), 5 + 258 + 2 + 20)
        self.assertEqual(set(self.manifest["pages"]), NEW_PAGES)
        self.assertEqual(self.manifest["atlasNodes"], 259)
        cache = {}
        failures = []
        for relative in sorted(NEW_PAGES | set(REDIRECTS)):
            page = self.site / relative
            index = page_index(page, cache)
            failures.extend(link_problems(self.site, page, [href for _, _, href in index.references], cache))
        self.assertEqual(failures, [])

    def test_license_and_copyright_notice_on_every_page(self):
        self.assertEqual((self.site / "LICENSE.txt").read_text(encoding="utf-8"),
                         (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn("All rights reserved.", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        for relative in sorted(NEW_PAGES | {"Smash/index.html"}):
            with self.subTest(page=relative):
                soup = BeautifulSoup((self.site / relative).read_text(encoding="utf-8"), "html.parser")
                notice = soup.select("footer.site-footer .site-copyright")
                self.assertEqual(len(notice), 1)
                self.assertIn("\u00a9 2026 Liam McGrath. All rights reserved.", notice[0].get_text())
                target, _ = local_target(self.site, self.site / relative, notice[0].a["href"])
                self.assertEqual(target, (self.site / "LICENSE.txt").resolve())

    def test_mental_map_request_form_drafts_an_email_and_knows_every_destination(self):
        page = self.site / "Mental-Map/index.html"
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        opener = soup.select_one("[data-request-open]")
        self.assertTrue(opener["href"].startswith("mailto:l2mcgrat@uwaterloo.ca?"), "works without JavaScript")
        dialog = soup.select_one("dialog#request-change")
        self.assertEqual(dialog["data-email"], "l2mcgrat@uwaterloo.ca")
        for name in ("name", "date", "section", "subsection", "subsubsection", "content"):
            self.assertIsNotNone(dialog.select_one(f'[name="{name}"]'), name)
        scripts = [tag["src"] for tag in soup.select("script[src]")]
        self.assertLess(scripts.index("../assets/data/atlas-schema.js"), scripts.index("../assets/request-change.js"))
        schema = json.loads((self.site / "assets/data/atlas-schema.js").read_text(encoding="utf-8")
                            .removeprefix("window.SITE_ATLAS=").removesuffix(";"))
        anchors = [leaf["a"] for field in schema["c"] for topic in field["c"] for leaf in [topic, *topic["c"]]]
        self.assertEqual(len(anchors), 252)
        self.assertTrue(all(soup.find(id=anchor) for anchor in anchors))

    def test_feature_cards_show_dates_and_new_pages_are_linked(self):
        page = self.site / "Language-and-Programming/Coding-Projects/Website-Changes/index.html"
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        cards = soup.select(".atlas-feature")
        self.assertTrue(cards)
        for card in cards:
            self.assertRegex(card.time["datetime"], r"^\d{4}-\d{2}-\d{2}$")
        targets = {local_target(self.site, page, card["href"])[0] for card in cards}
        for route in ("Change-Log", "Upcoming-Changes"):
            self.assertIn((page.parent / route / "index.html").resolve(), targets)
        for old in ("", "Predictions-and-Results/"):
            self.assertEqual(REDIRECTS[f"Sports-and-Entertainment/NBA-Analytics/{old}index.html"],
                             f"Sports-and-Entertainment/Sports-Analytics/{old}index.html")

    def test_old_routes_forward_to_new_pages_keeping_query_and_fragment(self):
        self.assertEqual(set(self.manifest["redirects"]), set(REDIRECTS))
        self.assertTrue(set(REDIRECTS).isdisjoint(NEW_PAGES))
        script = (self.site / "assets/redirect.js").read_text(encoding="utf-8")
        self.assertIn("location.search + location.hash", script)
        for old, new in REDIRECTS.items():
            with self.subTest(route=old):
                page = self.site / old
                soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
                canonical = soup.select_one('link[rel="canonical"]')["href"]
                self.assertEqual(local_target(self.site, page, canonical), ((self.site / new).resolve(), ""))
                self.assertIn("url=" + canonical, soup.select_one('meta[http-equiv="refresh"]')["content"])
                self.assertEqual(soup.select_one('meta[name="robots"]')["content"], "noindex")
                self.assertEqual(local_target(self.site, page, soup.select_one("script[src]")["src"])[0],
                                 (self.site / "assets/redirect.js").resolve())

    def test_every_branch_is_a_six_position_hexagon_around_its_mental_map_section(self):
        cache = {}
        positions = {"top", "upper-left", "upper-right", "lower-left", "bottom", "lower-right"}
        css = (self.site / "assets/atlas-icons.css").read_text(encoding="utf-8")
        for node in atlas.NODES.values():
            if not node.children:
                continue
            with self.subTest(node=node.key):
                page = self.site / (node.url if node.depth else "index.html")
                soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
                hexagon = soup.select_one("nav.hex-map")
                outer = hexagon.select("a.hex-node:not(.node-mental-map)")
                self.assertEqual({a["data-topic"] for a in outer}, positions)
                self.assertEqual([local_target(self.site, page, a["href"])[0] for a in outer],
                                 [(self.site / child.url).resolve() for child in node.children])
                self.assertEqual(len(hexagon.select(".map-spoke")), 6)
                centre = hexagon.select_one("a.node-mental-map")
                target, fragment = local_target(self.site, page, centre["href"])
                self.assertEqual(target, (self.site / "Mental-Map/index.html").resolve())
                self.assertEqual(fragment, atlas.anchor(node))
                if fragment:
                    self.assertIn(fragment, page_index(target, cache).ids)
                for svg in hexagon.select("svg.atlas-icon"):
                    name = next(c for c in svg["class"] if c.startswith("ai-"))
                    self.assertIn(f".{name} .", css)

    def test_every_leaf_page_animates_its_icon_and_links_back_up(self):
        for node in atlas.NODES.values():
            if node.children:
                continue
            with self.subTest(node=node.key):
                page = self.site / node.url
                soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
                if soup.select_one(".leaf-hero"):
                    self.assertIsNotNone(soup.select_one(".leaf-icon.is-playing svg.atlas-icon"))
                    self.assertEqual(soup.h1.get_text(), node.title)
                else:  # A hosted reader or explorer keeps an atlas location bar.
                    self.assertIsNotNone(soup.select_one("main .atlas-strip"), "hosted page lacks its location bar")
                crumbs = [local_target(self.site, page, a["href"])[0] for a in soup.select(".atlas-crumbs a")]
                self.assertIn((self.site / atlas.parent(node).url).resolve(), crumbs)

    def test_document_heading_levels_numbering_toc_and_unique_ids(self):
        headings = self.paper.select(".tex-paper h1, .tex-paper h2, .tex-paper h3, .tex-paper h4, .tex-paper h5, .tex-paper h6")
        links = self.paper.select("#reader-toc a")
        expected = source_heading_numbers(self.original.decode("utf-8"))
        numbered = Counter(level for level, number in expected if number)
        # The outline: six fields, 36 topics and 216 destinations, numbered like the website.
        self.assertEqual((numbered["h1"], numbered["h2"], numbered["h3"]), (6, 36, 216))
        self.assertEqual([(h.name, h.get("data-number", "")) for h in headings], expected)
        self.assertEqual([unquote(link["href"])[1:] for link in links], [h["id"] for h in headings])
        self.assertEqual([name for name, count in Counter(t["id"] for t in self.paper.select("[id]")).items() if count > 1], [])
        for anchor in ("about-this-notebook", "sec:science-and-engineering", "sec:physics", "sec:quantum-mechanics",
                       "sec:business-and-economics", "positivism", "study-control", "study-computation"):
            self.assertIsNotNone(self.paper.find(id=anchor), anchor)
        self.assertEqual(self.paper.find(id="sec:quantum-mechanics")["data-number"], "1.2.2")
        self.assertEqual(self.manifest["document"]["warnings"], [])

    def test_original_math_payloads_and_block_counts_match_source(self):
        source = self.original.decode("utf-8")
        # Independent literal fixtures in test_latex verify the lexical pass;
        # slots here preserve every delimiter form, comment and whitespace byte.
        warnings = []
        prepared, slots = _prepare(source, warnings)
        self.assertEqual(warnings, [])
        inline = [slot.payload for slot in slots.values() if not slot.display]
        display = [slot.payload for slot in slots.values() if slot.display]
        independent = re.compile(r"\\begin\{(?P<env>equation|align)\}.*?\\end\{(?P=env)\}|\\\[(.*?)\\\]", re.S)
        self.assertEqual([m[2] if m[2] is not None else m[0] for m in independent.finditer(active_tex(source))], display)
        self.assertEqual(len(display), 687)
        self.assertEqual(sum(slot.original.startswith(r"\[") for slot in slots.values()), 1)
        rendered_inline = [span.get_text()[2:-2] for span in self.paper.select(".tex-paper .math.inline")]
        reference = re.compile(r"\\(?:ref|eqref|autoref)\{([^{}]+)\}")
        self.assertFalse(any(reference.fullmatch(payload) for payload in inline))
        self.assertEqual([payload for payload in rendered_inline if not reference.fullmatch(payload)], inline)
        # Outside-math references become MathJax references or heading links;
        # their exact payloads/targets must also survive, not be filtered away.
        headings = {h["id"] for h in self.paper.select(".tex-paper :is(h1,h2,h3,h4,h5,h6)")}
        references = list(reference.finditer(active_tex(prepared)))
        self.assertEqual(Counter(payload for payload in rendered_inline if reference.fullmatch(payload)),
                         Counter(m[0] for m in references if m[1] not in headings))
        self.assertEqual(Counter(unquote(a["href"])[1:] for a in self.paper.select(".tex-paper a.tex-reference")),
                         Counter(m[1] for m in references if m[1] in headings))
        self.assertEqual([span.get_text()[2:-2] for span in self.paper.select(".tex-paper .math.display")], display)
        self.assertEqual(self.manifest["document"]["equation_count"], len(display))
        self.assertEqual(len(self.paper.select(".tex-paper .tex-display-math")), len(display))
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
        raw = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", active_tex(source))
        rendered = [unquote(image["src"].split("/mental-map/", 1)[1]) for image in self.paper.select(".tex-paper img")]
        self.assertEqual(len(raw), 79)
        self.assertEqual(raw, parsed)
        prefix = "tex_images/mental_map/"
        self.assertTrue(all(name.startswith(prefix) for name in parsed))
        self.assertEqual([name.removeprefix(prefix) for name in parsed], rendered)
        self.assertEqual(self.manifest["document"]["image_count"], len(parsed))
        assets = self.site / "assets/documents/mental-map"
        self.assertEqual(json.loads((assets / "source-images.json").read_text(encoding="utf-8")),
                         [{"archive": name, "asset": name.removeprefix(prefix)} for name in raw])
        with zipfile.ZipFile(assets / "source-bundle.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertCountEqual(archive.namelist(), {"mental_map.tex", *raw})
            self.assertEqual(archive.read("mental_map.tex"), self.original)
            for name in raw:
                expected = (ROOT / name).read_bytes()
                self.assertEqual((assets / name.removeprefix(prefix)).read_bytes(), expected)
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
        feelings = BeautifulSoup((self.site / FEELINGS).read_text(encoding="utf-8"), "html.parser")
        self.assertEqual([line.get_text() for line in feelings.select(".lyric-text")], [line["text"] for line in self.music["songs"][0]["lines"]])
        self.assertFalse(feelings.select("script:not([src])"))

    def test_rebuild_preserves_existing_pages_and_stable_content_hashes(self):
        paths = [self.site / path for path in NEW_PAGES]
        paths += [self.site / "Smash/index.html", self.site / "Physics/Dipole-Atlas/index.html"]
        self.assertEqual([path.relative_to(self.site).as_posix() for path in paths if not path.is_file()], [],
                         "Cannot check rebuild stability until all contracted pages are published")
        before = {path: sha256(path.read_bytes()).digest() for path in paths}
        with redirect_stdout(io.StringIO()):
            manifest = publish_portfolio(ROOT, self.site, self.music, self.code, **self.catalogs)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(before, {path: sha256(path.read_bytes()).digest() for path in paths})

    def test_leetcode_and_rap_destinations_show_their_entries(self):
        page = BeautifulSoup((self.site / "Language-and-Programming/LeetCode/Lists-and-Arrays/index.html").read_text(encoding="utf-8"), "html.parser")
        code = page.select_one(".catalog-item pre.catalog-code code").get_text()
        self.assertIn("def example", code)
        self.assertIn("assets/catalog.css", str(page.head))
        self.assertEqual(page.h1.get_text(), "Lists and Arrays")
        rap = BeautifulSoup((self.site / "Language-and-Programming/Rap/Vagabond/index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertIn("No music_work folder", rap.select_one(".leaf-hero .lede").get_text())
        self.assertEqual(self.manifest["leetcodeEntries"], 1)

    def test_focused_topic_readers_keep_fragment_math_images_source_and_backlinks(self):
        for fragment, relative in (("control", CONTROL), ("computation", ALGORITHMS)):
            with self.subTest(fragment=fragment):
                page = self.site / relative
                self.assertTrue(page.is_file(), f"Publisher has not added {relative}")
                up = "../" * relative.count("/")
                source = ROOT / "notebook_sources/additions" / (fragment + ".tex")
                original = source.read_bytes()
                text = original.decode("utf-8")
                anchor = re.search(r"\\label\{([^}]+)\}", text)[1]
                soup = BeautifulSoup(page.read_bytes().decode("utf-8"), "html.parser")
                self.assertEqual(soup.select_one(".brand")["href"], up + "index.html")
                self.assertEqual(soup.select_one("#MathJax-script")["src"], up + "assets/vendor/mathjax/tex-chtml.js")
                self.assertIsNotNone(soup.select_one(".tex-paper #" + anchor))
                self.assertEqual(len(soup.select("#reader-toc a")), len(source_heading_numbers(text)))
                self.assertFalse(soup.select(".tex-conversion-warnings, .tex-unsupported"))
                _, slots = _prepare(text, [])
                for display, selector in ((True, ".math.display"), (False, ".math.inline")):
                    self.assertEqual([s.get_text()[2:-2] for s in soup.select(".tex-paper " + selector)],
                                     [s.payload for s in slots.values() if s.display == display])
                # Every prose/caption paragraph is independently parsed, not
                # compared against a second invocation of convert_document.
                prose_soup = BeautifulSoup(str(soup.select_one(".tex-paper")), "html.parser")
                for span in prose_soup.select(".math"):
                    span.replace_with(" ")
                prose = re.sub(r"\s+", " ", prose_soup.get_text(" ", strip=True))
                prose_source = text
                for slot in slots.values():
                    prose_source = prose_source.replace(slot.original, " ")
                expected_html = pypandoc.convert_text(prose_source, "html5", format="latex+raw_tex-latex_macros", extra_args=["--sandbox"])
                for paragraph in BeautifulSoup(expected_html, "html.parser").select("p, figcaption"):
                    phrase = re.sub(r"\s+", " ", paragraph.get_text(" ", strip=True))
                    if not paragraph.select("img") and phrase:
                        self.assertIn(phrase, prose)
                names = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", active_tex(text))
                images = soup.select(".tex-paper img")
                self.assertEqual(len(images), len(names))
                for name, image in zip(names, images, strict=True):
                    target, _ = local_target(self.site, page, image["src"])
                    self.assertEqual(target.read_bytes(), (ROOT / name).read_bytes())
                    self.assertNotIn("tex_images/mental_map/", image["src"])
                source_link = soup.select_one(".tex-source-download a[download]")
                self.assertIsNotNone(source_link)
                published_source, _ = local_target(self.site, page, source_link["href"])
                self.assertEqual(published_source.read_bytes(), original)
                with zipfile.ZipFile(published_source.parent / "source-bundle.zip") as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertCountEqual(archive.namelist(), {source.name, *names})
                    self.assertEqual(archive.read(source.name), original)
                    for name in names:
                        self.assertEqual(archive.read(name), (ROOT / name).read_bytes())
                targets = [local_target(self.site, page, a["href"]) for a in soup.select("a[href]")]
                self.assertIn(((self.site / "Mental-Map/index.html").resolve(), anchor), targets)
                self.assertEqual(source.read_bytes(), original)

    def test_mental_map_study_callouts_open_the_correct_focused_pages(self):
        for fragment, relative in (("control", CONTROL), ("computation", ALGORITHMS)):
            with self.subTest(fragment=fragment):
                text = (ROOT / "notebook_sources/additions" / (fragment + ".tex")).read_text(encoding="utf-8")
                anchor = re.search(r"\\label\{([^}]+)\}", text)[1]
                heading = self.paper.find(id=anchor)
                self.assertIsNotNone(heading)
                callout = heading.find_next_sibling()
                self.assertIn("topic-callout", callout.get("class", []), f"Missing focused-page callout at #{anchor}")
                targets = [local_target(self.site, self.site / "Mental-Map/index.html", a["href"])
                           for a in callout.select("a[href]")]
                self.assertIn(((self.site / relative).resolve(), ""), targets)

    def test_resume_is_published_with_depth_two_shell_and_print_action(self):
        page = self.site / "About/Resume/index.html"
        self.assertTrue(page.is_file(), "Publisher has not added About/Resume/index.html")
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(soup.select_one(".brand")["href"], "../../index.html")
        self.assertIsNotNone(soup.select_one("main#main-content.resume-page"))
        self.assertIsNotNone(soup.select_one("button.print-reader"))
        self.assertEqual(len(soup.select('link[href="../../assets/career.css"]')), 1)


class QuantumSourceTests(TemporaryTest):
    def test_primary_and_legacy_quantum_filenames_keep_exact_source_and_local_math(self):
        for index, filename in enumerate(("Quantum_Mechanics.tex", "quantum_mechanics.tex")):
            with self.subTest(filename=filename):
                root = self.root / str(index)
                source = root / filename
                write(source, r"\section{Fixture}\label{fixture} $x$ \begin{equation}E=1\tag{Q}\end{equation}")
                site = root / "site"
                exists = Path.exists

                def exact_case_exists(path):
                    # Exercise the Linux filename contract even on Windows.
                    if path.parent == root and path.suffix == ".tex":
                        return path.name == filename
                    return exists(path)

                with patch.object(Path, "exists", exact_case_exists):
                    soup = BeautifulSoup(quantum_html(root, site), "html.parser")
                self.assertIsNotNone(soup.select_one(".tex-paper #fixture"), f"Reader did not find {filename}")
                self.assertEqual(soup.select_one("#reader-toc a")["href"], "#fixture")
                self.assertEqual(soup.select_one(".math.display").get_text()[2:-2], r"\begin{equation}E=1\tag{Q}\end{equation}")
                self.assertEqual(soup.select_one("#MathJax-script")["src"], "../../../assets/vendor/mathjax/tex-chtml.js")
                with zipfile.ZipFile(site / "assets/documents/quantum-mechanics/source-bundle.zip") as archive:
                    self.assertEqual(archive.namelist(), [filename])
                    self.assertEqual(archive.read(filename), source.read_bytes())


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
        expected = {
            "index.html", "Mental-Map/index.html", "Atlas/index.html", "Workbench/index.html", "Updates/index.html",
            "Smash/index.html", "Completion/index.html", "Traffic/index.html", "About/index.html",
        }
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