# JE-3000C EU energy-saving panel correction

## Cause and correction

The PT/NL/PL native intake registered `energy_saving` as a generic reference
figure. It joined the on/off mode and hold instruction into one label and
removed the source clock without restoring the shared CSS clock.

The new immutable intake migrates this one figure to
`HB-SPECIAL-OPERATION/footer-overlay`. Its native mode, hold instruction and two
button captions remain separate semantic slots. The shared renderer accepts
hash-bound `supporting_copy_rects` and optional `footer_y`, enabling captions and
the native bracket footer to retain their intended geometry. Mobile layouts
stack these labels in normal flow. This is reusable component behavior, not
locale-specific CSS or a new renderer.

The reference screenshot supplies the desired footer style. Its JE-3600A
product drawing is not used for JE-3000C. The original JE-3000C explanatory
paragraph remains outside the operation illustration, preserving its source
flow; it has not been converted into the other model's gray introductory card.

## Native source and preserved corrections

- Source: `HTE156-EU-9国语言-0923.ai`.
- SHA-256: `45219a6e488358c4a76b847cd0288f5a865fd8ab899d8ceb9e154a5696816574`.
- Native operation panel pages: PT 111, NL 127, PL 143 (one-based).
- Artwork reused without alteration in all three languages:
  `222be1caa5342b0c1a45df51df708d7b3bf656f11714827feded992a8db8bf27`.
- Previously approved NL DC-to-AC erratum now binds the new supporting-copy
  slot. The exact source text and existing operator decision are retained.
- PV line breaks and approved 8 A correction remain intact. Generated Markdown
  outside this one figure is byte-identical to the preceding PV snapshot.
- Historical frozen packages are unchanged. The new version is
  `git-20261002-45219a6e-energy-web`, with matching `energy-intake` evidence.

## Verification boundary

Three strict Sphinx builds and fresh native component admissions passed.
Desktop and 390px mobile visual checks passed for PT/NL/PL. Full repository
regression passed: 5,060 tests, 32 skipped (3,422.939 seconds). Shared caption tests check source copy once,
separate mode/duration, artwork identity and rejection of incomplete or invalid
geometry. Ruff, maintainability and documentation checks passed; the US build
check uses the existing read-only phase2 snapshot through `--data-root`.

Local evidence and reproducible preparation scripts are retained in
`.tmp/energy-style/`. This record does not claim a merge or RTD deployment.
