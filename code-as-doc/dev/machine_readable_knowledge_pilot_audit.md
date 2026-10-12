# 欧规知识观察 Phase 2a 试点验收记录（P2-4）

Status: done · Date: 2026-10-11 · 计划：[`machine_readable_knowledge_observation.md`](machine_readable_knowledge_observation.md) §7 P2-4、§8

## 1. 范围与方法

对象：观察命令（含本 PR 的修正，生成器 `manual-observations/0.4`）在 10-11 本地重建上的产物。
重建用 Hello-Docs main `5c0a76ef` 与 auto-manual main `7c1a80a`，命令与 RTD 相同（计划附录 C）；
`ht-doc.readthedocs.io` 在本环境仍无法访问，线上复核待补。产物覆盖 109 个 EU 版本：
3,336 条知识条目（警示 1,007、安全 1,804、合规 525）、1,410 条关系。

样本是计划 §7 建议的五个型号（每个 9 个单语版本），加上全量 8 条 `high` 齐套候选。`high` 是
D14 门槛的对象，只出现在印刷修订号相同的版本之间，10-11 只有 JE-2000E、JE-2000F 两个型号有。

| 型号 | 选择理由 | 条目 | 齐套关系 | 其中带差异主张 |
| --- | --- | ---: | ---: | ---: |
| JE-3000C | 谱系差异、UPS | 334 | 50 | 20 |
| JE-1000H | 拆词标签、batch 1465 | 340 | 51 | 23 |
| JE-3600A | 较新、语言混入、等级词不统一 | 332 | 38 | 7 |
| JBP-2000B | 呈现差异、配件 | 270 | 31 | 5 |
| JS-100I | 功能简单、太阳能板 | 195 | 22 | 3 |
| JE-2000E、JE-2000F | 全部 `high` | | | 8 |

做法：

1. **差异主张逐条核对**：齐套关系中的缺失、等级不一致、数字不一致共 66 条（`high` 8、`medium` 21、
   `low` 37），逐条对照网页原文，判为真实差异（内容确实缺失或不一致）、可解释差异（内容在，
   只是呈现方式、位置或谱系不同，D14 计入确认）或误报（主张不成立）。
2. **对齐抽查**：试点型号中没有差异主张的 134 个完整簇，`high`（数字锚定）35 个、`low` 22 个全部
   核对，`medium` 77 个抽 20 个。
3. **试点外的 `medium`**：另外 6 个型号的 12 条 `medium` 也逐条核对，用来判断 `medium` 能否交付。
4. §8 的其余各项用脚本在全量产物上检查（§5）。

核对中发现的规则缺陷先在本 PR 修正（§3.1），再用修正后的产物重做全部核对；下文数字均为修正后的结果。

## 2. 结果

| 验收项（计划 §8） | 结果 |
| --- | --- |
| 身份 | 通过。3,336 条条目都有 `manual_variant_id`、`source_ref`、`content_sha256`，`knowledge_id` 无重复；1,410 条关系的每个成员都带 `knowledge_id`、`manual_variant_id` 与 `source_ref`。 |
| 证据 | 通过。条目与 `hits` 中 762 个不同的 `source_ref`，锚点都在网页中存在（其中 8 条位于首个标题之前的引言，锚点为空，指向网页开头）；每条关系至少有一个成员带 `source_ref`；每个 `absent_in` 都写明搜索范围、`revision_alignment` 与 `html_sha256`。 |
| 如实 | 通过。`status` 只有 `extracted` 与 `candidate`，产物中没有 `reviewed` / `approved`；主题为空的条目都带 `topic_unknown`，等级未知的都带 `severity_unknown`；合规条目一律 `applicability: unknown`。 |
| 确定性 | 通过。同一语料两次运行，产物字节一致（9,817,277 字节）。 |
| 新鲜度 | 通过。模拟改动：在 JE-3000C/EU/nl 的 0 ms 警示末尾加一句，并改该版本的 `html_sha256`。只有这 1 条条目 stale（其余 3,335 条 fresh）；45 条关系 stale，即引用该条目的 2 条加上 `absent_in` 含该版本的 43 条，与按计划 §6.2 的规则推算的集合完全一致。 |
| 兼容 | 通过。观察相关模块只被 `observe` 命令导入，RTD 构建与 `manifest` 命令不导入。与 P2-0 时的重建相比，109 份 EU 文档除 `published_at` 外一致，网页 HTML 字节一致，清单只有随 `published_at` 变化的哈希不同。查询插件测试 18/18 通过，插件的真实语料审计脚本在 10-11 本地重建上通过。 |
| 试点精度 | 通过。`high` 8/8 确认（D14 门槛 80%）；`medium` 21/21 确认（真实 20、可解释 1）；全部误报记录了原因（§3.3）。 |
| SSOT | 通过。产物写在不入库的 `reports/knowledge_observations/`，不进入 `docs/publish/**`；本 PR 不改任何权威源，问题只以清单形式（§3.2）交内容负责人。 |

