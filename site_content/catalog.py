"""LeetCode solutions and rap projects from the sibling repositories, sorted onto atlas pages.

leetcode_catalog(repo) splits each .py file of leetcode_problems at its "# Problem title"
comments; rap_catalog(repo) reads every lyric .txt and the root-level tools of music_work.
Code is read as text and parsed with ast only to spot recursion: nothing is imported or run.
Raw strings are returned; the views escape them. Files missing from Git keep url None, so
an uncommitted draft never gets a broken GitHub link.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from .analysis import _files, _git, _provenance, _require_repo, _source_url, _words

# ---- LeetCode -------------------------------------------------------------------------

MODULE_TITLES = {"arrays_and_strings": "Arrays and Strings", "hash_tables": "Hash Tables",
                 "trees_and_tries": "Trees and Tries", "biggest_prime": "Biggest Prime"}
# Primary pages by module; other pages are technique pages that cross-list problems.
MODULE_PAGES = {"arrays_and_strings": "Lists-and-Arrays", "hash_tables": "Lists-and-Arrays",
                "trees_and_tries": "Trees-and-Tries", "biggest_prime": "Lists-and-Arrays"}
TREE_TITLE = re.compile(r"\b(?:Tree|Subtrees?|BST|Trie)\b")
GRAPH_TITLE = re.compile(r"\b(?:Traversal|BFS|DFS|Depth|Graph|Islands?|Course|Network|Clone)\b")
DP_NAMES = frozenset({"dp", "memo", "lru_cache"})
# LeetCode's own difficulty rating; the repository records no difficulty itself.
HARD_TITLES = frozenset({"Contains Duplicate III"})
PARTIAL = re.compile(r"\b\d+/\d+ cases passed\b|\bfails\b", re.I)
_BANNER = re.compile(r"#{3,}\s*(.*?)\s*#*")
_HEADING = re.compile(r"# ([^=]+?)\s*")


def _recursive(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and (
                        isinstance(call.func, ast.Name) and call.func.id == node.name
                        or isinstance(call.func, ast.Attribute) and call.func.attr == node.name
                        and isinstance(call.func.value, ast.Name) and call.func.value.id == "self"):
                    return True
    return False


def _memoized(tree: ast.AST) -> bool:
    return any(isinstance(node, ast.Name) and node.id in DP_NAMES or isinstance(node, ast.Attribute) and node.attr in DP_NAMES
               for node in ast.walk(tree))


def _problem(module: str, group: str, title: str, lines: list[str], start: int, path: str, tracked: bool,
             repo_url: str | None, commit: str | None) -> dict[str, Any] | None:
    body = lines[start:]
    while body and body[-1].strip() in {"", "'''", '"""'}:
        body.pop()
    while body and not body[0].strip():
        body.pop(0)
        start += 1
    code = "\n".join(body)
    empty = not any(line.strip() and not line.lstrip().startswith("#") for line in body)
    if title == "Next Problem" and empty:
        return None  # An empty slot left for the next problem.
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None
    first, end = start + 1, start + len(body)  # 1-based lines of the shown code
    url = _source_url(repo_url, commit, path, first) if tracked else None
    if url and end > first:
        url += f"-L{end}"
    status = "heading" if empty else "partial" if PARTIAL.search(title) else "solved"
    pages = [] if empty else [MODULE_PAGES.get(module, "Lists-and-Arrays")]
    if not empty and module != "trees_and_tries" and TREE_TITLE.search(title):
        pages = ["Trees-and-Tries"]
    if not empty and GRAPH_TITLE.search(title) and not title.startswith("Construct"):
        pages.append("Graphs")
    if tree is not None and _memoized(tree):
        pages.append("Dynamic-Programming")
    if tree is not None and _recursive(tree):
        pages.append("Recursion")
    if title.split(" (")[0] in HARD_TITLES or re.search(r"\bHard\b", title) or status == "partial":
        pages.append("Hard-Problems")
    return {"title": title, "module": module, "moduleTitle": MODULE_TITLES.get(module, module.replace("_", " ").title()),
            "group": group, "path": path, "line": first, "endLine": end, "code": code, "url": url,
            "status": status, "recursive": tree is not None and _recursive(tree), "pages": pages}


