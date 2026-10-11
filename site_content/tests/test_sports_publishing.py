"""Sports/work-report publishing boundaries, not basketball engine accounting.

Real sites are read-only; document renders write only to TemporaryDirectory.
PDFs are verified once per document by the real publisher cache gate, never
compiled or text-extracted here. No extra dependencies or production rebuilds.
"""

from collections import Counter
from copy import deepcopy
import csv
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote
import zipfile

from bs4 import BeautifulSoup

from site_content import publishing
from site_content.basketball import export_rows, load_basketball
from site_content.tests.test_publishing import (
    active_tex, link_problems, local_target, page_index,
)
from site_content.work_report import _assert_public, _private_values


ROOT = Path(__file__).resolve().parents[2]
# Field order and positions are the published contract for the home hexagon.
FIELDS = {
    "Science-and-Engineering": "top", "Business-and-Economics": "upper-left",
    "Career-and-Education": "upper-right", "Sports-and-Entertainment": "lower-left",
    "Gaming-and-Performance-Log": "bottom", "Language-and-Programming": "lower-right",
}
HUB = "Sports-and-Entertainment/Series-Hub/"
SPORTS_ROUTES = {
    HUB + "index.html": 2,
    HUB + "Analytics/index.html": 3,
    HUB + "Rules/index.html": 3,
    HUB + "Creator-Petition/index.html": 3,
}
DASHBOARDS = (HUB + "index.html", HUB + "Analytics/index.html")
REPORT = "Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations/index.html"
PHYSICS = "Science-and-Engineering/Physics/index.html"
TABLES = {
    "summary", "series", "rounds", "challenges", "transitions", "byPicker",
    "conditionalNextChallenge", "transitionMatrix", "trajectories",
    "seriesLengths", "comebacks", "timing",
}
# Deliberately independent of the publisher/PDF module's route/source mapping.
DOCUMENTS = {
    "work-term-report": (
        REPORT,
        "notebook_sources/work-report/work_term_report.tex", 7,
    ),
    "basketball-rules": (
        HUB + "Rules/index.html", "notebook_sources/sports/basketball_rules.tex", 23,
    ),
    "creator-pitch": (
        HUB + "Creator-Petition/index.html", "notebook_sources/sports/creator_pitch.tex", 2,
    ),
}
NEW_ROUTES = (*SPORTS_ROUTES, REPORT)
PDF_CACHE = ROOT / "reports/site_content/pdfs"


def soup(text):
    return BeautifulSoup(text, "html.parser")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def built_sites():
    return [site.resolve() for site in (
        ROOT / "LiamMs_PandasProjects", ROOT.parent / "liammspandasprojects",
    ) if (site / "assets/data/portfolio-build.json").is_file()]


def original_images(key):
    """Read includegraphics paths independently, not from an output manifest."""
    source = ROOT / DOCUMENTS[key][1]
    names = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^{}]+)\}",
                       active_tex(source.read_text(encoding="utf-8")))
    directory = ROOT / "WKRPT400" if key == "work-term-report" else ROOT
    return [(name, directory / name) for name in names]


