"""Read-only, deterministic data for the music and coding readers (schema 1).

Public APIs: analyze_music(Path), analyze_code(Path), music_rows(music_result).
No sibling module is imported/executed, no network access or output files are
created. Only Git config/revision queries run. Missing directories raise
FileNotFoundError; decoding/parsing errors propagate, never become stale data.

Music keys: schemaVersion, source, summary, frequencies, songs, emotions.
source: repoUrl, commit, counts, exclusions, methodology. Song aliases contain
title/collection/path/sourceUrl; the canonical song has these plus id, metrics,
frequencies and lines. Metrics include hapaxCount and mattrWindowCount as well
as tokenCount/vocabularySize/ttr/mattr. Frequency rows are word/count/songCount/
isStopword. Lines have number/text/tokens/polarity/emotion/subemotion/matches/
evidence/ambiguous/emotionScores/tiedEmotions. Evidence offsets are zero-based,
half-open Python character and token offsets in the original physical line.

Emotion scores are cue occurrence counts, NOT probabilities. These are custom
exploratory text categories inspired by the supplied 12-family feelings-wheel
description, not a reproduction of a particular wheel or a diagnosis of the
writer. Sarcasm, characters, quotations, slang and narrative voice are not
resolved. VADER is used ONLY for polarity. All display strings remain plain,
unescaped data: the publisher must use textContent/HTML escaping, safe JSON
embedding (including </script>), and spreadsheet-safe CSV cells if needed.

music_rows returns flat, scalar-only CSV-ready tables without publishing them:
frequencies, songs, songFrequencies, lines, matches, aliases. JSON consumers
should use analyze_music directly for full multi-emotion evidence and ties.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import tokenize as python_tokenize
from typing import Any
import unicodedata
from urllib.parse import quote, urlsplit

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


SCHEMA_VERSION = 1
MATTR_WINDOW = 50
NEGATION_WINDOW = 3
_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "＇": "'"})
_TIMESTAMP = re.compile(
    r"(?<![\w:])(?:\[\s*|\(\s*)?\d{1,2}:[0-5]\d"
    r"(?::[0-5]\d)?(?:[.,]\d{1,3})?(?:\s*\]|\s*\))?(?![\w:])"
)
_SECTION = re.compile(
    r"(?:verse|chorus|pre[- ]?chorus|post[- ]?chorus|hook|bridge|intro|outro|"
    r"refrain|interlude)(?:\s+(?:\d+|[ivxlcdm]+))?"
    r"(?:\s*(?:x\d+|\(x\d+\)))?\s*:?", re.IGNORECASE,
)
_CLAUSE_BREAK = re.compile(r"[.!?;:,\n\r—]")
_CONTRAST = frozenset({"but", "however", "yet", "though", "although"})
_NEGATORS = frozenset({
    "no", "not", "never", "neither", "nor", "without", "hardly", "scarcely",
    "cannot", "ain't",
})
# A small explicit display/filter flag list, never removed from metrics/cues.
_STOPWORDS = frozenset("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can can't cannot could couldn't
did didn't do does doesn't doing don't down during each few for from further
had hadn't has hasn't have haven't having he he'd he'll he's her here here's
hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't
it it's its itself just me more most mustn't my myself no nor not of off on once
only or other ought our ours ourselves out over own same she she'd she'll she's
should shouldn't so some such than that that's the their theirs them themselves
then there there's these they they'd they'll they're they've this those through
to too under until up very was wasn't we we'd we'll we're we've were weren't
what what's when when's where where's which while who who's whom why why's will
with won't would wouldn't you you'd you'll you're you've your yours yourself
yourselves ain't never neither without hardly scarcely
""".split())
_MODULE_TOPICS = {
    "arrays_and_strings.py": (
        "Array and string practice, including consecutive-one scanning.",
        ["arrays", "strings", "linear scans"],
    ),
    "trees_and_tries.py": (
        "Binary-tree traversal and binary-search-tree practice; the filename also names tries.",
        ["binary trees", "binary search trees", "breadth-first search", "depth-first search"],
    ),
    "hash_tables.py": (
        "Hash-table implementations and dictionary/set-based algorithm practice.",
        ["hash tables", "dictionaries", "sets", "counting", "lookup"],
    ),
    "biggest_prime.py": (
        "Primality testing and number-theory practice.",
        ["primality", "number theory"],
    ),
}


