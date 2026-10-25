# Hello-Docs-Review 资料开发工作台

*让产品内容成为可信、可复用、持续演进的知识资产。*

这是 Hello-Docs 的资料开发工作台（私有）。在这里把现有的基础设施、数据、模板和语料全部调用起来，
由 Agent 写作说明书等资料，人负责审核。基于数据和模板的自动构建按需使用，不是写作的前提。

稿件含未发布的地区版本、研发数值和待确认问题，只保存在本仓库，
不得复制到公开的 auto-manual 或 Hello-Docs；同步任务也会拦截。

## 可以调用什么

| 资源 | 在哪里 | 怎么用 |
| --- | --- | --- |
| 基础设施 | 本仓库里同步自 auto-manual 的工具、共享组件与样式、Skill | 按 [AGENTS.md](/AGENTS.md) 和各 Skill 调用；工具需要改时去 auto-manual 提 PR |
| 数据 | 业务飞书 base（文档构建、发布文档管理）、产品规格书、[`manual_sources/`](/manual_sources) 里的冻结源包 | 以读取为主；写实时表须操作者批准并回读，规则见 [lark-cli-bitable-ops](/.agents/skills/lark-cli-bitable-ops/SKILL.md) |
| 模板 | [`docs/templates/`](/docs/templates)、骨架、共享组件与[样式定义](/docs/renderers/contracts/STYLE_DEFINITION.md) | 作为结构与表达参考；复用前核对目标产品、市场、语言和版本 |
| 语料 | TM-B 翻译记忆、已发布的多语言说明书 | 优先复用已批准措辞，新增翻译单独统计；查询见 [bitable-translation-memory](/.agents/skills/bitable-translation-memory/SKILL.md) |

## 怎样写

1. 在 Claude Code 或 Codex 会话中加入本仓库，说明要写哪份稿、参考哪本说明书、依据哪份规格书。
2. Agent 按 [`manual-review-draft`](/.agents/skills/manual-review-draft/SKILL.md) 等 Skill 继承参考稿的结构、措辞和插图，
   按目标规格替换参数，把建议和疑问写进审核意见。
3. 每轮修改形成一个新版本；提交到 `main` 后，[私有审核站](https://ht-docs-review-doc-lib.readthedocs-hosted.com/)
   自动重建，登录后阅读。
4. 目录结构、`draft.json`、颜色约定和版本规则见
   [审核稿编写指南](https://github.com/Bingboom/Hello-Docs-Review/blob/main/docs/review-drafts/README.md)。

审核通过的稿件作为批准原稿进入 Hello-Docs 发布与追溯，这一衔接尚在建设中。

## 边界

- 本仓库只维护 `docs/review-drafts/`；其余文件是 auto-manual 的同步副本，下一次同步会覆盖。
- 相似产品的措辞和参数不能当作目标事实；安全、警示、合规和规格须有依据，没有依据的留在审核意见里。
- 实时飞书表、TM-B 和正式模板的写入各有批准流程，写作过程不直接改动它们。

## 三个仓库

| 仓库 | 角色 | 在那里做什么 |
| --- | --- | --- |
| [auto-manual](https://github.com/Bingboom/auto-manual)（公开） | 工程面 | 修改代码、模板、共享组件、Skill 和文档，跑 CI；合入后同步到另外两个仓库 |
| [Hello-Docs](https://github.com/Bingboom/Hello-Docs)（公开） | 业务面 | 存放业务数据与语料资产，发布网页说明书，按需构建多格式文档 |
| **Hello-Docs-Review**（本仓库，私有） | 资料开发工作台 | Agent 调用全部基础设施、数据、模板和语料写作；审核稿在私有站点审阅 |

站点、同步与构建见[审核稿私有站](/code-as-doc/dev/rtd_manual_portal/review-drafts-site.md)；
分工见[双平面地图](/user-guide/two_plane_map.md)；定位与能力边界见[项目定位](/code-as-doc/architecture/Hello_Docs_Positioning.md)。

> 本页由 auto-manual 的 `mirrors/Hello-Docs-Review/README.md` 同步而来，修改请在 auto-manual 提 PR。
