"""Fetch the JP web-manual component CSS from a published JP manual (default: JE-1000F JP).

  python3 -I fetch_jp_style.py <out_dir> [--url https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-1000F/JP/ja/md/manual_je1000f_jp.html]

Writes jp-manual-components.css (the page's inline <style> blocks: safety band,
signal table, symbol/warning panels, inbox cards, usage heading …) and
manual-locales.css. Shared components (H1 bars, ● H2, spec tables, callouts,
warranty cards, LCD/troubleshooting tables) come from _static/web_manual.css,
which the draft already links as assets/source-manual.css; refresh that file too
when it is older than the published one (``--with-web-manual``).
"""
from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

RTD = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"


def fetch(url: str) -> str:
    # RTD (behind Cloudflare) answers urllib's default User-Agent with 403.
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (auto-manual us-jp-review-draft)"})
    with urllib.request.urlopen(request, timeout=90) as resp:
        return resp.read().decode("utf-8", "replace")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out_dir")
    ap.add_argument("--url", default=f"{RTD}/JE-1000F/JP/ja/md/manual_je1000f_jp.html")
    ap.add_argument("--with-web-manual", action="store_true")
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", fetch(a.url), re.S)
    blocks = [b for b in blocks if "--color-code-background" not in b]
    (out / "jp-manual-components.css").write_text(
        f"/* JP web-manual component styles copied from {a.url} */\n" + "\n".join(blocks), encoding="utf-8")
    (out / "manual-locales.css").write_text(fetch(f"{RTD}/_static/manual-locales.css"), encoding="utf-8")
    if a.with_web_manual:
        (out / "web_manual.css").write_text(fetch(f"{RTD}/_static/web_manual.css"), encoding="utf-8")
    print("wrote", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
