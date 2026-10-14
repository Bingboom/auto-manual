# 快速开始：2026-04 更新与目标本地验收示例（§10）

属于[快速开始指南](../quick_start_guide.md)，其索引列出全部分页。章节编号与原文一致。
示例或流程变化时更新本页，不要把新内容追加到总文件。

## 10. 2026-04 更新

- `Review Init` 和 `Document_link` 都按“`Document_Key` 精确目标 + `Build_family` 语言范围”解析配置，再决定是否按 `Document_Key` 合并；像 `us-merged` 这样的合并语言范围会把空 `Lang` 的同一 `Document_Key` 合成一次 review / build，而 `Build Draft Package` 行只要填写了 `Lang`，就会按 `Document_Key + 规范化 Lang` 拆成独立构建。
- `Lang=br` / `pt-br` 会规范化为 `pt-BR`；`configs/config.pt-br.yaml` 现在按单语言入口构建巴西葡语文档，队列表用 `Build_family = pt-br` 加 `Lang=br` 或 `Lang=pt-BR`，不要再额外配一条英文对照稿。
- US 的 `configs/config.us.yaml` 现在是合并多语言入口，会产出一个合并 `en + fr + es` 的 Word：`docs/_build/<model>/US/word/manual_<model>_us.docx`。
- 队列表的 `Build_family` 只填写语言范围：`us-merged` / `us-en` / `us-es` / `us-fr` / `pt-br` / `jp-ja` / `cn-zh`；不要填写 BP/MAIN 等产品骨架值。`Lang` 只保留为兼容或单语言收窄字段。
- 合并 US 流程请填 `Build_family = us-merged`，`Lang` 可以留空；单语言流程请填对应单语言 family，例如 `us-en`、`us-es`、`us-fr` 或 `pt-br`，`Lang` 只填一个语言值即可。
- JBP 与普通 US 主机在 Base 中都使用 `Build_family = us-merged`；系统根据 `Document_Key` 的精确目标自动选择 BP 或 MAIN 骨架配置。
- 这条合并 US 流程不再要求法语、西语分别先创一份独立初稿 review bundle。
- `Spec_Master` 里由 `Source_lang` 定义 source language；`*_source` 内容必须有，其他语言列在 CSV 驱动内容里可以为空，系统会自动回退到 source language 文本。
- `Spec_Master` 现在是本地读取快照；人工维护规格参数时先改 `规格参数明细` / `页面占位参数`，再用 `sync-data --table spec_master` 或 `spec-master-rebuild` 生成。


### 合并配置的 Web 单语本地验收

要从合并 US 配置只验收英语 Web 输入，可显式传入 `--lang en`。
先准备含已核验附件和 Web composite 合同的本地快照，将下方示例路径替换为它；
纯仓库 fixture 不包含所有审稿附件，不能单独作为这项审稿构建的完整输入：

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python3 build.py check \
  --config configs/config.us.yaml \
  --model JE-1000F --region US --lang en \
  --source review-asis \
  --data-root /path/to/approved-local-snapshot \
  --staging-root .tmp/web-en
```

完整 EN/FR/ES 源会冻结到
`.tmp/web-en/docs/_build/JE-1000F/US/en/web/source/rst/`，英语规范投影位于
`.tmp/web-en/docs/_build/JE-1000F/US/en/rst/`。用相同参数运行 `build.py md` 或
`build.py html` 时，两者读取同一规范投影。该命令只做本地验收，不构成独立语言发布。
命令退出码为 0 只表示现有构建与结构门通过，不等于内容已验收；本路径不放宽任何内容门。

### 加电包日语 Web 本地验收

在工程仓库使用现有快照试构建（不写线上 Base、不发布）：

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.bp-jp.yaml --model JBP-2000B --region JP --source runtime --data-root tests/fixtures/phase2 --staging-root .tmp/bp-web --no-clean --skip-root-index
python -m tools.readthedocs_source --build-root .tmp/bp-web/docs/_build --output-dir .tmp/bp-web/docs/_build/rtd
python -m sphinx -b html .tmp/bp-web/docs/_build/rtd .tmp/bp-web/html
```

Web 图采用 PDF 带字裁切，正确操作说明以结构源为准。
IR、源读取退出路径与剩余边界见[完整执行记录](../../code-as-doc/dev/ir_document_closeout.md)。

### SolarSaga 100 Air 欧规英语 Web 本地验收

该目标从 Safety Tips 开始，不包含封面、目录或电源产品专属章节。使用提交的
bootstrap fixture 进行只读本地验收：

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.solar-eu-en.yaml \
  --model JS-100I --region EU --lang en \
  --data-root tests/fixtures/js100i_eu_en_phase2 \
  --staging-root .tmp/js100i-web
