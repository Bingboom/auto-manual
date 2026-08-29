# JBP-2000B_US S6 对账报告 — 管线侧验收（2026-08-28）

S6 分两半：**管线侧机械验收**（本页，已完成）与**操作者 InDesign 实排轮**
（待办清单见 §4，完成后回填 §3 的悬置项）。构建基线：main `5db6f6f9`
（#955 合入后），对账对象：出货书
`Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf`
（28 页，sha256 `c29a14da…`，pin 在装配契约内）。

## 1. 机械验收 — 11/11 通过

| 检查 | 结果 |
|---|---|
| 物理页数 = 出货书页数 | ✅ 28 = 28 |
| 源页匹配率 | ✅ 43/43（100%） |
| 裁切尺寸 | ✅ 368.754 × 524.659 pt，与出货书声明一致 |
| 包结构 | ✅ 28 spreads / 277 stories |
| 链接资产 | ✅ 29 个 production 链接全部在盘；交付 zip 收 41/41、0 缺失 |
| 文件名当正文 | ✅ 0 处 |
| 透明终止载体 | ✅ 6 个，全部独立 frame 且 fill/stroke = None |
| 三语同路径 | ✅ en/fr/es 正文组合类型集合一致（8 种共享 composition） |
| 内容掉落 | ✅ `skipped_raw = 0` |
| 可回溯 | ✅ source_trace + designer_checklist + missing_assets_report 齐套 |
| 回归门 | ✅ CI 18/18（含 3156 tests、三语 × 密度 golden、边界闸门） |

## 2. 已知差异四分类（管线侧可判部分）

| 差异 | 分类 | 说明 |
|---|---|---|
| 字体不随包交付 | **finishing-layer** | 交付 zip 字体 opt-in（授权原因，PR #615/#616 的设计）；`fonts_manifest.md` 列清单，InDesign 主机需自装 |
| 终止标记空间需最终化扩展 | **finishing-layer** | 载体已按 `tf_terminal_carrier_group_*` 预留，`indesign_finalize.jsx` 只碰载体（源码级测试钉住） |
| 封面/背板为置入成品图 | **finishing-layer** | `cover_jbp2000b-en.pdf` / 背板 QR 按批准资产置入，印前微调属实排轮 |
| 结构性管线缺口 | **无**（计划级） | 28/28 页、43/43 源页精确匹配。对比：JE-1000F/US 管线 66 页 vs 出货 58 页——BP 是首条计划级零结构分歧的产线 |
| 数据缺口 | **无** | spec 11 / lcd 2 / trouble 7 行全渲染，资产零缺失 |
| accepted-degradation | **待操作者裁决** | 管线侧无预置项 |

## 3. 悬置项 — 由实排轮回填

- [ ] 逐页视觉对照出货书 28 页（同页并排，非只看新产线自身）
- [ ] InDesign preflight：零 overset、零缺字体、零坏链接
- [ ] 每处视觉差异按四分类记入本表并计数
- [ ] 操作者对每条 pipeline-gap 裁决（S6 退出条件）

## 4. 实排轮操作序

1. 解压交付 zip（`Links/` 已相对化），安装 `fonts_manifest.md` 所列字体
2. 打开 `manual_jbp2000b_us.idml`，跑 `indesign_finalize.jsx`
3. 导出 PDF，与出货书逐页并排；差异记入 §3
4. 反馈通道：`layout_feedback.md`（版式）；文案改动回源表/模板，不改 IDML

## 5. 对 rollout 的直接输入

计划级零结构分歧意味着 rollout 重定范围时，BP 线不携带 JE 线那类
66-vs-58 的历史基线债；后续产线以本报告的机械验收清单为 S6 前置门
（已固化在 `dev/style_component_usage_guide.md` §6–§8 与
`tests/test_idml_page_boundaries.py`）。
