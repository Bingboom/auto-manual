# Template Maintenance and Using Guide

更新时间: 2026-03-10

本文档说明当前说明书模板系统的维护方式和使用方式。目标是让后续切换机型时，优先通过 `Spec_Master.csv` 驱动模板，而不是反复硬改 `docs/templates/**/*.rst`。

---

## 1. 当前模板体系概览

当前整本说明书由两类内容组成:

1. `safety` 页
   - 来源: `data/phase1/content_blocks.csv`
   - 先由 `tools/phase1_build.py` 生成 `docs/generated/{model}/safety_{lang}.rst`
   - 再进入 Word / PDF 构建链路

2. `spec` 页
   - 来源: `data/phase1/Spec_Master.csv` 和 `data/phase1/Spec_Footnotes.csv`
   - 先由 `tools/phase1_build.py` 生成 `docs/generated/{model}/spec_{lang}.rst`
   - 再进入 Word / PDF 构建链路

3. 其余页面
   - 来源: `docs/templates/page_en/*.rst`
   - 来源: `docs/templates/page_eu/*.rst`
   - 来源: `docs/templates/page_jp/*.rst`
   - 这些页面是“模板页”，用于承载不同机型复用的正文结构

结论:

- `safety` 和 `spec` 不应手改生成后的 `docs/generated/**/*.rst`
- 普通正文页应修改 `docs/templates/page_*/*.rst`
- 能抽象成“机型变量”的内容，优先做成占位符并从 `Spec_Master.csv` 注入

---

## 2. 关键目录

### 2.1 模板目录

- `docs/templates/page_en`
- `docs/templates/page_eu`
- `docs/templates/page_jp`

### 2.2 数据目录

- `data/phase1/Spec_Master.csv`
- `data/phase1/Spec_Footnotes.csv`
- `data/phase1/content_blocks.csv`

### 2.3 构建与注入逻辑

- `tools/build_docs.py`
- `tools/utils/spec_master.py`
- `tools/word_bundle_common.py`
- `tools/word_bundle_html.py`
- `docs/conf_base.py`

### 2.4 配置文件

- `config.yaml`
- `config.eu.yaml`
- `config.ja.yaml`
- 其他按机型新增的配置，例如 `config.hte1531000a.yaml`

---

## 3. 当前页面归属规则

### 3.1 必须走 CSV 自动构建的页面

- `safety`
- `spec`

不要直接修改这些生成结果:

- `docs/generated/*/safety_*.rst`
- `docs/generated/*/spec_*.rst`

正确修改入口:

- 安全页改 `content_blocks.csv`
- 规格页改 `Spec_Master.csv` / `Spec_Footnotes.csv`

### 3.2 应该改模板 RST 的页面

典型页面:

- `00_preface.rst`
- `01_meaning_of_symbols.rst`
- `02_whats_in_the_box.rst`
- `03_product_overview_placeholder.rst`
- `04_lcd_display_placeholder.rst`
- `05_operation_guide_placeholder.rst`
- `06_ups_mode.rst`
- `07_expansion_battery_pack.rst`
- `08_charging_methods.rst`
- `09_storage_and_maintenance.rst`
- `10_troubleshooting.rst`
- `11_warranty.rst`
- `12_app_setup_placeholder.rst`

这些页面的“固定正文结构”保留在模板里。

如果里面出现机型名、型号、按钮名、电池包名等耦合信息，应优先改成占位符。

---

## 4. 占位符体系

### 4.1 基础占位符

当前公共注入的基础占位符包括:

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

说明:

- `PRODUCT_NAME` 取自 `Spec_Master.csv` 中 `Row_key=product_name`
- `MODEL_NO` 取自 `Spec_Master.csv` 中 `Row_key=model_no`
- `PRODUCT_SHORT_NAME` 默认由 `PRODUCT_NAME` 去掉前缀 `Jackery ` 自动得到

示例:

```rst
Congratulations on your new |PRODUCT_NAME|.

**型番：|MODEL_NO|**

In the event of a sudden loss of grid power, the |PRODUCT_SHORT_NAME| will automatically switch to stored power.
```

### 4.2 模板专用占位符

