# OPS-05a：只读发布产物检查（不是部署验收）

在包含冻结发布产物的 checkout 中运行：

```bash
python -m tools.manual_operations_health \
  --repo-root . \
  --releases-root reports/releases \
  --output reports/manual_operations_health/health.json
```

报告扫描 `reports/releases/<model>/<market>/<language>/latest/web/publish_meta.json`，并检查
metadata 指向的受信任 release root 内全部 HTML 文件、`index.html` 及相对资源/链接。结果为
`manual-operations-health/v2` JSON，列出型号、市场、语言、版本、本地 HTML index、缺失资源
和失败原因；没有冻结 metadata 时为 `no_data`，故障时退出码为 1。部署状态和访客指标始终
明确为 `no_data`，本命令不联网、不写线上、不部署常驻服务、不统计访客。

发布负责人建议每次 Web Publish 后检查一次，或按周运行。故障按对应发布记录/Issue 定位，
必要时交由发布负责人处理；自动回滚尚属 OPS-04 待实现，不能把计划当作现有命令。该报告是可重建读模型，不是目录或内容权威；目录串联由
OPS-03 处理。第三方统计、Cookie、外部反馈渠道须另行完成隐私与采集批准。

`html_dir` 的相对路径以显式 `--repo-root`（默认当前目录）解释，安全范围始终为
`--releases-root`。HTML 的 src/href 支持查询参数、锚点、URL 编码和站内根路径，
越界链接与 HTML symlink 被报告为故障。CSS url()/srcset 和远端链接不探测。
语言维度只是元数据槽位，旧 `lang=en` 不证明正文单语；不能据此计算翻译齐套率。
本子切片不满足 OPS-05 的线上健康/负责人验收，整体 checklist 保持未勾选。
