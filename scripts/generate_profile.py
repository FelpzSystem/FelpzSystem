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


def badge(url, alt):
    return '<img src="{}" alt="{}">'.format(url, alt)

def featured_card(r):
    name = esc(r["name"])
    desc = esc(r.get("description") or "Projeto em destaque.")
    lang = esc(r.get("language") or "Code")
    url = r["html_url"]
    repo = urllib.parse.quote(r["name"], safe="")
    return (
        '<td align="center" valign="top" width="33%">'
        '<h3><a href="{}">{}</a></h3>'
        '<p>{}</p><p>{} {} {}</p></td>'
    ).format(
        url, name, desc,
        badge('https://img.shields.io/badge/{}-181717?style=flat-square'.format(urllib.parse.quote(lang, safe='')), lang),
        badge('https://img.shields.io/github/stars/{}/{}?style=flat-square'.format(OWNER, repo), 'stars'),
        badge('https://img.shields.io/github/forks/{}/{}?style=flat-square'.format(OWNER, repo), 'forks')
    )

feature_rows = []
for i in range(0, len(featured), 3):
    cells = [featured_card(r) for r in featured[i:i+3]]
    while len(cells) < 3:
        cells.append('<td width="33%"></td>')
    feature_rows.append('<tr>\n' + '\n'.join(cells) + '\n</tr>')
featured_html = '<div align="center"><table>\n' + '\n'.join(feature_rows) + '\n</table></div>'

all_rows = []
for i in range(0, len(repos), 3):
    cells = []
    for r in repos[i:i+3]:
        name = esc(r["name"]); desc = esc(r.get("description") or "Sem descrição.")
        lang = esc(r.get("language") or "Code"); repo = urllib.parse.quote(r["name"], safe="")
        cells.append(
            '<td align="center" valign="top" width="33%">'
            '<h3><a href="{}">{}</a></h3><p>{}</p><p>{} {} {}</p></td>'.format(
                r["html_url"], name, desc,
                badge('https://img.shields.io/badge/{}-181717?style=flat-square'.format(urllib.parse.quote(lang, safe='')), lang),
                badge('https://img.shields.io/github/stars/{}/{}?style=flat-square'.format(OWNER, repo), 'stars'),
                badge('https://img.shields.io/github/forks/{}/{}?style=flat-square'.format(OWNER, repo), 'forks')
            )
        )
    while len(cells) < 3:
        cells.append('<td width="33%"></td>')
    all_rows.append('<tr>\n' + '\n'.join(cells) + '\n</tr>')
all_projects_html = '<div align="center"><table>\n' + '\n'.join(all_rows) + '\n</table></div>'

total_stars = sum(r.get("stargazers_count", 0) for r in repos)
stats_html = ('<div align="center">'
    + '<img src="https://img.shields.io/badge/Repositories-{}-181717?style=for-the-badge&logo=github" alt="Repositories"> '.format(len(repos))
    + '<img src="https://img.shields.io/badge/Stars-{}-181717?style=for-the-badge&logo=github" alt="Stars"> '.format(total_stars)
    + '<img src="https://img.shields.io/badge/Followers-{}-181717?style=for-the-badge&logo=github" alt="Followers">'.format(user.get("followers", 0))
    + '</div>')

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