模板中还支持从 `Spec_Master.csv` 的 `tpl_*` 行读取自定义字段。

规则:

- CSV 里写 `Row_key=tpl_xxx`
- 注入后占位符名变成 `|XXX|`
- 如果该值存在，还会自动派生 `|XXX_BOLD|`
- 如果字段名以 `_label` 结尾，还会自动派生 `|XXX_LOWER|`

例如:

- `tpl_main_power_button_label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `tpl_main_power_button_label` -> `|MAIN_POWER_BUTTON_LABEL_LOWER|`
- `tpl_battery_pack_name` -> `|BATTERY_PACK_NAME|`
- `tpl_battery_pack_name` -> `|BATTERY_PACK_NAME_BOLD|`

### 4.3 当前已经在使用的模板变量

英文美规页:

- `MAIN_POWER_BUTTON_LABEL`
- `DC_USB_POWER_BUTTON_LABEL`
- `AC_POWER_BUTTON_LABEL`

欧规页:

- `POWER_BUTTON_LABEL`
- `USB_POWER_BUTTON_LABEL`
- `AC_POWER_BUTTON_LABEL`
- `BATTERY_PACK_NAME`

日文页:

- `PRODUCT_NAME`
- `MODEL_NO`

---

## 5. Spec_Master.csv 如何写模板变量

### 5.1 最小字段要求

模板变量行至少应保证这些列正确:

- `项目代码`
- `Region`
- `Is_Latest`
- `Page`
- `Section`
- `Section_order`
- `Row_key`
- `Row_label_en`
- `Line_order`
- `Value_en`
- `Model`

建议:

- `Page` 统一写 `specifications`
- `Section` 可写 `TEMPLATE VARS`
- `Section_order` 可统一放到较后位置，如 `99`

### 5.2 示例

```csv
项目代码,Region,Is_Latest,Page,Section,Section_order,Row_key,Row_label_en,Line_order,Param_en,Value_en,Model
HTE154-US,US,TRUE,specifications,TEMPLATE VARS,99,tpl_main_power_button_label,Main POWER Button,1,,Main POWER Button,JE-2000F
HTE154-US,US,TRUE,specifications,TEMPLATE VARS,99,tpl_dc_usb_power_button_label,DC/USB Power Button,1,,DC/USB Power Button,JE-2000F
HTE154-US,US,TRUE,specifications,TEMPLATE VARS,99,tpl_ac_power_button_label,AC Power Button,1,,AC Power Button,JE-2000F
```

欧规电池包名示例:

```csv
项目代码,Region,Is_Latest,Page,Section,Section_order,Row_key,Row_label_en,Line_order,Param_en,Value_en,Model
HTE132500A-EU-JAK,EU,TRUE,specifications,TEMPLATE VARS,99,tpl_battery_pack_name,Battery Pack Name,1,,Jackery Battery Pack 3600,JE-3600A
```

---

## 6. 新机型接入流程

### 6.1 只换参数，不换正文结构

适用场景:

- 说明书结构和现有模板基本一致
- 只需要替换产品名、型号、按钮名、部分称呼

步骤:

1. 在 `Spec_Master.csv` 中补该机型的 `product_name`
2. 在 `Spec_Master.csv` 中补该机型的 `model_no`
3. 如模板内按钮命名不同，补对应 `tpl_*`
4. 如欧规扩容包名称不同，补 `tpl_battery_pack_name`
5. 新建对应配置文件，或复用已有配置文件并改 `default_model/default_region`
6. 执行构建命令验证

### 6.2 既换参数，也换正文内容

适用场景:

- 附件说明书和现有模板差异较大
- 需要按附件复刻大段正文

步骤:

1. 先确定走哪一套模板目录
   - `page_en`
   - `page_eu`
   - `page_jp`
2. 逐页对照附件，修改对应 `*.rst`
3. 将机型绑定文案优先改成占位符
4. 不改图片路径时，可继续使用占位图
5. 补齐 `Spec_Master.csv` 的模板变量
6. 重新构建并核对 Word

---

## 7. 实际构建命令

### 7.1 英文默认模板

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config config.yaml --no-open
```

### 7.2 欧规模板

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config config.eu.yaml --no-open
```

### 7.3 日文模板

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config config.ja.yaml --no-open
```

