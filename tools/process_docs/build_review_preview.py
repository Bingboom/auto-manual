from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build a review-first HTML preview package for Vercel or local sharing."
    )
    ap.add_argument("--config", default="config.yaml", help="Config YAML path, relative to repo root by default.")
    ap.add_argument("--model", required=True, help="Target model, for example JE-1000F.")
    ap.add_argument("--region", required=True, help="Target region, for example US.")
    ap.add_argument(
        "--source",
        default="review",
        choices=("auto", "runtime", "review"),
        help="Bundle source passed to build.py html. Default keeps the preview tied to review content.",
    )
    ap.add_argument(
        "--tracked-root",
        default=None,
        help="Tracked subtree for diff-report. Defaults to docs/_review/<model>/<region>.",
    )
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref for diff-report.")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref for diff-report.")
    ap.add_argument(
        "--output-dir",
        default="site/review-preview/dist",
        help="Static site output directory, relative to repo root by default.",
    )
    ap.add_argument(
        "--clean-build",
        action="store_true",
        help="Allow build.py html to clean the current target output first.",
    )
    ap.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build.py html and reuse an existing HTML bundle.",
    )
    ap.add_argument(
        "--skip-diff",
        action="store_true",
        help="Skip diff-report generation and reuse the latest report set.",
    )
    return ap.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def capture(cmd: list[str]) -> str:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def git_value(env_name: str, fallback_cmd: list[str]) -> str:
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    return capture(fallback_cmd)


def collect_changed_files(from_ref: str, to_ref: str) -> list[str]:
    raw = capture(["git", "diff", "--name-only", "--diff-filter=ACMRT", from_ref, to_ref])
    return [line.strip() for line in raw.splitlines() if line.strip()]


def classify_changes(changed_files: list[str], model: str, region: str) -> list[dict[str, object]]:
    review_prefix = f"docs/_review/{model}/{region}/"
    groups = [
        ("Review Bundle", lambda p: p.startswith(review_prefix)),
        ("Shared Templates", lambda p: p.startswith("docs/templates/")),
        ("Structured Data", lambda p: p.startswith("data/phase1/")),
        ("Automation And Build", lambda p: p == "build.py" or p.startswith("tools/") or p.startswith(".github/workflows/")),
        ("Maintainer Docs", lambda p: p == "README.md" or p.startswith("code-as-doc/") or p.startswith("user-guide/")),
    ]
    areas: list[dict[str, object]] = []
    assigned: set[str] = set()
    for name, matcher in groups:
        files = [path for path in changed_files if matcher(path)]
        if files:
            assigned.update(files)
            areas.append({"name": name, "files": files})
    other = [path for path in changed_files if path not in assigned]
    if other:
        areas.append({"name": "Other", "files": other})
    return areas


