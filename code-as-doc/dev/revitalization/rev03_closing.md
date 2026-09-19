# REV-03：入口整合收尾核验（旧站下线）

执行：操作者于 2026-09-19 在 RTD 后台删除 `ht-manuals` 项目；核验由 Claude（Fable）执行。

## 死亡探针（2026-09-19T08:32:21Z）

| 探针 | 结果 |
|---|---|
| `https://ht-manuals.readthedocs.io/` | 404 |
| `https://ht-manuals.readthedocs.io/en/latest/` | 404 |
| `https://ht-manuals.readthedocs.io/manual_je1000f_us.html` | 404 |
| `https://readthedocs.org/api/v3/projects/ht-manuals/` | 404 |

对照：删除前同日 07:50Z 探针为 302/200/404/200（项目 `modified` 时间戳仍为
2026-08-02T12:15:47Z，证明删除前项目从未被改动过）。

## 新站回归（同时点）

门户、`JE-1000F/US/en` 嵌套正式页、`manual_je1000f_us.html` 旧形态兼容页、
`JE-1000H/EU/uk` 页全部 200；`ht-doc` 项目 API 200。

## 旧链接去向与恢复路径

- 三个受管登记面对旧域名零引用（[rev02_conclusions.md](rev02_conclusions.md)），
  旧 URL 形态由新站兼容跳转页承接（实测 200）；
- 旧站唯一内容（JE-1000F US 1.7）的重建来源 `Hello-Docs` `publish` 分支完好
  （tip `902adab8`），未删除——符合方案 §3.5 第 5 条"停止旧站更新不等于删除
  publish 分支"。

## 验收口径

REV-03 退出证据五项对照：迁移范围=操作者拍板直接删除（聊天记录 2026-09-19）；
跳转/兼容=新站兼容页实测；停止独立更新=项目已删（强于停止）；映射恢复记录=
[rev01_url_map.csv](rev01_url_map.csv) + publish 分支在位；历史版本语义=唯一
重叠目标 JE-1000F US 的 1.7→2.3 差异已在 [rev01_inventory.md](rev01_inventory.md)
留档。