@dataclass(frozen=True)
class _Word:
    word: str
    start: int
    end: int


def _words(text: str) -> list[_Word]:
    """Unicode letters/combining marks and internal apostrophes; no stemming.

    Digits, underscores, punctuation and hyphens delimit forms. Leading or
    trailing apostrophes are delimiters; internal contractions stay one form.
    Normalize each form (NFC then casefold), not the original display text.
    """
    text = text.translate(_APOSTROPHES)
    result = []
    position = 0
    while position < len(text):
        if not text[position].isalpha():
            position += 1
            continue
        start = position
        position += 1
        while position < len(text):
            char = text[position]
            if char.isalpha() or unicodedata.category(char).startswith("M"):
                position += 1
            elif char == "'" and position + 1 < len(text) and text[position + 1].isalpha():
                position += 1
            else:
                break
        result.append(_Word(unicodedata.normalize("NFC", text[start:position]).casefold(), start, position))
    return result


def _clean_line(text: str) -> str:
    # Spaces preserve original character offsets for cue evidence.
    return _TIMESTAMP.sub(lambda match: " " * len(match[0]), text)


def _is_header(text: str) -> bool:
    return bool(_SECTION.fullmatch(text.strip().strip("[](){} \t")))


def _physical_lines(text: str) -> tuple[list[tuple[int, str, str]], Counter[str]]:
    lines = []
    excluded: Counter[str] = Counter()
    for number, original in enumerate(text.splitlines(), 1):
        cleaned = _clean_line(original)
        if not original.strip():
            excluded["blankLines"] += 1
        elif not cleaned.strip():
            excluded["timestampOnlyLines"] += 1
        elif _is_header(cleaned):
            excluded["sectionHeaderLines"] += 1
        else:
            lines.append((number, original, cleaned))
    return lines, excluded


def _duplicate_key(lines: list[tuple[int, str, str]]) -> str:
    # Deliberately retain case, punctuation and lyric-line boundaries: do not
    # merge near-duplicates, reordered words, or paragraph/line reformatting.
    return "\n".join(
        " ".join(unicodedata.normalize("NFC", cleaned.translate(_APOSTROPHES)).split())
        for _, _, cleaned in lines
    )


def _mattr_parts(words: Sequence[str]) -> tuple[int, int]:
    if len(words) < MATTR_WINDOW:
        return 0, 0
    window = Counter(words[:MATTR_WINDOW])
    unique_sum = len(window)
    for index in range(MATTR_WINDOW, len(words)):
        outgoing = words[index - MATTR_WINDOW]
        window[outgoing] -= 1
        if not window[outgoing]:
            del window[outgoing]
        window[words[index]] += 1
        unique_sum += len(window)
    return unique_sum, len(words) - MATTR_WINDOW + 1


def _metrics(counts: Counter[str], mattr_parts: tuple[int, int]) -> dict[str, Any]:
    total = counts.total()
    unique_sum, window_count = mattr_parts
    return {
        "tokenCount": total, "vocabularySize": len(counts),
        "hapaxCount": sum(count == 1 for count in counts.values()),
        "ttr": len(counts) / total if total else None,
        "mattr": unique_sum / (MATTR_WINDOW * window_count) if window_count else None,
        "mattrWindowCount": window_count,
    }


def _frequencies(counts: Counter[str], songs: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"word": word, "count": count, "songCount": songs[word], "isStopword": word in _STOPWORDS}
        for word, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


def _read_lexicon() -> tuple[list[dict[str, Any]], dict[str, list[tuple[tuple[str, ...], str, str]]]]:
    data = json.loads(Path(__file__).with_name("emotions.json").read_text(encoding="utf-8"))
    emotions = []
    index: dict[str, list[tuple[tuple[str, ...], str, str]]] = {}
    for family in data["families"]:
        name = family["family"]
        branches = []
        for label, cues in family["branches"].items():
            branches.append({"label": label, "words": cues})
            for cue in cues:
                tokens = tuple(word.word for word in _words(cue))
                index.setdefault(tokens[0], []).append((tokens, name, label))
        emotions.append({"name": name, "color": family["color"], "branches": branches})
    return emotions, index