各档精度：

| 档 | 主张 | 真实差异 | 可解释差异 | 误报 | 确认率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high`（全量） | 8 | 8 | 0 | 0 | 100% |
| `medium`（试点） | 21 | 20 | 1 | 0 | 100% |
| `medium`（试点外） | 12 | 9 | 2 | 1 | 92% |
| `low`（试点） | 37 | 7，另 9 条部分属实 | 18 | 3 | 不交付 |

完整簇的对齐：`high` 35/35、`medium` 抽查 20/20、`low` 21/22 正确。唯一的错配在 JE-3600A/EU/fr：
法文版安全章节没有英文版的引导句（"Always follow these basic precautions…"），没有锚点的对齐
把这句配给了法文列表的第一条，连带产生 §3.3 的一条误报。

8 条 `high` 只对应两个问题（JE-2000E、JE-2000F 的 de/es/fr/it/uk 没有 EU 法规章节），样本小且
彼此相关。门槛按 D14 通过，但更能说明规则质量的是 `medium`：全量 33 条中 32 条确认。

## 3. 发现

### 3.1 已在本 PR 修正

试点核对出的误报来自四处规则缺陷。与 P2-3 的产物相比，`medium` 差异主张从 42 条降到 33 条：
减少的 9 条中 6 条是假缺失（内容在别的章节，或提示丢了冒号没被识别），3 条是谱系差异被主题误判
抬高了置信度；`high` 不变。错配拆开后，原先被掩盖的行各自报为 `low` 缺失，`low` 主张从 58 条
增至 83 条。

| 缺陷 | 现象 | 修正 | 影响 |
| --- | --- | --- | --- |
| 丢了冒号的等级词 | JE-1000H nl/pl/pt 的"节能模式开机后恢复之前状态"提示渲染为 `OPMERKING De …` 这类段落，不算警示，被报为三语缺失 | 段落开头的等级词全为大写时，没有冒号也视为标签（`carriers.py`）；全量只命中这 3 段 | 警示条目 +3；该簇变为九语完整，记 `presentation` |
| 主题只在条目里搜 | 生命周期段落（"储能产品在生命周期内会有一定的容量衰减"）在 nl/pl/pt 位于用户维护章节，是普通段落而非条目，搜不到，被报为缺失 | 共有主题不少于两个时，也在缺失版本里不承载条目的段落和列表中搜索（`topic_document`）；只接受主题包含全部共有主题、且最多多出一个主题的块，泛泛的长段落不算命中 | 5 条 `medium` → `low`（JE-1000H、JE-3000C、JE-2000E、JE-2000F、JE-100C），`hits` 指向实际位置 |
| 合规行按位置配对 | 合规章节里位置相邻、内容无关的行被配成一簇：网址配"下载 App"说明，`www.hello-tech.com` 配电池 WEEE 声明；JBP-2000B nl/pl/pt/uk 的两条 WEEE 声明顺序互换，被交叉配对且不报任何差异 | 规范化文本相同的配对基础分为 70；文本不同时，合规条目基础分为 0（警示、安全仍为 10），只能靠共同数字和主题配对 | P2-3 中 22 条含错配成员的关系不再出现；JE-2000E、JE-2000F、JE-3000C 的电池 WEEE 声明恢复为九语完整；JBP-2000B 的互换记为 `order` |
| 德语 *Laden … herunter* | nl/pl/pt 中的德语下载说明 "Laden Sie sich die Jackery Mobiltelefon-App herunter" 被归入 `charging`，多出的主题证据把它的缺失抬到 `medium` | `charging` 词干排除同一句中 60 个字符内跟着 *herunter* 的 *laden*（`topics.py`） | 3 条 `medium` → `low` |

每处修正都有对应用例（`tests/test_knowledge_extraction.py`、`tests/test_knowledge_relations.py`）。

### 3.2 交内容负责人的问题清单

以下均已对照网页原文确认。档位取自观察产物；"人工"表示机器没有报出、核对时发现。
位置给英文版（或持有该内容的版本）的 `source_ref`，缺失的版本写在"版本"列。

| # | 版本 | 问题 | 位置 | 档 |
| ---: | --- | --- | --- | --- |
| 1 | JE-2000E、JE-2000F / de、es、fr、it、uk | 没有 EU 法规章节：无 RED 符合性声明、无线电频段与功率、制造商联系方式；与英文版同为印刷修订号 2.10 / 2.6 | `JE-2000E/EU/en/md/manual_je2000e_eu_en.html#eu-regulations`、`JE-2000F/EU/en/md/manual_je2000f_eu_en.html#eu-regulations` | high |
| 2 | JE-1000H、JE-3000C / de、es、fr、it、uk | 同第 1 条（修订号不同，最高 `medium`） | `JE-1000H/EU/en/md/manual_je1000h_eu_en.html#eu-regulations`、`JE-3000C/EU/en/md/manual_je3000c_eu_en.html#eu-regulations` | medium |
| 3 | JE-2000E / nl、pl、pt | 没有无线电频段与功率；RED 声明比英文版少两项 RoHS 法规（2011/65/EU、(EU) 2015/863） | `JE-2000E/EU/en/md/manual_je2000e_eu_en.html#eu-regulations` | medium（所在关系因第 1 条为 high） |
| 4 | JE-1000F / en、de、es、fr、it | 没有 EU 符合性声明与制造商信息（nl/pl/pt/uk 有） | `JE-1000F/EU/nl/md/manual_je1000f_eu_nl.html#eu-declaration-and-manufacturer` | medium |
| 5 | JS-100I / en | 没有 CE 符合性声明（其余八语在保修章节中有） | `JS-100I/EU/de/md/manual_js100i_eu_de.html#garantie` | medium |
| 6 | JA-AD600A / de、it、pt | 没有 FCC 声明（en、es、fr、nl、pl、uk 有）；EU 版是否需要 FCC 声明由合规负责人判断 | `JA-AD600A/EU/en/md/manual_jaad600a_eu_en.html#product-installation` | medium |
| 7 | JE-1000H、JE-3000C、JE-2000E / nl、pl、pt | UPS 章节缺少"不得用于数据服务器、医疗设备等故障可能危及生命或造成重大财产损失的场合"的 WARNING | `JE-3000C/EU/en/md/manual_je3000c_eu_en.html#uninterruptible-power-supply-ups` | medium |
| 8 | JE-1000H、JE-3000C / nl、pl、pt | 0 ms 的 CAUTION 少了第四条"UPS 功能只在单台直接接墙插时有效，不得多台串联（级联）"，全文也没有 | 同上 | 人工 |
| 9 | JE-3000C / nl、pl、pt | 缺少节能模式的 WARNING："负载功率持续偏低时自动关闭 AC 输出，冰箱、路由器、监控摄像头等需持续供电的设备应关闭节能模式"；三语只有"12 小时无充放电自动关机"的说明 | `JE-3000C/EU/en/md/manual_je3000c_eu_en.html#operations` | medium |
| 10 | JBP-2000B / uk | 引言缺少兼容性 NOTE（本电池包兼容 E1000 Plus V2 与 E2000 Plus V2） | `JBP-2000B/EU/en/md/manual_jbp2000b_eu.html#`（引言，无锚点） | medium |
| 11 | JBP-2000B / it | 连接章节的 NOTES 写"不得堆叠超过三个"；英文版为"默认最多堆叠 3 个，4 个及以上须靠墙放置并采取防倾倒措施" | `JBP-2000B/EU/en/md/manual_jbp2000b_eu.html#connections` | medium |
| 12 | JA-AD600A / it | 兼容表中 Explorer 2000 v2 的充电时间写作约 3.7 小时（英文版 5.6），Explorer 3000 Pro 的电流写作 8 A（英文版 12 A） | `JA-AD600A/EU/en/md/manual_jaad600a_eu_en.html#important-safety-instructions` | medium |
| 13 | JE-1000H / nl、pl | 警示标签拆词 `WAARSCHU` / `OSTRZE`（P1-4 §3.2，仍未修） | `JE-1000H/EU/nl/md/manual_je1000h_eu_nl.html#belangrijke-veiligheidsinformatie` | medium |
| 14 | JE-2000E / nl | Wi-Fi 提示的标签为 `OK-knop. OPMERKING`，正文截断（P1-4 §3.2，仍未修） | `JE-2000E/EU/nl/md/manual_je2000e_eu_nl.html#app-instellen` | medium |
| 15 | JBP-2000B / fr、JBP-3600A / fr、JE-3600A / es | 英文版的 CAUTION 在这里写作 `IMPORTANT` / `Important` / `Importante`。2026-10-11 补记：D13 裁定这三个是 note 级等级词（与渲染器一致），等级比英文版低一级，应改为该语言的 CAUTION 等级词 | `JBP-2000B/EU/fr/md/manual_jbp2000b_eu_fr.html#connexions`、`JBP-3600A/EU/fr/md/manual_jbp3600a_eu_fr.html#connexions`、`JE-3600A/EU/es/md/manual_je3600a_eu_es.html#cargando` | medium |
| 16 | JE-3600A / de | App 设置章节的三条 NOTE 写作 `TIPP` | `JE-3600A/EU/de/md/manual_je3600a_eu_de.html#app-einstellung` | medium |
| 17 | JE-100C / de、es、fr、it | 充电温度提示为 NOTE（`HINWEIS` / `NOTA` / `REMARQUE`），en、nl、pl、pt、uk 为 CAUTION | `JE-100C/EU/en/md/manual_je100c_eu_en.html#charging` | medium |
| 18 | JE-1000H、JE-3600A / de | 禁止明火图标的说明写作 "Vermeiden Sie Hitze."（避免受热），其他语言为"远离火源" | `JE-1000H/EU/de/md/manual_je1000h_eu_de.html#bedeutung-der-symbole`、`JE-3600A/EU/de/md/manual_je3600a_eu_de.html#bedeutung-der-symbole` | low |
| 19 | JBP-3600A / de | 符号表把"勿拆解""避免受热"的说明配到了别的图标上（P2-3 已核） | `JBP-3600A/EU/de/md/manual_jbp3600a_eu_de.html#bedeutung-der-symbole` | low |
| 20 | JE-1000H / nl | "DC 12 V 口只兼容 12 V 车载电池、不适用于 24 V 系统"一条在 OPGELET 框外，框内只有其余两条（呈现差异，供参考） | `JE-1000H/EU/nl/md/manual_je1000h_eu_nl.html#handelingen` | medium |
| 21 | JE-3600A / fr | 安全章节缺少引导句 "Always follow these basic precautions when using this product." | `JE-3600A/EU/en/md/manual_je3600a_eu_en.html#important-safety-information` | 人工 |
| 22 | JE-3600A / fr | 充电章节有英文句 "*The car charging cable is sold separately."（计划附录 B 第 3 条） | `JE-3600A/EU/fr/md/manual_je3600a_eu_fr.html#charge` | 人工 |
| 23 | JE-1000H、JE-2000E、JE-2000F、JE-3000C / nl、pl、pt | "EU declaration and manufacturer" 章节开头有六种语言（en、fr、es、de、it、uk）的"下载 Jackery App"说明，单语版本中混入其他语言，是否保留由内容负责人判断 | `JE-3000C/EU/nl/md/manual_je3000c_eu_nl.html#eu-declaration-and-manufacturer` | low |

