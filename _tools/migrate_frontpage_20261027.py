"""
One-off migration (2026-10-27): turn the long card-grid landing page into the
category top-bar layout (Sermon / Bible Study / Music / Special).

Reads the card-grid index.html from git (commit 3c32b81, the last card-grid
version), extracts every card, and writes the new index.html from
_tools/frontpage_template.html.

Sermon rows are plain static HTML inside <div id="sermon-rows">; the page's JS
groups them by data-date into year / month groups. sermon_watcher.py inserts a
new row right after the SERMON-ROWS marker, so auto-publish needs no JSON.

Run: py -X utf8 _tools/migrate_frontpage_20261027.py
"""

import datetime as dt
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "3c32b81"

old = subprocess.run(["git", "-C", str(ROOT), "show", f"{SOURCE_COMMIT}:index.html"],
                     capture_output=True, text=True, encoding="utf-8", check=True).stdout

CARD_RE = re.compile(r'[ \t]*<article class="card( is-special)?" data-href="([^"]+)"[^>]*>(.*?)</article>', re.S)


def field(body, pat):
    m = re.search(pat, body, re.S)
    return m.group(1).strip() if m else ""


cards = []
for m in CARD_RE.finditer(old):
    body = m.group(3)
    cards.append({
        "special": bool(m.group(1)), "href": m.group(2), "block": m.group(0),
        "badge": field(body, r'<span class="special-badge">(.*?)</span>'),
        "tag": field(body, r'<span class="tag">(.*?)</span>'),
        "h3": field(body, r'<h3>(.*?)</h3>'),
        "zh": field(body, r'<div class="zh-title">(.*?)</div>'),
        "desc": field(body, r'<p class="desc">(.*?)</p>'),
        "watch": field(body, r'(<a class="card-watch".*?</a>)'),
    })


def short_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')} {d.year}"


def row(c, iso, extra_attrs="", disp=None):
    tag = c["tag"]
    tag_html = ""
    if tag and not tag.startswith(("Sermon", "Bible Study")):
        tag_html = f'\n        <span class="srow-tag">{tag}</span>'
    watch = f"\n      {c['watch']}" if c["watch"] else ""
    return (
        f'    <article class="srow" data-href="{c["href"]}" data-date="{iso}"{extra_attrs} tabindex="0">\n'
        f'      <div class="srow-date">{disp or short_date(iso)}</div>\n'
        f'      <div class="srow-body">{tag_html}\n'
        f'        <h3>{c["h3"]}</h3>\n'
        f'        <div class="zh-title">{c["zh"]}</div>\n'
        f'        <p class="desc">{c["desc"]}</p>\n'
        f'      </div>{watch}\n'
        f'    </article>')


# ---- sermons: featured card (kept verbatim) + one row per sermon ----
featured_sermon = next(c for c in cards if c["special"] and c["badge"] == "★ This Sunday")
seen, sermon_rows = set(), []
for c in cards:
    if c["href"].startswith("sermons/") and c["href"] not in seen:
        seen.add(c["href"])
        iso = re.match(r"sermons/(\d{4}-\d{2}-\d{2})", c["href"]).group(1)
        sermon_rows.append((iso, row(c, iso)))
sermon_rows.sort(key=lambda t: t[0], reverse=True)

# ---- studies: featured card + rows grouped by topic ----
featured_study = next(c for c in cards if c["special"] and c["href"].startswith("studies/"))
seen, study_rows = set(), []
for c in cards:
    if c["href"].startswith("studies/") and c["href"] not in seen:
        seen.add(c["href"])
        iso = re.match(r"studies/(\d{4}-\d{2}-\d{2})", c["href"]).group(1)
        topic = ' data-group="philippians" data-group-label="Philippians · 腓立比書"' \
            if "philippians" in c["href"] else ' data-group="other" data-group-label="Other · 其他"'
        study_rows.append((iso, row(c, iso, topic)))
study_rows.sort(key=lambda t: t[0], reverse=True)

# ---- special events: grouped by event ----
away = next(c for c in cards if c["href"] == "away-day-2026/" and not c["special"])
away_date = field(away["block"], r'<div class="date">(.*?)</div>')  # "May 2026": no exact day on record
special_rows = [row(away, "2026-05",
                    ' data-group="away-day-2026" data-group-label="Away Day 2026 · 2026 退修日"', disp=away_date)]

tpl = (ROOT / "_tools" / "frontpage_template.html").read_text(encoding="utf-8")
out = (tpl
       .replace("{{FEATURED_SERMON}}", featured_sermon["block"].strip("\n"))
       .replace("{{SERMON_ROWS}}", "\n\n".join(r for _, r in sermon_rows))
       .replace("{{FEATURED_STUDY}}", featured_study["block"].strip("\n"))
       .replace("{{STUDY_ROWS}}", "\n\n".join(r for _, r in study_rows))
       .replace("{{SPECIAL_ROWS}}", "\n\n".join(special_rows)))
assert "{{" not in out
(ROOT / "index.html").write_text(out, encoding="utf-8")
print(f"sermons {len(sermon_rows)}, studies {len(study_rows)}, special {len(special_rows)}")
