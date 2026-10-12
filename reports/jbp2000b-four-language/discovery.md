# JBP-2000B EU four-language completion

Source: /Users/pika/Downloads/HTP017-EU-9国说明书-0924.ai; PDF-compatible, 80 pages; SHA256 b7d7fca4207792e6337c6e14003d12fd418fcd192ecc23137519c1147b6f85a3. Cover identifies JBP-2000B / Jackery Battery Pack 2000. The ambient JBP-3600A page is a separate target.

Verified engineering base: 07859f7eae1fe90b72ee950025b28b12cf2c36ff. Isolated worktree: /private/tmp/jbp2000b-four-languages. The branch wrapper fetched main, then failed because main is checked out in the primary workspace; the task branch was created from the verified origin/main. Primary tmp/ and other worktrees are preserved.

Current Hello-Docs main manifest lists JBP-2000B EU en/fr/es/de/it at git-20261005-e267ff15-transparent-symbols. Remaining locales: uk/pt/nl/pl. JBP-3600A EU already has nine locales.

Plan:
1. Reproduce current English through build.py and pin its IR, artwork and shared component structure as the comparison candidate.
2. Record all native source blocks and page geometry for four locales, then map complete native paragraphs, table cells, warnings and labels to shared components. Each native source controls facts and copy. Record anomalies explicitly.
3. Inventory existing assets and reuse matching neutral art and transparent symbols byte-for-byte. Inspect all candidates before extracting missing dense native label panels; preserve all frame edges.
4. Produce four reproducible frozen semantic packages, strict HTML, cold replay and source-preservation evidence. Check desktop/mobile for copy, images, tables, frames and clock behavior.
5. Validate scoped regression and repository gates; prepare a reviewable engineering PR. Merge/publication require the applicable recorded operator grant and every final-head check green.

Non-goals: modify existing five published locale bodies, other models, online source/Base/queue/HTML_link writes, workflows, dependencies, public CLI or schema. No screenshot body/table pages. No new renderer or per-model configuration.