第 23 条更正 P2-3 PR 中"nl/pl/pt 混入乌克兰语"的说法：乌克兰语只是这组六语说明中的一条。

### 3.3 误报与可解释差异的原因

`medium` 唯一的误报在试点外：JE-100C 的 fr、nl 把英文版两段电池安全说明合成一段，配对落在后一段，
前一段被报为缺失（P2-3 已记录的误报模式）。`medium` 的 3 条可解释差异：JE-1000H nl 的 24 V 一条
在框外（§3.2 第 20 条）；JE-1000F 的 nl/pl/pt/uk 与 JE-2000F 的 nl/pl 首个警示框只有 ⚠ 图标
标签（P1-4 §3.1，等级未知）。

试点的 37 条 `low`：

| 判定 | 条数 | 原因 |
| --- | ---: | --- |
| 真实差异 | 7 | 制造商地址、邮箱在 JE-1000H、JE-3000C 的 de/es/fr/it/uk 缺失（§3.2 第 2 条；地址里的数字太短、在别处也搜到，邮箱没有数字，所以只给 `low`）；德语符号说明（§3.2 第 18 条，4 条关系） |
| 部分属实 | 9 | JE-1000H、JE-3000C 英文版单列的"声明全文见"及网址、公司名、邮箱、网站：de/es/fr/it/uk 确实没有；nl/pl/pt 有，但并在相邻段落或标题里（如 `+86 400 668 9293 www.hello-tech.com`）。这几行没有数字，只能按对齐判断 |
| 可解释差异 | 18 | nl/pl/pt 的六语下载说明与 `EU Regulations` 一行（13 条，谱系不同）；生命周期段落在 nl/pl/pt 位于维护章节（2 条，`hits` 指向实际位置）；JE-3000C 的"节能模式恢复之前状态"在英文等六语中写在图片 alt 里（1 条）；JS-100I 英文版的两条提示是普通段落（2 条，数字在全文中搜到） |
| 误报 | 3 | JBP-2000B nl/pl/pt/uk 把电话、邮箱、网站写在同一段，邮箱、网站两行被报为缺失（2 条）；JE-3600A fr 的错配（§2）把英文版第一条报为缺失，实际缺的是引导句（1 条，见 §3.2 第 21 条） |

