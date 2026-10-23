"""v0.66 (operator 2026-10-20: 日本接 MTS 要由持证电工（電気工事士）施工，可以加一句提醒 → 可以 加进去):
「MTS設置時のご注意」 opens with a 注意 callout 「MTSの設置と分電盤への配線工事は、必ず電気工事士に依頼してください。」
JP-only (the US has no such sentence), drafted directly in Japanese: green jp-draft-insert, not in the English-based
translation count. The corpus only has 「資格のある電気技師」 (JE-1000E-WH JP grounding warning, a literal rendering of
"qualified electrician"); the legal term 電気工事士 is used here.

  python3 -I make_v066.py <v065_dir> <v066_dir>
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


JP = "MTSの設置と分電盤への配線工事は、必ず電気工事士に依頼してください。"
ZH = "MTS 的安装及与配电盘之间的接线工程，务必委托持证电工（電気工事士）进行。"
H3 = 'MTS設置時のご注意<span class="zh-translation" lang="zh-CN">MTS 安装须知</span></h3>'
rep(H3, H3 +
    '<table class="manual-callout-table" data-v066="true"><tbody><tr><td class="manual-callout-label"><p>'
    '<strong class="jp-original" data-jp-original-source="Translation_Memory: 注意" lang="ja">注意</strong></p>'
    '<span class="zh-translation" lang="zh-CN">注意</span></td><td class="manual-callout-body">'
    '<p class="en-new jp-draft-insert" data-v066="true" lang="ja" title="v0.66 日规新增（美规无对应句，直接按日文新译，待母语审校）">'
    f'{JP}<span class="zh-translation" lang="zh-CN">{ZH}</span></p></td></tr></tbody></table>'
    '<div class="jp-review" data-v066="true" lang="zh-CN"><strong>审阅：</strong>v0.66 按用户指示新增（日规专有，美规无此句）：'
    "在日本，MTS 接入住宅配电盘属于电气工程，按《電気工事士法》须由持证电工施工。语料库无「電気工事士」句；"
    "仅 JE-1000E-WH 日规接地警告有「資格のある電気技師」（qualified electrician 直译），此处改用法定用语「電気工事士」。"
    "直接按日文新译（绿色），无英文原文，未计入新增翻译量，请母语审校。</div>")

CHG = ("按用户指示，「MTS設置時のご注意」开头新增「注意」框：「MTSの設置と分電盤への配線工事は、必ず電気工事士に依頼してください。」"
       "（日规专有，美规无此句；语料库无现成句，直接按日文新译，绿色，未计入英文新增翻译量）。")
for old, new in (
    ("<title>JHP-3600C · 日规说明书审核稿 v0.65</title>", "<title>JHP-3600C · 日规说明书审核稿 v0.66</title>"),
    ("<small>本地审阅 · v0.65 · MTS 为市售品</small>", "<small>本地审阅 · v0.66 · MTS 须由電気工事士安装</small>"),
    ("<strong>v0.65 · MTS 为市售品 · ", "<strong>v0.66 · MTS 须由電気工事士安装 · v0.65 MTS 为市售品 · "),
    ('<span class="manual-locale-current">日本語（审核稿 v0.65）</span>', '<span class="manual-locale-current">日本語（审核稿 v0.66）</span>'),
    ('<p class="print-note">JHP-3600C v0.65；', '<p class="print-note">JHP-3600C v0.66；'),
    ("<summary>本次改写记录与日文版面依据</summary>",
     "<summary>本次改写记录与日文版面依据</summary><p><strong>v0.66（2026-10-20）</strong> — " + CHG + "</p>"),
):
    rep(old, new)
P.write_text(h, encoding="utf-8")

sec_md = "## v0.66 MTS 须由電気工事士安装\n\n" + CHG + "\n\n"
for nm in ("README.md", "review.zh.md"):
    path = DST / nm
    t = path.read_text(encoding="utf-8")
    if nm == "README.md":
        assert "# JHP-3600C 日规说明书审核稿 v0.65" in t
        t = t.replace("# JHP-3600C 日规说明书审核稿 v0.65", "# JHP-3600C 日规说明书审核稿 v0.66", 1)
        head, rest = t.split("\n## ", 1)
        t = head + "\n" + sec_md + "## " + rest
    else:
        t = sec_md + t
    path.write_text(t, encoding="utf-8")
print("ok")
