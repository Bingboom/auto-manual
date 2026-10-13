# Web Publish pipeline: input paths and shared release outlet (§2)

Status: active · Part of the [Web Publish pipeline](../web_publish_pipeline.md) contract; its index lists the
other sections. Change this part of the contract here, not in the hub.

## 2. Web Publish input paths and shared release outlet

### 2.1 Queue-driven transaction

1. The business-plane worker claims only rows whose normalized action is
   `web_publish`; `Git_ref` is required.
2. It always runs live `sync-data` with the HT-Docs bot. Approved
   `04_资产导出物` rows are downloaded and hash-verified; unapproved or ambiguous
   Web composites fail closed.
3. The web presentation profile runs `check -> md -> html`. The HTML render is
   a verification output; the MyST directory is the durable publishing input.
   With an explicit target language, each successful action captures the
   canonical projection and complete include closure. The captures must agree;
   the [receipt](../web_language_release_evidence.md) is sealed with md/html in the
   same new immutable version. A shared-language config uses the selected
   language for release paths, not its first configured language.
4. `latest/web/publish_meta.json` records the target, version, review ref,
   queue rows, MyST source and verified HTML directory. Explicit-language
   metadata also requires the verified receipt path and SHA-256 before it can
   claim `language_scope=single`; language and evidence must be supplied together.
5. `publish_branch_assembly.py` copies that source into
   `docs/publish/sources/web/<model>/<region>/<lang>/md/`, preserves other targets,
   rebuilds `docs/publish/web/`, and writes a SHA-256 inventory in
   `docs/publish/publish_manifest.json`. Assembly rechecks fresh md/html against
   evidence and retains the receipt plus projection manifest with stored MyST.
   The stored target metadata (and therefore the manifest target entry) carries
   the validated `queue_record_ids` forward, so the post-merge receipt lane can
   still locate its queue rows after the release metadata of the queue run is
   gone. Stored replay rechecks the retained MyST/assets; the HTML digest is
   historical evidence, not a new HTML render check. Legacy links retain their
   redirects.
6. The workflow reconciles the generated `Hello-Docs/publish` candidate with
   current `main`, then refuses to push if the PR diff contains any path outside
   `docs/publish/**`. Review branches are build inputs only; they are never
   merged into either candidate or production history.
7. The workflow advances `publish` with an ordinary non-force push and creates
   or updates the single `publish -> main` PR. A human merges that PR after
   review; only the resulting `main` push is a production RTD trigger. One
   global concurrency group serializes the complete build, branch update, PR,
   and pending-registration transaction. At build time the queue records the
   deterministic URL in the release metadata only (`--pending`); it makes no
   `HTML_link` write, because at that point the PR is unmerged and RTD has not
   deployed.
8. The assembler creates a collision-checked root alias named from the manual
   stem (for example `/manual_je1000f_us.html`) that forwards to the canonical
   nested Sphinx route. The root alias is the countable printed/QR entry layer
   only. The deterministic URL that the receipt lane later writes to
   `Document_link.HTML_link` is the canonical nested page itself (for example
   `/JE-1000F/US/en/md/manual_je1000f_us.html`), matching the stored target
   `route` in `publish_manifest.json`. Relative forwarding keeps the generated
   alias valid in both RTD single-version and `/en/latest` deployments. A
   seven-day workflow artifact retains the Web release evidence; the Git
   branch remains the durable snapshot.
9. After the human merges `publish -> main`,
   [`web-publish-receipt.yml`](../../../.github/workflows/web-publish-receipt.yml)
   runs on the Hello-Docs `main` push (paths `docs/publish/**`):
   [`tools/write_web_publish_receipt_links.py`](../../../tools/write_web_publish_receipt_links.py)
   reads the merged manifest, selects the targets that recorded
   `queue_record_ids`, polls `verify_deployment` (frozen-source fingerprint,
   byte identity, expected RTD project slug; fresh `FetchSession` per attempt)
   until the deployment verifies or the deploy timeout expires, and only then
   writes the canonical URL to each queue row — idempotently (an equal stored
   value is skipped, so reruns never re-register) and with a same-record
   readback after every write. `HTML_link` is a Bitable URL field, which
   `lark-cli base +record-get` reads back as a Markdown link whose label and
   target are both the stored URL. Both comparisons accept exactly that form
   (`document_link_queue.url_field_matches`); a link whose label or target
   differs is a mismatch, so a hand-titled link is rewritten to the canonical
   URL and a link to another page fails the readback. Verification failure or
   timeout registers nothing and opens the `queue-failure-web-receipt`
   sentinel; the retry is a `workflow_dispatch` re-run (optionally scoped by
   `record_ids`), never a re-publish of the manual.

