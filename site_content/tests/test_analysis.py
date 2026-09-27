"""Focused, synthetic fixtures only; never import or execute sibling code.

Run with unittest discovery restricted to test_analysis.py. All temporary
source fixtures and CSV buffers are local to tests; no site output is written.
"""

import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from site_content.analysis import (
    MATTR_WINDOW, _mattr_parts, _public_repo_url, _source_url,
    analyze_code, analyze_music, music_rows,
)


class AnalysisFixtures(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def music(self, text: str):
        self.write("song.txt", text)
        return analyze_music(self.root)

    def line(self, text: str):
        return self.music(text)["songs"][0]["lines"][0]

    def test_schema_and_json_serialization_without_local_paths(self):
        data = self.music("happy copper")
        self.assertEqual(set(data), {"schemaVersion", "source", "summary", "frequencies", "songs", "emotions"})
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(set(data["source"]), {"repoUrl", "commit", "counts", "exclusions", "methodology"})
        self.assertEqual(set(data["summary"]), {"tokenCount", "vocabularySize", "hapaxCount", "ttr", "mattr", "mattrWindowCount"})
        self.assertEqual(set(data["songs"][0]), {
            "id", "title", "collection", "path", "sourceUrl", "aliases", "tokenCount",
            "vocabularySize", "hapaxCount", "ttr", "mattr", "mattrWindowCount", "frequencies", "lines",
        })
        line = data["songs"][0]["lines"][0]
        self.assertEqual(set(line), {
            "number", "text", "tokens", "polarity", "emotion", "subemotion", "matches",
            "evidence", "ambiguous", "emotionScores", "tiedEmotions",
        })
        self.assertEqual(set(line["polarity"]), {"compound", "neg", "neu", "pos"})
        self.assertEqual(set(line["matches"][0]), {"family", "label", "score", "evidence"})
        self.assertEqual(set(data["frequencies"][0]), {"word", "count", "songCount", "isStopword"})
        self.assertIsNone(data["source"]["repoUrl"])
        self.assertIsNone(data["source"]["commit"])
        self.assertNotIn(self.root.name, json.dumps(data, allow_nan=False))

    def test_apostrophes_unicode_digits_timestamps_and_no_stemming(self):
        text = "[01:23:45.678] I’m CAN’T rock’n’roll café cafe\u0301 123 hello-world foo_bar cats cat"
        line = self.line(text)
        self.assertEqual(line["text"], text)
        self.assertEqual(line["tokens"], [
            "i'm", "can't", "rock'n'roll", "café", "café", "hello", "world", "foo", "bar", "cats", "cat",
        ])
        self.assertEqual(self.line("'hello' ‘world’ won't WON’T")['tokens'], ["hello", "world", "won't", "won't"])

    def test_headers_timestamp_only_and_blank_lines_preserve_physical_numbers(self):
        text = "\ufeffVerse 1\r\n[00:01] I am happy.\r\n(chorus)\r\n01:23\r\n\r\n[Verse 2:]\r\n(2:04) Grateful!\r\n"
        data = self.music(text)
        lines = data["songs"][0]["lines"]
        self.assertEqual([line["number"] for line in lines], [2, 7])
        self.assertEqual([line["tokens"] for line in lines], [["i", "am", "happy"], ["grateful"]])
        self.assertEqual(lines[0]["text"], "[00:01] I am happy.")
        self.assertEqual(data["source"]["counts"]["excludedLinesBeforeDedup"], {
            "blankLines": 1, "timestampOnlyLines": 1, "sectionHeaderLines": 3,
        })

    def test_header_word_in_lyrics_is_not_removed_and_paragraph_not_segmented(self):
        text = "Verse after verse I am happy. Then I am sad! Why?"
        data = self.music(text)
        self.assertEqual(len(data["songs"][0]["lines"]), 1)
        self.assertEqual(data["songs"][0]["lines"][0]["text"], text)
        self.assertEqual(data["frequencies"][0]["count"], 2)
        self.assertIn("verse", data["songs"][0]["lines"][0]["tokens"])

    def test_metadata_git_and_nontext_files_are_not_read(self):
        self.write("real.TXT", "happy")
        (self.root / "._real.txt").write_bytes(b"\xff\xfe")
        self.write("._folder/another.txt", "sad")
        self.write(".git/ignored.txt", "sad")
        (self.root / "track.mp3").write_bytes(b"\xff\xfe")
        data = analyze_music(self.root)
        self.assertEqual(data["source"]["counts"]["lyricFiles"], 1)
        self.assertEqual(data["source"]["counts"]["resourceMetadataExcluded"], 2)
        self.assertEqual(data["summary"]["tokenCount"], 1)
        self.assertEqual(set(data["source"]["exclusions"]["resourceMetadata"]), {"._folder", "._real.txt"})

    def test_symlink_is_excluded_without_following_it(self):
        self.write("real.txt", "happy")
        link = self.root / "linked.txt"
        try:
            link.symlink_to(self.root / "real.txt")
        except OSError:
            self.skipTest("Creating symlinks is not permitted on this system")
        data = analyze_music(self.root)
        self.assertEqual(data["source"]["exclusions"]["symlinks"], ["linked.txt"])
        self.assertEqual(data["source"]["counts"]["lyricFiles"], 1)

    def test_normalized_duplicates_collapse_with_aliases_and_versions_remain(self):
        self.write("Album/first.txt", "Verse 1\n[0:01] I’m happy.\n")
        self.write("Album_v2/copy.txt", "  I'm   happy.\r\n")
        self.write("Album_v3/revision.txt", "I'm happy.\nI am grateful.")
        data = analyze_music(self.root)
        self.assertEqual(data["source"]["counts"]["lyricFiles"], 3)
        self.assertEqual(data["source"]["counts"]["songs"], 2)
        self.assertEqual(data["source"]["counts"]["duplicateFiles"], 1)
        song = data["songs"][0]
        self.assertEqual(song["path"], "Album/first.txt")
        self.assertEqual(song["lines"][0]["number"], 2)
        self.assertEqual(song["aliases"], [{
            "title": "copy", "collection": "Album_v2", "path": "Album_v2/copy.txt", "sourceUrl": None,
        }])
        frequencies = {row["word"]: row for row in data["frequencies"]}
        self.assertEqual(frequencies["happy"]["count"], 2)
        self.assertEqual(frequencies["happy"]["songCount"], 2)
        self.assertEqual(data["summary"]["tokenCount"], 7)
        self.assertIn("versions", data["source"]["methodology"]["versionBias"])

    def test_dedup_is_conservative_about_case_punctuation_and_line_boundaries(self):
        for index, text in enumerate(["happy sad", "Happy sad", "happy, sad", "happy\nsad", "sad happy"]):
            self.write(f"v{index}.txt", text)
        data = analyze_music(self.root)
        self.assertEqual(len(data["songs"]), 5)
        self.assertEqual(data["source"]["counts"]["duplicateFiles"], 0)

    def test_ids_are_injective_for_slug_collisions_and_stable_across_content_edits(self):
        self.write("A/a-b.txt", "happy")
        other = self.write("A/a_b.txt", "sad")
        self.write("B/a-b.txt", "grateful")
        first = analyze_music(self.root)
        self.assertEqual(first, analyze_music(self.root))
        ids = {song["path"]: song["id"] for song in first["songs"]}
        self.assertEqual(len(set(ids.values())), 3)
        for path, identifier in ids.items():
            self.assertRegex(identifier, r"^[a-z0-9-]+$")
            self.assertEqual(bytes.fromhex(identifier.rsplit("-", 1)[1]).decode("utf-8"), path)
        other.write_text("sad angry", encoding="utf-8")
        self.assertEqual(ids, {song["path"]: song["id"] for song in analyze_music(self.root)["songs"]})

    def test_sorted_frequencies_breadth_hapax_and_stopwords(self):
        self.write("a.txt", "The cat cat dog")
        self.write("b.txt", "the dog bird")
        data = analyze_music(self.root)
        self.assertEqual(data["frequencies"], [
            {"word": "cat", "count": 2, "songCount": 1, "isStopword": False},
            {"word": "dog", "count": 2, "songCount": 2, "isStopword": False},
            {"word": "the", "count": 2, "songCount": 2, "isStopword": True},
            {"word": "bird", "count": 1, "songCount": 1, "isStopword": False},
        ])
        self.assertEqual(data["summary"]["tokenCount"], 7)
        self.assertEqual(data["summary"]["vocabularySize"], 4)
        self.assertEqual(data["summary"]["hapaxCount"], 1)
        self.assertAlmostEqual(data["summary"]["ttr"], 4 / 7)
        self.assertTrue(all(row["songCount"] == 1 for song in data["songs"] for row in song["frequencies"]))

    def test_empty_repo_and_empty_lyrics_have_null_ratios(self):
        empty = analyze_music(self.root)
        self.assertEqual(empty["songs"], [])
        self.assertEqual(empty["summary"]["tokenCount"], 0)
        self.assertIsNone(empty["summary"]["ttr"])
        self.assertIsNone(empty["summary"]["mattr"])
        data = self.music("Verse 1\n[00:10]\n\n")
        self.assertEqual(len(data["songs"]), 1)
        self.assertEqual(data["songs"][0]["lines"], [])
        self.assertIsNone(data["songs"][0]["ttr"])

    def test_mattr_short_exact_window_and_sliding_window(self):
        self.assertEqual(MATTR_WINDOW, 50)
        for length in (0, 1, 49):
            with self.subTest(length=length):
                data = self.music(" ".join(["copper"] * length))
                self.assertIsNone(data["summary"]["mattr"])
                self.assertEqual(data["summary"]["mattrWindowCount"], 0)
        exact = self.music(" ".join(["copper"] * 50))
        self.assertAlmostEqual(exact["summary"]["mattr"], 1 / 50)
        sliding = self.music(" ".join(["copper"] * 50 + ["lattice"]))
        self.assertAlmostEqual(sliding["summary"]["mattr"], 0.03)
        self.assertEqual(sliding["summary"]["mattrWindowCount"], 2)

    def test_mattr_matches_brute_force_and_fixed_bounds(self):
        for words in (["a"] * 101, list("abcdefghijklmnopqrstuvwxyz") * 5, [str(i) for i in range(150)]):
            total, count = _mattr_parts(words)
            expected = sum(len(set(words[i:i + 50])) for i in range(len(words) - 49))
            self.assertEqual(total, expected)
            self.assertEqual(count, len(words) - 49)
            self.assertGreaterEqual(total / (50 * count), 1 / 50)
            self.assertLessEqual(total / (50 * count), 1)

    def test_corpus_mattr_never_crosses_song_boundaries(self):
        self.write("a.txt", " ".join(["copper"] * 30))
        self.write("b.txt", " ".join(["lattice"] * 30))
        data = analyze_music(self.root)
        self.assertEqual(data["summary"]["tokenCount"], 60)
        self.assertIsNone(data["summary"]["mattr"])

    def test_corpus_mattr_weights_by_window_count_not_song_count(self):
        unique = ["w" + chr(97 + i // 26) + chr(97 + i % 26) for i in range(50)]
        self.write("a.txt", " ".join(unique))
        self.write("b.txt", " ".join(["copper"] * 51))
        data = analyze_music(self.root)
        self.assertEqual(data["summary"]["mattrWindowCount"], 3)
        self.assertAlmostEqual(data["summary"]["mattr"], 52 / 150)

    def test_all_twelve_families_have_varied_branches_and_traceable_cues(self):
        data = self.music("copper")
        expected = ["Proud", "Joyful", "Intrigued", "Trusting", "Loving", "Grateful", "Disgusted", "Sad", "Depressed", "Surprised", "Afraid", "Angry"]
        self.assertEqual([family["name"] for family in data["emotions"]], expected)
        for family in data["emotions"]:
            self.assertRegex(family["color"], r"^#[0-9A-Fa-f]{6}$")
            self.assertGreaterEqual(len(family["branches"]), 4)
            for branch in family["branches"]:
                self.assertGreaterEqual(len(branch["words"]), 6)
                self.assertEqual(len(branch["words"]), len(set(branch["words"])))
                line = self.line(branch["words"][0])
                self.assertTrue(any(m["family"] == family["name"] and m["label"] == branch["label"] for m in line["matches"]))

    def test_no_cues_is_explicitly_unclassified_not_neutral_emotion(self):
        line = self.line("copper lattice matrix")
        self.assertEqual(line["emotion"], "Unclassified")
        self.assertIsNone(line["subemotion"])
        self.assertEqual(line["matches"], [])
        self.assertEqual(line["evidence"], [])
        self.assertEqual(line["emotionScores"], [])
        self.assertEqual(line["tiedEmotions"], [])
        self.assertFalse(line["ambiguous"])

    def test_vader_is_polarity_only_not_emotion_classifier(self):
        line = self.line("excellent")
        self.assertGreater(line["polarity"]["compound"], 0)
        self.assertEqual(line["emotion"], "Unclassified")

    def test_multiple_categories_ties_and_family_sum(self):
        line = self.line("happy grateful")
        self.assertEqual(line["emotion"], "Joyful")
        self.assertEqual(line["subemotion"], "Happy")
        self.assertEqual(line["tiedEmotions"], ["Joyful", "Grateful"])
        self.assertTrue(line["ambiguous"])
        self.assertEqual(line["emotionScores"], [{"family": "Joyful", "score": 1}, {"family": "Grateful", "score": 1}])
        line = self.line("happy excited sad")
        self.assertEqual(line["emotionScores"][0], {"family": "Joyful", "score": 2})
        self.assertEqual(line["tiedEmotions"], [])
        self.assertEqual(len(line["matches"]), 3)
        self.assertTrue(self.line("happy excited")["ambiguous"])

    def test_shared_cue_exposes_multiple_families(self):
        line = self.line("betrayed")
        self.assertEqual(line["tiedEmotions"], ["Sad", "Angry"])
        self.assertEqual(len(line["evidence"]), 2)

    def test_repeated_cues_score_occurrences_not_probability(self):
        line = self.line("happy happy happy")
        self.assertEqual(line["matches"][0]["score"], 3)
        self.assertEqual(len(line["evidence"]), 3)
        self.assertEqual(line["emotionScores"], [{"family": "Joyful", "score": 3}])

    def test_negation_keeps_zero_score_evidence_and_does_not_invert_emotion(self):
        for text in ("not happy", "never happy", "without joy", "I don't feel happy", "I can’t feel happy", "not ever really happy"):
            with self.subTest(text=text):
                line = self.line(text)
                self.assertEqual(line["emotion"], "Unclassified")
                self.assertEqual(line["matches"][0]["score"], 0)
                self.assertTrue(line["evidence"][0]["negated"])
                self.assertEqual(line["evidence"][0]["weight"], 0)
                self.assertTrue(line["evidence"][0]["negators"])
        self.assertEqual(self.line("not sad")["emotion"], "Unclassified")

    def test_negation_window_clause_boundaries_contrast_and_additive_not(self):
        for text in ("not ever really truly happy", "not here. happy", "not sad, happy", "not sad but happy", "not only happy", "not just happy"):
            with self.subTest(text=text):
                self.assertEqual(self.line(text)["emotion"], "Joyful")

    def test_multiword_longest_match_and_negation(self):
        line = self.line("running on empty")
        self.assertEqual(line["emotion"], "Depressed")
        self.assertEqual(line["subemotion"], "Exhausted")
        self.assertEqual(len(line["matches"]), 1)
        self.assertEqual(line["evidence"][0]["cue"], "running on empty")
        self.assertEqual(self.line("not on cloud nine")["emotion"], "Unclassified")
        self.assertEqual(self.line("on cloud nine")["emotion"], "Joyful")
        self.assertEqual(self.line("on cloud. nine")["emotion"], "Unclassified")

    def test_cues_are_forms_not_substrings_or_stems(self):
        self.assertEqual(self.line("unhappy sadly lovingkindness")["emotion"], "Unclassified")

    def test_evidence_character_and_token_spans_refer_to_original_unicode_text(self):
        text = "[01:02] cafe\u0301 I’m not happy, GRATEFUL"
        line = self.line(text)
        for evidence in line["evidence"]:
            self.assertEqual(text[evidence["start"]:evidence["end"]], evidence["text"])
            self.assertEqual(" ".join(line["tokens"][evidence["tokenStart"]:evidence["tokenEnd"]]), evidence["cue"])
            for negator in evidence["negators"]:
                self.assertEqual(text[negator["start"]:negator["end"]], negator["word"])
        self.assertEqual(line["emotion"], "Grateful")

    def test_xss_and_csv_formula_strings_remain_plain_data(self):
        text = '<script>alert("happy")</script>\n=HYPERLINK("https://example.test", "grateful")'
        data = self.music(text)
        self.assertEqual(data["songs"][0]["lines"][0]["text"], text.splitlines()[0])
        rows = music_rows(data)
        self.assertEqual(rows["lines"][1]["text"], text.splitlines()[1])
        self.assertIn("escape HTML", data["source"]["methodology"]["safety"])
        for table in rows.values():
            if table:
                self.assertTrue(all(not isinstance(value, (list, dict)) for row in table for value in row.values()))
                buffer = io.StringIO()
                writer = csv.DictWriter(buffer, fieldnames=list(table[0]))
                writer.writeheader()
                writer.writerows(table)
        self.assertEqual(set(rows), {"frequencies", "songs", "songFrequencies", "lines", "matches", "aliases"})
        self.assertEqual(json.loads(json.dumps(data)), data)

    def test_export_alias_and_negated_match_rows(self):
        self.write("a.txt", "not happy")
        self.write("b.txt", "not happy")
        rows = music_rows(analyze_music(self.root))
        self.assertEqual(len(rows["songs"]), 1)
        self.assertEqual(rows["songs"][0]["aliasCount"], 1)
        self.assertEqual(rows["aliases"][0]["path"], "b.txt")
        self.assertEqual(rows["matches"][0]["score"], 0)
        self.assertTrue(rows["matches"][0]["negated"])

    def test_missing_sources_raise_without_fallback(self):
        for analyzer in (analyze_music, analyze_code):
            with self.assertRaises(FileNotFoundError):
                analyzer(self.root / "missing")

    def test_invalid_text_encoding_fails_explicitly(self):
        (self.root / "bad.txt").write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            analyze_music(self.root)

    def test_ast_inspection_never_executes_source_and_only_counts_direct_definitions(self):
        self.write("safe.py", '''"""Example module."""
import nonexistent_package_do_not_import
raise RuntimeError("MUST NEVER RUN")
def outer():
    def nested():
        pass
    class Hidden:
        def hidden_method(self):
            pass
    return nested
async def async_top():
    pass
class Visible:
    raise RuntimeError("CLASS BODY MUST NEVER RUN")
    def __init__(self):
        pass
    @decorator_that_must_not_run()
    async def method(self):
        def nested_method():
            pass
    class NestedClass:
        def excluded(self):
            pass
if True:
    def conditional():
        pass
anonymous = lambda: 1
def outer():
    pass
''')
        self.write("._bad.py", "THIS IS NOT PYTHON!")
        data = analyze_code(self.root)
        self.assertEqual(data["moduleCount"], 1)
        self.assertEqual(data["functionCount"], 3)
        self.assertEqual(data["methodCount"], 2)
        self.assertEqual(data["routineCount"], 5)
        self.assertEqual(data["classCount"], 1)
        module = data["modules"][0]
        self.assertEqual([f["name"] for f in module["functions"]], ["outer", "async_top", "outer"])
        self.assertEqual([f["line"] for f in module["functions"]], [4, 11, 28])
        self.assertEqual([m["name"] for m in module["classes"][0]["methods"]], ["__init__", "method"])
        self.assertEqual(module["description"], "Example module.")
        self.assertIn("not unique problems solved", data["methodology"])
        self.assertEqual(set(module), {"name", "path", "url", "description", "topics", "functions", "classes"})
        self.assertEqual(set(module["functions"][0]), {"name", "line", "url"})
        self.assertEqual(set(module["classes"][0]), {"name", "line", "url", "methods"})

    def test_known_module_descriptions_and_topics_and_python_encoding_cookie(self):
        names = ["arrays_and_strings.py", "trees_and_tries.py", "hash_tables.py", "biggest_prime.py"]
        for name in names:
            self.write(name, "def example():\n    pass\n")
        (self.root / "encoded.py").write_bytes(b'# coding: latin-1\n"""caf\xe9"""\n')
        data = analyze_code(self.root)
        self.assertEqual(data["moduleCount"], 5)
        self.assertEqual(data["routineCount"], 4)
        for module in data["modules"]:
            if module["path"] in names:
                self.assertTrue(module["topics"])
                self.assertIn("practice", module["description"])
            else:
                self.assertEqual(module["description"], "café")
                self.assertEqual(module["topics"], [])

    def test_ast_parse_errors_are_not_silently_skipped(self):
        self.write("broken.py", "def broken(:\n")
        with self.assertRaises(SyntaxError):
            analyze_code(self.root)

    def test_git_provenance_urls_are_pinned_encoded_and_no_absolute_paths(self):
        commit = "a" * 40
        with patch("site_content.analysis._git", side_effect=["git@github.com:owner/repo.git", commit]) as git:
            self.write("Album name/a #%.txt", "happy")
            data = analyze_music(self.root)
        self.assertEqual(git.call_count, 2)
        self.assertEqual(git.call_args_list[0].args[1:], ("config", "--local", "--no-includes", "--get", "remote.origin.url"))
        self.assertEqual(git.call_args_list[1].args[1:], ("rev-parse", "--verify", "HEAD"))
        self.assertEqual(data["source"]["repoUrl"], "https://github.com/owner/repo")
        self.assertEqual(data["source"]["commit"], commit)
        self.assertEqual(data["songs"][0]["sourceUrl"], f"https://github.com/owner/repo/blob/{commit}/Album%20name/a%20%23%25.txt")
        self.write("module.py", "\nasync def routine():\n    pass\n")
        with patch("site_content.analysis._git", side_effect=["https://github.com/owner/repo.git", commit]):
            code = analyze_code(self.root)
        self.assertEqual(code["modules"][0]["functions"][0]["url"], f"https://github.com/owner/repo/blob/{commit}/module.py#L2")

    def test_remote_url_sanitization_and_missing_git(self):
        self.assertEqual(_public_repo_url("https://user:secret@github.com/owner/repo.git?token=secret"), "https://github.com/owner/repo")
        self.assertEqual(_public_repo_url("ssh://git@gitlab.com/group/repo.git"), "https://gitlab.com/group/repo")
        for value in (None, "C:/private/source", "file:///private/source", "javascript:alert(1)", "https://localhost/owner/repo", "https://github.com/../repo"):
            self.assertIsNone(_public_repo_url(value))
        self.assertIsNone(_source_url(None, None, "module.py"))
        self.assertEqual(_source_url("https://gitlab.com/group/repo", None, "module.py", 2), "https://gitlab.com/group/repo/-/blob/HEAD/module.py#L2")
        self.assertEqual(_source_url("https://bitbucket.org/group/repo", None, "module.py", 2), "https://bitbucket.org/group/repo/src/HEAD/module.py#lines-2")
        with patch("site_content.analysis.subprocess.run", side_effect=AssertionError("not a Git repo")):
            self.assertIsNone(analyze_music(self.root)["source"]["commit"])


if __name__ == "__main__":
    unittest.main()