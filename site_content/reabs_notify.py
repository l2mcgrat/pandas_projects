"""Cloud & CLI dispatcher for REABS (Random Extra Additional Bullshit) scheduled reminders.

Runs automatically via GitHub Actions on schedule (8am, 2pm, 3pm America/Toronto) or
on-demand via ``python -B -m site_content.reabs_notify --force`` to dispatch active
REABS reminders to l2mcgrat@uwaterloo.ca (with X-Priority urgency flags) and mobile push/SMS.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from urllib import request as urllib_request

from .workbench import load_workbench


def _toronto_now() -> datetime:
    """Return current time in America/Toronto (EDT UTC-4 Mar-Nov, EST UTC-5 Nov-Mar)."""
    utc_now = datetime.now(timezone.utc)
    offset_hours = -4 if 3 <= utc_now.month <= 10 else -5
    return utc_now + timedelta(hours=offset_hours)


def dispatch_reabs_item(item: dict) -> bool:
    """Send email & push/SMS notification for a single active REABS reminder."""
    urg = item.get("urgency", "Medium")
    x_priority = "1 (Highest)" if urg == "High" else "3 (Normal)" if urg == "Medium" else "5 (Lowest)"
    importance = "High" if urg == "High" else "Normal" if urg == "Medium" else "Low"
    ntfy_prio = "5" if urg == "High" else "3" if urg == "Medium" else "2"
    prefix = "🚨 [HIGH URGENCY · REABS]" if urg == "High" else "⚡ [MEDIUM URGENCY · REABS]" if urg == "Medium" else "📌 [LOW URGENCY · REABS]"

    phone = str(item.get("phoneNumber") or "").strip()
    has_phone = bool(phone) and phone.upper() != "N/A" and item.get("phoneSource") != "na"
    base_url = "https://liammspandasprojects.org/Reminders/index.html"
    rid = item["id"]

    subject = f"{prefix} {rid}: {item['title']} ({item['scheduleText']})"
    lines = [
        f"REABS REMINDER ({rid}) — Random Extra Additional Bullshit",
        "================================================================",
        f"Task:      {item['title']}",
        f"Urgency:   {urg} (Email Flag: X-Priority: {x_priority}, Importance: {importance})",
        f"Schedule:  {item['scheduleText']}",
    ]
    if has_phone:
        lines.append(f"Phone:     {phone}")
    lines.extend([
        f"Reasoning: {item['reasoning']}",
        "",
        "--- ONE-TAP COMPLETION & HOURS LOGGER ---",
        f"• Mark Completed (0.5 hrs): {base_url}?reabs_action=complete&id={rid}&hours=0.5",
        f"• Mark Completed (1.0 hr):  {base_url}?reabs_action=complete&id={rid}&hours=1.0",
        f"• Mark Completed (2.0 hrs): {base_url}?reabs_action=complete&id={rid}&hours=2.0",
        f"• Turn Off / Mute Reminder: {base_url}?reabs_action=mute&id={rid}",
    ])
    body_text = "\n".join(lines)

    recipients = [item.get("defaultEmail") or "l2mcgrat@uwaterloo.ca"]
    for extra in str(item.get("extraEmails") or "").split(","):
        if extra.strip() and extra.strip() not in recipients:
            recipients.append(extra.strip())

    sent_ok = False
    for email_addr in recipients:
        try:
            req = urllib_request.Request(
                "https://ntfy.sh/liam_reabs_email_67wxyE7L_v1",
                data=body_text.encode("utf-8"),
                headers={
                    "Title": subject.encode("ascii", errors="ignore").decode("ascii"),
                    "Priority": ntfy_prio,
                    "X-Email": email_addr,
                    "X-Priority": x_priority,
                    "Importance": importance,
                },
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    sent_ok = True
        except Exception:
            pass

    if item.get("smsEnabled", 1):
        try:
            short_sms = (
                f"[REABS {urg.upper()}] {rid}: {item['title']} ({item['scheduleText']})"
                + (f" · Call: {phone}" if has_phone else "")
                + f" · Done 1h: {base_url}?reabs_action=complete&id={rid}&hours=1.0"
            )
            req_sms = urllib_request.Request(
                "https://ntfy.sh/liam_reabs_sms_67wxyE7L_v1",
                data=short_sms.encode("utf-8"),
                headers={
                    "Title": f"REABS {rid}: {item['title'][:40]}",
                    "Priority": ntfy_prio,
                },
                method="POST",
            )
            with urllib_request.urlopen(req_sms, timeout=10) as resp:
                if resp.status == 200:
                    sent_ok = True
        except Exception:
            pass

    return sent_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Send all active REABS reminders immediately regardless of time.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    data = load_workbench(root)
    reabs = data.get("reabsReminders", [])
    now = _toronto_now()
    day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now.weekday()]
    cur_hour = now.hour

    dispatched = 0
    for item in reabs:
        if item.get("status") != "active" or not item.get("remindersEnabled", 1):
            continue
        days = [d.strip() for d in str(item.get("daysOfWeek") or "").split(",") if d.strip()]
        item_hour = int(str(item.get("timeOfDay") or "14:00").split(":")[0])
        if args.force or (day_abbr in days and item_hour == cur_hour):
            if dispatch_reabs_item(item):
                dispatched += 1
                print(f"Dispatched {item['id']} ({item['title']}) -> {item.get('defaultEmail', 'l2mcgrat@uwaterloo.ca')}")
    print(f"REABS check complete ({day_abbr} {now.strftime('%H:%M')} EDT): {dispatched} reminder(s) sent.")


if __name__ == "__main__":
    main()