### 2.2 Git-only transaction

Use this path only when the operator has designated reviewed Git content as the
release authority and explicitly excluded online-table writes. It does not
create synthetic queue rows or write `HTML_link`.

1. Commit the complete target structure, sources and assets with a
   `source_manifest.json`. Record the target identity, source authority,
   original filename and SHA-256, included pages, deliberate normalizations,
   and an input SHA-256 inventory. If the printed-manual version is unknown,
   keep it unknown. A technical snapshot version such as
   `git-<date>-<source-sha-prefix>` identifies the Git release input; it is not
   a paper-manual version.
2. At the exact source Git ref, run the target `build.py check`, render the Web
   presentation profile to MyST, build it with strict Sphinx, and inspect the
   actual page at desktop and mobile widths for image URLs and page overflow.
   When the target uses public IR or packaged assets, retain cold-replay and
   asset-tamper evidence as applicable.
   For an already frozen external manual whose new Web languages are absent
   from the phase2 build target, keep the existing target `build.py check` as a
   repository regression gate. Render the designated source through a
   source-local, hash-checked MyST adapter and state in `source_manifest.json`
   that the `build.py` result does not validate those new language bodies.
   Verify those bodies against their source pages, figures and structured
   tables, then run the same strict Sphinx and browser gates. This exception
   does not register a new phase2 or print target.
   When a reviewed native source has a different chapter map from the historical
   phase2 projection, enroll its exact original-source SHA-256 and target/locale
   requirements under `prepared_component_admission.json:source_profiles`.
   Admission selects that committed map from the frozen source identity; it
   never derives requirements from candidate inventories. The historical
   target entries remain applicable to existing phase2 builds. The JE-3600A
   0924 source review records the 16 native chapters, shared artwork and
   source-language exceptions in
   [its nine-language review](../../reviews/je3600a_eu_nine_language_web_2026-10.md).
3. Put the verified MyST and verification HTML in an isolated release root.
   Write a real `auto-manual-web-publish/v1` record at
   `<model>/<region>/<lang>/latest/web/publish_meta.json`. Its
   `md_output_path` and `html_dir` must stay inside that release root, and the
   HTML directory must contain `index.html`. Record at least `model`, `region`,
   `lang`, `version`, `built_at`, `git_ref`, `md_output_path`, and `html_dir`.
   An external frozen MyST language still declares `language_scope: single`.
   Its `source_manifest.json` uses `auto-manual-frozen-web-source/v1` and
   inventories every source input, including each locale's MyST and assets.
   At the actual source Git commit, call
   `seal_frozen_web_evidence` in `tools/web/frozen_source_evidence.py` for each
   language. The resulting `auto-manual-frozen-web-language-evidence/v1`
   receipt binds that manifest, the exact source commit, the versioned MyST
   tree, and verification HTML including local images. Point the versioned
   publish metadata at that receipt and its SHA-256. This evidence mode is
   distinct from the phase2 projection receipt; neither can be substituted
   for the other.
4. Start from current `Hello-Docs/main:docs/publish/**` in an isolated checkout
   so previously published targets remain present. Assemble and verify the
   candidate with:

   ```bash
   python -m tools.publish_branch_assembly --releases-root <isolated-release-root> --output-dir <hello-docs-candidate>/docs/publish
   python -m sphinx -W -b html -D extensions=myst_parser,tools.rtd.portal <hello-docs-candidate>/docs/publish/web <isolated-verification-html>
   ```

   The assembler replaces matching target routes, retains the other stored
   targets, rebuilds the aggregate Sphinx tree, and rewrites
   `publish_manifest.json`.
   Keep the RTD portal extension enabled in this aggregate preflight: it exports
   the query corpus and seals the deployment receipt, including the bounded
   frozen-source inventory. A plain Sphinx build without the extension cannot
   validate those production callbacks.
   The frozen-input inventory is bounded at 1280 MiB: it includes both the
   self-contained source packages and their assembled Web copies. JE-5000A JP
   brings the reviewed library from 1,057,291,744 to 1,093,933,355 bytes,
   exceeding the previous 1 GiB source budget. Served-output and network
   inventories retain their separate 512 MiB budget. Frozen source permits
   20,000 files; served output, selected routes, receipt inventories and online
   dependency traversal retain the 10,000-file limit. Every inventory retains
   the 32 MiB per-file limit. The source count budget is separate because
   stored packages and assembled copies coexist: batch-1465 reaches 10,043
   source files, and the operator authorized doubling the source allowance
   from 10,000 to 20,000. Do not remove reviewed artwork or evidence to fit
   the input budget. JHP-3600A US adds three reviewed native
   locales to the 138-target library: the candidate occupies 1,224,106,656
   source bytes (1167.4 MiB), exceeding the previous 1152 MiB source cap.
   The 1280 MiB source budget accommodates this frozen input without changing
   the served-output, network, per-file or file-count limits.
