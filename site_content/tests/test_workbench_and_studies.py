"""Tests for the hybrid log_sync script, SQLite Workbench subpage, and Macroeconomics / Alberta Referendum studies."""

from contextlib import closing
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest

from bs4 import BeautifulSoup

from docx_to_txt import convert_path, docx_to_text
from site_content.log_sync import extract_gdoc_id, repair_log_text, validate_or_repair
from site_content.pdf import copy_verified_pdf
from site_content.publishing import home_html
from site_content.studies import load_studies, studies_rows
from site_content.studies_views import ai_cost_study_body, alberta_study_body, gas_study_body, gen_tax_study_body, macro_study_body, sodium_study_body
from site_content.workbench import RAP_BUCKETS, load_workbench, validate_workbench, workbench_rows
from site_content.workbench_views import (
    completion_dashboard_body,
    database_leaf_content,
    reminders_dashboard_body,
    site_completion_dashboard_content,
    traffic_dashboard_body,
    updates_dashboard_body,
    workbench_body,
)

ROOT = Path(__file__).resolve().parents[2]


class LogSyncTests(unittest.TestCase):
    def test_zero_token_deterministic_repairs_across_logs(self):
        messy_sleep = "10/702026\n7.5\nDreamt about an iceberg map.\n"
        repaired, parsed, changes = validate_or_repair("sleep", messy_sleep)
        self.assertTrue(changes)
        self.assertEqual(parsed["nights"][0]["date"], "2026-10-07")
        self.assertEqual(parsed["nights"][0]["hours"], 7.5)
        self.assertTrue(repaired.startswith("Sleep_and_Dream_Log\n"))

        messy_lift = "10/18.2026 - Chest & Abs\nBarbell Press; 12x95, 10x115lbs, 12xbw\n"
        _, lift_parsed, lift_changes = validate_or_repair("weightlifting", messy_lift)
        self.assertTrue(lift_changes)
        sets = lift_parsed["sessions"][0]["exercises"][0]["sets"]
        self.assertEqual([(s["reps"], s["weight"]) for s in sets], [(12, 95.0), (10, 115.0), (12, 0.0)])

        messy_swim = "(10-18-2026) - 2000 yards - 5x400 of Fly-Back_Breast-Free\n"
        _, swim_parsed, _ = validate_or_repair("swimming", messy_swim)
        self.assertEqual(swim_parsed["sessions"][0]["unit"], "y")
        self.assertEqual(swim_parsed["sessions"][0]["distance"], 2000)

        messy_diet = (
            "10/19/2026\n"
            "Breakfast: 30/10/25g Eggs\n"
            "Total Expenditure: 3400 kcal (walk)\n"
            "Total Consumption: 2800 kcal - 250/90/160g\n"
            "Net Expenditure: 600 kcal loss\n"
        )
        _, diet_parsed, _ = validate_or_repair("diet", messy_diet)
        self.assertEqual(diet_parsed["days"][0]["deficit"], 600)

    def test_single_line_llm_fallback_invoked_only_for_unrecognized_line(self):
        broken_run = "Interval Training Data\nI1 - (10/18/2026) - 2 Intervals\n3:40.0\nthree minutes thirty five\nAvg: 3:37.5\n"
        calls = []

        def fake_llm(key: str, broken_line: str, error_msg: str) -> str:
            calls.append((key, broken_line, error_msg))
            return "3:35.0"

        _, parsed, changes = validate_or_repair("running", broken_run, llm_fixer=fake_llm)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], "three minutes thirty five")
        self.assertEqual(parsed["sessions"][0]["intervals"][1]["seconds"], 215)
        self.assertEqual(changes[-1]["method"], "llm")

    def test_docx_to_txt_extracts_paragraphs_and_tables(self):
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:r><w:t>Swimming Log</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>(10/18/2026) - 2000m - 5x400 of Fly-Back_Breast-Free</w:t></w:r></w:p>'
            '</w:body></w:document>'
        )
        with tempfile.TemporaryDirectory() as folder:
            docx_path = Path(folder) / "Swimming_Log.docx"
            import zipfile
            with zipfile.ZipFile(docx_path, "w") as zf:
                zf.writestr("word/document.xml", xml)
            self.assertIn("Swimming Log\n(10/18/2026)", docx_to_text(docx_path))
            written = convert_path(Path(folder))
            self.assertEqual(len(written), 1)
            self.assertEqual(written[0].name, "Swimming_Log.txt")

    def test_extract_gdoc_id_from_url_and_gdoc_json(self):
        doc_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
        self.assertEqual(extract_gdoc_id(f"https://docs.google.com/document/d/{doc_id}/edit?usp=sharing"), doc_id)
        self.assertEqual(extract_gdoc_id(f'{{"doc_id": "{doc_id}", "email": "user@example.com"}}'), doc_id)


