from __future__ import annotations

from datetime import datetime, timezone
from html import escape


LANGUAGE_LABELS = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "zh": "Chinese",
}


def display_text(value: object, fallback: str = "Not available") -> str:
    text = str(value or "").strip()
    return text or fallback


def format_generated_at(value: str) -> str:
    text = value.strip()
    if not text:
        return "Not available"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def preview_language_label(code: str) -> str:
    token = code.strip().lower()
    if not token:
        return "Not available"
    return LANGUAGE_LABELS.get(token, token.upper())


def derive_product_name(manual_title: str, fallback: str) -> str:
    text = manual_title.strip()
    if not text:
        return fallback
    for suffix in (
        " User Manual",
        " Manual de usuario",
        " Manuel d'utilisation",
        " Benutzerhandbuch",
        " 取扱説明書",
        " Manual",
    ):
        if text.endswith(suffix):
            candidate = text[: -len(suffix)].strip()
            if candidate:
                return candidate
    return text


def workspace_title(model: str) -> str:
    return f"{model} Review Preview"


def family_change_title(model: str, family: str) -> str:
    return f"{model} {family} Family Change Report"


def render_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"<li>{escape(empty_text)}</li>"
    return "".join(f"<li><code>{escape(item)}</code></li>" for item in items)


def render_link_list(items: list[tuple[str, str]]) -> str:
    if not items:
        return "<li>No downloads available for this review round.</li>"
    return "".join(f'<li><a href="{escape(target)}">{escape(label)}</a></li>' for label, target in items)


def render_areas(areas: list[dict[str, object]]) -> str:
    if not areas:
        return '<article class="card"><h2>Change Areas</h2><p>No grouped changes were detected.</p></article>'
    blocks: list[str] = []
    for area in areas:
        files = area.get("files", [])
        if not isinstance(files, list):
            continue
        blocks.append(
            "<article class=\"card\">"
            f"<h2>{escape(str(area['name']))}</h2>"
            "<ul>"
            + "".join(f"<li><code>{escape(str(item))}</code></li>" for item in files)
            + "</ul>"
            "</article>"
        )
    return "".join(blocks)