def leetcode_catalog(repo: Path) -> dict[str, Any]:
    repo = _require_repo(repo)
    repo_url, commit = _provenance(repo)
    tracked = set((_git(repo, "ls-files") or "").splitlines())
    files, _ = _files(repo, ".py")
    problems = []
    for file in files:
        path = file.relative_to(repo).as_posix()
        module = file.stem
        lines = file.read_text(encoding="utf-8-sig").splitlines()
        group = MODULE_TITLES.get(module, module)
        title, start, banners = None, 0, 0
        found = []

        def close(end: int) -> None:
            if title is not None:
                found.append(_problem(module, group_at_start, title, lines[:end], start, path, path in tracked, repo_url, commit))

        group_at_start = group
        for index, line in enumerate(lines):
            before = index == 0 or not lines[index - 1].strip() or lines[index - 1].startswith("###")
            after = index + 1 < len(lines) and not lines[index + 1].strip()
            if line.startswith("###"):
                close(index)
                title = None
                if (banner := _BANNER.fullmatch(line)) and banner[1]:
                    banners += 1
                    group = banner[1] if banners > 1 else group  # The first titled banner names the file.
            elif (heading := _HEADING.fullmatch(line)) and before and after and not line.startswith(("#!", "# -*-")):
                close(index)
                title, start, group_at_start = heading[1], index + 1, group
        close(len(lines))
        if not any(found):  # A file with no headings is one problem, e.g. biggest_prime.py.
            first = next((i for i, line in enumerate(lines) if line.startswith(("import", "from", "def", "class"))), 0)
            found = [_problem(module, MODULE_TITLES.get(module, module), MODULE_TITLES.get(module, module),
                              lines, first, path, path in tracked, repo_url, commit)]
        problems.extend(item for item in found if item)
    return {
        "sourceUrl": repo_url, "commit": commit, "problems": problems,
        "methodology": ("Each column-0 '# Title' comment with blank lines around it starts a problem; '###' banners name groups. "
                        "Code is shown as written, including blocks kept inside a string. Lists and Arrays and Trees and Tries take "
                        "problems by file (tree titles from Hash Tables move to Trees); Graphs takes traversal and depth titles, "
                        "not tree construction; "
                        "Recursion takes code where a function calls itself; Dynamic Programming takes code using a dp/memo table "
                        "or cache; Hard Problems takes LeetCode Hard titles and attempts the source marks as partly passing. "
                        "Nothing is imported or run."),
    }


# ---- Rap -----------------------------------------------------------------------------

RAP_PAGES = {
    "Seven-Deadly-Sins": ("Seven_Deadly_Sins", "Seven_Deadly_Sins2_v1", "Seven_Deadly_Sins2_v2", "Seven_Deadly_Sins2_v3"),
    "Homewood-and-Trafalgar": ("Homewood", "Trafalgar"),
    "Made-in-Abyss": ("Made_in_Abyss",),
    "Vagabond": ("Vagabond",),
    "NanoFtheAbove": ("Old_Classics", "My_Hero_Academia"),
    "Future-Projects": (),  # Production tools, plus any folder not yet placed.
}
FOLDER_TITLES = {"Seven_Deadly_Sins2_v1": "Seven Deadly Sins 2 · version 1 (the sins)",
                 "Seven_Deadly_Sins2_v2": "Seven Deadly Sins 2 · version 2 (the virtues)",
                 "Seven_Deadly_Sins2_v3": "Seven Deadly Sins 2 · version 3"}
TOOLS = {
    "music_visualizer.py": "Draws a .wav file as a waveform and/or spectrum, live or exported to PNG or MP4.",
    "export_visualizations.ps1": "Batch-exports a folder of songs through the visualizer into one output folder.",
    "convert_audio_to_wav.ps1": "Converts common audio formats (and mislabelled .wav files) to standard PCM .wav with ffmpeg.",
}


def rap_catalog(repo: Path) -> dict[str, Any]:
    repo = _require_repo(repo)
    repo_url, commit = _provenance(repo)
    tracked = set((_git(repo, "ls-files") or "").splitlines())
    placed = {folder: page for page, folders in RAP_PAGES.items() for folder in folders}
    files, _ = _files(repo, ".txt")
    songs = []
    for file in files:
        path = file.relative_to(repo).as_posix()
        if "/" not in path:
            continue  # Root-level text is not a lyric.
        folder = path.split("/")[0]
        text = file.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip("\n")
        songs.append({"title": file.stem.replace("_", " "), "folder": folder,
                      "folderTitle": FOLDER_TITLES.get(folder, folder.replace("_", " ")),
                      "page": placed.get(folder, "Future-Projects"), "path": path, "text": text,
                      "lines": sum(1 for line in text.splitlines() if line.strip()), "words": len(_words(text)),
                      "url": _source_url(repo_url, commit, path) if path in tracked else None})
    tools = []
    for name, description in TOOLS.items():
        file = repo / name
        if file.is_file():
            tools.append({"name": name, "description": description, "path": name,
                          "code": file.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip("\n"),
                          "url": _source_url(repo_url, commit, name) if name in tracked else None})
    return {
        "sourceUrl": repo_url, "commit": commit, "songs": songs, "tools": tools,
        "methodology": ("Every .txt lyric file in a music_work folder, shown as written; folders map to pages by name, and a "
                        "folder not yet placed appears under Future Projects. Root-level production scripts are shown as code. "
                        "Files not yet committed to GitHub are shown without a link. Nothing is run."),
    }
