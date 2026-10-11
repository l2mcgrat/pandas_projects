"""Site atlas page contracts: static outline, icon templates, schema data and the browser layout."""

from dataclasses import replace
from html import escape
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from unittest.mock import patch
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from site_content import atlas, atlas_tree

HERE = Path(__file__).resolve().parents[1]
SCRIPT = HERE / "web" / "atlas-tree.js"
STYLES = HERE / "web" / "atlas-tree.css"
NODE = shutil.which("node")
SITE = "https://example.test/"
PAGE = urljoin(SITE, "Atlas/index.html")
EVIL = '<b onmouseover="alert(1)">Fields & "Things"</b>'
# Upright compass angles for top, upper-left, upper-right, lower-left, bottom, lower-right.
HEX_DEGREES = [270, 210, 330, 150, 90, 30]

NODE_SCRIPT = r"""
const api = require(process.argv[1]);
let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { raw += chunk; });
process.stdin.on("end", () => {
  const built = api.buildAtlas(JSON.parse(raw));
  const nodes = built.nodes.map((n) => {
    const label = api.labelBox(n);
    return {
      key: n.key, url: n.url, title: n.title, depth: n.depth, index: n.index, angle: n.angle,
      start: n.start, end: n.end, radius: n.radius, x: n.x, y: n.y,
      parent: n.parent ? n.parent.key : null, children: n.children.map((c) => c.key),
      lineage: api.lineage(n).map((m) => m.key), anchor: label.anchor, lines: label.lines,
      link: n.parent ? api.linkPath(n.parent, n) : null,
    };
  });
  process.stdout.write(JSON.stringify({ nodes, leaves: built.leaves.length, extent: built.extent }));
});
"""


def stub_icon(key: str) -> str:
    return f'<svg class="atlas-icon stub" data-icon="{escape(key)}" viewBox="0 0 64 64" aria-hidden="true"></svg>'


def parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def compass(angle: float) -> float:
    return angle % 360


class AtlasTreeBodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = atlas_tree.atlas_tree_body(icon=stub_icon)
        cls.soup = parse(cls.html)

    def test_body_is_exactly_one_main(self):
        self.assertTrue(self.html.lstrip().startswith("<main") and self.html.rstrip().endswith("</main>"))
        mains = self.soup.find_all("main")
        self.assertEqual(len(mains), 1)
        self.assertEqual(mains[0]["id"], "main-content")
        self.assertIn("atlas-tree-page", mains[0]["class"])
        self.assertEqual(self.soup.find_all("h1")[0].get("id"), "atlas-tree-title")
        self.assertEqual(len(self.soup.find_all("h1")), 1)

    def test_one_icon_template_per_node(self):
        templates = self.soup.select(".atlas-tree-templates > template[data-key]")
        self.assertEqual(len(templates), 259)
        keys = [template["data-key"] for template in templates]
        self.assertEqual(len(set(keys)), 259)
        self.assertEqual(set(keys), set(atlas.NODES))
        for template in templates:
            self.assertEqual(template.find("svg")["data-icon"], template["data-key"])
        self.assertTrue(self.soup.select_one(".atlas-tree-templates").has_attr("hidden"))

    def test_fallback_outline_links_every_node_once(self):
        outline = self.soup.select_one(".atlas-tree-outline")
        links = outline.find_all("a", href=True)
        self.assertEqual(len(links), 259)
        by_url = {urljoin(PAGE, link["href"]): link for link in links}
        self.assertEqual(len(by_url), 259)
        for node in atlas.NODES.values():
            with self.subTest(node=node.key):
                link = by_url[urljoin(SITE, node.url)]
                self.assertEqual(link["href"], "../" + node.url)
                self.assertEqual(link.get_text(), node.title)
                self.assertIn(f"tier-{node.depth}", link["class"])
        self.assertEqual(outline.select_one(".atlas-tree-out-root > a")["href"], "../index.html")

    def test_outline_nests_six_by_six_by_six(self):
        root = self.soup.select_one(".atlas-tree-out > li.atlas-tree-out-root")
        fields = root.select(":scope > ol.atlas-tree-out-fields > li")
        self.assertEqual([field.a.get_text() for field in fields], [node.title for node in atlas.ROOT.children])
        for field in fields:
            self.assertTrue(field.details.has_attr("open"))
            topics = field.select(":scope > details > ol.atlas-tree-out-topics > li")
            self.assertEqual(len(topics), 6)
            for topic in topics:
                self.assertEqual(len(topic.select(":scope > ol.atlas-tree-out-leaves > li > a")), 6)

    def test_ids_are_unique_and_references_resolve(self):
        ids = [tag["id"] for tag in self.soup.find_all(id=True)]
        self.assertEqual(len(ids), len(set(ids)))
        for attribute in ("for", "aria-describedby", "aria-labelledby"):
            for tag in self.soup.find_all(attrs={attribute: True}):
                value = tag[attribute]  # BeautifulSoup splits <output for> into a list
                for reference in value if isinstance(value, list) else value.split():
                    with self.subTest(attribute=attribute, reference=reference):
                        self.assertIn(reference, ids)

    def test_no_inline_scripts_styles_or_handlers_even_with_real_icons(self):
        from site_content.icons import ICONS, icon_svg

        real = atlas_tree.atlas_tree_body(icon=lambda key: icon_svg(key) if key in ICONS else stub_icon(key))
        for html in (self.html, real):
            soup = parse(html)
            self.assertEqual(soup.find_all(["script", "style", "iframe", "object", "embed"]), [])
            for tag in soup.find_all(True):
                for name in tag.attrs:
                    self.assertFalse(name.startswith("on"), f"{tag.name} has {name}")
                    self.assertNotEqual(name, "style")
            self.assertNotIn("javascript:", html.lower())

    def test_interactive_stage_is_progressive_enhancement(self):
        stage = self.soup.select_one("[data-atlas-stage]")
        self.assertTrue(stage.has_attr("hidden"))
        self.assertEqual(stage.select_one("[data-atlas-mount]")["data-prefix"], "../")
        detail = stage.select_one("[data-atlas-detail]")
        self.assertEqual(detail["role"], "status")
        self.assertEqual(detail["aria-live"], "polite")
        self.assertEqual(detail.select_one("[data-atlas-detail-open]")["href"], "../index.html")
        for hook in ("icon", "tier", "title", "meta", "trail", "name"):
            self.assertIsNotNone(detail.select_one(f"[data-atlas-detail-{hook}]"), hook)
        self.assertEqual(stage.select_one("form[role=search] label")["for"], "atlas-tree-query")
        self.assertEqual(stage.select_one("#atlas-tree-query")["type"], "search")
        zoom = {button["data-zoom"]: button for button in stage.select("button[data-zoom]")}
        self.assertEqual(set(zoom), {"in", "out", "reset"})
        for button in zoom.values():
            self.assertEqual(button["type"], "button")
        self.assertEqual(zoom["in"]["aria-label"], "Zoom in")
        self.assertEqual(zoom["out"]["aria-label"], "Zoom out")

    def test_intro_counts_come_from_the_outline(self):
        legend = [item.get_text(" ", strip=True) for item in self.soup.select(".atlas-tree-legend li")]
        self.assertEqual(legend, ["Centre 1", "Fields 6", "Topics 36", "Destinations 216"])
        lede = self.soup.select_one(".atlas-tree-intro .lede").get_text()
        for number in ("6 fields", "36 topics", "216 pages"):
            self.assertIn(number, lede)

    def test_titles_are_escaped(self):
        field = atlas.ROOT.children[0]
        topic = field.children[0]
        leaf = replace(topic.children[0], title=EVIL)
        topic = replace(topic, children=(leaf,) + topic.children[1:])
        field = replace(field, title=EVIL, children=(topic,) + field.children[1:])
        root = replace(atlas.ROOT, title=EVIL, children=(field,) + atlas.ROOT.children[1:])
        with patch.object(atlas_tree, "ROOT", root):
            html = atlas_tree.atlas_tree_body(icon=stub_icon)
            script = atlas_tree.atlas_schema_script()
        self.assertNotIn("<b onmouseover", html)
        self.assertIn(escape(EVIL), html)
        soup = parse(html)
        self.assertFalse(soup.find_all(attrs={"onmouseover": True}))
        texts = [link.get_text() for link in soup.select(".atlas-tree-outline a")]
        self.assertEqual(texts.count(EVIL), 3)
        self.assertEqual(soup.select_one("[data-atlas-detail-title]").get_text(), EVIL)
        self.assertNotIn("<", script)
        data = json.loads(script[len("window.SITE_ATLAS="):-1])
        self.assertEqual(data["t"], EVIL)
        self.assertEqual(data["c"][0]["c"][0]["c"][0]["t"], EVIL)


