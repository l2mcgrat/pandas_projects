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
    "swimming": "records/athletics/swimming/Swimming_Log.txt",
    "weightlifting": "records/athletics/weightlifting/Weightlifting_Log.txt",
}
# Earlier copies beside the local site preview. If one differs, the build stops rather
# than silently ignoring an edit made there.
EARLIER_COPIES = {
    "running": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics/Running/Interval_Data.txt",
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
SPELLING = (("Assited", "Assisted"), ("Dumbell", "Dumbbell"), ("Bend Over", "Bent Over"))
SPLITS = {"chest": "Chest", "back": "Back", "delts": "Shoulders", "shoulders": "Shoulders"}

_DATE = r"(\d{1,2})/(\d{1,2})/(\d{4})"
_RUN = re.compile(rf"(I\d+) - \({_DATE}\) - (\d+) Intervals?")
_TIME = re.compile(r"(\d{1,2}):([0-5]\d)")
_AVG = re.compile(r"Avg: (\d{1,2}:[0-5]\d)")
_SWIM = re.compile(rf"\({_DATE}\) - (\d+)m - (\d+)x(\d+) of (.+)")
_LIFT_DAY = re.compile(rf"{_DATE} - (.+)")
_EXERCISE = re.compile(r"([^;:]+?)\s*[;:]\s*(.+)")
_SET = re.compile(r"(\d+)x(\d+(?:\.\d+)?)lbs")


def _iso(month: str, day: str, year: str) -> str:
    return date(int(year), int(month), int(day)).isoformat()


def seconds(raw: str) -> int:
    match = _TIME.fullmatch(raw)
    if not match:
        raise ValueError(f"Unreadable time {raw!r}")
    return int(match[1]) * 60 + int(match[2])


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
    for number, line in lines[1:]:
        if match := _RUN.fullmatch(line):
            if current is not None:
                raise ValueError(f"Line {number}: previous session has no Avg line.")
            if match[1] not in ROUTES:
                raise ValueError(f"Line {number}: route {match[1]} has no recorded distance.")
            current = {"route": match[1], "date": _iso(*match.group(2, 3, 4)), "declared": int(match[5]),
                       "line": number, "intervals": []}
        elif current is not None and _TIME.fullmatch(line):
            current["intervals"].append({"number": len(current["intervals"]) + 1, "raw": line, "seconds": seconds(line)})
        elif current is not None and (match := _AVG.fullmatch(line)):
            if len(current["intervals"]) != current["declared"]:
                raise ValueError(f"Line {current['line']}: {current['declared']} intervals declared, "
                                 f"{len(current['intervals'])} listed.")
            current["recordedAverage"] = {"raw": match[1], "seconds": seconds(match[1])}
            sessions.append(current)
            current = None
        else:
            raise ValueError(f"Line {number}: unreadable running entry {line!r}.")
    if current is not None:
        raise ValueError("The last running session has no Avg line.")
    for index, item in enumerate(sessions):
        times = [interval["seconds"] for interval in item["intervals"]]
        distance = ROUTES[item["route"]]["distanceKm"]
        item.update(id=f"{item['date']}-{item['route']}-{index + 1}", count=len(times), average=round(mean(times), 2),
                    best=min(times), worst=max(times), spread=max(times) - min(times),
                    fade=times[-1] - times[0], pacePerKm=round(mean(times) / distance, 1))
        item["averageDifference"] = round(item["average"] - item["recordedAverage"]["seconds"], 2)
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
            "recordedAverageMismatches": [item["date"] for item in sessions if abs(item["averageDifference"]) >= 0.5 + 1e-9],
        },
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
        total, sets, distance = int(match[4]), int(match[5]), int(match[6])
        if sets * distance != total:
            raise ValueError(f"Line {number}: {sets} × {distance} m does not equal {total} m.")
        sessions.append({"date": _iso(*match.group(1, 2, 3)), "meters": total, "sets": sets, "setMeters": distance,
                         "orderRaw": match[7], "strokes": re.split(r"[-_]", match[7])})
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
                    "lastDate": sessions[-1]["date"], "averageGapDays": round(mean(gaps), 1) if gaps else None},
    }


def display_name(raw: str) -> str:
    for wrong, right in SPELLING:
        raw = raw.replace(wrong, right)
    return raw


def _split(raw: str) -> str:
    first = re.split(r"\s*&\s*", raw)[0].strip().lower()
    if first not in SPLITS:
        raise ValueError(f"Unknown training split {raw!r}.")
    return SPLITS[first]


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
        raw_sets = [part.strip() for part in match[2].split(",")]
        if not all(_SET.fullmatch(part) for part in raw_sets):
            raise ValueError(f"Line {number}: sets must look like 12x95lbs.")
        sets = [{"reps": int(m[1]), "weight": float(m[2])} for m in map(_SET.fullmatch, raw_sets)]
        name = display_name(match[1])
        kind = "assisted" if "assisted" in name.lower() else "bodyweight" if not any(s["weight"] for s in sets) else "loaded"
        item = {"nameRaw": match[1], "name": name, "kind": kind, "sets": sets,
                "setCount": len(sets), "reps": sum(s["reps"] for s in sets)}
        for target in REP_TARGETS if kind != "bodyweight" else ():
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
                    "splits": {split: sum(item["split"] == split for item in sessions) for split in ("Chest", "Back", "Shoulders")}},
    }


def load_athletics(root: Path) -> dict:
    texts = {key: (root / path).read_text(encoding="utf-8-sig") for key, path in SOURCES.items()}
    data = {"running": parse_running(texts["running"]), "swimming": parse_swimming(texts["swimming"]),
            "weightlifting": parse_weightlifting(texts["weightlifting"])}
    for key, path in SOURCES.items():
        lines = [line for _, line in _lines(texts[key])]
        start = {"running": _RUN, "swimming": _SWIM, "weightlifting": _LIFT_DAY}[key]
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
                              "recordedAverage": s["recordedAverage"]["raw"], "bestSeconds": s["best"], "worstSeconds": s["worst"],
                              "spreadSeconds": s["spread"], "fadeSeconds": s["fade"], "paceSecondsPerKm": s["pacePerKm"]}
                             for s in run["sessions"]],
        "swimming-sessions": [{"date": s["date"], "meters": s["meters"], "sets": s["sets"], "setMeters": s["setMeters"],
                               "strokeOrder": s["orderRaw"], "cumulativeMeters": s["cumulativeMeters"]} for s in swim["sessions"]],
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
