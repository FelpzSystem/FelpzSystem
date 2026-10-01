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
    raise SystemExit('ERRO: GITHUB_TOKEN não está definido. Use: export GITHUB_TOKEN="SEU_TOKEN"')

README = Path("README.md")
API = "https://api.github.com"

FALLBACK_DESCRIPTIONS = {
    "virelix-tool": "Toolkit de processamento de imagens para Node.js (sharp): resize, conversão, compressão e batch.",
    "Bug-Hunter": "Analisador estático para JS, TS, ESM/CJS e Python, com revisão assistida por IA opcional.",
}

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

def repo_name_url(name):
    return urllib.parse.quote(name, safe="")

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

def tech_badge(language):
    language = language or "Code"
    colors = {
        "JavaScript": "F7DF1E", "TypeScript": "3178C6", "Python": "3776AB",
        "Lua": "2C2D72", "HTML": "E34F26", "CSS": "1572B6", "Java": "007396",
        "C++": "00599C", "PHP": "777BB4", "Shell": "89E051", "C#": "239120"
    }
    color = colors.get(language, "333333")
    return f'<img src="https://img.shields.io/badge/{urllib.parse.quote(language, safe="")}-{color}?style=flat&logo={urllib.parse.quote(language.lower(), safe="")}&logoColor=white" alt="{esc(language)}">'

def project_card(r):
    name = esc(r["name"])
    desc = esc(r.get("description") or FALLBACK_DESCRIPTIONS.get(r["name"]) or "Projeto em desenvolvimento.")
    url = r["html_url"]
    repo = repo_name_url(r["name"])
    language = r.get("language") or "Code"
    pin = urllib.parse.quote(f"{OWNER}/{r['name']}", safe="")
    return (
        '<td align="center" valign="top" width="33%">'
        f'<a href="{url}"><img src="https://github-readme-stats.vercel.app/api/pin/?username={urllib.parse.quote(OWNER, safe="")}&repo={pin}&theme=radical&hide_border=true" alt="{name}" width="100%" /></a>'
        f'<h3><a href="{url}">{name}</a></h3>'
        f'<p>{desc}</p>'
        f'<p>{tech_badge(language)} '
        f'<img src="https://img.shields.io/github/stars/{OWNER}/{repo}?style=flat&label=%20" alt="Stars"> '
        f'<img src="https://img.shields.io/github/forks/{OWNER}/{repo}?style=flat&label=%20" alt="Forks"></p>'
        '</td>'
    )

def render_cards(items):
    if not items:
        return '<div align="center"><p>Nenhum projeto público encontrado.</p></div>'
    rows = []
    for i in range(0, len(items), 3):
        cells = [project_card(r) for r in items[i:i+3]]
        while len(cells) < 3:
            cells.append('<td width="33%"></td>')
        rows.append('<tr>\n' + '\n'.join(cells) + '\n</tr>')
    return '<div align="center"><table>\n' + '\n'.join(rows) + '\n</table></div>'

featured_html = render_cards(featured)
all_html = render_cards(repos)

total_stars = sum(r.get("stargazers_count", 0) for r in repos)
stats_html = (
    '<div align="center">\n'
    f'<img src="https://img.shields.io/badge/Repositories-{len(repos)}-006bed?style=flat&label=%20&logo=github" alt="Repositories"> '
    f'<img src="https://img.shields.io/badge/Stars-{total_stars}-F59E0B?style=flat&label=%20&logo=github" alt="Stars"> '
    f'<img src="https://img.shields.io/badge/Followers-{user.get("followers", 0)}-EC4899?style=flat&label=%20&logo=github" alt="Followers"> '
    f'<img src="https://img.shields.io/badge/Following-{user.get("following", 0)}-10B981?style=flat&label=%20&logo=github" alt="Following">'
    '\n</div>'
)

text = README.read_text(encoding="utf-8")

def replace_section(text, start, end, replacement):
    if start not in text or end not in text:
        raise SystemExit(f"ERRO: marcadores ausentes no README: {start} / {end}")
    a = text.index(start) + len(start)
    b = text.index(end)
    if b < a:
        raise SystemExit(f"ERRO: ordem inválida dos marcadores: {start} / {end}")
    return text[:a] + "\n" + replacement.rstrip() + "\n" + text[b:]

text = replace_section(text, "<!-- PROFILE_STATS_START -->", "<!-- PROFILE_STATS_END -->", stats_html)
text = replace_section(text, "<!-- FEATURED_PROJECTS_START -->", "<!-- FEATURED_PROJECTS_END -->", featured_html)
text = replace_section(text, "<!-- ALL_PROJECTS_START -->", "<!-- ALL_PROJECTS_END -->", all_html)
README.write_text(text, encoding="utf-8")
print(f"✅ Perfil atualizado com {len(repos)} repositórios públicos.")
