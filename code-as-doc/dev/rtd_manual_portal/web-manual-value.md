# RTD portal: 网页说明书的定位与价值

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## Band and home line

The positioning of web manuals, in the operator's words, shows on two surfaces:

- **A band on the manual-library home**, after the catalog (zone 5 of the
  [home page layout](manual-center.md#page-layout)). The first screen stays the search hero.
- **The one line under 知识库首页's title** (the `tagline`), private site only.

Since the front cleanup (operator review 2026-11-17: the front is for product colleagues, not for
maintainers) both RTD roles show the reader-facing band: title, one sentence and three reader points
(便捷阅读, 版本清楚, 持续更新), with no links, status tags, internal names, governance or AI wording.
`tools/rtd/portal.py` calls `band_context`, which returns only that public view, in both roles. The 定位与价值 section of
知识库首页 (`#value`; 2026-11-04 to 2026-11-05 a page of its own, then a home section) and the private band's
theme links to it are gone; the internal themes stay in the YAML, and the internal band branch of `band_context` was
removed on 2026-11-17.

The `manuals`-role build in `tests/test_rtd_portal.py` checks the band and the absence of internal words and
of the knowledge base; the combined build checks that its band carries no link or status.

## Copy and status

`tools/rtd_portal_assets/web_manual_value.yaml` (schema `hello-docs-web-manual-value/v1`) holds both blocks.
`tools/rtd/web_manual_value.py` reads and validates it, and a malformed file fails the build.

知识库首页 opens with the positioning line: 网页说明书基于印刷版 PDF 转录：人能读，AI 能读，团队能持续维护和复用.
The internal themes (one per theme with its name, status, `summary` and facets) are kept in the YAML but
shown on no page since 2026-11-17. The theme formerly called 机器可读 is 「AI 可读」 (operator, 2026-11-05).

The copy says what the web manuals do, with no defensive caveats: this is the team's own knowledge base
(operator, 2026-11-04). So there is no 总纲, no 核心原则 and no long-term-direction block; the one legend only names the status marks.
What is unfinished shows only as a status tag, and `tests/test_rtd_web_manual_value.py` rejects the old
caveat phrasings.

Each 现状 facet carries a status from the 系统建设 page's vocabulary: `available` 可用, `validated` 已验证,
`in_progress` 建设中 or `planned` 已规划. A planned facet must name its REV. REV ids (`revs`) are evidence for
reviewers and are never shown. The theme tag is derived from the facets and never written by hand:

- every facet available: 可用;
- any facet available or validated, the rest not: 部分可用 (drawn as the outlined 可用);
- every facet planned: 已规划;
- otherwise: 建设中.

On 2026-11-04 that gives:

- 便捷阅读: 可用. Shared components and theme, QR codes that open the model's web manual, and search by
  model, name or text on phone and desktop.
- AI 可读: 部分可用. The machine-readable export and its checked receipt are produced at build, and the
  DingTalk bot answers from them ([EU manual query](../eu_manual_query.md)). Coverage is EU only and the
  content is extracted from the published HTML, not generated from the same source; see the
  [positioning doc](../../architecture/Hello_Docs_Positioning.md) §6.
- 内容治理: 部分可用. Version tracing and reader feedback (an after-sales link on every page, plus site
  analytics) are available; 质量改进 is in progress, as the positioning doc §7 records.
- 知识积累: 建设中. The workbench reuses data, templates and corpus under
  [REV-47](../manual_revitalization_execution.md#rev-47). Exporting knowledge candidates from approved drafts is
  the planned second part of [REV-48](../manual_revitalization_execution.md#rev-48).

The copy writes no counts, because they change with every release; 说明书工作台 reads them from the publish
manifest. `tests/test_rtd_web_manual_value.py` fails on any digit outside the REV ids, and on a REV id shown
on 知识库首页. When a facet's state changes, edit its status and note in the YAML.

Rollback: revert the change. Frozen manuals, short aliases and search are unaffected.
