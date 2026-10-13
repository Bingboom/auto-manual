# Optimization checklist: Milestone I (unknown-unknown probes and handover assurance)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6g. Milestone I: Unknown-Unknown Probes + Handover Assurance

Registered 2026-07-12 (operator-approved) from the workspace census ×
esp-docs comparison (see the espressif/esp-docs defensive-subsystem
inventory). Theme: auto-manual's defenses concentrate on **content
correctness**; the blind spots concentrate on **publication
sustainability** (links, language parity, environment drift, warning
debt) and **maintainer hand-over**. These are sensors first, fixes
second — each probe converts an unknown-unknown into a measured known.

- [x] PR I1: Language-tree parity check (探针·跨语言结构漂移; done 2026-07-13, #657)
  - Status: `done` — `tools/check_docs_lang_parity.py` wired into check:
    foreign-shell (script ratio), foreign lang-tag blocks, per-lang page-set
    completeness; known-exceptions CSV keeps pre-existing debt green. All
    three historical incident classes replicated in tests and tripped.
    First run caught live debt: the us-en line inherits the trilingual
    page_shared/en preface — trim decision pending with the operator.
- [x] PR I2: Build-warning ratchet (探针·警告债棘轮; done 2026-07-13, #658)
  - Status: `done` — `tools/warning_ratchet.py` + `-w` capture on every
    Sphinx run; staged enforcement (in-build hook reports by default,
    `AUTO_MANUAL_WARNING_RATCHET=strict` fails; standalone CLI always
    strict, missing baseline exits 2). sphinx-html baseline seeded; flip
    the in-build default to strict after 2–3 stable queue rounds. xelatex /
    extractor streams reuse the same engine when attached.
- [x] PR I3: Environment pinning + version provenance (探针·环境漂移; done 2026-07-13, #656; priority raised after #648)
  - Status: `done` — requirements.lock; `tools/toolchain_provenance.py`
    single collector (python/packages/xelatex/pandoc/InDesign/lock sha);
    doctor prints the block; release manifest embeds it (JSON + CSV).
    Probe caught real drift on day one (venv rebuilt on Python 3.14).
- [x] PR I4: Printed-URL inventory (探针·印刷外链; done 2026-07-13)
  - Status: `done` — `tools/printed_url_inventory.py` scan/check/liveness;
    tracked `data/printed_url_inventory.csv` (first scan: 6 targets — 4
    warranty mailboxes, jackery.jp, jp mailbox; liveness clean); QR targets
    register by hand in `data/printed_url_manual_entries.csv`; monthly ops
    rhythm updated (ops guide §4.8).
- [x] PR I5: Feishu base rebuild drill (探针·灾备演练; first drill run 2026-07-13)
  - Status: `done` — drill protocol + first measured run in ops guide §4.7:
    scratch base + 2 tables + fields + 25 seed rows restored from repo
    artifacts alone in **86s** (read-back verified). Headline finding: the
    schema mirror covers only 2/20 business tables — the other 18 tables'
    field structures live only in Feishu. Follow-up CLOSED same day:
    whole-base export committed (`bitable_schema/business_base_manifest.json`
    21 tables/366 fields + `tm_base_manifest.json` 2/58), complex fields
    carry rebuild detail (lookup source, link target, formula property);
    re-export rhythm documented in ops guide §4.7.
- [x] PR I0: ONBOARDING.md + cold-start drill protocol (接手保障)
  - Status: `done` — repo-root ONBOARDING.md is the single first-hour
    entrypoint (two-plane map, bus-factor register, golden-path drill);
    its quality is enforced by the quarterly cold-start drill (§7 of the
    file): a fresh maintainer or memory-less agent runs the golden path
    from repo docs alone; every blocker is a doc bug fixed same-day and
    logged in code_optimization_log.md.
- [x] PR I6: Repo-health metrics on the ops dashboard (接手保障·复杂度可见; done 2026-07-13)
  - Status: `done` — `repo_health_metric` on the ops face: worktree count,
    dirty files, tracked `docs/_build` files, tools module count and the
    largest module — complexity growth is now a monthly number; a rising
    trend is the signal to open a simplification workstream.
