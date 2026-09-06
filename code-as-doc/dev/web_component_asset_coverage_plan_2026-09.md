# Web Component and Figure Asset Coverage Plan (2026-09)

## Goal

Make shared Web components inherit across document targets while keeping
approved artwork as an explicit, hash-verified override. Give every generated
Web IR a stable coverage inventory so a reviewer can see where finished panels,
approved composites, editable fallbacks and missing slots are used.

## Non-goals

- create or approve new localized artwork;
- copy JE-1000F / US artwork into EU/CN/KR;
- remove either existing asset carrier;
- change review RST, phase2 schemas, live Base records or public CLI flags;
- make responsive Web pagination identical to IDML.

## Phase 1: semantic inheritance safety net

Files:

- `tests/test_web_presentation.py`
- `tools/web_presentation.py`

Steps:

1. Add a regression for warranty outside `figure_targets` and cover all five
   JE-1000F EU locales.
2. Keep the existing unsupported-overview assertion to prove frozen figure
   geometry is still gated.
3. Move only the warranty transformation before the figure gate.

Verification:

```bash
python3 -m ruff check tools/web_presentation.py tests/test_web_presentation.py
python3 -m unittest tests.test_web_presentation
```

## Phase 2: unified figure coverage inventory

Files:

- `tools/web_figure_coverage.py` (new focused module)
- `tools/web_document_source.py`
- `tests/test_web_figure_coverage.py` (new)
- `tests/test_web_document_ir.py`

Contract:

- one stable `web-figure-coverage/v1` payload in Web IR metadata;
- one row per declared or bound figure slot;
- status is exactly one of `finished-panel`, `approved-composite`,
  `editable-fallback`, or `missing`;
- both `web-illustrations/v1` and `web-composite-manifest/v1` feed the same
  read-only inventory;
- approved asset rows retain their identity/path/hash evidence;
- existing builds are not blocked solely by known asset debt.

The first version reports existing behavior; it does not replace either asset
loader or weaken their target/hash/source checks.

Verification:

```bash
python3 -m ruff check tools/web_figure_coverage.py tools/web_document_source.py tests/test_web_figure_coverage.py tests/test_web_document_ir.py
python3 -m unittest tests.test_web_figure_coverage tests.test_web_document_ir
```

## Phase 3: owning documentation and real builds

Files:

- `code-as-doc/dev/web_publish_pipeline.md`
- `user-guide/hello_auto-doc.md`
- `code-as-doc/code_optimization_log.md`

Verification ladder:

```bash
python3 -m ruff check build.py integrations tools tests scripts
python3 -m unittest
python3 tools/check_maintainability_guardrails.py
python3 tools/check_doc_link_integrity.py
```

Then run real Web builds for:

- JE-1000F / US (approved-composite path);
- JBP-2000B / JP (finished-panel path);
- JE-1000F / EU (shared warranty plus explicit artwork gaps).

Inspect the generated `manual.ir.json`, built HTML component counts, localized
warranty text and the coverage status summary. Generated `_build` output is
verification evidence only and is not added to the PR.

## Follow-up ledger

After product/design approval, add the missing localized finished panels or
composites through manifests/recipes. Promote a slot only when target, locale,
source fragment and SHA-256 evidence match. This implementation deliberately
keeps such missing assets visible instead of concealing them with copied art.
