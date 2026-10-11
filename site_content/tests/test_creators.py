"""Respected-creators showcase contracts: pure rendering, no network, no site writes."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from site_content import creators
from site_content.creators import (
    BLOCKED_TERMS, CLOSING_ID, CREATORS, FIRST_SECTION_ID, TOP_ID, Creator, Highlight,
    creators_html, scroll_cue_html, section_id, visible_creators,
)

WEB = Path(__file__).resolve().parents[1] / "web"
PAYLOAD = '<img src=x onerror=alert(1)>"\'&</p><script>alert(2)</script>'
SCOPE_TOKENS = ("home-snap", "creator-", "scroll-cue", "snap-rail", "snap-section")


def soup(markup: str) -> BeautifulSoup:
    return BeautifulSoup(markup, "html.parser")


def friend(key: str) -> Creator:
    return next(creator for creator in CREATORS if creator.key == key)


def split_selectors(selector_list: str) -> list[str]:
    parts, depth, current = [], 0, ""
    for char in selector_list:
        depth += (char == "(") - (char == ")")
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    return [*parts, current.strip()]


def css_rule_selectors(css: str) -> list[str]:
    """Selectors of style rules, skipping at-rule preludes and keyframe steps."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@keyframes[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    selectors = []
    for prelude in re.findall(r"([^{}]+)\{[^{}]*\}", css):
        prelude = prelude.strip()
        if prelude and not prelude.startswith("@"):
            selectors.extend(split_selectors(prelude))
    return selectors


