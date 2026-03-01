# 测试报告 - 260301（优化后复测）

- 测试日期: 2026-03-01
- 报告文件: `tests/test_report-260301.md`
- 执行人: Codex

## 1. 背景

基于上一版测试报告中的已知问题（转义安全、silent fail、SKU 选择策略、校验可定位性），已完成代码优化并进行复测。

## 2. 本次修复范围

- `tools/phase1/renderers.py`
  - 完善 `latex_arg_escape`，补齐 LaTeX 常见特殊字符转义。
  - `meta_json` 解析失败改为 fail-fast，错误信息包含 block/line。
- `tools/phase1/builder.py`
  - CSV 读取增加 `__line__`。
  - compact schema 遇到未知 `part` / 缺失 `part` 改为直接报错。
  - 非法 schema 改为明确报错。
- `tools/build_docs.py`
  - `config` 使用 `{sku}` 且多 SKU 时，未传 `--sku` 改为 fail-fast（不再隐式选首个 SKU）。
- `tools/gen_index_bundle.py`
  - 同步 SKU fail-fast 逻辑。
- `tools/validate_layout_params.py`
  - 数值/单位/CMYK 报错补齐行号。
- `config.yaml`
  - 新增 `build.default_sku: JB1000`，作为显式默认值。

## 3. 测试命令

```bash
python3 -m unittest discover -s tests -v
```

## 4. 测试结果

- 总用例数: 10
- 通过: 10
- 失败: 0
- 跳过/预期失败: 0
- 结论: 全部通过

## 5. 用例覆盖摘要

- `tests/test_phase1_renderers.py`
  - 渲染 happy path
  - LaTeX 特殊字符转义
  - 无效 `meta_json` fail-fast
- `tests/test_phase1_builder.py`
  - compact schema 正常转换
  - 未知 `part` fail-fast
- `tests/test_build_sku_resolution.py`
  - 显式 SKU 优先
  - 多 SKU + tokenized 配置时未指定 SKU 的 fail-fast
- `tests/test_validate_layout_params.py`
  - 重复 key 行号
  - 数值错误行号

## 6. 额外回归验证

文档构建复测：

```bash
python3 tools/build_docs.py --no-open
```

结果：构建成功，输出 PDF：
`/Users/pika/Documents/cms-demos/manual_demo/docs/_build/latex/manual_demo.pdf`

备注：仍存在字体环境告警（`Gilroy` 缺失），不影响本轮逻辑修复结论。
