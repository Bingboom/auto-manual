# 产品中心门户

门户只聚合入口，产品资料来自 Hello-Docs 的 `docs/publish/`；实践正文留在钉钉。
此目录保留独立预览构建器；正式 RTD 首页使用工程侧 knowledge_hub 模板和同一链接配置。不写线上多维表，不触发发布队列。

## 构建与预览

从工程仓库根目录运行，指定一个已检出的 Hello-Docs 发布快照和空输出目录：

```bash
python3 prototypes/product-knowledge-hub/build_portal.py \
  --publish-root /path/to/Hello-Docs/docs/publish \
  --manual-base-url https://ht-doc.readthedocs.io/ \
  --output /tmp/product-hub-preview \
  --audience internal
python3 -m http.server 8765 --bind 127.0.0.1 --directory /tmp/product-hub-preview
```

打开 <http://127.0.0.1:8765/#home>。产品目录通过共享 RTD catalog 读取发布索引、
语言身份与图片，自动生成 `products.json`，不手工维护第二份产品目录。
输出目录必须为空，且不得与发布目录或原型源码目录重叠；构建只读取发布输入。

## 实践链接

在共享配置 [`practice-links.json`](../../tools/rtd_portal_assets/practice-links.json) 的 `practices` 数组中录入：

- `title`：卡片标题。
- `summary`：简短介绍。
- `tags`：例如 `["Vibe Coding"]`。
- `url`：实际的 HTTPS 钉钉云文档链接，域名 `alidocs.dingtalk.com`。
- `updated_at`：可选，真实文档更新日期（ISO 格式）；不填则不列入最近更新。
- `visibility`：只有明确标为 `public` 的条目才进入对外构建，默认仅内部。

当前链接数组为空，页面展示“实践文档待收录”。没有虚构 URL、演示正文或
无法点击的假卡片。点击卡片直接在新标签页打开钉钉，权限由钉钉控制。
搜索匹配标题、简介、标签；没有读取云文档正文，也不宣称全文检索云文档。

## 输出与职责

| 内容 | 来源与维护位置 |
| --- | --- |
| 已发布手册、配套图片、语言与版本 | Hello-Docs `docs/publish/` |
| AI / Vibe Coding 实践正文 | 钉钉云文档 |
| 门户布局、链接元数据 | 本目录，位于 `publish` 外 |
| 产品更新 | 发布清单 `built_at`，明确显示“发布包构建于”，不是文档修订日期 |
| 门户 JSON、样式、图片及来源指纹 | 独立输出目录，可重新生成 |

`portal-source.json` 记录输入发布清单哈希、条目数和展示范围。
原型先前保存的 `products.json`、`asset-sources.json` 和 `assets/` 仅保留为
旧版面快照；新构建不读取它们，不代表当前目录。下一次清理可单独移除。

## 内外版与部署边界

内部构建保留内外版视觉切换，按钮不是权限控制。真实内部部署需要访问控制。
`--audience public` 会在生成数据时排除内部链接元数据，同时去掉运行时切换按钮；
产品更新与明确公开的实践更新可以保留。公开页面目前不显示 AI 栏。
不要将内部构建用于公开站点。源码中的示例正文已移除。

正式 RTD 首页已经接入此版面，并复用原有章节全文索引；独立预览构建器
仍只按产品名称/型号及实践元数据筛选。
