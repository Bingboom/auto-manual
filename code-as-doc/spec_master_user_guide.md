# Spec Master User Guide

更新时间：2026-03-08

本文说明 `Spec_Master.csv` 在当前仓库构建链路中的作用，并明确“构建 Word/PDF/HTML 时必备字段”。

## 1. `Spec_Master.csv` 在构建链路中的作用

当前 `spec` 页面数据源是单一配置源：

- 主表：`config.yaml -> paths.spec_master_csv`
- 脚注补充（可选）：`config.yaml -> paths.spec_footnotes_csv`

当前仓库默认配置：

```yaml
paths:
  spec_master_csv: data/phase1/Spec_Master.csv
  spec_footnotes_csv: data/phase1/Spec_Footnotes.csv
```

构建链路（统一内容源）：

1. `tools/build_docs.py` 解析构建目标（`model/region/lang`）
2. 按 `Model + Region + Language` 从 `Spec_Master.csv` 解析 `Row_key=product_name` 对应值
3. 注入 `|PRODUCT_NAME|` / `|PRODUCT_NAME_BOLD|`，供 RST 模板和 Word bundle 使用
4. `tools/phase1_build.py` 读取同一份 `Spec_Master.csv` 生成 `docs/generated/<model>/spec_<lang>.rst`
5. `html/pdf/word` 都基于同一份 `generated rst + templates rst` 继续构建

结论：`spec` 页面内容与产品名变量都来自同一个 `Spec_Master.csv`。

## 2. 构建必备字段

### 2.1 `spec` 页面可构建的硬必备表头

`Spec_Master.csv` 必须包含：

- `Section`
- `Row_key`
- `Line_order`

缺失时会被判定为非 Spec_Master schema，`spec` 页无法按当前主链路正常构建。

### 2.2 产品名变量注入的硬必备字段

当你使用 `build_docs.py --model ...`（或配置了 `build.default_model`）时，以下字段是硬必备：

- `Row_key`：必须存在 `product_name` 行
- `Value_<lang>`（例如 `Value_en`）或可回退的 `Value` / `Spec_Value`
- `Model`（建议显式填写，按型号精确匹配）
- `Region`（建议显式填写，按区域精确匹配）

`build_docs.py` 在有目标 `model` 的情况下会 fail-fast：如果无法从 `Spec_Master.csv` 解析到 `product_name`，构建直接失败。

### 2.3 推荐字段（提升可控性）

- `Section_order`：章节排序
- `Row_order` / `row_order`：行排序
- `Row_label_<lang>`：左侧字段显示名
- `Param_<lang>` + `Value_<lang>`：右侧内容拼装
- `Page`：建议标注为 `spec` 或 `specifications`
- `Is_Latest`、`enabled`：版本与启用控制

## 3. 过滤规则（常见“行被吃掉”原因）

以下字段不是必填，但填写不当会导致内容被过滤：

- `enabled`：仅保留 truthy 行
- `Is_Latest`：仅保留 truthy 行
- `Model`：若传入构建 model，会做精确匹配
- `Region`：若传入构建 region，会做精确匹配
- `Page`：若存在，必须是 `spec` / `specifications`

## 4. 最小可用示例

```csv
Section,Section_order,Page,Model,Region,Row_key,Row_label_en,Line_order,Value_en,Is_Latest,enabled
GENERAL INFO,1,spec,JHP-2000A,US,product_name,Product Name,1,Jackery HomePower 2000 Plus v2,1,1
GENERAL INFO,1,spec,JHP-2000A,US,model_no,Model No.,1,JHP-2000A,1,1
```

这份示例可同时满足：

- `spec` 页面基础渲染
- `PRODUCT_NAME` 变量注入
- `build_docs.py --model JHP-2000A --region US` 的 fail-fast 校验

## 5. 快速自检

```bash
python3 tools/phase1_build.py --model JHP-2000A --region US --page spec --lang en --spec-master-csv data/phase1/Spec_Master.csv --spec-footnotes-csv data/phase1/Spec_Footnotes.csv
python3 tools/build_docs.py --model JHP-2000A --region US --clean --no-open
```

如果失败，优先检查：

1. `Spec_Master.csv` 是否包含 `Section/Row_key/Line_order`
2. 是否存在 `Row_key=product_name` 且能取到 `Value_en`（或回退值）
3. `Model/Region/Page/Is_Latest/enabled` 是否把行过滤掉
