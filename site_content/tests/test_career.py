"""Public career contracts; never compile, publish, or modify the resume sources."""

from dataclasses import replace
from hashlib import sha256
from html import escape
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from site_content import career


ROOT = Path(__file__).resolve().parents[2]
RESUME_SOURCE = ROOT / "LiamMcGrath_Resume"


def soup(body):
    return BeautifulSoup(body, "html.parser")


class CareerFactsTests(unittest.TestCase):
    def setUp(self):
        self.resume = soup(career.resume_body())
        self.about = soup(career.career_body())

    def test_real_source_facts_and_dates_have_not_been_assumed(self):
        # Check the primary files, not another agent's summary or the publisher.
        expected = {
            "experience": ("Business Intelligence Lead", "Jan 2023 - Present", "Process Engineer",
                           "Jan 2020 - Jan 2023", "Roy Research Group", "Jan 2018 - Sept 2018",
                           "The Woodbridge Group", "Sept 2016 - May 2017"),
            "education": ("Honours Bachelor of Applied Science in Nanotechnology Engineering (Co-op)", "2014 - 2019"),
            "projects": ("Room Temperature NO2 Sensor Fabrication", "carbon nanotubes", "tellurium", "Arduino"),
            "honors": (r"NSERC \& USRA", "2018", "UW Presidents Scholarship", "2014"),
            "technical_skills": ("Linux", "AWS", "Tableau", "SIMUL8", "COMSOL"),
        }
        for name, facts in expected.items():
            source = (RESUME_SOURCE / "resume" / f"{name}.tex").read_text(encoding="utf-8")
            for fact in facts:
                with self.subTest(source=name, fact=fact):
                    self.assertIn(fact, source)

    def test_experience_is_reverse_chronological_with_exact_role_dates(self):
        entries = self.resume.select(".career-timeline > li > article")
        self.assertEqual(
            [(entry.h3.get_text(), entry.select_one(".career-dates").get_text()) for entry in entries],
            [("Business Intelligence Lead", "Jan 2023 – Present"),
             ("Process Engineer", "Jan 2020 – Jan 2023"),
             ("Simulation Software Developer", "Jan 2018 – Sept 2018"),
             ("Research Assistant", "Sept 2016 – May 2017")],
        )
        for entry, organization in zip(entries, ("Honda of Canada Mfg.", "Honda of Canada Mfg.",
                                                "University of Waterloo · Roy Research Group",
                                                "The Woodbridge Group · Corporate R&D")):
            self.assertIn(organization, entry.get_text())

    def test_current_division_scope_is_undated_and_collaborative(self):
        for page in (self.resume, self.about):
            with self.subTest(page=page.name):
                scope = page.select_one(".career-scope").get_text(" ", strip=True)
                self.assertIn("now supports the Manufacturing Division at Honda", scope)
                self.assertIn("previously focused on the Weld Department", scope)
                self.assertIn("Works with the company’s Pillar Leads, who oversee department-level matters", scope)
                self.assertIn("division-scope update is undated", scope)
                self.assertNotRegex(scope, r"\b(?:19|20)\d{2}\b")
                self.assertNotRegex(page.get_text(), r"(?i)promot(?:ed|ion)|oversees? (?:the )?Manufacturing Division|head of (?:the )?Manufacturing")
                self.assertEqual(page.select_one(".career-entry .career-dates").get_text(), "Jan 2023 – Present")

    def test_current_brief_covers_systems_etl_bi_simulation_controls(self):
        for page in (self.resume, self.about):
            brief = page.select_one(".career-brief").get_text()
            for fact in ("data-collection systems", "ETL", "Power BI", "simulation", "controls"):
                self.assertIn(fact, brief)

    def test_research_does_not_repeat_inaccurate_mb_pol_ml_claim(self):
        research = self.resume.select(".career-timeline > li")[2].get_text(" ", strip=True)
        self.assertIn("MB-pol many-body water potential", research)
        self.assertNotIn("machine learning", research.lower())
        for fact in ("Python/MMTK", "PIMC", "PIMD", "C++", "Compute Canada"):
            self.assertIn(fact, research)

    def test_education_capstone_and_academic_awards(self):
        education = self.resume.select_one("#resume-education").get_text()
        self.assertIn("Honours Bachelor of Applied Science in Nanotechnology Engineering (Co-op)", education)
        self.assertIn("University of Waterloo", education)
        self.assertIn("2014 – 2019", education)
        project = self.resume.select_one("#resume-projects").get_text()
        for fact in ("Room-temperature NO2 sensor", "educational capstone", "carbon nanotubes",
                     "tellurium", "Arduino", "Sept 2018 – Apr 2019"):
            self.assertIn(fact, project)
        awards = self.resume.select("#resume-honors .career-entry")
        self.assertEqual([entry.select_one(".career-dates").get_text() for entry in awards], ["2018", "2014"])
        self.assertIn("NSERC / USRA research grant", awards[0].get_text())
        self.assertIn("P. N. Roy", awards[0].get_text())
        self.assertIn("President’s Scholarship", awards[1].get_text())

    def test_skills_classifications_are_correct(self):
        groups = {group.dt.get_text(): [li.get_text() for li in group.select("li")]
                  for group in self.resume.select(".career-skill-group")}
        languages = groups["Programming & query languages"]
        for tool in ("Linux", "AWS", "Tableau", "TeX"):
            self.assertNotIn(tool, languages)
        self.assertIn("Linux", groups["Operating systems"])
        self.assertIn("AWS", groups["Cloud & collaboration"])
        self.assertIn("Tableau", groups["Data & business intelligence"])
        self.assertIn("Power BI", groups["Data & business intelligence"])
        self.assertIn("TeX", groups["Scientific authoring & visualization"])

    def test_no_unverified_numeric_savings_or_new_certifications(self):
        for page in (self.resume, self.about):
            text = page.get_text(" ", strip=True)
            self.assertNotRegex(text, r"[$€£]|\d+(?:\.\d+)?\s*%|\b\d+\s*(?:hours?|million|thousand)\b")
            self.assertNotRegex(text, r"(?i)certified|certification|Coursera|Six Sigma|credential ID")