class RenderedSectionsTest(unittest.TestCase):
    def setUp(self):
        self.html = creators_html()
        self.doc = soup(self.html)

    def test_only_public_or_consented_entries_render_then_closing(self):
        ids = [section["id"] for section in self.doc.find_all("section")]
        self.assertEqual(ids, ["creator-owen", "creator-asha", "creator-3blue1brown", "creator-complexly", CLOSING_ID])
        for section in self.doc.find_all("section"):
            self.assertIn("creator-section", section["class"])
            self.assertIn("snap-section", section["class"])
        self.assertNotIn("<main", self.html)
        self.assertEqual([c.key for c in visible_creators()], ["owen", "asha", "3blue1brown", "complexly"])
        closing = self.doc.find(id=CLOSING_ID)
        self.assertIn("More respected creators are on the way", closing.get_text())
        self.assertEqual(closing.find("a", class_="creator-top")["href"], f"#{TOP_ID}")

    def test_public_entry_without_url_is_not_rendered(self):
        data = tuple(replace(c, url=None) if c.key == "complexly" else c for c in CREATORS)
        with patch.object(creators, "CREATORS", data):
            ids = [s["id"] for s in soup(creators_html()).find_all("section")]
        self.assertEqual(ids, ["creator-owen", "creator-asha", "creator-3blue1brown", CLOSING_ID])

    def test_friends_hidden_until_consent_and_url(self):
        asha = self.doc.find(id="creator-asha")
        self.assertIn("Shared with Asha’s permission.", asha.get_text())
        self.assertEqual(asha.select_one("a.creator-preview")["href"], "https://www.smallshots.ca/")
        owen = friend("owen")
        self.assertTrue(owen.consent)
        self.assertEqual(owen.url, "https://wwhattoeat.com/")
        section = self.doc.find(id="creator-owen")
        self.assertIn("Shared with Owen Paget’s permission.", section.get_text())
        self.assertEqual(section.select_one("a.creator-preview img")["src"], "assets/creators/owen.webp")
        entry = friend("camille")
        self.assertIsNone(entry.url)
        self.assertFalse(entry.consent)
        self.assertFalse(entry.public_figure)
        self.assertNotIn(entry.name.lower(), self.html.lower())
        self.assertNotIn(entry.name.lower(), scroll_cue_html(FIRST_SECTION_ID).lower())
        url = "https://camille.example.org/"
        cases = {
            "consent only": dict(consent=True),
            "url only": dict(url=url),
        }
        for label, change in cases.items():
            data = tuple(replace(c, **change) if c.key == "camille" else c for c in CREATORS)
            with self.subTest(label), patch.object(creators, "CREATORS", data):
                markup = creators_html()
                self.assertNotIn("camille", markup.lower())
                self.assertIsNone(soup(markup).find(id="creator-camille"))
        data = tuple(replace(c, url=url, consent=True, domains=("camille.example.org",)) if c.key == "camille" else c for c in CREATORS)
        with patch.object(creators, "CREATORS", data):
            doc = soup(creators_html())
            self.assertIsNotNone(doc.find(id="creator-camille"))
            self.assertIn("Shared with Camille’s permission.", doc.get_text())
        for bad in ("http://camille.example.org/", "https://camille.example.org/shop", "javascript:alert(1)"):
            data = tuple(replace(c, url=bad, consent=True) if c.key == "camille" else c for c in CREATORS)
            with self.subTest(bad), patch.object(creators, "CREATORS", data), self.assertRaises(ValueError):
                creators_html()

    def test_projects_not_live_yet_render_without_links(self):
        section = self.doc.find(id="creator-owen")
        pending = section.select("li.creator-highlight.is-pending")
        self.assertEqual([row.h3.get_text(" ", strip=True) for row in pending],
                         ["Creator Hub Coming soon", "Stock Monitoring Coming soon"])
        for row in pending:
            self.assertIsNone(row.find("a"))
            self.assertEqual(row.select_one("span.creator-symbol")["aria-hidden"], "true")

    def test_links_are_https_on_own_domains_and_never_commercial(self):
        for creator in visible_creators():
            section = self.doc.find(id=section_id(creator))
            links = [a for a in section.find_all("a") if not a["href"].startswith("#")]
            self.assertEqual(len(links), 1 + sum(item.url is not None for item in creator.highlights))
            for link in links:
                parts = urlsplit(link["href"])
                self.assertEqual(parts.scheme, "https")
                self.assertIn(parts.hostname, creator.domains)
                self.assertEqual(parts.netloc, parts.hostname)
                tokens = re.split(r"[^a-z0-9]+", link["href"].lower())
                self.assertFalse([t for t in tokens if t.startswith(BLOCKED_TERMS)], link["href"])
                for term in ("store", "merch", "shop", "donate", "patreon"):
                    self.assertNotIn(term, link["href"].lower())
                self.assertEqual(link["target"], "_blank")
                self.assertEqual(set(link["rel"]), {"noopener", "noreferrer"})

    def test_highlights_are_sourced_and_sized(self):
        for creator in visible_creators():
            self.assertTrue(3 <= len(creator.highlights) <= 5, creator.key)
            self.assertRegex(creator.verified, r"^\d{4}-\d{2}-\d{2}$")
            for item in creator.highlights:
                self.assertTrue(item.label and item.description)
                if item.url is None:
                    self.assertIsNone(item.source)
                    continue
                source = urlsplit(item.source)
                self.assertEqual(source.scheme, "https")
                self.assertIn(source.hostname, creator.domains)

    def test_symbol_links_have_accessible_names_and_descriptions(self):
        for creator in visible_creators():
            site = urlsplit(creator.url).hostname.removeprefix("www.")
            section = self.doc.find(id=section_id(creator))
            rows = section.select("li.creator-highlight")
            self.assertEqual(len(rows), len(creator.highlights))
            for row, item in zip(rows, creator.highlights):
                text = row.select_one(".creator-highlight-text")
                if item.url is None:
                    self.assertIs(text.find_next_sibling(), row.select_one("span.creator-symbol"))
                    continue
                symbol = row.select_one("a.creator-symbol")
                self.assertIs(text.find_next_sibling(), symbol, "description left, symbol right")
                self.assertEqual(symbol["aria-label"], f"Open {item.label} on {site} (opens in a new tab)")
                self.assertEqual(self.doc.find(id=symbol["aria-describedby"]).get_text(), item.description)
                self.assertEqual(symbol.svg["aria-hidden"], "true")
                self.assertEqual(symbol["href"], item.url)
            preview = section.select_one("a.creator-preview")
            self.assertEqual(preview["href"], creator.url)
            self.assertIn(f"Visit {site}", preview.get_text())
            self.assertIn(creator.name, preview.get_text())
            self.assertIn("(opens in a new tab)", preview.get_text())
            if creator.image is None:
                self.assertIsNone(preview.find("img"), "original art only until a consented image exists")
            if creator.public_figure:
                self.assertIn("not affiliated with or endorsed by", section.get_text())

    def test_ids_unique_and_references_resolve(self):
        page = soup(scroll_cue_html(FIRST_SECTION_ID) + self.html)
        ids = [tag["id"] for tag in page.find_all(id=True)]
        self.assertEqual(len(ids), len(set(ids)))
        known = set(ids) | {TOP_ID}
        for tag in page.find_all(attrs={"aria-labelledby": True}):
            self.assertIn(tag["aria-labelledby"], known)
        for tag in page.find_all(attrs={"aria-describedby": True}):
            self.assertIn(tag["aria-describedby"], known)
        for link in page.find_all("a", href=re.compile("^#")):
            self.assertIn(link["href"][1:], known)
        for ref in re.findall(r'url\(#([^)]+)\)', str(page)):
            self.assertIn(ref, ids)
        for section in page.find_all("section"):
            heading = page.find(id=section["aria-labelledby"])
            self.assertEqual(heading.name, "h2")
            self.assertTrue(section.find(id=section["aria-labelledby"]))

    def test_no_inline_script_style_or_handlers(self):
        for markup in (self.html, scroll_cue_html(FIRST_SECTION_ID)):
            doc = soup(markup)
            self.assertIsNone(doc.find("script"))
            self.assertIsNone(doc.find("style"))
            for tag in doc.find_all(True):
                self.assertNotIn("style", tag.attrs, tag.name)
                self.assertFalse([name for name in tag.attrs if name.lower().startswith("on")], tag.name)
            self.assertNotIn("javascript:", markup.lower())

    def test_every_data_field_is_escaped(self):
        hostile = Creator(
            key="payload", name=f"Name{PAYLOAD}", url="https://example.org/a?x=1&y=2",
            domains=("example.org",), public_figure=True, eyebrow=f"Eyebrow{PAYLOAD}",
            tagline=f"Tagline{PAYLOAD}", blurb=f"Blurb{PAYLOAD}", art="orbit", theme="jade",
            highlights=(Highlight(f"Label{PAYLOAD}", f"Description{PAYLOAD}",
                                  "https://example.org/b?p=1&q=2", "arrow", "https://example.org/"),),
            verified="2026-10-03",
        )
        with patch.object(creators, "CREATORS", (hostile,)):
            markup = creators_html()
        doc = soup(markup)
        self.assertIsNone(doc.find("script"))
        self.assertIsNone(doc.find("img"))
        for tag in doc.find_all(True):
            self.assertFalse([name for name in tag.attrs if name.lower().startswith("on")])
        text = doc.get_text()
        for field in ("Name", "Eyebrow", "Tagline", "Blurb", "Label", "Description"):
            self.assertIn(field + PAYLOAD, text)
        self.assertIn("&amp;y=2", markup)
        self.assertIn("&amp;q=2", markup)
        symbol = doc.select_one("a.creator-symbol")
        self.assertEqual(symbol["aria-label"], f"Open Label{PAYLOAD} on example.org (opens in a new tab)")
        self.assertIn('class="creator-orbit-initial" y="30" text-anchor="middle">N</text>', markup)

    def test_enumerated_and_structural_fields_are_rejected_not_rendered(self):
        base = next(c for c in CREATORS if c.key == "3blue1brown")
        good = base.highlights[0]
        bad_values = {
            "key": dict(key='x" onmouseover="1'),
            "theme": dict(theme=f"azure{PAYLOAD}"),
            "art": dict(art=PAYLOAD),
            "image external": dict(image="https://example.org/face.jpg"),
            "image traversal": dict(image="assets/creators/../../x.png"),
            "verified": dict(verified=PAYLOAD),
            "url quote": dict(url='https://www.3blue1brown.com/"><script>'),
            "url other domain": dict(url="https://evil.example/"),
            "url userinfo": dict(url="https://user@www.3blue1brown.com/"),
            "symbol": dict(highlights=(replace(good, symbol=PAYLOAD),)),
            "highlight domain": dict(highlights=(replace(good, url="https://store.dftba.com/collections/3blue1brown"),)),
            "highlight members": dict(highlights=(replace(good, url="https://www.3blue1brown.com/members"),)),
            "too many": dict(highlights=(good,) * 6),
        }
        for label, change in bad_values.items():
            with self.subTest(label), patch.object(creators, "CREATORS", (replace(base, **change),)):
                with self.assertRaises(ValueError):
                    creators_html()
        with patch.object(creators, "CREATORS", (base, base)), self.assertRaises(ValueError):
            creators_html()

    def test_future_consented_image_replaces_art(self):
        base = next(c for c in CREATORS if c.key == "complexly")
        with patch.object(creators, "CREATORS", (replace(base, image="assets/creators/complexly.webp"),)):
            preview = soup(creators_html()).select_one("a.creator-preview")
        self.assertEqual(preview.img["src"], "assets/creators/complexly.webp")
        self.assertEqual(preview.img["alt"], "")
        self.assertIsNone(preview.find("svg"))


