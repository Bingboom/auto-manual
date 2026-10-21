# JE-1500D JP V2 native Web source

The operator supplied the Japanese **Jackery ポータブル電源 1500 New** PDF and requested Git-only conversion through publication on 2026-10-19, with the existing JE-1000F JP manual as the structural reference (MA-322). The cover and specification table identify **JE-1500D**, V2, Japan only. The original 27-page PDF has SHA-256 `6ddeef548ccf8552185ffd300a7222df849e7ac8f5e16bdc67fd081a976862e6`.

- Web body: physical pages 3–26; printed cover, TOC and back cover remain in the original archive.
- `source/native_pages.json` and `source/text_selections.json` retain the positioned source text and disposition of every native line; `source/unassigned_text.json` must be empty.
- `source/outlined_recoveries.json` holds manually checked transcriptions with physical coordinates and source pixel hashes for outlined precautions/disclaimer text and the distinct 12V vehicle input/output warnings. These are original-source recoveries, not new wording.
- `source/ja/content.json` binds shared ComponentSpecs. Prose, warnings, symbols, specifications, LCD descriptions, LCD mode actions, button combinations, troubleshooting and warranty stay native HTML. Target-specific overview, operation, charging and App artwork retains complete panels/phone frames. Embedded artwork captions remain in searchable source/IR and image accessibility text; body/table screenshots are not used.
- `source/asset_decisions.json` inventories the JE-1000F JP reference and shared candidates before extraction. Shared LCD/button bytes are unchanged. The 12 source symbols are independently matched against native glyphs; six existing variants match, while six native variants preserve the source glyph shape/tint as additions to the shared catalog. No existing shared bytes are replaced.
- `source/geometry.css` contains only geometry for readable diagram panning; shared theme/component contracts own presentation.
- The structure follows JE-1000F JP; all model facts and product-specific art come from JE-1500D; matching shared art is reused. There is no inherited emergency-charge button shortcut, expansion pack chapter or auto-resume feature absent from this source.

Source wording is retained, including the 5 cm general ventilation guidance versus the 30 cm F6 remedy, the printed “主電源ボタン/オフ”, “充電速度限制”, “出カポート”, two temperature entries sharing LCD number 20, and the three AC ports/two simultaneously used wording. These are source statements, not conversion corrections. Source US/EU data and other models are not imported.

Replay from repository root into an unused directory:

```bash
python3 manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/rebuild.py --output tmp/je1500d-replay
python3 -m sphinx -W -b html tmp/je1500d-replay tmp/je1500d-html
```

`source_manifest.json` pins input and repository dependencies. Git-only scope excludes Feishu/Base, queue, source-table, online asset/catalog and HTML_link writes. Release evidence is sealed at the actual committed source ref; engineering merge, RTD deployment and live browser acceptance are checked separately.

Validation boundary: the v7 full-body desktop/mobile browser preflight passed. The final complete-panel/outlined-copy patch passes static source, fresh symbol/style admission, cold-replay byte parity and strict Sphinx checks; a fresh browser attempt was refused because the administrator-policy verification service was unavailable. Neither that refusal nor a publication merge proves live visual acceptance.
