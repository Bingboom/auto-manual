# 原稿归档范围与身份检查

当前范围由用户确认：仅归档原 PDF、插图和来源记录到 Git。完整英文逐字转写未完成，不继续转换正文；目录状态必须标记 archive-only、不可 Web 发布。不提交本地未审 OCR 输出。

封面和规格页均显示 JE-300E-SG；封面标识 US 联系电话，美规 120V 输出。原 PDF 43 页，18,416,463 字节；印刷版本未知；精确来源 SHA-256 写入 source_manifest.json。逐页检查页范围，正文三语范围记录 page-map.json。

独立工作区：/Users/pika/.codex/worktrees/je300e-sg-us-web/auto-manual2。主检出和 JA-TS02A PR 的工作区均保留。任务分支通过 scripts/start_branch.sh 创建于 main 9e7e27ed64196bf3a0cae639cae2c127ade4255c；使用既有系统代理和 HTTP/1.1 进行 Git 传输。

验证范围：原稿/复制件字节哈希、43 页页码地图、源图裁切坐标边界和 SHA-256、共享符号字节一致、图片格式完整、文件闭包、diff 检查和远端树读回。不是网页构建或排版验收。
