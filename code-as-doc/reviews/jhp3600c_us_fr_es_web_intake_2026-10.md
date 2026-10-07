# JHP-3600C / US / FR + ES English-baseline extension

Status: done

Boundary: operator-authorized release in progress under MA-262.

## Authority and accepted baseline

The operator requested “继续补法语和西语” after the English Git-only publication. English structure, registered components, shared styles, transparent symbols/buttons and reviewed textless artwork are the accepted baseline. Locale wording, numbers, warnings and legal content come from the same authoritative 97-page PDF (SHA-256 `31fd069216fb282968bf90ba8ef7da0e885a875140667e083bca5cbc9e0122c7`). French body: physical p35–65; Spanish: p66–96. Each language has its own p2 preface region; p97 contact metadata is shared. Engineering baseline: `07859f7eae1fe90b72ee950025b28b12cf2c36ff`.

The task-owned isolated worktree is reused on `feat/web-jhp3600c-us-fr-es`. The branch wrapper refused to switch to main because main belongs to the primary checkout; the new branch was created directly from verified origin/main. Both primary and task-owned tmp/ artifacts are preserved.

## Plan and safety net

1. Record language-native selectable copy and source regions; inspect outlined captions and source tables visually. Map all semantic slots into the confirmed English skeleton.
2. Inventory every consumed English asset first. Reuse symbols, LCD icons, buttons, textless connection/operation drawings and matching English App UI byte-for-byte. Reuse base art with native editable captions. Extract only genuinely language-bearing finished overview panels when no approved textless base exists; no recrop of language-neutral art and no blank text frames in new base artwork.
3. Freeze FR/ES copy and explicit baseline inheritance evidence; use the existing ManualSource, Manual IR, ComponentSpec and frozen replay entrypoints. No new per-model config or alternate renderer.
4. Check source-line coverage, semantic component order/variants, technical values, asset byte identity, deterministic/cold replay, strict Sphinx and desktop/mobile rendering before presenting candidates. English source/output must remain byte-identical.

No live Feishu/source/queue/HTML_link writes, print enrollment, schema/workflow/dependency/public CLI changes, deletion of prior artifacts, merge or publication of these new languages. MA-260 covers the preceding English publication only.

## Discovery

Native page count is confirmed. Source layouts have corresponding chapter/page order, with French/Spanish paragraph wraps, table heights and some page-boundary shifts. Therefore locale copy must be mapped by semantic slot, not blindly by English clip coordinates or filename. Symbols use the approved shared native-v1 variants; statuses retain strong emphasis. Narrow captions must be checked for locale wrapping.

## Validation and candidate evidence

The frozen package is `data/manual_sources/JHP-3600C/US/added-locales/git-20261007-31fd0692/`. Each locale contains source selections, explicit native exceptions, asset reuse decisions, source-local presentation corrections, shared Manual IR, MyST and the Sphinx scaffold. The exact authoritative PDF Git blob is included in this standalone package for source-bound release sealing.

| Acceptance item | French | Spanish |
| --- | --- | --- |
| Chapters / flow nodes | 20 / 230 | 20 / 230 |
| Shared component order and types | Identical to English | Identical to English |
| Component variants | One native signal exception | Identical to English |
| Source coverage | 1263 lines; 17 explicit illustrative exceptions | 1263 lines; 17 explicit illustrative exceptions |
| Assets | 90; 86 byte-identical English reuses / 4 native panels | 90; 86 byte-identical English reuses / 4 native panels |
| Strict Sphinx | Passed | Passed |
| Frozen / independent cold replay | All 96 files byte-identical | All 96 files byte-identical |
| Local resource closure | 102 requests; zero failures | 102 requests; zero failures |
| Spec footnote markers | 12 rendered references | 12 rendered references |
| Browser widths | 1280 desktop / 390 mobile | 1280 desktop / 390 mobile |
| Page horizontal overflow | Zero at both widths | Zero at both widths |
| ReferenceFigure / operation caption overflow | Zero at both widths | Zero at both widths |

The sole component-variant difference is the indoor-use safety signal: English uses `danger`; native French physical p36 uses **AVERTISSEMENT**, so French retains the shared `warning` variant. Chapter IDs, component order and types otherwise match the English baseline. Duplicate warning/tip labels introduced by PDF reading order were removed from body copy while retaining the separate native signal slots. Native paragraph omissions, mixed-language wording, technical values and model spellings are documented in the package README; they were not silently rewritten. French symbol spelling “Mlise en garde!” was visually confirmed against physical p36.

All eleven ReferenceFigures retain native live captions on the approved base artwork. CSS continues to draw blank caption frames. The ATS cable captions now include the complete native wording. Longer operation labels wrap within the shared geometry; native state words remain strong. The battery-placement clearance label uses a slightly wider live-text region to avoid desktop clipping, without changing its base image. Four locale panels differ from English: front overview, side overview, App controls and complete App connection results. Native App results show HomePower3600 Plus rather than the old generic Explorer1000 screenshot; phone frames and UI remain complete.

