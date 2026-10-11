"""LeetCode and Rap destination content: escaped code and lyrics in collapsible entries, no scripts.

leetcode_content(page, catalog, root) and rap_content(page, catalog, root) return
(lede, markup) for leaf_body; page is the destination slug, root the prefix to the site root.
"""

from __future__ import annotations

from collections import Counter
from html import escape
import re
from typing import Any

from .atlas_views import ALGORITHMS, FEELINGS, LEETCODE, VOCABULARY

__all__ = ["leetcode_content", "rap_content"]

LEETCODE_RULES = {
    "Lists-and-Arrays": "Every solution in arrays_and_strings.py, hash_tables.py and biggest_prime.py, except tree problems.",
    "Trees-and-Tries": "Every solution in trees_and_tries.py, plus tree problems solved with hash tables. Trie problems are next in the source.",
    "Graphs": ("Traversal and depth problems. There are no general graph problems in the source yet; trees are the connected, "
               "acyclic case, so these breadth- and depth-first searches are the same graph searches."),
    "Dynamic-Programming": "Solutions that keep a dp or memo table, or use functools.lru_cache.",
    "Recursion": "Solutions in which a function calls itself, found by reading the code's syntax tree.",
    "Hard-Problems": "Problems LeetCode rates Hard, and attempts the source marks as only partly passing.",
}


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "item"


def _source(catalog: dict, repo: str, what: str) -> str:
    url, commit = catalog.get("sourceUrl"), catalog.get("commit")
    name = f'<a href="{_e(url)}" rel="noopener noreferrer">{_e(repo)} ↗</a>' if url else _e(repo)
    at = f" at commit <code>{_e(commit[:7])}</code>" if commit else ""
    return f'<p class="catalog-source">From {name}{at}. {_e(what)}</p>'


def _item(ident: str, title: str, meta: str, body: str, url: str | None, extra: str = "") -> str:
    link = f'<a href="{_e(url)}" rel="noopener noreferrer">View on GitHub ↗</a>' if url else '<span>Not on GitHub yet: a local draft.</span>'
    return (f'<details class="catalog-item" id="{_e(ident)}"><summary><span class="catalog-title">{_e(title)}</span>'
            f'<span class="catalog-meta">{_e(meta)}</span></summary>{body}<p class="catalog-links">{link}{extra}</p></details>')


def _section(title: str, head: str, groups: dict[str, list[tuple[str, str, str]]]) -> str:
    """groups: heading -> [(id, label, item markup)]; renders an index and the grouped items."""
    index = "".join(f'<li><a href="#{_e(ident)}">{_e(label)}</a></li>' for items in groups.values() for ident, label, _ in items)
    body = "".join(f'<h3 class="catalog-group">{_e(name)}</h3>' + "".join(markup for _, _, markup in items) for name, items in groups.items())
    return (f'<section class="catalog" aria-labelledby="catalog-title"><div class="catalog-head"><h2 id="catalog-title">{_e(title)}</h2>{head}</div>'
            f'<details class="catalog-index"><summary>Index</summary><ol>{index}</ol></details>{body}</section>')


