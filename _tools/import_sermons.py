"""
Import Sunday sermons from G:\My Drive\AI_Development\03_church\01_bible-study\sunday\
into the public ridgeway-resources/sermons/ folder.

For HTMLs with embedded base64 audio (data:audio/mpeg;base64,...), strip the data URI
and rewrite the <audio src> to point at an external audio/cantonese.mp3 file copied
from the source folder. Smaller HTML = faster page load.
"""

import re
import shutil
from pathlib import Path

SRC_BASE = Path(r"G:\My Drive\AI_Development\03_church\01_bible-study\sunday")
DST_BASE = Path(r"C:\ridgeway-resources\sermons")

SERMONS = [
    {
        "slug": "2026-01-04-psalm-16",
        "src_folder": "2026-01-04 Psalm_16",
        "html": "Psalm_16_Sermon_Bilingual.html",
        "audio": None,
    },
    {
        "slug": "2026-03-29-one-of-us-part-1",
        "src_folder": "2026-03-29 One of Us (I)",
        "html": "Hebrews_2-5-9_Bilingual.html",
        "audio": None,
    },
    {
        "slug": "2026-04-02-value-of-the-cross",
        "src_folder": "2026-04-02 The Value of the Cross",
        "html": "Good_Friday_Sermon_Bilingual.html",
        "audio": None,
    },
    {
        "slug": "2026-04-19-dont-look-elsewhere",
        "src_folder": "2026-04-19 Don't Look Elsewhere",
        "html": "2026-04-19-Sunday Service-Don't Look Elsewhere.html",
        "audio": None,
    },
    {
        "slug": "2026-04-26-finishing-well",
        "src_folder": "2026-04-26 Finishing Well",
        "html": "2026-04-26-Sunday Service-Finishing Well.html",
        "audio": "finishing-well-cantonese.mp3",
    },
    {
        "slug": "2026-05-03-rest-is-coming",
        "src_folder": "2026-05-03 Rest is Coming",
        "html": "2026-05-03-Sunday Service-Rest is Coming.html",
        "audio": "2026-05-03-Sunday Service-Rest is Coming-cantonese.mp3",
    },
]

DATA_URI_RE = re.compile(
    r'src=(["\'])data:audio/[^;]+;base64,[A-Za-z0-9+/=\s]+\1',
    re.DOTALL,
)


def strip_data_uri(html: str, new_src: str) -> tuple[str, bool]:
    """Replace base64 data:audio src with external file ref. Returns (html, replaced)."""
    new_html, count = DATA_URI_RE.subn(f'src="{new_src}"', html)
    return new_html, count > 0


def import_sermon(s: dict) -> dict:
    src_folder = SRC_BASE / s["src_folder"]
    src_html = src_folder / s["html"]
    dst_folder = DST_BASE / s["slug"]
    dst_folder.mkdir(parents=True, exist_ok=True)
    dst_html = dst_folder / "index.html"

    raw = src_html.read_text(encoding="utf-8")
    info = {"slug": s["slug"], "in_kb": len(raw) // 1024, "audio": False, "stripped": False}

    if s["audio"]:
        audio_dir = dst_folder / "audio"
        audio_dir.mkdir(exist_ok=True)
        audio_dst = audio_dir / "cantonese.mp3"
        shutil.copy2(src_folder / s["audio"], audio_dst)
        info["audio"] = True

        rewritten, did = strip_data_uri(raw, "audio/cantonese.mp3")
        info["stripped"] = did
        raw = rewritten

    dst_html.write_text(raw, encoding="utf-8")
    info["out_kb"] = len(raw) // 1024
    return info


def main():
    DST_BASE.mkdir(parents=True, exist_ok=True)
    for s in SERMONS:
        info = import_sermon(s)
        flags = []
        if info["audio"]:
            flags.append("audio")
        if info["stripped"]:
            flags.append(f"stripped({info['in_kb']}KB->{info['out_kb']}KB)")
        print(f"{info['slug']:<40} {info['out_kb']:>5} KB  {' '.join(flags)}")


if __name__ == "__main__":
    main()
