# RTD manual-center entrance

## Discovery and implementation plan

Operator accepted the local card/search design and requested RTD implementation,
with **EU temporarily the default**, on 2026-09-12. Region options remain
US / EU / UK. EU and UK share existing EU publications; no UK copy is created.

Verified baseline: engineering main `ff5e3556`; RTD listens to Hello-Docs/main
and renders frozen `docs/publish/web` with Sphinx/Furo. The frozen config does
not load engineering extensions. Editing only the assembler would not update
already published snapshots. The live index has 21 entries (US 1, EU 20).

Implementation phases:

1. Add a root-only Sphinx portal extension, a catalog adapter over the existing
   frozen index, and the accepted responsive template/styles. No live requests
   or body duplication. Keep ordinary links usable without JavaScript.
2. Enable the extension in both RTD build paths, without modifying frozen
   sources, GitHub workflows, review content, dependencies or public build CLI.
3. Test EU default, shared EU/UK links, search, missing-language states, safe
   assets/URLs, existing non-portal regions and unchanged manual rendering.
   Run syntax/lint, targeted and full unit tests, guardrails, link check, the
   build quality check, then real Sphinx baseline/new builds of the same frozen
   corpus. Only the home and portal-specific static files may differ.
4. PR in auto-manual, gate-on-green only with current authorization, mirror to
   Hello-Docs, and verify the actual RTD page. Do not call a local build online.

Non-goals: independent twelve-language publication storage, new translations,
IR/print changes, online Base writes, product facts, and advertising removal.
Existing bundled languages remain accessible through their original manual.
Only verified independent locale links may be enabled; do not construct URLs
by replacing a language suffix. Product illustrations come from each frozen
manual's packing-list product asset; missing images use model-only cards.

The root template keeps an EthicalAds placement for RTD. No CSS hides platform
advertisements. Other markets remain accessible in an all-publications fallback
even though the primary dropdown is limited to US/EU/UK.

Rollback: revert the portal extension's RTD activation and rebuild. Frozen
content, QR aliases and nested manual URLs are unchanged.

## Maintenance surface

- `tools/rtd_portal.py` reads explicit frozen index links and only existing
  local packing-list product assets. It does not scrape the live website.
- `tools/rtd_portal_assets/settings.json` owns the temporary default, entrance
  bindings, category-prefix presentation rules and twelve planned labels.
  These category rules are navigation hints, not new product master data.
- `.readthedocs.yaml` activates the extension for frozen and bootstrap builds.
  This is needed for old frozen configs as well as future publications.
- The template renders real links before JavaScript; scripts only enhance
  filtering and the language dialog. Search/aliases/manual pages are unchanged.

Current implementation is the entrance slice only. The language dialog keeps
the existing publication available and does not enable invented locale URLs.
Independent locale storage and real locale links remain a separate milestone.

## Local verification

- `python3 -m unittest`: 3,975 tests run, OK, 22 skipped.
- Portal + RTD source targeted tests: 8 run, OK; real Sphinx fixture builds
  preserve all three manual pages and three QR aliases byte-for-byte, and leave
  the entire source tree unchanged.
- Ruff, maintainability guardrails, JS syntax and documentation links passed.
- `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
  --data-root tests/fixtures/phase2` passed. The initial command without an
  explicit data root stopped on the intentionally absent local phase2 snapshot;
  no live-data sync was performed.
- Production corpus comparison and RTD rollout remain pending until their
  evidence is recorded; the above is not an online acceptance claim.
