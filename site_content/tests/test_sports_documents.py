"""Sports-only contracts. All generated test output stays in temporary roots.

Run: python -B -m unittest site_content.tests.test_sports_documents -v
PDF compilation is a separate parent check; Pandoc conversion is exercised here.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from PIL import Image

from site_content.basketball import load_basketball
from site_content.latex import convert_document
from site_content.sports_diagrams import DIAGRAMS, build_sports_diagrams


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = ROOT / "notebook_sources/sports"
ASSETS = ROOT / "tex_images/sports"
IMAGE_PATTERN = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^{}]+)\}")
GAME_HEADINGS = {
    "SHOOTING": "shooting", "HORSE": "horse", "1v1": "one-on-one",
    "BACKBOARD": "backboard", "3 POINT": "three-point", "RIM": "rim", "BUMP": "bump",
}


def active(text: str) -> str:
    """Drop real comments, preserving escaped percent signs."""
    return re.sub(r"\\(?:[A-Za-z@]+|[^\r\n])|%[^\r\n]*",
                  lambda match: "" if match[0].startswith("%") else match[0], text)


def chapters(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"\\section\{([^{}]+)\}", text))
    return {match[1]: text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
            for i, match in enumerate(matches)}


def fingerprints(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


class SportsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = active((DOCUMENTS / "basketball_rules.tex").read_text(encoding="utf-8"))
        cls.pitch = active((DOCUMENTS / "creator_pitch.tex").read_text(encoding="utf-8"))
        cls.sections = chapters(cls.rules)

    def test_articles_are_substantial_standalone_conventional_latex(self) -> None:
        for name, text, minimum in (("rules", self.rules, 3200), ("pitch", self.pitch, 1700)):
            with self.subTest(document=name):
                self.assertGreater(len(text.split()), minimum)
                self.assertIn(r"\documentclass[11pt]{article}", text)
                self.assertEqual(text.count(r"\begin{document}"), 1)
                self.assertEqual(text.count(r"\end{document}"), 1)
                for package in ("geometry", "amsmath", "amssymb", "graphicx", "enumitem", "hyperref"):
                    self.assertIn(package, text.split(r"\begin{document}")[0])
                self.assertNotRegex(text, r"\\(?:input|include|write18|today|newcommand)\b|tikzpicture|pgfplots")
                stack: list[str] = []
                for match in re.finditer(r"\\(begin|end)\{([^{}]+)\}", text):
                    if match[1] == "begin":
                        stack.append(match[2])
                    else:
                        self.assertTrue(stack, match[0])
                        self.assertEqual(stack.pop(), match[2])
                self.assertFalse(stack)
                self.assertNotIn("literally include this each time", text)

    def test_high_jump_rules_is_fully_repeated_in_all_three_games(self) -> None:
        copies = []
        for game in ("SHOOTING", "BACKBOARD", "RIM"):
            match = re.search(r"\\textbf\{HIGH JUMP RULES\.\}(.+?)\\end\{enumerate\}",
                              self.sections[game], re.S)
            self.assertIsNotNone(match, game)
            assert match is not None
            paragraph = " ".join(match[1].split())
            for phrase in ("both players are out of mercies", "previous successful shot",
                           "fewest attempts wins", "because both creators competed in high jump",
                           "attempt counts tie", "compare the shot before it", "as far as the very first shot",
                           "SUDDEN DEATH", "five, four or three attempts in Shooting, Rim and Backboard",
                           "move to a closer shot", "no previous successful shot"):
                self.assertIn(phrase, paragraph)
            if game != "SHOOTING":
                self.assertNotRegex(paragraph, r"[()]")
            copies.append(paragraph)
        self.assertEqual(copies, [copies[0]] * 3)
        self.assertEqual(self.rules.count(r"\textbf{HIGH JUMP RULES.}"), 3)
        self.assertNotIn("HIGHJUMP", self.rules + self.pitch)

    def test_attempt_budgets_and_game_numbering_match_owner_rules(self) -> None:
        for game, budget in (("SHOOTING", "five attempts per shot location"),
                             ("BACKBOARD", "three attempts per location"),
                             ("RIM", "four attempts per location")):
            self.assertIn(budget, self.sections[game])
        expected = {"SHOOTING": (1, 5), "HORSE": (0, 7), "1v1": (0, 7),
                    "BACKBOARD": (0, 6), "3 POINT": (1, 4), "RIM": (0, 7), "BUMP": (0, 9)}
        for game, (start, count) in expected.items():
            section = self.sections[game]
            self.assertIn(r"\begin{enumerate}[start=" + str(start) + "]", section)
            first_list = section.split(r"\end{enumerate}", 1)[0]
            self.assertEqual(first_list.count(r"\item"), count, game)
        self.assertIn("three consecutive BALLs count as one missed attempt", self.sections["RIM"])
        self.assertIn("two points", self.sections["1v1"])
        self.assertIn("one point", self.sections["1v1"])
        self.assertIn("reach or exceed", self.sections["1v1"])
        self.assertIn("Win by two is not specified", self.sections["1v1"])

    def test_named_clauses_and_distinct_dinner_conventions_survive(self) -> None:
        flattened = " ".join(self.rules.split())
        for name in ("RUIN THE VIBE", "WEASILY WESLEY", "BAD VIBES BETTY",
                     "IM NOT A BIG OL BABY", "YOUR MOM", "WE DON'T HAVE ALL DAY",
                     "GET WORSE", "SKILL ISSUE", "SILLY BOY YOU SHOULDVE BEEN PAYING ATTENTION"):
            self.assertIn(name, flattened)
        horse = " ".join(self.sections["HORSE"].split())
        self.assertIn("purple lipstick", horse)
        self.assertIn("miniskirt", horse)
        self.assertIn("for the others whether they win or lose", horse)
        self.assertIn("for the loser(s)", self.sections["SHOOTING"])
        self.assertIn("not strict", self.sections["SHOOTING"])
        self.assertIn("not a unified payment obligation", flattened)

    def test_safety_overrides_are_explicit_not_financial_or_contact_rules(self) -> None:
        flattened = " ".join(self.rules.split())
        for phrase in ("Ball-to-ball only in a clear court", "Do not target or hit any people",
                       "eliminated, resting, or on their phone", "Pause for bystanders",
                       "Reckless contact stops play", "first aid", "no credit-card sharing",
                       "no passwords and no financial access", "voluntary, mutually agreed opt-in",
                       "No coerced humiliation", "Stop when asked", "No hate, threats"):
            self.assertIn(phrase, flattened)
        bump = " ".join(self.sections["BUMP"].split())
        self.assertIn("not a real rule", bump)
        self.assertIn("No credit cards, passwords or financial access", bump)
        self.assertIn("no hands or body on an opponent's ball", bump)
        self.assertIn("annoyingly good", bump)
        self.assertIn("unless Liam", bump)

    def test_unspecified_mechanics_are_not_silently_invented(self) -> None:
        text = " ".join(self.rules.split())
        for phrase in ("first picker is unrecorded", "Whether repeats are allowed is unspecified",
                       "does not prove a fixed opening rule", "Made-basket possession is unspecified",
                       "free-throw rebound handling", "reset the game where it previously ended",
                       "Decide the exact reset state before play", "operational interpretation",
                       "streak-reset handling", "not a verified source rule",
                       "pending clarification", "Do not invent first-to-five",
                       "selection mechanism is unspecified", "maximum of six",
                       "two or three players per round", "whether sudden-death attempts alternate shot for shot"):
            self.assertIn(phrase, text)
        self.assertIn("no fixed attempt budget", self.sections["3 POINT"])
        self.assertIn("not a demonstrated statistical effect", text)
        self.assertIn("if nobody has already reached four", text)

    def test_twenty_one_game_figures_plus_format_and_multiplayer_and_pitch(self) -> None:
        self.assertEqual(len(DIAGRAMS), 24)
        self.assertEqual(len({spec.slug for spec in DIAGRAMS}), 24)
        counts = Counter(spec.game for spec in DIAGRAMS)
        for heading, game in GAME_HEADINGS.items():
            refs = IMAGE_PATTERN.findall(self.sections[heading])
            self.assertEqual(counts[game], 3, game)
            self.assertEqual(len(refs), 3, game)
            self.assertEqual({Path(ref).stem for ref in refs},
                             {spec.slug for spec in DIAGRAMS if spec.game == game})
        rule_images = IMAGE_PATTERN.findall(self.rules)
        pitch_images = IMAGE_PATTERN.findall(self.pitch)
        self.assertEqual(len(rule_images), 23)
        self.assertEqual(len(pitch_images), 2)
        self.assertEqual(set(rule_images + pitch_images),
                         {f"tex_images/sports/{spec.slug}.png" for spec in DIAGRAMS})
        for text in (self.rules, self.pitch):
            self.assertEqual(text.count(r"\caption{"), len(IMAGE_PATTERN.findall(text)))

    def test_pitch_contains_ready_proposal_and_no_claim_of_outreach(self) -> None:
        text = " ".join(self.pitch.split())
        for phrase in ("Hello Jesser team", "Ludwig or Atrioc", "90-second original opener",
                       "0:00--0:20", "1:10--1:30", "6--10 minute", "one court", "two balls",
                       "no affiliation, endorsement", "No NBA footage rights",
                       "actual picker", "rim height", "accepted mercies", "assistance",
                       "explicit data opt-in separate from filming permission",
                       "Publish approved aggregate CSV", "no outreach",
                       "auto-publishes no raw or private data", "selection and clinch-truncation bias",
                       "not a forecast", "actual picker decisions were not logged"):
            self.assertIn(phrase.lower(), text.lower())
        for private_marker in ("@gmail.com", "@uwaterloo.ca", "LiamMcGrath_Resume", "WKRPT400", "C:\\Users"):
            self.assertNotIn(private_marker, self.rules + self.pitch)

    def test_pitch_snapshot_is_verified_against_engine_not_guessed(self) -> None:
        result = load_basketball(ROOT)
        summary = result["summary"]
        self.assertEqual(summary["seriesCount"], 13)
        self.assertEqual(summary["challengeCount"], 73)
        self.assertEqual(summary["seriesWins"], {"L": 12, "O": 1})
        self.assertEqual(summary["challengeWins"], {"L": 50, "O": 23})
        self.assertEqual(summary["currStreak"], {"player": "L", "length": 11})
        self.assertEqual(result["timing"]["bestOverall"]["seconds"], 82)
        self.assertEqual(summary["transitions"]["total"], 60)
        self.assertEqual(summary["transitions"]["retentions"], 35)
        self.assertEqual(summary["transitions"]["switches"], 25)
        by_id = {series["id"]: series for series in result["series"]}
        self.assertEqual((by_id["2026-09-10-1"]["order"], by_id["2026-09-10-1"]["finalScore"]), ("OLLOLOL", "4-3"))
        self.assertEqual((by_id["2026-09-16-1"]["order"], by_id["2026-09-16-1"]["finalScore"]), ("LLLOOL", "4-2"))
        for literal in ("13 completed series", "12--1", "50--23", "73 played challenges",
                        "11-series", "82 seconds", "60 transitions", "OLLOLOL", "LLLOOL",
                        "comeback attempt stopped"):
            self.assertIn(literal, " ".join(self.pitch.split()))


class SportsDiagramBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.paths = build_sports_diagrams(cls.root)

    def test_api_returns_all_absolute_paths_only_in_owned_asset_tree(self) -> None:
        expected = [self.root / "tex_images/sports" / f"{spec.slug}.{suffix}"
                    for spec in DIAGRAMS for suffix in ("png", "svg")]
        self.assertEqual(self.paths, expected)
        self.assertTrue(all(path.is_absolute() and path.is_file() for path in self.paths))
        self.assertEqual(set(fingerprints(self.root)),
                         {path.relative_to(self.root).as_posix() for path in expected})

    def test_import_does_not_generate_read_records_or_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            # The module needs only stdlib at import time and no source records.
            env = {**os.environ, "PYTHONPATH": str(ROOT)}
            result = subprocess.run([sys.executable, "-B", "-c", "import site_content.sports_diagrams"],
                                    cwd=directory, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertEqual(fingerprints(Path(directory)), {})

    def test_render_is_deterministic_across_roots_and_matches_shipped_assets(self) -> None:
        before = fingerprints(self.root)
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            build_sports_diagrams(str(other))
            self.assertEqual(before, fingerprints(other))
        self.assertEqual(fingerprints(self.root / "tex_images/sports"), fingerprints(ASSETS))

    def test_all_pngs_decode_and_svgs_contain_substantive_annotations(self) -> None:
        for spec in DIAGRAMS:
            with self.subTest(diagram=spec.slug):
                generated = self.root / "tex_images/sports"
                for root in (generated, ASSETS):
                    with Image.open(root / f"{spec.slug}.png") as image:
                        image.load()
                        self.assertEqual(image.format, "PNG")
                        self.assertEqual(image.size, (1920, 1120))
                        self.assertGreater(len(image.convert("RGB").getcolors(1920 * 1120) or []), 100)
                svg_path = generated / f"{spec.slug}.svg"
                svg = ET.fromstring(svg_path.read_bytes())
                texts = ["".join(node.itertext()) for node in svg.iter("{http://www.w3.org/2000/svg}text")]
                self.assertGreaterEqual(len(texts), 12, spec.slug)
                all_text = " ".join(texts)
                self.assertIn(spec.title, all_text)
                self.assertIn("Schematic, not official court dimensions", all_text)
                self.assertNotIn("HIGHJUMP", all_text)
                if spec.slug.endswith("_highjump"):
                    self.assertIn("HIGH JUMP RULES", all_text)
                    self.assertIn("Both creators competed in high jump", all_text)
                self.assertNotIn("<dc:date>", svg_path.read_text(encoding="utf-8"))
                self.assertIsNone(svg.find(".//{http://www.w3.org/2000/svg}image"), "SVG must remain vector")

    def test_tactic_svg_explicitly_protects_people_and_financial_access(self) -> None:
        svg = (self.root / "tex_images/sports/bump_tactics.svg").read_text(encoding="utf-8")
        for text in ("NO human targets", "resting/eliminated/on-phone", "first aid",
                     "No credit cards, passwords or financial access", "skip the tactic"):
            self.assertIn(text, svg)


class SportsConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.results = {}
        for name in ("basketball_rules", "creator_pitch"):
            cls.results[name] = convert_document(DOCUMENTS / f"{name}.tex", ASSETS,
                                                 cls.root / name, f"assets/{name}", source_root=ROOT)

    def test_both_articles_convert_without_warnings_or_unsupported_commands(self) -> None:
        for name, count in (("basketball_rules", 23), ("creator_pitch", 2)):
            with self.subTest(document=name):
                result = self.results[name]
                self.assertEqual(result["warnings"], [])
                self.assertEqual(result["image_count"], count)
                self.assertNotIn("tex-unsupported", result["body"])
                self.assertGreater(len(result["headings"]), 10)
                self.assertEqual((self.root / name / f"{name}.tex").read_bytes(),
                                 (DOCUMENTS / f"{name}.tex").read_bytes())

    def test_zero_based_numbering_survives_pandoc(self) -> None:
        soup = BeautifulSoup(self.results["basketball_rules"]["body"], "html.parser")
        zero_lists = soup.select('ol[start="0"]')
        self.assertEqual(len(zero_lists), 5)
        self.assertEqual([len(node.find_all("li", recursive=False)) for node in zero_lists], [7, 7, 6, 7, 9])
        rendered = " ".join(soup.get_text(" ", strip=True).split())
        self.assertEqual(rendered.count("HIGH JUMP RULES."), 3)
        self.assertEqual(rendered.count("because both creators competed in high jump"), 3)

    def test_all_source_paths_copy_decode_and_remain_available_to_parent_zip(self) -> None:
        for name, result in self.results.items():
            text = active((DOCUMENTS / f"{name}.tex").read_text(encoding="utf-8"))
            references = IMAGE_PATTERN.findall(text)
            output = self.root / name
            manifest = json.loads((output / "source-images.json").read_text(encoding="utf-8"))
            self.assertEqual([row["archive"] for row in manifest], references)
            for row in manifest:
                reference = Path(row["archive"])
                self.assertFalse(reference.is_absolute())
                self.assertNotIn("..", reference.parts)
                self.assertTrue(reference.as_posix().startswith("tex_images/sports/"))
                self.assertEqual(reference.suffix, ".png")
                source, copied = ROOT / reference, output / row["asset"]
                self.assertEqual(source.read_bytes(), copied.read_bytes())
                with Image.open(copied) as image:
                    image.load()
                    self.assertEqual(image.size, (1920, 1120))
            soup = BeautifulSoup(result["body"], "html.parser")
            for image in soup.find_all("img"):
                figure = image.find_parent("figure")
                self.assertIsNotNone(figure, "Each article image must belong to a captioned figure")
                assert figure is not None
                caption = figure.find("figcaption")
                self.assertIsNotNone(caption)
                assert caption is not None
                self.assertGreater(len(caption.get_text(" ", strip=True).split()), 10)
                src = unquote(str(image["src"]))
                self.assertTrue(src.startswith(f"assets/{name}/"))
                self.assertTrue((output / src.removeprefix(f"assets/{name}/")).is_file())
            self.assertEqual({p.suffix for p in output.iterdir()}, {".png", ".tex", ".json"})
            self.assertFalse(list(output.rglob("*.csv")), "The converter must not export raw records")


if __name__ == "__main__":
    unittest.main()