"""Hybrid Gaming & Performance log sync: strict parse first, deterministic repair second, single-line LLM fallback third.

Run ``python -B -m site_content.log_sync`` to pull updated logs from a Google Drive
folder (``--drive-dir`` or ``LIAM_LOGS_DIR`` or a mounted ``G:\\My Drive\\Logs``) or from
``LiamMs_PandasProjects/Gaming-and-Performance-Log``, repair common paste slips without
spending tokens, optionally repair a stubborn line via Gemini API (``--llm-repair``),
and write identical validated copies to both ``records/`` and ``LiamMs_PandasProjects/``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Callable
from urllib import request as urllib_request

from .athletics import (
    EARLIER_COPIES as ATHLETICS_COPIES,
    SOURCES as ATHLETICS_SOURCES,
    parse_running,
    parse_swimming,
    parse_tempo,
    parse_weightlifting,
)
from .health import (
    EARLIER_COPIES as HEALTH_COPIES,
    SOURCES as HEALTH_SOURCES,
    parse_diet,
    parse_sleep,
)


@dataclass(frozen=True)
class LogSpec:
    key: str
    filename: str
    records_path: str
    preview_path: str
    header: str
    grammar_hint: str
    parser: Callable[[str], dict]


SPECS: dict[str, LogSpec] = {
    "running": LogSpec(
        "running", "Interval_Data.txt", ATHLETICS_SOURCES["running"], ATHLETICS_COPIES["running"],
        "Interval Training Data",
        "Header 'Interval Training Data'; session header 'I1 - (M/D/YYYY) - N Intervals'; interval lines 'M:SS' or 'M:SS.d'; optional 'Avg: M:SS'.",
        parse_running,
    ),
    "tempo": LogSpec(
        "tempo", "Tempo_Run_Log.txt", ATHLETICS_SOURCES["tempo"], ATHLETICS_COPIES["tempo"],
        "Tempo_Run_Log",
        "Header 'Tempo_Run_Log'; blocks of '(M/D/YYYY)', 'Tempo Run - X.Xkm (Route)', 'MM:SS.dd', 'M:SS.d min/km - X.XXm/s'.",
        parse_tempo,
    ),
    "swimming": LogSpec(
        "swimming", "Swimming_Log.txt", ATHLETICS_SOURCES["swimming"], ATHLETICS_COPIES["swimming"],
        "Swimming Log",
        "Header 'Swimming Log'; lines '(M/D/YYYY) - 2000m - 5x400 of Fly-Back_Breast-Free' (unit m or y).",
        parse_swimming,
    ),
    "weightlifting": LogSpec(
        "weightlifting", "Weightlifting_Log.txt", ATHLETICS_SOURCES["weightlifting"], ATHLETICS_COPIES["weightlifting"],
        "Weightlifting Log (Dropsets Excluded)",
        "Header 'Weightlifting Log (Dropsets Excluded)'; day 'M/D/YYYY - Split'; exercises 'Name; 12x95lbs, 10x115lbs'.",
        parse_weightlifting,
    ),
    "sleep": LogSpec(
        "sleep", "Sleep_and_Dream_Log.txt", HEALTH_SOURCES["sleep"], HEALTH_COPIES["sleep"],
        "Sleep_and_Dream_Log",
        "Header 'Sleep_and_Dream_Log'; date 'M/D/YYYY'; duration '7.5hrs'; dream paragraphs or 'No dreams recorded'.",
        parse_sleep,
    ),
    "diet": LogSpec(
        "diet", "Diet_and_Calorie_Tracking.txt", HEALTH_SOURCES["diet"], HEALTH_COPIES["diet"],
        "Diet and Calorie Tracking",
        "Header 'Diet and Calorie Tracking'; date 'M/D/YYYY'; meals 'Breakfast - 30/10/25g Food'; 'Total Expenditure - 3400cals'; 'Total Consumption - 2800cals - 300/100/150g'; 'Net Expenditure - 600cal loss'.",
        parse_diet,
    ),
}

_DASHES = str.maketrans({"–": "-", "—": "-", "−": "-"})
_MERGED_YEAR = re.compile(r"\b(\d{1,2})/(\d{1,2})0(20\d{2})\b")
_DOT_DATE = re.compile(r"^(\(?)\s*(\d{1,2})[/.\-](\d{1,2})[/.\-](20\d{2})(\)?)(.*)$")
_LINE_ERROR = re.compile(r"Line (\d+):")
_GDOC_ID = re.compile(r"(?:/document/d/|^)([A-Za-z0-9_-]{20,})")
GDOC_MAP_PATH = "records/workbench/gdoc_sources.json"


def extract_gdoc_id(raw: str) -> str | None:
    """Extract a Google Doc ID from a share URL, a raw ID, or a .gdoc JSON shortcut file."""
    text = raw.strip()
    if text.startswith("{"):
        try:
            payload = json.loads(text)
            for field in ("doc_id", "resource_id", "url"):
                val = str(payload.get(field, "")).strip()
                if val:
                    val = val.split(":")[-1] if field == "resource_id" and ":" in val else val
                    if m := _GDOC_ID.search(val):
                        return m[1]
        except json.JSONDecodeError:
            pass
    match = _GDOC_ID.search(text)
    return match[1] if match else None


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    shift = 0
    res = 0
    while pos < len(buf):
        b = buf[pos]
        pos += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res, pos


def _snappy_decompress(data: bytes) -> bytes:
    ulen, pos = _read_varint(data, 0)
    n = len(data)
    out = bytearray()
    while pos < n and len(out) < ulen:
        tag = data[pos]
        pos += 1
        ttype = tag & 0x03
        if ttype == 0:
            length = (tag >> 2) + 1
            if length > 60:
                extra = length - 60
                length = int.from_bytes(data[pos : pos + extra], "little") + 1
                pos += extra
            out.extend(data[pos : pos + length])
            pos += length
        else:
            if ttype == 1:
                length = ((tag >> 2) & 0x07) + 4
                offset = ((tag & 0xE0) << 3) | data[pos]
                pos += 1
            elif ttype == 2:
                length = (tag >> 2) + 1
                offset = int.from_bytes(data[pos : pos + 2], "little")
                pos += 2
            else:
                length = (tag >> 2) + 1
                offset = int.from_bytes(data[pos : pos + 4], "little")
                pos += 4
            if offset <= 0 or offset > len(out):
                break
            for _ in range(length):
                out.append(out[-offset])
    return bytes(out)


def _extract_gdoc_from_local_indexeddb(doc_id: str) -> str | None:
    """Fallback when a Google Doc is still set to 'Restricted' (HTTP 401): read its V8 Kix text from local Chrome/Edge IndexedDB."""
    target = doc_id.encode("ascii")
    home = Path.home()
    candidate_dirs = [
        home / "AppData/Local/Google/Chrome/User Data/Default/IndexedDB/https_docs.google.com_0.indexeddb.leveldb",
        home / "AppData/Local/Microsoft/Edge/User Data/Default/IndexedDB/https_docs.google.com_0.indexeddb.leveldb",
    ]
    segments: dict[int, str] = {}
    for docs_dir in candidate_dirs:
        if not docs_dir.is_dir():
            continue
        for ldb_path in sorted(docs_dir.glob("*.ldb")):
            try:
                raw = ldb_path.read_bytes()
                if len(raw) < 48:
                    continue
                footer = raw[-48:]
                _, pos = _read_varint(footer, 0)
                _, pos = _read_varint(footer, pos)
                idx_off, pos = _read_varint(footer, pos)
                idx_size, pos = _read_varint(footer, pos)
                idx_raw = raw[idx_off : idx_off + idx_size]
                idx_block = _snappy_decompress(idx_raw) if raw[idx_off + idx_size] == 1 else idx_raw
                num_restarts = int.from_bytes(idx_block[-4:], "little")
                limit = len(idx_block) - 4 * (num_restarts + 1)
                p_idx = 0
                blocks = []
                while p_idx < limit:
                    _, p_idx = _read_varint(idx_block, p_idx)
                    nsh, p_idx = _read_varint(idx_block, p_idx)
                    vlen, p_idx = _read_varint(idx_block, p_idx)
                    p_idx += nsh
                    val = idx_block[p_idx : p_idx + vlen]
                    p_idx += vlen
                    b_off, vp = _read_varint(val, 0)
                    b_sz, vp = _read_varint(val, vp)
                    blocks.append((b_off, b_sz))
                for b_off, b_sz in blocks:
                    b_raw = raw[b_off : b_off + b_sz]
                    b_data = _snappy_decompress(b_raw) if raw[b_off + b_sz] == 1 else b_raw
                    n_rest = int.from_bytes(b_data[-4:], "little")
                    b_lim = len(b_data) - 4 * (n_rest + 1)
                    bp = 0
                    while bp < b_lim:
                        _, bp = _read_varint(b_data, bp)
                        nsh, bp = _read_varint(b_data, bp)
                        vlen, bp = _read_varint(b_data, bp)
                        bp += nsh
                        val = b_data[bp : bp + vlen]
                        bp += vlen
                        if target in val and b"ibiI" in val:
                            search_pos = 0
                            while True:
                                idx = val.find(b"ibiI", search_pos)
                                if idx == -1:
                                    break
                                ibi_val, p2 = _read_varint(val, idx + 4)
                                if val[p2 : p2 + 3] == b'"\x01s':
                                    p2 += 3
                                    stag = val[p2]
                                    p2 += 1
                                    slen, p2 = _read_varint(val, p2)
                                    sbytes = val[p2 : p2 + slen]
                                    text_seg = (
                                        sbytes.decode("utf-16le", errors="ignore")
                                        if stag == 0x63
                                        else sbytes.decode("latin1", errors="ignore")
                                    )
                                    segments[ibi_val] = text_seg
                                search_pos = idx + 4
            except Exception:
                continue
    if segments:
        return "".join(segments[k] for k in sorted(segments))
    return None


def fetch_gdoc_text(doc_id_or_url: str) -> str:
    """Download a Google Doc as UTF-8 plain text via /export?format=txt, falling back to local Chrome IndexedDB if Restricted."""
    doc_id = extract_gdoc_id(doc_id_or_url)
    if not doc_id:
        raise ValueError(f"Could not extract a Google Doc ID from {doc_id_or_url!r}")
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    req = urllib_request.Request(url, headers={"User-Agent": "LiamPortfolioLogSync/1.0"})
    try:
        with urllib_request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8-sig")
    except Exception:
        cached = _extract_gdoc_from_local_indexeddb(doc_id)
        if cached:
            return cached
        raise


def load_gdoc_map(root: Path) -> dict[str, str]:
    path = root / GDOC_MAP_PATH
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: str(v) for k, v in data.items() if k in SPECS and v}


def save_gdoc_link(root: Path, key: str, url_or_id: str) -> str:
    if key not in SPECS:
        raise ValueError(f"Unknown log key {key!r}; choose from {', '.join(SPECS)}")
    doc_id = extract_gdoc_id(url_or_id)
    if not doc_id:
        raise ValueError(f"Invalid Google Docs URL or ID: {url_or_id!r}")
    path = root / GDOC_MAP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    current = load_gdoc_map(root)
    current[key] = doc_id
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return doc_id


def default_drive_dirs() -> list[Path]:
    """Candidate local Google Drive / OneDrive 'Logs' folders on Windows."""
    candidates: list[Path] = []
    env = os.environ.get("LIAM_LOGS_DIR")
    if env:
        candidates.append(Path(env))
    home = Path.home()
    for root in (Path("G:/My Drive"), Path("G:/"), home / "Google Drive" / "My Drive", home / "Google Drive", home / "OneDrive"):
        candidates.append(root / "Logs")
    return [path for path in candidates if path.is_dir()]


def _repair_line(key: str, line: str, prev_nonempty: str) -> str:
    fixed = re.sub(r"[\u200b\u200c\u200d\ufeff\xa0]", " ", line).translate(_DASHES).strip()
    if not fixed:
        return ""
    if re.fullmatch(r"-{5,}", fixed):
        return "-" * 50
    fixed = _MERGED_YEAR.sub(r"\1/\2/\3", fixed)
    if match := _DOT_DATE.fullmatch(fixed):
        fixed = f"{match[1]}{match[2]}/{match[3]}/{match[4]}{match[5]}{match[6]}"

    if key == "running":
        if m := re.fullmatch(r"[iI](\d+)\s*-\s*\(?(\d{1,2}/\d{1,2}/\d{4})\)?\s*-\s*(\d+)\s*[iI]ntervals?", fixed):
            return f"I{m[1]} - ({m[2]}) - {m[3]} Intervals"
        if m := re.fullmatch(r"\(?(\d{1,2}/\d{1,2}/\d{4})\)?\s*(?:-\s*)?(\d+)\s*[iI]ntervals?", fixed):
            return f"I1 - ({m[1]}) - {m[2]} Intervals"
        if m := re.fullmatch(r"(\d{1,2})\.([0-5]\d(?:\.\d+)?)", fixed):
            return f"{m[1]}:{m[2]}"
        if m := re.fullmatch(r"(?:[aA]vg|[aA]verage)\s*:?\s*(\d{1,2})[:.]([0-5]\d(?:\.\d+)?)", fixed):
            return f"Avg: {m[1]}:{m[2]}"
    elif key == "tempo":
        if m := re.fullmatch(r"(\d{1,2}/\d{1,2}/\d{4})", fixed):
            return f"({m[1]})"
        if m := re.fullmatch(r"[tT]empo\s+[rR]un\s*[-:]\s*(\d+(?:\.\d+)?)\s*km\s*(?:\((.+)\)|-\s*(.+))", fixed):
            return f"Tempo Run - {m[1]}km ({(m[2] or m[3]).strip()})"
        if m := re.fullmatch(r"(\d{1,2}):([0-5]\d(?:\.\d+)?)\s*min/km\s*[-:]\s*(\d+(?:\.\d+)?)\s*m/s", fixed, re.I):
            return f"{m[1]}:{m[2]} min/km - {m[3]}m/s"
    elif key == "swimming":
        if m := re.fullmatch(r"\(?(\d{1,2}/\d{1,2}/\d{4})\)?\s*[-:]?\s*(\d+)\s*(m|y|yd|yds|yards?|meters?|metres?)\s*[-:]\s*(.+)", fixed, re.I):
            unit = "y" if m[3].lower().startswith("y") else "m"
            return f"({m[1]}) - {m[2]}{unit} - {m[4].strip()}"
    elif key == "weightlifting":
        if m_day := re.match(r"^(\d{1,2}/\d{1,2}/20\d{2})\s*(?:[-:]\s*)?([A-Za-z].*)$", fixed):
            split_txt = re.sub(r"\bTries\b", "Tris", m_day[2].strip())
            return f"{m_day[1]} - {split_txt}"
        m_ex = re.match(r"^([A-Za-z][A-Za-z0-9\s'()/&]*?)\s*(?:([;:])\s*|[-,]\s*|\s+)(?=\d+\s*[xX*]|\s*$)(.*)$", fixed)
        if m_ex:
            head = m_ex[1].strip()
            sep = m_ex[2] or ";"
            rest = m_ex[3].strip()
            parts = []
            for token in rest.split(","):
                tok = token.strip().rstrip(".")
                if not tok:
                    continue
                if m := re.fullmatch(r"(\d+)\s*[xX*]\s*(\d+(?:\.\d+)?)\s*(?:lbs?|lb)?", tok, re.I):
                    parts.append(f"{m[1]}x{m[2]}lbs")
                elif m := re.fullmatch(r"(\d+)\s*[xX*]\s*(?:bw|bodyweight)", tok, re.I):
                    parts.append(f"{m[1]}xBodyweight")
                else:
                    parts.append(tok)
            return f"{head}{sep} {', '.join(parts)}" if parts else f"{head}{sep}"
    elif key == "sleep":
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", prev_nonempty):
            if m := re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:hrs?|hours?|h)?", fixed, re.I):
                return f"{m[1]}hrs"
    elif key == "diet":
        if m := re.fullmatch(r"(Breakfast|Lunch|Dinner|Snacks)\s*[:\-]\s*(.+)", fixed, re.I):
            return f"{m[1].capitalize()} - {m[2].strip()}"
        if m := re.fullmatch(r"Total Expenditure\s*[:\-]\s*(\d+)\s*(?:k?cals?)?(?:\s*\((.+)\))?", fixed, re.I):
            return f"Total Expenditure - {m[1]}cals" + (f" ({m[2]})" if m[2] else "")
        if m := re.fullmatch(r"Total Consumption\s*[:\-]\s*(.+)", fixed, re.I):
            body = re.sub(r"(\d+)\s*k?cals?\b", r"\1cals", m[1].strip(), flags=re.I)
            return f"Total Consumption - {body}"
        if m := re.fullmatch(r"Net Expenditure\s*[:\-]\s*([+-]?\d+)\s*(?:k?cals?)?\s*(loss|gain)?", fixed, re.I):
            raw_val = int(m[1])
            direction = (m[2] or ("gain" if raw_val < 0 else "loss")).lower()
            return f"Net Expenditure - {abs(raw_val)}cal {direction}"
    return fixed


def repair_log_text(key: str, text: str) -> tuple[str, list[dict]]:
    """Apply zero-token deterministic repairs and return (repaired_text, changes)."""
    spec = SPECS[key]
    raw_lines = [re.sub(r"[\u200b\u200c\u200d\ufeff\xa0]", " ", ln) for ln in text.replace("\r\n", "\n").splitlines()]
    changes: list[dict] = []

    first_idx = next((i for i, ln in enumerate(raw_lines) if ln.strip()), None)
    if first_idx is None:
        return text, changes
    first = raw_lines[first_idx].strip()
    alt_headers = {
        "weightlifting": r"(?:Weight)?[lL]ifting\s+[lL]og.*",
        "swimming": r"Swimming(?:\s+Tempo)?\s+Log.*",
        "sleep": r"Sleep(?:_and_Dream)?[\s_]+Log.*",
        "diet": r"(?:Food\s+Log|Diet\s+and\s+Calorie\s+Tracking).*",
        "running": r"(?:Running\s+)?Interval\s+Training.*",
        "tempo": r"Tempo[\s_]+Run[\s_]+Log.*",
    }
    if first != spec.header and not (key == "weightlifting" and first.startswith("Weightlifting Log")):
        if key in alt_headers and re.fullmatch(alt_headers[key], first, re.I):
            raw_lines[first_idx] = spec.header
            changes.append({"line": first_idx + 1, "before": first, "after": spec.header, "method": "rule-header"})
        else:
            raw_lines.insert(first_idx, spec.header)
            changes.append({"line": first_idx + 1, "before": "", "after": spec.header, "method": "rule-header"})

    _MONTH_BANNER = re.compile(
        r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}$",
        re.I,
    )
    out: list[str] = []
    prev_nonempty = ""
    last_year = 0
    last_sleep_hrs = "6hrs"
    for number, line in enumerate(raw_lines, 1):
        s_line = line.strip()
        if not s_line:
            out.append("")
            continue
        if _MONTH_BANNER.fullmatch(s_line) or (key == "running" and re.fullmatch(r"1KM\s+Interval\s+Training.*", s_line, re.I)):
            changes.append({"line": number, "before": s_line, "after": "", "method": "rule-month-heading"})
            continue
        if number == 1 or (prev_nonempty == "" and s_line == spec.header):
            out.append(s_line)
            prev_nonempty = s_line
            continue
        if key == "diet":
            if m_combo := re.fullmatch(r"(Breakfast|Lunch|Dinner|Snacks)\s*[/&]\s*(Breakfast|Lunch|Dinner|Snacks)\s*[:\-]\s*(.+)", s_line, re.I):
                l1 = f"{m_combo[1].capitalize()} - {m_combo[3].strip()}"
                l2 = f"{m_combo[2].capitalize()} - {m_combo[3].strip()}"
                changes.append({"line": number, "before": s_line, "after": f"{l1} / {l2}", "method": "rule-split-meal"})
                out.extend([l1, l2])
                prev_nonempty = l2
                continue
        repaired = _repair_line(key, line, prev_nonempty)
        if m_yr := re.match(r"^(\(?(\d{1,2})/(\d{1,2})/)(20\d{2})(\)?(?:\s*-\s*.+)?)$", repaired):
            yr = int(m_yr[4])
            if last_year and yr < last_year:
                repaired = f"{m_yr[1]}{last_year}{m_yr[5]}"
            else:
                last_year = yr
        if key == "sleep":
            if re.fullmatch(r"\d+(?:\.\d+)?hrs", repaired, re.I):
                last_sleep_hrs = repaired
            elif re.fullmatch(r"\d{1,2}/\d{1,2}/20\d{2}", prev_nonempty):
                out.append(last_sleep_hrs)
                changes.append({"line": number, "before": "", "after": last_sleep_hrs, "method": "rule-default-hours"})
        if repaired != s_line:
            changes.append({"line": number, "before": s_line, "after": repaired, "method": "rule"})
        out.append(repaired)
        prev_nonempty = repaired
    if key == "sleep" and re.fullmatch(r"\d{1,2}/\d{1,2}/20\d{2}", prev_nonempty):
        out.extend([last_sleep_hrs, "No dreams recorded"])
        changes.append({"line": len(raw_lines), "before": "", "after": last_sleep_hrs, "method": "rule-default-hours"})
    return "\n".join(out) + "\n", changes


def gemini_repair_line(key: str, broken_line: str, error_msg: str, api_key: str | None = None) -> str:
    """Repair a single malformed log line via Gemini API (sends <80 tokens)."""
    token = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not token:
        raise RuntimeError("No GEMINI_API_KEY/GOOGLE_API_KEY set for --llm-repair fallback.")
    spec = SPECS[key]
    prompt = (
        f"Fix this single line from {spec.filename} so it matches the grammar: {spec.grammar_hint}\n"
        f"Parser error: {error_msg}\n"
        f"Broken line: {broken_line}\n"
        "Reply with ONLY the corrected single line, no quotes or explanation."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={token}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}}).encode("utf-8")
    req = urllib_request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib_request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    candidate = body["candidates"][0]["content"]["parts"][0]["text"].strip().splitlines()[0].strip("`\"'")
    return candidate


def validate_or_repair(
    key: str,
    text: str,
    *,
    llm_fixer: Callable[[str, str, str], str] | None = None,
    max_llm_lines: int = 5,
) -> tuple[str, dict, list[dict]]:
    """Run strict parse -> deterministic repair -> optional single-line LLM repair."""
    spec = SPECS[key]
    clean = text.replace("\r\n", "\n")
    try:
        return clean, spec.parser(clean), []
    except ValueError:
        pass

    repaired, changes = repair_log_text(key, clean)
    try:
        return repaired, spec.parser(repaired), changes
    except ValueError as err:
        if llm_fixer is None:
            raise
        lines = repaired.splitlines()
        last_err: Exception = err
        for _ in range(max_llm_lines):
            match = _LINE_ERROR.search(str(last_err))
            if not match:
                break
            lineno = int(match[1])
            nonempty = [i for i, ln in enumerate(lines) if ln.strip()]
            idx = lineno - 1 if 0 <= lineno - 1 < len(lines) and lines[lineno - 1].strip() else (
                nonempty[lineno - 1] if 0 < lineno <= len(nonempty) else None
            )
            if idx is None:
                break
            before = lines[idx]
            after = llm_fixer(key, before, str(last_err))
            if not after or after == before:
                break
            lines[idx] = after
            changes.append({"line": idx + 1, "before": before, "after": after, "method": "llm"})
            candidate_text = "\n".join(lines) + "\n"
            try:
                return candidate_text, spec.parser(candidate_text), changes
            except ValueError as next_err:
                last_err = next_err
        raise last_err


def sync_logs(
    root: Path,
    *,
    drive_dir: Path | None = None,
    llm_repair: bool = False,
    dry_run: bool = False,
) -> dict[str, dict]:
    """Sync all 6 logs from drive_dir (if given/found) or newer local copy into records/ and preview."""
    root = root.resolve()
    if drive_dir is None:
        found = default_drive_dirs()
        drive_dir = found[0] if found else None

    fixer = gemini_repair_line if llm_repair else None
    gdoc_map = load_gdoc_map(root)
    report: dict[str, dict] = {}
    for key, spec in SPECS.items():
        rec_file = root / spec.records_path
        prev_file = root / spec.preview_path
        raw: str | None = None
        source_label = ""
        chosen_desc = ""

        if key in gdoc_map:
            try:
                raw = fetch_gdoc_text(gdoc_map[key])
                source_label = "gdoc-cloud"
                chosen_desc = f"https://docs.google.com/document/d/{gdoc_map[key]}"
                if key == "running" and rec_file.is_file():
                    rec_txt = rec_file.read_text(encoding="utf-8-sig")
                    rec_dates = sorted(
                        f"{m[3]}-{int(m[1]):02d}-{int(m[2]):02d}"
                        for m in re.finditer(r"(\d{1,2})/(\d{1,2})/(20\d{2})", rec_txt)
                    )
                    gdoc_dates = sorted(
                        f"{m[3]}-{int(m[1]):02d}-{int(m[2]):02d}"
                        for m in re.finditer(r"(\d{1,2})/(\d{1,2})/(20\d{2})", raw)
                    )
                    if rec_dates and (not gdoc_dates or gdoc_dates[-1] <= rec_dates[-1]):
                        raw = rec_txt
            except Exception:
                if rec_file.is_file():
                    raw = rec_file.read_text(encoding="utf-8-sig")
                    source_label = "records-fallback"
                    chosen_desc = str(rec_file.relative_to(root))
                else:
                    raise
        else:
            candidates: list[tuple[str, Path]] = []
            if drive_dir is not None:
                stem = Path(spec.filename).stem
                for probe in (
                    drive_dir / spec.filename,
                    drive_dir / f"{stem}.docx",
                    drive_dir / f"{stem}.gdoc",
                    drive_dir / key / spec.filename,
                    drive_dir / key / f"{stem}.docx",
                    drive_dir / key / f"{stem}.gdoc",
                ):
                    if probe.is_file():
                        candidates.append(("drive", probe))
                        break
            if prev_file.is_file():
                candidates.append(("preview", prev_file))
            if rec_file.is_file():
                candidates.append(("records", rec_file))
            if not candidates:
                raise FileNotFoundError(f"No source file found for {spec.filename}")

            source_label, chosen = max(candidates, key=lambda item: (item[1].stat().st_mtime_ns, item[1].stat().st_size))
            chosen_desc = str(chosen.relative_to(root) if chosen.is_relative_to(root) else chosen)
            suffix = chosen.suffix.lower()
            if suffix == ".docx":
                from docx_to_txt import docx_to_text
                raw = docx_to_text(chosen)
            elif suffix == ".gdoc":
                raw = fetch_gdoc_text(chosen.read_text(encoding="utf-8-sig"))
                source_label = "drive-gdoc"
            else:
                raw = chosen.read_text(encoding="utf-8-sig")

        validated_text, parsed, repairs = validate_or_repair(key, raw, llm_fixer=fixer)
        updated = False
        for target in (rec_file, prev_file):
            existing = target.read_text(encoding="utf-8-sig").replace("\r\n", "\n") if target.is_file() else None
            if existing != validated_text:
                updated = True
                if not dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(validated_text, encoding="utf-8", newline="\n")
        report[key] = {
            "source": source_label,
            "path": chosen_desc,
            "updated": updated,
            "repairs": repairs,
            "summary": parsed.get("summary", {}),
        }
    return report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-dir", type=Path, default=None, help="Path to Google Drive 'Logs' folder.")
    parser.add_argument("--set-doc", nargs=2, metavar=("KEY", "URL_OR_ID"),
                        help=f"Link a Google Doc share URL/ID for automatic cloud pull ({', '.join(SPECS)}).")
    parser.add_argument("--llm-repair", action="store_true", help="Use Gemini API to fix single lines that deterministic rules cannot.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report repairs without writing files.")
    args = parser.parse_args()
    if args.set_doc:
        key, url_or_id = args.set_doc
        doc_id = save_gdoc_link(root, key, url_or_id)
        print(f"Linked {key} -> Google Doc {doc_id} (saved in {GDOC_MAP_PATH})")
        return
    report = sync_logs(root, drive_dir=args.drive_dir, llm_repair=args.llm_repair, dry_run=args.dry_run)
    for key, info in report.items():
        status = "updated" if info["updated"] else "in-sync"
        repairs = f" ({len(info['repairs'])} line repairs)" if info["repairs"] else ""
        print(f"{key:13s}: {status} from {info['source']}{repairs}")


if __name__ == "__main__":
    main()
