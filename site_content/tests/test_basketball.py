"""Basketball source contracts and independent first-to-four accounting.

These tests never publish or rewrite the owner-supplied log. Temporary files
exercise the loader only; synthetic games are not observations in the dataset.
"""

from collections import Counter
from copy import deepcopy
from datetime import date
from hashlib import sha256
from itertools import product
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from site_content.basketball import (
    BasketballValidationError,
    analyze_series,
    export_rows,
    load_basketball,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "records" / "basketball" / "series.json"
CHALLENGES = ("shooting", "bump", "horse", "backboard", "three-point", "rim", "one-on-one")
ORDERS = ("LOLLOL", "OOLLOO", "LLLL", "OLLLL", "OLLOLOL", "LLOOLL", "LOOLLL",
          "LLLL", "OOLLLL", "LLOOLL", "OLLOLL", "LLLOOL", "OLLLL")


def example(order="LLLL"):
    """A synthetic complete log, with no inferred times/scores or new rules."""
    return {
        "schemaVersion": 1, "title": "Synthetic validation fixture",
        "sourceTitle": "Liam McGrath-Dent",
        "players": [{"id": "L", "name": "Liam"}, {"id": "O", "name": "Owen"}],
        "provenance": {"source": "Test-only, not a played series"},
        "series": [{"id": "2026-09-27-1", "date": "2026-09-27", "sourceDate": "9/27/2026",
                    "session": 1, "order": order,
                    "games": [{"challenge": CHALLENGES[index % 7], "winner": player}
                              for index, player in enumerate(order)]}],
    }


class BasketballGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.result = analyze_series(cls.raw)

    def test_transcribed_orders_and_independent_golden_counts(self):
        self.assertEqual(tuple(series["order"] for series in self.raw["series"]), ORDERS)
        for series in self.raw["series"]:
            self.assertEqual(series["order"], "".join(game["winner"] for game in series["games"]))
        raw_wins = Counter(game["winner"] for series in self.raw["series"] for game in series["games"])
        # Compute the series winner independently by counting raw round wins.
        raw_series_wins = Counter(
            Counter(game["winner"] for game in series["games"]).most_common(1)[0][0]
            for series in self.raw["series"]
        )
        self.assertEqual(raw_wins, {"L": 50, "O": 23})
        self.assertEqual(raw_series_wins, {"L": 12, "O": 1})
        summary = self.result["summary"]
        self.assertEqual(summary["challengeCount"], 73)
        self.assertEqual(summary["seriesCount"], 13)
        self.assertEqual(summary["challengeWins"], dict(raw_wins))
        self.assertEqual(summary["seriesWins"], dict(raw_series_wins))
        self.assertEqual(summary["currStreak"], {"player": "L", "length": 11})
        self.assertAlmostEqual(summary["seriesWinRates"]["L"], 12 / 13)
        self.assertAlmostEqual(summary["challengeWinRates"]["O"], 23 / 73)

    def test_dates_sessions_and_source_order_are_not_clock_times(self):
        series = self.result["series"]
        self.assertEqual([item["date"] for item in series], [
            "2026-08-07", "2026-08-08", "2026-09-07", "2026-09-07", "2026-09-10",
            "2026-09-10", "2026-09-11", "2026-09-11", "2026-09-11", "2026-09-13",
            "2026-09-13", "2026-09-16", "2026-09-16",
        ])
        self.assertEqual([item["session"] for item in series], [1, 1, 1, 2, 1, 2, 1, 2, 3, 1, 2, 1, 2])
        self.assertEqual([item["sourceIndex"] for item in series], list(range(1, 14)))
        self.assertEqual([item["sequenceIndex"] for item in series], list(range(1, 14)))
        self.assertEqual(self.result["summary"]["distinctDateCount"], 7)
        for item in series:
            self.assertEqual(item["id"], f"{item['date']}-{item['session']}")
            self.assertNotIn("startTime", item)
            self.assertNotIn("timestamp", item)

    def test_sports_names_and_provenance_preserved(self):
        self.assertEqual(self.result["players"], [{"id": "L", "name": "Liam"}, {"id": "O", "name": "Owen"}])
        self.assertEqual(self.result["source"]["sourceTitle"], "Liam McGrath-Dent")
        self.assertEqual(self.result["source"]["path"], "records/basketball/series.json")
        self.assertEqual(self.result["provenance"], self.raw["provenance"])
        self.assertEqual([row["id"] for row in self.result["challengeDefinitions"]], list(CHALLENGES))

    def test_challenge_rows_have_explicit_played_denominators(self):
        expected = {
            "shooting": (7, 6), "bump": (10, 1), "horse": (3, 6), "backboard": (10, 2),
            "three-point": (9, 3), "rim": (7, 3), "one-on-one": (4, 2),
        }
        for row in self.result["challenges"]:
            liam, owen = expected[row["id"]]
            self.assertEqual(row["wins"], {"L": liam, "O": owen})
            self.assertEqual(row["played"], liam + owen)
            self.assertEqual(row["winRateDenominator"], row["played"])
            self.assertEqual(row["seriesWithChallenge"], row["played"])
            self.assertEqual(row["notPlayed"], 13 - row["played"])
            self.assertAlmostEqual(row["winRates"]["L"], liam / row["played"])
            self.assertAlmostEqual(sum(row["winRates"].values()), 1)
            self.assertEqual(row["duplicateSeriesCount"], 0)

    def test_every_raw_game_note_and_unknown_court_is_preserved(self):
        for original, enriched in zip(self.raw["series"], self.result["series"]):
            self.assertEqual(enriched["games"], original["games"])
            for raw, row in zip(original["games"], enriched["rounds"]):
                self.assertEqual({key: row[key] for key in raw}, raw)
            if original["date"] in ("2026-08-07", "2026-08-08"):
                self.assertEqual(enriched["court"], "Left Court")
                self.assertEqual(enriched["rimHeightInches"], 114)
            else:
                self.assertIsNone(enriched["court"])
                self.assertIsNone(enriched["rimHeightInches"])
        notes = [row["note"] for item in self.result["series"] for row in item["rounds"] if "note" in row]
        self.assertIn("got to half court", notes)
        self.assertIn("barely", notes)

    def test_horse_bump_raw_scores_do_not_become_points_or_letters(self):
        for item in self.result["series"]:
            for row in item["rounds"]:
                if row["challenge"] in ("horse", "bump"):
                    score = row["score"]
                    self.assertEqual(score["raw"], row.get("scoreRaw"))
                    self.assertIsNone(score["winnerPoints"])
                    self.assertIsNone(score["loserPoints"])
                    self.assertIsNone(score["normalized"])
                    self.assertEqual(score["status"], "recorded-uninterpreted" if "scoreRaw" in row else "not-recorded")

    def test_1v1_colon_score_normalizes_without_touching_raw(self):
        row = self.result["series"][4]["rounds"][2]
        self.assertEqual(row["scoreRaw"], "7:3")
        self.assertEqual(row["score"], {"raw": "7:3", "normalized": "7-3", "winnerPoints": 7,
                                        "loserPoints": 3, "status": "winner-loser-points"})
        self.assertEqual(self.result["series"][4]["games"][2]["scoreRaw"], "7:3")

    def test_timing_golden_counts_and_best_entries(self):
        timing = self.result["timing"]
        self.assertEqual(timing["played"], 12)
        self.assertEqual(timing["validCount"], 10)
        self.assertEqual(timing["missingCount"], 2)
        self.assertEqual(timing["notPlayedCount"], 1)
        self.assertEqual([row["seconds"] for row in timing["validEntries"]],
                         [215, 193, 296, 82, 182, 125, 225, 163, 294, 300])
        raw_times = [game["timeRaw"] for series in self.raw["series"] for game in series["games"]
                     if game.get("timeRaw") not in (None, "TBD", "N/A")]
        seconds = [int(value.split(":")[0]) * 60 + int(value.split(":")[1]) for value in raw_times]
        self.assertEqual(min(seconds), 82)
        self.assertEqual(timing["bestOverall"]["seconds"], 82)
        self.assertEqual(timing["bestOverall"]["raw"], "1:22")
        self.assertEqual(timing["bestOverall"]["seriesId"], "2026-09-07-2")
        self.assertEqual(timing["bestByPlayer"]["L"]["seconds"], 82)
        self.assertEqual(timing["bestByPlayer"]["O"]["seconds"], 193)
        self.assertEqual(timing["byPlayer"], [{"player": "L", "played": 9, "validCount": 7, "missingCount": 2},
                                             {"player": "O", "played": 3, "validCount": 3, "missingCount": 0}])

    def test_pending_not_recorded_not_played_are_separate_states(self):
        timing = self.result["timing"]
        self.assertEqual(timing["statusCounts"], {"valid": 10, "pending": 1, "not-recorded": 1,
                                                  "missing": 0, "not-played": 1})
        self.assertEqual([(row["seriesId"], row["raw"], row["status"]) for row in timing["missingEntries"]],
                         [("2026-09-10-1", "TBD", "pending"), ("2026-09-16-2", "N/A", "not-recorded")])
        for row in timing["missingEntries"]:
            self.assertTrue(row["played"])
            self.assertEqual(row["winner"], "L")
            self.assertIsNone(row["seconds"])
        row = timing["notPlayedEntries"][0]
        self.assertEqual(row["seriesId"], "2026-09-10-2")
        self.assertFalse(row["played"])
        for key in ("round", "winner", "raw", "seconds"):
            self.assertIsNone(row[key])

    def test_transition_accounting_is_within_series_only(self):
        result = self.result
        raw_pairs = [(series, index, series["games"][index - 1], game)
                     for series in self.raw["series"] for index, game in enumerate(series["games"]) if index]
        self.assertEqual(len(raw_pairs), 60)
        self.assertEqual(len(result["transitions"]), 73 - 13)
        for row, (series, index, previous, following) in zip(result["transitions"], raw_pairs):
            self.assertEqual(row["seriesId"], series["id"])
            self.assertEqual(row["previousRound"], index)
            self.assertEqual(row["nextRound"], index + 1)
            self.assertEqual(row["prevWinner"], previous["winner"])
            self.assertEqual(row["inferredPicker"], previous["winner"])
            self.assertEqual(row["previousChallenge"], previous["challenge"])
            self.assertEqual(row["nextChallenge"], following["challenge"])
            self.assertEqual(row["nextWinner"], following["winner"])
            self.assertIs(row["retained"], previous["winner"] == following["winner"])
        for series in result["series"]:
            first = series["rounds"][0]
            self.assertIsNone(first["inferredPicker"])
            self.assertIsNone(first["retained"])
        totals = result["summary"]["transitions"]
        self.assertEqual((totals["total"], totals["retentions"], totals["switches"]), (60, 35, 25))
        self.assertAlmostEqual(totals["retentionRate"], 35 / 60)
        self.assertAlmostEqual(totals["switchRate"], 25 / 60)

    def test_picker_denominators_exclude_clinching_wins(self):
        rows = {row["player"]: row for row in self.result["byPicker"]}
        for player, picks, holds, losses in (("L", 38, 28, 10), ("O", 22, 7, 15)):
            self.assertEqual(rows[player]["countPicks"], picks)
            self.assertEqual(rows[player]["denominator"], picks)
            self.assertEqual(rows[player]["holds"], holds)
            self.assertEqual(rows[player]["losses"], losses)
            self.assertAlmostEqual(rows[player]["holdRate"], holds / picks)
            self.assertAlmostEqual(rows[player]["lossRate"], losses / picks)
            self.assertEqual(picks, self.result["summary"]["challengeWins"][player]
                             - self.result["summary"]["seriesWins"][player])

    def test_conditional_next_challenges_distinguish_picks_from_wins(self):
        rows = self.result["conditionalNextChallenge"]
        self.assertEqual(len(rows), 14)
        for row in rows:
            pairs = [(a, b) for series in self.raw["series"] for a, b in zip(series["games"], series["games"][1:])
                     if a["winner"] == row["player"] and b["challenge"] == row["nextChallenge"]]
            count_wins = sum(b["winner"] == row["player"] for _, b in pairs)
            self.assertEqual(row["countPicks"], len(pairs))
            self.assertEqual(row["countWins"], count_wins)
            self.assertEqual(row["countLosses"], len(pairs) - count_wins)
            self.assertAlmostEqual(row["choiceShare"], len(pairs) / row["pickerTotal"])
            if pairs:
                self.assertAlmostEqual(row["winRate"], count_wins / len(pairs))
            else:
                self.assertIsNone(row["winRate"])
            if row["nextChallenge"] == "shooting":
                self.assertEqual(row["countPicks"], 0)
        for player, expected in (("L", 38), ("O", 22)):
            self.assertEqual(sum(row["countPicks"] for row in rows if row["player"] == player), expected)

    def test_matrix_has_all_49_cells_and_matches_independent_raw_pairs(self):
        matrix = self.result["transitionMatrix"]
        self.assertEqual(matrix["challengeOrder"], list(CHALLENGES))
        counts = Counter((a["challenge"], b["challenge"]) for series in self.raw["series"]
                         for a, b in zip(series["games"], series["games"][1:]))
        self.assertEqual(len(matrix["counts"]), 7)
        for i, previous in enumerate(CHALLENGES):
            self.assertEqual(len(matrix["counts"][i]), 7)
            for j, following in enumerate(CHALLENGES):
                self.assertEqual(matrix["counts"][i][j], counts[previous, following])
        self.assertEqual(sum(map(sum, matrix["counts"])), 60)

    def test_lengths_sweeps_deciders_and_comebacks_are_distinct(self):
        summary = self.result["summary"]
        self.assertEqual(summary["sweeps"], 2)
        self.assertEqual(summary["deciders"], 1)
        self.assertEqual(summary["sweepWins"], {"L": 2, "O": 0})
        self.assertEqual(summary["deciderWins"], {"L": 1, "O": 0})
        self.assertEqual(summary["comebacks"], 6)
        self.assertEqual(summary["openingWinnerWonSeries"], 8)
        self.assertAlmostEqual(summary["openingWinnerWinRate"], 8 / 13)
        self.assertEqual({row["roundCount"]: row["seriesCount"] for row in self.result["seriesLengths"]},
                         {4: 2, 5: 2, 6: 8, 7: 1})
        self.assertEqual({row["winnerMaxDeficit"]: row["seriesCount"] for row in self.result["comebacks"]},
                         {0: 7, 1: 5, 2: 1, 3: 0})

    def test_trajectories_include_the_zero_origin_and_every_round(self):
        self.assertEqual(len(self.result["trajectories"]), 73 + 13)
        for item in self.result["series"]:
            trajectory = item["trajectory"]
            self.assertEqual(trajectory[0], {"round": 0, "L": 0, "O": 0, "margin": 0})
            self.assertEqual(len(trajectory), item["roundCount"] + 1)
            for index, point in enumerate(trajectory):
                self.assertEqual(point["round"], index)
                self.assertEqual(point["L"], item["order"][:index].count("L"))
                self.assertEqual(point["O"], item["order"][:index].count("O"))
                self.assertEqual(point["margin"], point["L"] - point["O"])
            self.assertEqual(trajectory[-1][item["winner"]], 4)
        comeback = self.result["series"][8]
        self.assertEqual(comeback["winnerMaxDeficit"], 2)
        self.assertTrue(comeback["comeback"])


class BasketballValidationTests(unittest.TestCase):
    def assert_invalid(self, data, location=None):
        before = deepcopy(data)
        with self.assertRaises(BasketballValidationError) as error:
            analyze_series(data)
        self.assertTrue(str(error.exception).startswith("$"))
        if location:
            self.assertIn(location, str(error.exception))
        self.assertEqual(data, before, "failed validation must not mutate the input")

    def test_invalid_top_level_containers_and_schema_versions(self):
        for value in (None, True, [], "log", 1):
            with self.subTest(value=value):
                self.assert_invalid(value)
        for value in (True, False, "1", 1.0, 0, 2, None, []):
            data = example()
            data["schemaVersion"] = value
            with self.subTest(version=value):
                self.assert_invalid(data, "schemaVersion")

    def test_required_fields_at_every_level(self):
        locations = [(), ("series", 0), ("series", 0, "games", 0), ("players", 0)]
        for location in locations:
            parent = example()
            for key in location:
                parent = parent[key]
            for field in parent:
                data = example()
                target = data
                for key in location:
                    target = target[key]
                del target[field]
                with self.subTest(location=location, missing=field):
                    self.assert_invalid(data, field)

    def test_rejects_unsupported_format_extensions_instead_of_ignoring_them(self):
        for path, key, value in (((), "format", "multiplayer"), (("series", 0), "status", "in-progress"),
                                 (("series", 0, "games", 0), "players", ["L", "O", "X"]),
                                 (("players", 0), "team", "A")):
            data = example()
            target = data
            for part in path:
                target = target[part]
            target[key] = value
            with self.subTest(path=path):
                self.assert_invalid(data, key)

    def test_two_known_players_shortnames_and_no_duplicates(self):
        valid = example()["players"]
        cases = [None, {}, [], valid[:1], valid + [{"id": "X", "name": "Extra"}],
                 [valid[0], valid[0]], [{"id": "X", "name": "Liam"}, valid[1]],
                 [{"id": True, "name": "Liam"}, valid[1]],
                 [{"id": [], "name": "Liam"}, valid[1]],
                 [{"id": "L", "name": "Liam McGrath-Dent"}, valid[1]],
                 [{"id": "L", "name": None}, valid[1]], [None, valid[1]]]
        for value in cases:
            data = example()
            data["players"] = value
            with self.subTest(players=value):
                self.assert_invalid(data, "players")
        data = example()
        data["players"].reverse()
        self.assertEqual(analyze_series(data)["summary"]["challengeWins"], {"L": 4, "O": 0})

    def test_titles_and_provenance_must_be_strings_not_arbitrary_objects(self):
        for field in ("title", "sourceTitle"):
            for value in (None, False, 3, [], {}, "", " "):
                data = example()
                data[field] = value
                with self.subTest(field=field, value=value):
                    self.assert_invalid(data, field)
        for value in (None, [], {}, {"source": True}, {"source": "notes", "clock": []}):
            data = example()
            data["provenance"] = value
            with self.subTest(provenance=value):
                self.assert_invalid(data, "provenance")

    def test_iso_dates_are_strict_real_calendar_dates(self):
        for value in (True, False, None, 20260927, date(2026, 9, 27), [], {}, "2026-9-27",
                      "20260927", "2026-09-27T12:00:00", "2026-W39-7", "2026-02-29",
                      "2026-09-31", "2026-13-01", "0000-01-01", " 2026-09-27"):
            data = example()
            data["series"][0]["date"] = value
            with self.subTest(date=value):
                self.assert_invalid(data, ".date")

    def test_source_date_must_match_month_day_year_not_day_month_year(self):
        for value in (True, None, 9272026, [], {}, "27/9/2026", "9/26/2026", "9/27/26",
                      "9-27-2026", "2026-09-27", "9/27/2027", "9/00/2026", " 9/27/2026"):
            data = example()
            data["series"][0]["sourceDate"] = value
            with self.subTest(sourceDate=value):
                self.assert_invalid(data, "sourceDate")
        data = example()
        data["series"][0]["sourceDate"] = "09/27/2026"
        self.assertEqual(analyze_series(data)["series"][0]["sourceDate"], "09/27/2026")

    def test_valid_leap_day_is_supported(self):
        data = example()
        data["series"][0].update(date="2028-02-29", sourceDate="2/29/2028", id="2028-02-29-1")
        self.assertEqual(analyze_series(data)["series"][0]["date"], "2028-02-29")

    def test_sessions_are_positive_integer_not_boolean_or_float(self):
        for value in (True, False, 0, -1, 1.0, "1", None, [], {}):
            data = example()
            data["series"][0]["session"] = value
            with self.subTest(session=value):
                self.assert_invalid(data, "session")

    def test_unique_exact_date_session_ids_and_no_gaps_or_reversed_sessions(self):
        for value in (None, True, 1, [], "2026-09-27", "2026-09-27-01", "2026-09-27-2", "other"):
            data = example()
            data["series"][0]["id"] = value
            with self.subTest(id=value):
                self.assert_invalid(data, ".id")
        data = example()
        data["series"].append(deepcopy(data["series"][0]))
        self.assert_invalid(data, "duplicate")
        for session in (2, 3):
            data = example()
            data["series"][0].update(session=session, id=f"2026-09-27-{session}")
            self.assert_invalid(data, "session")
        data = example()
        second = deepcopy(data["series"][0])
        second.update(session=2, id="2026-09-27-2")
        data["series"] = [second, data["series"][0]]
        self.assert_invalid(data, "session")

    def test_series_games_and_game_objects_have_the_right_types(self):
        for path in (("series",), ("series", 0), ("series", 0, "games"), ("series", 0, "games", 0)):
            for value in (None, False, 1, "games", {}):
                data = example()
                target = data
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.subTest(path=path, value=value):
                    self.assert_invalid(data)

    def test_all_winners_and_challenges_are_known_and_case_sensitive(self):
        for field, bad_values in (("winner", (None, True, False, "l", "Liam", "X", 1, [], {})),
                                  ("challenge", (None, True, "HORSE", "unknown", "", 3, [], {}))):
            for value in bad_values:
                data = example()
                data["series"][0]["games"][0][field] = value
                with self.subTest(field=field, value=value):
                    self.assert_invalid(data, field)

    def test_round_limits_completion_and_no_post_clinch_play(self):
        for order in ("", "LLL", "LLLLLLLL", "LLOL", "LOLOLO", "LLLLL", "LLLLO", "OOOOLOL"):
            with self.subTest(order=order):
                self.assert_invalid(example(order), "games" if order else "order")

    def test_order_is_an_exact_string_not_a_reconstructed_replacement(self):
        for value in (None, True, 4, ["L"] * 4, "llll", " LLLL", "LLLL ", "LLLO", "LLLLL"):
            data = example()
            data["series"][0]["order"] = value
            with self.subTest(order=value):
                self.assert_invalid(data, "order")

    def test_all_240_short_binary_sequences_obey_first_to_four(self):
        completed = 0
        for length in range(4, 8):
            for values in product("LO", repeat=length):
                order = "".join(values)
                # Independent oracle: the final winner has exactly 4, and no
                # strict prefix reached 4 for either player.
                valid = (max(order.count("L"), order.count("O")) == 4
                         and max(order[:-1].count("L"), order[:-1].count("O")) < 4)
                with self.subTest(order=order):
                    if valid:
                        result = analyze_series(example(order))
                        self.assertEqual(result["series"][0]["winner"], order[-1])
                        self.assertEqual(result["summary"]["challengeCount"], length)
                        completed += 1
                    else:
                        self.assert_invalid(example(order))
        self.assertEqual(completed, 70)

    def test_rim_court_and_note_types_are_validated_without_guessing(self):
        for field, bad_values in (("court", (True, 1, [], {}, " ")),
                                  ("rimHeightInches", (True, False, "114", 0, -1, [], {}, float("inf"))),
                                  ("note", (None, False, 3, [], {}))):
            for value in bad_values:
                data = example()
                data["series"][0][field] = value
                with self.subTest(field=field, value=value):
                    self.assert_invalid(data, field)
        data = example()
        data["series"][0]["rimHeightInches"] = float("nan")
        with self.assertRaisesRegex(BasketballValidationError, "rimHeightInches"):
            analyze_series(data)
        data = example()
        data["series"][0].update(rimHeightInches=114.5, court="Synthetic court", note="")
        self.assertEqual(analyze_series(data)["series"][0]["rimHeightInches"], 114.5)
        for value in (None, True, 1, [], {}):
            data = example()
            data["series"][0]["games"][0]["note"] = value
            self.assert_invalid(data, "note")

    def test_invalid_durations_and_wrong_challenge_time_fields(self):
        for value in (None, True, False, 82, 82.0, [], {}, "", "1:60", "1:99", "1:2", "100:00",
                      "-1:10", "1:22.5", "1:22:00", "1m22s", " 1:22", "1:22 ", "tbd", "n/a"):
            data = example()
            data["series"][0]["games"][0].update(challenge="three-point", timeRaw=value)
            with self.subTest(time=value):
                self.assert_invalid(data, "timeRaw")
        data = example()
        data["series"][0]["games"][0]["timeRaw"] = "1:22"
        self.assert_invalid(data, "timeRaw")

    def test_scores_reject_wrong_types_and_invalid_1v1_points(self):
        for kind in ("horse", "bump", "one-on-one"):
            for value in (None, True, 7, 7.3, [], {}, ""):
                data = example()
                data["series"][0]["games"][0].update(challenge=kind, scoreRaw=value)
                with self.subTest(challenge=kind, score=value):
                    self.assert_invalid(data, "scoreRaw")
        for value in ("6-3", "9-3", "7-7", "8-7", "3-7", "7.3", "7/3", "7--3", "7:03", "07-3", "7 - 3"):
            data = example()
            data["series"][0]["games"][0].update(challenge="one-on-one", scoreRaw=value)
            with self.subTest(score=value):
                self.assert_invalid(data, "scoreRaw")
        data = example()
        data["series"][0]["games"][0]["scoreRaw"] = "7-3"
        self.assert_invalid(data, "scoreRaw")


class BasketballDynamicTests(unittest.TestCase):
    def test_duplicate_challenges_are_flagged_not_rejected(self):
        data = example()
        for game in data["series"][0]["games"]:
            game["challenge"] = "shooting"
        result = analyze_series(data)
        self.assertEqual(result["series"][0]["duplicateChallenges"], [{"challenge": "shooting", "count": 4}])
        shooting = result["challenges"][0]
        self.assertEqual(shooting["played"], 4)
        self.assertEqual(shooting["seriesWithChallenge"], 1)
        self.assertEqual(shooting["notPlayed"], 0)
        self.assertEqual(shooting["duplicateSeriesCount"], 1)
        self.assertEqual(result["transitionMatrix"]["counts"][0][0], 3)
        self.assertEqual(result["byPicker"][0]["countPicks"], 3)

    def test_absent_played_time_is_missing_not_not_played(self):
        data = example()
        data["series"][0]["games"][0]["challenge"] = "three-point"
        timing = analyze_series(data)["timing"]
        self.assertEqual(timing["played"], 1)
        self.assertEqual(timing["missingCount"], 1)
        self.assertEqual(timing["notPlayedCount"], 0)
        self.assertEqual(timing["missingEntries"][0]["status"], "missing")
        self.assertIsNone(timing["bestOverall"])
        self.assertEqual(timing["bestByPlayer"], {"L": None, "O": None})

    def test_zero_time_is_numeric_valid_and_distinct_from_unplayed(self):
        data = example()
        data["series"][0]["games"][0].update(challenge="three-point", timeRaw="00:00")
        timing = analyze_series(data)["timing"]
        self.assertEqual(timing["bestOverall"]["seconds"], 0)
        self.assertEqual(timing["bestOverall"]["status"], "valid")
        self.assertEqual(timing["missingCount"], 0)
        self.assertEqual(timing["played"], 1)
        self.assertEqual(timing["notPlayedCount"], 0)
        no_time = analyze_series(example())["timing"]
        self.assertEqual(no_time["notPlayedCount"], 1)
        self.assertIsNone(no_time["entries"][0]["seconds"])

    def test_tied_and_repeated_3point_games_are_all_retained(self):
        data = example()
        for game in data["series"][0]["games"]:
            game.update(challenge="three-point", timeRaw="01:22")
        timing = analyze_series(data)["timing"]
        self.assertEqual(timing["played"], 4)
        self.assertEqual(timing["validCount"], 4)
        self.assertEqual(len(timing["validEntries"]), 4)
        self.assertEqual(timing["bestOverall"]["round"], 1)
        self.assertEqual(timing["bestOverall"]["seconds"], 82)

    def test_1v1_can_end_at_eight_without_creating_another_match(self):
        data = example()
        data["series"][0]["games"][0].update(challenge="one-on-one", scoreRaw="8:6")
        result = analyze_series(data)
        self.assertEqual(result["summary"]["challengeCount"], 4)
        self.assertEqual(result["series"][0]["rounds"][0]["score"]["normalized"], "8-6")
        self.assertEqual(result["series"][0]["games"][0]["scoreRaw"], "8:6")

    def test_horse_and_bump_do_not_invent_an_orientation(self):
        for kind in ("horse", "bump"):
            data = example()
            data["series"][0]["games"][0].update(challenge=kind, scoreRaw="5-x")
            score = analyze_series(data)["series"][0]["rounds"][0]["score"]
            self.assertEqual(score["raw"], "5-x")
            self.assertEqual(score["status"], "recorded-uninterpreted")
            self.assertIsNone(score["winnerPoints"])

    def test_stable_date_sort_preserves_same_day_source_order(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        expected = [row["id"] for row in data["series"]]
        data["series"] = data["series"][2:] + data["series"][:2]
        before = deepcopy(data)
        result = analyze_series(data)
        self.assertEqual([row["id"] for row in result["series"]], expected)
        self.assertEqual([row["sourceIndex"] for row in result["series"][:2]], [12, 13])
        self.assertEqual(data, before)
        self.assertEqual(result["summary"]["currStreak"], {"player": "L", "length": 11})

    def test_future_logged_results_recompute_streak_without_date_cutoffs(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        extra = example("OOOO")["series"][0]
        extra.update(date="2027-01-01", sourceDate="1/1/2027", id="2027-01-01-1")
        data["series"].append(extra)
        result = analyze_series(data)
        self.assertEqual(result["summary"]["currStreak"], {"player": "O", "length": 1})
        self.assertEqual(result["summary"]["seriesWins"], {"L": 12, "O": 2})
        self.assertEqual(result["summary"]["challengeWins"], {"L": 50, "O": 27})
        self.assertEqual(result["summary"]["lastDate"], "2027-01-01")
        self.assertIsNone(result["series"][-1]["court"])
        self.assertEqual(result["summary"]["transitions"]["total"], 63)

    def test_winner_picks_next_is_not_forced_turn_taking(self):
        result = analyze_series(example("LLOOLL"))
        self.assertEqual([row["inferredPicker"] for row in result["series"][0]["rounds"]],
                         [None, "L", "L", "O", "O", "L"])
        self.assertEqual(result["summary"]["transitions"]["retentions"], 3)
        self.assertEqual(result["summary"]["transitions"]["switches"], 2)

    def test_comebacks_work_for_either_winner_including_three_round_deficit(self):
        for order in ("LLLOOOO", "OOOLLLL"):
            item = analyze_series(example(order))["series"][0]
            self.assertTrue(item["comeback"])
            self.assertEqual(item["winnerMaxDeficit"], 3)
            self.assertFalse(item["openingWinnerWonSeries"])
            self.assertTrue(item["decider"])

    def test_empty_completed_log_has_zero_counts_and_null_rates(self):
        data = example()
        data["series"] = []
        result = analyze_series(data)
        self.assertEqual(result["summary"]["seriesCount"], 0)
        self.assertEqual(result["summary"]["challengeCount"], 0)
        self.assertEqual(result["summary"]["currStreak"], {"player": None, "length": 0})
        self.assertIsNone(result["summary"]["firstDate"])
        self.assertIsNone(result["summary"]["transitions"]["retentionRate"])
        self.assertIsNone(result["timing"]["bestOverall"])
        for row in result["challenges"]:
            self.assertEqual(row["played"], 0)
            self.assertEqual(row["wins"], {"L": 0, "O": 0})
            self.assertEqual(row["winRates"], {"L": None, "O": None})
        for row in result["conditionalNextChallenge"]:
            self.assertEqual(row["countPicks"], 0)
            self.assertIsNone(row["choiceShare"])
            self.assertIsNone(row["winRate"])
        self.assertEqual(sum(map(sum, result["transitionMatrix"]["counts"])), 0)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)


class BasketballIOAndExportTests(unittest.TestCase):
    def test_analysis_is_deterministic_io_free_and_deeply_unmutating(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        before = deepcopy(data)
        with patch("builtins.open", side_effect=AssertionError("No analysis I/O")), \
             patch.object(Path, "open", side_effect=AssertionError("No analysis I/O")):
            first = analyze_series(data)
            second = analyze_series(data)
            self.assertEqual(first, second)
        self.assertEqual(data, before)
        first["series"][0]["games"][0]["winner"] = "O"
        self.assertEqual(first["series"][0]["rounds"][0]["winner"], "L")
        first["series"][0]["rounds"][1]["score"]["raw"] = "changed"
        first["players"][0]["name"] = "changed"
        first["provenance"]["source"] = "changed"
        first["timing"]["bestOverall"]["raw"] = "changed"
        self.assertEqual(data, before)
        self.assertEqual(second, analyze_series(data))

    def test_loader_reads_only_authored_source_and_preserves_its_bytes(self):
        before = sha256(SOURCE.read_bytes()).hexdigest()
        self.assertEqual(load_basketball(ROOT), analyze_series(json.loads(SOURCE.read_text(encoding="utf-8"))))
        self.assertEqual(sha256(SOURCE.read_bytes()).hexdigest(), before)

    def test_missing_source_raises_without_creating_fallback(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(FileNotFoundError):
                load_basketball(root)
            self.assertEqual(list(root.iterdir()), [])

    def test_loader_rejects_malformed_json_duplicate_keys_and_nonfinite_constants(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "records" / "basketball" / "series.json"
            path.parent.mkdir(parents=True)
            cases = ["{", "[]", '{"schemaVersion": 1, "schemaVersion": 1}',
                     json.dumps(example()).replace('"session": 1', '"session": NaN'),
                     json.dumps(example()).replace('"session": 1', '"session": Infinity'),
                     json.dumps(example()).replace('"session": 1', '"session": -Infinity'),
                     json.dumps(example()).replace('"winner": "L"', '"winner": "L", "winner": "O"', 1)]
            for text in cases:
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text[:50]):
                    with self.assertRaises(ValueError):
                        load_basketball(root)
                    self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_loader_decodes_utf8_without_escaping_display_data(self):
        data = example()
        data["title"] = "Court — résumé"
        with TemporaryDirectory() as folder:
            path = Path(folder) / "records" / "basketball" / "series.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(load_basketball(Path(folder))["title"], data["title"])

    def test_export_tables_are_scalar_consistent_and_json_csv_ready(self):
        result = load_basketball(ROOT)
        before = deepcopy(result)
        with patch("builtins.open", side_effect=AssertionError("No export I/O")), \
             patch.object(Path, "open", side_effect=AssertionError("No export I/O")):
            tables = export_rows(result)
        expected_lengths = {"summary": 1, "series": 13, "rounds": 73, "challenges": 7,
                            "transitions": 60, "byPicker": 2, "conditionalNextChallenge": 14,
                            "transitionMatrix": 49, "trajectories": 86, "timing": 13,
                            "seriesLengths": 4, "comebacks": 4}
        self.assertEqual({key: len(rows) for key, rows in tables.items()}, expected_lengths)
        for name, rows in tables.items():
            with self.subTest(table=name):
                keys = set(rows[0])
                for row in rows:
                    self.assertEqual(set(row), keys)
                    for value in row.values():
                        self.assertIn(type(value), (str, int, float, bool, type(None)))
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
                self.assertEqual(len(list(csv.DictReader(io.StringIO(output.getvalue())))), len(rows))
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        self.assertEqual(result, before)
        tables["transitions"][0]["nextWinner"] = "changed"
        tables["timing"][0]["raw"] = "changed"
        self.assertEqual(result, before)

    def test_export_retains_raw_scores_notes_nulls_and_zero_denominators(self):
        tables = export_rows(load_basketball(ROOT))
        row = next(row for row in tables["rounds"] if row["scoreRaw"] == "7:3")
        self.assertEqual(row["scoreNormalized"], "7-3")
        horse = next(row for row in tables["rounds"] if row["challenge"] == "horse" and row["scoreRaw"])
        self.assertIsNone(horse["winnerPoints"])
        self.assertIsNone(horse["scoreNormalized"])
        missing = next(row for row in tables["timing"] if row["status"] == "not-played")
        self.assertIsNone(missing["seconds"])
        self.assertFalse(missing["played"])
        shooting = next(row for row in tables["conditionalNextChallenge"] if row["nextChallenge"] == "shooting")
        self.assertEqual(shooting["countPicks"], 0)
        self.assertIsNone(shooting["winRate"])

    def test_display_and_csv_safety_belong_to_parent_not_data_transformation(self):
        data = example()
        payload = '=1+1 <script> & "quoted" </script>'
        data["series"][0]["games"][0]["note"] = payload
        result = analyze_series(data)
        self.assertEqual(result["series"][0]["games"][0]["note"], payload)
        self.assertEqual(export_rows(result)["rounds"][0]["note"], payload)
        self.assertEqual(json.loads(json.dumps(result))["series"][0]["rounds"][0]["note"], payload)


if __name__ == "__main__":
    unittest.main()