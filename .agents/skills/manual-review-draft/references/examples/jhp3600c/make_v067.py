"""v0.67 (operator 2026-10-20): spec table 「1 × AC入力」 follows the JE-1000F JP spec (主な仕様・入力ポート):
  - first line drops the label 「充電モード」 and keeps only the values;
  - 「パススルーモード①」 → 「パススルー①」 (existing JP, black; JE-1000F PDF — its Web copy has the typo 「バススルー」).
The two v0.53 term units (Charge Mode / Bypass Mode) leave the translation list; counts are refreshed with scripts/count_translation.py --previous.

  python3 -I make_v067.py <v066_dir> <v067_dir>
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

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


SRC_1000F = "JE-1000F 日规说明书 PDF「主な仕様・入力ポート」（Web 版此格误作「バススルー」）"
rep('<span class="en-new" data-needs-translation="term" data-previous-english="Charge Mode" data-translated="v0.53" lang="ja" '
    'title="v0.53 新译日文（按美规规格表结构新增）。原英文：Charge Mode">充電モード</span>：', "")
rep('<span class="en-new" data-needs-translation="term" data-previous-english="Bypass Mode" data-translated="v0.53" lang="ja" '
    'title="v0.53 新译日文（按美规规格表结构新增）。原英文：Bypass Mode">パススルーモード</span>',
    f'<span class="jp-original" data-jp-original-source="{SRC_1000F}" data-previous-english="Bypass Mode" data-v067="true" lang="ja" '
    f'title="现成日文：{SRC_1000F}">パススルー</span>')
rep('<span class="zh-translation" lang="zh-CN">充电模式：100–120V，50/60Hz，最大 15A，最大 1500W；旁路模式①：100–120V，50/60Hz，最大 15A，最大 1500W</span>',
    '<span class="zh-translation" lang="zh-CN">100–120V，50/60Hz，最大 15A，最大 1500W；旁路①：100–120V，50/60Hz，最大 15A，最大 1500W</span>')
rep("一行分写「充電モード」与「パススルーモード①」（美规 Charge Mode／Bypass Mode①，新译绿色）。",
    "一行分写「充電モード」与「パススルーモード①」（美规 Charge Mode／Bypass Mode①，新译绿色）。"
    "v0.67 按用户指示改按 JE-1000F 日规规格表：第一行去掉「充電モード」只写数值，「パススルーモード①」改为「パススルー①」（现成日文，黑色）。")
assert "パススルーモード</span><sup" not in h

CHG = ("按用户指示，规格表「1 × AC入力」改按 JE-1000F 日规规格表写法：第一行去掉「充電モード」只写数值；"
       "「パススルーモード①」改为「パススルー①」（现成日文，黑色）。两个 v0.53 新译术语单元移出新增翻译清单。")
for old, new in (
    ("<title>JHP-3600C · 日规说明书审核稿 v0.66</title>", "<title>JHP-3600C · 日规说明书审核稿 v0.67</title>"),
    ("<small>本地审阅 · v0.66 · MTS 须由電気工事士安装</small>", "<small>本地审阅 · v0.67 · AC入力行按 JE-1000F 写「パススルー①」</small>"),
    ("<strong>v0.66 · MTS 须由電気工事士安装 · ", "<strong>v0.67 · AC入力行按 JE-1000F 写「パススルー①」 · v0.66 MTS 须由電気工事士安装 · "),
    ('<span class="manual-locale-current">日本語（审核稿 v0.66）</span>', '<span class="manual-locale-current">日本語（审核稿 v0.67）</span>'),
    ('<p class="print-note">JHP-3600C v0.66；', '<p class="print-note">JHP-3600C v0.67；'),
    ("<summary>本次改写记录与日文版面依据</summary>",
     "<summary>本次改写记录与日文版面依据</summary><p><strong>v0.67（2026-10-20）</strong> — " + CHG + "</p>"),
):
    rep(old, new)
P.write_text(h, encoding="utf-8")

# translation list: drop the two removed units, recount ---------------------------------------------------
COUNT = Path(__file__).resolve().parents[3] / "scripts" / "count_translation.py"
subprocess.run([sys.executable, "-I", str(COUNT), str(P), str(DST), "--previous", str(SRC)], check=True)
summ = json.loads((DST / "new-translation-summary.json").read_text(encoding="utf-8"))

h = P.read_text(encoding="utf-8")
h, n = re.subn(r"需新增翻译量（v0\.\d+；", "需新增翻译量（v0.67；", h, count=1)
assert n == 1
h, n = re.subn(r"共 <strong>\d+</strong> 个单元（去重 \d+），英文 <strong>\d+</strong> 词（去重 \d+ 词），\d+ 字符。",
               f"共 <strong>{summ['units']}</strong> 个单元（去重 {summ['unique_units']}），英文 <strong>{summ['words']}</strong> 词"
               f"（去重 {summ['unique_words']} 词），{summ['chars']} 字符。", h, count=1)
assert n == 1
soup = BeautifulSoup(h, "html.parser")
h2 = next(t for t in soup.find_all("h2") if t.get_text().startswith("需新增翻译量"))
tables = [d.find("table") for d in h2.find_all_next("div", class_="jp-grid-composition", limit=2)]
for tbl, key in zip(tables, ("by_chapter", "by_type"), strict=True):
    tb = tbl.find("tbody")
    tb.clear()
    for name, d in summ[key].items():
        tr = soup.new_tag("tr")
        for v in (name, d["units"], d["words"]):
            td = soup.new_tag("td")
            td.string = str(v)
            tr.append(td)
        tb.append(tr)
P.write_text(str(soup), encoding="utf-8")

sec_md = "## v0.67 AC入力行按 JE-1000F 写「パススルー①」\n\n" + CHG + "\n\n" + \
    f"新增翻译量：{summ['units']} 个单元（去重 {summ['unique_units']}），英文 {summ['words']} 词（去重 {summ['unique_words']} 词）。\n\n"
for nm in ("README.md", "review.zh.md"):
    path = DST / nm
    t = path.read_text(encoding="utf-8")
    if nm == "README.md":
        assert "# JHP-3600C 日规说明书审核稿 v0.66" in t
        t = t.replace("# JHP-3600C 日规说明书审核稿 v0.66", "# JHP-3600C 日规说明书审核稿 v0.67", 1)
        head, rest = t.split("\n## ", 1)
        t = head + "\n" + sec_md + "## " + rest
    else:
        t = sec_md + t
    path.write_text(t, encoding="utf-8")
print("ok", {k: summ[k] for k in ("units", "unique_units", "words", "unique_words", "chars", "pending_parameters")})
