# Auto-Manual

*One source of truth — every market's manual, in every format.*

Auto-Manual 将飞书结构化数据、RST 模板、翻译记忆和受控资产，转换为可评审、
可追溯的多语言说明书，并同源输出 PDF、DOCX、IDML、HTML、Markdown 和 ZIP。

## 工作流路线图

手册中心按冻结发布记录提供[独立语言切换](code-as-doc/dev/rtd_locale_navigation.md)，区分已验证单语与语言身份待核验的旧出版物。

Web 发布身份与旧链接兼容规则见[locale 发布契约](code-as-doc/dev/web_locale_publication_identity.md)。
封存源辅助文件的复制边界见[构建指南](code-as-doc/build_doc_guide.md)。

Web 发布产物可运行[本地只读检查](code-as-doc/dev/manual_operations_health_report.md)；本地通过不等于线上部署通过。
冻结目录也可运行[只读线上链接检查](code-as-doc/dev/manual_operations_online_health.md)，HTTP成功不等于版本验收。

Web profile 配合显式 `--lang` 会冻结完整配置语言源，再将所选语言投影为
`check`、Markdown 和 HTML 共用的规范 RST；边界见[说明](code-as-doc/dev/web_language_projection.md)。
这项本地构建能力不代表已接通独立语言发布。
审稿语言裁剪同时清理生成页副本和目录引用，原审稿文件保留；见[构建指南](code-as-doc/build_doc_guide.md)。
Web 队列支持显式语言的单语配置，约束与未释放的发布门禁见[队列契约](code-as-doc/dev/web_publish_locale_queue.md)。

![Auto-Manual workflow roadmap](docs/readme-assets/auto-manual-roadmap.svg)

内容源 → 冻结输入 → 构建检查 → 评审回写 → 多格式输出 → 发布追踪。

## 视频演示

<!-- VIDEO_SLOT_START -->
> 视频位已预留。视频就绪后，可用一张封面图链接到 GitHub、Bilibili 或其他播放页。
<!-- VIDEO_SLOT_END -->

## 快速开始

[`build.py`](build.py) 是统一入口。最小 US/EN 验证路径：

```bash
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py doctor --data-plane --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
python build.py check  --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
```

`check` 会在进入 Word/Web 导出前校验 FCC 的目标语言、结构和受控分栏标记；
manifest 中新增 FCC 语言但未补齐渲染契约时会直接失败。

## 只记住四条规则

- **修改源头，不修改生成物：** 共享内容在 `docs/templates/`，结构化数据在飞书源表，
  评审后的目标专属修改在 `docs/_review/`；不要手改 `docs/_build/`。
- **一个冻结包，多种输出：** 不同格式可以采用不同排版，但不能分叉文案、规格、
  法务内容、术语或资产身份。
- **代码只改工程面：** `auto-manual/main` 单向同步到 `Hello-Docs/main`；不要直接
  修改 Hello-Docs 的工程树。
- **触发不等于完成：** 队列验收读取阶段化 `delivery_ready / delivery_url`（Draft
  云文档、Publish IDML 交付包、Web HTML），并核对提交、产物和飞书回读；不读取已退役的 `Document link`。

## 文档入口

| 想了解什么 | 从这里开始 |
| --- | --- |
| 第一次接手项目 | [`ONBOARDING.md`](ONBOARDING.md) |
| 完整命令和运维流程 | [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md) |
| Web 发布：队列与 Git-only 输入、冻结快照、RTD 和本地版本封存 | [`code-as-doc/dev/web_publish_pipeline.md`](code-as-doc/dev/web_publish_pipeline.md)；[`OPS-04a 封存契约`](code-as-doc/dev/ops_04a_web_version_seal.md) |
| RTD 手册中心：首页、地区筛选与发布链接 | [`code-as-doc/dev/rtd_manual_portal.md`](code-as-doc/dev/rtd_manual_portal.md) |
| RTD 手册反馈：GitHub Issues 与发布后健康检查 | [`code-as-doc/dev/rtd_manual_portal.md`](code-as-doc/dev/rtd_manual_portal.md) |
| 当前工作流和编辑规则 | [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md) |
| 复用已有样式和完整组件 | [`code-as-doc/dev/style_component_usage_guide.md`](code-as-doc/dev/style_component_usage_guide.md) |
| 规格书结构化入库 | [`.agents/skills/spec-sheet-structured-intake/SKILL.md`](.agents/skills/spec-sheet-structured-intake/SKILL.md) |
| 工程面、业务面与飞书 Base | [`user-guide/two_plane_map.md`](user-guide/two_plane_map.md) |
| 最短上手示例 | [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md) |
| 公共 IR 的调用方与迁移边界 | [`Shared-source plan`](code-as-doc/dev/latex_indesign_same_source_plan.md) |
| 整本 IR → Web 收口与加电包日语验收 | [`执行目标与证据`](code-as-doc/dev/ir_document_closeout.md) |
| JS-100I 欧规英语 Web 目标与验收 | [`目标实现记录`](code-as-doc/dev/js100i_eu_en_web_acceptance.md) |
| JBP-3600A / EU / en Web 工程接入 | [`来源映射与验收记录`](code-as-doc/reviews/jbp3600a_eu_en_web_intake_2026-09.md) |
| JE-2000F / EU / en Web 工程接入 | [`来源映射与验收记录`](code-as-doc/reviews/je2000f_eu_en_web_intake_2026-09.md) |
| JE-2000E / EU / en Web 工程接入 | [`来源映射与验收记录`](code-as-doc/reviews/je2000e_eu_en_web_intake_2026-09.md) |
| ManualIR v2 中立 flow、v1 兼容与后续组件边界 | [`ManualIR v2 plan`](code-as-doc/dev/manual_ir_v2_neutral_flow_plan.md) |
| Web 共享层、产品骨架与目标差异如何继承 | [`Web presentation overlay`](code-as-doc/dev/web_presentation_overlay_plan_2026-09.md) |
| 长期架构边界 | [`System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md) |
| AI Agent 操作规则 | [`AGENTS.md`](AGENTS.md) |
| 钉钉悟空 MCP Bridge 源码与部署 | [`agent/wukong-bridge/README.md`](agent/wukong-bridge/README.md) |

README 只保留路线图、视频位和最短入口；详细机制由上表中的权威文档维护。
