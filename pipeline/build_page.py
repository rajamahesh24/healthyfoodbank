#!/usr/bin/env python3
"""
Build index.html for the HealthyFoodBank Susgaon "this Saturday" page.

- Reads pipeline/week_data.json  ->  the current week's sellers (maintained by the agent).
- Renders pipeline/page_template.html  ->  ../index.html
- Computes the target Saturday + the "post window" dates deterministically (IST).
- If week_data.json has no sellers, the page renders the friendly empty state
  (this is how "blank after Saturday 3pm" shows up until people start posting).

The agent (scheduled Claude run) is responsible for keeping week_data.json in sync
with messages.db and for clearing it after each Saturday 15:00 IST.
"""
import json, datetime, pathlib

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

MONTHS_EN = ["January","February","March","April","May","June","July",
             "August","September","October","November","December"]
MONTHS_MR = ["जानेवारी","फेब्रुवारी","मार्च","एप्रिल","मे","जून","जुलै",
             "ऑगस्ट","सप्टेंबर","ऑक्टोबर","नोव्हेंबर","डिसेंबर"]

RESET_HOUR = 15  # Saturday 15:00 IST -> page resets for the next Saturday


def most_recent_saturday_reset(now: datetime.datetime) -> datetime.datetime:
    """Most recent Saturday 15:00 IST at or before `now` (the start of the current window)."""
    # weekday(): Mon=0 ... Sat=5, Sun=6
    days_since_sat = (now.weekday() - 5) % 7
    candidate = (now - datetime.timedelta(days=days_since_sat)).replace(
        hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    if candidate > now:                      # today is Saturday but before 15:00
        candidate -= datetime.timedelta(days=7)
    return candidate


def fmt_date(d: datetime.date):
    en = f"Saturday, {d.day} {MONTHS_EN[d.month-1]} {d.year}"
    mr = f"शनिवार, {d.day} {MONTHS_MR[d.month-1]} {d.year}"
    return en, mr


def fmt_range(start: datetime.date, end: datetime.date):
    if start.month == end.month and start.year == end.year:
        en = f"{start.day}–{end.day} {MONTHS_EN[end.month-1]} {end.year}"
        mr = f"{start.day}–{end.day} {MONTHS_MR[end.month-1]} {end.year}"
    else:
        en = f"{start.day} {MONTHS_EN[start.month-1]} – {end.day} {MONTHS_EN[end.month-1]} {end.year}"
        mr = f"{start.day} {MONTHS_MR[start.month-1]} – {end.day} {MONTHS_MR[end.month-1]} {end.year}"
    return en, mr


def main():
    now = datetime.datetime.now(IST)
    window_start = most_recent_saturday_reset(now)
    target_saturday = (window_start + datetime.timedelta(days=7)).date()

    date_en, date_mr = fmt_date(target_saturday)
    range_en, range_mr = fmt_range(window_start.date(), now.date())
    _t = now.strftime("%I:%M %p").lstrip("0")
    build_en = f"{now.day} {MONTHS_EN[now.month-1]} {now.year}, {_t} IST"
    build_mr = f"{now.day} {MONTHS_MR[now.month-1]} {now.year}, {_t} IST"

    data = json.loads((HERE / "week_data.json").read_text(encoding="utf-8"))
    sellers = data.get("sellers", [])

    template = (HERE / "page_template.html").read_text(encoding="utf-8")
    html = (template
            .replace("__SELLERS_JSON__", json.dumps(sellers, ensure_ascii=False))
            .replace("__DATE_EN__", date_en)
            .replace("__DATE_MR__", date_mr)
            .replace("__RANGE_EN__", range_en)
            .replace("__RANGE_MR__", range_mr)
            .replace("__BUILD_EN__", build_en)
            .replace("__BUILD_MR__", build_mr))

    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"[build] now(IST)={now:%Y-%m-%d %H:%M}")
    print(f"[build] window_start={window_start:%Y-%m-%d %H:%M} -> target Saturday {target_saturday}")
    print(f"[build] sellers={len(sellers)}  range='{range_en}'")
    print(f"[build] wrote {ROOT/'index.html'}")


if __name__ == "__main__":
    main()
