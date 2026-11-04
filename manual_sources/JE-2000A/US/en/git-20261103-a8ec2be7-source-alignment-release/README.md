# JE-2000A US English — current attachment alignment

Candidate correction of `git-20261027-a8ec2be7`. The 19-page current single-language PDF is byte-identical to the package PDF. Front cover p1 is excluded by explicit user instruction; all substantive pages p2–19 are reviewed, including the package list on p3 and contact/QR on p19.

The authoritative corrective carrier is `source/en/content.json`. `rebuild.py --output <new-directory>` verifies source and repository hashes then performs shared IR/style/symbol admission and replay. Run `refresh_manifest.py` before replay if source files change. Historical `build_content.py` and `derive_assets.py` are provenance for initial intake; do not rerun them over this reviewed corrective content.

Original art is unchanged except a new crop of the original p19 QR. Text and tables remain native. Source-native headings, open specifications, two-column package list, paired LCD table, run-in cautions, merged troubleshooting cell and ordinary warranty paragraphs replace the old conversion's layout choices. The hidden metadata title supports Sphinx document navigation; native chapter anchors remain while the former automatic chapter sidebar is absent.

Local pass is the operator's checkbox criterion; this package remains candidate and does not claim release. Complete page, reverse-copy, numeric, resource, viewport and rebuild evidence is in `audit/current-source-review/`. Earlier `evidence/local-review-20261103.json` only covers the initial partial pass and is superseded by that complete review.

## Authorized release snapshot

This immutable -release copy binds the fully reviewed candidate at cd3703837dfc119790906351486d1517772572eb under MA-381 (operator: 授权本批逐本全绿后合入上线; local acceptance: 本地构建复核通过就可以了). Candidate content, CSS and artwork remain unchanged. Original repo_inputs pins are preserved. Current approval and byte-equivalence evidence supersede inherited candidate-status statements for this copy only. Publication itself remains a separate transaction.