5. Commit that candidate on the normal Hello-Docs release branch and open the
   usual `docs/publish/**`-only PR. Do not include engineering code, review
   branches, print artifacts, or unrelated targets.
6. After the approved PR merges, verify the Read the Docs build commit, each
   canonical target route, each short root alias, all referenced assets, and
   desktop/mobile rendering.

The durable evidence is the source Git commit, source-manifest and input hashes,
release metadata, publish-manifest hash, Hello-Docs snapshot commit, Read the
Docs build commit, and the verified production URLs. `Document_link.HTML_link`
readback belongs only to the queue-driven transaction. A Git-only transaction
does not write online staging, source, asset, build, or link records.

### 2.3 Catalog mirror and continuous reconciliation (M1/M2)

The operations catalog sheet 「说明书目录」 (spreadsheet
`K13JsXoUjhd75sth7eec1sKpnKd`, sheet `15c75c`) is a **derived view** of the
publication record, never a second authority. The single frozen-record
authority for Web targets is `docs/publish/publish_manifest.json` on
Hello-Docs `main` (REV-06/M0-10: `reports/releases` is deliberately not in
Git). Rows align on the `(model, region, lang)` triple; version strings are
display-only vocabulary and are not machine-reconciled across faces (M0-11).

[`tools/ops_catalog_sync.py`](../../../tools/ops_catalog_sync.py) owns both
directions:

- **`sync` (M2, catalog registration as a post-publication transaction).**
  Reads the manifest at a pinned Hello-Docs commit (the recorded source SHA)
  and upserts only the machine columns A..K (文档ID/型号/市场/语言/当前版本/
  正文链接/根别名链接/语言范围声明/目标构建时间UTC/内容提交/收录状态). The
  human-owned columns L..O (负责人/运营状态/下次复盘日期/运营备注) are never
  written on existing rows; a new row seeds 运营状态=待评估 only. New targets
  append at the bottom; an existing row is rewritten only when a machine
  column actually differs; a row whose key has left the manifest is reported
  as an orphan and never modified or deleted. Default is dry-run; `--write`
  is an operator-authorized run that applies row by row, reads each row back
  (verifying the human columns survived byte-for-byte), and records a failed
  row for a later idempotent retry without blocking the other rows. This
  registration is a separately approved transaction after publication: it
  does not change the Git-only contract above (no queue rows, no source-table
  writes), and a failed deployment must never be registered as online.
- **`reconcile` (M1, continuous three-face cross-check).** Read-only
  comparison of manifest ↔ ops sheet ↔ `Document_link.HTML_link` queue
  receipts. Receipts register the canonical nested page (M4 semantics, as
  `write_web_publish_html_link.py` writes it); a flat root-alias receipt is
  flagged as `receipt_flat_form_link`. Every difference is classified against
  the committed whitelist
  [`data/ops_catalog_reconcile_whitelist.json`](../../../data/ops_catalog_reconcile_whitelist.json)
  (seeded from the REV-06 M0 diff table: the 49-target Git-only
  no-receipt baseline, M0-05). A whitelisted difference is listed and exits 0
  so known history never re-alarms; any new difference exits 1. Growing the
  whitelist is an operator decision recorded in the entry's `reason`; targets
  never enter it automatically.

Neither mode fabricates queue history for alignment (the acceptance goal is
"no unexplained difference", not "no difference"), and both refuse to act on a
sheet whose header row no longer matches the 15-column contract.
