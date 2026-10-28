"""Health logs: strict parsing, flagged arithmetic, labelled dream reading, safe dashboards."""

from pathlib import Path
import re
import unittest

from bs4 import BeautifulSoup

from site_content.athletics import load_athletics
from site_content.health import DAILY_TARGET_DEFICIT, OCTOBER_BMR, health_rows, load_health, parse_diet, parse_sleep
from site_content.health_views import diet_body, sleep_body

ROOT = Path(__file__).resolve().parents[2]


class SleepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sleep = load_health(ROOT)["sleep"]

    def test_nights_hours_and_recall(self):
        summary = self.sleep["summary"]
        self.assertEqual((summary["nights"], summary["dreams"]), (14, 15))
        self.assertEqual((summary["firstDate"], summary["lastDate"]), ("2026-10-05", "2026-10-18"))
        nights = {night["date"]: night for night in self.sleep["nights"]}
        self.assertEqual(nights["2026-10-05"]["hours"], 6.5)
        self.assertEqual(len(nights["2026-10-05"]["dreams"]), 2)
        # "No dreams recorded" stays a deliberate entry, not a parse gap.
        self.assertTrue(nights["2026-10-16"]["noDreamsWritten"])
        self.assertEqual(nights["2026-10-16"]["dreams"], [])
        self.assertEqual(summary["nightsWithDreams"], 11)

    def test_dream_reading_is_lexicon_based_and_keeps_text_as_written(self):
        first = self.sleep["nights"][0]["dreams"][0]
        self.assertIn("Moon trip with Owen", first["text"])
        self.assertIn("frmlok", first["text"], "typos stay as written")
        self.assertIn("compound", first["polarity"])
        motifs = {m["motif"] for m in self.sleep["motifs"]}
        self.assertIn("Exploration & other worlds", motifs)
        self.assertIn("Pursuit, escape & danger", motifs)
        for entry in self.sleep["motifs"]:
            self.assertTrue(entry["cues"], "every reported motif names the words that matched")
        chased = next(m for m in self.sleep["motifs"] if m["motif"] == "Pursuit, escape & danger")
        self.assertIn("2026-10-05", chased["nights"])

    def test_malformed_sleep_log_stops(self):
        with self.assertRaisesRegex(ValueError, "duration"):
            parse_sleep("Sleep_and_Dream_Log\n10/5/2026\nA dream before any hours line")
        with self.assertRaisesRegex(ValueError, "date"):
            parse_sleep("Sleep_and_Dream_Log\n7hrs")


class DietTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diet = load_health(ROOT)["diet"]

    def test_deficits_are_computed_and_written_values_flagged(self):
        days = {day["date"]: day for day in self.diet["days"]}
        oct5 = days["2026-10-05"]
        self.assertEqual((oct5["expenditure"], oct5["consumption"], oct5["deficit"]), (3930, 2962, 968))
        self.assertEqual(oct5["writtenNet"], 948)
        self.assertTrue(oct5["netMismatch"], "948 written vs 968 computed is flagged, not corrected")
        self.assertEqual(days["2026-10-06"]["deficit"], -150)  # a gain stays negative
        self.assertEqual(days["2026-10-15"]["expenditureNote"], "16k walk, high NEAT, cold")
        self.assertEqual(oct5["activity"], 3930 - OCTOBER_BMR)
        summary = self.diet["summary"]
        self.assertEqual(summary["days"], 15)
        self.assertEqual(summary["totalDeficit"], sum(day["deficit"] for day in self.diet["days"]))
        self.assertEqual(summary["targetDeficit"], DAILY_TARGET_DEFICIT)

    def test_weekly_summaries_checked_against_computed_totals(self):
        weeks = {week["weekOf"]: week for week in self.diet["weeks"]}
        self.assertEqual(weeks["2026-10-05"]["writtenLoss"], 4079)
        self.assertEqual(weeks["2026-10-05"]["computedLoss"], 4079)
        self.assertEqual(weeks["2026-10-12"]["writtenLoss"], 4120)
        self.assertNotEqual(weeks["2026-10-12"]["computedLoss"], 4120)

    def test_malformed_diet_log_stops(self):
        with self.assertRaisesRegex(ValueError, "no Total"):
            parse_diet("Diet and Calorie Tracking\n10/5/2026\nBreakfast - 3/1/28g Shake")
        with self.assertRaisesRegex(ValueError, "unreadable"):
            parse_diet("Diet and Calorie Tracking\n10/5/2026\nSecond Breakfast - 3/1/28g Shake")


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.health = load_health(ROOT)
        cls.athletics = load_athletics(ROOT)

    def test_dashboards_are_static_escaped_and_honest(self):
        pages = {
            "sleep": sleep_body(self.health["sleep"]),
            "diet": diet_body(self.health["diet"], self.athletics),
        }
        for key, markup in pages.items():
            with self.subTest(page=key):
                page = BeautifulSoup(markup, "html.parser")
                self.assertIsNone(page.find("script"))
                ids = [tag["id"] for tag in page.find_all(id=True)]
                self.assertEqual(len(ids), len(set(ids)))
                for svg in page.select("svg.sports-chart"):
                    for ref in svg["aria-labelledby"].split():
                        self.assertIn(ref, ids)
                self.assertTrue(page.select("table"))
                self.assertFalse(re.search(r"\b(?:nan|inf)\b", markup))
                notes = page.select_one(f"#{key}-update")
                self.assertIn(self.health[key]["source"]["path"], notes.get_text())

    def test_sleep_page_keeps_the_disclaimer_and_dream_text(self):
        markup = sleep_body(self.health["sleep"])
        self.assertIn("not psychoanalysis", markup)
        self.assertIn("For fun, not Freud", markup)
        page = BeautifulSoup(markup, "html.parser")
        self.assertEqual(len(page.select(".dream-card")), self.health["sleep"]["summary"]["dreams"])

    def test_diet_page_charts_both_axes_and_training_days(self):
        markup = diet_body(self.health["diet"], self.athletics)
        page = BeautifulSoup(markup, "html.parser")
        chart = page.select_one("#diet-balance-svg-title")
        self.assertIn("left axis", chart.find_parent("svg").find("desc").get_text())
        self.assertTrue(page.select(".diet-target"))
        self.assertTrue(page.select(".diet-deficit.is-gain"), "gain days render as gain bars")
        table = page.select_one("#diet-table").get_text()
        self.assertIn("Tempo 4.6 km", table)
        self.assertIn("Lift · Chest & Abs", table)
        self.assertIn("Rest day", table)
        self.assertIn(str(OCTOBER_BMR), markup)

    def test_dream_text_is_escaped(self):
        health = load_health(ROOT)
        health["sleep"]["nights"][0]["dreams"][0]["text"] = '<script>alert(1)</script>'
        markup = sleep_body(health["sleep"])
        self.assertNotIn("<script>alert", markup)


if __name__ == "__main__":
    unittest.main()
