#!/usr/bin/env python3
"""Generate a dark contribution 'cubes' SVG for the current calendar year only."""
import os, json, datetime, urllib.request

USER = "Jerry256254"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
year = datetime.datetime.now(datetime.timezone.utc).year

query = 'query($from:DateTime!,$to:DateTime!){ user(login:"%s"){ contributionsCollection(from:$from,to:$to){ contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount contributionLevel } } } } } }' % USER
body = json.dumps({"query": query, "variables": {
    "from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"}}).encode()
req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
    "Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "contributions-year"})
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.load(r)
cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
total = cal["totalContributions"]
weeks = cal["weeks"]

COLORS = {"NONE": "#21262d", "FIRST_QUARTILE": "#0e4429", "SECOND_QUARTILE": "#006d32",
          "THIRD_QUARTILE": "#26a641", "FOURTH_QUARTILE": "#39d353"}
CELL, GAP = 14, 3
STEP = CELL + GAP
LEFT, TOP = 14, 58
grid_w = len(weeks) * STEP - GAP
W = LEFT * 2 + grid_w
H = TOP + 7 * STEP - GAP + 34

parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{total} contributions in {year}">']
parts.append(f'<rect width="{W}" height="{H}" rx="8" fill="#0d1117"/>')
parts.append(f'<text x="{LEFT}" y="30" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600" fill="#e6edf3">{total} contributions in {year}</text>')

# month labels
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
seen = set()
for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        m = int(day["date"][5:7])
        if m not in seen:
            seen.add(m)
            parts.append(f'<text x="{LEFT + wi*STEP}" y="{TOP-8}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10" fill="#7d8590">{months[m-1]}</text>')
        break

for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        dt = datetime.date.fromisoformat(day["date"])
        row = (dt.weekday() + 1) % 7  # Sunday = 0
        x, y = LEFT + wi * STEP, TOP + row * STEP
        parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{COLORS[day["contributionLevel"]]}"><title>{day["contributionCount"]} contributions on {day["date"]}</title></rect>')

ly = TOP + 7 * STEP - GAP + 22
lx = LEFT + grid_w
parts.append(f'<text x="{lx-150}" y="{ly+3}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10" fill="#7d8590">Less</text>')
for i, lvl in enumerate(["NONE","FIRST_QUARTILE","SECOND_QUARTILE","THIRD_QUARTILE","FOURTH_QUARTILE"]):
    parts.append(f'<rect x="{lx-118 + i*(CELL+3)}" y="{ly-8}" width="{CELL}" height="{CELL}" rx="3" fill="{COLORS[lvl]}"/>')
parts.append(f'<text x="{lx-118 + 5*(CELL+3) + 4}" y="{ly+3}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="10" fill="#7d8590">More</text>')
parts.append('</svg>')

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "contributions-year.svg")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    f.write("\n".join(parts) + "\n")
print(f"Wrote {out}: {total} contributions in {year}, {len(weeks)} weeks")