def _negators(words: list[_Word], start: int, text: str) -> list[dict[str, Any]]:
    found = []
    for index in range(start - 1, max(-1, start - NEGATION_WINDOW - 1), -1):
        word = words[index]
        if _CLAUSE_BREAK.search(text[word.end:words[index + 1].start]) or word.word in _CONTRAST:
            break
        if word.word in _NEGATORS or word.word.endswith("n't"):
            # "not only happy" is additive, not a denial of happy.
            if word.word == "not" and words[index + 1].word in {"only", "just"}:
                continue
            found.append({"word": word.word, "start": word.start, "end": word.end})
    return list(reversed(found))


def _feelings(
    words: list[_Word], text: str, cleaned: str, emotions: list[dict[str, Any]],
    index: dict[str, list[tuple[tuple[str, ...], str, str]]],
) -> dict[str, Any]:
    by_branch: dict[tuple[str, str], list[dict[str, Any]]] = {}
    evidence = []
    position = 0
    forms = [word.word for word in words]
    while position < len(words):
        candidates = [
            (cue, family, label) for cue, family, label in index.get(forms[position], [])
            if tuple(forms[position:position + len(cue)]) == cue
            and all(
                not _CLAUSE_BREAK.search(cleaned[words[i].end:words[i + 1].start])
                for i in range(position, position + len(cue) - 1)
            )
        ]
        if not candidates:
            position += 1
            continue
        longest = max(len(cue) for cue, _, _ in candidates)
        negators = _negators(words, position, cleaned)
        start, end = words[position].start, words[position + longest - 1].end
        for cue, family, label in candidates:
            if len(cue) != longest:
                continue
            item = {
                "family": family, "label": label, "cue": " ".join(cue),
                "text": text[start:end], "start": start, "end": end,
                "tokenStart": position, "tokenEnd": position + longest,
                "negated": bool(negators), "negators": negators,
                "weight": 0 if negators else 1,
            }
            by_branch.setdefault((family, label), []).append(item)
            evidence.append(item)
        position += longest

    order = {family["name"]: i for i, family in enumerate(emotions)}
    branch_order = {
        (family["name"], branch["label"]): i
        for family in emotions for i, branch in enumerate(family["branches"])
    }
    matches = [
        {"family": family, "label": label, "score": sum(e["weight"] for e in items), "evidence": items}
        for (family, label), items in by_branch.items()
    ]
    matches.sort(key=lambda m: (-m["score"], order[m["family"]], branch_order[(m["family"], m["label"])]))
    totals: Counter[str] = Counter()
    for match in matches:
        totals[match["family"]] += match["score"]
    scores = [
        {"family": family, "score": score}
        for family, score in sorted(totals.items(), key=lambda pair: (-pair[1], order[pair[0]]))
        if score > 0
    ]
    tied = [score["family"] for score in scores if score["score"] == scores[0]["score"]] if scores else []
    primary = scores[0]["family"] if scores else "Unclassified"
    primary_matches = [match for match in matches if match["family"] == primary and match["score"] > 0]
    label_tie = len(primary_matches) > 1 and primary_matches[0]["score"] == primary_matches[1]["score"]
    return {
        "emotion": primary,
        "subemotion": primary_matches[0]["label"] if primary_matches else None,
        "matches": matches, "evidence": evidence,
        "ambiguous": len(scores) > 1 or label_tie,
        "emotionScores": scores, "tiedEmotions": tied if len(tied) > 1 else [],
    }


def _require_repo(repo: Path) -> Path:
    repo = Path(repo)
    if not repo.is_dir():
        raise FileNotFoundError(f"Source repository directory is missing: {repo.name}")
    return repo


