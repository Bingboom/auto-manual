# JA-AD01A / EU / en Web-first acceptance record

## Discovery baseline

- Branch baseline: `origin/main` at `ef45a0df`.
- Target: `JA-AD01A` / `EU` / `en`, project `HTO847`, product name
  `Jackery 102W GaN 3-Port Fast Charger`.
- Candidate source: `/tmp/auto-manual-web-intake-20260906/xG4bYnERxR.ai`,
  SHA-256 `0252cb5db68fb67b3fe0947824de4655e13e26f90b3dde1f6bada3b64aa390fc`,
  nine PDF-compatible pages. Printed English manual content is on source pages 3-9.
- Authority boundary: the source-list row has no linked reference manual, and
  exact project searches in the current publication/material views returned no
  row. The implementation therefore treats this file as a candidate source;
  it does not claim an approved published version or authorize publication.
- Live source-table writes are outside this change. No Feishu source record is
  created or modified by this branch.

## Implementation plan

1. Add a reusable charger/accessory skeleton and a single-language EU region
   profile, then commit the byte-identical resolved manifest.
2. Add target-owned English templates and exact structured specification rows.
   Preserve every advertised voltage/current combination; do not infer missing
   wattage splits.
3. Extract target-owned Web illustrations from the candidate source with a
   committed recipe and bind them through `web-illustrations/v1`.
4. Add a target-specific phase2 fixture and regression tests for manifest
   resolution, content fidelity, semantic components, asset provenance, public
   IR replay, and asset-tamper rejection.
5. Run the target Web build/check, desktop and 375 px browser acceptance, cold
   replay, and the existing `JE-1000F` EU/en regression before opening an
   engineering PR.

## Ownership and non-goals

- This branch owns only JA-AD01A target/category files and target tests.
- Shared Web runtime work for variable Inbox cards, short-manual entry policy,
  and Word-bundle HTML remains in the separate shared branch and must be merged
  before final acceptance.
- This branch does not edit shared registry/style files, publish artifacts,
  external business-plane repositories, or live source tables.

## Acceptance results

Pending implementation and verification.