class AtlasSchemaScriptTests(unittest.TestCase):
    def test_schema_script_round_trips(self):
        text = atlas_tree.atlas_schema_script()
        self.assertTrue(text.startswith("window.SITE_ATLAS="))
        self.assertTrue(text.endswith(";"))
        self.assertNotIn("<", text)
        self.assertNotIn("\n", text)
        self.assertEqual(json.loads(text[len("window.SITE_ATLAS="):-1]), atlas.schema())

    def test_schema_script_matches_publishing_safe_json(self):
        try:
            from site_content.publishing import safe_json
        except Exception as error:  # publishing is edited elsewhere; this is only a cross-check
            self.skipTest(f"publishing unavailable: {error}")
        self.assertEqual(atlas_tree.atlas_schema_script(), "window.SITE_ATLAS=" + safe_json(atlas.schema()) + ";")
        tricky = {"t": "a</script>&\u2028b", "s": "", "c": []}
        self.assertEqual(atlas_tree._safe_json(tricky), safe_json(tricky))


def selectors(css: str) -> list[str]:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@keyframes[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    css = re.sub(r"@media[^{]+\{", "", css)
    found = []
    for group in re.findall(r"([^{}]+)\{[^{}]*\}", css):
        depth, part = 0, ""
        for char in group + ",":
            depth += char == "("
            depth -= char == ")"
            if char == "," and depth == 0:
                found.append(part.strip())
                part = ""
            else:
                part += char
    return [item for item in found if item]


class AtlasTreeAssetTests(unittest.TestCase):
    def test_css_is_scoped_and_offline(self):
        css = STYLES.read_text(encoding="utf-8")
        found = selectors(css)
        self.assertGreater(len(found), 60)
        for selector in found:
            self.assertTrue(selector.startswith(".atlas-tree"), selector)
        self.assertNotIn("@import", css)
        self.assertNotIn("http", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_script_is_generated_not_hardcoded(self):
        js = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"https?://[^\s\"']+", js), ["http://www.w3.org/2000/svg"])
        for node in atlas.NODES.values():
            if node.path:
                self.assertNotIn(node.path, js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("eval(", js)
        self.assertIn("module.exports", js)

    @unittest.skipUnless(NODE, "node is not installed")
    def test_node_syntax_check(self):
        result = subprocess.run([NODE, "--check", str(SCRIPT)], capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))


