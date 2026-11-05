# JHP-1000B US en — authorized release snapshot

This separate snapshot retains the complete locally reviewed source/manual of `git-20261103-e546301b-full-source-alignment` (commit `0f057292`). The original candidate remains unchanged. Publication eligibility is authorized by the operator’s conditional batch grant in MA-381: “授权本批逐本全绿后合入上线”, with the later instruction that local build/content/layout review is sufficient. It does not claim that the operator personally inspected every page.

The current source SHA, target and all current non-approval source inputs are bound in `source/approval.json`. Cold-rebuild and visible-byte equivalence evidence is in `evidence/release-conversion.json`. The native Markdown, stylesheet, artwork and IR pages must equal the reviewed candidate; only release metadata changes. This package is an authorized snapshot, not a claim of deployment or publication. No registry, live record or shared code is modified.

Rebuild: run this directory’s `rebuild.py --output <unused-output>`. Original source reproduction uses `derive_assets.py`, `derive_restored_assets.py`, `build_content.py`; modifying any source invalidates the bound approval and requires renewed input verification.
