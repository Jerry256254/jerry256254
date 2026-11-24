#!/usr/bin/env python3
"""Generate a dark contribution 'cubes' SVG for the current calendar year only.

Data source: the public contributions page (github.com/users/<user>/contributions),
which needs no token, so the scheduled GitHub Action can regenerate this daily.
"""
import re, datetime, urllib.request

USER = "Jerry256254"
year = datetime.datetime.now(datetime.timezone.utc).year

url = f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    html = r.read().decode()

m = re.search(r"(\d[\d,]*)\s+contributions\s+in\s+" + str(year), re.sub(r"<[^>]+>", " ", html))
total = int(m.group(1).replace(",", "")) if m else 0

levels = {date: int(level) for date, _r, _c, level in
          re.findall(r'data-date="([^"]+)" id="contribution-day-component-(\d+)-(\d+)" data-level="(\d)"', html)}

MONTHS = {name: i + 1 for i, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
counts = {}
for tip in re.findall(r"<tool-tip[^>]*>([^<]+)</tool-tip>", html):
    mm = re.match(r"(No|\d+) contributions? on (\w+) (\d+)(?:st|nd|rd|th)\.", tip)
    if mm:
        d = datetime.date(year, MONTHS[mm.group(2)], int(mm.group(3)))
        counts[d.isoformat()] = 0 if mm.group(1) == "No" else int(mm.group(1))

days = sorted(levels)
assert len(days) >= 360, f"unexpected day count: {len(days)}"

LEVEL_NAMES = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
COLORS = {"NONE": "#21262d", "FIRST_QUARTILE": "#0e4429", "SECOND_QUARTILE": "#006d32",
          "THIRD_QUARTILE": "#26a641", "FOURTH_QUARTILE": "#39d353"}

first = datetime.date(year, 1, 1)
origin = first - datetime.timedelta(days=(first.weekday() + 1) % 7)  # Sunday of first week
last = datetime.date(year, 12, 31)
ncols = ((last - origin).days) // 7 + 1

CELL, GAP = 14, 3
STEP = CELL + GAP
LEFT, TOP = 14, 58
grid_w = ncols * STEP - GAP
W = LEFT * 2 + grid_w
H = TOP + 7 * STEP - GAP + 34

parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{total} contributions in {year}">']
parts.append(f'<rect width="{W}" height="{H}" rx="8" fill="#0d1117"/>')
parts.append(f'<text x="{LEFT}" y="30" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600" fill="#e6edf3">{total} contributions in {year}</text>')

month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
seen = set()
for iso in days:
    d = datetime.date.fromisoformat(iso)
    if d.month not in seen:
        seen.add(d.month)
        col = ((d - origin).days) // 7
        parts.append(f'<text x="{LEFT + col*STEP}" y="{TOP-8}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10" fill="#7d8590">{month_names[d.month-1]}</text>')

for iso in days:
    d = datetime.date.fromisoformat(iso)
    col = ((d - origin).days) // 7
    row = (d.weekday() + 1) % 7  # Sunday = 0
    x, y = LEFT + col * STEP, TOP + row * STEP
    lvl = LEVEL_NAMES[levels[iso]]
    parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{COLORS[lvl]}"><title>{counts.get(iso, 0)} contributions on {iso}</title></rect>')

ly = TOP + 7 * STEP - GAP + 22
lx = LEFT + grid_w
parts.append(f'<text x="{lx-150}" y="{ly+3}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10" fill="#7d8590">Less</text>')
for i, lvl in enumerate(LEVEL_NAMES):
    parts.append(f'<rect x="{lx-118 + i*(CELL+3)}" y="{ly-8}" width="{CELL}" height="{CELL}" rx="3" fill="{COLORS[lvl]}"/>')
parts.append(f'<text x="{lx-118 + 5*(CELL+3) + 4}" y="{ly+3}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10" fill="#7d8590">More</text>')
parts.append('</svg>')

import os
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "contributions-year.svg")
with open(out, "w") as f:
    f.write("\n".join(parts) + "\n")
print(f"Wrote {out}: {total} contributions in {year}, {ncols} weeks, {len(days)} days")