class ScrollCueTest(unittest.TestCase):
    def test_cue_targets_first_section(self):
        self.assertEqual(FIRST_SECTION_ID, soup(creators_html()).find("section")["id"])
        cue = soup(scroll_cue_html(FIRST_SECTION_ID)).a
        self.assertEqual(cue["href"], f"#{FIRST_SECTION_ID}")
        self.assertIn("scroll-cue", cue["class"])
        self.assertEqual(cue.get_text(" ", strip=True), "Scroll to see other respected creators")
        self.assertEqual(cue.select_one(".scroll-cue-chevron")["aria-hidden"], "true")

    def test_invalid_targets_raise(self):
        for bad in ("", "#x", 'a" onclick="x', "1abc", None):
            with self.subTest(bad), self.assertRaises(ValueError):
                scroll_cue_html(bad)


class AssetContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (WEB / "creators.css").read_text(encoding="utf-8")
        cls.compact = re.sub(r"\s+", "", cls.css)
        cls.js = (WEB / "creators.js").read_text(encoding="utf-8")

    def test_snap_rules(self):
        for needle in (
            "html:has(main.home-snap){", "scroll-snap-type:ymandatory", "scroll-padding-top:var(--creator-header)",
            ".home-snap.snap-section{scroll-snap-align:start", "min-height:calc(100svh-var(--creator-header,87px))",
            "main.home-snap{overflow:visible;overflow-x:clip;}", ".site-footer{scroll-snap-align:end;}",
        ):
            self.assertIn(needle, self.compact)

    def test_reduced_motion_block(self):
        block = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\}", self.css, re.S)
        self.assertIsNotNone(block)
        body = re.sub(r"\s+", "", block.group(1))
        self.assertIn("scroll-behavior:auto", body)
        self.assertIn("animation:none!important", body)
        self.assertIn("transition:none!important", body)

    def test_every_rule_is_scoped(self):
        selectors = css_rule_selectors(self.css)
        self.assertGreater(len(selectors), 50)
        for selector in selectors:
            self.assertTrue(any(token in selector for token in SCOPE_TOKENS), selector)
        for name in re.findall(r"@keyframes\s+([\w-]+)", self.css):
            self.assertTrue(name.startswith("creator-"), name)

    def test_javascript_is_progressive_and_safe(self):
        self.assertIn('document.querySelector("main.home-snap")', self.js)
        self.assertIn("if (!main) return;", self.js)
        self.assertIn('setAttribute("aria-current"', self.js)
        for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "eval(", "document.write", "setAttribute(\"style\""):
            self.assertNotIn(banned, self.js)


if __name__ == "__main__":
    unittest.main()
