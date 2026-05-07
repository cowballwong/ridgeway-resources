"""
Inject a floating "← Resources / 資源庫" home button into every reading page so visitors
can return to the landing page from any sermon or special-event page.

Idempotent: looks for the rg-home-btn class marker and skips files that already have it.
"""

import re
from pathlib import Path

ROOT = Path(r"C:\ridgeway-resources")

SNIPPET = """
<style>
.rg-home-btn {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 9999;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #ffffff;
  color: #2d2a25;
  border: 1px solid #e6dfd5;
  border-radius: 999px;
  font-family: "Noto Serif TC", "Source Han Serif TC", "PingFang TC", Georgia, serif;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 4px 12px rgba(45,42,37,.08);
  transition: transform .15s, border-color .15s, color .15s;
}
.rg-home-btn:hover {
  border-color: #b25530;
  color: #b25530;
  transform: translateY(-1px);
}
.rg-home-btn .arrow { color: #b25530; font-weight: 600; }
.rg-home-btn .zh { color: #6f6a62; font-size: 12px; }
@media (prefers-color-scheme: dark) {
  .rg-home-btn { background: #1d2024; color: #ebe7df; border-color: #2a2d31; }
  .rg-home-btn .zh { color: #9a9590; }
  .rg-home-btn .arrow { color: #e9956a; }
}
html[data-theme="night"] .rg-home-btn {
  background: #1d2024; color: #ebe7df; border-color: #2a2d31;
}
html[data-theme="night"] .rg-home-btn .zh { color: #9a9590; }
html[data-theme="night"] .rg-home-btn .arrow { color: #e9956a; }

/* push existing topbars rightward so the pill doesn't overlap */
body > .topbar { padding-left: 140px !important; }
@media (max-width: 600px) {
  .rg-home-btn { padding: 6px 11px; font-size: 12px; }
  .rg-home-btn .zh { display: none; }
  body > .topbar { padding-left: 78px !important; }
}
</style>
<a class="rg-home-btn" href="{home_href}" aria-label="Back to resources index">
  <span class="arrow">&larr;</span>
  <span>Resources</span>
  <span class="zh">資源庫</span>
</a>
"""


def find_pages() -> list[tuple[Path, str]]:
    """Return list of (file, home_href) for every reading index.html."""
    pages = []
    away = ROOT / "away-day-2026" / "index.html"
    if away.exists():
        pages.append((away, "../"))
    sermons_dir = ROOT / "sermons"
    if sermons_dir.exists():
        for slug_dir in sorted(sermons_dir.iterdir()):
            html = slug_dir / "index.html"
            if html.exists():
                pages.append((html, "../../"))
    return pages


def inject(file: Path, home_href: str) -> str:
    raw = file.read_text(encoding="utf-8")
    if 'class="rg-home-btn"' in raw:
        return "skip (already injected)"
    snippet = SNIPPET.replace("{home_href}", home_href)
    new = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + snippet, raw, count=1)
    if new == raw:
        return "FAIL (no <body> tag found)"
    file.write_text(new, encoding="utf-8")
    return "ok"


def main():
    for file, home_href in find_pages():
        rel = file.relative_to(ROOT)
        result = inject(file, home_href)
        print(f"{str(rel):<60} -> {home_href:<7} {result}")


if __name__ == "__main__":
    main()
