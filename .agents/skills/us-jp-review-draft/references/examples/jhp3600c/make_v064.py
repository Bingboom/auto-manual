"""v0.64 (operator 2026-10-20):
  1. UPS: the two new-translation sentences reuse the corpus where it says the same thing
     (docs/templates/page_jp/06_ups_mode.rst, also JE-3600A／JE-5000A／JE-1000F JP):
       「…によって変わり、」(new) +「停電時には定格出力に戻ります。」(corpus, black)
       「本製品の最大出力を超える負荷を接続しないでください。」(new) +「超えると、機器が過負荷保護により停止するおそれがあります。」(corpus, black)
  2. 「MTSに接続する（別売り）」 heading → 「手動切替スイッチ（MTS）に接続する（別売り）」 (full name, new words green).
The translation list / counts are refreshed with scripts/count_translation.py --previous (the two units keep only their new-translation English).

  python3 -I make_v064.py <v063_dir> <v064_dir>
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


CORPUS = "docs/templates/page_jp/06_ups_mode.rst（JE-3600A／JE-5000A／JE-1000F 日规同句）"
E1A = "In UPS mode, the unit's peak output varies with grid input voltages before power outages."
E1 = E1A + " The actual output power returns to the rated output power during outages."
E2A = "Do not connect loads exceeding the maximum output power of the product."
E2 = E2A + " Otherwise, overload protection will be triggered."


def unit(old_jp: str, old_zh: str, eng: str, eng_new: str, jp_new: str, jp_corpus: str, zh: str) -> None:
    global h
    m = re.findall(r'<p class="en-new" data-needs-translation="sentence" data-previous-english="' + re.escape(eng)
                   + r'"[^>]*>' + re.escape(old_jp) + r'<span class="zh-translation" lang="zh-CN">' + re.escape(old_zh) + r"</span></p>", h)
    assert len(m) == 1, (eng, len(m))
    new = (f'<p data-us-source="JHP-3600C US en · UPS" data-v064="true" lang="ja">'
           f'<span class="en-new" data-needs-translation="sentence" data-previous-english="{eng_new}" data-translated="v0.51" lang="ja" '
           f'title="新译日文（v0.64 起只含本句，后半句改用现成日文）。原英文：{eng_new}">{jp_new}</span>'
           f'<span class="jp-original" data-jp-original-source="{CORPUS}" data-previous-english="{eng[len(eng_new) + 1:]}" lang="ja" '
           f'title="现成日文复用：{CORPUS}">{jp_corpus}</span>'
           f'<span class="zh-translation" lang="zh-CN">{zh}</span></p>')
    h = h.replace(m[0], new)


# 1. UPS sentences ---------------------------------------------------------------------------------------
unit("UPSモードでは、停電前の本機のピーク出力は系統電力の入力電圧によって変動します。停電時には、実際の出力電力は定格出力に戻ります。",
     "UPS 模式下，停电前本机的峰值输出随市电输入电压而变化；停电期间，实际输出功率恢复为额定输出功率。",
     E1, E1A, "UPSモードでは、停電前の本機のピーク出力は系統電力の入力電圧によって変わり、", "停電時には定格出力に戻ります。",
     "UPS 模式下，停电前本机的峰值输出随市电输入电压而变化，停电时恢复为额定输出。")
unit("本製品の最大出力を超える負荷を接続しないでください。接続すると過負荷保護が作動します。",
     "请勿连接超过本产品最大输出功率的负载，否则将触发过载保护。",
     E2, E2A, "本製品の最大出力を超える負荷を接続しないでください。", "超えると、機器が過負荷保護により停止するおそれがあります。",
     "请勿连接超过本产品最大输出功率的负载。超过时，设备可能因过载保护而停止。")
NOTE = ('<div class="jp-review" data-v064="true" lang="zh-CN"><strong>审阅：</strong>v0.64 按用户指示复用现成日文：'
        "「停電時には定格出力に戻ります。」「超えると、機器が過負荷保護により停止するおそれがあります。」取自日文模板 06_ups_mode.rst"
        "（JE-3600A／JE-5000A／JE-1000F 日规同句，黑色），与美规后半句同义；前半句仍为新译（绿色）。模板原句中的“最大出力電流は…に制限”"
        "与本机（100V 输入超出部分由电池补足、200V 输入 20A／4000W）不符，未采用。</div>")
i = h.index("超えると、機器が過負荷保護により停止するおそれがあります。</span>")
j = h.index("</p>", i) + len("</p>")
h = h[:j] + NOTE + h[j:]

# 2. MTS chapter heading --------------------------------------------------------------------------------
GI = '<span class="en-new jp-draft-insert" lang="ja" title="v0.64 新加（新译：章节标题写全称「手動切替スイッチ」）">{}</span>'
rep('lang="ja">MTSに接続する（別売り）<span class="zh-translation" lang="zh-CN">连接 MTS（需另购）</span></h2>',
    f'lang="ja">{GI.format("手動切替スイッチ（")}MTS{GI.format("）")}に接続する（別売り）'
    '<span class="zh-translation" lang="zh-CN">连接手动切换开关（MTS）（需另购）</span></h2>')

CHG = ("按用户指示：① UPS 章两句复用现成日文——「停電時には定格出力に戻ります。」「超えると、機器が過負荷保護により停止するおそれがあります。」"
       "取自日文模板 06_ups_mode.rst（JE-3600A／JE-5000A／JE-1000F 日规同句，黑色），前半句仍为新译（绿色），新增翻译量相应减少；"
       "② 章节标题「MTSに接続する（別売り）」改为「手動切替スイッチ（MTS）に接続する（別売り）」，「手動切替スイッチ（」「）」为新加（绿色）。")
for old, new in (
    ("<title>JHP-3600C · 日规说明书审核稿 v0.63</title>", "<title>JHP-3600C · 日规说明书审核稿 v0.64</title>"),
    ("<small>本地审阅 · v0.63 · L14-30R 加回用途说明句</small>", "<small>本地审阅 · v0.64 · UPS 两句复用语料 · MTS 标题写全称</small>"),
    ("<strong>v0.63 · L14-30R 加回用途说明句 · ", "<strong>v0.64 · UPS 两句复用语料 · MTS 标题写全称 · v0.63 L14-30R 加回用途说明句 · "),
    ('<span class="manual-locale-current">日本語（审核稿 v0.63）</span>', '<span class="manual-locale-current">日本語（审核稿 v0.64）</span>'),
    ('<p class="print-note">JHP-3600C v0.63；', '<p class="print-note">JHP-3600C v0.64；'),
    ("<summary>本次改写记录与日文版面依据</summary>",
     "<summary>本次改写记录与日文版面依据</summary><p><strong>v0.64（2026-10-20）</strong> — " + CHG + "</p>"),
):
    rep(old, new)
P.write_text(h, encoding="utf-8")

# 3. translation list: recount, carrying the previous version's rows forward (the two split units are recounted) ---
COUNT = Path(__file__).resolve().parents[3] / "scripts" / "count_translation.py"
subprocess.run([sys.executable, "-I", str(COUNT), str(P), str(DST), "--previous", str(SRC)], check=True)
summ = json.loads((DST / "new-translation-summary.json").read_text(encoding="utf-8"))

# appendix numbers
h = P.read_text(encoding="utf-8")
rep("需新增翻译量（v0.53；", "需新增翻译量（v0.64；")
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

sec_md = "## v0.64 UPS 两句复用语料 · MTS 标题写全称\n\n" + CHG + "\n\n" + \
    f"新增翻译量：{summ['units']} 个单元（去重 {summ['unique_units']}），英文 {summ['words']} 词（去重 {summ['unique_words']} 词）。\n\n"
for nm in ("README.md", "review.zh.md"):
    path = DST / nm
    t = path.read_text(encoding="utf-8")
    if nm == "README.md":
        assert "# JHP-3600C 日规说明书审核稿 v0.63" in t
        t = t.replace("# JHP-3600C 日规说明书审核稿 v0.63", "# JHP-3600C 日规说明书审核稿 v0.64", 1)
        head, rest = t.split("\n## ", 1)
        t = head + "\n" + sec_md + "## " + rest
    else:
        t = sec_md + t
    path.write_text(t, encoding="utf-8")
print("ok", {k: summ[k] for k in ("units", "unique_units", "words", "unique_words", "chars", "pending_parameters")})
