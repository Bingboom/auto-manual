# JS-100I EU English Web release readiness — 2026-09-06

Status: engineering output revalidated on final main; exact business-input
increments prepared; formal publication is blocked by approvals and one shared
queue-routing defect. No live Base write, workflow dispatch, mirror PR, or
production publication occurred in this run.

## Checklist

| Gate | Status | Evidence |
| --- | --- | --- |
| Final engineering base | Complete | `origin/main=9b356ecadfe355aae0eb474ef4c49bf168a01e4c` |
| Current published source | Complete | Catalog `rec27BPMtc8kJl`; V2.0-2026-04-01; PDF English physical pages 4–12 |
| PDF/master identity | Complete | PDF `cec27af…`; 10-page AI master `5d7ded6b…` |
| Target structure/content | Complete on fixture | 9 IR pages, Safety Tips first, five-card Inbox, STC/BNPI notes, no LCD/UPS/App chapters |
| Asset package | Complete offline | Two deterministic runs; 33 artifacts; 13/13 semantic exports match committed assets |
| IR cold replay | Complete on fixture | Replays 9 fragments with `.rst`/`.csv` reads denied |
| IR tamper rejection | Complete on fixture | Mutated packaged image rejected with `asset missing or changed` |
| Real Sphinx HTML | Complete on fixture | Pandoc → Sphinx 8.2.3 with `-W`; no warning |
| Final image URLs | Complete on fixture | 13/13 loaded over HTTP 200 from final Sphinx tree |
| 1440×900 browser | Complete on fixture | 13 images, 0 broken, 0 image overflow, 0 page horizontal overflow, five Inbox columns |
| 375×812 browser | Complete on fixture | 13 images, 0 broken, 0 image overflow, 0 page horizontal overflow, one Inbox column |
| Live business input | Pending approval | Target records are all zero; exact additive plan prepared |
| Queue target routing | Blocked | `eu-merged` selects generic `config.eu.yaml`; `eu-en` is rejected for Web Publish |
| Review branch | Not started | `review/JS-100I-EU` does not exist |
| Hello-Docs publish snapshot | Not started | No open `publish -> main` PR and no JS-100I path under `docs/publish/**` |
| Formal URL/link readback | Not started | Must follow the generated snapshot PR and production-site verification |

The fixture build is regression evidence only. It is not a formal live-source
build and is not publication evidence.

## Source and build evidence

The source of authority is the current published manual, not a historical
comparison:

- [Jackery SolarSaga 100 Air User Manual V2.0-2026-04-01](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3XrMnMUONl9pAxJkb4Mw9r?utm_scene=team_space)
- Catalog identity: JS-100I, 欧英规, English, PVT, `Is_latest=TRUE`, version
  V2.0.
- Published PDF SHA-256:
  `cec27af653d9f5da11d641e2431ddc0b71ced186bbadfd9594fa8cd9c96e1596`.
- `371JNuMVqZ.ai` SHA-256:
  `5d7ded6ba7810505cfb4c91b128a71cbef16a0e11aae720cdbd887559224b96a`.

Latest-main fixture outputs:

| Artifact | SHA-256 |
| --- | --- |
| `manual.ir.json` | `b49ee1b0da00418ee63a7440152192fcd2fa1720b8722dc0a235c0781a8ace6f` |
| `manual_js100i_eu_en.md` | `5126285d0a34d91786ed7fe7084d376d7994cee2891946874e025fc12ef50dc9` |
| final nested Sphinx HTML | `4f7bf8aac16d92c13f441bb17d5c09968814e32aa021071a096b235e3e683447` |

The IR declares `manual-ir/v2` with projection
`whole-document-components/v1`, target `(JS-100I, EU, en)`, 9 pages, and 13
asset references.

Commands used:

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.solar-eu-en.yaml \
  --model JS-100I --region EU --lang en \
  --data-root tests/fixtures/js100i_eu_en_phase2 \
  --staging-root <temporary-directory>
python tools/readthedocs_source.py \
  --build-root <temporary-directory>/docs/_build \
  --output-dir <temporary-directory>/docs/_build/rtd \
  --title "JS-100I Web Release Readiness"
python -m sphinx -W -b html \
  <temporary-directory>/docs/_build/rtd <temporary-directory>/html
