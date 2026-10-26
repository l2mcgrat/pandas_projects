"""Sleep/dream and diet logs in records/health; nothing is written or diagnosed.

load_health(root) -> {"sleep", "diet"}. Parsers keep every raw value and fail with a
line number on anything unreadable. Written calorie totals that disagree with the
listed numbers are flagged, never corrected. The dream reading is a playful,
lexicon-based pattern count over the owner's own journal: it is not psychoanalysis,
psychology or any statement about mental health.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from statistics import mean

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .analysis import _feelings, _read_lexicon, _words

SOURCES = {
    "sleep": "records/health/sleep/Sleep_and_Dream_Log.txt",
    "diet": "records/health/diet/Diet_and_Calorie_Tracking.txt",
}
EARLIER_COPIES = {
    "sleep": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Health/Sleep/Sleep_and_Dream_Log.txt",
    "diet": "LiamMs_PandasProjects/Gaming-and-Performance-Log/Health/Diet/Diet_and_Calorie_Tracking.txt",
}
# Owner-stated context for October 2026, shown beside the charts, not inferred.
OCTOBER_BMR = 2050
HIGH_NEAT_NOTE = ("Expenditure is the owner's daily estimate built on a BMR set to "
                  f"{OCTOBER_BMR} kcal for October plus activity; non-exercise activity "
                  "(NEAT) runs high, so most days sit well above the BMR.")
DAILY_TARGET_DEFICIT = 500  # the conventional ~1 lb/week cut; an owner-chosen reference line
CALORIES_PER_POUND = 3500

# A playful motif lexicon for the dream journal. Multiword cues match consecutive
# word forms. The notes are folklore-style readings, labelled as such on the page.
MOTIFS = (
    ("Exploration & other worlds",
     ("moon", "island", "map", "dimension", "world", "worlds", "portal", "portals", "travel",
      "travelled", "trip", "expedition", "exp dition", "desert", "climates", "areas", "continents"),
     "Maps, portals and unexplored terrain: the classic reading is a mind busy with ambitions and options not yet taken."),
    ("Water, ice & winter",
     ("water", "beach", "ice", "icy", "winter", "boat", "chilly"),
     "Dream folklore treats water as emotion and ice as emotion put on hold; this journal keeps returning to both."),
    ("Pursuit, escape & danger",
     ("chased", "escape", "break out", "breakout", "breat out", "breakcout", "demon", "creepy",
      "creepier", "dangerous", "treatourous", "torture", "sketchy", "cult", "punishment"),
     "Being chased or breaking out is the textbook avoidance motif: something is being outrun rather than faced."),
    ("Parties & social scenes",
     ("party", "partying", "parties", "vibing", "drink", "strangers", "fest", "penthouse",
      "bonds", "friends", "friend"),
     "Crowded rooms and shifting social standing: dreams rehearsing belonging, status and who is worth the effort."),
    ("Competition & school",
     ("school", "grades", "compete", "hs", "cohort", "hockey", "athletic", "runs", "running",
      "survivor", "show", "game", "games"),
     "Contests, grades and shows: evaluation dreams, the mind re-running old scoreboards (and inventing new ones)."),
    ("Work & purpose",
     ("working", "analytics", "justify", "justifying", "duty", "team", "purpose", "website",
      "legal", "info"),
     "Even asleep, the analyst justifies the analytics. Work bleeding into dreams usually tracks waking preoccupation."),
    ("Games, media & famous faces",
     ("pokemon", "mario", "videos", "geography", "elites", "secret"),
     "Media consumed near bedtime shows up nearly verbatim; the journal even hypothesizes this itself on Oct 18."),
)

_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_NIGHT = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_HOURS = re.compile(r"(\d+(?:\.\d+)?)hrs")
_NO_DREAMS = re.compile(r"No dreams recorded\.?", re.IGNORECASE)
_DIET_DAY = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})(?: - (\d+) ?cals? (loss|gain))?")
_MEAL = re.compile(r"(Breakfast|Lunch|Dinner|Snacks) ?- ?(.+)")
_EXPENDITURE = re.compile(r"Total Expenditure - (\d+) ?cals?(?: \((.+)\))?")
_CONSUMPTION = re.compile(r"Total Consumption - (.+)")
_NET = re.compile(r"Net Expenditure - (\d+) ?cals? (loss|gain)")
_RULE = re.compile(r"-{5,}")
_WEEK = re.compile(r"Week of (\d{1,2})/(\d{1,2})/(\d{4}) --> (\d+) ?cals? loss or ~(\d+(?:\.\d+)?) ?lbs")
_CALS = re.compile(r"(\d+) ?cals?\b")
_MACROS = re.compile(r"(\d+)/(\d+)/(\d+) ?g?\b")


def _iso(month: str, day: str, year: str) -> str:
    return date(int(year), int(month), int(day)).isoformat()


def _lines(text: str) -> list[tuple[int, str]]:
    return [(number, line.strip()) for number, line in enumerate(text.splitlines(), 1) if line.strip()]


def _motifs(tokens: list[str]) -> list[dict]:
    found = []
    for name, cues, note in MOTIFS:
        hits = []
        for cue in cues:
            parts = tuple(word.word for word in _words(cue))
            hits += [" ".join(parts)] * sum(
                tuple(tokens[i:i + len(parts)]) == parts for i in range(len(tokens) - len(parts) + 1))
        if hits:
            found.append({"motif": name, "count": len(hits), "cues": sorted(set(hits)), "note": note})
    return found


def parse_sleep(text: str) -> dict:
    lines = _lines(text)
    if not lines or lines[0][1] != "Sleep_and_Dream_Log":
        raise ValueError("Sleep log must start with 'Sleep_and_Dream_Log'.")
    nights: list[dict] = []
    for number, line in lines[1:]:
        if match := _NIGHT.fullmatch(line):
            nights.append({"date": _iso(*match.groups()), "hours": None, "dreams": [], "line": number})
        elif not nights:
            raise ValueError(f"Line {number}: expected a date before {line!r}.")
        elif nights[-1]["hours"] is None:
            if not (match := _HOURS.fullmatch(line)):
                raise ValueError(f"Line {number}: expected a duration like 7hrs, got {line!r}.")
            nights[-1]["hours"] = float(match[1])
        elif _NO_DREAMS.fullmatch(line):
            nights[-1]["noDreamsWritten"] = True
        else:
            nights[-1]["dreams"].append(line)
    emotions, lexicon = _read_lexicon()
    polarity = SentimentIntensityAnalyzer()
    for night in nights:
        if night["hours"] is None:
            raise ValueError(f"Line {night['line']}: the night has no duration.")
        del night["line"]
        night["recall"] = bool(night["dreams"])
        dreams = []
        for index, text_ in enumerate(night["dreams"], 1):
            spans = _words(text_)
            tokens = [word.word for word in spans]
            feelings = _feelings(spans, text_, text_, emotions, lexicon)
            dreams.append({
                "number": index, "text": text_, "tokenCount": len(tokens),
                "emotion": feelings["emotion"], "subemotion": feelings["subemotion"],
                "emotionScores": feelings["emotionScores"], "ambiguous": feelings["ambiguous"],
                "evidence": [{key: item[key] for key in ("family", "label", "cue", "text", "negated")}
                             for item in feelings["evidence"]],
                "polarity": polarity.polarity_scores(text_), "motifs": _motifs(tokens),
            })
        night["dreams"] = dreams
    if not nights:
        raise ValueError("The sleep log has no nights.")
    with_dreams = [night for night in nights if night["recall"]]
    without = [night for night in nights if not night["recall"]]
    motif_totals: dict[str, dict] = {}
    for night in nights:
        for dream in night["dreams"]:
            for found in dream["motifs"]:
                entry = motif_totals.setdefault(found["motif"], {"motif": found["motif"], "note": found["note"],
                                                                 "count": 0, "nights": set(), "cues": set()})
                entry["count"] += found["count"]
                entry["nights"].add(night["date"])
                entry["cues"] |= set(found["cues"])
    motifs = [{**entry, "nights": sorted(entry["nights"]), "cues": sorted(entry["cues"])}
              for entry in sorted(motif_totals.values(), key=lambda e: (-e["count"], e["motif"]))]
    return {
        "nights": nights, "motifs": motifs,
        "summary": {
            "nights": len(nights), "firstDate": nights[0]["date"], "lastDate": nights[-1]["date"],
            "averageHours": round(mean(night["hours"] for night in nights), 2),
            "longest": max(night["hours"] for night in nights), "shortest": min(night["hours"] for night in nights),
            "dreams": sum(len(night["dreams"]) for night in nights),
            "nightsWithDreams": len(with_dreams),
            "averageHoursWithDreams": round(mean(n["hours"] for n in with_dreams), 2) if with_dreams else None,
            "averageHoursWithout": round(mean(n["hours"] for n in without), 2) if without else None,
        },
    }


def parse_diet(text: str) -> dict:
    lines = _lines(text)
    if not lines or lines[0][1] != "Diet and Calorie Tracking":
        raise ValueError("Diet log must start with 'Diet and Calorie Tracking'.")
    days: list[dict] = []
    weeks: list[dict] = []
    for number, line in lines[1:]:
        if _RULE.fullmatch(line):
            continue
        if match := _WEEK.fullmatch(line):
            weeks.append({"weekOf": _iso(*match.group(1, 2, 3)), "writtenLoss": int(match[4]),
                          "writtenPounds": float(match[5])})
        elif match := _DIET_DAY.fullmatch(line):
            headline = None
            if match[4]:
                headline = int(match[4]) * (1 if match[5] == "loss" else -1)
            days.append({"date": _iso(*match.group(1, 2, 3)), "headline": headline,
                         "meals": [], "line": number})
        elif not days:
            raise ValueError(f"Line {number}: expected a date before {line!r}.")
        elif match := _MEAL.fullmatch(line):
            raw = match[2].strip()
            macros = [(int(a), int(b), int(c)) for a, b, c in _MACROS.findall(raw)]
            days[-1]["meals"].append({"meal": match[1], "raw": raw,
                                      "carbs": sum(m[0] for m in macros) or None,
                                      "fat": sum(m[1] for m in macros) or None,
                                      "protein": sum(m[2] for m in macros) or None})
        elif match := _EXPENDITURE.fullmatch(line):
            days[-1]["expenditure"] = int(match[1])
            days[-1]["expenditureNote"] = match[2]
        elif match := _CONSUMPTION.fullmatch(line):
            cals = _CALS.search(match[1])
            if not cals:
                raise ValueError(f"Line {number}: no calorie total in {line!r}.")
            macros = _MACROS.search(_CALS.sub(" ", match[1]))
            days[-1]["consumption"] = int(cals[1])
            days[-1]["macros"] = ({"carbs": int(macros[1]), "fat": int(macros[2]), "protein": int(macros[3])}
                                  if macros else None)
        elif match := _NET.fullmatch(line):
            days[-1]["writtenNet"] = int(match[1]) * (1 if match[2] == "loss" else -1)
        else:
            raise ValueError(f"Line {number}: unreadable diet entry {line!r}.")
    if not days:
        raise ValueError("The diet log has no days.")
    for day_ in days:
        for field in ("expenditure", "consumption"):
            if field not in day_:
                raise ValueError(f"Line {day_['line']}: {day_['date']} has no Total {field.capitalize()} line.")
        del day_["line"]
        day_.setdefault("writtenNet", None)
        day_["deficit"] = day_["expenditure"] - day_["consumption"]  # positive = loss
        day_["activity"] = day_["expenditure"] - OCTOBER_BMR
        day_["netMismatch"] = (day_["writtenNet"] is not None and abs(day_["writtenNet"] - day_["deficit"]) > 10)
        day_["headlineMismatch"] = (day_["headline"] is not None and abs(day_["headline"] - day_["deficit"]) > 10)
        day_["mealMacros"] = {
            "carbs": sum(m["carbs"] or 0 for m in day_["meals"]),
            "fat": sum(m["fat"] or 0 for m in day_["meals"]),
            "protein": sum(m["protein"] or 0 for m in day_["meals"]),
        }
    total = sum(day_["deficit"] for day_ in days)
    for week in weeks:
        start = date.fromisoformat(week["weekOf"])
        inside = [day_ for day_ in days if 0 <= (date.fromisoformat(day_["date"]) - start).days < 7]
        week["computedLoss"] = sum(day_["deficit"] for day_ in inside)
        week["days"] = len(inside)
    return {
        "days": days, "weeks": weeks,
        "summary": {
            "days": len(days), "firstDate": days[0]["date"], "lastDate": days[-1]["date"],
            "averageExpenditure": round(mean(day_["expenditure"] for day_ in days)),
            "averageConsumption": round(mean(day_["consumption"] for day_ in days)),
            "averageDeficit": round(mean(day_["deficit"] for day_ in days)),
            "totalDeficit": total, "estimatedPounds": round(total / CALORIES_PER_POUND, 2),
            "daysOnTarget": sum(day_["deficit"] >= DAILY_TARGET_DEFICIT for day_ in days),
            "netMismatches": [day_["date"] for day_ in days if day_["netMismatch"]],
            "headlineMismatches": [day_["date"] for day_ in days if day_["headlineMismatch"]],
            "bmr": OCTOBER_BMR, "targetDeficit": DAILY_TARGET_DEFICIT,
        },
    }


def load_health(root: Path) -> dict:
    texts = {key: (root / path).read_text(encoding="utf-8-sig") for key, path in SOURCES.items()}
    data = {"sleep": parse_sleep(texts["sleep"]), "diet": parse_diet(texts["diet"])}
    for key, path in SOURCES.items():
        lines = [line for _, line in _lines(texts[key])]
        start = _NIGHT if key == "sleep" else _DIET_DAY
        latest = max(index for index, line in enumerate(lines) if start.fullmatch(line))
        data[key]["source"] = {"path": path, "raw": texts[key], "latestEntry": lines[latest:]}
        copy = root / EARLIER_COPIES[key]
        if copy.is_file() and copy.read_text(encoding="utf-8-sig") != texts[key]:
            raise ValueError(f"{EARLIER_COPIES[key]} differs from {path}, the file the build reads. "
                             f"Copy the edited version over {path} (or delete the older copy), then rebuild.")
    return data


def health_rows(data: dict) -> dict[str, list[dict]]:
    sleep, diet = data["sleep"], data["diet"]
    return {
        "sleep-nights": [{"date": n["date"], "hours": n["hours"], "dreams": len(n["dreams"]),
                          "recall": n["recall"]} for n in sleep["nights"]],
        "sleep-dreams": [{"date": n["date"], "dream": d["number"], "text": d["text"], "tokens": d["tokenCount"],
                          "emotion": d["emotion"], "subemotion": d["subemotion"], "ambiguous": d["ambiguous"],
                          "compound": d["polarity"]["compound"],
                          "motifs": "; ".join(m["motif"] for m in d["motifs"])}
                         for n in sleep["nights"] for d in n["dreams"]],
        "diet-days": [{"date": d["date"], "expenditureCal": d["expenditure"], "consumptionCal": d["consumption"],
                       "deficitCal": d["deficit"], "writtenNetCal": d["writtenNet"], "headlineCal": d["headline"],
                       "activityAboveBmrCal": d["activity"], "carbsG": d["mealMacros"]["carbs"],
                       "fatG": d["mealMacros"]["fat"], "proteinG": d["mealMacros"]["protein"],
                       "note": d["expenditureNote"]} for d in diet["days"]],
        "diet-meals": [{"date": d["date"], "meal": m["meal"], "asWritten": m["raw"], "carbsG": m["carbs"],
                        "fatG": m["fat"], "proteinG": m["protein"]} for d in diet["days"] for m in d["meals"]],
    }
