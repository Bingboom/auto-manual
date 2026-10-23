# Hello-Docs 业务面

*让产品内容成为可信、可复用、持续演进的知识资产。*

Hello-Docs 是产品资料的业务面：存放业务数据与语料资产，发布网页说明书，
按需构建 Word、PDF、IDML 等多格式文档，并保留发布与追溯记录。

资料写作在私有的资料开发工作台 Hello-Docs-Review 进行；代码、模板和工具在工程面
[auto-manual](https://github.com/Bingboom/auto-manual) 修改，合入后单向同步到这里。

## 这里放什么

| 内容 | 位置 | 怎么维护 |
| --- | --- | --- |
| 已发布的网页说明书 | [`docs/publish/`](https://github.com/Bingboom/Hello-Docs/tree/main/docs/publish) | Web Publish 写入发布候选；只含该目录的发布 PR 合入 `main` 后，Read the Docs 重建资料库 |
| 知识资料与业务数据 | [`docs/knowledge/`](https://github.com/Bingboom/Hello-Docs/blob/main/docs/knowledge/README.md) | 在本仓库开内容 PR，例如说明书工作台的数据快照、知识问题台账、分享稿 |
| 产品数据与翻译语料 | 业务飞书 base：文档构建（phase2 源表）、TM-B 翻译记忆、发布文档管理 | 在飞书维护，构建时冻结为快照；ID 见[双平面地图](/user-guide/two_plane_map.md) §1.1 |
| 业务账本 | 本地 checkout 的 `reports/` | 修订台账、TM 命中率等，日常命令见[闭环运营手册](/user-guide/closed_loop_ops_guide.md) |

`docs/publish/` 和 `docs/knowledge/` 之外的文件都是 auto-manual 的同步副本，下一次同步会覆盖：
**不要在这里改代码、模板或文档。**

## 在这里做什么

- **发布网页说明书：** 发布流程与冻结快照规则见 [Web 发布指南](/code-as-doc/dev/web_publish_pipeline.md)。
- **按需构建多格式文档：** 在飞书「文档构建表」发起 Start Review、Build Draft Package 或 Publish，
  队列在本仓库的 Actions 运行；步骤见[快速开始](/user-guide/quick_start_guide.md)。
- **维护知识资料与业务数据：** 按 `docs/knowledge/` 的 README 开内容 PR。
- **查阅已发布资料：** 说明书资料库、知识库和说明书工作台页见 [RTD 门户指南](/code-as-doc/dev/rtd_manual_portal.md)。

## 三个仓库

| 仓库 | 角色 | 在那里做什么 |
| --- | --- | --- |
| [auto-manual](https://github.com/Bingboom/auto-manual)（公开） | 工程面 | 修改代码、模板、共享组件、Skill 和文档，跑 CI；合入后同步到另外两个仓库 |
| **Hello-Docs**（本仓库，公开） | 业务面 | 存放业务数据与语料资产，发布网页说明书，按需构建多格式文档 |
| [Hello-Docs-Review](https://github.com/Bingboom/Hello-Docs-Review)（私有） | 资料开发工作台 | Agent 调用全部基础设施、数据、模板和语料写作；审核稿在私有站点审阅 |

审核通过的工作台稿件作为批准原稿进入本仓库发布与追溯，这一衔接尚在建设中。
分工、同步通道和飞书 base 见[双平面地图](/user-guide/two_plane_map.md)；
定位与能力边界见[项目定位](/code-as-doc/architecture/Hello_Docs_Positioning.md)。

> 本页由 auto-manual 的 `mirrors/Hello-Docs/README.md` 同步而来，修改请在 auto-manual 提 PR。
