"""Read and summarize the athletics logs in records/athletics; nothing is written.

load_athletics(root) -> {"running", "swimming", "weightlifting"}; athletics_rows(data)
returns CSV-ready tables. Parsers keep every raw value, fail with the line number on
anything they cannot read, and never fill gaps: a recorded average that differs from
the computed mean is reported, not corrected. Owner-recalled history (best times and
peaks from the overviews) is labelled as an estimate, separate from the logs.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import re
from statistics import mean

SOURCES = {
    "running": "records/athletics/running/Interval_Data.txt",
    "tempo": "records/athletics/running/Tempo_Run_Log.txt",
    "swimming": "records/athletics/swimming/Swimming_Log.txt",
    "weightlifting": "records/athletics/weightlifting/Weightlifting_Log.txt",
}
# Earlier copies beside the local site preview. If one differs, the build stops rather
# than silently ignoring an edit made there.
EARLIER_COPIES = {
    "running": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics/Running/Interval_Data.txt",
    "tempo": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics/Running/Tempo_Run_Log.txt",
    "swimming": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics/Swimming/Swimming_Log.txt",
    "weightlifting": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics/Weightlifting/Weightlifting_Log.txt",
}
# Heaviest weight (least assistance for assisted lifts) managed for at least this many reps.
REP_TARGETS = (10, 12)
ROUTES = {"I1": {"name": "Interval route 1", "distanceKm": 0.95,
                 "distanceSource": "GeoDistance measurement shown on the route map"}}
RUN_HISTORY = (
    {"year": 2013, "session": "12 × 400 m", "repeatMeters": 400, "best": "1:08"},
    {"year": 2017, "session": "8 × 800 m", "repeatMeters": 800, "best": "2:42"},
    {"year": 2017, "session": "4 × 1600 m", "repeatMeters": 1600, "best": "5:38"},
)
SWIM_BESTS = (
    {"event": "50 m freestyle", "liam": 27.09, "owen": 26.99},
    {"event": "50 m butterfly", "liam": 32.60, "owen": 33.80},
)
LIFT_PEAKS = (
    {"peak": "First peak", "lift": "Squat", "weightLbs": 315, "reps": None},
    {"peak": "First peak", "lift": "Deadlift", "weightLbs": 315, "reps": None},
    {"peak": "Second peak", "lift": "Barbell press", "weightLbs": 205, "reps": None},
    {"peak": "Another peak", "lift": "Chest press", "weightLbs": 65, "reps": 6},
    {"peak": "Another peak", "lift": "Shoulder press", "weightLbs": 65, "reps": 6},
)
# Display-only spelling fixes; the raw names stay in every export.
SPELLING = (("Assited", "Assisted"), ("Dumbell", "Dumbbell"), ("Bend Over", "Bent Over"), ("Lazanga", "Lasagna"))
SPLITS = {"chest": "Chest", "back": "Back", "delts": "Shoulders", "shoulders": "Shoulders"}
YARD = 0.9144  # exact metres per yard

_DATE = r"(\d{1,2})/(\d{1,2})/(\d{4})"
_RUN = re.compile(rf"(I\d+) - \({_DATE}\) - (\d+) Intervals?")
_TIME = re.compile(r"(\d{1,2}):([0-5]\d(?:\.\d+)?)")
_AVG = re.compile(r"Avg: (\d{1,2}:[0-5]\d(?:\.\d+)?)")
_SWIM = re.compile(rf"\({_DATE}\) - (\d+)(m|y) - (.+)")
_SWIM_REPEAT = re.compile(r"(\d+)\s*x\s*(\d+)m?")
_SWIM_SINGLE = re.compile(r"(?<![\dx.])(\d{2,})m\b")
_STROKES = re.compile(r"Fly|Back|Breast|Free")
_LIFT_DAY = re.compile(rf"{_DATE}(?: ?- ?| )(.+)")
_EXERCISE = re.compile(r"([^;:]+?)\s*[;:]\s*(.*)")
_SET = re.compile(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*lbs")
_SET_BODYWEIGHT = re.compile(r"(\d+)xBodyweight", re.IGNORECASE)
_SET_DROP = re.compile(r"ds(\d+)x(\d+(?:\.\d+)?)(?:lbs)?")
_SET_WEIGHT_ONLY = re.compile(r"(\d+(?:\.\d+)?)lbs")
_TEMPO_HEAD = re.compile(rf"\({_DATE}\)")
_TEMPO_RUN = re.compile(r"Tempo Run - (\d+(?:\.\d+)?)km \((.+)\)")
# Total time as written: 23:35.21, or with dots as separators (33.23.81).
_TEMPO_TIME = re.compile(r"(\d{1,2})[:.]([0-5]\d)\.(\d{1,2})")
_TEMPO_WRITTEN = re.compile(r"(\d{1,2}):([0-5]\d(?:\.\d+)?) ?min/km - (\d+(?:\.\d+)?) ?m/s")


def _iso(month: str, day: str, year: str) -> str:
    return date(int(year), int(month), int(day)).isoformat()


def seconds(raw: str) -> float:
    match = _TIME.fullmatch(raw)
    if not match:
        raise ValueError(f"Unreadable time {raw!r}")
    value = int(match[1]) * 60 + float(match[2])
    return int(value) if value == int(value) else value


def clock(value: float) -> str:
    whole = int(value + 0.5)  # Half-seconds round up, as on a stopwatch display.
    return f"{whole // 60}:{whole % 60:02d}"


def _lines(text: str) -> list[tuple[int, str]]:
    return [(number, line.strip()) for number, line in enumerate(text.splitlines(), 1) if line.strip()]


def _week(iso: str) -> str:
    day = date.fromisoformat(iso)
    return (day - timedelta(days=day.weekday())).isoformat()


def parse_running(text: str) -> dict:
    lines = _lines(text)
    if not lines or lines[0][1] != "Interval Training Data":
        raise ValueError("Running log must start with 'Interval Training Data'.")
    sessions, current = [], None

    def close(current: dict | None) -> None:
        if current is None:
            return
        if len(current["intervals"]) != current["declared"]:
            raise ValueError(f"Line {current['line']}: {current['declared']} intervals declared, "
                             f"{len(current['intervals'])} listed.")
        current.setdefault("recordedAverage", None)  # 10/3 has no written Avg; kept missing.
        sessions.append(current)

    for number, line in lines[1:]:
        if match := _RUN.fullmatch(line):
            close(current)
            if match[1] not in ROUTES:
                raise ValueError(f"Line {number}: route {match[1]} has no recorded distance.")
            current = {"route": match[1], "date": _iso(*match.group(2, 3, 4)), "declared": int(match[5]),
                       "line": number, "intervals": []}
        elif current is not None and _TIME.fullmatch(line):
            current["intervals"].append({"number": len(current["intervals"]) + 1, "raw": line, "seconds": seconds(line)})
        elif current is not None and "recordedAverage" not in current and (match := _AVG.fullmatch(line)):
            current["recordedAverage"] = {"raw": match[1], "seconds": seconds(match[1])}
        else:
            raise ValueError(f"Line {number}: unreadable running entry {line!r}.")
    close(current)
    for index, item in enumerate(sessions):
        times = [interval["seconds"] for interval in item["intervals"]]
        distance = ROUTES[item["route"]]["distanceKm"]
        item.update(id=f"{item['date']}-{item['route']}-{index + 1}", count=len(times), average=round(mean(times), 2),
                    best=min(times), worst=max(times), spread=round(max(times) - min(times), 2),
                    fade=round(times[-1] - times[0], 2), pacePerKm=round(mean(times) / distance, 1))
        item["averageDifference"] = (round(item["average"] - item["recordedAverage"]["seconds"], 2)
                                     if item["recordedAverage"] else None)
        del item["declared"], item["line"]
    if not sessions:
        raise ValueError("The running log has no sessions.")
    every = [(interval["seconds"], item["date"]) for item in sessions for interval in item["intervals"]]
    best = min(every)
    first, last = sessions[0], sessions[-1]
    history = [{**row, "seconds": seconds(row["best"]),
                "pacePerKm": round(seconds(row["best"]) / (row["repeatMeters"] / 1000), 1)} for row in RUN_HISTORY]
    return {
        "routes": ROUTES, "sessions": sessions, "history": history,
        "summary": {
            "sessions": len(sessions), "intervals": len(every), "firstDate": first["date"], "lastDate": last["date"],
            "bestInterval": {"seconds": best[0], "date": best[1]},
            "bestAverage": min((item["average"], item["date"]) for item in sessions)[0],
            "averageChange": round(last["average"] - first["average"], 2),
            "averageChangePercent": round(100 * (last["average"] - first["average"]) / first["average"], 1),
            "latestSpread": last["spread"],
            "recordedAverageMismatches": [item["date"] for item in sessions
                                          if item["averageDifference"] is not None and abs(item["averageDifference"]) >= 0.5 + 1e-9],
            "unwrittenAverages": [item["date"] for item in sessions if item["recordedAverage"] is None],
        },
    }


def parse_tempo(text: str) -> dict:
    """Tempo runs: one dated block with distance, route, total time and a written pace/speed."""
    lines = _lines(text)
    if not lines or lines[0][1] != "Tempo_Run_Log":
        raise ValueError("Tempo log must start with 'Tempo_Run_Log'.")
    runs, current = [], None
    for number, line in lines[1:]:
        if match := _TEMPO_HEAD.fullmatch(line):
            if current is not None and "writtenPace" not in current:
                raise ValueError(f"Line {number}: the previous tempo run is missing its pace line.")
            current = {"date": _iso(*match.group(1, 2, 3)), "line": number}
            runs.append(current)
        elif current is not None and (match := _TEMPO_RUN.fullmatch(line)):
            current.update(distanceKm=float(match[1]), route=match[2])
        elif current is not None and "distanceKm" in current and "timeRaw" not in current and (match := _TEMPO_TIME.fullmatch(line)):
            # 33.23.81 uses dots as separators; the value is kept as written.
            current.update(timeRaw=line, timeSeconds=round(int(match[1]) * 60 + int(match[2]) + float(f"0.{match[3]}"), 2))
        elif current is not None and (match := _TEMPO_WRITTEN.fullmatch(line)):
            current["writtenPace"] = {"raw": line, "paceSeconds": round(int(match[1]) * 60 + float(match[2]), 2),
                                      "speed": float(match[3])}
        else:
            raise ValueError(f"Line {number}: unreadable tempo entry {line!r}.")
    for run in runs:
        if "writtenPace" not in run or "timeRaw" not in run:
            raise ValueError(f"Line {run['line']}: tempo run is missing its time or pace line.")
        run["paceSeconds"] = round(run["timeSeconds"] / run["distanceKm"], 2)
        run["speed"] = round(run["distanceKm"] * 1000 / run["timeSeconds"], 2)
        run["paceDifference"] = round(run["paceSeconds"] - run["writtenPace"]["paceSeconds"], 2)
        del run["line"]
    if not runs:
        raise ValueError("The tempo log has no runs.")
    return {
        "runs": runs,
        "summary": {"runs": len(runs), "kilometres": round(sum(run["distanceKm"] for run in runs), 1),
                    "bestPace": min(run["paceSeconds"] for run in runs),
                    "firstDate": runs[0]["date"], "lastDate": runs[-1]["date"],
                    "paceMismatches": [run["date"] for run in runs if abs(run["paceDifference"]) > 1]},
    }


def parse_swimming(text: str) -> dict:
    lines = _lines(text)
    if not lines or lines[0][1] != "Swimming Log":
        raise ValueError("Swimming log must start with 'Swimming Log'.")
    sessions = []
    for number, line in lines[1:]:
        match = _SWIM.fullmatch(line)
        if not match:
            raise ValueError(f"Line {number}: unreadable swimming entry {line!r}.")
        total, unit, description = int(match[4]), match[5], match[6]
        # Freeform description: repeats (4x400) plus standalone segments (650m); the
        # segment numbers share the total's unit even when suffixed m on a yard day.
        repeats = _SWIM_REPEAT.findall(description)
        remainder = _SWIM_REPEAT.sub(" ", description)
        singles = [int(value) for value in _SWIM_SINGLE.findall(remainder)]
        covered = sum(int(count) * int(distance) for count, distance in repeats) + sum(singles)
        strokes = _STROKES.findall(description)
        if not strokes:
            raise ValueError(f"Line {number}: no strokes named in {description!r}.")
        sessions.append({"date": _iso(*match.group(1, 2, 3)), "distance": total, "unit": unit,
                         "meters": round(total * (YARD if unit == "y" else 1)),
                         "sets": sum(int(count) for count, _ in repeats) + len(singles),
                         # The total is kept as written; a disagreeing set list is flagged, not fixed.
                         "setsCover": covered, "setMismatch": covered - total if covered != total else None,
                         "orderRaw": description, "strokes": strokes})
    if not sessions:
        raise ValueError("The swimming log has no sessions.")
    weeks: dict[str, int] = {}
    running = 0
    for item in sessions:
        running += item["meters"]
        item["cumulativeMeters"] = running
        weeks[_week(item["date"])] = weeks.get(_week(item["date"]), 0) + item["meters"]
    gaps = [(date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days for a, b in zip(sessions, sessions[1:])]
    return {
        "sessions": sessions, "weeks": [{"weekOf": key, "meters": value} for key, value in weeks.items()],
        "bests": list(SWIM_BESTS),
        "summary": {"sessions": len(sessions), "meters": running, "average": round(running / len(sessions)),
                    "longest": max(item["meters"] for item in sessions), "firstDate": sessions[0]["date"],
                    "lastDate": sessions[-1]["date"], "averageGapDays": round(mean(gaps), 1) if gaps else None,
                    "yardSessions": sum(item["unit"] == "y" for item in sessions),
                    "setMismatches": [item["date"] for item in sessions if item["setMismatch"]]},
    }


def display_name(raw: str) -> str:
    for wrong, right in SPELLING:
        raw = raw.replace(wrong, right)
    return raw


def _split(raw: str) -> str:
    first = re.split(r"[^A-Za-z]+", raw.strip())[0].lower()
    if first not in SPLITS:
        raise ValueError(f"Unknown training split {raw!r}.")
    return SPLITS[first]


def _set_token(raw: str) -> dict | None:
    """One comma-separated token; None for an empty token. Excluded sets keep a reason."""
    token = raw.strip().rstrip(".")
    if not token:
        return None
    if match := _SET.fullmatch(token):
        return {"raw": token, "reps": int(match[1]), "weight": float(match[2])}
    if match := _SET_BODYWEIGHT.fullmatch(token):
        return {"raw": token, "reps": int(match[1]), "weight": 0.0}
    if match := _SET_DROP.fullmatch(token):
        # The log excludes dropsets; one written inline stays excluded from every total.
        return {"raw": token, "reps": int(match[1]), "weight": float(match[2]), "excluded": "dropset"}
    if match := _SET_WEIGHT_ONLY.fullmatch(token):
        return {"raw": token, "reps": None, "weight": float(match[1]), "excluded": "no rep count written"}
    raise ValueError(f"Unreadable set {raw!r}.")


def parse_weightlifting(text: str) -> dict:
    lines = _lines(text)
    if not lines or not lines[0][1].startswith("Weightlifting Log"):
        raise ValueError("Weightlifting log must start with 'Weightlifting Log'.")
    sessions = []
    for number, line in lines[1:]:
        if match := _LIFT_DAY.fullmatch(line):
            sessions.append({"date": _iso(*match.group(1, 2, 3)), "splitRaw": match[4],
                             "split": _split(match[4]), "exercises": []})
            continue
        match = _EXERCISE.fullmatch(line)
        if not sessions or not match:
            raise ValueError(f"Line {number}: unreadable weightlifting entry {line!r}.")
        try:
            tokens = [token for token in (_set_token(part) for part in match[2].split(",")) if token]
        except ValueError as error:
            raise ValueError(f"Line {number}: {error}") from None
        sets = [{"reps": t["reps"], "weight": t["weight"]} for t in tokens if "excluded" not in t]
        excluded = [{"raw": t["raw"], "reason": t["excluded"]} for t in tokens if "excluded" in t]
        name = display_name(match[1])
        kind = ("unrecorded" if not sets  # e.g. "Back Extensions;" with nothing after it
                else "assisted" if "assisted" in name.lower()
                else "bodyweight" if not any(s["weight"] for s in sets) else "loaded")
        item = {"nameRaw": match[1], "name": name, "kind": kind, "sets": sets, "excludedSets": excluded,
                "setCount": len(sets), "reps": sum(s["reps"] for s in sets)}
        for target in REP_TARGETS if kind in ("loaded", "assisted") else ():
            weights = [s["weight"] for s in sets if s["reps"] >= target]
            item[f"best{target}"] = ((min if kind == "assisted" else max)(weights)) if weights else None
        if kind == "loaded":
            top = max(s["weight"] for s in sets)
            item.update(topWeight=top, topReps=max(s["reps"] for s in sets if s["weight"] == top),
                        volume=round(sum(s["reps"] * s["weight"] for s in sets)),
                        e1rm=round(max(s["weight"] * (1 + s["reps"] / 30) for s in sets if s["weight"]), 1))
        elif kind == "assisted":
            least = min(s["weight"] for s in sets)
            item.update(leastAssist=least, repsAtLeastAssist=max(s["reps"] for s in sets if s["weight"] == least))
        sessions[-1]["exercises"].append(item)
    if not sessions or any(not item["exercises"] for item in sessions):
        raise ValueError("Every weightlifting day needs at least one exercise.")
    for item in sessions:
        item.update(sets=sum(e["setCount"] for e in item["exercises"]), reps=sum(e["reps"] for e in item["exercises"]),
                    volume=sum(e.get("volume", 0) for e in item["exercises"]))
    progress: dict[str, dict] = {}
    for item in sessions:
        for exercise in item["exercises"]:
            if exercise["kind"] == "unrecorded":
                continue
            entry = progress.setdefault(exercise["name"], {"name": exercise["name"], "kind": exercise["kind"], "points": []})
            if entry["kind"] != exercise["kind"]:
                entry["kind"] = "mixed"
            value = exercise.get("topWeight", exercise.get("leastAssist"))
            entry["points"].append({"date": item["date"], "value": value, "reps": exercise.get("topReps", exercise.get("repsAtLeastAssist")),
                                    "e1rm": exercise.get("e1rm"), "totalReps": exercise["reps"],
                                    **{f"best{t}": exercise.get(f"best{t}") for t in REP_TARGETS}})
    tracked = []
    for entry in progress.values():
        points = entry["points"]
        if entry["kind"] == "loaded" and len(points) > 1:
            entry["change"] = points[-1]["value"] - points[0]["value"]
        tracked.append(entry)
    return {
        "sessions": sessions, "exercises": tracked, "peaks": list(LIFT_PEAKS),
        "summary": {"sessions": len(sessions), "firstDate": sessions[0]["date"], "lastDate": sessions[-1]["date"],
                    "sets": sum(item["sets"] for item in sessions), "reps": sum(item["reps"] for item in sessions),
                    "volume": sum(item["volume"] for item in sessions), "exercises": len(tracked),
                    "excludedSets": sum(len(e["excludedSets"]) for item in sessions for e in item["exercises"]),
                    "splits": {split: sum(item["split"] == split for item in sessions) for split in ("Chest", "Back", "Shoulders")}},
    }


def load_athletics(root: Path) -> dict:
    texts = {key: (root / path).read_text(encoding="utf-8-sig") for key, path in SOURCES.items()}
    data = {"running": parse_running(texts["running"]), "tempo": parse_tempo(texts["tempo"]),
            "swimming": parse_swimming(texts["swimming"]), "weightlifting": parse_weightlifting(texts["weightlifting"])}
    for key, path in SOURCES.items():
        lines = [line for _, line in _lines(texts[key])]
        start = {"running": _RUN, "tempo": _TEMPO_HEAD, "swimming": _SWIM, "weightlifting": _LIFT_DAY}[key]
        latest = max(index for index, line in enumerate(lines) if start.fullmatch(line))
        data[key]["source"] = {"path": path, "raw": texts[key], "latestEntry": lines[latest:]}
        copy = root / EARLIER_COPIES[key]
        if copy.is_file() and copy.read_text(encoding="utf-8-sig") != texts[key]:
            raise ValueError(f"{EARLIER_COPIES[key]} differs from {path}, the file the build reads. "
                             f"Copy the edited version over {path} (or delete the older copy), then rebuild.")
    return data


def athletics_rows(data: dict) -> dict[str, list[dict]]:
    run, swim, lift = data["running"], data["swimming"], data["weightlifting"]
    return {
        "running-intervals": [{"date": s["date"], "route": s["route"], "interval": i["number"], "time": i["raw"], "seconds": i["seconds"]}
                              for s in run["sessions"] for i in s["intervals"]],
        "running-sessions": [{"date": s["date"], "route": s["route"], "intervals": s["count"], "averageSeconds": s["average"],
                              "recordedAverage": s["recordedAverage"]["raw"] if s["recordedAverage"] else None,
                              "bestSeconds": s["best"], "worstSeconds": s["worst"],
                              "spreadSeconds": s["spread"], "fadeSeconds": s["fade"], "paceSecondsPerKm": s["pacePerKm"]}
                             for s in run["sessions"]],
        "running-tempo": [{"date": r["date"], "route": r["route"], "distanceKm": r["distanceKm"], "time": r["timeRaw"],
                           "seconds": r["timeSeconds"], "paceSecondsPerKm": r["paceSeconds"], "speedMs": r["speed"],
                           "writtenPace": r["writtenPace"]["raw"]} for r in data["tempo"]["runs"]],
        "swimming-sessions": [{"date": s["date"], "distance": s["distance"], "unit": s["unit"], "meters": s["meters"],
                               "sets": s["sets"], "strokeOrder": s["orderRaw"], "cumulativeMeters": s["cumulativeMeters"]}
                              for s in swim["sessions"]],
        "weightlifting-sets": [{"date": s["date"], "split": s["splitRaw"], "exercise": e["nameRaw"], "kind": e["kind"],
                                "set": n, "reps": x["reps"], "weightLbs": x["weight"]}
                               for s in lift["sessions"] for e in s["exercises"] for n, x in enumerate(e["sets"], 1)],
        "weightlifting-sessions": [{"date": s["date"], "split": s["splitRaw"], "exercises": len(s["exercises"]), "sets": s["sets"],
                                    "reps": s["reps"], "loadedVolumeLbs": s["volume"]} for s in lift["sessions"]],
        "weightlifting-progress": [{"exercise": e["name"], "kind": e["kind"], "date": p["date"], "topSetLbs": p["value"],
                                    "repsAtTopSet": p["reps"], **{f"best{t}RepsLbs": p[f"best{t}"] for t in REP_TARGETS},
                                    "totalReps": p["totalReps"], "estimated1rmLbs": p["e1rm"]}
                                   for e in lift["exercises"] if e["kind"] in ("loaded", "assisted") for p in e["points"]],
    }