@unittest.skipUnless(NODE, "node is not installed")
class AtlasTreeLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run([NODE, "-e", NODE_SCRIPT, str(SCRIPT)], input=json.dumps(atlas.schema()).encode("utf-8"),
                                capture_output=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stderr.decode("utf-8", "replace"))
        cls.data = json.loads(result.stdout.decode("utf-8"))
        cls.nodes = {node["key"]: node for node in cls.data["nodes"]}

    def test_counts(self):
        self.assertEqual(len(self.data["nodes"]), 259)
        self.assertEqual(len(self.nodes), 259)
        self.assertEqual(self.data["leaves"], 216)
        self.assertEqual(sum(not node["children"] for node in self.nodes.values()), 216)
        for node in self.nodes.values():
            if node["depth"] < 3:
                self.assertEqual(len(node["children"]), 6, node["key"])

    def test_urls_titles_and_lineage_match_python(self):
        self.assertEqual(set(self.nodes), set(atlas.NODES))
        for key, node in self.nodes.items():
            with self.subTest(key=key):
                source = atlas.NODES[key]
                self.assertEqual(node["url"], source.url)
                self.assertEqual(node["title"], source.title)
                self.assertEqual(node["depth"], source.depth)
                self.assertEqual(node["index"], source.index)
                self.assertEqual(node["lineage"], [item.key for item in atlas.lineage(source)])

    def test_radii_form_distinct_increasing_tiers(self):
        radii = []
        for depth in range(4):
            values = {node["radius"] for node in self.nodes.values() if node["depth"] == depth}
            self.assertEqual(len(values), 1, depth)
            radii.append(values.pop())
        self.assertEqual(radii[0], 0)
        self.assertEqual(radii, sorted(set(radii)))
        for node in self.nodes.values():
            self.assertAlmostEqual(math.hypot(node["x"], node["y"]), node["radius"], delta=0.02)
        self.assertGreater(self.data["extent"], radii[-1])

    def test_fields_take_the_hexagon_slots(self):
        fields = [self.nodes[child] for child in self.nodes["root"]["children"]]
        self.assertEqual([compass(field["angle"]) for field in fields], HEX_DEGREES)
        self.assertEqual([field["key"] for field in fields], [node.key for node in atlas.ROOT.children])
        for field in fields:
            self.assertAlmostEqual(field["end"] - field["start"], 60)
            self.assertAlmostEqual((field["start"] + field["end"]) / 2, field["angle"])
        edges = sorted(compass(field["start"]) for field in fields)
        self.assertEqual(edges, [0, 60, 120, 180, 240, 300])

    def test_children_fan_clockwise_inside_parent_wedge(self):
        for node in self.nodes.values():
            if node["depth"] < 1 or not node["children"]:
                continue
            children = [self.nodes[key] for key in node["children"]]
            for child in children:
                with self.subTest(child=child["key"]):
                    self.assertGreaterEqual(child["start"], node["start"] - 1e-9)
                    self.assertLessEqual(child["end"], node["end"] + 1e-9)
                    self.assertTrue(child["start"] < child["angle"] < child["end"])
            angles = [child["angle"] for child in children]
            self.assertEqual(angles, sorted(angles))

    def test_leaf_angles_are_unique_and_evenly_spaced(self):
        leaves = sorted(compass(node["angle"]) for node in self.nodes.values() if not node["children"])
        self.assertEqual(len(set(round(angle, 6) for angle in leaves)), 216)
        gaps = [b - a for a, b in zip(leaves, leaves[1:])] + [leaves[0] + 360 - leaves[-1]]
        self.assertAlmostEqual(min(gaps), 360 / 216, places=6)
        self.assertAlmostEqual(max(gaps), 360 / 216, places=6)

    def test_labels_read_outward_and_links_join_nodes(self):
        for node in self.nodes.values():
            with self.subTest(key=node["key"]):
                if node["depth"] >= 2:
                    left = math.cos(math.radians(node["angle"])) < -1e-9
                    self.assertEqual(node["anchor"], "end" if left else "start")
                else:
                    self.assertEqual(node["anchor"], "middle")
                self.assertEqual(" ".join(node["lines"]), node["title"])
                if node["parent"]:
                    parent = self.nodes[node["parent"]]
                    number = r"-?\d+(?:\.\d+)?"
                    start = re.match(rf"M({number}),({number})", node["link"])
                    end = re.search(rf"({number}),({number})$", node["link"])
                    self.assertEqual((float(start[1]), float(start[2])), (parent["x"], parent["y"]))
                    self.assertEqual((float(end[1]), float(end[2])), (node["x"], node["y"]))


if __name__ == "__main__":
    unittest.main()
