# JBP-3600A EU native-language intake candidates

The English release is complete at engineering commit `565c52a2d450d2b353e0186b22d0b230a2fb13ee` (PR1404), Hello-Docs PR170 and RTD34910454. These files are subsequent native-language intake candidates. They do not authorize another release or promote a language baseline.

Source: `HTP011-EU-9国语言-0924.ai`, 79 PDF-compatible pages, SHA256 `8c6c25ddbc885b8e186b3b643fb53677a383ddf22295b3a2ba689c4d5d8cf8d1`. Native bodies: FR15–22, ES23–30, DE31–38, IT39–46, UK47–54, PT55–62, NL63–70, PL71–78. `uk` is Ukrainian. Frontmatter1–6 and shared English legal/manufacturer page79 are separate.

## First review batch: French r4

- [Native positioned copy](source/fr-native-pages.json) and [169 source mappings](copy-maps/fr.json).
- [Portable Web input](web/fr-r4/manual.ir.json), [generated Markdown](web/fr-r4/manual_jbp3600a_eu_fr.md), packaged assets and CSS.
- [Review ledger](review/fr-r4/review-ledger.json), [IR package hashes](review/fr-r4/package-manifest.json), [HTML dependency hashes](review/fr-r4/html-manifest.json), [baseline trial](review/fr-r4/fr-baseline-trial.json), [admission result](web/fr-r4/admission-report.json).
- [Local immutable r4 preview](http://127.0.0.1:56059/fr-r4/manual_jbp3600a_eu_fr.html).

FR uses the final English prepared-document IR structure, the existing ComponentSpec renderers and shared CSS. It reuses18 neutral assets byte-for-byte (including8 shared symbols). Three English label-bearing panels are replaced with source-native French candidates. The missing native ×5 connection badge is restored as a transparent inline asset. Its [provenance](assets/shared/connection-x5-provenance.json) records rejected alternatives, source vectors and hashes; no asset-registry promotion occurred.

Independent review closed FR-001/002 in r2 and requested FR-003 for mobile anchor clearance. The r4 producer checks cover all three findings. FR-001 is corrected in shared frozen MyST replay: styled document headings enter the Sphinx TOC, while component headings remain intact. Published English already had a Markdown specifications heading. FR-002 corrects the shared locking label binding to source dark fill/white foreground and a readable14px minimum mobile badge; it preserves artwork/leader geometry. This is a **proposed English baseline revision**, recorded as a difference from the immutable released English reference. FR-003 uses the existing shared mobile stylesheet to clear Furo's sticky header and its back-to-top control; desktop anchor spacing stays unchanged. No automatic approval or baseline refresh occurs.

The trial reports9 exact differences:3 panel hashes,1 inline-icon carrier addition,4 locking fill/foreground fields and1 Web-contract hash. Those represent5 review decisions (3 panels, inline icon, shared locking revision). The shared mobile CSS revision is recorded separately: the trial does not compare stylesheet bytes or all renderer behavior. The figure inventory is10 slots with zero missing/fallback; that classification alone is not approval. Fresh publication admission remains blocked by pending source review and absent FR applicability enrollment. The English applicability comparison has no component issues, but is a read-only trial, not FR enrollment.

Earlier `web/fr`, `web/fr-r2`, `web/fr-r3` and matching review folders remain preserved locally and are superseded by r4. Only the final r4 package is included in this Git review batch. Full-suite validation passed5075 tests with35 skipped before the final opt-in badge marker;36 targeted tests then passed for that refinement. FR-003 is a CSS-only change with desktop and390px French/English browser evidence. Cold replay and strict Sphinx pass for the sealed r4 package.

ES/DE/IT copy maps and assets are work in progress; UK/PT/NL/PL currently have positioned native source records. Do not publish or treat those as completed language acceptances.

## Cold replay

Use the repository runtime with `requirements.lock`. Work in a new output directory, preserving this candidate:

```sh
python3 - <<'PY'
from pathlib import Path
from shutil import copytree
from tools.frozen_ai_web import replay_package
source = Path('manual_sources/JBP-3600A/EU/native-0924/web/fr-r4')
target = Path('.tmp/jbp-fr-r4-replay')
copytree(source, target)
replay_package(target)
PY
python3 -m sphinx -b html -W --keep-going .tmp/jbp-fr-r4-replay .tmp/jbp-fr-r4-html
```

The prepared JSON paths inside the IR identify semantic source pages; replay uses the packaged IR/assets and does not reopen those temporary files. Native source provenance remains in the copy maps, source receipt and IR manifest. English semantic page IDs are retained intentionally.

The baseline trial was run read-only against PR1409 head `2edbda652c3ceb9ed26357ab6fb7004337127793`, without importing that PR into this branch. Operator baseline approval, reviewed locale exceptions/applicability, independent acceptance, and merge/publication remain separate steps.