def _git(repo: Path, *arguments: str) -> str | None:
    # Do not inherit a parent's Git repo, user includes, or GIT_* overrides.
    if not (repo / ".git").exists():
        return None
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    try:
        process = subprocess.run(
            ["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", str(repo), *arguments],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return process.stdout.strip() or None if process.returncode == 0 else None


def _public_repo_url(remote: str | None) -> str | None:
    if not remote:
        return None
    if re.match(r"^[\w.-]+@[\w.-]+:", remote):
        remote = "ssh://" + remote.replace(":", "/", 1)
    parsed = urlsplit(remote)
    if parsed.scheme not in {"http", "https", "ssh"} or parsed.hostname not in {"github.com", "gitlab.com", "bitbucket.org"}:
        return None  # Never publish local paths, credentials or arbitrary URLs.
    path = parsed.path.strip("/").removesuffix(".git")
    if len(path.split("/")) < 2 or not all(re.fullmatch(r"[\w.-]+", part) and part not in {".", ".."} for part in path.split("/")):
        return None
    return f"https://{parsed.hostname}/{path}"


def _provenance(repo: Path) -> tuple[str | None, str | None]:
    remote = _git(repo, "config", "--local", "--no-includes", "--get", "remote.origin.url")
    commit = _git(repo, "rev-parse", "--verify", "HEAD")
    if commit and not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", commit):
        commit = None
    return _public_repo_url(remote), commit


def _source_url(repo_url: str | None, commit: str | None, path: str, line: int | None = None) -> str | None:
    if repo_url is None:
        return None
    host = urlsplit(repo_url).hostname
    action = "-/blob" if host == "gitlab.com" else "src" if host == "bitbucket.org" else "blob"
    suffix = f"#lines-{line}" if host == "bitbucket.org" else f"#L{line}"
    return f"{repo_url}/{action}/{commit or 'HEAD'}/{quote(path, safe='/')}" + (suffix if line else "")


def _files(repo: Path, suffix: str) -> tuple[list[Path], dict[str, list[str]]]:
    exclusions: dict[str, list[str]] = {"resourceMetadata": [], "symlinks": []}
    result = []

    def walk(directory: Path) -> Iterator[Path]:
        for path in sorted(directory.iterdir(), key=lambda p: (p.name.casefold(), p.name)):
            relative = path.relative_to(repo).as_posix()
            if path.name.startswith("._"):
                exclusions["resourceMetadata"].append(relative)
            elif path.is_symlink() or path.is_junction():
                exclusions["symlinks"].append(relative)
            elif path.name == ".git":
                continue
            elif path.is_dir():
                yield from walk(path)
            elif path.is_file() and path.suffix.casefold() == suffix:
                yield path

    result.extend(walk(repo))
    return result, exclusions


def _song_identity(relative: str, repo_url: str | None, commit: str | None) -> dict[str, Any]:
    path = Path(relative)
    return {
        "title": path.stem.replace("_", " "),
        "collection": path.parent.as_posix() if path.parent != Path(".") else "(root)",
        "path": relative, "sourceUrl": _source_url(repo_url, commit, relative),
    }


def analyze_music(repo: Path) -> dict[str, Any]:
    """Analyze UTF-8(-BOM) lyrics recursively, without writing or publishing.

    Distinct versions remain independent observations. Exact normalized copies
    have one deterministic, path-sorted representative; aliases are not counted
    as extra songs. Line numbers/text refer to that representative, not aliases.
    """
    repo = _require_repo(repo)
    repo_url, commit = _provenance(repo)
    files, exclusions = _files(repo, ".txt")
    emotions, lexicon = _read_lexicon()
    polarity = SentimentIntensityAnalyzer()
    songs: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    corpus: Counter[str] = Counter()
    song_counts: Counter[str] = Counter()
    line_exclusions: Counter[str] = Counter()
    unique_sum = window_count = 0
    for path in files:
        physical, skipped = _physical_lines(path.read_text(encoding="utf-8-sig"))
        line_exclusions.update(skipped)
        relative = path.relative_to(repo).as_posix()
        identity = _song_identity(relative, repo_url, commit)
        key = _duplicate_key(physical)
        if key in seen:
            seen[key]["aliases"].append(identity)
            continue
        lines = []
        tokens = []
        for number, text, cleaned in physical:
            spans = _words(cleaned)
            forms = [word.word for word in spans]
            tokens.extend(forms)
            lines.append({
                "number": number, "text": text, "tokens": forms,
                "polarity": polarity.polarity_scores(cleaned.translate(_APOSTROPHES)),
                **_feelings(spans, text, cleaned, emotions, lexicon),
            })
        counts = Counter(tokens)
        parts = _mattr_parts(tokens)
        unique_sum += parts[0]
        window_count += parts[1]
        slug = re.sub(r"[^a-z0-9]+", "-", identity["title"].casefold()).strip("-") or "song"
        # Full UTF-8 path hex is injective, unlike a truncated hash or slug.
        song = {
            "id": f"{slug}-{relative.encode('utf-8').hex()}", **identity, "aliases": [],
            **_metrics(counts, parts), "frequencies": _frequencies(counts, Counter(counts.keys())),
            "lines": lines,
        }
        songs.append(song)
        seen[key] = song
        corpus.update(counts)
        song_counts.update(counts.keys())

    counts = {
        "lyricFiles": len(files), "songs": len(songs),
        "duplicateFiles": len(files) - len(songs),
        "resourceMetadataExcluded": len(exclusions["resourceMetadata"]),
        "symlinksExcluded": len(exclusions["symlinks"]),
        "retainedLines": sum(len(song["lines"]) for song in songs),
        "excludedLinesBeforeDedup": {name: line_exclusions[name] for name in ("blankLines", "timestampOnlyLines", "sectionHeaderLines")},
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "source": {
            "repoUrl": repo_url, "commit": commit, "counts": counts, "exclusions": exclusions,
            "methodology": {
                "input": "Local UTF-8 text working tree; .git, ._ metadata, symlinks/junctions and non-.txt files excluded. No source is executed or modified.",
                "provenance": "Commit is HEAD when available, not proof of a clean working tree. Links use HEAD if no commit; unavailable/non-public origin yields null URLs. No snapshot fallback.",
                "tokenization": "NFC/casefold letter forms with internal normalized apostrophes; digits, punctuation, underscores and hyphens delimit. Timestamps and standalone section headers excluded. No stemming; stopwords flagged, never removed.",
                "lines": "One record per nonblank physical line except standalone headers/timestamps; original text and 1-based line number preserved. No sentence segmentation, even for long paragraphs.",
                "deduplication": "Exact equality after NFC/apostrophe normalization, timestamp/header/blank-line removal and per-line whitespace collapse. Case, punctuation and lyric-line boundaries retained. First sorted path is canonical; aliases excluded from all corpus metrics.",
                "versionBias": "Nonidentical versions, repeated verses and shared phrases remain, so revisions/repetition and collection sizes bias frequencies. Counts are not independent songs or representative language samples.",
                "vocabulary": "Observed casefold word forms only, not total personal vocabulary, intelligence/IQ or writing quality. TTR is distinct forms / tokens; hapaxCount counts forms appearing once. Empty TTR is null.",
                "mattrWindow": MATTR_WINDOW,
                "mattr": "Mean distinct-form fraction across every overlapping 50-token window, never resized. Null below 50 tokens. Corpus pools within-song windows weighted by window count, never crossing songs; null if no song has a window.",
                "emotion": "Custom English lexicon text categories, not diagnosis or an emotion model. Every longest nonoverlapping cue occurrence scores 1 per mapped branch; negated cues score 0 and stay in evidence. Scores are not probabilities; unclassified means no active cues, not neutral feelings.",
                "negationWindow": NEGATION_WINDOW,
                "negation": "Suppress on a negator in the preceding 3 tokens, stopping at . ! ? ; : , em dash or contrast words. Internal n't contractions included; 'not only/just' exempt. No inversion, double-negation logic or post-cue negation; multiword cues do not cross clause punctuation.",
                "ties": "Sum branch scores by family; choose largest family total then largest branch. Ties use checked-in family/branch order only. All matches and family scores retained; tiedEmotions lists top family ties. ambiguous means multiple active families or tied primary branches.",
                "uncertainty": "Exploratory heuristic, not calibrated confidence: no syntax, sarcasm, figurative/slang, speaker or quotation resolution. Family/branch names including Depressed describe text cues only; omissions and false matches are expected.",
                "polarity": "vaderSentiment on timestamp-cleaned original physical lines (case/punctuation retained); compound/neg/neu/pos are VADER polarity outputs only, not feelings-wheel classification.",
                "safety": "Plain unescaped display data. Publisher must escape HTML, embed JSON safely and handle spreadsheet formula injection in CSV; this module renders nothing.",
            },
        },
        "summary": _metrics(corpus, (unique_sum, window_count)),
        "frequencies": _frequencies(corpus, song_counts), "songs": songs, "emotions": emotions,
    }


def analyze_code(repo: Path) -> dict[str, Any]:
    """Index immediate module definitions/direct class methods using AST only.

    Include repeated definitions and async functions. Exclude lambdas, nested
    functions/classes and definitions inside control-flow blocks. routineCount
    counts these definition sites, including constructors: NOT problems solved.
    """
    repo = _require_repo(repo)
    repo_url, commit = _provenance(repo)
    files, exclusions = _files(repo, ".py")
    modules = []
    functions = methods = 0
    for path in files:
        relative = path.relative_to(repo).as_posix()
        with python_tokenize.open(path) as handle:
            tree = ast.parse(handle.read(), filename=relative)

        def routine(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
            return {"name": node.name, "line": node.lineno, "url": _source_url(repo_url, commit, relative, node.lineno)}

        top_functions = [routine(node) for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [
            {
                "name": node.name, "line": node.lineno,
                "url": _source_url(repo_url, commit, relative, node.lineno),
                "methods": [routine(method) for method in node.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))],
            }
            for node in tree.body if isinstance(node, ast.ClassDef)
        ]
        description, topics = _MODULE_TOPICS.get(path.name, (
            ast.get_docstring(tree) or "Python source indexed statically; no curated topic mapping.", [],
        ))
        modules.append({
            "name": path.stem, "path": relative, "url": _source_url(repo_url, commit, relative),
            "description": description, "topics": list(topics), "functions": top_functions, "classes": classes,
        })
        functions += len(top_functions)
        methods += sum(len(cls["methods"]) for cls in classes)
    return {
        "schemaVersion": SCHEMA_VERSION, "sourceUrl": repo_url, "commit": commit,
        "modules": modules, "moduleCount": len(modules),
        "routineCount": functions + methods, "functionCount": functions, "methodCount": methods,
        "classCount": sum(len(module["classes"]) for module in modules),
        "exclusions": exclusions,
        "methodology": "AST only: immediate top-level functions and direct methods of top-level classes, including async/repeated definitions and constructors. Excludes nested/control-flow definitions and lambdas; routineCount is definition sites, not unique problems solved. Curated filename topics are descriptive, not proof of implementations. Local working tree may differ from linked HEAD commit; no imports, execution or snapshot fallback.",
    }


def music_rows(analysis: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Flatten export tables; preserve raw strings for the publisher to escape."""
    rows: dict[str, list[dict[str, Any]]] = {
        "frequencies": [dict(row) for row in analysis["frequencies"]],
        "songs": [], "songFrequencies": [], "lines": [], "matches": [], "aliases": [],
    }
    for song in analysis["songs"]:
        identity = {"songId": song["id"], "path": song["path"]}
        rows["songs"].append({
            **identity, **{key: song[key] for key in (
                "title", "collection", "sourceUrl", "tokenCount", "vocabularySize", "hapaxCount", "ttr", "mattr", "mattrWindowCount",
            )}, "aliasCount": len(song["aliases"]),
        })
        rows["songFrequencies"].extend({**identity, **row} for row in song["frequencies"])
        rows["aliases"].extend({"songId": song["id"], **alias} for alias in song["aliases"])
        for line in song["lines"]:
            rows["lines"].append({
                **identity, "number": line["number"], "text": line["text"],
                "tokenCount": len(line["tokens"]), "emotion": line["emotion"],
                "subemotion": line["subemotion"], "ambiguous": line["ambiguous"],
                **line["polarity"],
            })
            for match in line["matches"]:
                for evidence in match["evidence"]:
                    rows["matches"].append({
                        **identity, "number": line["number"], "family": match["family"],
                        "label": match["label"], "score": match["score"],
                        **{key: evidence[key] for key in ("cue", "text", "start", "end", "tokenStart", "tokenEnd", "negated", "weight")},
                    })
    return rows