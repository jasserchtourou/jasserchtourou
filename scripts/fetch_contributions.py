"""Scrape the public GitHub contribution calendar and write data/contributions.json.

No token needed: uses the same HTML fragment the profile page loads.
"""
import json
import os
import re
from collections import OrderedDict
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "jasserchtourou")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def parse_count(text: str) -> int:
    if not text or text.startswith("No contributions"):
        return 0
    m = re.match(r"(\d[\d,]*)", text)
    return int(m.group(1).replace(",", "")) if m else 0


def main() -> None:
    url = f"https://github.com/users/{USERNAME}/contributions"
    html = requests.get(url, headers={"User-Agent": "profile-readme-bot"}, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": parse_count(tips.get(td.get("id"), "")),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("No contribution cells found - GitHub markup may have changed.")

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # Streaks (today with 0 contributions doesn't break the current streak yet)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["count"] > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break

    monthly = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    data = {
        "username": USERNAME,
        "generated": date.today().isoformat(),
        "total": total,
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{len(days)} days, {total} contributions, streak {current}/{longest}")


if __name__ == "__main__":
    main()