def protected_fingerprints():
    """Hash only relevant sources/data/outputs; never retain private values."""
    paths = set()
    for relative in (
        "WKRPT400", "LiamMcGrath_Resume", "records/basketball", "records/site_content",
        "notebook_sources/work-report", "notebook_sources/sports", "tex_images/sports",
    ):
        paths.update(path for path in (ROOT / relative).rglob("*") if path.is_file())
    paths.update(PDF_CACHE.glob("*.pdf"))
    paths.update(PDF_CACHE.glob("*.json"))
    for site in built_sites():
        paths.update(site / route for route in (*NEW_ROUTES, "index.html", "About/index.html",
                                               "About/Resume/index.html", PHYSICS))
        paths.update(path for path in (site / "assets/data").rglob("*") if path.is_file())
        for key in DOCUMENTS:
            paths.update(path for path in (site / "assets/documents" / key).rglob("*")
                         if path.is_file())
    return {path: (sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in paths}


class HomepageHexagonTests(unittest.TestCase):
    def test_six_fields_at_their_hex_positions_around_the_mental_map(self):
        page = soup(publishing.home_html())
        nodes = page.select(".hex-map a.hex-node")
        self.assertEqual(len(nodes), 7)
        self.assertEqual([node["href"] for node in nodes],
                         [f"{name}/index.html" for name in FIELDS] + ["Mental-Map/index.html"])
        self.assertEqual([node["data-topic"] for node in nodes], [*FIELDS.values(), "center"])
        for node in nodes:
            self.assertEqual(len(node.select("svg.atlas-icon")), 1)
            self.assertIn("atlas-hover", node["class"])
            self.assertTrue(node["data-hint"])
        self.assertEqual(page.select_one(".node-mental-map strong").get_text(), "Mental Map")
        self.assertEqual(page.select_one(".pos-lower-left strong").get_text(), "Sports & Entertainment")

    def test_six_spokes_end_at_matching_css_centres(self):
        page = soup(publishing.home_html())
        css = (ROOT / "site_content/web/portfolio.css").read_text(encoding="utf-8")
        self.assertEqual(page.select_one(".map-connections")["viewbox"], "0 0 600 600")
        spokes = page.select(".map-connections .map-spoke")
        self.assertEqual(len(spokes), 6)
        centres = set()
        for position in FIELDS.values():
            with self.subTest(position=position):
                rule = re.search(re.escape(f".hex-map .pos-{position}") + r"\s*\{([^{}]*)\}", css)
                self.assertIsNotNone(rule)
                positions = dict(re.findall(r"\b(left|top)\s*:\s*([\d.]+)%", rule[1]))
                self.assertEqual(set(positions), {"left", "top"})
                matching = page.select(f".map-spoke.spoke-{position}")
                self.assertEqual(len(matching), 1)
                path = re.fullmatch(r"M\s*300[ ,]+300\s*L\s*([\d.]+)[ ,]+([\d.]+)", matching[0]["d"])
                self.assertIsNotNone(path)
                x, y = float(path[1]), float(path[2])
                self.assertAlmostEqual(x / 6, float(positions["left"]), places=5)
                self.assertAlmostEqual(y / 6, float(positions["top"]), places=5)
                centres.add((x, y))
        self.assertEqual(len(centres), 6)
        # A regular hexagon: every vertex is equidistant from the centre.
        radii = {round(((x - 300) ** 2 + (y - 300) ** 2) ** 0.5) for x, y in centres}
        self.assertEqual(len(radii), 1)

    def test_every_home_node_has_a_hover_animation_and_no_svg_ids(self):
        page = soup(publishing.home_html())
        css = publishing.icons_css()
        self.assertIn(".atlas-hover:is(:hover,:focus-visible) .atlas-icon :is(.a,.b,.c)", css)
        for node in page.select(".hex-map a.hex-node"):
            name = next(c for c in node.svg["class"] if c.startswith("ai-"))
            with self.subTest(icon=name):
                self.assertRegex(css, re.escape(f".{name} .") + r"[abc]\{--o:[^}]*--n:" + re.escape(name))
                self.assertTrue(node.svg.select(".a, .b, .c"))
        ids = [node["id"] for node in page.select("[id]")]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(page.select(".hex-map svg [id]"))

    def test_reduced_motion_disables_icon_and_page_animation(self):
        page = soup(publishing.home_html())
        self.assertFalse(page.select('link[href$="sports.css"]'))
        self.assertIn("@media (prefers-reduced-motion:reduce){.atlas-icon *{animation:none!important}}",
                      publishing.icons_css())
        for name in ("portfolio.css", "sports.css"):
            with self.subTest(stylesheet=name):
                text = (ROOT / "site_content/web" / name).read_text(encoding="utf-8")
                motion = re.search(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", text)
                self.assertIsNotNone(motion)
                self.assertRegex(text[motion.end():], r"animation\s*:\s*none\s*!important")


class SportsShellIntegrationTests(unittest.TestCase):
    def test_report_accent_alias_matches_pdf_and_inline_overflow_is_global(self):
        config = (ROOT / 'site_content/web/math-config.js').read_text(encoding='utf-8')
        self.assertIn("Tilde: '\\\\tilde'", config)
        source = (ROOT / DOCUMENTS['work-term-report'][1]).read_text(encoding='utf-8')
        self.assertIn(r'\providecommand{\Tilde}{\tilde}', source)
        css = (ROOT / 'site_content/web/portfolio.css').read_text(encoding='utf-8')
        # Tablet readers retain a sidebar, so phone-only containment is not enough.
        rule = re.search(r'\.tex-paper \.math\.inline\s*\{([^}]+)\}', css)
        self.assertIsNotNone(rule)
        self.assertLess(rule.start(), css.index('@media'))
        for declaration in ('display:inline-block', 'max-width:100%', 'overflow-x:auto'):
            self.assertIn(declaration, rule[1])

    def test_sports_css_follows_every_shared_stylesheet_at_each_depth(self):
        for depth in (0, 1, 2, 4):
            with self.subTest(depth=depth):
                prefix = "../" * depth
                page = soup(publishing.shell("Sports", "<main>Body</main>", depth, sports=True))
                links = [node["href"] for node in page.select('link[rel="stylesheet"]')]
                self.assertEqual(links.count(prefix + "assets/sports.css"), 1)
                for name in ("styles.css", "portfolio.css", "career.css"):
                    self.assertLess(links.index(prefix + "assets/" + name),
                                    links.index(prefix + "assets/sports.css"))
                self.assertEqual(page.select_one(".brand")["href"], prefix + "index.html")

    def test_basketball_data_loads_before_deferred_sports_script(self):
        for depth in (0, 1, 2, 4):
            with self.subTest(depth=depth):
                prefix = "../" * depth
                page = soup(publishing.shell("Sports", "<main>Body</main>", depth,
                                            "assets/data/basketball-analysis.js", sports=True))
                scripts = page.select("script[src]")
                paths = [node["src"] for node in scripts]
                data_path, ui_path = (prefix + path for path in (
                    "assets/data/basketball-analysis.js", "assets/sports.js"))
                self.assertEqual(paths.count(data_path), 1)
                self.assertEqual(paths.count(ui_path), 1)
                self.assertLess(paths.index(data_path), paths.index(ui_path))
                self.assertFalse(scripts[paths.index(data_path)].has_attr("defer"))
                self.assertFalse(scripts[paths.index(data_path)].has_attr("async"))
                self.assertTrue(scripts[paths.index(ui_path)].has_attr("defer"))
                self.assertFalse(scripts[paths.index(ui_path)].has_attr("async"))

    def test_false_and_default_omit_sports_assets(self):
        for options in ({}, {"sports": False}):
            page = soup(publishing.shell("Plain", "<main>Body</main>", 2, **options))
            self.assertFalse(page.select('link[href$="sports.css"], script[src$="sports.js"], '
                                         'script[src$="basketball-analysis.js"]'))


class PublishedSportsIntegrationTests(unittest.TestCase):
    """Use the same optional real-site convention as test_publishing."""

    @classmethod
    def setUpClass(cls):
        cls.sites = built_sites()
        if not cls.sites:
            raise unittest.SkipTest("Build the portfolio first to check published Sports outputs")
        cls.raw = read_json(ROOT / "records/basketball/series.json")
        cls.analysis = load_basketball(ROOT)
        cls.cache = {}

    def test_manifest_includes_series_hub_routes_fields_and_old_sports_redirects(self):
        for site in self.sites:
            with self.subTest(site=site.name):
                manifest = read_json(site / "assets/data/portfolio-build.json")
                self.assertEqual(len(manifest["pages"]), len(set(manifest["pages"])))
                self.assertEqual({path for path in manifest["pages"] if path.startswith(HUB)},
                                 {*SPORTS_ROUTES, *(f"{HUB}{leaf}/index.html" for leaf in ("Videos", "History", "Records"))})
                self.assertTrue(set(NEW_ROUTES).issubset(manifest["pages"]))
                self.assertTrue({f"{name}/index.html" for name in FIELDS}.issubset(manifest["pages"]))
                self.assertTrue({"Sports/index.html", "Sports/Basketball-Series/index.html", "Sports/Rules/index.html",
                                 "Sports/Creator-Pitch/index.html"}.issubset(manifest["redirects"]))
                self.assertEqual(manifest["basketball"], self.analysis["summary"])

    def test_built_sports_routes_use_correct_shell_depth_and_assets(self):
        for site in self.sites:
            for relative, depth in SPORTS_ROUTES.items():
                with self.subTest(site=site.name, route=relative):
                    page = soup((site / relative).read_text(encoding="utf-8"))
                    prefix = "../" * depth
                    self.assertEqual(page.select_one(".brand")["href"], prefix + "index.html")
                    self.assertEqual(len(page.select("main#main-content")), 1)
                    self.assertEqual(page.select_one('.skip-link')["href"], "#main-content")
                    if relative in DASHBOARDS:
                        styles = [tag["href"] for tag in page.select('link[rel="stylesheet"]')]
                        self.assertGreater(styles.index(prefix + "assets/sports.css"),
                                           styles.index(prefix + "assets/portfolio.css"))
                        scripts = page.select("script[src]")
                        paths = [tag["src"] for tag in scripts]
                        self.assertLess(paths.index(prefix + "assets/data/basketball-analysis.js"),
                                        paths.index(prefix + "assets/sports.js"))
                        self.assertTrue(scripts[paths.index(prefix + "assets/sports.js")].has_attr("defer"))
                    else:
                        self.assertEqual(page.select_one("#MathJax-script")["src"],
                                         prefix + "assets/vendor/mathjax/tex-chtml.js")

    def test_all_new_page_local_links_assets_fragments_and_downloads_resolve(self):
        for site in self.sites:
            for relative in NEW_ROUTES:
                with self.subTest(site=site.name, route=relative):
                    path = site / relative
                    index = page_index(path, self.cache)
                    self.assertEqual(link_problems(site, path, [href for _, _, href in index.references],
                                                   self.cache), [])
                    page = soup(path.read_text(encoding="utf-8"))
                    downloads = page.select("a[download][href]")
                    self.assertTrue(downloads)
                    for link in downloads:
                        target = local_target(site, path, link["href"])
                        self.assertIsNotNone(target, "Downloads must be local, not third-party URLs")
                        self.assertTrue(target[0].is_relative_to(site))
                        self.assertTrue(target[0].is_file())
                        self.assertGreater(target[0].stat().st_size, 0)

    def test_new_pages_have_unique_ids_and_valid_svg_references(self):
        for site in self.sites:
            for relative in ("index.html", *NEW_ROUTES):
                with self.subTest(site=site.name, route=relative):
                    index = page_index(site / relative, self.cache)
                    self.assertEqual([key for key, count in index.ids.items() if count > 1], [])
                    self.assertFalse(any(sum(key == "id" for key, _ in pairs) > 1
                                         for _, _, pairs in index.tags))
                    page = soup((site / relative).read_text(encoding="utf-8"))
                    for element in page.select("svg, svg *"):
                        for attr in ("aria-labelledby", "aria-describedby"):
                            for identifier in element.get(attr, "").split():
                                self.assertIn(identifier, index.ids)
                        for value in element.attrs.values():
                            for identifier in re.findall(r"url\(#([^)]*)\)", str(value)):
                                self.assertIn(identifier, index.ids)

    def test_hub_cards_and_all_twelve_csv_plus_two_json_download_targets(self):
        for site in self.sites:
            hub_path = site / DASHBOARDS[0]
            hub = soup(hub_path.read_text(encoding="utf-8"))
            targets = [local_target(site, hub_path, node["href"])[0].relative_to(site).as_posix()
                       for node in hub.select(".sports-card")]
            self.assertCountEqual(targets, set(SPORTS_ROUTES) - {DASHBOARDS[0]})
            for relative in DASHBOARDS:
                with self.subTest(site=site.name, route=relative):
                    path = site / relative
                    page = soup(path.read_text(encoding="utf-8"))
                    targets = {local_target(site, path, node["href"])[0].relative_to(site).as_posix()
                               for node in page.select(".sports-downloads a[download]")}
                    self.assertEqual(targets, {
                        *(f"assets/data/basketball-{name}.csv" for name in TABLES),
                        "assets/data/basketball-source.json", "assets/data/basketball-analysis.json",
                    })

    def test_twelve_published_csv_files_match_export_rows_and_formula_safe_csv_text(self):
        tables = export_rows(self.analysis)
        self.assertEqual(set(tables), TABLES)
        for site in self.sites:
            directory = site / "assets/data"
            self.assertEqual({path.name for path in directory.glob("basketball-*.csv")},
                             {f"basketball-{name}.csv" for name in TABLES})
            for name, rows in tables.items():
                with self.subTest(site=site.name, table=name):
                    data = (directory / f"basketball-{name}.csv").read_bytes()
                    self.assertEqual(data, publishing.csv_text(rows).encode("utf-8"))
                    # Independent spreadsheet-cell check, including negative
                    # numeric margins which must NOT acquire an apostrophe.
                    parsed = list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))
                    self.assertEqual(len(parsed), len(rows))
                    for raw, exported in zip(rows, parsed, strict=True):
                        for key, value in raw.items():
                            expected = "" if value is None else str(value)
                            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                                expected = "'" + value
                            self.assertEqual(exported[key], expected)

    def test_raw_json_is_lossless_and_analysis_js_matches_json_with_explicit_opt_in(self):
        expected = {**self.analysis, "sourceDownloadAvailable": True}
        for site in self.sites:
            with self.subTest(site=site.name):
                directory = site / "assets/data"
                self.assertEqual(read_json(directory / "basketball-source.json"), self.raw)
                enriched = read_json(directory / "basketball-analysis.json")
                self.assertEqual(enriched, expected)
                script = (directory / "basketball-analysis.js").read_text(encoding="utf-8")
                self.assertTrue(script.startswith("window.BASKETBALL_ANALYSIS="))
                self.assertTrue(script.endswith(";"))
                self.assertNotIn("</script", script.lower())
                self.assertEqual(json.loads(script.removeprefix("window.BASKETBALL_ANALYSIS=")
                                           .removesuffix(";")), enriched)

    def test_enriched_download_keeps_all_raw_games_orders_and_missing_time_statuses(self):
        for site in self.sites:
            with self.subTest(site=site.name):
                enriched = read_json(site / "assets/data/basketball-analysis.json")
                self.assertEqual(len(enriched["series"]), 13)
                self.assertEqual(sum(len(item["games"]) for item in enriched["series"]), 73)
                for raw, item in zip(self.raw["series"], enriched["series"], strict=True):
                    self.assertEqual(item["order"], raw["order"])
                    self.assertEqual(item["games"], raw["games"])
                    for key in ("id", "date", "sourceDate", "session"):
                        self.assertEqual(item[key], raw[key])
                    self.assertFalse({"timestamp", "startTime", "endTime"}.intersection(item))
                    for game, row in zip(raw["games"], item["rounds"], strict=True):
                        self.assertEqual({key: row[key] for key in game}, game)
                        self.assertFalse({"timestamp", "startTime", "endTime"}.intersection(row))
                        self.assertEqual(row["score"]["raw"], game.get("scoreRaw"))
                        if game.get("timeRaw") in ("TBD", "N/A"):
                            self.assertEqual(row["time"]["raw"], game["timeRaw"])
                            self.assertIsNone(row["time"]["seconds"])
                            self.assertEqual(row["time"]["status"],
                                             "pending" if game["timeRaw"] == "TBD" else "not-recorded")
                timing = enriched["timing"]
                self.assertEqual({entry["status"] for entry in timing["missingEntries"]},
                                 {"pending", "not-recorded"})
                self.assertTrue(timing["notPlayedEntries"])
                for entry in timing["notPlayedEntries"]:
                    self.assertEqual(entry["status"], "not-played")
                    self.assertIs(entry["played"], False)
                    self.assertIsNone(entry["seconds"])

    def test_published_home_and_sports_assets_match_current_producers(self):
        for site in self.sites:
            with self.subTest(site=site.name):
                self.assertEqual((site / "index.html").read_text(encoding="utf-8"), publishing.home_html())
                for name in ("portfolio.css", "portfolio.js", "sports.css", "sports.js"):
                    self.assertEqual((site / "assets" / name).read_bytes(),
                                     (ROOT / "site_content/web" / name).read_bytes())

    def test_about_resume_physics_link_to_work_report_with_correct_depth(self):
        for site in self.sites:
            for relative in ("About/index.html", "About/Resume/index.html", PHYSICS):
                with self.subTest(site=site.name, route=relative):
                    path = site / relative
                    page = soup(path.read_text(encoding="utf-8"))
                    targets = [local_target(site, path, node["href"]) for node in page.select("main a[href]")]
                    self.assertIn(((site / REPORT).resolve(), ""), targets)