python -m unittest tests.test_solar_js100i_eu_target -v
```

The test command passed all 7 cases. It covers slot order, target identity,
required copy, exact figure hashes, cold replay, and fail-closed art tampering.

## Full image-URL acceptance

The browser-loaded URLs are rooted at:

```text
/_static/manual-assets/JS-100I/EU/en/md/assets/ir/<sha256>/<filename>
```

All thirteen target files returned HTTP 200 and had a non-zero
`naturalWidth`: `inbox_panel.png`, `inbox_bag.png`, `inbox_cable.png`,
`inbox_adapter.png`, `inbox_manual.png`, `product_views.png`,
`unfold_steps_1_3.png`, `unfold_step_4.png`, `fold_steps.png`,
`dc_connections.png`, `optional_connections.png`, `angle_and_device.png`, and
`multifunctional_adapter.png`. The unrelated browser request for
`/favicon.ico` returned 404 and is not a manual asset.

This confirms the shared packaged-asset copy fix is active; no temporary copy
workaround was used.

## Live business-input readiness

The exact additive plan and approval wording are in:

- [`../../reports/source_intake/JS-100I_EU/formal_business_input_plan.json`](../../reports/source_intake/JS-100I_EU/formal_business_input_plan.json)
- [`../../reports/source_intake/JS-100I_EU/formal_business_input_review.md`](../../reports/source_intake/JS-100I_EU/formal_business_input_review.md)

The live product and EU region dimensions already exist, but Document_key,
specification rows, notes, the three new asset-table layers, and the build row
do not. The plan contains:

- 1 Document_key record;
- 18 new row-key dimensions, reusing 3 existing English keys;
- 21 specification rows and 0 page placeholders;
- 3 specification notes after the `JS-100I` Model option is promoted;
- 1 asset source with 3 hash-bound attachments;
- 13 asset definitions and 33 export records;
- 1 inert Web Publish build row, created only after routing is fixed.

The asset package was reproduced twice from the committed recipe. Both runs
gave package SHA-256
`d3f56e541c5522548066991026dd375925264a41678884b540c6a8786d726a1b`
and manifest SHA-256
`87c9be492c71d172aeb559d89650e269b78484172b5986d09d1d8a7cf8e7c7f1`.

## Shared queue-routing blocker

The target cannot safely be placed into the current Web Publish lane yet.
Using the exact live row identity (`Build_family=eu-merged`, blank `Lang`) gives:

```text
resolve_config_path_for_task(
  model="JS-100I", region="EU", lang=None,
  build_family="eu-merged", workflow_action="Web Publish"
) -> config.eu.yaml
```

That is the generic JE-1000F EU carrier, not the target's
`config.solar-eu-en.yaml`. Removing the live family does not fix it:

```text
build_family=None, lang=None
-> RuntimeError: Web Publish queue rows must use a whole-book Build_family,
   not a single-language family

build_family=None, lang="en"
-> RuntimeError: Web Publish queue rows must leave Lang blank
```

This is a shared resolver/queue-contract issue, so this target branch does not
alter `tools/queue_config_resolution.py` or the Web Publish workflow.

The centralized fix must prove all of the following before this target's build
row is created or triggered:

1. `(JS-100I, EU, blank Lang, live Build_family=eu-merged, Web Publish)`
   resolves to `configs/config.solar-eu-en.yaml` by exact target identity.
2. A one-language whole-manual Web Publish is accepted without allowing a
   language-fragment row to masquerade as a whole-book release.
3. Existing JE-1000F EU merged and JBP target routing remains unchanged.
4. The Hello-Docs mirror commit explicitly names the auto-manual fix SHA.

## Mirror and publication state

Hello-Docs main is `f6df757e601ef505446828118b2d3aa272822be6`; its
commit message confirms source `Bingboom/auto-manual@9b356eca…`. The business
queue pause variable is `false`. There is no `review/JS-100I-EU` branch, no
open `publish -> main` PR, and the current Hello-Docs main tree contains no
JS-100I path under `docs/publish/**`.

After approvals and the shared routing fix, the coordinating task must execute
in this order:

1. Apply and read back the approved business-input batches.
2. Freeze a live data snapshot and build JS-100I with that snapshot; rerun IR,
   tamper, Sphinx, image URL, and 1440/375 browser checks on the live-derived
   package.
3. Start `review/JS-100I-EU` and verify its exact tip/content before Web
   Publish.
4. Trigger only the JS-100I Web Publish row in the agreed shared order.
5. Verify the workflow settled, the generated PR diff contains only
   `docs/publish/**`, and all checks are green; do not self-merge without a
   valid authorization.
6. After merge, verify the production URL and read the same URL back from the
   build record's published-link field.

Until step 6 succeeds, the correct release state is **ready for approved data
intake, not formally published**.
