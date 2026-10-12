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
