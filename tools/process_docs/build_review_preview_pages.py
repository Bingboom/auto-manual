from __future__ import annotations

from html import escape

from tools.process_docs.build_review_preview_render import (
    base_css,
    build_download_links,
    display_text,
    family_change_title,
    render_areas,
    render_link_list,
    render_list,
    workspace_css,
)


def render_workspace_html(title: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>{escape(title)}</title>\n"
        f"  <style>{workspace_css()}</style>\n"
        "</head>\n"
        "<body>\n"
        "  <main class=\"workspace-shell\">\n"
        "    <div id=\"workspace-app\">Loading review preview...</div>\n"
        "  </main>\n"
        "  <script>\n"
        "const app = document.getElementById('workspace-app');\n"
        "function asArray(value) { return Array.isArray(value) ? value : []; }\n"
        "function normalizeToken(value) { return typeof value === 'string' ? value.trim() : ''; }\n"
        "function valueOr(value, fallback = 'Not available') { const text = normalizeToken(value == null ? '' : String(value)); return text || fallback; }\n"
        "function escapeHtml(value) {\n"
        "  return String(value == null ? '' : value).replace(/[&<>\"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', \"'\": '&#39;' }[char]));\n"
        "}\n"
        "function readQuery() {\n"
        "  const params = new URLSearchParams(window.location.search);\n"
        "  return {\n"
        "    family: normalizeToken(params.get('family')).toUpperCase(),\n"
        "    model: normalizeToken(params.get('model')),\n"
        "    lang: normalizeToken(params.get('lang')).toLowerCase(),\n"
        "  };\n"
        "}\n"
        "function findFamily(workspace, family) {\n"
        "  return asArray(workspace.families).find((item) => normalizeToken(item.family).toUpperCase() === normalizeToken(family).toUpperCase());\n"
        "}\n"
        "function findModel(familyEntry, model) {\n"
        "  return asArray(familyEntry.models).find((item) => normalizeToken(item.model) === normalizeToken(model));\n"
        "}\n"
        "function findLanguage(modelEntry, lang) {\n"
        "  return asArray(modelEntry.languages).find((item) => normalizeToken(item.lang).toLowerCase() === normalizeToken(lang).toLowerCase());\n"
        "}\n"
        "function normalizeSelection(workspace, requested) {\n"
        "  const families = asArray(workspace.families);\n"
        "  if (!families.length) {\n"
        "    throw new Error('No families available in generated/workspace.json.');\n"
        "  }\n"
        "  const defaults = workspace.defaults || {};\n"
        "  const familyEntry = findFamily(workspace, requested.family) || findFamily(workspace, defaults.family) || families[0];\n"
        "  const models = asArray(familyEntry.models);\n"
        "  if (!models.length) {\n"
        "    throw new Error(`No model groups are available for family ${familyEntry.family}.`);\n"
        "  }\n"
        "  const modelEntry = findModel(familyEntry, requested.model) || findModel(familyEntry, defaults.model) || models[0];\n"
        "  const languages = asArray(modelEntry.languages);\n"
        "  if (!languages.length) {\n"
        "    throw new Error(`No languages are available for model ${modelEntry.model}.`);\n"
        "  }\n"
        "  const languageEntry = findLanguage(modelEntry, requested.lang) || findLanguage(modelEntry, defaults.lang) || languages[0];\n"
        "  return {\n"
        "    family: String(familyEntry.family),\n"
        "    model: String(modelEntry.model),\n"
        "    lang: String(languageEntry.lang),\n"
        "    familyEntry,\n"
        "    modelEntry,\n"
        "    languageEntry,\n"
        "  };\n"
        "}\n"
        "function writeUrl(selection, mode) {\n"
        "  const params = new URLSearchParams(window.location.search);\n"
        "  params.set('family', selection.family);\n"
        "  params.set('model', selection.model);\n"
        "  params.set('lang', selection.lang);\n"
        "  const next = `${window.location.pathname}?${params.toString()}`;\n"
        "  const method = mode === 'push' ? 'pushState' : 'replaceState';\n"
        "  window.history[method]({ family: selection.family, model: selection.model, lang: selection.lang }, '', next);\n"
        "}\n"
        "function actionButton(label, href, className, downloadName) {\n"
        "  if (!href) {\n"
        "    return '';\n"
        "  }\n"
        "  const downloadAttr = downloadName ? ` download=\"${escapeHtml(downloadName)}\"` : '';\n"
        "  return `<a class=\"button ${className}\" href=\"${escapeHtml(href)}\"${downloadAttr}>${escapeHtml(label)}</a>`;\n"
        "}\n"
        "function bindEvents(workspace, currentSelection) {\n"
        "  document.querySelectorAll('[data-family-tab]').forEach((button) => {\n"
        "    button.addEventListener('click', () => {\n"
        "      const family = normalizeToken(button.getAttribute('data-family-tab')).toUpperCase();\n"
        "      const familyEntry = findFamily(workspace, family);\n"
        "      if (!familyEntry) {\n"
        "        return;\n"
        "      }\n"
        "      const modelEntry = asArray(familyEntry.models)[0];\n"
        "      const languageEntry = modelEntry && asArray(modelEntry.languages)[0];\n"
        "      if (!modelEntry || !languageEntry) {\n"
        "        return;\n"
        "      }\n"
        "      const selection = normalizeSelection(workspace, { family: familyEntry.family, model: currentSelection.model, lang: currentSelection.lang });\n"
        "      writeUrl(selection, 'push');\n"
        "      render(selection, workspace);\n"
        "    });\n"
        "  });\n"
        "  document.querySelectorAll('[data-model-tab]').forEach((button) => {\n"
        "    button.addEventListener('click', () => {\n"
        "      const model = normalizeToken(button.getAttribute('data-model-tab'));\n"
        "      const selection = normalizeSelection(workspace, { family: currentSelection.family, model, lang: currentSelection.lang });\n"
        "      writeUrl(selection, 'push');\n"
        "      render(selection, workspace);\n"
        "    });\n"
        "  });\n"
        "  document.querySelectorAll('[data-lang-tab]').forEach((button) => {\n"
        "    button.addEventListener('click', () => {\n"
        "      const lang = normalizeToken(button.getAttribute('data-lang-tab')).toLowerCase();\n"
        "      const selection = normalizeSelection(workspace, { family: currentSelection.family, model: currentSelection.model, lang });\n"
        "      writeUrl(selection, 'push');\n"
        "      render(selection, workspace);\n"
        "    });\n"
        "  });\n"
        "}\n"
        "function render(selection, workspace) {\n"
        "  const productName = valueOr(selection.languageEntry.product_name, selection.modelEntry.product_name || selection.model);\n"
        "  const manualTitle = valueOr(selection.languageEntry.manual_title, selection.modelEntry.manual_title || workspace.title);\n"
        "  const familyTabs = asArray(workspace.families).map((familyEntry) => {\n"
        "    const active = familyEntry.family === selection.family;\n"
        "    return `<button type=\"button\" class=\"switch-pill ${active ? 'is-active' : ''}\" data-family-tab=\"${escapeHtml(familyEntry.family)}\">${escapeHtml(familyEntry.family)}</button>`;\n"
        "  }).join('');\n"
        "  const modelTabs = asArray(selection.familyEntry.models).map((modelEntry) => {\n"
        "    const active = modelEntry.model === selection.model;\n"
        "    return `<button type=\"button\" class=\"switch-pill ${active ? 'is-active' : ''}\" data-model-tab=\"${escapeHtml(modelEntry.model)}\">${escapeHtml(modelEntry.model)}</button>`;\n"
        "  }).join('');\n"
        "  const languageTabs = asArray(selection.modelEntry.languages).map((languageEntry) => {\n"
        "    const active = languageEntry.lang === selection.lang;\n"
        "    const label = valueOr(languageEntry.language_label, languageEntry.lang.toUpperCase());\n"
        "    return `<button type=\"button\" class=\"switch-pill ${active ? 'is-active' : ''}\" data-lang-tab=\"${escapeHtml(languageEntry.lang)}\">${escapeHtml(label)}</button>`;\n"
        "  }).join('');\n"
        "  const actions = [\n"
        "    actionButton('Open Review HTML', selection.languageEntry.manual_url, 'primary', ''),\n"
        "    actionButton('Download Word', selection.languageEntry.word_url, 'download', 'review-manual.docx'),\n"
        "    actionButton('Download Change Workbook', selection.modelEntry.change_workbook_url, 'download', 'change-report.xlsx'),\n"
        "  ].join('');\n"
        "  const changeReportLink = selection.modelEntry.change_index_url ? `<a href=\"${escapeHtml(selection.modelEntry.change_index_url)}\">Open Change Report.</a>` : '';\n"
        "  app.innerHTML = `<section class=\"workspace-card\"><div class=\"hero-grid\"><section class=\"hero-copy\"><span class=\"eyebrow\">Review Preview</span><h1>${escapeHtml(selection.model)} Review Preview</h1><p class=\"product-line\">Product Name: ${escapeHtml(productName)}</p><p class=\"lede\">Open the current review HTML, download the Word handoff, and use the change package to brief design on this round.</p><div class=\"actions\">${actions}</div><p class=\"detail-link\">${changeReportLink ? `Need the detailed diff? ${changeReportLink}` : ''}</p></section><aside class=\"identity-card\"><span class=\"label\">Document Identity</span><h2>${escapeHtml(productName)}</h2><p class=\"identity-title\">${escapeHtml(manualTitle)}</p><div class=\"pill-row\"><span class=\"pill\">Model ${escapeHtml(selection.model)}</span><span class=\"pill\">Family ${escapeHtml(selection.family)}</span></div><div class=\"switch-group\"><span class=\"switch-label\">Region</span><div class=\"switch-row\">${familyTabs}</div></div><div class=\"switch-group\"><span class=\"switch-label\">Model</span><div class=\"switch-row\">${modelTabs}</div></div><div class=\"switch-group\"><span class=\"switch-label\">Language</span><div class=\"switch-row\">${languageTabs}</div></div></aside></div></section>`;\n"
        "  document.title = `${selection.model} / ${selection.family} / ${selection.lang.toUpperCase()} Review Preview`;\n"
        "  bindEvents(workspace, selection);\n"
        "}\n"
        "async function boot() {\n"
        "  try {\n"
        "    const response = await fetch('./generated/workspace.json', { cache: 'no-store' });\n"
        "    if (!response.ok) {\n"
        "      throw new Error(`Failed to load generated/workspace.json (${response.status}).`);\n"
        "    }\n"
        "    const workspace = await response.json();\n"
        "    const selection = normalizeSelection(workspace, readQuery());\n"
        "    writeUrl(selection, 'replace');\n"
        "    render(selection, workspace);\n"
        "    window.addEventListener('popstate', () => {\n"
        "      const nextSelection = normalizeSelection(workspace, readQuery());\n"
        "      writeUrl(nextSelection, 'replace');\n"
        "      render(nextSelection, workspace);\n"
        "    });\n"
        "  } catch (error) {\n"
        "    const message = error && error.message ? error.message : 'Unable to load workspace data.';\n"
        "    app.innerHTML = `<section class=\"workspace-card error-card\"><span class=\"eyebrow\">Preview Error</span><h1>Workspace data is not available</h1><p class=\"lede\">${escapeHtml(message)}</p></section>`;\n"
        "  }\n"
        "}\n"
        "boot();\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )


def render_redirect_html(*, title: str, target: str, heading: str, copy: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escape(target)}">
  <title>{escape(title)}</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="redirect-card">
      <span class="eyebrow">Redirecting</span>
      <h1>{escape(heading)}</h1>
      <p class="redirect-copy">{escape(copy)}</p>
      <div class="actions">
        <a class="button primary" href="{escape(target)}">Open default entry</a>
        <a class="button secondary" href="../index.html">Back to workspace</a>
      </div>
    </section>
  </main>
</body>
</html>
"""


def render_model_changes_html(
    meta: dict[str, object],
    family_entry: dict[str, object],
    model_entry: dict[str, object],
    model_changes: dict[str, object],
) -> str:
    family = display_text(family_entry.get("family"))
    model = display_text(model_entry.get("model"), display_text(meta.get("model")))
    default_lang = display_text(model_entry.get("default_lang"), "en").lower()
    manual_url = display_text(model_entry.get("default_manual_url"), "")
    downloads = model_changes.get("downloads", {})
    if not isinstance(downloads, dict):
        downloads = {}
    report_files = model_changes.get("report_files", {})
    if not isinstance(report_files, dict):
        report_files = {}
    areas = model_changes.get("areas", [])
    if not isinstance(areas, list):
        areas = []
    review_pages = model_changes.get("review_pages", [])
    if not isinstance(review_pages, list):
        review_pages = []

    report_links = []
    for label, key in (
        ("Report overview", "report-index.html"),
        ("Field diff", "report-fields.html"),
        ("Page diff", "report-pages.html"),
        ("File diff", "report-files.html"),
        ("Raw summary", "report-summary.html"),
    ):
        target = report_files.get(key)
        if isinstance(target, str):
            report_links.append((label, f"../../{target}"))
    download_links = build_download_links(downloads, prefix="../../")
    workspace_back_link = f"../../index.html?family={escape(family)}&model={escape(model)}&lang={escape(default_lang)}"
    shared_languages = model_entry.get("shared_language_labels", [])
    language_copy = ", ".join(str(item) for item in shared_languages if str(item).strip())
    manual_href = f"../../{manual_url}" if manual_url else "../../manual/index.html"
    workbook_href = downloads.get("change_workbook")
    workbook_button = (
        f'<a class="button download" href="../../{escape(str(workbook_href))}" download="change-report.xlsx">Download Change Workbook</a>'
        if isinstance(workbook_href, str)
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(family_change_title(model, family))}</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">{escape(family)} / {escape(model)} Diff</span>
      <h1>{escape(model)} change report</h1>
      <p class="lede">Use this page to brief design on the packaged diff for {escape(model)} in {escape(family)}. The change report, workbook, and CSV exports are shared across this model's language variants{escape(': ' + language_copy) if language_copy else ''}.</p>
      <div class="pill-row">
        <span class="pill">Model {escape(model)}</span>
        <span class="pill">Family {escape(family)}</span>
        <span class="pill">Diff scope Model-level</span>
      </div>
      <div class="actions">
        <a class="button primary" href="{manual_href}">Open default review HTML</a>
        <a class="button secondary" href="{workspace_back_link}">Back to workspace</a>
        {workbook_button}
      </div>
      <p class="note">Language switching happens in the workspace entry page. The diff package on this page stays shared across the {escape(model)} language set for {escape(family)}.</p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Diff Links</h2>
        <ul>{render_link_list(report_links)}</ul>
      </article>
      <article class="card">
        <h2>Downloads</h2>
        <ul>{render_link_list(download_links)}</ul>
      </article>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Downloadables</h2>
        <ul>{render_link_list(download_links)}</ul>
      </article>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Review Pages Touched</h2>
        <ul>{render_list([str(item) for item in review_pages], "No review pages changed in the selected diff range.")}</ul>
      </article>
      <article class="card">
        <h2>Review Context</h2>
        <p>Open <strong>Field diff</strong> for text or value deltas and <strong>Page diff</strong> for page-level impact. Use the workbook when design needs one offline handoff file for this model.</p>
      </article>
    </section>

    <section class="grid">
      {render_areas([item for item in areas if isinstance(item, dict)])}
    </section>
  </main>
</body>
</html>
"""


def render_family_changes_html(meta: dict[str, object], family_entry: dict[str, object]) -> str:
    family = display_text(family_entry.get("family"))
    cards: list[str] = []
    models = family_entry.get("models", [])
    if not isinstance(models, list):
        models = []
    for model_entry in models:
        if not isinstance(model_entry, dict):
            continue
        model = display_text(model_entry.get("model"))
        language_labels = model_entry.get("shared_language_labels", [])
        if not isinstance(language_labels, list):
            language_labels = []
        languages = ", ".join(str(item) for item in language_labels if str(item).strip())
        default_manual_url = display_text(model_entry.get("default_manual_url"), "")
        change_index_url = display_text(model_entry.get("change_index_url"), "")
        workbook_url = display_text(model_entry.get("change_workbook_url"), "")
        workbook_button = (
            f'<a class="button download" href="../../{escape(workbook_url)}" download="change-report.xlsx">Download workbook</a>'
            if workbook_url
            else ""
        )
        cards.append(
            f"""<article class="card">
        <h2>{escape(model)}</h2>
        <p class="muted">Languages: {escape(languages or "Not available")}</p>
        <div class="actions">
          <a class="button primary" href="../../{escape(change_index_url)}">Open model change report</a>
          <a class="button secondary" href="../../{escape(default_manual_url)}">Open default review HTML</a>
          {workbook_button}
        </div>
      </article>"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(family)} change reports</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">{escape(family)} Family</span>
      <h1>{escape(family)} change reports</h1>
      <p class="lede">Choose the model-specific diff package you want to inspect for {escape(family)}.</p>
      <div class="actions">
        <a class="button secondary" href="../index.html">Back to families</a>
        <a class="button secondary" href="../../index.html">Back to workspace</a>
      </div>
    </section>

    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def render_changes_home_html(meta: dict[str, object], families_payload: list[dict[str, object]]) -> str:
    cards: list[str] = []
    for family_entry in families_payload:
        family = display_text(family_entry.get("family"))
        models = family_entry.get("models", [])
        if not isinstance(models, list):
            models = []
        language_labels = family_entry.get("shared_language_labels", [])
        if not isinstance(language_labels, list):
            language_labels = []
        default_manual_url = display_text(family_entry.get("default_manual_url"), "")
        change_index_url = display_text(family_entry.get("change_index_url"), "")
        model_names = ", ".join(display_text(item.get("model")) for item in models if isinstance(item, dict))
        language_names = ", ".join(str(item) for item in language_labels if str(item).strip())
        cards.append(
            f"""<article class="card">
        <h2>{escape(family)} family</h2>
        <p class="muted">Models: {escape(model_names or display_text(meta.get("model")))}</p>
        <p class="muted">Languages: {escape(language_names or "Not available")}</p>
        <div class="actions">
          <a class="button primary" href="../{escape(change_index_url)}">Open {escape(family)} change report</a>
          <a class="button secondary" href="../{escape(default_manual_url)}">Open default review HTML</a>
        </div>
      </article>"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(display_text(meta.get("model")))} change reports</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Change Reports</span>
      <h1>{escape(display_text(meta.get("model")))} review diff workspace</h1>
      <p class="lede">Choose the family report you want to inspect. Each family keeps its own diff pages, workbook, and CSV exports so region-specific review changes stay easy to trace.</p>
      <div class="pill-row">
        <span class="pill">Families {escape(str(len(families_payload)))}</span>
        <span class="pill">Model {escape(display_text(meta.get("model")))}</span>
      </div>
      <div class="actions">
        <a class="button secondary" href="../index.html">Back to workspace</a>
      </div>
    </section>

    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""
