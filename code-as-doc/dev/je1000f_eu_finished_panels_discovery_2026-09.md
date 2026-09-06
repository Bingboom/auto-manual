# JE-1000F/EU 含文字完整面板资产收口（5B）

日期：2026-09-05

源文件：`Jackery Explorer 1000 User Manual (JE-1000F) V2.0 EU-UK-2026-06-18.pdf`

源文件 SHA-256：`0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe`
页数与页面尺寸：92 页，368.787 × 524.692 pt

## 决策

JE-1000F/EU 的 Overview、Operation、Charging 统一消费源 PDF 中像素忠实裁切的、已包含文字和引线的完整面板图。`无字底图 + 本地化 HTML 文字/引线` 仅登记为待清偿的旧债，不是该目标的最终交付模式。

不将 Specifications、Warranty、LCD、Troubleshooting、Symbols 截图化；这些内容继续使用可搜索、可访问、可响应的原生 HTML 组件。

本轮覆盖 `data/model_languages.csv` 为 JE-1000F/EU 声明的全部语言：`en`、`fr`、`es`、`de`、`it`。每种语言 11 个槽位，共 55 张图：

- Overview：`product-overview.front`、`product-overview.right`
- Operation：`operation.main-power`、`operation.ac-output`、`operation.dc-usb-output`、`operation.energy-saving`、`operation.led-light`
- Charging：`reference.charging-ac-wall`、`reference.charging-solar-direct`、`reference.charging-solar-adapter`、`reference.charging-car`

## 源页映射

| locale | Overview | Operation | Charging AC | Solar / Car |
| --- | ---: | ---: | ---: | ---: |
| en | 8 | 11–14 | 16 | 17–18 |
| fr | 25 | 28–31 | 33 | 34–35 |
| es | 42 | 45–48 | 50 | 51–52 |
| de | 60 | 63–66 | 68 | 69–70 |
| it | 77 | 80–83 | 85 | 86–87 |

## 抽取与可追溯合同

- 坐标为 PDF 1-based 页码、top-left 原点、pt 单位。
- 每个资产由版本化 recipe 固定源文件哈希、源页、裁切框、locale、输出哈希和审批状态。
- Web composite manifest 同时固定 `content_sha256` 与由实际 review RST 投影得到的 `source_fragment_sha256`。
- committed fixture 仅承载可离线重放的批准资产；不写线上 Base，也不引入第二套运行时加载器。
- Overview 裁切排除页面 H1 和视图 H2，只保留完整产品图、图内标签和引线。Operation/Charging 以完整圆角面板边界外扩约 1 pt，避免截断边框。

## 已知源稿缺陷

德语 Overview 源页 60 的页面标题与视图标题误用西班牙语；前视图内第一条标签也保留了源稿中的西班牙语。德语车充源页 69 的图内“Vehicle”写成西班牙语 `Vehículo`。5B 不重绘或改写源图文字：H1/H2 不进入裁图并继续由 HTML 提供，面板内部则按源 PDF 像素忠实保留。这两项作为源内容缺陷单独追踪，不以 Web 资产生成阶段静默修字。

## 强制覆盖闸门

presentation 合同声明需要清债的 target、locale、slot 与允许状态。通用 Python 校验器只解释合同，不写 `JE-1000F` 型号特判。对受管目标，任何 required slot 为 `editable-fallback`、`missing`、重复或缺失时均阻断整本 IR/Web 构建。

验收要求：

1. 55/55 required slot 为 `approved-composite` 或 `finished-panel`。
2. DE/IT 重点检查 On/Off、Prerequisite/前提说明、图中文字和引线完整。
3. 五语言桌面与 390 px 移动端均无破图、无横向溢出。
4. 整本 IR 冷重放在禁止读取 RST/CSV 时仍成功，且资产哈希漂移会失败。
5. 资产 recipe 重放的 55 个输出哈希与 committed fixture 完全一致。
