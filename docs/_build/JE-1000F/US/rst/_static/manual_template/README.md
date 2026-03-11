# Manual Template Images

`docs/templates/page_en`、`docs/templates/page_eu`、`docs/templates/page_jp` 里的图片都统一引用这里的公共默认图。

规则：

- 默认图放在 `docs/_static/manual_template/...`
- review 覆盖图放在 `docs/_review/<MODEL>/<REGION>/overrides/_static/manual_template/...`
- 覆盖图必须和默认图使用同一段相对路径
- 构建时如果发现 review 里有同路径文件，会优先使用 review 覆盖图

示例：

- 默认图：`docs/_static/manual_template/page_jp/03_product_overview_placeholder/slot_01.jpg`
- JP review 覆盖图：`docs/_review/JE-1000F/JP/overrides/_static/manual_template/page_jp/03_product_overview_placeholder/slot_01.jpg`

槽位映射见 `docs/_static/manual_template/mapping.json`。
