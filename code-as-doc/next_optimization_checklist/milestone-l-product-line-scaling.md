# Optimization checklist: Milestone L (product-line scaling, Workstream W)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6j. Milestone L: Product-Line Scaling Execution (Workstream W)

Registered 2026-07-30, operator-approved same day (「按方案来 落PR 让codex开跑」).
The **authoritative per-PR breakdown lives in
[`architecture/scaling_execution_plan.md`](../architecture/scaling_execution_plan.md) §4**
(~76 S/M PRs with machine-verifiable done_when each) — this section tracks
stage-level progress only, to keep the two files from drifting. Execution
rules (validation ladder, golden-regenerate review exception, gate/stop
behavior, nightly report format) are the plan's §3 and bind every PR.

Entry rules: stages run in order; a stage's gated items wait for the
operator picks listed in the plan's §5; behavior-preserving stages (0–4a)
never require a gate to *start*. Reused item numbers (K2, K8 slices + the
snapshot file-lock, K13, K14, E1, I2's normalization prerequisite) tick their
original entries when the matching W-slice lands.

- [x] Stage 0: safety nets + silent-failure sensors (8 PRs, zero behavior)
- [x] Stage 1: CI/gate auto-scaling with product lines (7 PRs)
- [x] Stage 2: zero-code language onboarding = K13 (13 PRs; exit = fake-lang zero-Python proof)
- [x] Stage 3: clone-artifact generation, new region = one command (13 PRs)
- [x] Stage 4a: run throughput without concurrency-semantics change (18 PRs; incl. K8 all four Done-when items, E1 both slices)
- [x] Stage 4b: concurrency sub-stage (3 PRs; verified claim lease, per-record workflow domains + Vercel mutex, and bounded selective artifacts complete)
- [x] Stage 5: behavior close-out + expansion pre-gates (14 PRs; strict flips, placeholder-ization template halves, CJK trio, K14, K15 design doc)

Engineering close-out: all registered Stage 0–5 implementation slices are on
`main` as of 2026-07-31. The operator released the remaining Stage 4 and Stage
5 gates with 「814批准：Stage4全部放心；Stage5全量放行」. The F6 production seed
for `pv_input_range`, `dc_input_connector`, and `ups_transfer_time` is complete
for the current US/EU/AU/KR/pt-BR document keys; the exact readback and build
evidence is recorded in
[`reviews/workstream_w_closeout_2026-07-31.md`](../reviews/workstream_w_closeout_2026-07-31.md).
The first timed K14 rollback drill and the next real product-line ≤2
operator-day measurement remain operator-owned field evidence, not unfinished
engineering checkboxes.

Operator gate summary: the plan's §5 (workflow edits, `export_idml --model`,
Feishu column list, promotion-contract carrier, F6 seeds, queue concurrency
live test, strict flips, CJK/IDML line decision, K15 approval, and the three
report-only items: K3 new-binary LFS routing evidence, bus-factor report,
HTML_link alias semantics).
