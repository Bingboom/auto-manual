# RTD portal: 网页说明书的定位与价值

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## Band and page (2026-11-04)

The positioning of web manuals, in the operator's words, shows on two surfaces:

- **A band on the manual-library home**, after the catalog (zone 5 of the
  [home page layout](manual-center.md#page-layout)). The first screen stays the search hero.
- **An internal page**, `workspace/positioning/index.html` (知识库 · 定位与价值), with its own entry
  in the sidebar's 知识库 group.

Both RTD projects serve the same home page, so the copy has two audiences:

| `RTD_SITE_ROLE` | Band on the home page | Page |
| --- | --- | --- |
| `manuals` (public) | title, one sentence and three reader points (便捷阅读, 版本清楚, 持续更新): only what a reader can use today, with no links, status tags, internal names, governance or AI wording | not built |
| unset or `combined` (private) | eyebrow, heading and subtitle, then the four themes (便捷阅读, 机器可读, 内容治理, 知识积累), each with its facet keywords and a status tag, linking to its section of the page | built |

Only the public block reaches public HTML: `band_context(..., internal=False)` carries no internal copy. The
`manuals`-role build in `tests/test_rtd_portal.py` checks the band and the absence of internal words and of
the page; the combined build checks that each theme link lands on an existing section.

## Copy and status

`tools/rtd_portal_assets/web_manual_value.yaml` (schema `hello-docs-web-manual-value/v1`) holds both blocks.
`tools/rtd/web_manual_value.py` reads and validates it, and a malformed file fails the build.

The page opens with one positioning line: 网页说明书是已批准说明书的可信发布源，人能读，机器能读，团队能持续维护和复用.
The key idea 「已批准的历史内容，不天然等于可直接复用的标准知识。」 stands under it as the 总纲. The first
level is one card per theme with its name, status and one sentence (`summary`). Each card folds its 现状 list,
one line per facet, and its 核心原则 under 「现状与原则」. The page is kept to one screen on purpose (operator,
2026-11-04: too much content, no clear hierarchy). It has no long-term-direction block.

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
- 机器可读: 部分可用. The machine-readable export and its checked receipt are produced at build, and the
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
on the page. When a facet's state changes, edit its status and note in the YAML: the tags on the band and on
the page follow.

Rollback: revert the change. Frozen manuals, short aliases and search are unaffected.
