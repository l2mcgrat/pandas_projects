"""Circular site atlas page: static outline and icon templates; the browser draws the tree."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from html import escape
import json

from .atlas import ROOT, Node, schema, walk
from .icons import icon_svg

PREFIX = "../"
TIERS = ("Centre", "Fields", "Topics", "Destinations")


def _safe_json(data: object) -> str:
    # Identical to publishing.safe_json; publishing imports this module, so importing it back would be circular.
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
            .replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def atlas_schema_script() -> str:
    """Contents of assets/data/atlas-schema.js."""
    return "window.SITE_ATLAS=" + _safe_json(schema(ROOT)) + ";"


def _href(node: Node) -> str:
    return escape(PREFIX + node.url)


def _outline_item(node: Node) -> str:
    link = f'<a class="atlas-tree-out-link tier-{node.depth}" href="{_href(node)}">{escape(node.title)}</a>'
    if not node.children:
        return f"<li>{link}</li>"
    items = "".join(_outline_item(child) for child in node.children)
    if node.depth == 1:
        leaves = sum(len(child.children) for child in node.children)
        return (f'<li class="atlas-tree-out-field">{link}<details open><summary>{len(node.children)} topics · '
                f'{leaves} destinations</summary><ol class="atlas-tree-out-topics">{items}</ol></details></li>')
    level = "fields" if node.depth == 0 else "leaves"
    return f'<li class="atlas-tree-out-{"root" if node.depth == 0 else "topic"}">{link}<ol class="atlas-tree-out-{level}">{items}</ol></li>'


def atlas_tree_body(icon: Callable[[str], str] = icon_svg) -> str:
    nodes = list(walk(ROOT))
    counts = Counter(node.depth for node in nodes)
    fields, topics, leaves = counts[1], counts[2], counts[3]
    legend = "".join(f'<li class="tier-{depth}"><span class="atlas-tree-swatch" aria-hidden="true"></span>'
                     f'{name} <b>{counts[depth]}</b></li>' for depth, name in enumerate(TIERS))
    templates = "".join(f'<template data-key="{escape(node.key)}">{icon(node.key)}</template>' for node in nodes)
    root = escape(ROOT.title)
    return f'''<main id="main-content" class="atlas-tree-page">
  <header class="atlas-tree-intro">
    <p class="eyebrow"><span class="status-dot"></span> Site atlas · every page at a glance</p>
    <h1 id="atlas-tree-title">One centre, <em>every branch.</em></h1>
    <p class="lede">The whole notebook as a single tree. From the centre, {fields} fields branch into {topics} topics, and every topic into six destinations: {leaves} pages around the rim. Hover or focus any node to trace its path back to the centre, search for a page by name, then follow the link to jump straight there.</p>
    <ul class="atlas-tree-legend" aria-label="Tiers of the atlas">{legend}</ul>
  </header>
  <section class="atlas-tree-stage" aria-labelledby="atlas-tree-map-title" data-atlas-stage hidden>
    <h2 id="atlas-tree-map-title" class="atlas-tree-visually-hidden">Radial map of the site</h2>
    <div class="atlas-tree-toolbar">
      <form class="atlas-tree-search" role="search" data-atlas-search>
        <label for="atlas-tree-query">Find a page</label>
        <span class="atlas-tree-search-row"><input id="atlas-tree-query" type="search" autocomplete="off" spellcheck="false" placeholder="e.g. Quantum Mechanics" aria-describedby="atlas-tree-search-status"><button class="button ghost" type="submit">Find</button></span>
        <output id="atlas-tree-search-status" class="atlas-tree-search-status" for="atlas-tree-query" aria-live="polite"></output>
      </form>
      <div class="atlas-tree-zoom" role="group" aria-label="Map zoom">
        <button class="button ghost" type="button" data-zoom="out" aria-label="Zoom out">−</button>
        <span class="atlas-tree-zoom-level" aria-live="polite" data-atlas-zoom-level>100%</span>
        <button class="button ghost" type="button" data-zoom="in" aria-label="Zoom in">+</button>
        <button class="button ghost" type="button" data-zoom="reset">Reset view</button>
      </div>
    </div>
    <p class="atlas-tree-hint" id="atlas-tree-hint">Tab into the map, then use ← and → to move inward or outward, ↑ and ↓ to travel around a ring, Home for the centre and Enter to open. Zoom with the buttons, Ctrl + scroll or a pinch; drag to pan. Every page is also listed below the map.</p>
    <div class="atlas-tree-layout">
      <div class="atlas-tree-viewport" data-atlas-mount data-prefix="{PREFIX}"></div>
      <div class="atlas-tree-detail" role="status" aria-live="polite" aria-atomic="true" data-atlas-detail>
        <div class="atlas-tree-detail-icon" data-atlas-detail-icon></div>
        <div class="atlas-tree-detail-copy">
          <p class="atlas-tree-detail-tier" data-atlas-detail-tier>Centre</p>
          <p class="atlas-tree-detail-title" data-atlas-detail-title>{root}</p>
          <p class="atlas-tree-detail-meta" data-atlas-detail-meta>{fields} fields · {topics} topics · {leaves} destinations</p>
          <ol class="atlas-tree-trail" aria-label="Path from the centre" data-atlas-detail-trail><li><span aria-current="location">{root}</span></li></ol>
          <a class="button primary atlas-tree-open" href="{_href(ROOT)}" data-atlas-detail-open>Open <span class="atlas-tree-visually-hidden" data-atlas-detail-name>{root}</span> <span aria-hidden="true">↗</span></a>
        </div>
      </div>
    </div>
  </section>
  <section class="atlas-tree-outline" aria-labelledby="atlas-tree-outline-title">
    <div class="atlas-tree-outline-head"><p class="eyebrow">Outline</p><h2 id="atlas-tree-outline-title">Every page, as a list</h2></div>
    <ol class="atlas-tree-out">{_outline_item(ROOT)}</ol>
  </section>
  <div class="atlas-tree-templates" hidden>{templates}</div>
</main>'''
