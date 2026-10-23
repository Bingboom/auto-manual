# Pitfalls seen in practice

| Symptom | Cause | Fix |
| --- | --- | --- |
| LCD icon column empty in screenshots | `loading="lazy"` images off-screen | force `loading=eager` before screenshots (render_check.cjs does) |
| "No JP term" but the manual has it | sentence pool dropped short labels | keep strings ≥2 chars (「認証：」) and grep labels too |
| TM query script fails | needs lark-cli config / base binding | dump TM tables via `feishu_api.py bitable-dump` |
| Whole groups judged "missing" | unit extractor skipped inline text in `<div>/<strong>/td` with nested blocks | use `extract_units.py` (own inline text per block) and check coverage first |
| Agent marks image labels missing | labels live inside the US screenshot figure | override as covered "图中英文标注，重绘时需日文化" |
| H1/band text invisible after restyle | overlay `color: inherit` on `.jp-original` beats `#furo-main-content h1` | force white on dark headings |
| 使用上のご注意 bar missing | reference page styles it via inline `style` attributes | mirror the inline styles in the overlay |
| Warranty tab covers first line | Chinese gloss wraps inside the absolute tab | gloss inline, `flex-basis:auto` |
| Duplicate symbol text | name vs meaning compared before stripping the gloss | strip `.zh-translation` first |
| Right-view figure inside the front-view table | malformed earlier draft markup | rebuild product-overview tables per view |
| Spec numbers mistaken as translation | spec values were green in an older round | values inside Japanese are black; green is only English to translate |
| US value leaks into JP text | convenience fill | US values only in orange notes; JP text uses JP spec values or magenta TBC |
| New Japanese term proposed as final | no corpus term | US English label + optional candidate in an orange note |
| Two US spec chapters counted twice | annex reprints the main spec table | list annex ids in `duplicates.json` |
| LCD table mixes 「オン／オフ」 and 「点灯時／消灯時」 | the shared LCD icons source table is itself mixed (JPD-01) | write 点灯時／点滅時／消灯時 in the draft; see `source-data-debt.md` |
| Word count jumps after a recount | recounting from `data-previous-english` brings back numbers the earlier rounds left out, or overwrites rows that were adjusted by hand | `count_translation.py --previous <last dir>` carries unchanged units forward; only units added, removed or re-sourced move the totals |
| `rep()` assertion fails on the second run of a step | the anchor also matches text in your own review note or change log | anchor on markup next to the text (`</span>`, a class) or a phrase the notes never quote |
| Anchor not found although the text is on screen | a review note or gloss sits between the parts you joined (you printed the cell with `.jp-review` removed) | read the raw HTML around the anchor before writing the replacement |
| A derived value turns out wrong | the draft filled a number R&D never gave (e.g. MTS output = one L14-30R = 4000W) | write only what R&D stated; keep the derivation as a question in the appendix |
| Spec label copied with a typo | the repo's JE-1000F JP Web package has 「バススルー」 in the input-port cell (JPD-03) | take spec labels from the JE-1000F PDF or TM, and grep the term in `data/terminology_rules.csv` |
| `Cannot find module 'playwright'` / no Python Playwright | only the global Node package is installed | run the bundled `.cjs` scripts as `NODE_PATH="$(npm root -g)" node scripts/render_check.cjs …` |

## RTD moved to the private Read the Docs domain (2026-10)

Since main #1514 / #1520 the manuals live under `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/<MODEL>/<REGION>/<lang>/md/...`;
the old `ht-doc.readthedocs.io` paths answer 404. Some cloud environments' network
policy does not allow the new host (proxy answers 403 to CONNECT): ask the operator
to add it under the environment's allowed domains, and meanwhile use the reviewed
JP packages in the repo (`data/manual_sources/<MODEL>/JP/*-reviewed/web/ja/*.md`)
via `jp_corpus.py pool --extra ...` or a previously fetched copy.

