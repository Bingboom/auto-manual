# JE-2000F EU batch 1465 Web candidate

Candidate for pt, nl, pl only. Adds the six reviewed PDF safety notices and removes duplicate Portuguese and Dutch UPS prose and caution blocks. The original frozen release is retained. AC labels, DC glyphs, native HTML components, assets, App sections and the other six languages are unchanged.

Source: JE-2000F_修正版_竖版.pdf, physical pages 124/125, 142/143, 160/161. Native IR is authoritative; MyST is replayed through tools.web.frozen_ai_web.replay_package. batch_1465_changes.json retains exact prior blocks and added text. No review colours are imported.

Status: `operator-approved-git-only-release`. On 2026-10-10 the operator reviewed the 1280/390 renderings and decided “按波兰语的顺序调，译文直接用，上线提交发布”: in pt and nl the retained UPS CAUTION callout now precedes the WARNING callout, as in the single-copy Polish chapter, and the six supplied translations are published as delivered. `finalize_release.py` applies these decisions idempotently (block order only, visible text unchanged), marks each IR publication-eligible with the hash-bound `approval.json`, replays the MyST and refreshes `verification.json` and `source_manifest.json`; `tests/test_je2000f_eu_batch1465_release.py` checks the binding, the order and cold replay.

The engineering PR is merged by operator review (AGENTS.md §8.6). Afterwards the Git-only release seals `seal_frozen_web_evidence` per language at the merged main commit and opens a Hello-Docs `docs/publish/**`-only PR. No Feishu write, review re-seed or queue row is used; the old EU queue row points at main with a recorded failure and must not be reused for this source.
