# JBP-2000B_US S6 对账报告 — 最终收口（2026-08-30）

S6 分两半：**管线侧机械验收**与**操作者 InDesign 实排轮**，现均已完成。
初始构建基线：main `5db6f6f9`
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
| 字体最初不随包交付 | **finishing-layer（已解决）** | #971 改为随包携带 Noto Sans / Noto Sans Symbols / Noto Sans Symbols2 与 OFL；最终原生预检 0 缺字体、0 缺字形 |
| 终止标记空间需最终化扩展 | **finishing-layer（已解决）** | 载体按 `tf_terminal_carrier_group_*` 预留；真实 `indesign_finalize.jsx` 实排后 0 overset |
| 封面/背板为置入成品图 | **finishing-layer（已接受）** | `cover_jbp2000b-en.pdf` / 背板 QR 按批准资产置入；这是交付方法差异，不构成视觉缺陷 |
| 结构性管线缺口 | **无**（计划级） | 28/28 页、43/43 源页精确匹配。对比：JE-1000F/US 管线 66 页 vs 出货 58 页——BP 是首条计划级零结构分歧的产线 |
| 数据缺口 | **无** | spec 11 / lcd 2 / trouble 7 行全渲染，资产零缺失 |
| 当前内容源与历史参考稿存在两类差异 | **accepted-degradation（已接受）** | 当前内容源使用 `EN` 而历史参考稿显示 `US`；当前内容源目录顺序与历史参考稿不同。二者均保留当前内容源 authority，不按截图反写事实 |

## 3. 实排轮回填与最终计数

- [x] 逐页视觉对照出货书 28 页（同页并排，非只看新产线自身）
- [x] InDesign preflight：0 overset、0 missing fonts、0 missing glyphs、
  0 bad links
- [x] 每处视觉差异按四分类记入本表并计数
- [x] 操作者完成 `pipeline-gap` / `accepted-degradation` 裁决

计数单位是**独立根因类别**，不是同一根因跨语言、跨页重复出现的次数：

| 分类 | 已观察 | 未关闭 | 最终裁决 |
|---|---:|---:|---|
| pipeline-gap | 0 | 0 | 无结构或渲染管线缺口；28/28 页、43/43 bindings |
| finishing-layer | 3 | 0 | 字体携带与终止载体已由 #971 / 实排关闭；置入封面/背板接受为交付方法 |
| data-gap | 0 | 0 | 结构化行、资产与绑定完整；内容源差异不是缺失数据 |
| accepted-degradation | 2 | 0 | 接受 `EN`/`US` 标签与目录顺序两类 source-authority 差异，仅用于本次 S6 slice 收口 |

操作者裁决（2026-08-30，“继续，收尾这个 checklist”）：S6 以 0 条
pipeline-gap 收口，并接受上表 2 类 source-authority 差异。此裁决不等于
approved reference-layout 晋升；JBP 装配继续保持 `candidate`、
`production_eligible=false`。

## 4. 实排轮执行记录

1. [x] 从全新临时目录解压交付 zip；`Links/` 相对化，41/41 链接齐全，
   portable fonts 与授权说明齐全
2. [x] 打开 `manual_jbp2000b_us.idml`，运行 `indesign_finalize.jsx`；
   InDesign 2026 `21.0.1.6` 原生预检全绿
3. [x] 导出 28 页 PDF，与出货书 28 页逐页并排；差异按 §3 归档
4. [x] 解包前后 PDF 的 28 页渲染一致；未把版面差异直接改进 IDML，
   文案/目录 source-authority 差异保留在源数据边界

## 5. 对 rollout 的直接输入

计划级零结构分歧意味着 rollout 重定范围时，BP 线不携带 JE 线那类
66-vs-58 的历史基线债；后续产线以本报告的机械验收清单为 S6 前置门
（已固化在 `dev/style_component_usage_guide.md` §6–§8 与
`tests/test_idml_page_boundaries.py`）。

S6 已完成；rollout 仍需逐项重新定界，不能由本次收口自动视为完成。
