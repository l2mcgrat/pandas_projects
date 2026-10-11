"""Sports frontend contracts. No publisher calls, writes, or network access.

Run: python -B -m unittest site_content.tests.test_sports_views
The source engine has its own independent validation/accounting tests.
"""

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from site_content.basketball import analyze_series, export_rows, load_basketball
from site_content.sports_views import basketball_body, sports_body, sports_net_svg


ROOT = Path(__file__).resolve().parents[2]
TABLES = {
    "summary", "series", "rounds", "challenges", "transitions", "byPicker",
    "conditionalNextChallenge", "transitionMatrix", "trajectories",
    "seriesLengths", "comebacks", "timing",
}


def soup(body):
    return BeautifulSoup(body, "html.parser")


class SportsViewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_basketball(ROOT)
        cls.raw = json.loads((ROOT / "records/basketball/series.json").read_text(encoding="utf-8"))

    def test_two_shell_free_single_main_apis(self):
        for view in (sports_body, basketball_body):
            with self.subTest(view=view.__name__):
                doc = soup(view(self.data))
                self.assertEqual(len(doc.find_all("main")), 1)
                self.assertEqual(len(doc.find_all("h1")), 1)
                self.assertEqual(doc.main["id"], "main-content")
                self.assertTrue({"collection-page", "sports-page"}.issubset(doc.main["class"]))
                self.assertIsNone(doc.find(["html", "head", "body", "script", "link", "iframe"]))
                self.assertEqual(len(doc.find_all("main", recursive=False)), 1)

    def test_deep_nonmutation_and_determinism(self):
        before = deepcopy(self.data)
        for view in (sports_body, basketball_body):
            self.assertEqual(view(self.data), view(self.data))
            self.assertEqual(self.data, before)

    def test_all_ids_are_unique_and_local_anchors_exist(self):
        for view in (sports_body, basketball_body):
            doc = soup(view(self.data))
            ids = [node["id"] for node in doc.select("[id]")]
            self.assertEqual(len(ids), len(set(ids)))
            for link in doc.select('a[href^="#"]'):
                self.assertIn(link["href"][1:], ids)
            for node in doc.select("[aria-labelledby]"):
                for identifier in node["aria-labelledby"].split():
                    self.assertIn(identifier, ids)

    def test_dashboard_baseline_comes_from_analysis(self):
        doc = soup(basketball_body(self.data))
        self.assertEqual(doc.select_one("#sports-metric-series").text, "13")
        self.assertEqual(doc.select_one("#sports-metric-rounds").text, "73")
        self.assertEqual(doc.select_one("#sports-metric-streak").text, "11")
        self.assertEqual(doc.select_one("#sports-metric-best").text, "1:22")
        score = doc.select_one(".sports-scoreboard")
        self.assertEqual([node.text for node in score.select(".sports-score strong")], ["12", "1"])
        self.assertIn("L 50", score.get_text(" ", strip=True))
        self.assertIn("O 23", score.get_text(" ", strip=True))

    def test_counts_are_not_hardcoded_to_current_fixture(self):
        raw = deepcopy(self.raw)
        raw["series"] = raw["series"][:1]
        data = analyze_series(raw)
        doc = soup(basketball_body(data))
        self.assertEqual(doc.select_one("#sports-metric-series").text, "1")
        self.assertEqual(doc.select_one("#sports-metric-rounds").text, "6")
        self.assertEqual(doc.select_one("#sports-metric-streak").text, "1")
        self.assertEqual(doc.select_one("#sports-metric-best").text, "3:35")
        self.assertIn("2026-08-07", doc.select_one("#sports-selected-title").text)
        self.assertNotIn("2026-09-10", doc.get_text())

    def test_empty_log_and_partial_data_are_informative(self):
        raw = deepcopy(self.raw)
        raw["series"] = []
        for data in (analyze_series(raw), {}, {"summary": {}, "timing": {}}, None):
            for view in (sports_body, basketball_body):
                with self.subTest(view=view.__name__, data=data):
                    html = view(data)
                    doc = soup(html)
                    self.assertEqual(len(doc.find_all("main")), 1)
                    self.assertIn("No completed", doc.get_text())
                    self.assertNotRegex(html, r"(?:NaN|Infinity|inf)%")
                    self.assertIsNotNone(doc.find("a", href=re.compile("Rules/index.html")))

    def test_zero_second_valid_time_is_not_missing(self):
        raw = deepcopy(self.raw)
        raw["series"] = raw["series"][:1]
        raw["series"][0]["games"][4]["timeRaw"] = "00:00"
        doc = soup(basketball_body(analyze_series(raw)))
        self.assertEqual(doc.select_one("#sports-metric-best").text, "0:00")
        self.assertEqual(len(doc.select("#sports-timing-chart .timing-point")), 1)
        self.assertIn("00:00", doc.select_one("#sports-timing-table").text)
        self.assertNotIn("TBD", doc.select_one(".sports-missing").text)

    def test_raw_source_xss_escaped_as_text(self):
        payload = '<img src=x onerror="alert(1)"><script>alert(2)</script> & "\''
        raw = deepcopy(self.raw)
        raw["sourceTitle"] = payload
        raw["provenance"]["source"] = payload
        raw["series"][4]["note"] = payload
        raw["series"][4]["games"][6]["scoreRaw"] = payload  # Bump is uninterpreted.
        raw["series"][4]["games"][6]["note"] = payload
        data = analyze_series(raw)
        data["caveats"].append(payload)
        data["challenges"][0]["label"] = payload
        before = deepcopy(data)
        for view in (sports_body, basketball_body):
            html = view(data)
            doc = soup(html)
            self.assertIsNone(doc.find(["script", "img", "iframe"]))
            for node in doc.find_all(True):
                self.assertFalse(any(key.lower().startswith("on") for key in node.attrs))
            self.assertEqual(data, before)
        self.assertIn(payload, soup(basketball_body(data)).get_text())

    def test_dynamic_attribute_values_cannot_break_out(self):
        data = deepcopy(self.data)
        data["series"][0]["id"] = '\"><svg onload="alert(1)">?&=#'
        data["series"][0]["date"] = '\"><input autofocus onfocus="alert(2)">'
        data["series"][0]["order"] = '\" onmouseover="alert(3)'
        data["series"][0]["winner"] = '\" style="color:red'
        data["source"]["path"] = "javascript:alert(4)"
        doc = soup(basketball_body(data))
        for node in doc.find_all(True):
            self.assertFalse(any(key.startswith("on") for key in node.attrs))
        link = doc.select_one("a[data-select-series]")
        self.assertEqual(parse_qs(urlsplit(link["href"]).query)["series"], [data["series"][0]["id"]])
        self.assertFalse(any(a["href"].startswith("javascript:") for a in doc.select("a[href]")))

    def test_nonfinite_chart_values_never_become_svg_or_css(self):
        data = deepcopy(self.data)
        data["challenges"][0]["wins"]["L"] = float("nan")
        data["transitionMatrix"]["counts"][0][0] = float("inf")
        data["timing"]["entries"][0]["seconds"] = float("nan")
        data["timing"]["bestOverall"]["seconds"] = float("inf")
        doc = soup(basketball_body(data))
        for node in doc.find_all(True):
            for value in node.attrs.values():
                self.assertNotRegex(str(value), r"(?i)\b(?:nan|infinity|inf)\b")

    def test_depth_correct_routes_and_all_twelve_csv_downloads(self):
        self.assertEqual(set(export_rows(self.data)), TABLES)
        hub = "Sports-and-Entertainment/Series-Hub/"
        for view, route in ((sports_body, hub + "index.html"), (basketball_body, hub + "Analytics/index.html")):
            doc = soup(view(self.data))
            base = "https://example.test/" + route
            urls = [urlsplit(urljoin(base, a["href"])) for a in doc.select("a[href]")]
            paths = {url.path for url in urls}
            for target in (f"/{hub}Rules/index.html", f"/{hub}Creator-Petition/index.html", "/assets/data/basketball-analysis.json"):
                self.assertIn(target, paths)
            self.assertEqual({path for path in paths if path.endswith(".csv")}, {f"/assets/data/basketball-{key}.csv" for key in TABLES})
            self.assertTrue(all(url.hostname == "example.test" for url in urls))
            self.assertFalse(any(path.endswith(".pdf") or path.endswith(".tex") for path in paths))
            self.assertNotIn("/assets/data/basketball-source.json", paths)

    def test_raw_source_download_requires_explicit_parent_opt_in(self):
        data = deepcopy(self.data)
        data["sourceDownloadAvailable"] = True
        for view, prefix in ((sports_body, "../../"), (basketball_body, "../../../")):
            doc = soup(view(data))
            link = doc.find("a", href=prefix + "assets/data/basketball-source.json")
            self.assertIsNotNone(link)
            self.assertTrue(link.has_attr("download"))

    def test_hub_cards_pending_and_original_art(self):
        doc = soup(sports_body(self.data))
        self.assertEqual([a["href"] for a in doc.select(".sports-card")], ["Analytics/index.html", "Rules/index.html", "Creator-Petition/index.html"])
        self.assertIn("pending", doc.select_one(".sports-pending").get_text().lower())
        self.assertNotIn("team results", doc.select_one(".sports-hero").text.lower())
        self.assertIsNone(doc.find(["img", "video", "audio"]))
        art = soup(sports_net_svg()).svg
        self.assertEqual(art.get("role"), "img")
        self.assertIsNotNone(art.title)
        self.assertIsNotNone(art.desc)
        self.assertIsNone(art.find(id=True))

    def test_sequence_grid_preserves_all_orders_seven_slots(self):
        doc = soup(basketball_body(self.data))
        rows = doc.select("#sports-series-table tbody tr")
        self.assertEqual(len(rows), 13)
        for row, original in zip(rows, self.raw["series"]):
            self.assertEqual(row.code.text, original["order"])
            self.assertEqual(len(row.select(".round-chip")), 7)
            self.assertEqual("".join(node.text for node in row.select(".round-chip:not(.unused)")), original["order"])
        self.assertIn("source entry order", doc.select_one("#sports-series-table caption").text)

    def test_all_seven_challenge_denominators_and_percentages(self):
        doc = soup(basketball_body(self.data))
        bars = doc.select(".sports-challenge")
        self.assertEqual(len(bars), 7)
        for bar, record in zip(bars, self.data["challenges"]):
            self.assertEqual(bar["data-challenge"], record["id"])
            for who in ("L", "O"):
                self.assertIn(f"{who} {record['wins'][who]}/{record['played']}", bar.text)
                self.assertIn(f"{100 * record['wins'][who] / record['played']:.1f}%", bar.text)
        self.assertIn("not ability estimates", doc.get_text())

    def test_picker_conditioning_composition_matrix_and_choice_rows(self):
        doc = soup(basketball_body(self.data))
        text = doc.select_one("#picker-patterns").get_text(" ", strip=True)
        for value in ("28 / 38 holds", "7 / 22 holds", "35/60 holds", "25/60 switches", "73.7%", "31.8%"):
            self.assertIn(value, text)
        matrix = doc.select_one("#sports-transition-matrix")
        self.assertEqual(len(matrix.select("tbody tr")), 7)
        self.assertEqual(len(matrix.select("tbody td")), 49)
        self.assertEqual(sum(int(cell.text) for cell in matrix.select("tbody td")), 60)
        self.assertEqual([row.th.text for row in matrix.select("tbody tr")], [row["label"] for row in self.data["challengeDefinitions"]])
        choices = doc.select("#sports-choice-table tbody tr")
        self.assertEqual(len(choices), 14)
        for node, row in zip(choices, self.data["conditionalNextChallenge"]):
            self.assertIn(f"{row['countPicks']}/{row['pickerTotal']}", node.text)
            self.assertIn(f"{row['countWins']}/{row['countPicks']}", node.text)
        self.assertIn("different inferred pickers", text)
        self.assertIn("no causal", text)

    def test_timing_numeric_points_separate_missing_and_unplayed(self):
        doc = soup(basketball_body(self.data))
        chart = doc.select_one("#sports-timing-chart")
        self.assertEqual(len(chart.select(".timing-point")), 10)
        self.assertEqual(len(chart.select(".sports-best-ring")), 1)
        self.assertIn("Best 1:22", chart.text)
        self.assertIsNone(chart.find("polyline"))
        self.assertEqual(len(doc.select("#sports-timing-table tbody tr")), 13)
        missing = doc.select_one(".sports-missing")
        self.assertEqual(len(missing.select("li")), 3)
        self.assertIn("TBD", missing.text)
        self.assertIn("N/A", missing.text)
        self.assertIn("not played", missing.text)
        self.assertIn("Owen: 3:13", doc.get_text())
        self.assertIn("assistance is unknown", doc.get_text())
        self.assertIn("114 inches", doc.get_text())

    def test_default_decider_game_seven_and_source_details(self):
        doc = soup(basketball_body(self.data))
        option = doc.select_one("#sports-series-select option[selected]")
        self.assertEqual(option["value"], "2026-09-10-1")
        self.assertEqual(doc.select_one("#sports-round-range")["min"], "0")
        self.assertEqual(doc.select_one("#sports-round-range")["max"], "7")
        self.assertEqual(doc.select_one("#sports-round-range")["value"], "7")
        self.assertIn("L 4 – O 3", doc.select_one("#sports-round-score").text)
        self.assertEqual(len(doc.select("#sports-round-list li")), 7)
        self.assertEqual(doc.select_one('#sports-round-list [aria-current="step"]')["id"], "sports-round-7")
        self.assertIn("Unrecorded · opening round", doc.select_one("#sports-round-1").text)
        self.assertIn("7:3", doc.select_one("#sports-round-3").text)
        self.assertIn("TBD", doc.select_one("#sports-round-5").text)
        hero = doc.select_one(".sports-hero a[href]")
        self.assertEqual(parse_qs(urlsplit(hero["href"]).query), {"series": ["2026-09-10-1"], "round": ["7"]})

    def test_controls_disabled_until_hydrated_and_static_accessibility(self):
        doc = soup(basketball_body(self.data))
        for identifier in ("sports-series-controls", "sports-round-controls", "sports-log-controls", "sports-picker-controls"):
            self.assertTrue(doc.find(id=identifier).has_attr("disabled"))
        for node in doc.find_all(["select", "input"]):
            self.assertIsNotNone(doc.find("label", attrs={"for": node["id"]}))
        for table in doc.find_all("table"):
            self.assertIsNotNone(table.caption)
            self.assertIn("sports-table-wrap", table.parent.get("class", []))
            self.assertEqual(table.parent.get("tabindex"), "0")
        for svg in doc.find_all("svg"):
            self.assertEqual(svg.get("role"), "img")
            self.assertIsNotNone(svg.title)
            self.assertIsNotNone(svg.desc)
        self.assertEqual(doc.select_one("#play-by-play")["tabindex"], "-1")
        self.assertIn("Filters affect this log only", doc.get_text())

    def test_frontend_safety_dependencies_and_motion_contract(self):
        js = (ROOT / "site_content/web/sports.js").read_text(encoding="utf-8")
        css = (ROOT / "site_content/web/sports.css").read_text(encoding="utf-8")
        self.assertNotRegex(js, r"\b(?:eval|fetch|XMLHttpRequest)\s*\(|innerHTML|outerHTML|insertAdjacentHTML|document\.write")
        self.assertIn("window.BASKETBALL_ANALYSIS", js)
        self.assertIn("createElementNS", js)
        self.assertIn("textContent", js)
        self.assertIn("replaceState", js)
        self.assertIn("popstate", js)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("animation:none!important", css)
        self.assertNotIn("infinite", css)
        self.assertNotRegex(css, r"(?:^|\n)\s*(?:body|html|:root)\b")
        self.assertNotIn("@import", css)
        self.assertIn(".sports-page .button.primary", css)

    @unittest.skipUnless(shutil.which("node"), "Node is optional for frontend syntax checking")
    def test_javascript_syntax(self):
        result = subprocess.run([shutil.which("node"), "--check", str(ROOT / "site_content/web/sports.js")], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()