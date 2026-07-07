# IDML 字体映射（translate-idml retypeset 用）· 全系统通用

翻译 IDML 时把源版欧文字体换成目标语种字体（防豆腐字）。配 `translate-idml` 的 retypeset / fill 用。

> **原则：字体按【脚本 script】选，不按语言。** 一套字体覆盖一个脚本下的所有语言 —— 所谓"英文字体 Gilroy"其实是**拉丁字体**，德/法/西/意/荷/葡/波/捷…同一套 `fontmap-EN-gilroy.json`。哪个语言用哪套，见 **[`语言字体映射.yml`](./语言字体映射.yml)**（脚本 × 语言全表，源自配套规范 §4.4，字形覆盖经 fontTools 实测）。

| 文件 | 脚本 | 用途 |
|---|---|---|
| `fontmap-EN-gilroy.json` | 拉丁 | 中文字体（方正兰亭各字重/思源黑体/宋体等）→ **Gilroy** 对应权重；`_preserve` 温存 Noto Sans SC；段落开 Hyphenation。**覆盖全部拉丁语种**（en/fr/de/it/es/nl/pt/pl/cs…，字形已验证） |
| `fontmap-JA-noto.json` | 日文 | Gilroy 等欧文 → **Noto Sans JP**；`_preserve` 温存日文前文 Noto Sans SC / EmojiOne；旧 Noto 缺的 SemiBold 正规化到 Bold |
| `fontmap-KO-source-han.json` | 谚文 | 中文各字重 + Gilroy → **Source Han Sans K**（自带拉丁字形，欧文一并归一）；⚠ 已建**未实测**，首次 KO retypeset 校验豆腐字/字重/粉色名 |

**状态**（见 `语言字体映射.yml` status 字段）：西里尔(乌/俄)已定用 Gilroy(字形实测覆盖，用户接受) ✅；韩语 fontmap 已建待实测 ✅；阿拉伯(RTL)**暂不在范围**。

新语种照此格式加 `fontmap-<lang>-*.json` 并在 `语言字体映射.yml` 登记。⚠ InDesign 里字体名变粉色=本机实名不符，改 family 为已安装实名（如 `Noto Sans CJK JP`）后重跑。配套日语规范见 `共享内容/通用/翻译规范/日语-house-style.md`。
