# JBP-3600A EU native-language intake candidates

English is already published at engineering commit `565c52a2d450d2b353e0186b22d0b230a2fb13ee` (PR1404), Hello-Docs PR170 and RTD34910454. These eight native packages are local review candidates. They do not authorize another release or promote an English baseline.

Source: `HTP011-EU-9国语言-0924.ai`,79 PDF-compatible pages, SHA256 `8c6c25ddbc885b8e186b3b643fb53677a383ddf22295b3a2ba689c4d5d8cf8d1`. Native bodies: FR15–22, ES23–30, DE31–38, IT39–46, UK47–54, PT55–62, NL63–70, PL71–78. `uk` is Ukrainian. Frontmatter FR/ES/DE/IT is on page2; UK/PT/NL/PL is on page3. Shared legal/manufacturer page79 remains English as in the original.

## Current fixed candidates

| Language | Preview | Fixed files | Independent content/layout review |
| --- | --- | --- | --- |
| fr | [fr-r4](http://127.0.0.1:56059/fr-r4/manual_jbp3600a_eu_fr.html) | [package](web/fr-r4/manual.ir.json) / [evidence](review/fr-r4/review-ledger.json) | [PASS](review/fr-r4-independent/acceptance.md) |
| es | [es-r2](http://127.0.0.1:56059/es-r2/manual_jbp3600a_eu_es.html) | [package](web/es-r2/manual.ir.json) / [evidence](review/es-r2/review-ledger.json) | [PASS](review/es-r2-independent/acceptance.md) |
| de | [de-r1](http://127.0.0.1:56059/de-r1/manual_jbp3600a_eu_de.html) | [package](web/de-r1/manual.ir.json) / [evidence](review/de-r1/review-ledger.json) | [PASS](review/de-r1-independent/acceptance.md) |
| it | [it-r1](http://127.0.0.1:56059/it-r1/manual_jbp3600a_eu_it.html) | [package](web/it-r1/manual.ir.json) / [evidence](review/it-r1/review-ledger.json) | Pending |
| uk | [uk-r1](http://127.0.0.1:56059/uk-r1/manual_jbp3600a_eu_uk.html) | [package](web/uk-r1/manual.ir.json) / [evidence](review/uk-r1/review-ledger.json) | Pending |
| pt | [pt-r1](http://127.0.0.1:56059/pt-r1/manual_jbp3600a_eu_pt.html) | [package](web/pt-r1/manual.ir.json) / [evidence](review/pt-r1/review-ledger.json) | Pending |
| nl | [nl-r1](http://127.0.0.1:56059/nl-r1/manual_jbp3600a_eu_nl.html) | [package](web/nl-r1/manual.ir.json) / [evidence](review/nl-r1/review-ledger.json) | Pending |
| pl | [pl-r1](http://127.0.0.1:56059/pl-r1/manual_jbp3600a_eu_pl.html) | [package](web/pl-r1/manual.ir.json) / [evidence](review/pl-r1/review-ledger.json) | Pending |

The [review status and full hashes](review-status.json) bind every candidate. The [operator confirmation material](REVIEW.md) separates the English r5 style proposal, native artwork/content exceptions, independent acceptance and publication authority. French r4 remains sealed with its earlier CSS; the other seven use the later candidate CSS. Do not imply that all eight have the same stylesheet baseline.

Each locale has169 explicit source mappings under `copy-maps/`. All packages use the existing prepared-document IR and shared ComponentSpec renderers. Each reuses18 neutral English assets byte-for-byte (including8 symbols), has3 native label-bearing overview/LCD panels and1 shared ×5 inline icon. The icon's [provenance](assets/shared/connection-x5-provenance.json) records vectors and hashes; no asset-registry promotion occurred. Source-page comparisons for the seven later locales are under `review/<language>-source`; French evidence is in its sealed review ledger.

Strict Sphinx, native-copy checks, byte-identical cold replay and desktop1440×1000/mobile390×844 browser checks passed for each fixed package. All22 images decode, LCD stays2×2, the CSS clock shows3s and there is no document horizontal overflow. Native source anomalies remain explicit review items. The structural trial reports9 differences per locale except Italian11 for its extra specification row; stylesheet bytes and all renderer behavior are outside that trial. Its no-issues English applicability comparison is not locale enrollment. Fresh admission remains blocked.

FR r4 independently passed with FR-001/002/003 closed. ES r2 independently passed with ES-001 closed; ES r1 is superseded. DE r1 independently passed content/layout review with its native source anomalies still pending operator decisions. The five other packages await independent review. Independent PASS is not approval of the English baseline, source exceptions, enrollment, merge or publication. Sealed producer ledgers preserve their original historical status; later independent reports are separate records.

Shared logic validation from producer commit5de0abb passed5075 tests with35 skipped;36 targeted tests cover the final opt-in badge marker. This second CSS/native-content batch reuses that evidence and adds per-language browser/build/replay checks, without repeating the full suite. No online source, queue, registry or publication write occurred.

Historical French `web/fr`, `fr-r2`, `fr-r3` and matching reviews, plus superseded ES r1, remain preserved locally. They are not the selected Git review packages.

## Cold replay

Use the repository runtime with `requirements.lock` and a fresh output directory, preserving each sealed package:

```sh
python3 - <<'PY'
from pathlib import Path
from shutil import copytree
from tools.frozen_ai_web import replay_package
source = Path('manual_sources/JBP-3600A/EU/native-0924/web/nl-r1')
target = Path('.tmp/jbp-nl-r1-replay')
copytree(source, target)
replay_package(target)
PY
python3 -m sphinx -b html -W --keep-going .tmp/jbp-nl-r1-replay .tmp/jbp-nl-r1-html
```

The IR's prepared JSON paths identify semantic source pages; replay uses packaged IR/assets without reopening those temporary files. English semantic page IDs remain intentional. The read-only baseline trial used PR1409 head `2edbda652c3ceb9ed26357ab6fb7004337127793` without importing that implementation. Operator baseline approval, reviewed native exceptions/applicability, independent acceptance, and merge/publication remain separate steps.
