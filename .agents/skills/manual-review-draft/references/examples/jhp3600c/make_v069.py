"""v0.69 (operator 2026-10-21, Feishu screenshot: 首次 指代 改到这里来): the first product-name reference moves from the
preface to the opening sentence of 「使用上のご注意」:
  「Jackery HomePower 3600 Plus Max（以下、「本製品」）は、定格出力4000Wです。…」 (the JE-1000F original also opens with
  the full product name there — 「Jackery ポータブル電源 1000 New は、…」).
The preface keeps the full name without the reference: 「このたびは、Jackery HomePower 3600 Plus Maxをご購入いただき、…」.
Format 「（以下、「本製品」）」 follows the operator's screenshot (with 、).

  python3 -I make_v069.py <v068_dir> <v069_dir>
"""
import shutil
import sys
from pathlib import Path

SRC, DST = Path(sys.argv[1]), Path(sys.argv[2])
if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
P = DST / "manual_jhp3600c_jp_en_draft.html"
h = P.read_text(encoding="utf-8")


def rep(old: str, new: str, count: int = 1) -> None:
    global h
    n = h.count(old)
    if n != count:
        raise SystemExit(f"expected {count} got {n}: {old[:120]}")
    h = h.replace(old, new)


NAME = ('<span class="jp-spec-updated" data-previous-value="—" data-spec-ref="商品名称" data-spec-source="用户 2026-10-14 提供（商品名称），'
        '与 A0 规格书正面丝印“HomePower 3600 Plus Max”一致" lang="ja" title="商品名称：用户 2026-10-14 提供（商品名称），'
        '与 A0 规格书正面丝印“HomePower 3600 Plus Max”一致">Jackery HomePower 3600 Plus Max</span>')
OLD_T = 'title="商品名称指代（v0.24，全称见卷首）"'
NEW_T = 'title="商品名称指代（v0.24；v0.69 起全称与「（以下、「本製品」）」见「使用上のご注意」首句）"'

# 1. preface: drop the reference, keep the full name ---------------------------------------------------------
rep(NAME + f'<span class="jp-name-ref" lang="ja" {OLD_T}>（以下「本製品」）</span>をご購入いただき、誠にありがとうございます。'
    '<span class="zh-translation" lang="zh-CN">感谢您购买 Jackery HomePower 3600 Plus Max（以下简称“本产品”）。</span></p>',
    NAME + 'をご購入いただき、誠にありがとうございます。'
    '<span class="zh-translation" lang="zh-CN">感谢您购买 Jackery HomePower 3600 Plus Max。</span></p>'
    '<div class="jp-review" data-v069="true" lang="zh-CN"><strong>审阅：</strong>v0.69 按用户指示，首次指代「（以下、「本製品」）」'
    "移至「使用上のご注意」首句；此处只保留全称。</div>")
rep("＋ 用户指示「（以下「本製品」）」", "")

# 2. 使用上のご注意 opening sentence: full name + reference ------------------------------------------------------
rep('<div class="jp-usage-intro"><p class="jp-original" data-jp-original-source="JE-1000F JP 取扱説明書（RTD 已发布版，2026-10-12 抓取）· 安全上のご注意" lang="ja">'
    f'<span class="jp-name-ref" lang="ja" {OLD_T}>本製品</span>は、定格出力',
    '<div class="jp-usage-intro"><p class="jp-original" data-jp-original-source="JE-1000F JP 取扱説明書（RTD 已发布版，2026-10-12 抓取）· 安全上のご注意" lang="ja">'
    + NAME + f'<span class="jp-name-ref" data-v069="true" lang="ja" {NEW_T}>（以下、「本製品」）</span>は、定格出力')
rep('<span class="zh-translation" lang="zh-CN">本产品额定输出 4000W，通常可为功耗不超过 4000W 的设备供电',
    '<span class="zh-translation" lang="zh-CN">Jackery HomePower 3600 Plus Max（以下简称“本产品”）额定输出 4000W，通常可为功耗不超过 4000W 的设备供电')
rep("可能需要标称功率 3～7 倍的功率。</span></p>",
    "可能需要标称功率 3～7 倍的功率。</span></p>"
    '<div class="jp-review" data-v069="true" lang="zh-CN"><strong>审阅：</strong>v0.69 按用户指示，商品全称与首次指代「（以下、「本製品」）」'
    "放在此句（原在卷首感谢句）。JE-1000F 日规此句原本即以全称开头（「Jackery ポータブル電源 1000 New は、…」）；"
    "指代写法「（以下、「本製品」）」按用户示例，日文语料中无原句，请日方确认。此前「安全上のご注意」警告／注意中的「本製品」不改。</div>")

# 3. tooltips on the remaining 本製品 references ---------------------------------------------------------------
n = h.count(OLD_T)
assert n == 13, n
h = h.replace(OLD_T, NEW_T)

CHG = ("按用户指示，首次指代移到「使用上のご注意」首句：「Jackery HomePower 3600 Plus Max（以下、「本製品」）は、定格出力4000Wです。」"
       "（JE-1000F 日规此句原即以全称开头）；卷首感谢句去掉「（以下「本製品」）」，保留全称。指代写法按用户示例加「、」。")
for old, new in (
    ("<title>JHP-3600C · 日规说明书审核稿 v0.68</title>", "<title>JHP-3600C · 日规说明书审核稿 v0.69</title>"),
    ("<small>本地审阅 · v0.68 · DC8020 行补「シガーソケット」「PV」</small>", "<small>本地审阅 · v0.69 · 首次指代移至「使用上のご注意」</small>"),
    ("<strong>v0.68 · DC8020 行补「シガーソケット」「PV」 · ",
     "<strong>v0.69 · 首次指代移至「使用上のご注意」 · v0.68 DC8020 行补「シガーソケット」「PV」 · "),
    ('<span class="manual-locale-current">日本語（审核稿 v0.68）</span>', '<span class="manual-locale-current">日本語（审核稿 v0.69）</span>'),
    ('<p class="print-note">JHP-3600C v0.68；', '<p class="print-note">JHP-3600C v0.69；'),
    ("<summary>本次改写记录与日文版面依据</summary>",
     "<summary>本次改写记录与日文版面依据</summary><p><strong>v0.69（2026-10-21）</strong> — " + CHG + "</p>"),
):
    rep(old, new)
P.write_text(h, encoding="utf-8")

sec_md = "## v0.69 首次指代移至「使用上のご注意」\n\n" + CHG + "\n\n"
for nm in ("README.md", "review.zh.md"):
    path = DST / nm
    t = path.read_text(encoding="utf-8")
    if nm == "README.md":
        assert "# JHP-3600C 日规说明书审核稿 v0.68" in t
        t = t.replace("# JHP-3600C 日规说明书审核稿 v0.68", "# JHP-3600C 日规说明书审核稿 v0.69", 1)
        head, rest = t.split("\n## ", 1)
        t = head + "\n" + sec_md + "## " + rest
    else:
        t = sec_md + t
    path.write_text(t, encoding="utf-8")
print("ok")
