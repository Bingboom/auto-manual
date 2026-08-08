# Auto-Manual 自动说明书工具

Updated: 2026-08-07

Auto-Manual 将飞书结构化数据、共享 RST 模板、翻译记忆和受控资产，转换为
可评审、可追溯的多语言说明书，并输出 PDF、DOCX、IDML、HTML、Markdown 和 ZIP。

> 工程代码在 `auto-manual` 演进；业务发布在 `Hello-Docs` 运行。

## 工作流路线图

![Auto-Manual workflow roadmap](docs/readme-assets/auto-manual-roadmap.svg)

沿编号主路径工作；图底部的质量门禁是各阶段的验收条件。

## 视频演示

<!-- VIDEO_SLOT_START -->
> 视频位已预留。视频就绪后，建议用封面图链接到 GitHub、Bilibili 或其他播放页，
> 避免在 README 中直接加载大体积视频文件。
<!-- VIDEO_SLOT_END -->

## 六步流程

| 阶段 | 做什么 | 主要入口或产物 |
| --- | --- | --- |
| 1. 治理内容源 | 在正确源头维护文案、参数、术语和资产 | 飞书 phase2、[`docs/templates/`](docs/templates)、TM-B、资产注册表 |
| 2. 冻结输入 | 将目标数据、附件、页面清单和哈希固化 | `data/phase2/`、manifest、`bundle_sha256` |
| 3. 构建与检查 | 检查环境、数据和质量门禁 | [`build.py`](build.py) 的 `doctor`、`check`、`review` |
| 4. 评审与回写 | 在评审面修改，并把共性问题写回源头 | [`docs/_review/`](docs/_review)、`sync-review`、cloud-doc backport |
| 5. 生成输出 | 从同一冻结构建包生成多种交付格式 | PDF、DOCX、IDML、HTML、Markdown、ZIP |
| 6. 发布与追踪 | 经 Hello-Docs 发布，并核对线上与飞书状态 | Publish Queue、Read the Docs、飞书回读 |

## 快速开始

[`build.py`](build.py) 是统一入口。最小 US/EN 验证路径：

```bash
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py doctor --data-plane --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
python build.py check  --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
```

当前维护的冒烟基线是 `JE-1000F / US` 和 `JE-1000F / JP`。其他区域、语言、
新产线、资产接入和发布命令见[构建与运维指南](code-as-doc/build_doc_guide.md)。

## 关键规则

- **修改源头，不修改生成物：** 共享内容在 `docs/templates/`，结构化数据在飞书源表，
  评审后的目标专属修改在 `docs/_review/`；不要手改 `docs/_build/`。
- **先锁定范围：** 写入前确认型号、区域、语言、仓库、Base 和记录。
- **一个冻结包，多种输出：** 各格式可以采用不同排版，但不能分叉文案、规格、
  法务内容、术语或资产身份。
- **代码只改工程面：** `auto-manual/main` 单向同步到 `Hello-Docs/main`；不要直接
  修改 Hello-Docs 的工程树。
- **触发不等于完成：** 最终验收必须核对提交、产物、在线 URL 和飞书回读。
- **保护工作区：** `_build/`、`reports/version_tracking/` 和 `reports/releases/`
  可能包含用户或其他窗口的验证产物，不要擅自清理。

## 文档入口

| 想了解什么 | 从这里开始 |
| --- | --- |
| 第一次接手项目 | [`ONBOARDING.md`](ONBOARDING.md) |
| 完整命令和运维流程 | [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md) |
| 当前用户工作流和编辑规则 | [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md) |
| 工程面、业务面与飞书 Base 的关系 | [`user-guide/two_plane_map.md`](user-guide/two_plane_map.md) |
| 最短上手示例 | [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md) |
| 长期架构边界 | [`System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md) |
| AI Agent 操作规则 | [`AGENTS.md`](AGENTS.md) |

README 只保留路线图和最短入口。详细机制由上表中的权威文档维护，避免多处重复后
逐渐产生不一致。