class WorkbenchTests(unittest.TestCase):
    def test_sqlite_materialization_and_views(self):
        with tempfile.TemporaryDirectory() as folder:
            temp_root = Path(folder)
            data = load_workbench(temp_root)
            db_file = temp_root / "records/workbench/workbench.db"
            self.assertTrue(db_file.is_file())
            with closing(sqlite3.connect(db_file)) as conn:
                counts = {
                    name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                    for name in ("study_queue", "wishlist_todos", "rap_lyrics", "voice_notes")
                }
            self.assertEqual(counts["study_queue"], len(data["studyQueue"]))
            self.assertEqual(counts["wishlist_todos"], len(data["wishlistTodos"]))
            self.assertEqual(counts["rap_lyrics"], len(data["rapLyrics"]))
            self.assertEqual(counts["voice_notes"], len(data["voiceNotes"]))

        rows = workbench_rows(data)
        self.assertEqual(set(rows), {"studies", "todos", "lyrics", "voice"})
        markup = workbench_body(data, "../")
        page = BeautifulSoup(markup, "html.parser")
        self.assertIsNone(page.find("script"))
        ids = [tag["id"] for tag in page.find_all(id=True)]
        self.assertEqual(len(ids), len(set(ids)))
        bucket_values = [opt["value"] for opt in page.select("#wb-lyric-bucket option")]
        self.assertEqual(bucket_values, [slug for slug, _ in RAP_BUCKETS])
        # Add forms sit above the queue tables in every section and snap-scroll from the hero buttons.
        for form_id, table_id in (
            ("wb-study-form", "workbench-studies-table"),
            ("wb-theory-form", "workbench-theory-table"),
            ("wb-app-form", "workbench-apps-table"),
            ("wb-todo-form", "workbench-todos-table"),
            ("wb-lyric-form", "workbench-lyrics-table"),
            ("wb-voice-form", "workbench-voice-table"),
        ):
            self.assertLess(markup.index(f'id="{form_id}"'), markup.index(f'id="{table_id}"'))
            self.assertIsNotNone(page.select_one(f'a[data-wb-jump="{form_id}"]'))
        # Toggle to run a study immediately + last-column run button for queued studies + passkey auth dialog.
        self.assertIsNotNone(page.select_one("#wb-study-run-now"))
        self.assertIsNotNone(page.select_one("#wb-auth-dialog"))
        self.assertEqual(page.select_one("#wb-auth-title").get_text(strip=True), "Unlock Admin")
        self.assertIsNotNone(page.select_one("#wb-auth-new-pass"))
        self.assertEqual(page.select_one("#wb-auth-model option[selected]")["value"], "argon-high")
        self.assertIsNotNone(page.select_one("#wb-run-dialog"))
        self.assertIsNotNone(page.select_one("#wb-run-rerun"))
        self.assertIsNotNone(page.select_one("#wb-run-key-bar"))
        self.assertIsNotNone(page.select_one("#wb-run-save-key"))
        self.assertIsNotNone(page.select_one("#wb-run-visuals"))
        self.assertIsNotNone(page.select_one("#wb-run-download-py"))
        self.assertIsNotNone(page.select_one("#wb-run-download-csv"))
        self.assertIsNotNone(page.select_one("#wb-filter-sort"))
        run_buttons = [btn["data-run-study-id"] for btn in page.select("#workbench-studies-table [data-run-study-id]")]
        self.assertEqual(run_buttons, ["ST-03-00", "ST-04-00", "ST-07-00"])
        restudy_buttons = [btn["data-restudy-id"] for btn in page.select("#workbench-studies-table [data-restudy-id]")]
        self.assertEqual(
            restudy_buttons,
            ["ST-01-00", "ST-02-00", "ST-05-00", "ST-06-00", "ST-08-00", "ST-09-00", "ST-10-00", "ST-11-00"],
        )
        followup_buttons = [btn["data-followup-id"] for btn in page.select("#workbench-studies-table [data-followup-id]")]
        self.assertEqual(len(followup_buttons), len(data["studyQueue"]))
        self.assertIsNotNone(page.select_one("#wb-followup-dialog"))
        # Study filter bar is always visible; table has 6 public columns (including Linkages) + 2 hidden Admin columns (IP Index & Admin).
        self.assertIsNotNone(page.select_one("#wb-study-filters"))
        self.assertIsNotNone(page.select_one("#wb-filter-search"))
        self.assertIsNotNone(page.select_one("#wb-filter-status"))
        self.assertIsNotNone(page.select_one("#wb-filter-field"))
        self.assertIsNotNone(page.select_one("#wb-filter-ip"))
        study_headers = [th.get_text(strip=True) for th in page.select("#workbench-studies-table thead th")]
        self.assertEqual(study_headers, ["ID", "Date", "Study (hover / tap)", "Data", "Linkages", "Status", "IP Index", "Admin"])
        self.assertEqual(len(page.select("#workbench-studies-table thead th[data-wb-admin-col][hidden]")), 2)
        self.assertEqual(len(page.select("#workbench-studies-table .wb-study-link")), len(data["studyQueue"]))
        self.assertEqual(len(page.select("#workbench-studies-table .wb-pbi-tooltip")), len(data["studyQueue"]))
        self.assertTrue(page.select("[data-delete-study-id]"))
        # Main home page (index.html) also includes the Unlock Admin modal and button + separate Password Manager dialog.
        home_soup = BeautifulSoup(home_html(), "html.parser")
        self.assertIn("Unlock Admin", home_soup.select_one("[data-wb-auth-open]").get_text())
        self.assertIsNotNone(home_soup.select_one("#wb-auth-dialog"))
        self.assertIsNotNone(home_soup.select_one("#wb-password-dialog"))
        self.assertIsNotNone(home_soup.select_one("#wb-auth-new-pass"))
        self.assertIsNotNone(home_soup.select_one("#wb-pwd-confirm"))
        self.assertIsNotNone(home_soup.select_one("#wb-pwd-revoke-all"))
        # Peek (👀) buttons exist only for Passphrase fields, never for the Gemini API key.
        peek_targets = [btn["data-wb-peek"] for btn in page.select("[data-wb-peek]")]
        self.assertEqual(peek_targets, ["wb-auth-pass", "wb-auth-new-pass", "wb-pwd-confirm", "wb-pwd-master"])
        self.assertEqual([btn["data-wb-peek"] for btn in home_soup.select("[data-wb-peek]")], ["wb-auth-pass", "wb-auth-new-pass", "wb-pwd-confirm", "wb-pwd-master"])
        self.assertIsNone(page.select_one('[data-wb-peek="wb-auth-key"]'))
        js_source = (ROOT / "site_content/web/workbench.js").read_text(encoding="utf-8")
        self.assertIn("67wxyE7LLICnHCNkjjGbBSKiCXdsQXw5YSjn1+lNzHo=", js_source)
        self.assertNotIn("crypto.subtle", js_source, "must work over http:// where crypto.subtle is undefined")
        for msg in (
            "Incorrect current passphrase — verification failed. No tokens used.",
            "Passphrase Is Incorrect You Potential Clanker",
            "Persistant Are We 👀👀👀👀👀👀",
            "Maybe its time to give up and Touch Some Grassss",
            "Why are you still trying bro 😆🤣🥹🤤😬",
            "Dilly Dallying away our whole life away huh 🙂‍↔️",
            "🥶🥶🥶🥶🥶🥶🥶🥶🥶🥶🥶",
            "Why 😐",
            "Whyyyyy 😑😑😑😑",
            "Last Try 👉🤢👈👉😶👈👉😼👈👉😈👈",
        ):
            self.assertIn(msg, js_source)
        for slug in ("Database-Exploration", "Relational-Database-Development"):
            lede, leaf_html = database_leaf_content(slug, data, "../../../")
            self.assertTrue(lede)
            self.assertIn("Workbench/index.html", leaf_html)
        # Standalone Admin-protected Map & Site % and IP & Traffic reflection pages
        comp_body = completion_dashboard_body(ROOT, "../")
        self.assertIn("site-completion-fields-chart", comp_body)
        self.assertIn("site-completion-table", comp_body)
        self.assertIn("data-wb-admin-only", comp_body)
        traffic_body = traffic_dashboard_body(data, "../")
        self.assertIn("db-ip-traffic-chart", traffic_body)
        self.assertIn("db-study-clicks-chart", traffic_body)
        self.assertIn("data-wb-admin-only", traffic_body)
        reabs_body = reminders_dashboard_body(data, "../")
        self.assertIn("Random Extra Additional Bullshit", reabs_body)
        self.assertIn("Put this rant in the page too this part included!", reabs_body)
        self.assertIn("l2mcgrat@uwaterloo.ca", reabs_body)
        self.assertIn("Contact Manulife Financial Regarding TFSA Setup", reabs_body)
        self.assertIn("Contact HCM AR and Payroll Regarding Missed Overtime", reabs_body)
        self.assertIn("Barrie Recycling and Waste Corp", reabs_body)
        self.assertIn("705-792-6557", reabs_body)
        self.assertIn("reabs-history-chart", reabs_body)
        # 3-stage cascading Section -> Subsection -> Subsubsection dropdowns on Workbench forms + Follow-Up modal
        self.assertEqual(len(page.select("[data-wb-cascade]")), 6)
        self.assertEqual(len(page.select("[data-cascade-field]")), 6)
        self.assertEqual(len(page.select("[data-cascade-topic]")), 6)
        self.assertEqual(len(page.select("[data-cascade-leaf]")), 6)
        # Voice note / Journal transcripts are Admin-protected
        self.assertTrue(page.select("#workbench-voice-table [data-wb-admin-only][hidden]"))

    def test_invalid_atlas_path_or_bucket_rejected(self):
        data = load_workbench(ROOT)
        bad = {**data, "rapLyrics": [{**data["rapLyrics"][0], "bucket": "Not-A-Bucket"}]}
        with self.assertRaisesRegex(ValueError, "unknown Rap bucket"):
            validate_workbench(bad)


class StudiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.studies = load_studies()

    def test_macro_and_alberta_data_and_dashboards(self):
        macro = self.studies["macro"]
        alberta = self.studies["alberta"]
        gas = self.studies["gas"]
        sodium = self.studies["sodium"]
        ai_cost = self.studies["ai_cost"]
        gen_tax = self.studies["gen_tax"]
        self.assertEqual(len(macro["industries"]), 12)
        self.assertEqual(len(macro["regions"]), 12)
        self.assertEqual(len(alberta["questions"]), 10)
        self.assertEqual(alberta["summary"]["nonConstitutionalPassed"], 5)
        self.assertEqual(alberta["summary"]["constitutionalPassed"], 0)
        self.assertEqual(alberta["summary"]["q10RemainPct"], 74.95)
        self.assertEqual(len(gas["countries"]), 12)
        self.assertEqual(len(gas["industries"]), 10)
        self.assertIn("import pandas as pd", gas["pandasScript"])
        self.assertEqual(len(sodium["chemistries"]), 6)
        self.assertIn("import pandas as pd", sodium["pandasScript"])
        self.assertEqual(len(ai_cost["models"]), 8)
        self.assertEqual(len(ai_cost["layers"]), 6)
        self.assertIn("import pandas as pd", ai_cost["pandasScript"])
        self.assertEqual(len(gen_tax["cohorts"]), 8)
        self.assertIn("import pandas as pd", gen_tax["pandasScript"])
        csvs = studies_rows(self.studies)
        self.assertEqual(len(csvs["macro-industries"]), 12)
        self.assertEqual(len(csvs["alberta-questions"]), 10)
        self.assertEqual(len(csvs["gas-countries"]), 12)
        self.assertEqual(len(csvs["gas-industries"]), 10)
        self.assertEqual(len(csvs["sodium-chemistries"]), 6)
        self.assertEqual(len(csvs["ai-cost-models"]), 8)
        self.assertEqual(len(csvs["ai-cost-layers"]), 6)
        self.assertEqual(len(csvs["gen-tax-cohorts"]), 8)

        for key, body in (
            ("macro", macro_study_body(macro)),
            ("alberta", alberta_study_body(alberta)),
            ("gas", gas_study_body(gas)),
            ("gas-tab", gas_study_body(gas, is_subtab=True)),
            ("sodium", sodium_study_body(sodium)),
            ("sodium-tab", sodium_study_body(sodium, is_subtab=True)),
            ("ai-cost", ai_cost_study_body(ai_cost)),
            ("ai-cost-tab", ai_cost_study_body(ai_cost, is_subtab=True)),
            ("gen-tax", gen_tax_study_body(gen_tax)),
            ("gen-tax-tab", gen_tax_study_body(gen_tax, is_subtab=True)),
        ):
            with self.subTest(study=key):
                page = BeautifulSoup(body, "html.parser")
                self.assertIsNone(page.find("script"))
                ids = [tag["id"] for tag in page.find_all(id=True)]
                self.assertEqual(len(ids), len(set(ids)))
                for svg in page.select("svg.sports-chart"):
                    for ref in svg["aria-labelledby"].split():
                        self.assertIn(ref, ids)
                self.assertTrue(page.select("table"))
                self.assertTrue(page.select("[data-kpi-card]"))
                # Verify primary SVG chart sits ON TOP of (before) the KPI metric cards
                first_svg_pos = body.find("<svg")
                first_kpi_pos = body.find("sports-metrics")
                self.assertGreater(first_svg_pos, 0)
                self.assertLess(first_svg_pos, first_kpi_pos)
                self.assertFalse(re.search(r"\b(?:nan|inf)\b", body))

    def test_compiled_study_pdfs_are_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for key in ("macro-ai-iceberg", "alberta-referendum-2026", "gas-price-collusion", "sodium-battery-technology", "ai-cost-economics", "generational-taxes"):
                self.assertTrue(copy_verified_pdf(ROOT, key, out / key))
                self.assertTrue((out / key / "document.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
