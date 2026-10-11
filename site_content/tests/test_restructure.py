"""Mental Map restructure: nothing from the merged notebook is lost, and the outline is complete.

The restructure itself is a pure function of the archived merge, so these checks
hold even after mental_map.tex gains new notes. The live file is only checked
for the outline markers the website depends on.
"""

from collections import Counter
from pathlib import Path
import re
import unittest

from site_content import restructure
from site_content.atlas import NODES, mental_map_anchors
from site_content.latex import _prepare

ROOT = Path(__file__).resolve().parents[2]
LABEL = re.compile(r"\\label\{([^{}]+)\}")
IMAGE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")


def body(text):
    return text.split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0]


def math(text):
    _, slots = _prepare(body(text), [])
    return Counter((slot.display, slot.payload) for slot in slots.values())


def comparable(lines):
    text = re.sub(r"(?<!\\)%[^\n]*", "", "\n".join(lines))
    text = LABEL.sub("", text.replace(restructure.TRANSITION, ""))
    return " ".join(text.split())


class RestructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged = restructure.MERGED.read_text(encoding="utf-8")
        cls.output, cls.manifest = restructure.restructure(cls.merged)
        cls.live = (ROOT / "mental_map.tex").read_text(encoding="utf-8")

    def test_every_math_payload_image_and_label_survives(self):
        self.assertEqual(math(self.output), math(self.merged))
        self.assertEqual(Counter(IMAGE.findall(self.output)), Counter(IMAGE.findall(self.merged)))
        old, new = Counter(LABEL.findall(self.merged)), Counter(LABEL.findall(self.output))
        self.assertFalse(old - new, "A label was lost")
        self.assertTrue(all(name.startswith("sec:") or name == "about-this-notebook" for name in new - old))

    def test_every_block_of_prose_appears_unchanged(self):
        flat = comparable(self.output.splitlines())
        _, _, _, blocks = restructure.parse(self.merged)
        for block in blocks:
            with self.subTest(block=" > ".join(block.path)):
                self.assertIn(comparable(restructure.clean(block.body)), flat)

    def test_every_earlier_heading_title_is_kept_or_named(self):
        _, _, _, blocks = restructure.parse(self.merged)
        for block in blocks:
            target, mode = restructure.PLACE.get(block.path, ("", "moved"))
            loose = [child for child in block.children if child.path not in restructure.PLACE]
            empty = not restructure.active(block.body) and not loose
            if mode == restructure.DROP or (mode == restructure.MERGE and target in NODES and (
                    empty or restructure._similar(block.title, NODES[target].title))):
                continue
            with self.subTest(title=block.title):
                self.assertTrue(re.search(r"\\(?:sub)*(?:section|paragraph)\*?\{" + re.escape(block.title) + r"\}", self.output)
                                or f"``{block.title}''" in self.output or block.path == ("Introductory Summary",))

    def test_outline_is_six_by_six_by_six_with_unique_labels(self):
        anchors = restructure.node_ids(restructure.place(restructure.parse(self.merged)[3])[0])
        self.assertEqual(len(anchors), 258)
        headings = re.findall(r"(?m)^% atlas: (\S+)\n\\((?:sub){0,2})section\{(.*)\}\\label\{([^{}]+)\}$", self.output)
        self.assertEqual([path for path, *_ in headings], [n.path for n in NODES.values() if n.depth])
        for path, subs, title, label in headings:
            node = NODES[path]
            self.assertEqual(len(subs) // 3 + 1, node.depth)
            self.assertEqual(title, node.title.replace("&", r"\&"))
            self.assertEqual(label, anchors[path])
        self.assertEqual(self.manifest["openDestinations"] + self.manifest["destinationsWithNotes"], 216)

    def test_live_notebook_keeps_every_outline_marker(self):
        anchors = mental_map_anchors(ROOT / "mental_map.tex")
        self.assertEqual(set(anchors), {n.path for n in NODES.values() if n.depth})
        self.assertEqual(len(set(anchors.values())), 258)
        self.assertEqual(self.live.count("\\label{about-this-notebook}"), 1)

    def test_levels_never_exceed_five_and_front_matter_is_unnumbered(self):
        self.assertNotRegex(body(self.output), r"\\paragraph\{")
        front = self.output.split(r"\section*{About this notebook}", 1)[1].split("% atlas:", 1)[0]
        self.assertFalse(re.search(r"\\(?:sub)*section\{", front), "Front matter headings must be starred")


if __name__ == "__main__":
    unittest.main()