def build_download_links(downloads: dict[str, object], *, prefix: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    word_path = downloads.get("word_docx")
    workbook_path = downloads.get("change_workbook")
    csv_reports = downloads.get("csv_reports", {})
    if isinstance(word_path, str):
        links.append(("Download Word", f"{prefix}{word_path}"))
    if isinstance(workbook_path, str):
        links.append(("Download Change Workbook", f"{prefix}{workbook_path}"))
    if isinstance(csv_reports, dict):
        for file_name, label in (
            ("changes-summary.csv", "Download Summary CSV"),
            ("changes-pages.csv", "Download Page CSV"),
            ("changes-fields.csv", "Download Field CSV"),
            ("changes-files.csv", "Download File CSV"),
        ):
            target = csv_reports.get(file_name)
            if isinstance(target, str):
                links.append((label, f"{prefix}{target}"))
    return links


def workspace_css() -> str:
    return """
:root {
  --bg: #f4efe4;
  --panel: rgba(255, 252, 246, 0.96);
  --ink: #172b4d;
  --muted: #5b6777;
  --line: #d9cfbf;
  --accent: #1f5eff;
  --accent-dark: #12335f;
  --accent-soft: #eaf0ff;
  --chip: #f4f7ff;
  --chip-line: #d7e2ff;
  --shadow: 0 22px 48px rgba(23, 43, 77, 0.10);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Aptos", "Segoe UI", "Noto Sans", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(31, 94, 255, 0.10), transparent 30%),
    radial-gradient(circle at top right, rgba(18, 51, 95, 0.08), transparent 26%),
    linear-gradient(180deg, #f8f4ea 0%, #eee7db 100%);
}
a {
  color: var(--accent);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
.workspace-shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.workspace-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 32px;
  box-shadow: var(--shadow);
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.92fr);
  gap: 22px;
  align-items: start;
}
.hero-copy {
  padding-top: 4px;
}
h1 {
  margin: 16px 0 10px;
  font-size: 44px;
  line-height: 1.06;
}
.product-line {
  margin: 0;
  color: var(--accent);
  font-size: 18px;
  font-weight: 800;
}
.lede {
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.7;
  max-width: 700px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 188px;
  padding: 12px 18px;
  border-radius: 999px;
  font-weight: 800;
  border: 1px solid var(--accent);
}
.button.primary {
  background: var(--accent);
  color: white;
}
.button.secondary {
  background: white;
  color: var(--accent);
}
.button.download {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  color: white;
}
.detail-link {
  margin: 22px 0 0;
  color: var(--muted);
  font-size: 16px;
  min-height: 24px;
}
.identity-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(248,243,234,0.98));
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
}
.label {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.identity-card h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.3;
}
.identity-title {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.55;
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--chip);
  border: 1px solid var(--chip-line);
  color: #20438f;
  font-size: 12px;
  font-weight: 800;
}
.switch-group {
  margin-top: 16px;
}
.switch-label {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.switch-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.switch-pill {
  border: 1px solid var(--chip-line);
  background: var(--chip);
  color: #20438f;
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}
.switch-pill.is-active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.error-card {
  text-align: center;
}
@media (max-width: 960px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 720px) {
  .workspace-shell {
    padding: 24px 16px 40px;
  }
  .workspace-card {
    padding: 22px;
  }
  h1 {
    font-size: 34px;
  }
  .identity-card h2 {
    font-size: 18px;
  }
  .button {
    width: 100%;
  }
}
"""


def base_css() -> str:
    return """
:root {
  --bg: #f4efe4;
  --panel: rgba(255, 252, 246, 0.96);
  --ink: #172b4d;
  --muted: #5b6777;
  --line: #d9cfbf;
  --accent: #1f5eff;
  --accent-dark: #12335f;
  --accent-soft: #eaf0ff;
  --callout-bg: #fff6e8;
  --callout-line: #efd19d;
  --callout-ink: #7a4b04;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Aptos", "Segoe UI", "Noto Sans", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top right, rgba(31, 94, 255, 0.10), transparent 28%),
    linear-gradient(180deg, #f8f4ea 0%, #eee7db 100%);
}
a {
  color: var(--accent);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
.shell {
  max-width: 1140px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.hero,
.card,
.redirect-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 18px 42px rgba(23, 43, 77, 0.10);
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 {
  margin: 14px 0 10px;
  font-size: 40px;
  line-height: 1.08;
}
.lede,
.note,
.redirect-copy {
  margin: 0;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.7;
}
.note {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: var(--callout-bg);
  border: 1px solid var(--callout-line);
  color: var(--callout-ink);
  font-size: 15px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 188px;
  padding: 12px 18px;
  border-radius: 999px;
  font-weight: 800;
  border: 1px solid var(--accent);
}
.button.primary {
  background: var(--accent);
  color: white;
}
.button.secondary {
  background: white;
  color: var(--accent);
}
.button.download {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  color: white;
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #f4f7ff;
  border: 1px solid #d7e2ff;
  color: #20438f;
  font-size: 12px;
  font-weight: 800;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
  margin-top: 22px;
}
.card h2 {
  margin: 0 0 12px;
  font-size: 24px;
}
.card ul {
  margin: 0;
  padding-left: 20px;
}
.card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}
.redirect-card {
  max-width: 760px;
  margin: 72px auto;
}
code {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 0.95em;
}
@media (max-width: 720px) {
  .shell {
    padding: 24px 16px 40px;
  }
  .hero,
  .card,
  .redirect-card {
    padding: 22px;
  }
  h1 {
    font-size: 32px;
  }
  .button {
    width: 100%;
  }
}
"""