class CareerPublicBoundaryTests(unittest.TestCase):
    def test_public_content_has_no_private_contacts(self):
        bodies = (career.resume_body(), career.career_body())
        for body in bodies:
            self.assertNotRegex(body, r"(?i)mailto:|tel:|[\w.+-]+@[\w.-]+\.[a-z]{2,}|\+?\d[\d ().-]{8,}\d")
            self.assertNotIn("200 University Avenue West", body)
        # Read private fields only to compare; failure messages never disclose values.
        contacts = []
        for filename in ("resume.tex", "cv.tex", "coverletter.tex"):
            source = (RESUME_SOURCE / filename).read_text(encoding="utf-8")
            contacts.extend(re.findall(r"\\(?:mobile|email|address)\s*\{([^}]+)\}", source))
        self.assertTrue(contacts, "Privacy regression check must inspect actual contact fields.")
        for body in bodies:
            text = soup(body).get_text(" ", strip=True).casefold()
            self.assertFalse(any(value.strip().casefold() in text for value in contacts if value.strip()),
                             "Public HTML must not contain source contact values.")

    def test_no_source_template_or_pdf_downloads(self):
        for body in (career.resume_body(), career.career_body()):
            page = soup(body)
            self.assertEqual(page.select("[download], iframe, object, embed"), [])
            for link in page.select("a[href]"):
                self.assertNotRegex(link["href"], r"(?i)\.(?:pdf|zip|tex|cls)(?:[?#]|$)|LiamMcGrath_Resume|assets/documents")
            self.assertIn("public HTML résumé", page.get_text())
            self.assertIn("not the original awesome-cv PDF", page.get_text())
            self.assertIn("original template is preserved privately", page.get_text())
            self.assertIn("no compiled original PDF is available yet", page.get_text())
            self.assertIn("Waters in a 1D Carbon Nanotube", page.get_text())
            self.assertIn("privacy-safe public article", page.get_text())
            self.assertNotIn("awaiting separate publication", page.get_text())

    def test_rendering_is_deterministic_and_has_no_source_io(self):
        before = {p.relative_to(RESUME_SOURCE): sha256(p.read_bytes()).hexdigest()
                  for p in RESUME_SOURCE.rglob("*") if p.is_file()}
        for renderer in (career.resume_body, career.career_body):
            expected = renderer()
            with patch("builtins.open", side_effect=AssertionError("No runtime source reads")), \
                 patch.object(Path, "open", side_effect=AssertionError("No runtime source reads")):
                self.assertEqual(renderer(), expected)
        after = {p.relative_to(RESUME_SOURCE): sha256(p.read_bytes()).hexdigest()
                 for p in RESUME_SOURCE.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_every_public_entry_field_is_escaped(self):
        payload = '<script data-test="injection">unsafe & \'quoted\'</script>'
        entry = replace(career._EXPERIENCE[0], title=payload, organization=payload,
                        context=payload, dates=payload, highlights=(payload,))
        with patch.object(career, "_EXPERIENCE", (entry, entry)), \
             patch.object(career, "_EDUCATION", entry), \
             patch.object(career, "_PROJECT", entry), \
             patch.object(career, "_HONORS", (entry,)), \
             patch.object(career, "_SKILLS", ((payload, (payload,)),)), \
             patch.object(career, "_PUBLIC_LINKS", ((payload, "https://github.com/l2mcgrat"),)):
            for renderer in (career.resume_body, career.career_body):
                body = renderer()
                self.assertIn(escape(payload), body)
                self.assertNotIn(payload, body)
                self.assertEqual(soup(body).select("script, [data-test]"), [])

    def test_public_prose_and_name_are_escaped(self):
        payload = '<img src=x onerror="unsafe()"> & \'quoted\''
        for field in ("_NAME", "_TAGLINE", "_BRIEF", "_CURRENT_SCOPE", "_SCOPE_NOTE",
                      "_DOCUMENT_NOTE", "_WORK_TERM_NOTE"):
            with self.subTest(field=field), patch.object(career, field, payload):
                body = career.resume_body() + career.career_body()
                self.assertIn(escape(payload), body)
                self.assertNotIn(payload, body)
                self.assertEqual(soup(body).select("img, [onerror]"), [])

    def test_profile_links_escape_attributes_and_strip_tracking(self):
        url = 'https://github.com/name"<unsafe>&?utm_source=private-tracker#tracking'
        with patch.object(career, "_PUBLIC_LINKS", (("GitHub & portfolio", url),)):
            body = career.resume_body()
        page = soup(body)
        link = page.select_one(".career-profile-links a")
        self.assertEqual(link["href"], 'https://github.com/name"<unsafe>&')
        self.assertIn('name&quot;&lt;unsafe&gt;&amp;', body)
        self.assertNotIn("private-tracker", body)
        self.assertNotIn("tracking", body)
        self.assertEqual(page.select("unsafe"), [])

    def test_profile_links_reject_unsafe_schemes_hosts_and_credentials(self):
        for url in ("javascript:alert(1)", "http://github.com/l2mcgrat", "//github.com/l2mcgrat",
                    "https://untrusted.invalid/user", "https://github.com.evil.invalid/user",
                    "https://user:secret@github.com/l2mcgrat", "https://github.com:444/l2mcgrat"):
            with self.subTest(url=url), patch.object(career, "_PUBLIC_LINKS", (("Profile", url),)):
                with self.assertRaisesRegex(ValueError, "approved HTTPS host"):
                    career.resume_body()


class CareerMarkupTests(unittest.TestCase):
    def test_double_quoted_main_is_compatible_with_shell_skip_link(self):
        body = career.resume_body()
        self.assertTrue(body.startswith('<main id="main-content" class="collection-page resume-page">'))
        page = soup(body)
        self.assertEqual(len(page.select("main")), 1)
        self.assertEqual(page.h1.get_text(), "Liam McGrath")
        self.assertEqual(page.select("html, head, body, script, style, link"), [])
        self.assertEqual(len(page.select("h1")), 1)
        self.assertEqual(career.__all__, ["resume_body", "career_body"])

    def test_about_fragment_has_no_second_main_or_h1(self):
        page = soup(career.career_body())
        self.assertEqual(page.select("main, h1, html, head, body, script, style, link"), [])
        self.assertEqual(len(page.select("section.career-block")), 1)
        self.assertEqual(page.select_one("a[href]")["href"], "Resume/index.html")

    def test_all_relative_links_resolve_at_expected_depths(self):
        report = "/Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations/index.html"
        for route, renderer, expected in (
            ("About/Resume/index.html", career.resume_body, {"/About/index.html", "/index.html", "/About/Resume/index.html", report}),
            ("About/index.html", career.career_body, {"/About/Resume/index.html", report}),
        ):
            paths = set()
            page = soup(renderer())
            for link in page.select("a[href]"):
                href = link["href"]
                if urlsplit(href).scheme:
                    continue
                self.assertFalse(href.startswith(("/", "\\")))
                self.assertNotIn("\\", href)
                resolved = urlsplit(urljoin("https://portfolio.invalid/" + route, href))
                self.assertEqual(resolved.netloc, "portfolio.invalid")
                paths.add(resolved.path)
                if resolved.fragment:
                    self.assertIsNotNone(page.find(id=resolved.fragment))
            self.assertEqual(paths, expected)

    def test_only_approved_clean_public_profile_links(self):
        page = soup(career.resume_body())
        links = page.select(".career-profile-links a")
        self.assertEqual([a["href"] for a in links], [
            "https://www.linkedin.com/in/liam-mcgrath-54a917111/", "https://github.com/l2mcgrat",
        ])
        for link in links:
            self.assertEqual(set(link["rel"]), {"noopener", "noreferrer"})
            parts = urlsplit(link["href"])
            self.assertEqual((parts.query, parts.fragment, parts.username, parts.password), ("", "", None, None))
            print_label = link.select_one(".career-print-url").get_text()
            self.assertNotRegex(print_label, r"https?://|\?|#")

    def test_print_button_reuses_existing_script_and_is_honest(self):
        page = soup(career.resume_body())
        buttons = page.select("button.print-reader")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0]["type"], "button")
        self.assertEqual(buttons[0].get_text(), "Print / Save PDF")
        self.assertNotIn("onclick", buttons[0].attrs)
        self.assertIn("browser-formatted", page.find(id=buttons[0]["aria-describedby"]).get_text())
        script = (ROOT / "site_content/web/portfolio.js").read_text(encoding="utf-8")
        self.assertIn("querySelector('.print-reader')", script)
        self.assertIn("window.print()", script)

    def test_ids_and_accessible_references_are_unique_and_resolve(self):
        for renderer in (career.resume_body, career.career_body):
            page = soup(renderer())
            ids = [tag["id"] for tag in page.select("[id]")]
            self.assertEqual(len(ids), len(set(ids)))
            for tag in page.select("[aria-labelledby], [aria-describedby]"):
                for attribute in ("aria-labelledby", "aria-describedby"):
                    for reference in tag.get(attribute, "").split():
                        self.assertIsNotNone(page.find(id=reference))
            for element in page.find_all(True):
                self.assertFalse(any(attr.lower().startswith("on") for attr in element.attrs))

    def test_print_styles_hide_chrome_and_preserve_readable_content(self):
        css = (ROOT / "site_content/web/career.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 680px)", css)
        self.assertIn("@media print", css)
        printing = css.split("@media print", 1)[1]
        for selector in (".site-header", ".site-footer", ".skip-link", ".print-reader", ".career-navigation", ".career-actions"):
            self.assertRegex(printing, re.escape(selector) + r"[^{}]*\{\s*display: none !important;")
        self.assertIn(".career-print-url { display: inline;", printing)
        self.assertIn("break-after: avoid", printing)
        self.assertIn("break-inside: avoid", printing)
        self.assertIn("orphans: 3; widows: 3", printing)
        self.assertNotIn("attr(href)", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)


if __name__ == "__main__":
    unittest.main()