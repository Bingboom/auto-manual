from __future__ import annotations

import argparse
import json
import os
import re
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


def env_value(env_names: list[str]) -> str:
    for env_name in env_names:
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return ""


def git_value(env_names: list[str], fallback_cmd: list[str]) -> str:
    value = env_value(env_names)
    if value:
        return value
    return capture(fallback_cmd)


def github_pull_request_id() -> str:
    explicit = env_value(["VERCEL_GIT_PULL_REQUEST_ID"])
    if explicit:
        return explicit

    github_ref = os.environ.get("GITHUB_REF", "").strip()
    match = re.fullmatch(r"refs/pull/(\d+)/(?:head|merge)", github_ref)
    if match:
        return match.group(1)
    return ""


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


def page_title(model: str, region: str) -> str:
    return f"{model} / {region} Review Preview"


def base_css() -> str:
    return """
:root {
  --bg: #f5f1e8;
  --panel: #fffdf8;
  --ink: #1f2933;
  --muted: #52606d;
  --line: #d9d1c3;
  --accent: #1f5eff;
  --accent-soft: #e8efff;
  --success: #1f845a;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "Noto Sans", sans-serif;
  background:
    radial-gradient(circle at top right, rgba(31,94,255,0.08), transparent 28%),
    linear-gradient(180deg, #f7f3ea 0%, #efe8db 100%);
  color: var(--ink);
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.shell {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.hero {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 16px 40px rgba(31, 41, 51, 0.08);
}
.eyebrow {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 {
  margin: 14px 0 10px;
  font-size: 40px;
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
  border-radius: 20px;
  padding: 18px 20px;
}
.card h2, .card h3 {
  margin: 0 0 12px;
}
.card ul {
  margin: 0;
  padding-left: 20px;
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
  min-width: 180px;
  padding: 12px 18px;
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
.foot {
  margin-top: 24px;
  color: var(--muted);
  font-size: 14px;
}
code {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 0.95em;
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
    <section class="hero">
      <span class="eyebrow">Review Preview</span>
      <h1>{escape(str(meta['title']))}</h1>
      <p class="lede">Share the current review-stage manual with design and pair it with the exact diff-report set for this round.</p>
      <div class="actions">
        <a class="button primary" href="./manual/index.html">Open Review HTML</a>
        <a class="button secondary" href="./changes/index.html">Open Change Report</a>
      </div>
      <div class="meta">
        <div class="meta-item"><span class="label">Model</span><strong>{escape(str(meta['model']))}</strong></div>
        <div class="meta-item"><span class="label">Region</span><strong>{escape(str(meta['region']))}</strong></div>
        <div class="meta-item"><span class="label">Source</span><strong>{escape(str(meta['source']))}</strong></div>
        <div class="meta-item"><span class="label">Branch</span><strong>{escape(str(meta['branch']))}</strong></div>
        <div class="meta-item"><span class="label">Commit</span><strong><code>{escape(str(meta['commit_sha_short']))}</code></strong></div>
        <div class="meta-item"><span class="label">Generated</span><strong>{escape(str(meta['generated_at']))}</strong></div>
      </div>
      <p class="foot">Commit message: <code>{escape(str(meta['commit_message']))}</code></p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Review Pages Touched</h2>
        <ul>{render_list([str(item) for item in top_pages])}</ul>
      </article>
      <article class="card">
        <h2>Changed Files</h2>
        <ul>{render_list([str(item) for item in changed_files[:12]])}</ul>
      </article>
    </section>

    <section class="grid">
      {render_areas([item for item in areas if isinstance(item, dict)])}
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
    reports = changes.get("report_files", {})
    if not isinstance(reports, dict):
        reports = {}
    report_links = []
    for label, target in (
        ("Report overview", reports.get("report-index.html")),
        ("Field diff", reports.get("report-fields.html")),
        ("Page diff", reports.get("report-pages.html")),
        ("File diff", reports.get("report-files.html")),
        ("Raw summary", reports.get("report-summary.html")),
    ):
        if target:
            report_links.append(f"<li><a href=\"./{escape(str(target))}\">{escape(label)}</a></li>")
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
      <h1>{escape(str(meta['title']))}</h1>
      <p class="lede">Use this page to brief design on what changed in the current review round before they open the rendered manual.</p>
      <div class="actions">
        <a class="button primary" href="../manual/index.html">Open Review HTML</a>
        <a class="button secondary" href="../index.html">Back To Summary</a>
      </div>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Diff Links</h2>
        <ul>{''.join(report_links) or '<li>No diff-report html files were copied.</li>'}</ul>
      </article>
      <article class="card">
        <h2>Review Pages Touched</h2>
        <ul>{render_list([str(item) for item in review_pages])}</ul>
      </article>
    </section>

    <section class="grid">
      {render_areas([item for item in areas if isinstance(item, dict)])}
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

    commit_sha = git_value(["VERCEL_GIT_COMMIT_SHA", "GITHUB_SHA"], ["git", "rev-parse", "HEAD"])
    commit_message = git_value(["VERCEL_GIT_COMMIT_MESSAGE"], ["git", "log", "-1", "--pretty=%s"])
    branch = git_value(["VERCEL_GIT_COMMIT_REF", "GITHUB_HEAD_REF", "GITHUB_REF_NAME"], ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    author = git_value(["VERCEL_GIT_COMMIT_AUTHOR_NAME"], ["git", "log", "-1", "--pretty=%an"])
    pr_id = github_pull_request_id()
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
