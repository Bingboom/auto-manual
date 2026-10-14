# JP web-manual styling

Reference page: `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-1000F/JP/ja/md/manual_je1000f_jp.html`.
Shared components (H1 dark bar, ● H2, spec tables, callout tables, warranty
cards, LCD and troubleshooting tables) come from `_static/web_manual.css`, which
the draft links as `assets/source-manual.css`. JP-only components (safety band,
signal table, symbol/warning panels, inbox cards, usage heading) are inline
`<style>` blocks of the reference page — `scripts/fetch_jp_style.py` saves them as
`assets/jp-style/jp-manual-components.css`. Link order: source-manual.css →
jp-manual-components.css → manual-locales.css → review-overlay.css; remove the
draft's older inline review styles (they override the manual look).

## Component mapping

| Draft content | JP manual markup |
| --- | --- |
| chapter `section > h1` | unchanged — web_manual.css draws the bar |
| safety lead sentence | `p.jp-safety-lead` |
| 絵表示について / 絵表示の説明 | `h2.jp-safety-band` (pill) |
| 表示/意味 signal table | `div.jp-signal-wrap > table.jp-signal-table`, rows `th` (svg alert icon for 警告/注意 + `<strong>`) + `td` |
| symbol meanings (move the separate 絵表示の説明 chapter into safety) | `div.jp-symbol-grid` with two `table.jp-symbol-panel` (icon td + text td); recycling rows in `div.jp-symbol-grid.jp-recycling-grid#jp-recycling` |
| 警告 / 注意 headings | `h2.jp-warning-heading` = svg alert icon + label |
| warning cards | `div.jp-symbol-grid.jp-warning-grid` of two `table.jp-symbol-panel` |
| 万が一…異常 block | second `h2.jp-warning-heading` 警告 + `table.jp-symbol-panel.jp-safety-detail`, first row `td.jp-safety-copy.jp-safety-split` with `div.jp-safety-cell-section`s and `ul.jp-emergency-list` |
| 注意 list | `table.jp-symbol-panel.jp-safety-detail`, prohibition icon per row |
| 使用上のご注意 | `h2.jp-usage-heading` + first paragraph in `div.jp-usage-intro` |
| 同梱品 | `div.jp-inbox-grid > figure.jp-inbox-card` (`span.jp-inbox-number`, `div.jp-inbox-art`, figcaption), notes `div.jp-inbox-notes`, `p.jp-inbox-disclaimer` "■ <strong>…</strong>" |
| spec groups | `section > h2` + `figure.hb-spec-table-composition > table.hb-spec-table.manual-table.manual-spec-table` with `th.hb-spec-label.manual-spec-label` / `td.hb-spec-value.manual-spec-value` |
| other grid tables | wrapper `hb-spec-table-composition jp-grid-composition`, table `hb-spec-table manual-table jp-grid-table` |
| warranty | intro `figure.hb-warranty-intro-composition` (`hb-warranty-intro-panel` + `hb-warranty-local-note`); each H2 run nested as `section > h2 + figure.hb-warranty-card` |
| CAUTION/NOTE boxes | `table.manual-callout-table > tr > td.manual-callout-label + td.manual-callout-body` |
| page head | `nav.manual-locale-nav` "<MODEL> · JP" |

Worked transformation: `examples/jhp3600c/make_v018.py`.

## Overlay rules that are easy to get wrong

- A generic `.jp-original { color: inherit }` turns white text on the dark H1 /
  band / warranty tab dark → force `#fff` on those headings (see the end of
  `assets/review-overlay.css`).
- `jp-usage-heading` and `jp-safety-band` get their dark fill from **inline
  style attributes** on the reference page; mirror them in the overlay.
- Chinese gloss inside the absolutely positioned warranty tab must stay inline
  (`flex-basis:auto`) or the tab grows and covers the card's first line.
- H2 is `display:flex` in web_manual.css: give the gloss `flex-basis:100%` and a
  left indent so it sits under the title.
- Provide toolbar toggles: 强调玫红差异 (`only-changes`), 中文审阅 (`hide-notes`),
  中文对照 (`hide-zh`) so reviewers can view the pure JP layout.
