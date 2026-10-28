"""Athletics logs: strict parsing, honest summaries and safe dashboards."""

from pathlib import Path
import re
import shutil
import tempfile
import unittest

from bs4 import BeautifulSoup

from site_content.athletics import (EARLIER_COPIES, SOURCES, athletics_rows, clock, load_athletics, parse_running,
                                    parse_swimming, parse_tempo, parse_weightlifting)
from site_content.athletics_views import running_body, swimming_body, weightlifting_body

ROOT = Path(__file__).resolve().parents[2]


class ParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_athletics(ROOT)

    def test_running_means_are_computed_and_written_averages_kept(self):
        run = self.data["running"]
        first = run["sessions"][0]
        self.assertEqual([i["seconds"] for i in first["intervals"]], [275, 253, 231])
        self.assertEqual(first["recordedAverage"]["raw"], "4:13")
        self.assertEqual(run["summary"]["bestInterval"], {"seconds": 214, "date": "2026-10-11"})  # 3:34.0
        # 9/26: (250+228+227+236)/4 = 235.25 s, written as 3:56; flagged, not corrected.
        self.assertEqual(run["summary"]["recordedAverageMismatches"], ["2026-09-26"])
        self.assertEqual(run["sessions"][1]["recordedAverage"]["raw"], "3:56")
        # 10/3 has no written Avg: kept missing, listed, and the mean stands alone.
        self.assertEqual(run["summary"]["unwrittenAverages"], ["2026-10-03"])
        self.assertIsNone(run["sessions"][3]["recordedAverage"])
        self.assertEqual(run["sessions"][4]["recordedAverage"]["raw"], "3:36.9")  # decimal seconds
        self.assertEqual(clock(202.5), "3:23")
        self.assertEqual([row["pacePerKm"] for row in run["history"]], [170.0, 202.5, 211.2])

    def test_tempo_runs_pace_and_speed_match_the_written_lines(self):
        tempo = self.data["tempo"]
        self.assertEqual(tempo["summary"]["runs"], 4)
        first, second, third, fourth = tempo["runs"]
        self.assertEqual((first["route"], first["distanceKm"], first["timeSeconds"]), ("House to Vape Store & Back", 4.6, 1415.21))
        self.assertEqual(first["paceSeconds"], 307.65)
        self.assertEqual(second["timeRaw"], "33.23.81")  # dots as written
        self.assertEqual(second["speed"], 2.89)
        self.assertEqual((third["date"], third["timeSeconds"]), ("2026-10-24", 1287.96))
        self.assertEqual((fourth["date"], fourth["timeSeconds"]), ("2026-10-26", 1276.16))
        self.assertEqual(tempo["summary"]["paceMismatches"], [])

    def test_swimming_totals_and_weeks(self):
        swim = self.data["swimming"]
        self.assertEqual(swim["summary"]["sessions"], 20)
        self.assertEqual(swim["summary"]["yardSessions"], 17)
        first = swim["sessions"][0]  # 1600 yd → 1463 m
        self.assertEqual((first["distance"], first["unit"], first["meters"]), (1600, "y", 1463))
        self.assertEqual(next(s for s in swim["sessions"] if s["date"] == "2026-10-14")["meters"], 2000)  # Oct 14 logged in metres
        self.assertEqual(swim["sessions"][-1]["meters"], 1463)  # Oct 27 logged as 1600 yd
        self.assertEqual(sum(week["meters"] for week in swim["weeks"]), swim["summary"]["meters"])
        # Oct 10 freeform: 650 + 3×450 = 2000, four sets, strokes from the words.
        mixed = next(s for s in swim["sessions"] if s["date"] == "2026-10-10")
        self.assertEqual((mixed["sets"], mixed["setsCover"], mixed["strokes"]), (4, 2000, ["Free", "Back", "Breast", "Fly"]))
        # Oct 5: 5×450 = 2250 against a written 2200; flagged, not corrected.
        self.assertEqual(swim["summary"]["setMismatches"], ["2026-10-05"])
        self.assertEqual(next(s for s in swim["sessions"] if s["date"] == "2026-10-05")["setMismatch"], 50)
        self.assertEqual(first["strokes"], ["Fly", "Back", "Breast", "Free"])

    def test_weightlifting_keeps_raw_names_and_never_merges_lifts(self):
        lift = self.data["weightlifting"]
        names = {e["nameRaw"] for s in lift["sessions"] for e in s["exercises"]}
        self.assertIn("Assited Pullups", names)
        shown = {e["name"] for e in lift["exercises"]}
        self.assertIn("Assisted Pullups", shown)
        self.assertIn("Barbell Press", shown)
        self.assertIn("Incline Barbell Press", shown)
        assisted = next(e for e in lift["exercises"] if e["name"] == "Assisted Pullups")
        self.assertEqual(assisted["kind"], "assisted")
        self.assertNotIn("change", assisted)
        self.assertEqual(lift["summary"]["sessions"], 22)
        self.assertEqual(lift["summary"]["splits"], {"Chest": 7, "Back": 9, "Shoulders": 6})

    def test_new_set_formats_are_kept_or_excluded_with_reasons(self):
        lift = self.data["weightlifting"]
        exercises = {(s["date"], e["name"]): e for s in lift["sessions"] for e in s["exercises"]}
        # "30lbs" without reps and the inline "ds12x22" dropset are excluded, with reasons.
        self.assertEqual(exercises[("2026-10-05", "Decline Chest Press")]["excludedSets"],
                         [{"raw": "30lbs", "reason": "no rep count written"}])
        self.assertEqual(exercises[("2026-10-08", "Shoulder Press")]["excludedSets"],
                         [{"raw": "ds12x22", "reason": "dropset"}])
        self.assertEqual(lift["summary"]["excludedSets"], 2)
        # "12xBodyweight" counts as a zero-weight set; "Back Extensions;" has nothing recorded.
        self.assertEqual(exercises[("2026-10-13", "Pushups")]["kind"], "bodyweight")
        self.assertEqual(exercises[("2026-10-14", "Back Extensions")]["kind"], "unrecorded")
        # The Oct 4 & Oct 25 Back Extensions had sets; the empty Oct 14 line adds no progress point.
        tracked = next(e for e in lift["exercises"] if e["name"] == "Back Extensions")
        self.assertEqual([p["date"] for p in tracked["points"]], ["2026-10-04", "2026-10-25"])
        # "10x 130lbs", a trailing period and a header without a dash all parse.
        self.assertEqual(max(s["weight"] for s in exercises[("2026-10-10", "Diverging Seated Rows")]["sets"]), 130)
        self.assertEqual(next(s for s in lift["sessions"] if s["date"] == "2026-10-13")["split"], "Chest")
        self.assertEqual(next(s for s in lift["sessions"] if s["date"] == "2026-10-16")["split"], "Shoulders")

    def test_rep_targets_take_the_heaviest_qualifying_set(self):
        lift = parse_weightlifting("Weightlifting Log\n9/14/2026 - Chest\nPress; 20x45lbs, 12x95lbs, 10x115lbs, 6x125lbs\n"
                                   "Assisted Pullups; 18x120lbs, 12x90lbs, 10x70lbs, 7x50lbs\nDips; 9x0lbs\n"
                                   "9/15/2026 - Chest\nPress; 8x135lbs\nAssisted Pullups; 12x80lbs")
        press, pullups, dips = lift["sessions"][0]["exercises"]
        self.assertEqual((press["topWeight"], press["best10"], press["best12"]), (125, 115, 95))
        # Assisted: the least assistance among sets reaching the rep target.
        self.assertEqual((pullups["leastAssist"], pullups["best10"], pullups["best12"]), (50, 70, 90))
        self.assertNotIn("best10", dips)
        points = lift["exercises"][0]["points"]
        self.assertEqual([(p["best10"], p["best12"]) for p in points], [(115, 95), (None, None)])
        page = BeautifulSoup(weightlifting_body({**lift, "source": {"path": "log.txt", "latestEntry": ["9/15/2026 - Chest"]}}), "html.parser")
        chart = page.select_one(".athletics-multiple svg")
        self.assertIn("Right axis: reps", chart["aria-label"])
        self.assertEqual(len(chart.select("rect.lift-reps")), 2)
        self.assertFalse(chart.select(".lift-10 polyline"), "a session without a 10-rep set breaks the line")
        self.assertIn("10+ reps", page.select_one("#lifting-progress-table").get_text())

    def test_csv_rows_cover_every_value(self):
        rows = athletics_rows(self.data)
        self.assertEqual(len(rows["running-intervals"]), 19)
        self.assertEqual(len(rows["running-tempo"]), 4)
        self.assertEqual(len(rows["weightlifting-sets"]), self.data["weightlifting"]["summary"]["sets"])
        progress = rows["weightlifting-progress"]
        self.assertEqual(set(progress[0]), {"exercise", "kind", "date", "topSetLbs", "repsAtTopSet", "best10RepsLbs",
                                            "best12RepsLbs", "totalReps", "estimated1rmLbs"})
        rows_ = next(r for r in progress if r["exercise"] == "Bent Over Rows" and r["date"] == "2026-09-30")
        self.assertEqual((rows_["topSetLbs"], rows_["best10RepsLbs"], rows_["best12RepsLbs"]), (135, 135, 115))

    def test_an_edited_earlier_copy_stops_the_build(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for path in SOURCES.values():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / path, root / path)
            self.assertEqual(load_athletics(root)["swimming"]["summary"]["sessions"], 20)
            copy = root / EARLIER_COPIES["swimming"]
            copy.parent.mkdir(parents=True)
            copy.write_text((ROOT / SOURCES["swimming"]).read_text(encoding="utf-8") + "\n(10/16/2026) - 400m - 1x400 of Free\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from records/athletics/swimming"):
                load_athletics(root)

    def test_malformed_logs_stop_with_a_line_number(self):
        cases = (
            (parse_running, "Interval Training Data\nI1 - (9/22/2026) - 3 Intervals\n4:35\n4:13\nAvg: 4:24", "declared"),
            (parse_running, "Interval Training Data\nI9 - (9/22/2026) - 1 Interval\n4:35\nAvg: 4:35", "distance"),
            (parse_swimming, "Swimming Log\n(9/21/2026) - 1600k - 4x400 of Free", "unreadable"),
            (parse_swimming, "Swimming Log\n(9/21/2026) - 1600m - 4x400 of nothing", "strokes"),
            (parse_tempo, "Tempo_Run_Log\n(10/07/2026)\nTempo Run - 4.6km (Loop)\n23:35.21", "pace"),
            (parse_weightlifting, "Weightlifting Log\n9/14/2026 - Chest & Abs\nPress; 20x45kg", "Unreadable set"),
            (parse_weightlifting, "Weightlifting Log\n9/14/2026 - Legs\nSquat; 5x225lbs", "split"),
        )
        for parser, text, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                parser(text)