Browser inspection covered headings/callouts, state labels, battery placement, ATS/MTS connection panels, solar charging and native App panels across the two locales. French ATS and mobile energy-saving panels and Spanish mobile MTS steps were rechecked after the final copy/geometry corrections. DOM measurements confirmed no page or caption overflow, and completed images had no decode failures. Resource closure additionally fetched every page image, script, stylesheet and CSS font/image reference. Wide specification tables retain the shared mobile table behavior. This is local candidate acceptance, not an RTD release receipt or a full editorial approval of the native PDF.

### Reproduction and checks run

From the task-owned worktree, for each `LOCALE` in `fr`, `es`:

```sh
python3 data/manual_sources/JHP-3600C/US/added-locales/git-20261007-31fd0692/rebuild.py --language LOCALE --output tmp/jhp3600c-fr-es/LOCALE-complete
python3 data/manual_sources/JHP-3600C/US/added-locales/git-20261007-31fd0692/validate_source.py --language LOCALE --output tmp/jhp3600c-fr-es/LOCALE-complete
python3 -m sphinx -W --keep-going -b html tmp/jhp3600c-fr-es/LOCALE-complete tmp/jhp3600c-fr-es/site/JHP-3600C/US/LOCALE/md
python3 data/manual_sources/JHP-3600C/US/added-locales/git-20261007-31fd0692/rebuild.py --language LOCALE --output tmp/jhp3600c-fr-es/LOCALE-cold-complete
```

Use unused replay output directories. The task scratch receipt `tmp/jhp3600c-fr-es/final_static_evidence.json` records recursive frozen/cold hash equality, ordered component/variant comparison, unchanged English manifest hashes and resource closure. Its check script is `tmp/jhp3600c-fr-es/final_acceptance.py`; scratch files are preserved and excluded from the commit.

Additional checks: source-package Python Ruff and `python3 -m ruff check build.py integrations tools tests scripts` passed; repository documentation link integrity passed (264 documents, 2566 links, zero broken); staged diff whitespace check passed. No shared renderer/core logic, schema, workflow or dependency changes are included.

The required `python3 -m unittest` run finished with **5210 tests, 1 error, 35 skips**. The unchanged baseline test `tests.test_manual_knowledge.IdentityProvenanceTests.test_provenance_names_release_path_from_frozen_files_only` fails because `publication_identity` resolves the root to `/private/var/...` but leaves the temporary source path under `/var/...`, so `Path.relative_to` raises `ValueError`. The exact test reproduces the same error independently. It passes when the test process's temporary-directory path is normalized to its real path; no repository code or system setting was changed for that diagnosis. Logs remain in `tmp/jhp3600c-fr-es/unittest-final.log` and `unittest-path-alias-repro.log`. This is an existing macOS path-alias regression to follow up separately; full repository regression is **not green**, and no PR is opened. The locale-specific acceptance checks above passed.

### Local review routes

- French: `http://127.0.0.1:8878/JHP-3600C/US/fr/md/manual_jhp3600c_us_fr.html`
- Spanish: `http://127.0.0.1:8878/JHP-3600C/US/es/md/manual_jhp3600c_us_es.html`

English source and frozen outputs passed their existing manifest hashes and remain unchanged. Primary and worktree `tmp/` artifacts are preserved. No FR/ES push, PR, merge, publication or live business-plane write is claimed.


## Authorized publication preflight (2026-10-07)

The operator requested “发布上线”; MA-262 covers the engineering PR and matching isolated Hello-Docs publication PR. This supersedes the candidate-only authorization boundary above. No live business-plane writes are permitted.

Canonical-temp full regression passed: **5210 tests, 35 skips**, by setting only `tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())` inside the test process before unittest discovery. This removes the macOS `/var` alias from test fixtures without changing repository code or host settings. The fixture-backed `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2 --staging-root tmp/jhp3600c-fr-es/publish-regression --no-clean --skip-root-index` passed; it validates repository regression, not the new FR/ES native bodies.

Formal frozen release preflight passed for both languages, with all source-root files inventoried by path/size/SHA-256. Native symbol admission binds all eleven shared assets per locale to physical p36/p67 glyphs and exact native captions; all 22 comparisons passed existing glyph/transparency thresholds without new artwork or shared-registry changes. The French source ligature in “ﬂamme” is retained exactly for source-caption equality. Strict Sphinx and source coverage passed for the final frozen bodies. English assets and package remain unchanged.

Logs and preflight receipts are preserved in `tmp/jhp3600c-fr-es/`; actual publication receipts will bind the final merged engineering commit rather than the preliminary preflight ref.