`low` 的证据本来就弱（没有数字锚点，或数字在别处也出现），按设计不交付；它们的用处是给维护者
指出规则的盲区。

### 3.4 已知边界

- **召回**：只比较条目之间的对应，条目内部少了一句、又没有数字可比时发现不了。§3.2 第 8 条
  就是这样：四条变三条，前三条仍能配上，关系判为完整。要发现它需要句子级对齐，留给后续阶段。
- **`high` 很少**：`high` 要求印刷修订号相同，10-11 只有 8 条。正式修订号由发布元数据补充
  之前（D11），可交付的候选主要是 `medium`。
- **新鲜度粒度**：`product_specific` 把同语言的其他型号都列入 `absent_in`，任一版本重新发布都会
  让同语言的这类关系全部 stale（模拟中 35 条）。这是计划 §6.2 规则的直接结果，不会漏判，代价是重算。
- **新鲜度不反映规则变化**：以 P2-3 的产物作 `--previous`，3,333 条条目与 1,393 条关系全部
  fresh，但其中 22 条关系在新规则下已不再产生（§3.1）。新鲜度只看源内容；规则变了要看
  `generator_version`，不同版本的关系不应混用。
- **锚点为空**：首个标题之前的引言没有章节锚点，8 条条目的 `source_ref` 指向网页开头。
- **图片盲区**：361 张图片没有 alt。JE-3000C 的节能提示在六种语言里只写在图片 alt 中，没有 alt
  的图片里的提示完全不可见。
