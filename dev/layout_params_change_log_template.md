# Layout Params 变更记录模板（Phase1）

用于记录每一次 `data/layout_params.csv` 调整，确保可回溯、可复现、可回滚。

---

## 1. 变更基本信息

- 记录日期：`YYYY-MM-DD`
- 变更人：
- 分支：
- 关联任务/需求：
- 影响页面：`safety/spec`（可多选）
- 影响语言：`en/fr/es`（可多选）
- 变更目标（一句话）：

---

## 2. 参数变更明细

> 一次记录建议只覆盖同一类问题（如“spec 标题间距”）。

| key                                 |            旧值 |                             新值 | unit     | 影响范围          | 调整原因           |
| ----------------------------------- | --------------: | -------------------------------: | -------- | ----------------- | ------------------ |
| `comp_spec_section_after`         |        `0.40` |                         `0.13` | `mm`   | `spec en/fr/es` | 标题与下表间距压缩 |
| `comp_spec_section_bullet_symbol` | `\textbullet` | `\scalebox{1.67}{\textbullet}` | `none` | `spec en/fr/es` | 小节圆点放大       |

---

## 3. 非 CSV 代码变更（如有）

> 仅当 `.tex/.py` 同步改动时填写。

| 文件                      | 行号/位置 | 变更说明                                | 是否可参数化 |
| ------------------------- | --------- | --------------------------------------- | ------------ |
| `/abs/path/to/file.tex` | `Lxx`   | 示例：把 spec bullet 从 list raise 解耦 | 是/否        |

---

## 4. 验证步骤（必须）

执行命令：

```bash
python3 tools/validate_layout_params.py
python3 tools/csv_to_tex_params.py
python3 tools/build_docs.py --no-open
```

如怀疑缓存影响，再执行：

```bash
rm -rf docs/_build/latex
python3 tools/build_docs.py --no-open
```

---

## 5. 验证结果

- 参数校验：`通过/失败`
- 构建状态：`通过/失败`
- 产物路径：`docs/_build/latex/manual_demo.pdf`
- 视觉对比页面：
  - `safety_en`
  - `safety_fr`
  - `spec_en`
  - `spec_fr`
- 结果结论：

---

## 6. 风险与回滚

- 潜在副作用（例如 FR/ES 分页风险）：
- 回滚方式：
  - 恢复 key：`key1,key2,...`
  - 或回退 commit：

---

## 7. 审阅与确认

- 审阅人：
- 审阅结论：`通过/需调整`
- 最终确认时间：