python -m tools.readthedocs_source \
  --build-root .tmp/js100i-web/docs/_build \
  --output-dir .tmp/js100i-web/docs/_build/rtd \
  --title "JS-100I Web Acceptance"
python -m sphinx -b html \
  .tmp/js100i-web/docs/_build/rtd .tmp/js100i-web/html
```

这只是本地 Web 验收。正式发布仍由 `Workflow_action=Web Publish` 冻结审核通过的
线上快照并创建 Hello-Docs `docs/publish/**` PR；不要把 fixture 当成线上源表，也
不要直接修改业务镜像工程树。

### SolarSaga 100 Air 欧规新增语言候选

八语候选 `fr/es/de/it/uk/pt/nl/pl` 共用一个配置，但每次使用匹配语言的结构源：

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.solar-eu-multilingual.yaml \
  --model JS-100I --region EU --lang fr \
  --data-root data/manual_sources/JS-100I/EU/added-locales/2026-09-28/phase2/fr \
  --staging-root .tmp/js100i-locales
```

将两处 `fr` 一起替换为目标语言；`Source_lang` 不负责在混合 CSV 中筛选行。
随后按上方示例用 `readthedocs_source.py` 和 Sphinx 组装预览，将目录改成
`.tmp/js100i-locales`。英语正式 Git 源使用
`data/manual_sources/JS-100I/EU/en/2.0/phase2` 和原英语配置。
本轮保留原稿技术事实与制造商名称，勘误和待确认项见
[九语候选验收记录](../../code-as-doc/reviews/js100i_eu_nine_language_2026-09.md)。

### SolarSaga 40 Air 欧规英语 Web 本地验收

JS-40C 使用同一 Solar 配置入口，但由独立 Product Manual Plan 解析七项 Inbox、
充电连接、角度/设备、收纳、规格和保修。只读本地构建命令如下：

```bash
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py html \
  --config configs/config.solar-eu-en.yaml \
  --model JS-40C --region EU --lang en \
  --data-root data/manual_sources/JS-40C/EU/en/2026-08-30/phase2
```

该命令只生成本地验收页面，不写线上 Base、不上传 OSS，也不构成正式发布。

JBP-2000B 欧规英文单语的可执行示例见
[版本化结构源](../../manual_sources/JBP-2000B/EU/en/2.0/README.md)。


JE-100C/EU 九语 Web 的本地示例见[构建指南](../../code-as-doc/build_doc_guide/web-target-notes.md#je-100ceu-nine-language-web-source)：
`--config configs/config.eu-fr.yaml --model JE-100C --region EU --lang fr`，
并显式指定 `--data-root manual_sources/JE-100C/EU/en/2.0/phase2`。
其余可用语言为 `en/es/de/it/uk/pt/nl/pl`，配置文件后缀与 `--lang` 同步替换。
这些产物是本地候选，未修改线上构建表或发布链接。

For English/native Web intake, start with the [source-copy work packet and shared-art review](../../code-as-doc/dev/manual_intake_assistance.md) before assembling a candidate.

### FridgeGuard Git-only 示例

JE-1000E-SIL / US / en 的完整构建示例与源文件哈希见
[录入记录](../../code-as-doc/reviews/je1000e_sil_us_en_web_intake.md)。
必须使用记录中的冻结数据根目录；不要用其他型号的 phase2 快照代替。

### FridgeGuard US native FR/ES local candidate

French and Spanish use `configs/config.us-fr.yaml` / `configs/config.us-es.yaml`, target `JE-1000E-SIL`, region `US`. Their Git-only data roots are `data/manual_sources/JE-1000E-SIL/US/<lang>/git-20261002-537939d0/phase2`; edit the corresponding `docs/templates/page_fridgeguard/<lang>/` source. Build with `build.py md --lang <lang> --data-root <data-root> --staging-root <isolated-output> --skip-root-index`. Native source discrepancies and asset reuse are recorded in [the intake review](../../code-as-doc/reviews/je1000e_sil_us_fr_es_web_intake.md). Publication resumed under the operator’s 2026-10-03 “推上去 发布” authorization; release acceptance is tracked in the intake review.


### SlimPower H1 日规日文 Git-only 回放

使用[批准的冻结源](../../manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-reviewed/README.md)；先核对其 `approval.json` 与 MA-274。
输出目录必须新建，旧候选和历史验证记录保留。

```sh
PKG=manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-reviewed
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "$PKG/rebuild.py" --output /tmp/h1-reviewed-new
python3 -m sphinx -W --keep-going -b html /tmp/h1-reviewed-new /tmp/h1-reviewed-html-new
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "$PKG/verify.py" --html /tmp/h1-reviewed-html-new/manual.html
```

本地回放不等于上线；继续使用现有 Git-only 发布出口，无线上表或队列操作。
