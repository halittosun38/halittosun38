#!/usr/bin/env python3
"""halittosun38 profil kartlarini statik SVG olarak uretir.
GitHub Actions icinde calisir; ciktilar repoya commit edilir."""
import json, os, re, html, urllib.request, collections

USER  = os.environ.get("GH_USER", "halittosun38")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BG, BORDER = "#0d1117", "#30363d"
ORANGE, BLUE, PURPLE, GREEN, GRAY = "#ffa657", "#79c0ff", "#d2a8ff", "#7ee787", "#8b949e"
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": USER,
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def esc(s): return html.escape(str(s), quote=False)

# ---------- veri ----------
user, repos, page = api(f"https://api.github.com/users/{USER}"), [], 1
while True:
    b = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
    repos += b
    if len(b) < 100: break
    page += 1

owned  = [r for r in repos if not r["fork"]]
stars  = sum(r["stargazers_count"] for r in owned)
forks  = sum(r["forks_count"] for r in owned)

# dil dagilimi: her reponun gercek byte sayilarina gore agirliklandirilir
langs = collections.Counter()
for r in owned:
    try:
        for k, v in api(r["languages_url"]).items():
            langs[k] += v
    except Exception:
        if r.get("language"):
            langs[r["language"]] += 1

LANG_COLOR = {"Python":"#3572A5","Lua":"#000080","JavaScript":"#f1e05a","C#":"#178600",
              "HTML":"#e34c26","CSS":"#563d7c","TypeScript":"#3178c6","Shell":"#89e051",
              "Java":"#b07219","C++":"#f34b7d","Go":"#00ADD8","Batchfile":"#C1F12E"}

# ---------- kart cizici ----------
def card(title, rows, path, w=420):
    lh, top = 26, 92
    h = top + len(rows)*lh + 18
    out = [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
      f'viewBox="0 0 {w} {h}" font-family="{FONT}" font-size="13px">',
      f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
      f'<text x="24" y="40" fill="{GREEN}" font-size="15px" font-weight="bold">{esc(title)}</text>',
      f'<line x1="24" y1="58" x2="{w-24}" y2="58" stroke="{BORDER}"/>']
    for i, (label, val, bar) in enumerate(rows):
        y = top + i*lh
        dots = '.' * max(1, 22 - len(label))
        out.append(f'<text x="24" y="{y}" xml:space="preserve">'
                   f'<tspan fill="{ORANGE}">{esc(label)}</tspan>'
                   f'<tspan fill="{GRAY}"> {dots} </tspan>'
                   f'<tspan fill="{BLUE}">{esc(val)}</tspan></text>')
        if bar:
            pct, col = bar
            bw = w - 48
            out.append(f'<rect x="24" y="{y+6}" width="{bw}" height="5" rx="2.5" fill="#21262d"/>')
            out.append(f'<rect x="24" y="{y+6}" width="{max(3,int(bw*pct))}" height="5" rx="2.5" fill="{col}"/>')
    out.append('</svg>')
    open(path, "w").write("\n".join(out) + "\n")
    print("yazildi:", path)

# ---------- stats ----------
card(f"{USER}@github  -  Stats", [
    ("Public Repos", user["public_repos"], None),
    ("Total Stars",  stars,  None),
    ("Total Forks",  forks,  None),
    ("Followers",    user["followers"], None),
    ("Following",    user["following"], None),
    ("Member Since", user["created_at"][:10], None),
], "stats.svg")

# ---------- languages ----------
top = [(k, v) for k, v in langs.most_common(6) if v] or [("Python", 1)]
tot = sum(v for _, v in top)
rows = []
for name, cnt in top:
    pct = cnt / tot
    rows.append((name, f"{pct*100:.1f}%", (pct, LANG_COLOR.get(name, "#8b949e"))))
card("Top Languages", rows, "langs.svg")

# ---------- contributions / streak ----------
# Public katki takvimi; token gerektirmez, bu yuzden her zaman calisir.
try:
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "Mozilla/5.0"})
    doc = urllib.request.urlopen(req, timeout=30).read().decode()

    tds  = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="(contribution-day-component-[\d-]+)"', doc)
    tips = dict(re.findall(r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>(.*?)</tool-tip>', doc, re.S))

    days = []
    for date, cid in tds:
        m = re.match(r"(No|\d+)\s+contribution", html.unescape(tips.get(cid, "")).strip())
        days.append((date, 0 if (not m or m.group(1) == "No") else int(m.group(1))))
    days.sort()
    if not days:
        raise ValueError("takvim bos")

    total   = sum(n for _, n in days)
    active  = sum(1 for _, n in days if n > 0)
    longest = run = 0
    for _, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    # bugun henuz bitmedigi icin sifirsa dunden geriye say
    tail, cur = (days[:-1] if days[-1][1] == 0 else days), 0
    for _, n in reversed(tail):
        if n > 0: cur += 1
        else: break

    card("Contributions", [
        ("Last Year",      total,            None),
        ("Current Streak", f"{cur} days",     None),
        ("Longest Streak", f"{longest} days", None),
        ("Active Days",    f"{active} / {len(days)}", None),
    ], "streak.svg")
except Exception as e:
    print("streak karti atlandi:", e)