class DashboardTests(unittest.TestCase):
    def test_dashboards_are_static_escaped_and_ids_unique(self):
        data = load_athletics(ROOT)
        data["weightlifting"]["sessions"][0]["exercises"][0]["name"] = '<script>alert(1)</script>'
        for render, key in ((running_body, "running"), (swimming_body, "swimming"), (weightlifting_body, "weightlifting")):
            with self.subTest(page=key):
                markup = render(data[key]) if key != "running" else render(data[key], "", data["tempo"])
                page = BeautifulSoup(markup, "html.parser")
                self.assertIsNone(page.find("script"))
                self.assertNotIn("<script>alert", markup)
                ids = [tag["id"] for tag in page.find_all(id=True)]
                self.assertEqual(len(ids), len(set(ids)))
                for svg in page.select("svg.sports-chart"):
                    for ref in svg["aria-labelledby"].split():
                        self.assertIn(ref, ids)
                self.assertTrue(page.select("table"), "every chart needs a table or text equivalent")
                self.assertFalse(re.search(r"\b(?:nan|inf)\b", markup))
                notes = page.select_one(f"#{key}-update")
                self.assertIn(data[key]["source"]["path"], notes.get_text())
                self.assertIn("plain text (.txt)", notes.get_text())
                self.assertTrue(page.select_one(f'a[href="#{key}-update"]'))


if __name__ == "__main__":
    unittest.main()