def latest_report_prefix(report_root: Path) -> str:
    candidates = sorted(report_root.glob("*_index.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No diff-report index html found under {report_root}")
    return candidates[0].name[: -len("_index.html")]


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_report_set(report_root: Path, prefix: str, changes_dir: Path) -> dict[str, str]:
    mapping = {
        f"{prefix}_index.html": "report-index.html",
        f"{prefix}.html": "report-summary.html",
        f"{prefix}_fields.html": "report-fields.html",
        f"{prefix}_pages.html": "report-pages.html",
        f"{prefix}_files.html": "report-files.html",
    }
    copied: dict[str, str] = {}
    changes_dir.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in mapping.items():
        src = report_root / src_name
        if src.exists():
            shutil.copy2(src, changes_dir / dst_name)
            copied[src_name] = dst_name
    return copied


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def render_list(items: list[str]) -> str:
    if not items:
        return "<li>No files changed in the selected diff range.</li>"
    return "".join(f"<li><code>{escape(item)}</code></li>" for item in items)


def render_areas(areas: list[dict[str, object]]) -> str:
    if not areas:
        return "<p>No grouped changes were detected.</p>"
    blocks: list[str] = []
    for area in areas:
        files = area.get("files", [])
        if not isinstance(files, list):
            continue
        blocks.append(
            "<section class=\"card\">"
            f"<h3>{escape(str(area['name']))}</h3>"
            "<ul>"
            + "".join(f"<li><code>{escape(str(item))}</code></li>" for item in files)
            + "</ul>"
            "</section>"
        )
    return "".join(blocks)


def render_area_list(areas: list[dict[str, object]]) -> str:
    if not areas:
        return "<p class=\"muted-note\">No grouped changes were detected.</p>"
    rows: list[str] = []
    for area in areas:
        files = area.get("files", [])
        if not isinstance(files, list):
            continue
        rows.append(
            "<li><strong>{name}</strong><br><span class=\"muted-note\">{count} file(s)</span></li>".format(
                name=escape(str(area["name"])),
                count=len(files),
            )
        )
    return "<ul>{}</ul>".format("".join(rows))


def display_review_pages(review_pages: list[str]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for raw_path in review_pages:
        path = Path(raw_path)
        name = path.stem if path.suffix else path.name
        if name == "index" and len(path.parts) >= 2:
            name = path.parts[-2]
        tokens = [token for token in name.replace("-", "_").split("_") if token]
        if not tokens:
            label = raw_path
        else:
            head = []
            tail = []
            for token in tokens:
                if token.isdigit() and not tail:
                    head.append(token)
                else:
                    tail.append(token.upper() if token.isupper() else token.capitalize())
            label = " ".join(head + tail).strip()
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def report_link_cards(prefix: str = "./changes/") -> list[dict[str, str]]:
    return [
        {
            "title": "页面差异",
            "href": f"{prefix}report-pages.html",
            "description": "先看哪些页面或章节被改动，最适合设计同事快速判断要不要细看。",
        },
        {
            "title": "字段差异",
            "href": f"{prefix}report-fields.html",
            "description": "看参数、字段和文案级变化，适合确认规格、术语和局部内容调整。",
        },
        {
            "title": "文件差异",
            "href": f"{prefix}report-files.html",
            "description": "面向维护人，保留原始文件级视角，适合追查变更来源。",
        },
        {
            "title": "汇总总览",
            "href": f"{prefix}report-index.html",
            "description": "查看完整 diff-report 导航页，适合需要逐项深挖时再打开。",
        },
    ]


def render_report_cards(cards: list[dict[str, str]]) -> str:
    return "".join(
        "<a class=\"report-card\" href=\"{href}\">"
        "<span class=\"report-kicker\">Change report</span>"
        "<strong>{title}</strong>"
        "<span>{description}</span>"
        "</a>".format(
            href=escape(card["href"]),
            title=escape(card["title"]),
            description=escape(card["description"]),
        )
        for card in cards
    )


def page_title(model: str, region: str) -> str:
    return f"{model} / {region} Review Preview"


def base_css() -> str:
    return """
:root {
  --bg: #f4efe6;
  --panel: #fffdfa;
  --panel-strong: #fff7ea;
  --ink: #1d2733;
  --muted: #5e6d7a;
  --line: #d8ccbb;
  --accent: #1c4cff;
  --accent-soft: #e8efff;
  --accent-ink: #11318e;
  --signal: #b65c18;
  --signal-soft: #fff1e5;
  --success: #1f845a;
  --success-soft: #e7f6ee;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "Noto Sans SC", "Noto Sans", sans-serif;
  background:
    radial-gradient(circle at top right, rgba(28,76,255,0.12), transparent 26%),
    radial-gradient(circle at top left, rgba(182,92,24,0.08), transparent 22%),
    linear-gradient(180deg, #f7f2e8 0%, #efe6d7 100%);
  color: var(--ink);
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 36px 24px 56px;
}
.hero {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 28px;
  box-shadow: 0 20px 50px rgba(31, 41, 51, 0.08);
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
  gap: 22px;
}
.eyebrow {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--signal-soft);
  color: var(--signal);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 {
  margin: 14px 0 10px;
  font-family: "Aptos Display", "Trebuchet MS", "Segoe UI", sans-serif;
  font-size: 44px;
  line-height: 1.1;
}
.lede {
  margin: 0;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.7;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
  margin-top: 22px;
}
.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 18px 20px;
}
.card h2, .card h3 {
  margin: 0 0 12px;
}
.card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.65;
}
.card ul {
  margin: 0;
  padding-left: 20px;
}
.card li + li {
  margin-top: 8px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 22px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 190px;
  padding: 13px 18px;
  border-radius: 999px;
  font-weight: 700;
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
.button.ghost {
  background: transparent;
  color: var(--accent-ink);
  border-color: rgba(17, 49, 142, 0.24);
}
.guide-panel {
  background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(255,247,234,0.96));
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 22px;
}
.guide-panel h2 {
  margin: 0 0 12px;
  font-size: 22px;
}
.step-list {
  margin: 0;
  padding-left: 20px;
}
.step-list li {
  color: var(--muted);
  line-height: 1.7;
}
.step-list li + li {
  margin-top: 10px;
}
.status-banner {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.7);
}
.status-banner strong {
  display: block;
  margin-bottom: 4px;
}
.status-banner.success {
  background: var(--success-soft);
  border-color: rgba(31, 132, 90, 0.18);
}
.status-banner.signal {
  background: var(--signal-soft);
  border-color: rgba(182, 92, 24, 0.18);
}
.status-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  flex: 0 0 auto;
}
.status-banner.success .status-icon {
  background: rgba(31, 132, 90, 0.14);
  color: var(--success);
}
.status-banner.signal .status-icon {
  background: rgba(182, 92, 24, 0.14);
  color: var(--signal);
}
.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 24px;
}
.meta-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255,255,255,0.72);
  border: 1px solid var(--line);
}
.label {
  display: block;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}
.value {
  display: block;
  font-size: 18px;
}
.foot {
  margin-top: 24px;
  color: var(--muted);
  font-size: 14px;
}
.section-title {
  margin: 28px 0 14px;
  font-size: 24px;
}
.section-kicker {
  margin: 0 0 8px;
  color: var(--signal);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.review-card {
  display: block;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 18px 18px 16px;
  box-shadow: 0 10px 24px rgba(31, 41, 51, 0.05);
}
.review-card strong,
.report-card strong {
  display: block;
  margin-bottom: 6px;
  font-size: 18px;
}
.review-card span,
.report-card span {
  color: var(--muted);
  line-height: 1.65;
}
.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.report-card {
  display: block;
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 18px;
}
.report-kicker {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--accent-ink);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.muted-note {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
}
code {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 0.95em;
}
@media (max-width: 900px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
  h1 {
    font-size: 36px;
  }
}
"""


def render_index_html(meta: dict[str, object], changes: dict[str, object]) -> str:
    areas = changes.get("areas", [])
    if not isinstance(areas, list):
        areas = []
    top_pages = changes.get("review_pages", [])
    if not isinstance(top_pages, list):
        top_pages = []
    changed_files = changes.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = []
    review_labels = display_review_pages([str(item) for item in top_pages])
    cards = report_link_cards()
    status_title = "本轮包含页面级改动"
    status_body = "建议先看“页面差异”，确认受影响章节，再打开完整 HTML 看最终呈现。"
    status_kind = "success"
    if not review_labels:
        status_title = "本轮没有直接修改 review 页面"
        status_body = "这轮更像流程、文档或配置调整。设计同事可优先看变更说明，再决定是否需要做视觉复核。"
        status_kind = "signal"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(meta['title']))}</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero hero-grid">
      <div>
        <span class="eyebrow">Design Review Hub</span>
        <h1>{escape(str(meta['model']))} / {escape(str(meta['region']))} 设计评审入口</h1>
        <p class="lede">先看最终页面效果，再看这轮改动说明。这个入口页是给设计同事快速判断“该看什么、这轮改了哪里”用的，不需要先理解源码结构。</p>
        <div class="actions">
          <a class="button primary" href="./manual/index.html">先看页面效果</a>
          <a class="button secondary" href="./changes/index.html">再看本轮改动</a>
          <a class="button ghost" href="./changes/report-pages.html">直接看页面差异</a>
        </div>
        <div class="status-banner {status_kind}">
          <span class="status-icon">i</span>
          <div>
            <strong>{escape(status_title)}</strong>
            <span>{escape(status_body)}</span>
          </div>
        </div>
      </div>
      <aside class="guide-panel">
        <h2>建议评审顺序</h2>
        <ol class="step-list">
          <li>先打开 <strong>页面效果</strong>，确认整体层级、图文比例、告警块和留白节奏。</li>
          <li>再打开 <strong>页面差异</strong>，快速锁定这轮真正变动的章节和页面。</li>
          <li>如果涉及规格或术语，再补看 <strong>字段差异</strong>，避免只看版式漏掉关键内容变化。</li>
        </ol>
      </aside>
      <div class="meta">
        <div class="meta-item"><span class="label">目标手册</span><strong class="value">{escape(str(meta['model']))} / {escape(str(meta['region']))}</strong></div>
        <div class="meta-item"><span class="label">页面改动数</span><strong class="value">{len(review_labels)}</strong></div>
        <div class="meta-item"><span class="label">文件改动数</span><strong class="value">{len(changed_files)}</strong></div>
        <div class="meta-item"><span class="label">变更类别数</span><strong class="value">{len(areas)}</strong></div>
        <div class="meta-item"><span class="label">版本标识</span><strong class="value"><code>{escape(str(meta['commit_sha_short']))}</code></strong></div>
        <div class="meta-item"><span class="label">生成时间</span><strong class="value">{escape(str(meta['generated_at']))}</strong></div>
      </div>
      <p class="foot">Branch: <code>{escape(str(meta['branch']))}</code> | Commit message: <code>{escape(str(meta['commit_message']))}</code></p>
    </section>

    <p class="section-kicker">Start here</p>
    <h2 class="section-title">设计同事先看这三块</h2>
    <section class="review-grid">
      <a class="review-card" href="./manual/index.html">
        <strong>完整页面效果</strong>
        <span>看最终渲染后的页面层级、排版节奏、图片关系和整页观感。</span>
      </a>
      <a class="review-card" href="./changes/report-pages.html">
        <strong>页面差异</strong>
        <span>快速确认这轮到底改了哪些页面、章节或段落，适合先筛选范围。</span>
      </a>
      <a class="review-card" href="./changes/report-fields.html">
        <strong>字段差异</strong>
        <span>当页面改动牵涉规格、文案或数据字段时，从这里看最直接。</span>
      </a>
    </section>

    <p class="section-kicker">This round</p>
    <h2 class="section-title">本轮重点</h2>
    <section class="grid">
      <article class="card">
        <h2>受影响页面</h2>
        <ul>{render_list(review_labels)}</ul>
      </article>
      <article class="card">
        <h2>设计关注点</h2>
        <ul>
          <li>页面结构和信息层级是否仍然清晰。</li>
          <li>警示块、图标、图片和正文是否仍然协调。</li>
          <li>改动页面之间的排版语言是否保持一致。</li>
          <li>若涉及规格或术语变化，再补看字段差异。</li>
        </ul>
      </article>
    </section>

    <p class="section-kicker">Reports</p>
    <h2 class="section-title">变更入口</h2>
    <section class="report-grid">
      {render_report_cards(cards)}
    </section>

    <p class="section-kicker">Technical context</p>
    <h2 class="section-title">技术参考</h2>
    <section class="grid">
      <article class="card">
        <h2>变更类别</h2>
        {render_area_list([item for item in areas if isinstance(item, dict)])}
      </article>
      <article class="card">
        <h2>改动文件</h2>
        <ul>{render_list([str(item) for item in changed_files[:12]])}</ul>
        <p class="muted-note">这块更偏维护视角，设计同事通常只需要确认受影响页面和差异入口即可。</p>
      </article>
    </section>
  </main>
