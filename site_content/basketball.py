"""Validated, read-only descriptions of the two-player first-to-four log.

Public API: analyze_series(data), load_basketball(root), export_rows(result).
The JSON/CSV contract and denominators are in records/basketball/README.md.
No publishing, clocks, network, randomness, pandas, or optional dependencies.
Strings are unescaped source data: the caller owns safe JSON/HTML/CSV output.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import date
import json
import math
from pathlib import Path
import re
from typing import Any


__all__ = ["BasketballValidationError", "analyze_series", "load_basketball", "export_rows"]

_PLAYERS = {"L": "Liam", "O": "Owen"}
_CHALLENGES = (
    ("shooting", "Shooting"),
    ("bump", "Bump"),
    ("horse", "HORSE"),
    ("backboard", "Backboard"),
    ("three-point", "3 Point"),
    ("rim", "Rim"),
    ("one-on-one", "1v1"),
)
_IDS = tuple(key for key, _ in _CHALLENGES)
_SOURCE_PATH = "records/basketball/series.json"
_CAVEATS = (
    "Small-sample, within-series descriptions only; no statistical significance or ability estimates.",
    "There is no implied 50% random baseline: player skill may differ and selection is truncated by the clinch.",
    "After round one, the previous winner is only the inferred picker under winner-picks-next; actual decisions were not logged.",
    "Holds and losses describe observed next-round outcomes, not causal effects or a best picking strategy.",
    "A switch means consecutive round winners differ, not that the choice of challenge caused an outcome.",
    "Same-day sessions follow source entry order, not measured start times; no cross-series transition is counted.",
    "HORSE and Bump score mechanics and orientation are unconfirmed; raw strings are not interpreted as points or letters.",
    "1v1 winner-labelled scores use a minimum of 7; a two-point shot can finish at 8. This is a rule note, not an extra match.",
    "3 Point times are listed winner completion times only; attempt counts, losing times and rebounding assistance are not standardized.",
    "Absent courts and rim heights stay null; the August observations are not carried forward.",
    "Mercies and dinner obligations are unlogged and are not inferred.",
    "Only completed two-player first-to-four series are supported; no future wins or multiplayer extensions are projected.",
)


class BasketballValidationError(ValueError):
    """Malformed source with a JSON-style location in the error message."""


def _fail(path: str, message: str) -> None:
    raise BasketballValidationError(f"{path}: {message}")


def _object(value: Any, path: str, required: set[str], optional: set[str]) -> None:
    if not isinstance(value, dict):
        _fail(path, "expected an object")
    missing = required - value.keys()
    if missing:
        _fail(path, f"missing fields: {', '.join(sorted(missing))}")
    extra = value.keys() - required - optional
    if extra:
        _fail(path, f"unsupported fields: {', '.join(sorted(map(str, extra)))}")


def _text(value: Any, path: str, *, empty: bool = False) -> None:
    if not isinstance(value, str) or (not empty and not value.strip()):
        _fail(path, "expected a string" if empty else "expected a nonempty string")


def _fraction(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _opponent(player: str) -> str:
    return "O" if player == "L" else "L"


def _time(game: dict[str, Any], path: str) -> dict[str, Any]:
    raw = game.get("timeRaw")
    if game["challenge"] != "three-point":
        if "timeRaw" in game:
            _fail(f"{path}.timeRaw", "only 3 Point has a completion-time field")
        return {"raw": None, "seconds": None, "status": "not-applicable"}
    if "timeRaw" not in game:
        return {"raw": None, "seconds": None, "status": "missing"}
    _text(raw, f"{path}.timeRaw")
    if raw in ("TBD", "N/A"):
        return {"raw": raw, "seconds": None,
                "status": "pending" if raw == "TBD" else "not-recorded"}
    if not re.fullmatch(r"[0-9]{1,2}:[0-5][0-9]", raw):
        _fail(f"{path}.timeRaw", "expected M:SS or MM:SS (seconds < 60), TBD, or N/A")
    minutes, seconds = map(int, raw.split(":"))
    return {"raw": raw, "seconds": minutes * 60 + seconds, "status": "valid"}


def _score(game: dict[str, Any], path: str) -> dict[str, Any]:
    raw = game.get("scoreRaw")
    kind = game["challenge"]
    result = {"raw": raw, "normalized": None, "winnerPoints": None,
              "loserPoints": None, "status": "not-recorded"}
    if "scoreRaw" not in game:
        if kind not in ("horse", "bump", "one-on-one"):
            result["status"] = "not-applicable"
        return result
    _text(raw, f"{path}.scoreRaw")
    if kind in ("horse", "bump"):
        result["status"] = "recorded-uninterpreted"
        return result
    if kind != "one-on-one":
        _fail(f"{path}.scoreRaw", "scored format is supported only for HORSE, Bump and 1v1")
    if not re.fullmatch(r"[78][:-][0-6]", raw):
        _fail(f"{path}.scoreRaw", "expected winner-loser 1v1 points: 7 or 8 to 0..6, using - or :")
    winner_points, loser_points = map(int, re.split(r"[:-]", raw))
    return {"raw": raw, "normalized": f"{winner_points}-{loser_points}",
            "winnerPoints": winner_points, "loserPoints": loser_points,
            "status": "winner-loser-points"}


def _validate(data: dict[str, Any]) -> None:
    _object(data, "$", {"schemaVersion", "title", "sourceTitle", "players", "provenance", "series"}, set())
    if type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1:
        _fail("$.schemaVersion", "only integer schema version 1 is supported")
    for key in ("title", "sourceTitle"):
        _text(data[key], f"$.{key}")
    players = data["players"]
    if not isinstance(players, list) or len(players) != 2:
        _fail("$.players", "exactly two players, Liam (L) and Owen (O), are supported")
    seen_players: set[str] = set()
    for index, player in enumerate(players):
        path = f"$.players[{index}]"
        _object(player, path, {"id", "name"}, set())
        _text(player["id"], f"{path}.id")
        if player["id"] not in _PLAYERS or player["id"] in seen_players:
            _fail(f"{path}.id", "expected a unique L or O")
        if player["name"] != _PLAYERS[player["id"]]:
            _fail(f"{path}.name", "sports player names must be the public shortnames Liam and Owen")
        seen_players.add(player["id"])
    provenance = data["provenance"]
    if not isinstance(provenance, dict) or "source" not in provenance:
        _fail("$.provenance", "expected an object with a source string")
    for key, value in provenance.items():
        _text(key, "$.provenance key")
        _text(value, f"$.provenance.{key}")
    if not isinstance(data["series"], list):
        _fail("$.series", "expected an array of completed series")

    seen_ids: set[str] = set()
    sessions: Counter[str] = Counter()
    for index, series in enumerate(data["series"]):
        path = f"$.series[{index}]"
        _object(series, path, {"id", "date", "sourceDate", "session", "order", "games"},
                {"court", "rimHeightInches", "note"})
        iso = series["date"]
        _text(iso, f"{path}.date")
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", iso):
            _fail(f"{path}.date", "expected an ISO YYYY-MM-DD date, without a clock time")
        try:
            parsed_date = date.fromisoformat(iso)
        except ValueError:
            _fail(f"{path}.date", "not a valid calendar date")
        source_date = series["sourceDate"]
        _text(source_date, f"{path}.sourceDate")
        if not re.fullmatch(r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}", source_date):
            _fail(f"{path}.sourceDate", "expected M/D/YYYY")
        month, day, year = map(int, source_date.split("/"))
        if (year, month, day) != (parsed_date.year, parsed_date.month, parsed_date.day):
            _fail(f"{path}.sourceDate", "M/D/YYYY does not match the ISO date")
        session = series["session"]
        if type(session) is not int or session < 1:
            _fail(f"{path}.session", "expected a positive integer, not a boolean")
        _text(series["id"], f"{path}.id")
        if series["id"] != f"{iso}-{session}":
            _fail(f"{path}.id", "expected date-session, e.g. 2026-09-07-1")
        if series["id"] in seen_ids:
            _fail(f"{path}.id", "duplicate date-session identifier")
        seen_ids.add(series["id"])
        sessions[iso] += 1
        if session != sessions[iso]:
            _fail(f"{path}.session", "sessions on each date must be 1-based consecutive source entries")
        if series.get("court") is not None:
            _text(series["court"], f"{path}.court")
        rim = series.get("rimHeightInches")
        if rim is not None and (type(rim) not in (int, float) or not math.isfinite(rim) or rim <= 0):
            _fail(f"{path}.rimHeightInches", "expected a finite positive number or null, not a boolean")
        if "note" in series:
            _text(series["note"], f"{path}.note", empty=True)
        _text(series["order"], f"{path}.order")
        games = series["games"]
        if not isinstance(games, list) or not 4 <= len(games) <= 7:
            _fail(f"{path}.games", "a completed first-to-four series has 4..7 rounds")
        wins = {player: 0 for player in _PLAYERS}
        for number, game in enumerate(games):
            game_path = f"{path}.games[{number}]"
            _object(game, game_path, {"challenge", "winner"}, {"scoreRaw", "timeRaw", "note"})
            _text(game["challenge"], f"{game_path}.challenge")
            if game["challenge"] not in _IDS:
                _fail(f"{game_path}.challenge", "unknown challenge kind")
            _text(game["winner"], f"{game_path}.winner")
            if game["winner"] not in _PLAYERS:
                _fail(f"{game_path}.winner", "expected L or O")
            if 4 in wins.values():
                _fail(game_path, "round after the first-to-four clinch")
            wins[game["winner"]] += 1
            if "note" in game:
                _text(game["note"], f"{game_path}.note", empty=True)
            _score(game, game_path)
            _time(game, game_path)
        if 4 not in wins.values():
            _fail(f"{path}.games", "incomplete series: neither player reached four wins")
        if series["order"] != "".join(game["winner"] for game in games):
            _fail(f"{path}.order", "must exactly match the game winners in source order")


def _definitions() -> list[dict[str, Any]]:
    return [
        {"id": key, "label": label, "hasWinnerTime": key == "three-point",
         "scoreSemantics": ("winner-loser-points" if key == "one-on-one" else
                            "unconfirmed" if key in ("horse", "bump") else "not-recorded"),
         "repeatPolicy": "unconfirmed; duplicates are flagged, not rejected"}
        for key, label in _CHALLENGES
    ]


def _enrich_series(raw: dict[str, Any], source_index: int, sequence_index: int) -> dict[str, Any]:
    series = deepcopy(raw)
    wins = {player: 0 for player in _PLAYERS}
    rounds = []
    trajectory = [{"round": 0, "L": 0, "O": 0, "margin": 0}]
    for number, game in enumerate(raw["games"], 1):
        previous = raw["games"][number - 2]["winner"] if number > 1 else None
        wins[game["winner"]] += 1
        point = {"round": number, **wins, "margin": wins["L"] - wins["O"]}
        trajectory.append(point)
        rounds.append({
            **deepcopy(game), "number": number, "loser": _opponent(game["winner"]),
            "cumulativeWins": dict(wins), "margin": point["margin"],
            "score": _score(game, "game"), "time": _time(game, "game"),
            "previousWinner": previous, "inferredPicker": previous,
            "retained": previous == game["winner"] if previous is not None else None,
        })
    winner = rounds[-1]["winner"]
    direction = 1 if winner == "L" else -1
    deficit = max(-direction * point["margin"] for point in trajectory)
    counts = Counter(game["challenge"] for game in raw["games"])
    retentions = sum(row["retained"] is True for row in rounds)
    transitions = len(rounds) - 1
    series.update({
        "sourceIndex": source_index, "sequenceIndex": sequence_index,
        "court": raw.get("court"), "rimHeightInches": raw.get("rimHeightInches"),
        "rounds": rounds, "roundCount": len(rounds), "winner": winner,
        "loser": _opponent(winner), "challengeWins": wins,
        "finalScore": f"{wins[winner]}-{wins[_opponent(winner)]}",
        "sweep": len(rounds) == 4, "decider": len(rounds) == 7,
        "openingWinner": rounds[0]["winner"],
        "openingWinnerWonSeries": rounds[0]["winner"] == winner,
        "trajectory": trajectory, "winnerMaxDeficit": deficit, "comeback": deficit > 0,
        "duplicateChallenges": [{"challenge": key, "count": counts[key]} for key in _IDS if counts[key] > 1],
        "transitionCount": transitions, "retentions": retentions,
        "switches": transitions - retentions,
        "retentionRate": _fraction(retentions, transitions),
        "switchRate": _fraction(transitions - retentions, transitions),
    })
    return series


def _timing(series: list[dict[str, Any]]) -> dict[str, Any]:
    entries = []
    for item in series:
        context = {"seriesId": item["id"], "date": item["date"], "session": item["session"],
                   "sequenceIndex": item["sequenceIndex"]}
        played = [row for row in item["rounds"] if row["challenge"] == "three-point"]
        entries.extend({**context, "round": row["number"], "winner": row["winner"],
                        "played": True, **row["time"], "note": row.get("note")}
                       for row in played)
        if not played:
            entries.append({**context, "round": None, "winner": None, "played": False,
                            "raw": None, "seconds": None, "status": "not-played", "note": None})
    valid = [row for row in entries if row["status"] == "valid"]
    missing = [row for row in entries if row["played"] and row["status"] != "valid"]
    not_played = [row for row in entries if not row["played"]]
    best = min(valid, key=lambda row: row["seconds"], default=None)
    by_player = {player: [row for row in valid if row["winner"] == player] for player in _PLAYERS}
    return {
        "entries": entries, "validEntries": deepcopy(valid), "missingEntries": deepcopy(missing),
        "notPlayedEntries": deepcopy(not_played), "played": len(valid) + len(missing),
        "validCount": len(valid), "missingCount": len(missing), "notPlayedCount": len(not_played),
        "statusCounts": {status: sum(row["status"] == status for row in entries)
                         for status in ("valid", "pending", "not-recorded", "missing", "not-played")},
        "bestOverall": deepcopy(best),
        "bestByPlayer": {player: deepcopy(min(rows, key=lambda row: row["seconds"], default=None))
                         for player, rows in by_player.items()},
        "byPlayer": [{"player": player,
                      "played": sum(row["winner"] == player for row in entries),
                      "validCount": len(by_player[player]),
                      "missingCount": sum(row["winner"] == player for row in missing)}
                     for player in _PLAYERS],
    }


def analyze_series(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and describe schema-1 data without mutating it or performing I/O.

    Stable ISO-date ordering keeps source order for entries on the same day.
    All rates are fractions, not percentages; a zero denominator yields None.
    BasketballValidationError rejects malformed/unsupported data atomically.
    """
    _validate(data)
    ordered = sorted(enumerate(data["series"], 1), key=lambda pair: pair[1]["date"])
    series = [_enrich_series(raw, source_index, index)
              for index, (source_index, raw) in enumerate(ordered, 1)]
    rounds = [row for item in series for row in item["rounds"]]
    series_wins = {player: sum(item["winner"] == player for item in series) for player in _PLAYERS}
    challenge_wins = {player: sum(row["winner"] == player for row in rounds) for player in _PLAYERS}
    streak_player = series[-1]["winner"] if series else None
    streak_length = 0
    for item in reversed(series):
        if item["winner"] != streak_player:
            break
        streak_length += 1

    transitions = []
    matrix = [[0 for _ in _IDS] for _ in _IDS]
    for item in series:
        for previous, following in zip(item["rounds"], item["rounds"][1:]):
            transitions.append({
                "seriesId": item["id"], "date": item["date"], "session": item["session"],
                "previousRound": previous["number"], "nextRound": following["number"],
                "prevWinner": previous["winner"], "inferredPicker": previous["winner"],
                "previousChallenge": previous["challenge"], "nextChallenge": following["challenge"],
                "nextWinner": following["winner"], "retained": following["retained"],
            })
            matrix[_IDS.index(previous["challenge"])][_IDS.index(following["challenge"])] += 1
    by_picker = []
    conditional = []
    for player in _PLAYERS:
        picks = [row for row in transitions if row["inferredPicker"] == player]
        holds = sum(row["retained"] for row in picks)
        by_picker.append({"player": player, "countPicks": len(picks), "denominator": len(picks),
                          "holds": holds, "losses": len(picks) - holds,
                          "holdRate": _fraction(holds, len(picks)),
                          "lossRate": _fraction(len(picks) - holds, len(picks))})
        for challenge in _IDS:
            choices = [row for row in picks if row["nextChallenge"] == challenge]
            count_wins = sum(row["retained"] for row in choices)
            conditional.append({
                "player": player, "nextChallenge": challenge,
                "countPicks": len(choices), "countWins": count_wins,
                "countLosses": len(choices) - count_wins, "pickerTotal": len(picks),
                "choiceShare": _fraction(len(choices), len(picks)),
                "winRate": _fraction(count_wins, len(choices)),
            })
    challenges = []
    for key, label in _CHALLENGES:
        games = [row for row in rounds if row["challenge"] == key]
        wins = {player: sum(row["winner"] == player for row in games) for player in _PLAYERS}
        played_series = sum(any(row["challenge"] == key for row in item["rounds"]) for item in series)
        challenges.append({
            "id": key, "label": label, "played": len(games), "wins": wins,
            "winRateDenominator": len(games),
            "winRates": {player: _fraction(count, len(games)) for player, count in wins.items()},
            "seriesWithChallenge": played_series, "notPlayed": len(series) - played_series,
            "duplicateSeriesCount": sum(any(row["challenge"] == key for row in item["duplicateChallenges"])
                                        for item in series),
        })
    lengths = []
    for length in range(4, 8):
        items = [item for item in series if item["roundCount"] == length]
        lengths.append({"roundCount": length, "seriesCount": len(items),
                        "seriesRate": _fraction(len(items), len(series)),
                        "seriesWins": {player: sum(item["winner"] == player for item in items)
                                       for player in _PLAYERS}})
    comebacks = []
    for deficit in range(4):
        items = [item for item in series if item["winnerMaxDeficit"] == deficit]
        comebacks.append({"winnerMaxDeficit": deficit, "seriesCount": len(items),
                          "seriesWins": {player: sum(item["winner"] == player for item in items)
                                         for player in _PLAYERS}})
    retentions = sum(row["retained"] for row in transitions)
    opening_wins = sum(item["openingWinnerWonSeries"] for item in series)
    summary = {
        "seriesCount": len(series), "challengeCount": len(rounds),
        "distinctDateCount": len({item["date"] for item in series}),
        "firstDate": series[0]["date"] if series else None,
        "lastDate": series[-1]["date"] if series else None,
        "seriesWins": series_wins, "challengeWins": challenge_wins,
        "seriesWinRates": {player: _fraction(count, len(series)) for player, count in series_wins.items()},
        "challengeWinRates": {player: _fraction(count, len(rounds)) for player, count in challenge_wins.items()},
        "currStreak": {"player": streak_player, "length": streak_length},
        "sweeps": sum(item["sweep"] for item in series),
        "deciders": sum(item["decider"] for item in series),
        "sweepWins": {player: sum(item["sweep"] and item["winner"] == player for item in series)
                      for player in _PLAYERS},
        "deciderWins": {player: sum(item["decider"] and item["winner"] == player for item in series)
                        for player in _PLAYERS},
        "comebacks": sum(item["comeback"] for item in series),
        "openingWinnerWonSeries": opening_wins, "openingWinnerWinRate": _fraction(opening_wins, len(series)),
        "transitions": {"total": len(transitions), "switches": len(transitions) - retentions,
                        "retentions": retentions, "switchRate": _fraction(len(transitions) - retentions, len(transitions)),
                        "retentionRate": _fraction(retentions, len(transitions))},
    }
    return {
        "schemaVersion": 1, "title": data["title"],
        "source": {"path": _SOURCE_PATH, "schemaVersion": data["schemaVersion"],
                   "sourceTitle": data["sourceTitle"],
                   "chronology": "ISO date, then source entry order; no actual clock times"},
        "provenance": deepcopy(data["provenance"]), "players": deepcopy(data["players"]),
        "challengeDefinitions": _definitions(), "series": series, "summary": summary,
        "challenges": challenges, "transitions": transitions, "byPicker": by_picker,
        "transitionMatrix": {"challengeOrder": list(_IDS), "counts": matrix},
        "conditionalNextChallenge": conditional, "seriesLengths": lengths,
        "comebacks": comebacks,
        "trajectories": [{"seriesId": item["id"], "date": item["date"], "session": item["session"], **point}
                         for item in series for point in item["trajectory"]],
        "timing": _timing(series), "caveats": list(_CAVEATS),
    }


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("$", f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _json_constant(value: str) -> Any:
    _fail("$", f"non-finite JSON constant: {value}")


def load_basketball(root: Path) -> dict[str, Any]:
    """Read root/records/basketball/series.json as UTF-8 and analyze it.

    Missing files and invalid JSON propagate, never trigger fallback data.
    JSON duplicate keys and NaN/Infinity are rejected before source validation.
    """
    data = json.loads((root / _SOURCE_PATH).read_text(encoding="utf-8"),
                      object_pairs_hook=_json_object, parse_constant=_json_constant)
    return analyze_series(data)


def export_rows(result: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return fresh, scalar-only CSV tables; do not escape strings or write files.

    Input is a result of analyze_series/load_basketball, not the raw source.
    None means missing/undefined, never a fabricated zero. CSV output safety
    (including spreadsheet formula handling) remains the publisher's job.
    """
    series_rows = []
    round_rows = []
    for item in result["series"]:
        context = {key: item[key] for key in ("date", "sourceDate", "session", "sourceIndex", "sequenceIndex")}
        context["seriesId"] = item["id"]
        series_rows.append({
            **context, **{key: item[key] for key in (
                "order", "roundCount", "winner", "loser", "finalScore", "sweep", "decider",
                "openingWinner", "openingWinnerWonSeries", "winnerMaxDeficit", "comeback",
                "court", "rimHeightInches", "transitionCount", "retentions", "switches", "retentionRate", "switchRate")},
            "winsL": item["challengeWins"]["L"], "winsO": item["challengeWins"]["O"],
            "duplicateChallenges": ";".join(f"{row['challenge']}:{row['count']}" for row in item["duplicateChallenges"]),
            "note": item.get("note"),
        })
        for row in item["rounds"]:
            round_rows.append({
                **context, "round": row["number"], "challenge": row["challenge"],
                "winner": row["winner"], "loser": row["loser"], "note": row.get("note"),
                "court": item["court"], "rimHeightInches": item["rimHeightInches"],
                "cumulativeL": row["cumulativeWins"]["L"], "cumulativeO": row["cumulativeWins"]["O"],
                "margin": row["margin"], "inferredPicker": row["inferredPicker"],
                "previousWinner": row["previousWinner"], "retained": row["retained"],
                "scoreRaw": row["score"]["raw"], "scoreNormalized": row["score"]["normalized"],
                "scoreStatus": row["score"]["status"], "winnerPoints": row["score"]["winnerPoints"],
                "loserPoints": row["score"]["loserPoints"], "timeRaw": row["time"]["raw"],
                "timeSeconds": row["time"]["seconds"], "timeStatus": row["time"]["status"],
            })
    summary = result["summary"]
    summary_row = {key: value for key, value in summary.items() if not isinstance(value, dict)}
    for key in ("seriesWins", "challengeWins", "seriesWinRates", "challengeWinRates", "sweepWins", "deciderWins"):
        summary_row.update({f"{key}{player}": value for player, value in summary[key].items()})
    summary_row.update({"streakPlayer": summary["currStreak"]["player"], "streakLength": summary["currStreak"]["length"]})
    summary_row.update({f"transitions{key[0].upper()}{key[1:]}": value for key, value in summary["transitions"].items()})
    challenges = []
    for row in result["challenges"]:
        challenges.append({
            **{key: value for key, value in row.items() if key not in ("wins", "winRates")},
            **{f"wins{player}": row["wins"][player] for player in _PLAYERS},
            **{f"winRate{player}": row["winRates"][player] for player in _PLAYERS},
        })
    order = result["transitionMatrix"]["challengeOrder"]
    tables = {
        "summary": [summary_row], "series": series_rows, "rounds": round_rows,
        "challenges": challenges,
        "transitionMatrix": [{"previousChallenge": previous, "nextChallenge": following,
                              "count": result["transitionMatrix"]["counts"][i][j]}
                             for i, previous in enumerate(order) for j, following in enumerate(order)],
        "timing": [dict(row) for row in result["timing"]["entries"]],
    }
    for key in ("transitions", "byPicker", "conditionalNextChallenge", "trajectories"):
        tables[key] = [dict(row) for row in result[key]]
    for key in ("seriesLengths", "comebacks"):
        tables[key] = [{**{name: value for name, value in row.items() if name != "seriesWins"},
                        **{f"seriesWins{player}": row["seriesWins"][player] for player in _PLAYERS}}
                       for row in result[key]]
    return tables