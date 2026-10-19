# IT-META-001：映射计数补充勘误

状态：生产方补充完成，等待独立复核关闭；不改变原稿内容与发布权限。

每语 `copy_by_page` 的实际条目数均为 **170**，`evidence` 列表均为 **169** 条。两者相差的是 `warranty_en.rst` 中 `YEARS` 的本地化键，供3年和2年保修徽标复用。计数按每页字典条目相加，不对同文去重，也不按网页出现次数计算。

旧生成脚本把 `len(evidence)` 写入 `mapped_native_entries` / `explicit_native_mappings`，source review 与 ledger继承了169这一计数。实际文案存在性检查遍历的是全部 `copy_by_page` 值，因此计数标签错误没有跳过第170项。本次重新核对八语的170个值，正文及图片alt/aria-label中均能找到；此项检查不代替独立原稿或视觉验收。

意大利语 `extra_spec_row` 单独保存原稿第45页的 `Corrente massima di cortocircuito e durata` / `1160A/860μs`，不属于上述170个字典条目，也不是计数差1的原因。该行在正文中存在，原稿结构有两处表示，因此意大利语结构试验为11项差异。

| 语言 | 固定候选 | YEARS本地化 | copy-map SHA256 |
| --- | --- | --- | --- |
| fr | fr-r4 | ANS | `21c64705dfd1e79d436f177c93079e4ccff298fa41e135d641a6a314981bbc3e` |
| es | es-r2 | AÑOS | `d683c84689d5a649909039c381ab7fa3fc61b4c296f66e6e19f40595a5176ccf` |
| de | de-r1 | JAHRE | `b0a91833a9c12fbedf894863ab5827f34a3e356756390e673bdaadbd81f30b3b` |
| it | it-r1 | ANNI | `b91742ab46eb02a99923c5d538a9c8db3945d9563d9df91954bd9603179ac2bc` |
| uk | uk-r1 | РОКИ | `2c6a03f3a441bb8508e33a996c55cffb22a2f06a41bead912f67381dd641b84d` |
| pt | pt-r1 | ANOS | `daf848b6afb8a38ab265b3aac79cefb73e1e0b54680f6e782444404c2966d281` |
| nl | nl-r1 | JAAR | `de7554b57efdaaf4b289e878e1d9f8445c151043f4ff61039efeffafb22f2ffb` |
| pl | pl-r1 | LATA | `60bfe06d622dee2d330649855b4c621706731e6f2b5603823bf1d76bc57c1d59` |

[机器可读记录与逐页数量](IT-META-001.json)。本勘误只更正统计标签；所有封存包、HTML、copy map、source review、ledger和manifest原字节保持不变。原始独立意大利语报告另行[原样归档](../it-r1-independent/acceptance.md)。UK/PT/NL/PL仍待独立原稿与视觉验收。
