# Explicit Git-only publication withdrawal and restoration

## Discovery and plan

Baseline: engineering main `af3d6d12c19a2b5e2de8febb65cdb53ec791501b`.
The existing publish assembler preserves targets absent from incoming releases.
It already validates locale identity, copies sealed source evidence, rebuilds
the catalog and aliases, and promotes a candidate atomically. There is no
explicit withdrawal operation or protection against reintroducing a withdrawn
version. Reuse these contracts rather than infer deletion from missing input.

This slice will add a small internal operation over a copied publish tree:

1. Validate an explicit model/region/language/version plus reason, operator and
   pinned before/restore refs; preserve an append-only action ledger under
   `sources`. Candidate and deployed commit refs belong to a separate receipt,
   because a Git commit cannot contain its own hash.
2. Remove only the selected active source, rebuild through the existing
   assembler, and retain a canonical withdrawal notice. Withdrawing a default
   language while another remains requires an explicit replacement default.
3. Make normal assembly reject a withdrawn identity/version. Restoration must
   be explicit and use byte-verified source from the recorded cold snapshot;
   record default-routing changes without replacing other manual contents.
4. Exercise withdrawal, rejection, restoration, wrong-version/source failures,
   and atomic failure on fixtures and a copy of the existing frozen tree.
   Do not modify production, workflows, online data, or public `build.py` CLI.

Rollback verification uses the same approved content under a traceable
technical release version; it must not select known incorrect safety content.
## Operator procedure

Use `tools.publication_withdrawal.change_publication_state` from an isolated
engineering checkout against a local copy of the current business publish
tree. The ordinary assembler is unchanged at its public entrypoint. There
are no new `build.py` flags, workflow actions or online data writes.

Before applying an action, verify the current business Git commit through
GitHub and retain its complete cold publish snapshot. Pass that commit as
`before_ref`, plus `manifest_sha256(candidate)` as the local stale-input guard.
For withdrawal, `restore_ref` must be the same before commit. Name the exact
currently active `model`, `region`, `lang` and `version`, the responsible
`operator`, and a concrete `reason`. An input with a mismatched version or
changed manifest fails before promotion. Never infer withdrawal from an absent
release folder or a missing source record.

```python
from pathlib import Path
from tools.publication_withdrawal import change_publication_state, manifest_sha256

# candidate is a local copy; these refs must be verified actual Git commits.
candidate = Path("/absolute/path/to/copied-publish")
receipt = change_publication_state(
    output_dir=candidate, action="withdraw",
    model=model, region=region, lang=language, version=version,
    reason=reason, operator=operator, before_ref=before_commit,
    restore_ref=before_commit,
    expected_manifest_sha256=manifest_sha256(candidate),
    default_language=replacement_language,
)
```

Set `default_language` only when intentionally selecting the remaining
default language for that model/market. Withdrawal of the current default
while a sibling language remains otherwise fails. The canonical withdrawn
manual and old aliases receive a withdrawal notice where a surviving
publication does not already own the route. Generic default routes follow
the explicitly selected replacement. The portal catalog lists only active
publications; other source content and language evidence remain untouched.
Retiring the final publication is rejected and requires a separate site
retirement plan rather than silently creating an empty library.

Restoration uses the same function with `action="restore"`, the current
verified `before_ref`, the original ledger `restore_ref`, and
`restore_snapshot=Path("/absolute/path/to/original-cold-publish")`. The complete
stored source subtree, including metadata and sealed evidence, must match the
withdrawal digest before it is copied. If another language has become the
default, choose the resulting `default_language` explicitly. Source body and
asset bytes are restored; default-routing metadata changes remain recorded.
An active identity cannot be overwritten by restoration: use an independently
reviewed version update instead. A normal retry cannot reintroduce a withdrawn
version, even after a different version has been published.

The append-only `sources/publication_actions.json` records the target/version,
operator/reason, timestamp, before and restore refs, original source ref/hash,
before/after routes and default-language routing. It is part of the publish
inventory and survives later ordinary assembly. Each action is built and
validated in a sibling temporary directory using the existing promotion
contract; failure retains the original tree.

Persist the returned receipt separately from the candidate. It contains the
candidate manifest digest and null candidate/deployed refs. After the
`docs/publish/**`-only PR is created and merged, attach its actual commit and
RTD deployed commit to that external receipt. A commit cannot contain its own
hash, and local success cannot claim production withdrawal or restoration.

## Validation and rollback drill

Run the targeted action tests and strict Sphinx over a copy of the current
frozen source. Verify target removal, canonical notice, sibling-language
preservation, blocked ordinary retry and explicit byte-verified restoration.
Record the original snapshot commit, action receipt, candidate Git commit,
final deployed commit and canonical/default routes separately.

For version rollback, reuse the existing versioned release and assembler:
select an earlier approved seal through a copied latest pointer, build a
candidate, verify source/asset identity and routes, and follow the same
business PR and deployed-revision gates. A drill should use two traceable
technical versions of the same approved content. Never pick an older version
whose known incorrect electrical/safety content has since been corrected.

## Local evidence — 2026-09-13

The action and assembly tests cover explicit defaults, version/manifest
preconditions, source drift, failed rebuild atomicity, blocked ordinary retry,
safe later-version publication and nondefault short-alias notices.

A copy of the 23-publication frozen source from business commit
`a87ff6ec97c2a4f1a071936dce5dd38b976550e2` was exercised in a separate local
Git repository. The final drill started from local commit
`74a3f4e55f2ab3e05acfd2dfce4f8e95052d98aa`, withdrew JE-1000F/EU/fr/2.0
as `862579c241dd7fe67a1fdb6784c66e9e2a4bc7d2` (22 active publications),
then restored it as `38dc878a8d7c0409a34e18d31aa35139c8d3936f` (23).
Both candidates passed strict Sphinx with the portal extension. Other stored
source bytes were unchanged during withdrawal; all restored `sources/web`
bytes matched the cold snapshot. The canonical and root short-alias pages
showed withdrawal notices, and ordinary version reentry was rejected.
These are local drill commits; no production reference was moved.

An independent fixture used the existing assembler for versions
`1.0 -> 2.0 -> 1.0`, retaining identical manual bytes (SHA-256
`1602b1ae6c74a7b6957f24f31fe7b2aea566324331090d73171626f6df5ae2ed`).
It proves same-content version selection in the existing mechanism, not a
real approved-release rollback. No production withdrawal, rollback, online
data write, workflow dispatch or final deployed receipt is claimed.