- **线上复核**：全部检查基于 10-11 本地重建，线上复核待补（与 P2-1～P2-3 相同）。

## 4. 结论

Phase 2a 验收标准全部满足。D14 门槛以 `high` 8/8 通过；`medium` 全量 33 条中 32 条确认，误报
原因清楚。建议交内容负责人的候选取 `high` 与 `medium`，`low` 只供维护者参考。§3.2 的问题清单
交内容负责人，在各版本声明的权威源修改后重新发布；D13 的等级词已于 2026-10-11 裁定（补记，见 §3.2 第 15 条）。
Phase 2b（跨区域比较）与 Phase 3（审核与回流）需另行立项。

## 5. 复现

auto-manual 与 Hello-Docs 为同级检出时，在 auto-manual 根目录运行：

```bash
PYTHONPATH="$PWD" python -m sphinx -q -b html \
  -D extensions=myst_parser,tools.rtd.portal \
  -D rtd_knowledge_dir=../Hello-Docs/docs/knowledge \
  ../Hello-Docs/docs/publish/web .tmp/machine-phase2/site
python -m tools.manual_knowledge.observe --site .tmp/machine-phase2/site --output .tmp/machine-phase2/a.json
python -m tools.manual_knowledge.observe --site .tmp/machine-phase2/site --output .tmp/machine-phase2/b.json
cmp .tmp/machine-phase2/a.json .tmp/machine-phase2/b.json
node integrations/openclaw/auto-manual-control-layer/test/verify-published-corpus.mjs "$PWD/.tmp/machine-phase2/site"
```

逐条核对用临时脚本按 `source_ref` 把关系成员与网页原文并排列出；身份、证据与如实检查用
BeautifulSoup 收集网页锚点后对照产物；新鲜度在修改过的语料副本上调用 `observe.build_items` 与
`judge_previous` 重算。脚本不入库（与 P1-4 相同）。
