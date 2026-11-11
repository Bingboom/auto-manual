# Manual layout regression repair

Status: final local verification passed; prepared for PR review. No merge or publication authorization.

## Discovery and plan

The earlier 6,250-test run used Python 3.14 instead of CI's Python 3.12 and failed in several shared families: historical Web dependencies drifted from immutable packages, macOS temporary-directory aliases tripped containment checks, exception characterizations varied with the interpreter, the workflow shell could not find `python`, and the RTD sidebar fixture expected an older anchor shape. Some historical derivation tests also write manifests into their real source packages.

1. Install the unchanged `requirements.lock` in a disposable Python 3.12 environment and reproduce each family. Safety net: commit `4b09f1caf`, clean starting tree, existing immutable outputs and acceptance records.
2. Correct shared path handling and historical replay fixtures without refreshing approved packages or reducing integrity checks. Characterize temporary aliases, exact historical dependency bytes and mutation rejection. Keep test derivation output in temporary directories.
3. Address the newly reported solar subscript and storage-bag crop using the existing target template and correction artwork recipe; preserve wording and technical values.
4. Run Ruff, affected modules, the complete `python -m unittest`, guardrails, documentation links and real build/check routes. Record exact commands/results; open the PR only when the full set is green.

No dependency version changes, live table writes, old source-package reapproval, workflow edits, merge or publication are planned.

## Implemented corrections

- Historical model tests read five exact shared-input fixtures from commit `8364aa16b52ccdf99f17194a34b4a1192d313ed4`, each checked against its SHA-256. The five fixtures include the prepared presentation source pin, whose new class additions concern the requested solar layout. Replay still executes the current renderer and compares its full output with the historical bytes. The existing pre-divider/pre-four-control stylesheet adapters cover editions frozen before those changes. The current-style assembly tests continue to exercise the current contracts. Every immutable output comparison and changed-source/acceptance rejection assertion is retained. The fixture context covers text, byte and streamed file reads consistently and clears the target-contract cache on entry/exit, so historical data cannot leak into current-layout tests.
- Temporary package roots are canonicalized before supplying them to frozen scripts that require canonical containment roots. Publication metadata canonicalizes both root and source before calculating a relative route. The APFS alias test uses the normal temporary area and validates the same physical-volume alias.
- Historical derivation tests copy their output package into a temporary directory and compare the complete resulting file inventory with the approved original. They do not rewrite the repository's source manifests.
- The sidebar's `#` link is a valid link to the current page; the test validates its parsed URL path and current-page state.
- Python 3.12.13 with the unchanged 47-package `requirements.lock` reproduces all six command/help/exception characterization goldens. No characterization golden or dependency pin was changed. The test shell puts that environment's `bin` on `PATH`, including subprocesses that invoke `python`.

## Additional screenshot corrections

The old bag crop ended at x=215 pt; its original outer shape reaches x=215.182 pt, so it cut the right-hand stroke. The correction recipe now preserves `[155,254,217,328]` on English physical page 5. The full recipe replay reproduces all twelve committed PNGs byte-identically. New bag SHA-256: `22c646f370939c669dff4573e97a38b98cca4e1e5921dc78a5a0024b91b954cc`.

The solar safety template now uses semantic RST subscripts `sc` and `oc` in place of look-alike Unicode characters. Actual Sphinx/browser output contains two `sub` elements with CSS `vertical-align: sub`, and the body remains searchable. No technical number or safety instruction changed.

Browser evidence at 1280px: [safety subscripts](safety-subscript-fixed.png), [complete bag and 3+2 Inbox](inbox-bag-fixed.png). Strict Sphinx passed for the follow-up build.

## Verification so far

- Six CI-Python characterization tests: passed.
- 60 focused historical/layout/portal tests: passed (five existing prerequisite skips).
- 66 path/template/publication/business-content tests: passed.
- Two explicit historical Pandoc cold-render tests: passed, including exact committed bytes.
- Ruff, maintainability guardrails, documentation links and reference-layout pins: passed.
- US `build.py check` with `tests/fixtures/phase2`: passed.
- Node UI suite: 86 passed, zero skipped.
- Final full suite: 6,253 tests in 1,161.413 seconds, zero failures/errors, 92 existing conditional skips. Exit code 0. Full command: `PATH=/tmp/manual-layout-python312/bin:$PATH python -m unittest -v`.

The first complete Python 3.12 diagnostic run executed 6,247 tests in 1,198.039 seconds, with zero assertion failures and eight errors (92 skipped). Two errors identified the APFS temporary-directory assumption and the streamed-read fixture gap; both now pass their direct regressions. The other six came from sandbox denial of loopback socket binding. The same 23 local HTTP tests pass with loopback permission. Final full-suite verification uses that permission and all final code changes.

The new JHP candidate also cold-rebuilt on Python 3.12: its Markdown, Manual IR, source geometry stylesheet and shared stylesheet all match the four committed artifacts byte-for-byte.

## JBP-1000B-SIL US follow-up

The final screenshot identifies the English `DC Input` LCD row of the existing `data/manual_sources/JBP-1000B-SIL/US/git-20261008-7afcb2a1` package. Its authoritative description already has separate On/Off meanings; only the HTML joins the labels with a space. Plan: derive an English-only pending-review candidate, reuse all 50 existing assets and the original PDF, add one semantic `<br />` before `Off:`, and retain every native word/value. Validate the new candidate through its actual rebuild entrypoint, exact source/artwork parity, a second cold rebuild and strict Sphinx. The old frozen package and its acceptance records remain untouched. This adds a source-package correction; the shared Python implementation tested by the ongoing full suite is unchanged.

The LCD candidate passed source parity (exactly one HTML field gains one `<br />`), identical native rendered words, all 50 unchanged artwork bytes, strict Sphinx and two cold builds with 56 identical files. The browser confirms `Off:` on the following line. See [LCD verification](jbp-lcd-verification.json) and [screenshot](jbp-lcd-linebreak-fixed.png). Its two retired parent language-navigation dependencies are recorded explicitly, following upstream #1469. The candidate is registered with no release authorization.

Final machine-readable results: [verification.json](verification.json). The generated root `docs/index.rst` from the US check was restored to its prior bytes and is excluded from the patch. No old source package was rewritten.
