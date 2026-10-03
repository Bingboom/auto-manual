# JBP-3600A EU 最终确认项

技术验收已完成：原八语全文/版式验收，加上对提交 `44b6ce6101141681a6cf75c9fdfef05b8aef93b0` 的[九语最终差量独立验收](review/transparent-final-independent/acceptance.md)，共同覆盖英语 r6、法语 r5、西语 r3、德/意/乌/葡/荷/波 r2。新差量检查了每份包、实际 HTML/IR、所有图片和桌面/手机布局；36 张稳定截图通过。旧封存与新制作者证据均保持原字节。

这些是候选技术验收结论，不是操作者批准或上线授权。[原英语正式页](https://ht-doc.readthedocs.io/JBP-3600A/EU/en/md/manual_jbp3600a_eu.html)保持原发布版本。

## 需要操作者裁定的三项

| 确认项 | 具体对象 | 确认后动作 |
| --- | --- | --- |
| 英语 r6 作为新基线 | [英语 r6 页面](http://127.0.0.1:56059/en-r6/manual_jbp3600a_eu.html)：锁扣深底白字、手机最小 14px、章节留白、保修长标题换行，以及两张高分辨率透明符号复用；CSS 时钟保持 3s | 登记这份精确 IR、CSS、素材及桌面/手机证据的批准身份。 |
| 德语警示图文错配 | 当前按原稿：禁止拆卸图配 `Vermeiden Sie Hitze.`，禁火图配 `Demontieren Sie das Produkt nicht.` | 明确保留原稿，或批准交换两条说明。建议更正配对；获批后另作小修订与定向验收，不改旧封存。 |
| 意语及其余原稿差异 | 意语拓展线原稿标 `Cavo di ricarica CA`，规格多一行 `1160A/860μs`，保修正文没有 36 个月句子但有 3+2 徽标；[其余已列明原稿差异](REVIEW.md#待确认的原稿差异) | 明确保留原稿作为受审例外，或提供更正依据后作差量修订。不得自行补写英文内容。 |

×5 继续按 JBP 原稿保留；HTE152 ×8 未代入。设备 WEEE 有底杠、电池 WEEE 无底杠的语义区分保持不变。旧图本已有 alpha，本轮是高分辨率透明素材复用，不是首次去底色。

## 工程后续和发布范围

三项裁定落实后，工程侧还需登记英语基线与八语适用性、同步最新 main 的 `tools/web` 模块迁移、补齐相应验证并准备 PR。现有候选保持 `pending_source_review` 和 `publication_eligible=false`；独立验收没有绕过门禁。

[依赖快照](review/transparent-symbol-r1/publication-dependencies.json)是 2026-10-03 的已核查状态：PR1409 的英语继承门禁尚未合入，本分支仅只读引用其比较实现；PR1416 是共享素材复核参考，不是 JBP 代码依赖。提交 PR 或发布前应重新查询这些状态，不能把旧快照当最终合并依据。

本次拟发布范围仅 `JBP-3600A/EU/{en,fr,es,de,it,uk,pt,nl,pl}`。最终合并/发布仍需对应的新批次授权登记及全部检查通过；MA-234 仅覆盖已完成的原英语稿。保持 Git-only，不写飞书表、队列、HTML_link 或资产注册表。此次只归档独立验收与确认材料，未执行新的合并发布。

完整九语预览、哈希、差量及素材对照见[制作者确认包](review/transparent-symbol-r1/README.md)；独立报告原字节及采纳/排除截图清单见[独立验收回执](review/transparent-final-independent/receipt.json)。
