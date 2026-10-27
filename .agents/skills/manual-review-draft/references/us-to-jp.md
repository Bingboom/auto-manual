# US→JP：保留既有日文复用流程

共同的结构继承、参数证据和审核意见规则见上级 SKILL.md；日文模式保留以下专属工具、术语、统计和已确认显示约定，不套用英文稿的计数方式。

## 语料、翻译与规格

1. 读取 [corpus-and-color-rules.md](corpus-and-color-rules.md)：依次查 JP RST 模板、Translation_Memory 术语与句对、已发布／实时规格和 LCD 措辞、同类 JP Web 手册。实时表读取先遵守相应 Bitable skill，不用来源值替代目标规格。
2. 优先复用整句；只有名称、参数或端口槽位变化时仍是语料复用。半句可复用则拆分单元，只补译缺失片段。不能仅查一个来源就断言没有日文。
3. 必要而无语料的部分，给出绿色首轮日文，保留 `data-needs-translation`、`data-previous-english`；邻近语料、未匹配原因分别记入 `data-reference-jp`、`data-unmatched-reason`。纯规格字段不计翻译量。
4. 先查 `data/terminology_rules.csv`；现行术语优先于旧稿中的退役表达。标签、LCD 点灯時／点滅時／消灯時、全角片假名和商品名引用按语料指引与本任务决定处理。
5. 规格表标签和措辞复用已发布 JP 组件，数值只取目标 JP 规格或明确研发答复，紫色标明出处及日期。US 数值保留审核意见，不带入日文正文；整机、并联或级联系统的额定值分开。
6. 只有有依据且适用的日本专属内容才新增；历史案例中的安装、电工或配件措辞不是所有型号的默认承诺。补充章节按操作者要求和目标差异落实，并保留来源。

## 颜色与显示兼容

| 含义 | 既有标记 |
| --- | --- |
| 既有日文，黑色 | `.jp-original` + `data-jp-original-source` |
| 必要的新翻译，绿色且计数 | `.en-new` + `data-needs-translation`，英文保存在 `data-previous-english` |
| 小型新增／JP 专属新增，绿色但不计翻译量 | `.en-new.jp-draft-insert`，保留新增原因 |
| 目标规格／研发值，紫色 | `.jp-spec-updated` / `.jp-spec-filled`，附来源 |
| 目标缺数据时的一代补写，绿色但不计翻译量 | `.en-new` + `title="一代数据"`，用一代日文措辞 |
| 既有稿的待确认占位，玫红色（下次修订时改为一代补写） | `.us-difference.jp-parameter` |
| 商品名引用，琥珀色 | `.jp-name-ref` |
| 中文对照／审核意见 | `.zh-translation` / `.jp-review` |

新稿和下次修订的日文稿按 SKILL.md 的一代补写和 3+2 质保默认处理：一代补写沿用一代日文措辞，绿色、不计翻译量，同 `.jp-draft-insert`。操作者已确认的既有日文稿在下次修订前保留原占位和色彩。来源、解释和建议仍归审核层；已知冲突不能隐藏成普通正文。共享样式按 [jp-style-mapping.md](jp-style-mapping.md) 和 `../assets/review-overlay.css`，不是另写一套近似版式。

## 专属统计和审查

- `../scripts/jp_corpus.py`：语料池、TM 查询；来源查询次序及参数见语料指引。
- `../scripts/count_translation.py --previous <last version dir>`：沿用上一版统计，输出 `new-translation-needed.xlsx/.csv`；审核附录同步单元、词数、字符数及章节／类型汇总。
- 请求内容对照或重要交付前读 [alignment-audit.md](alignment-audit.md)，使用 `extract_units.py` / `aggregate_align.py`。图内标签、短标题、框内文字也要纳入。对照工具的 JP 字段及状态约定不直接套到英文模式。
- `../scripts/fetch_jp_style.py`、`../scripts/rtd_figures.cjs`、`../scripts/render_check.cjs` 保持原用途；US 底图的适用性记录在审核层，按当前稿约定显示。
- [pitfalls.md](pitfalls.md) 记录 JP 已验证问题；[jhp3600c-case.md](jhp3600c-case.md) 索引历史转换示例，仅在对应问题出现时读。示例中的参数、型号和操作者决定不可直接运行或跨型号套用。

版本化、上传与私有发布统一执行上级 SKILL.md，既有工具不构成额外的写入或发布授权。