def leetcode_content(page: str, catalog: dict, root: str) -> tuple[str, str]:
    problems = [p for p in catalog["problems"] if page in p["pages"]]
    rule = f'<p class="catalog-rule"><strong>On this page:</strong> {_e(LEETCODE_RULES[page])}</p>'
    source = _source(catalog, "l2mcgrat/leetcode_problems", "Code is shown as written, test lines included; this site never runs it.")
    if not problems:
        empty = (f'<section class="catalog" aria-labelledby="catalog-title"><div class="catalog-head"><h2 id="catalog-title">No solutions yet</h2>{rule}{source}'
                 f'<p class="catalog-empty">Nothing in leetcode_problems matches yet, so this page fills itself once one does. Until then, '
                 f'the <a href="{_e(root + ALGORITHMS)}">illustrated algorithms reader</a> covers the idea.</p></div></section>')
        return "No solutions in leetcode_problems match this destination yet; its selection rule is below.", empty
    groups: dict[str, list[tuple[str, str, str]]] = {}
    for problem in problems:
        ident = f'p-{_slug(problem["module"])}-{problem["line"]}'
        lines = (f'lines {problem["line"]}–{problem["endLine"]}' if problem["endLine"] > problem["line"]
                 else f'line {problem["line"] - 1}')
        flags = [label for flag, label in ((problem["recursive"], "Recursive"), (problem["status"] == "partial", "Partly passing"),
                                           (problem["status"] == "heading", "Heading only")) if flag]
        meta = " · ".join([problem["path"], lines, *flags])
        body = (f'<pre class="catalog-code"><code>{_e(problem["code"])}</code></pre>' if problem["status"] != "heading"
                else '<p class="catalog-empty">The source has this heading with no solution under it yet.</p>')
        groups.setdefault(f'{problem["moduleTitle"]} · {problem["group"]}' if problem["group"] != problem["moduleTitle"]
                          else problem["moduleTitle"], []).append((ident, problem["title"], _item(ident, problem["title"], meta, body, problem["url"])))
    solved = sum(p["status"] != "heading" for p in problems)
    files = sorted({p["path"] for p in problems})
    lede = (f"{solved} solution{'s' * (solved != 1)} from leetcode_problems ({', '.join(files)}), shown as written. "
            "Open any entry to read the code.")
    more = f'<p class="catalog-source">Every module, function and class is also listed in the <a href="{_e(root + LEETCODE)}">source index</a>.</p>'
    return lede, _section(f"{len(problems)} entries", rule + source + more, groups)


def rap_content(page: str, catalog: dict, root: str) -> tuple[str, str]:
    songs = [s for s in catalog["songs"] if s["page"] == page]
    tools = catalog["tools"] if page == "Future-Projects" else []
    explore = (f'<p class="catalog-source">Word counts and feelings for every song are in the <a href="{_e(root + VOCABULARY)}">vocabulary</a> '
               f'and <a href="{_e(root + FEELINGS)}">feelings</a> explorers.</p>')
    sections = []
    if songs:
        drafts = sum(not s["url"] for s in songs)
        note = "Lyrics are shown as written." + (f" {drafts} draft{'s' * (drafts != 1)} not yet on GitHub {'are' if drafts != 1 else 'is'} shown without a link." if drafts else "")
        groups: dict[str, list[tuple[str, str, str]]] = {}
        seen: Counter[str] = Counter()
        for song in songs:
            ident = f's-{_slug(song["path"].rsplit(".", 1)[0])}'
            seen[ident] += 1
            ident += f'-{seen[ident]}' if seen[ident] > 1 else ""
            body = f'<pre class="catalog-lyrics">{_e(song["text"])}</pre>'
            meta = f'{song["lines"]} lines · {song["words"]} words'
            groups.setdefault(song["folderTitle"], []).append((ident, song["title"], _item(ident, song["title"], meta, body, song["url"])))
        sections.append(_section(f"{len(songs)} song{'s' * (len(songs) != 1)}", _source(catalog, "l2mcgrat/music_work", note) + explore, groups))
    if tools:
        items = "".join(_item(f't-{_slug(tool["name"])}', tool["name"], tool["description"],
                              f'<pre class="catalog-code"><code>{_e(tool["code"])}</code></pre>', tool["url"]) for tool in tools)
        sections.append(f'<section class="catalog" aria-labelledby="catalog-tools-title"><div class="catalog-head">'
                        f'<h2 id="catalog-tools-title">The production tools</h2>'
                        f'{_source(catalog, "l2mcgrat/music_work", "Scripts for turning recordings into visuals, shown as written; this site never runs them.")}'
                        '<p class="catalog-rule">Upcoming releases go through these: convert a recording to WAV, then export a waveform and '
                        'spectrum video for it. Lyric folders not yet placed on a Rap page also appear here.</p></div>'
                        f'{items}</section>')
    folders = sorted({s["folderTitle"] for s in songs})
    if songs:
        lede = (f"{len(songs)} song{'s' * (len(songs) != 1)} from music_work ({', '.join(folders)}), lyrics as written. "
                f"Open any song to read it.")
    elif tools:
        lede = "What comes next: the scripts that turn new recordings into visuals."
    else:
        lede = "No music_work folder is placed on this page yet."
    return lede, "".join(sections)