class BasketballCsvBoundaryTests(unittest.TestCase):
    def test_real_export_shape_protects_synthetic_formula_notes_without_mutating_json(self):
        data = load_basketball(ROOT)
        original = deepcopy(data)
        # Change only this in-memory copy; no fabricated game is written to the log.
        values = ["=1+1", "  +SUM(A1:A2)", "\t@SUM(A1:A2)", "-1+2", 'ordinary, "quoted"\nnote']
        for round_, value in zip(data["series"][0]["rounds"], values):
            round_["note"] = value
        before_export = deepcopy(data)
        rows = export_rows(data)["rounds"]
        encoded = publishing.csv_text(rows)
        parsed = list(csv.DictReader(io.StringIO(encoded, newline="")))
        self.assertEqual([row["note"] for row in parsed[:len(values)]],
                         ["'" + value for value in values[:-1]] + [values[-1]])
        self.assertEqual(data, before_export)
        self.assertEqual([row["note"] for row in rows[:len(values)]], values)
        self.assertEqual(json.loads(publishing.safe_json(data)), before_export)
        self.assertEqual(load_basketball(ROOT), original)


class DocumentPublishingIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = protected_fingerprints()
        temporary = tempfile.TemporaryDirectory(prefix="sports-publishing-tests-")
        cls.addClassCleanup(temporary.cleanup)
        cls.site = Path(temporary.name) / "site"
        cls.results = {}
        real_convert, real_report = publishing.convert_document, publishing.report_result

        def convert(*args, **kwargs):
            result = real_convert(*args, **kwargs)
            cls.results[args[2].name] = result
            return result

        def report(*args, **kwargs):
            result = real_report(*args, **kwargs)
            cls.results["work-term-report"] = result
            return result

        # Exercise the actual gate once per document. Subsequent checks use
        # hashes, not another expensive converter or PDF validation invocation.
        with patch.object(publishing, "convert_document", side_effect=convert), \
             patch.object(publishing, "report_result", side_effect=report), \
             patch.object(publishing, "copy_verified_pdf", wraps=publishing.copy_verified_pdf) as verified:
            for key, (route, _, _) in DOCUMENTS.items():
                html = (publishing.work_report_html(ROOT, cls.site) if key == "work-term-report"
                        else publishing.sports_document_html(ROOT, cls.site, key, route))
                publishing.write(cls.site / route, html)
            cls.verified_calls = verified.call_args_list
        cls.sites = [cls.site, *built_sites()]

    def documents(self):
        for site in self.sites:
            for key, (route, _, _) in DOCUMENTS.items():
                path = site / route
                yield site, key, path, soup(path.read_text(encoding="utf-8"))

    def test_renderer_writes_leave_originals_caches_records_and_real_sites_unchanged(self):
        self.assertEqual(protected_fingerprints(), self.before)

    def test_publishers_call_real_verified_pdf_gate_once_per_document_with_root(self):
        self.assertEqual(len(self.verified_calls), 3)
        self.assertEqual([call.args for call in self.verified_calls], [
            (ROOT, key, self.site / "assets/documents" / key) for key in DOCUMENTS
        ])
        self.assertTrue(all(not call.kwargs for call in self.verified_calls))

    def test_converter_metadata_and_rendered_report_sports_counts(self):
        self.assertEqual(set(self.results), set(DOCUMENTS))
        for key, result in self.results.items():
            with self.subTest(document=key):
                self.assertEqual(result["warnings"], [])
                self.assertEqual(result["image_count"], DOCUMENTS[key][2])
        report = self.results["work-term-report"]
        self.assertEqual(len(report["headings"]), 37)
        self.assertEqual(report["equation_count"], 96)
        for site, key, _, page in self.documents():
            with self.subTest(site=site.name, document=key):
                self.assertEqual(len(page.select(".tex-paper img")), DOCUMENTS[key][2])
                self.assertFalse(page.select(".tex-conversion-warnings, .tex-unsupported"))
                if key == "work-term-report":
                    self.assertEqual(len(page.select("#reader-toc a")), 37)
                    self.assertEqual(len(page.select(".tex-paper .math.display")), 96)
                    self.assertEqual(len(page.select(".tex-paper figure")), 7)
                    self.assertEqual(len(page.select(".tex-paper table")), 1)

    def test_reader_headings_toc_ids_and_local_fragments_are_consistent(self):
        for site, key, path, page in self.documents():
            with self.subTest(site=site.name, document=key):
                ids = Counter(node["id"] for node in page.select("[id]"))
                self.assertTrue(all(count == 1 for count in ids.values()))
                headings = page.select(".tex-paper h1, .tex-paper h2, .tex-paper h3, "
                                       ".tex-paper h4, .tex-paper h5, .tex-paper h6")
                self.assertEqual([unquote(node["href"])[1:] for node in page.select("#reader-toc a")],
                                 [node["id"] for node in headings])
                for node in page.select('a[href^="#"]'):
                    self.assertIn(unquote(node["href"])[1:], ids)
                for node in page.select("a[download][href], .tex-paper img[src]"):
                    target = local_target(site, path, node.get("href", node.get("src")))
                    self.assertIsNotNone(target)
                    self.assertTrue(target[0].is_relative_to(site))
                    self.assertTrue(target[0].is_file())

    def test_pdf_links_resolve_to_exact_cache_bytes_and_manifest_sha256(self):
        for site, key, path, page in self.documents():
            with self.subTest(site=site.name, document=key):
                links = page.select('a[download][href$=".pdf"]')
                self.assertEqual(len(links), 1)
                published, fragment = local_target(site, path, links[0]["href"])
                self.assertEqual(published, (site / "assets/documents" / key / "document.pdf").resolve())
                self.assertEqual(fragment, "")
                data = published.read_bytes()
                cached = (PDF_CACHE / f"{key}.pdf").read_bytes()
                manifest = read_json(PDF_CACHE / f"{key}.json")
                self.assertTrue(data.startswith(b"%PDF-"))
                self.assertEqual(data, cached)
                self.assertEqual(sha256(data).hexdigest(), manifest["pdfSha256"])

    def test_pdf_manifest_input_hashes_match_exact_public_sources_and_images(self):
        for key, (_, relative, _) in DOCUMENTS.items():
            with self.subTest(document=key):
                manifest = read_json(PDF_CACHE / f"{key}.json")
                self.assertEqual(manifest["schemaVersion"], 1)
                self.assertEqual(manifest["key"], key)
                self.assertEqual(manifest["inputs"]["source"], {
                    "path": relative, "sha256": sha256((ROOT / relative).read_bytes()).hexdigest(),
                })
                self.assertEqual(manifest["inputs"]["images"], [
                    {"archive": name, "path": path.relative_to(ROOT).as_posix(),
                     "sha256": sha256(path.read_bytes()).hexdigest()}
                    for name, path in original_images(key)
                ])

    def test_source_zips_contain_exact_source_and_original_image_paths_only(self):
        for site, key, path, page in self.documents():
            with self.subTest(site=site.name, document=key):
                links = page.select('a[download][href$=".zip"]')
                self.assertEqual(len(links), 1)
                archive_path, _ = local_target(site, path, links[0]["href"])
                assets = site / "assets/documents" / key
                self.assertEqual(archive_path, (assets / "source-bundle.zip").resolve())
                source = ROOT / DOCUMENTS[key][1]
                images = original_images(key)
                self.assertEqual(len(images), DOCUMENTS[key][2])
                self.assertEqual(read_json(assets / "source-images.json"), [
                    {"archive": name, "asset": PurePosixPath(name).name} for name, _ in images
                ])
                with zipfile.ZipFile(archive_path) as archive:
                    self.assertIsNone(archive.testzip())
                    names = archive.namelist()
                    self.assertEqual(len(names), len(set(names)))
                    self.assertCountEqual(names, [source.name, *(name for name, _ in images)])
                    # Hash comparisons do not print source text on a failure.
                    self.assertEqual(sha256(archive.read(source.name)).digest(), sha256(source.read_bytes()).digest())
                    self.assertEqual(sha256((assets / source.name).read_bytes()).digest(), sha256(source.read_bytes()).digest())
                    for name, original in images:
                        expected = sha256(original.read_bytes()).digest()
                        self.assertEqual(sha256(archive.read(name)).digest(), expected)
                        self.assertEqual(sha256((assets / PurePosixPath(name).name).read_bytes()).digest(), expected)
                    self.assertFalse(any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                                         or "\\" in name or ":" in name for name in names))
                    self.assertFalse(any(name.lower().endswith(".cls") or "liammcgrath_resume" in name.lower()
                                         or name.startswith("WKRPT400/") for name in names))

    def test_rendered_images_resolve_to_the_original_image_bytes(self):
        for site, key, path, page in self.documents():
            with self.subTest(site=site.name, document=key):
                images = page.select(".tex-paper img")
                originals = original_images(key)
                self.assertEqual(len(images), len(originals))
                for node, (_, original) in zip(images, originals, strict=True):
                    target, _ = local_target(site, path, node["src"])
                    self.assertEqual(sha256(target.read_bytes()).digest(), sha256(original.read_bytes()).digest())

    def test_public_report_edition_metadata_is_undated_and_audit_matches_canonical(self):
        canonical = read_json(ROOT / "notebook_sources/work-report/manifest.json")
        for site in self.sites:
            with self.subTest(site=site.name):
                manifest = read_json(site / "assets/documents/work-term-report/edition-manifest.json")
                self.assertEqual(manifest, canonical)
                self.assertIsNone(manifest["edition"]["completionDate"])
                self.assertEqual(manifest["edition"]["dateStatus"], "undated historical 3B report")
                for flag in ("originalFolderDistributed", "templateClassDistributed", "originalCommentsDistributed"):
                    self.assertIs(manifest["privacy"][flag], False)
                page = soup((site / REPORT).read_text(encoding="utf-8"))
                byline = page.select_one(".reader-top p:not(.eyebrow)").get_text()
                self.assertIn("Completion date unverified", byline)
                self.assertNotRegex(byline, r"\b(?:19|20)\d{2}\b")

    def test_public_text_metadata_and_zip_members_have_no_private_report_values(self):
        # Values exist only in ephemeral memory and never enter failure messages,
        # subTest labels, snapshots, or an assertion's repr of expected/actual.
        private = _private_values((ROOT / "WKRPT400/main.tex").read_text(encoding="utf-8-sig"))
        self.assertTrue(private, "The privacy check must inspect the original administrative fields")
        for site in self.sites:
            for key, (route, _, _) in DOCUMENTS.items():
                with self.subTest(site=site.name, document=key):
                    _assert_public([(site / route).read_bytes()], private)
                    assets = site / "assets/documents" / key
                    for artifact in assets.rglob("*"):
                        if not artifact.is_file():
                            continue
                        if artifact.suffix.lower() == ".zip":
                            with zipfile.ZipFile(artifact) as archive:
                                _assert_public([archive.read(name) for name in archive.namelist()], private)
                        elif artifact.suffix.lower() != ".pdf":
                            _assert_public([artifact.read_bytes()], private)
                    _assert_public([(PDF_CACHE / f"{key}.json").read_bytes()], private)
            if site != self.site:
                _assert_public([(site / relative).read_bytes() for relative in (
                    "index.html", *DASHBOARDS,
                    "About/index.html", "About/Resume/index.html", PHYSICS,
                )], private)

    def test_reader_page_outputs_are_deterministic_without_rerendering_or_revalidating_pdf(self):
        # Feed the captured conversion result back into the pure page composer;
        # the full publishing rebuild already has coverage in test_publishing.
        for key, (route, _, _) in DOCUMENTS.items():
            with self.subTest(document=key):
                result = self.results[key]
                before = deepcopy(result)
                options = {"pdf": "../../assets/documents/" + key + "/document.pdf"}
                first = publishing.document_html(result, key, 2, "", "source-bundle.zip", **options)
                self.assertEqual(first, publishing.document_html(result, key, 2, "", "source-bundle.zip", **options))
                self.assertEqual(result, before)
                for site in self.sites[1:]:
                    self.assertEqual((site / route).read_bytes(), (self.site / route).read_bytes())


if __name__ == "__main__":
    unittest.main()