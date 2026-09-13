#!/usr/bin/env python3
import html
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

OWNER = os.getenv("PROFILE_OWNER", "FelpzSystem")
TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit('ERRO: GITHUB_TOKEN não está definido. No Termux, use: export GITHUB_TOKEN="SEU_TOKEN"')
README = Path("README.md")
API = "https://api.github.com"

def api(path):
    req = urllib.request.Request(
        API + path,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "FelpzSystem-profile-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

def esc(value):
    return html.escape(value or "", quote=True)

user = api(f"/users/{urllib.parse.quote(OWNER)}")
repos = api(f"/users/{urllib.parse.quote(OWNER)}/repos?per_page=100&sort=updated")

repos = [r for r in repos if not r.get("fork") and r.get("name") != OWNER]
repos.sort(
    key=lambda r: (
        r.get("stargazers_count", 0),
        r.get("forks_count", 0),
        r.get("pushed_at") or "",
    ),
    reverse=True,
)

featured = repos[:6]

def featured_card(r):
    name = esc(r["name"])
    desc = esc(r.get("description") or "Projeto em destaque da conta.")
    lang = esc(r.get("language") or "Code")
    url = r["html_url"]
    stars = urllib.parse.quote(r["name"], safe="")
    return f"""
<td width="33%" valign="top">
<div>
<h3><a href="{url}">{name}</a></h3>
<p>{desc}</p>
<p>
<img src="https://img.shields.io/badge/{urllib.parse.quote(lang, safe='')}-6E56CF?style=flat-square"/>
<img src="https://img.shields.io/github/stars/{OWNER}/{stars}?style=flat-square"/>
<img src="https://img.shields.io/github/forks/{OWNER}/{stars}?style=flat-square"/>
</p>
</div>
</td>"""

feature_rows = []
for i in range(0, len(featured), 3):
    chunk = featured[i:i+3]
    cells = [featured_card(r) for r in chunk]
    while len(cells) < 3:
        cells.append('<td width="33%"></td>')
    feature_rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
featured_html = '<div align="center"><table>\n' + "\n".join(feature_rows) + "\n</table></div>"

all_rows = []
for i in range(0, len(repos), 3):
    chunk = repos[i:i+3]
    cells = []
    for r in chunk:
        name = esc(r["name"])
        desc = esc(r.get("description") or "No description")
        lang = esc(r.get("language") or "Code")
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        cells.append(
            f'<td width="33%" valign="top"><h3><a href="{r["html_url"]}">{name}</a></h3>'
            f'<p>{desc}</p><p><b>{lang}</b> · ⭐ {stars} · 🍴 {forks}</p></td>'
        )
    while len(cells) < 3:
        cells.append('<td width="33%"></td>')
    all_rows.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
all_projects_html = '<div align="center"><table>\n' + "\n".join(all_rows) + "\n</table></div>"

total_stars = sum(r.get("stargazers_count", 0) for r in repos)
stats_html = (
    '<div align="center">'
    f'<img src="https://img.shields.io/badge/Repositories-{len(repos)}-7F00FF?style=for-the-badge"/> '
    f'<img src="https://img.shields.io/badge/Stars-{total_stars}-F5C542?style=for-the-badge"/> '
    f'<img src="https://img.shields.io/badge/Followers-{user.get("followers", 0)}-00C6FF?style=for-the-badge"/>'
    '</div>'
)

text = README.read_text(encoding="utf-8")

def replace_section(text, start, end, replacement):
    if start not in text or end not in text:
        raise ValueError(f"Marcadores ausentes no README: {start} / {end}")
    start_pos = text.index(start) + len(start)
    end_pos = text.index(end)
    if end_pos < start_pos:
        raise ValueError(f"Ordem inválida dos marcadores: {start} / {end}")
    return text[:start_pos] + "\n" + replacement.rstrip() + "\n" + text[end_pos:]

text = replace_section(text, "<!-- PROFILE_STATS_START -->", "<!-- PROFILE_STATS_END -->", stats_html)
text = replace_section(text, "<!-- FEATURED_PROJECTS_START -->", "<!-- FEATURED_PROJECTS_END -->", featured_html)
text = replace_section(text, "<!-- ALL_PROJECTS_START -->", "<!-- ALL_PROJECTS_END -->", all_projects_html)

README.write_text(text, encoding="utf-8")
print(f"Updated profile with {len(repos)} repositories.")