</body>
</html>
"""


def render_changes_html(meta: dict[str, object], changes: dict[str, object]) -> str:
    areas = changes.get("areas", [])
    if not isinstance(areas, list):
        areas = []
    review_pages = changes.get("review_pages", [])
    if not isinstance(review_pages, list):
        review_pages = []
    review_labels = display_review_pages([str(item) for item in review_pages])
    reports = changes.get("report_files", {})
    if not isinstance(reports, dict):
        reports = {}
    report_cards = []
    for label, target, description in (
        ("页面差异", reports.get("report-pages.html"), "先看这一轮改了哪些页面或章节。"),
        ("字段差异", reports.get("report-fields.html"), "规格、术语、字段内容变化优先看这里。"),
        ("文件差异", reports.get("report-files.html"), "需要追文件来源时再打开。"),
        ("汇总总览", reports.get("report-index.html"), "完整 diff-report 导航。"),
        ("原始摘要", reports.get("report-summary.html"), "保留系统生成的原始摘要页。"),
    ):
        if target:
            report_cards.append(
                {
                    "title": label,
                    "href": f"./{target}",
                    "description": description,
                }
            )
    status_title = "这轮没有直接改动 review 页面"
    status_body = "如果你只关心版面变化，可以先看页面差异；若页面差异为空，这轮大概率是流程或文档调整。"
    status_kind = "signal"
    if review_labels:
        status_title = "这轮包含页面级调整"
        status_body = "建议先打开页面差异，再回到完整 HTML 查看修改后的最终效果。"
        status_kind = "success"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(meta['title']))} - Changes</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Change Report</span>
      <h1>{escape(str(meta['model']))} / {escape(str(meta['region']))} 本轮改动说明</h1>
      <p class="lede">先用这里判断这轮具体动了哪些页面、字段和文件，再决定要不要逐页看完整 HTML。</p>
      <div class="actions">
        <a class="button primary" href="../manual/index.html">打开完整页面</a>
        <a class="button secondary" href="../index.html">返回入口页</a>
      </div>
      <div class="status-banner {status_kind}">
        <span class="status-icon">i</span>
        <div>
          <strong>{escape(status_title)}</strong>
          <span>{escape(status_body)}</span>
        </div>
      </div>
    </section>

    <p class="section-kicker">Diff shortcuts</p>
    <h2 class="section-title">先从哪类差异开始看</h2>
    <section class="report-grid">
      {render_report_cards(report_cards)}
    </section>

    <p class="section-kicker">This round</p>
    <h2 class="section-title">本轮改动范围</h2>
    <section class="grid">
      <article class="card">
        <h2>受影响页面</h2>
        <ul>{render_list(review_labels)}</ul>
      </article>
      <article class="card">
        <h2>变更类别</h2>
        {render_area_list([item for item in areas if isinstance(item, dict)])}
      </article>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    config_path = resolve_path(args.config)
    tracked_root = resolve_path(args.tracked_root) if args.tracked_root else ROOT / "docs" / "_review" / args.model / args.region
    tracked_root = tracked_root.resolve()
    output_dir = resolve_path(args.output_dir)
    html_root = ROOT / "docs" / "_build" / args.model / args.region / "html"
    report_root = ROOT / "reports" / "version_tracking" / args.model / args.region

    if args.source == "review" and not tracked_root.exists():
        raise FileNotFoundError(f"Review root not found: {tracked_root}")

    if not args.skip_build:
        cmd = [
            sys.executable,
            str(ROOT / "build.py"),
            "html",
            "--config",
            str(config_path),
            "--model",
            args.model,
            "--region",
            args.region,
            "--source",
            args.source,
        ]
        if not args.clean_build:
            cmd.append("--no-clean")
        run(cmd)

    if not html_root.exists():
        raise FileNotFoundError(f"HTML output not found: {html_root}")

    if not args.skip_diff:
        cmd = [
            sys.executable,
            str(ROOT / "build.py"),
            "diff-report",
            "--config",
            str(config_path),
            "--model",
            args.model,
            "--region",
            args.region,
            "--tracked-root",
            str(tracked_root),
            "--from-ref",
            args.from_ref,
            "--to-ref",
            args.to_ref,
        ]
        run(cmd)

    prefix = latest_report_prefix(report_root)
    changed_files = collect_changed_files(args.from_ref, args.to_ref)
    review_pages = [
        path.removeprefix(f"docs/_review/{args.model}/{args.region}/")
        for path in changed_files
        if path.startswith(f"docs/_review/{args.model}/{args.region}/page/")
        or path.startswith(f"docs/_review/{args.model}/{args.region}/generated/")
    ]
    areas = classify_changes(changed_files, args.model, args.region)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    manual_dir = output_dir / "manual"
    changes_dir = output_dir / "changes"
    generated_dir = output_dir / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_tree(html_root, manual_dir)
    report_files = copy_report_set(report_root, prefix, changes_dir)

    commit_sha = git_value("VERCEL_GIT_COMMIT_SHA", ["git", "rev-parse", "HEAD"])
    commit_message = git_value("VERCEL_GIT_COMMIT_MESSAGE", ["git", "log", "-1", "--pretty=%s"])
    branch = git_value("VERCEL_GIT_COMMIT_REF", ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    author = git_value("VERCEL_GIT_COMMIT_AUTHOR_NAME", ["git", "log", "-1", "--pretty=%an"])
    pr_id = os.environ.get("VERCEL_GIT_PULL_REQUEST_ID", "").strip()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    meta = {
        "title": page_title(args.model, args.region),
        "model": args.model,
        "region": args.region,
        "source": args.source,
        "config": str(config_path.relative_to(ROOT)),
        "tracked_root": str(tracked_root.relative_to(ROOT)),
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_sha_short": commit_sha[:7],
        "commit_message": commit_message,
        "author": author,
        "pr_id": pr_id,
        "generated_at": generated_at,
        "vercel_env": os.environ.get("VERCEL_ENV", "").strip(),
        "vercel_url": os.environ.get("VERCEL_URL", "").strip(),
    }
    changes = {
        "from_ref": args.from_ref,
        "to_ref": args.to_ref,
        "changed_files": changed_files,
        "review_pages": review_pages,
        "areas": areas,
        "report_prefix": prefix,
        "report_files": report_files,
    }

    write_json(generated_dir / "meta.json", meta)
    write_json(generated_dir / "changes.json", changes)
    (output_dir / "index.html").write_text(render_index_html(meta, changes), encoding="utf-8")
    (changes_dir / "index.html").write_text(render_changes_html(meta, changes), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
