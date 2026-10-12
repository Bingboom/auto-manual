# JBP EU publication: bounded frozen-source capacity repair

Status: active

The approved nine-language publication merged in Hello-Docs #172 at
`b6e02187df6f3002a262d91a56935041fb90d00e`, after engineering #1426 at
`56d0e9fc740c7421d168970e0c8b30db4a1d7887`. RTD latest build 34916463 failed
in the `tools.manual_knowledge.export.write_knowledge` callback with
`Deployment inventory exceeds safety limits`. Plain strict Sphinx had passed
because that local command omitted the production portal extension.

The actual frozen publication has 6,740 files totaling 686,644,486 bytes
(654.8 MiB). Its self-contained sources and assembled Web copy exceed the
previous 640 MiB source allowance by 15,555,846 bytes. The same input
reproduces the failure with the old cap; no content, artwork, historical
seal, publication source, or source-manifest entry was removed or rewritten.

The repair changes only the local frozen-source allowance to 768 MiB.
Served output and each network-verification traversal remain capped at
512 MiB; the 32 MiB single-file, 10,000-file, symlink, safe-path and byte-hash
checks remain unchanged. The operator guides now require the aggregate
preflight to load `myst_parser,tools.rtd.portal`, matching the real RTD
knowledge-export and receipt callbacks.

## Regression evidence

[Measured before/after proof](jbp3600a-rtd-source-capacity-20261003.json) records
the old-cap failure, retained limits and resulting source fingerprint.

- 39 existing deployment receipt and transport-throttle tests pass, including
  source/output budget separation, source overflow, file count and file-size
  rejection, recursive resource identity, and the real Sphinx receipt fixture.
- Strict aggregate build with `-W --keep-going -D extensions=myst_parser,tools.rtd.portal`
  passes against the exact merged publication snapshot. All 1,928 output
  hashes in the generated deployment receipt match actual files; total
  inventoried output is 259,063,178 bytes (247.1 MiB).
- The query corpus contains all nine JBP locales. Receipt and corpus share
  source fingerprint `51b231e186d31464d4060d5190334fdf45812243d248210e35ac0c240ce6c132`.
- Ruff, maintainability guardrails, documentation links and the US target
  `build.py check` pass. The US check uses the same isolated existing phase2
  snapshot as the approved release validation; no live-data synchronization.
- Full local suite: 5,122 tests pass, 35 skipped, 877.133 seconds.
  Final remote CI must also pass before merge.

The publication snapshot is already merged. Engineering repair must flow
through the normal Hello-Docs mirror; no code PR targets the mirror, and no
new hand-edited publication candidate or queue record is needed. A successful
RTD build and actual nine-language online verification are still required.