### 7.4 指定单独机型配置

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config config.hte1531000a.yaml --no-open
```

---

## 8. 当前配置与模板的对应关系

### 8.1 `config.yaml`

- 语言: `en`
- 模板目录: `docs/templates/page_en`
- `safety/spec` 走 CSV 自动页

### 8.2 `config.eu.yaml`

- 语言: `en`
- 模板目录: `docs/templates/page_eu`
- `safety/spec` 走 CSV 自动页

### 8.3 `config.ja.yaml`

- 语言: `ja`
- 模板目录: `docs/templates/page_jp`
- `safety/spec` 走 CSV 自动页

注意:

- `config.ja.yaml` 现在已经指向 `page_jp`
- 不应再继续使用已删除的 `page_ja`

---

## 9. 常见维护原则

### 9.1 什么时候改模板

改模板的情况:

- 文字内容来自 Word 附件正文
- 页面结构、段落、标题、列表、表格需要复刻
- 该段文字不是“机型参数”，而是“说明书话术”

### 9.2 什么时候改 CSV

改 CSV 的情况:

- 产品名称变了
- 型号变了
- 按钮名称变了
- 电池包名称变了
- 规格参数变了
- `safety/spec` 页内容变了

### 9.3 不要做的事情

- 不要直接改 `docs/generated/**/*.rst`
- 不要把整机型名称硬编码回模板，除非它就是永久固定文案
- 不要把 `safety/spec` 手动塞回模板页

---

## 10. 常见坑

### 10.1 RST 替换引用两侧黏连

在日文里，`|PRODUCT_NAME|の` 这种写法容易被 docutils 误判。

建议写法:

```rst
|PRODUCT_NAME| のDC入力電圧範囲
```

不要写:

```rst
|PRODUCT_NAME|のDC入力電圧範囲
```

### 10.2 表格项缩进被破坏

在 `list-table` 中替换文字时，必须保持原有缩进，否则会触发 docutils 警告。

重点检查:

- `* -`
- `  -`
- 多行单元格内容

### 10.3 把生成页和模板页混改

如果同时改了:

- `docs/templates/page_*/...`
- `docs/generated/...`

最终很容易出现“构建后一覆盖，改动丢失”的假象。

原则:

- 只改上游源文件

### 10.4 忘记补 `Spec_Master.csv`

如果模板里已经用了占位符，但对应机型没有补 `product_name/model_no/tpl_*`，构建时会退回默认值，或者最终文案不对。

---

## 11. 回归检查清单

每次修改模板或模板变量后，至少做以下检查:

1. 运行目标配置的 `build_docs.py`
2. 确认 `docx` 文件成功生成
3. 搜索生成 Word 中是否还残留占位符:
   - `|PRODUCT_NAME|`
   - `|MODEL_NO|`
   - `|...|`
4. 确认旧机型硬编码是否已经消失:
   - 如 `Explorer 2000`
   - 如 `Explorer 3600 Plus`
   - 如 `JE-2000F`
5. 检查 `safety` 和 `spec` 页是否仍来自自动生成
6. 检查 Sphinx 是否出现新的 docutils 语法警告

---

## 12. 推荐维护顺序

建议每次按这个顺序工作:

1. 先定模板目录
2. 再抽取正文到 `page_*/*.rst`
3. 再把机型耦合文案抽成占位符
4. 再补 `Spec_Master.csv`
5. 再构建 Word 验证
6. 最后再做文字细调和版面微调

这样成本最低，也最不容易把模板越改越散。

---

## 13. 后续扩展建议

如果后续还有新的固定差异需要抽象，建议继续沿用 `tpl_*` 机制，例如:

- `tpl_customer_support_email`
- `tpl_app_name`
- `tpl_solar_adapter_name`
- `tpl_dc_input_port_label`
- `tpl_battery_pack_max_count`

原则:

- 先确认这个差异是否跨机型重复出现
- 如果会重复出现，就抽成 `tpl_*`
- 如果只存在于单一本说明书，优先留在模板正文

---

## 14. 一句话原则

模板负责“结构和话术”，CSV 负责“机型和参数”，生成文件只作为结果，不作为维护入口。
