"""Build JHP-3600C JP review draft v0.15 from v0.14 + JP spec sheet (2026-10-12).

Usage: python3 -I make_v015.py <v014_dir> <out_dir>
"""
import json
import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(SRC, OUT)
HTML = OUT / "manual_jhp3600c_jp_en_draft.html"
soup = BeautifulSoup(HTML.read_text(encoding="utf-8"), "html.parser")

SPEC = "JHP-3600C 日规规格书（用户 2026-10-12 提供截图）"
JE5 = "data/manual_sources/JE-5000A/JP/git-20261010-26cccfe2-reviewed/web/ja/manual_je5000a_jp_ja.md"
LIVE = "Feishu 文档构建/内容源_规格参数明细"
REGISTER = []


def esc(t):
    return t.replace("&", "&amp;").replace('"', "&quot;")


def O(text, src):
    return f'<span class="jp-original" data-jp-original-source="{esc(src)}" lang="ja">{text}</span>'


def G(text, basis=SPEC):
    REGISTER.append({"value": text, "basis": basis})
    return f'<span class="jp-spec-filled" data-jp-spec-source="{esc(basis)}" lang="ja">{text}</span>'


def P(text):
    return f'<span class="us-difference jp-parameter">{text}</span>'


def E(text, reason):
    return f'<span class="us-difference" data-unmatched-reason="{esc(reason)}">{text}</span>'


def Z(text):
    return f'<span class="zh-translation" lang="zh-CN">{text}</span>'


def R(text, src=None):
    small = f'<small class="jp-review-source">{src}</small>' if src else ""
    return f'<div class="jp-review" data-v015="true" lang="zh-CN"><strong>审阅：</strong>{text}{small}</div>'


def frag(html):
    return BeautifulSoup(html, "html.parser")


def fill_param(name, value, zh_pairs=(), occurrences=None, basis=SPEC):
    """Replace a template-parameter span with a spec-filled value; patch the Chinese gloss."""
    els = soup.find_all(attrs={"data-template-parameter": name})
    assert els, name
    if occurrences is not None:
        assert len(els) == occurrences, (name, len(els))
    values = value if isinstance(value, list) else [value] * len(els)
    parents = set()
    for el, val in zip(els, values, strict=False):
        el["class"] = ["jp-spec-filled"]
        el["data-jp-spec-source"] = basis
        el["data-v015-filled"] = name
        el.string = val
        REGISTER.append({"value": val, "basis": basis, "template_parameter": name})
        parents.add(id(el.find_parent(["p", "li"])))
    for old, new, count in zh_pairs:
        hits = 0
        for zh in soup.select(".zh-translation"):
            if zh.string and old in zh.string:
                n = zh.string.count(old)
                hits += n
                zh.string.replace_with(zh.string.replace(old, new))
        assert hits == count, (name, old, hits)


# ---------------------------------------------------------------- styles
style = soup.new_tag("style")
style.string = (
    "html body #furo-main-content .jp-spec-filled.jp-spec-filled.jp-spec-filled,"
    "html body #furo-main-content :is(.jp-original,.us-difference,.jp-change) span.jp-spec-filled.jp-spec-filled"
    "{color:#047857 !important;font-weight:600}"
    "html body.only-changes #furo-main-content .jp-spec-filled{background:#ecfdf5;outline:1px solid #a7f3d0;outline-offset:2px}"
    ".legend i.green{background:#047857}"
    "html body #furo-main-content .jp-table th[colspan]{background:#f3f4f6;font-weight:700}"
    "html body #furo-main-content .jp-table td .jp-review{margin:8px 0 0}"
)
soup.head.append(style)

# ---------------------------------------------------------------- header/banner
hdr = soup.find("header")
hdr.find("strong").string = "JHP-3600C ／日规说明书 · 审核稿"
hdr.find("small").string = "本地审阅 · v0.15 · 日规规格书回填＋日文复用＋中文对照"
soup.title.string = "JHP-3600C · 日规说明书审核稿 v0.15"
banner = soup.find(class_="draft-banner")
banner.find("strong").string = "v0.15 · 按日规规格书回填参数 · 现成日文复用 · 剩余英文逐项说明"
legend = banner.find(class_="legend")
legend.append(frag('<span><i class="green"></i>绿色：本轮按日规规格书回填的参数</span>'))
banner.find(class_="legend-detail").string = (
    "绿色数值来自 2026-10-12 日规规格书；句式优先复用 JE-5000A 日规说明书（同为 100V/200V、L14-30R、6-20 端口）"
    "及线上日规规格参数表。规格书未列的参数仍为玫红占位，不以美规或其他机型数值代入。"
)

# ---------------------------------------------------------------- spec table
spec = soup.find(id="specifications")
tbody = spec.find("tbody")
rows = []


def row(label, value):
    rows.append(f"<tr><td>{label}</td><td>{value}</td></tr>")


def group(label):
    rows.append(f'<tr><th colspan="2">{label}</th></tr>')


row(O("製品の名称", LIVE + " JP:product_name") + Z("产品名称"),
    P("【未入力】") + Z("【待填】")
    + R("规格书称 HP3600 Pro Max，美规商品名 Jackery HomePower 3600 Pro Max。日文商品名（既有命名如“Jackery ポータブル電源 5000 Plus”）待业务确定，正文【製品名】同步替换。"))
row(O("型番", LIVE + " JP:model_no") + Z("型号"),
    P("JHP-3600C【要確認】") + Z("JHP-3600C【待确认】")
    + R("项目机型代码为 JHP-3600C；规格书未列日规铭牌型号，需确认是否相同。"))
row(O("定格容量", LIVE + " JP:capacity") + Z("额定容量"),
    P("【Ah/V：未入力】") + " (" + G("3584Wh") + ")" + Z("（Ah／电压待填）3584Wh")
    + R("规格书：3584Wh（C40）。句式同 JE-5000A 日规“45Ah/112Vdc (5040Wh)”。美规 80Ah/44.8V DC 未列入日规规格书，未代入。"))
row(O("バッテリータイプ", LIVE + " JP:cell_chemistry") + Z("电池类型"),
    O("LiFePO4（リン酸鉄リチウムイオン電池）", JE5 + " 主な仕様") + Z("LiFePO4（磷酸铁锂电池）"))
row(O("サイズ＆重量", LIVE + " JP:weight") + Z("尺寸与重量"),
    G("約375×275×450 mm (約32 kg）") + Z("约 375×275×450 mm（约 32 kg）")
    + R("规格书：32 kg，375×275×450 mm。句式同 JE-5000A 日规“約420×390×635 mm (約60 kg）”。注意美规为 33.5 kg（73.85 lbs），重量不一致，请以日规实测／铭牌为准。"))
row(O("サイクル寿命", LIVE + " JP:cycle_life") + Z("循环寿命"),
    O("6,000回の充放電後も容量の70％以上を維持", LIVE + " JBP-2000B_JP:cycle_life") + Z("充放电 6000 次后仍保持 70% 以上容量"))
row(O("UPS", JE5 + " 主な仕様") + Z("UPS"),
    G("10ms") + Z("切换时间 10 ms")
    + R("规格书“UPS：是（10ms）”；与 UPS 章节模板“約10ミリ秒（0.010秒）以内”一致。美规写＜10 ms。"))
group(O("入力ポート", JE5 + " 主な仕様") + Z("输入接口"))
row(O("AC入力", JE5 + " 右側面") + Z("交流输入"),
    O("100V-120V ~ 50/60Hz, 最大15A，最大", JE5 + " 右側面 AC入力") + G("1500W")
    + Z("100–120V，50/60Hz，最大 15A，最大 1500W")
    + R("规格书：AC 充电（日规）1500W，充电口为品字尾。电压／频率／电流沿用 JE-5000A 日规 AC 入力原句（与美规 100–120V、15A 一致）；美规 1800W 未采用。"))
row(O("AC出力(パススルー)", "Translation_Memory 術語表: AC Output in Bypass Mode") + Z("交流输出（直通）"),
    O("AC入力", JE5) + "：" + G("最大1500W") + "<br/>"
    + P("並列ポート") + "：" + G("最大30A，最大6000W")
    + Z("经 AC 输入：最大 1500W；经并机口：最大 30A，最大 6000W")
    + R("规格书：旁路功率 过流 30A，并机口 6000W；AC 品字尾 1500W。“並列ポート”为新拟日文（语料库无“并机口”术语，美规称 AC Expansion Port），玫红待日方定词。"))
row(O("2×DC8020ポート", LIVE + " JE-1000F_JP:dc8020_ports") + Z("2 个 DC8020 接口"),
    P("【電圧・電流：未入力】") + ", " + G("最大1200W") + Z("电压／电流待填，最大 1200W")
    + R("规格书：DC 充电 1200W Max（8020），右视图标“2×8020（低压光伏）”。美规 12–16V⎓8A／16–60V⎓12A（两口合计 24A）未列入日规规格书，未代入；是否支持シガーソケット充电待确认。"))
group(O("出力ポート", JE5 + " 主な仕様") + Z("输出接口"))
row(G("2 × ") + O("AC 出力", JE5) + G(" (NEMA 5-20R)") + Z("2 × 交流输出（NEMA 5-20R）"),
    O("100V ~ 50/60Hz, 20A, 2000W", JE5 + " 4 × AC 出力") + Z("100V，50/60Hz，20A，2000W")
    + R("规格书：2×AC 100V，20A，单口 2000W，与 JE-5000A 日规原句一致。频率 50/60Hz 为日规原句写法，规格书未列，请确认。"))
row(O("AC 出力(NEMA L14-30R)", JE5) + Z("交流输出（NEMA L14-30R）"),
    O("100V/200V ~ 50/60Hz, ", JE5) + G("最大20A, 最大4000W") + Z("100V/200V，50/60Hz，最大 20A，最大 4000W")
    + R("规格书：1×AC 100V/200V，20A，4000W；外观图标注“NEMA L14-30”（插座写法沿用 JE-5000A 日规 L14-30R）。JE-5000A 同口为最大 30A，本机按规格书 20A。"))
row(O("AC 出力(NEMA 6-20)", JE5) + Z("交流输出（NEMA 6-20）"),
    O("200V ~ 50/60Hz, 最大20A", JE5) + ", " + G("最大4000W") + Z("200V，50/60Hz，最大 20A，最大 4000W")
    + R("规格书：1×AC 200V，20A，4000W；位于右侧面（美规此位置为 EPO 端子）。"))
row(O("AC Total 出力", JE5) + Z("交流总输出"),
    G("最大4000W") + ", " + P("【瞬間最大：未入力】") + Z("最大 4000W，瞬时峰值待填")
    + R("规格书：AC 输出 4000W Max，未列瞬时峰值（美规 8000W Surge 未代入）。另：规格书备注“主机逆变器只有 3.6kW”，与 4000W 额定需厂内统一口径。"))
row(G("1 × ") + O("USB-C 出力", JE5) + Z("1 × USB-C 输出"),
    O("5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A, 最大100W", JE5 + " 2 × USB-C 出力") + Z("最大 100W")
    + R("规格书：1×USB-C 100W Max（PD）。各档电压电流与 JE-5000A 日规及美规一致。"))
row(G("1 × ") + O("USB-A 出力", JE5) + Z("1 × USB-A 输出"),
    O("5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A, 最大18W", JE5 + " 2 × USB-A 出力") + Z("最大 18W")
    + R("规格书：1×USB-A 18W Max。"))
row(O("バッテリーパック", "docs/templates/page_jp/charging.rst") + Z("扩展电池包"),
    G("Jackery Battery Pack 3600 × 最大5個（合計 約21.5kWh）") + Z("Jackery Battery Pack 3600，最多 5 个（合计约 21.5kWh）")
    + R("规格书：单机 Max 21.5kWh，加电包共用 BP3600；21.5kWh＝3584Wh＋5×3584Wh，与美规“最多 5 个”一致。BP3600 日文商品名、DC 拡張ポート电压电流（美规 36.4–50.4V⎓126A/60A）待确认。"))
row(E("Cascade parallel connection", "本机新增并机功能；现有日文模板与语料无对应术语，保留美规英文标签待日方定词。") + Z("级联并机"),
    G("2台・最大6000W（並列通信ポート ×1）／最大43kWh") + Z("2 台，最大 6000W（并机通讯口 1 个）；最大 43kWh")
    + R("规格书：并机＝通过级联并机 6kW；并机通讯口 1 个；级联后可扩容到 43kWh（2×21.5kWh）。“並列通信ポート”等日文用语语料库无，需日方定词。"))
row(O("騒音", "Translation_Memory 句対: 静音充電モード説明（充電中の騒音…）") + Z("噪音"),
    G("≤50dB（静音充電モード時の充電：≤30dB）") + Z("≤50dB（静音模式充电时 ≤30dB）")
    + R("规格书新增项：噪音 静音模式充电 ≤30dB，≤50dB。美规规格表无此项，是否写入日规规格表请确认。"))
row(O("充電温度<br/>動作温度", LIVE + " JP:charging/discharging_temperature") + Z("充电温度／工作温度"),
    P("【未入力】") + Z("【待填】") + R("规格书未列；美规充放电均为 -20～45°C，未代入。"))
row(O("保存温度", LIVE + " JP:storage_temperature") + Z("存放温度"),
    P("【未入力】") + Z("【待填】")
    + R("规格书未列。既有日规机型写法为“1ヶ月 -20℃~45℃／3ヶ月 0℃~45℃／1年間 0℃~25℃”，本机待确认。"))
row(E("Altitude / installation conditions", "该项为本机新增规格；现有日文模板与语料无完整对应原句。") + Z("海拔／安装条件"),
    P("【未入力】") + Z("【待填】") + R("规格书未列；美规 ≤3000m。"))
row(E("Certification / required markings", "该项为本机新增规格／标识要求，现有日文模板与语料无完整对应原句；待补充本机日规资料。") + Z("认证／必需标识"),
    P("【未入力】") + Z("【待填】") + R("待按日规认证包补齐（PSE 等标识及编号）。"))
tbody.clear()
tbody.append(frag("".join(rows)))

# trademark line: JE-5000A reviewed JP manual keeps it in English
tm = spec.find(string=re.compile("USB Type-C® and USB-C® are registered")).find_parent("p")
nxt = tm.find_next_sibling()
if nxt is not None and "jp-review" in (nxt.get("class") or []):
    nxt.decompose()
tm.replace_with(frag(
    '<p class="jp-original" data-jp-original-source="' + JE5 + ' 主な仕様" lang="ja">'
    "※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."
    + Z("※USB Type-C® 和 USB-C® 是 USB Implementers Forum 的注册商标。（日规原稿保留英文）") + "</p>"
    + '<p class="jp-original" data-jp-original-source="' + JE5 + ' 主な仕様" lang="ja">'
    "本機の仕様および外観は、改善のため予告なく変更することがあります。"
    + Z("本机的规格和外观可能因改进而变更，恕不另行通知。") + "</p>"))
spec_review = spec.find_all(class_="jp-review")[-1]
spec_review.clear()
spec_review.append(frag(
    "<strong>审阅：</strong>v0.15 按日规规格书回填（绿色）。表结构与句式参照 JE-5000A 日规说明书“主な仕様”及线上日规规格参数表；"
    "规格书未列的数值保留玫红，不以美规或其他机型数值代入。美规“EPO / other interfaces”行已删除：日规外观图与规格书均无 EPO 端子。"
    "规格书中 APP（有）、显示屏（彩色断码屏）、轮子＆拉杆（无）、包装（牛皮盒＋贴纸）不属于既有日规规格表项目，未列入。"
    '<small class="jp-review-source">版面依据：manual_jp.yaml: spec ／ JE-5000A JP 主な仕様</small>'))
first_note = spec.find(attrs={"data-review-placeholder": "true"})
if first_note is not None:
    first_note.string = "最终数值须与经确认的日规规格书及产品标签一致。绿色为 2026-10-12 规格书数值；玫红为规格书未列、待确认项。"

# ---------------------------------------------------------------- product overview
po = soup.find(id="product-overview")
figs = po.find_all("figure")
front_fig, right_fig = figs[0], figs[1]
front_fig.find("figcaption").string = (
    "审阅：美规原图 · 主机正面。日规正面为 NEMA L14-30R（100V/200V）＋2×NEMA 5-20R（100V）；图中 NEMA 14-50R、"
    "120/240 V、60 Hz 等美规标注不适用，需按日规规格书正视图重绘。")
right_fig.find("figcaption").string = (
    "审阅：美规原图 · 主机右侧。日规右侧依次为并机口、并机通讯口、NEMA 6-20（200V）、2×DC8020（低压光伏）、"
    "AC 充电口（品字尾），面板左列为扩容口；美规 EPO 端子日规无。需按日规右视图重绘。")
front_fig_html, right_fig_html = str(front_fig), str(right_fig)
TH = ('<thead><tr><th class="us-difference" data-jp-original-source="table_header:日文补写" lang="ja">項目'
      + Z("项目") + '</th><th class="jp-original" data-jp-original-source="docs/templates/page_jp/safety_ja.rst" lang="ja">説明'
      + Z("说明") + "</th></tr></thead>")


def table(rws):
    body = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rws)
    return f'<div class="jp-table-scroll"><table class="jp-table">{TH}<tbody>{body}</tbody></table></div>'


front_rows = [
    (O("LCDディスプレイ", "data/phase2/Localized_Copy.csv:product_overview.part.lcd") + Z("LCD 显示屏"),
     R("规格书：彩色断码屏。")),
    (O("主電源ボタン", "docs/templates/page_jp/05_operation_guide_placeholder.rst") + Z("主电源按钮"), ""),
    (O("USB-C 出力ポート", JE5 + " 前面") + Z("USB-C 输出接口"),
     O("5V ⎓ 3A, 9V ⎓ 3A, 12V ⎓ 3A, 15V ⎓ 3A, 20V ⎓ 5A, 最大100W", JE5 + " 前面") + Z("最大 100W")),
    (O("USB-A 出力ポート", JE5 + " 前面") + Z("USB-A 输出接口"),
     O("5-6V ⎓ 3A, 6-9V ⎓ 2A, 9-12V ⎓ 1.5A, 最大18W", JE5 + " 前面") + Z("最大 18W")),
    (O("USB出力ボタン", "docs/templates/page_jp/05_operation_guide_placeholder.rst") + Z("USB 输出按钮"), ""),
    (O("AC出力ポート (NEMA 5-20)", JE5 + " 前面") + G(" ×2") + Z("交流输出接口（NEMA 5-20）×2"),
     O("1*AC出力: 100V~ 50/60Hz, 20A, 2000W", JE5 + " 前面") + Z("单口：100V，50/60Hz，20A，2000W")
     + R("规格书写 2×NEMA 5-20R；JE-5000A 日规原稿写 NEMA 5-20。两种写法待统一。")),
    (O("AC出力ボタン", "data/phase2/Spec_Master.csv:ac_power_button/JP") + Z("交流输出按钮"), ""),
    (O("NEMA L14-30R AC出力ポート", JE5 + " 左側面") + Z("NEMA L14-30R 交流输出接口"),
     O("100V/200V ~ 50/60Hz, ", JE5 + " 左側面") + G("最大20A，最大4000W") + "<br/>"
     + O("高出力機器に電力を供給し、家庭用電源のインレットボックスまたは切替スイッチに接続します。", JE5 + " 左側面")
     + Z("100V/200V，50/60Hz，最大 20A，最大 4000W。为大功率设备供电，并可连接住宅电源入户箱或切换开关。")
     + R("功能说明句来自 JE-5000A 日规；本机规格书选配 MTS 连接线／ATS，适用的入户箱／切换开关连接方式需确认。")),
]
right_rows = [
    (O("ハンドル", "Translation_Memory 術語表: Handle") + Z("把手"), R("规格书：顶部把手；无轮子和拉杆。")),
    (E("AC Expansion Port", "本机新增并机口；现有日文模板与语料无对应术语。") + Z("并机口"),
     O("AC出力(パススルー)", "Translation_Memory 術語表") + "：" + G("最大30A，最大6000W") + Z("旁路：最大 30A，最大 6000W")
     + R("规格书：并机口，级联并机 6kW，旁路 过流 30A／6000W。候选日文“並列ポート”（新拟，非语料），待日方确认。")),
    (E("Parallel Communication", "本机新增并机通讯口；现有日文模板与语料无对应术语。") + Z("并机通讯口"),
     R("规格书：并机通讯口 1 个；选配 30A 并机通讯线。候选日文“並列通信ポート”（新拟，非语料），待日方确认。")),
    (O("NEMA 6-20 AC出力ポート", JE5 + " 左側面") + Z("NEMA 6-20 交流输出接口"),
     O("200V ~ 50/60Hz, 最大20A", JE5 + " 左側面") + "，" + G("最大4000W") + "<br/>"
     + O("200Vの入力電圧を必要とする機器と互換性があります。", JE5 + " 左側面")
     + Z("200V，50/60Hz，最大 20A，最大 4000W。适用于需要 200V 输入电压的设备。")),
    (O("低電圧入力ポート", JE5 + " 右側面") + Z("低压输入接口"),
     G("2 x DC8020ポート；最大1200W") + Z("2 个 DC8020 接口，最大 1200W")
     + R("规格书：2×8020（低压光伏），1200W Max。各档电压电流（美规 12–16V⎓8A／16–60V⎓12A）未列入日规规格书，未代入。")),
    (O("AC入力", JE5 + " 右側面") + Z("交流输入"),
     O("100V-120V ~ 50/60Hz, 最大15A，最大", JE5 + " 右側面") + G("1500W") + Z("100–120V，50/60Hz，最大 15A，最大 1500W")
     + R("规格书：AC 充电口（品字尾），日规 1500W。")),
    (O("DC拡張ポート", JE5 + " 右側面 DC拡張ポート端子A") + Z("直流扩展接口（扩容口）"),
     O("バッテリーパックに接続", JE5 + " 右側面") + Z("连接电池包") + R("规格书：扩容口位于右侧面板左列；加电包共用 BP3600。")),
]
new_po = (
    '<div class="jp-change">'
    + str(po.find("h2"))  # 正面
    + front_fig_html + table(front_rows)
    + str(po.find_all("h2")[1])  # 右側面
    + right_fig_html + table(right_rows)
    + R("v0.15 按日规规格书正视图／右视图重排端口表，端口说明优先复用 JE-5000A 日规原句（同为 L14-30R、6-20、5-20 端口）。"
        "日规无 EPO 端子，美规 EPO 行已删除；并机口、并机通讯口在语料库中无日文，保留英文标签并给出候选日文。主机外观图仍为美规原图，需设计按日规外观重绘。",
        "版面依据：03_product_overview_placeholder.rst ／ JE-5000A JP 各部の名称")
    + "</div>")
po_body = po.find("div", class_="jp-change", recursive=False)
po_body.replace_with(frag(new_po))

# ---------------------------------------------------------------- box
box = soup.find(id="what-s-in-the-box")
box_review = box.find_all(class_="jp-review")[-1]
box_review.clear()
box_review.append(frag(
    "<strong>审阅：</strong>v0.15：日规规格书确认标配为 本体／AC 充电线（品字尾）／说明书，与日规三栏版面一致；"
    "美规附带的 EPO 螺丝端子台日规不附。主机与 AC 充电线仍为美规原图，日规插头图待补。包装：牛皮盒＋贴纸。"
    '<small class="jp-review-source">版面依据：02_whats_in_the_box.rst</small>'))
for cap in box.find_all("figcaption"):
    if "交流充电线" in cap.get_text():
        cap.string = "审阅：美规原图 · 交流充电线。日规为品字尾 AC 充电线（规格书），日规插头图待补。"

# ---------------------------------------------------------------- LCD
lcd_review = soup.find(id="lcd-display").find(class_="jp-review")
lcd_review.append(frag("<br/>v0.15：规格书显示屏为“彩色断码屏”；图标编号与状态仍需按日规固件核对（EPO 相关显示日规不适用）。"))

# ---------------------------------------------------------------- operations: USB-C PS3 note
fill_param("USB_C_RATING", "100W", [("USB-C【功率待填】", "USB-C 100W", 1)], occurrences=2)
fill_param("USB_C_CABLE_CURRENT", "5A", basis=SPEC + "；100W PD 端口线缆要求（模板原值）", occurrences=1)
fill_param("USB_C_CABLE_RATING", "20V DC/5A", basis=SPEC + "；100W PD 端口线缆要求（模板原值）", occurrences=1,
           zh_pairs=[("获得最大输出所需的线缆电流、电压与功率等级均【待填】", "获得最大输出请使用 USB-C to USB-C 5A 线缆（20V DC/5A，100W）", 1)])

# ---------------------------------------------------------------- UPS
fill_param("UPS_BYPASS_OUTPUT_TEXT", "1500W", [("【最大旁路输出待填】", "1500W", 2)], occurrences=2)
ups = soup.find(id="uninterruptible-power-supply-ups")
ups.find(class_="jp-ups-template").append(frag(R(
    "v0.15：规格书 UPS 10ms，与模板“約10ミリ秒（0.010秒）以内”一致；AC 品字尾旁路功率 1500W 已回填（同 JE-5000A 日规“最大出力は1500Wに制限”）。"
    "经并机口旁路（30A／6000W）及 MTS／ATS 备电场景本节模板未覆盖，见文末审阅清单。")))

# ---------------------------------------------------------------- charging: battery pack
fill_param("BATTERY_PACK_COUNT", "5", [("最多可连接【数量待填】个电池包", "最多可连接 5 个电池包", 1)], occurrences=1,
           basis=SPEC + "：单机 Max 21.5kWh＝3584Wh＋5×BP3600")
fill_param("BATTERY_PACK_MANUAL", "Jackery Battery Pack 3600の取扱説明書",
           [("【适配电池包说明书待填】", "《Jackery Battery Pack 3600 使用说明书》", 1)], occurrences=1,
           basis=SPEC + "：加电包共用 BP3600")
fill_param("BATTERY_PACK_NAME", "Jackery Battery Pack 3600", [("【适配电池包待填】", "Jackery Battery Pack 3600", 1)],
           occurrences=1, basis=SPEC + "：加电包共用 BP3600")
bp_par = soup.find(attrs={"data-v015-filled": "BATTERY_PACK_NAME"}).find_parent("ul")
bp_review = bp_par.find_next_sibling(class_="jp-review")
bp_review.clear()
bp_review.append(frag(
    "<strong>审阅：</strong>v0.15：规格书单机最大 21.5kWh＝本机 3584Wh＋5×BP3600，与美规“最多 5 个”一致，已回填 5 个及 "
    "Jackery Battery Pack 3600（日文商品名待确认）。散热间距：美规约 200 mm、JE-5000A 日规写“少なくとも20cm”，规格书未列，仍待确认；"
    "堆叠层数及防倾倒条件待确认。级联并机后可扩容至 43kWh，见规格表。"
    '<small class="jp-review-source">版面依据：charging.rst: model_je_2000e ／ JE-5000A JP バッテリーパック（別売）に接続</small>'))

# ---------------------------------------------------------------- charging: solar
fill_param("SOLAR_CONNECTOR", "DC8020", [("（【连接器待填】）", "（DC8020）", 1)], occurrences=1)
fill_param("DC_INPUT_COUNT", ["2", "2つ", "2つ"],
           [("×【接口数量待填】", "×2", 1), ("为【数量待填】个【接口型号待填】连接", "为 2 个 DC8020 接口连接", 1)], occurrences=3)
fill_param("SOLAR_INPUT_CONNECTOR", "DC8020", occurrences=1)
fill_param("SOLAR_MAX_INPUT", "1200W", [("合计最大输入功率为【待填】", "合计最大输入功率为 1200W", 1)], occurrences=1)
solar_review = soup.find(attrs={"data-v015-filled": "SOLAR_INPUT_CONNECTOR"}).find_parent("p")
for sib in solar_review.find_next_siblings():
    if "jp-review" in (sib.get("class") or []):
        sib.append(frag(
            "<br/>v0.15：规格书 DC 充电 1200W Max（2×8020，低压光伏），已回填接口与总功率。选配为 200W 光伏板；"
            "可连接块数须按 8020 输入电压范围及串并联方式确认后再填，不能按 1200÷200 简单推算。"))
        break

# ---------------------------------------------------------------- AC cable review
for rv in soup.find(id="charging").find_all(class_="jp-review"):
    if "AC 充电线" in rv.get_text() and "插头插紧" not in rv.get_text() and rv.find("small"):
        if "使用日规“AC 充电线”标题" in rv.get_text():
            rv.find("small").insert_before(frag("<br/>v0.15：规格书 AC 充电（日规）1500W，充电口为品字尾；日规插头图仍待补。"))

# ---------------------------------------------------------------- appendix
app = soup.find(id="jp-review-appendix")
app.clear()
app.append(frag(
    "<h1>中文审阅清单</h1>"
    "<p><strong>产品定位（用户提供）：</strong>针对日本家庭 200V 用电场景开发，日本首款用户可负担得起的即插即用式、大功率自动备电储能解决方案。"
    "核心升级：支持 200V 家用空调；边充边放，100V/200V 双电压输出。</p>"
    "<h2>v0.15 已按日规规格书回填（绿色）</h2><ul>"
    "<li>规格表：3584Wh、LiFePO4、约 375×275×450 mm／约 32 kg、6000 次／70%、UPS 10ms、AC 入力 1500W、旁路 1500W／并机口 30A·6000W、"
    "DC8020×2 最大 1200W、2×AC 100V 20A 2000W、L14-30R 100V/200V 20A 4000W、6-20 200V 20A 4000W、总输出 4000W、USB-C 100W、USB-A 18W、"
    "BP3600 最多 5 个（21.5kWh）、级联并机 2 台 6kW／43kWh、噪音。</li>"
    "<li>各部名称：按日规正视图／右视图重排端口，删除 EPO；端口说明复用 JE-5000A 日规原句。</li>"
    "<li>同梱品：本体／AC 充电线（品字尾）／说明书 已确认。</li>"
    "<li>正文参数：USB-C 100W（PS3 注意事项）、UPS 旁路 1500W、电池包 5 个／Jackery Battery Pack 3600、太阳能 DC8020×2／1200W。</li></ul>"
    "<h2>规格书与美规差异，需确认</h2><ul>"
    "<li><strong>重量：</strong>规格书 32 kg，美规 33.5 kg。</li>"
    "<li><strong>输出口：</strong>美规 NEMA 14-50R（240V）→ 日规 NEMA L14-30R（100V/200V，20A）；日规右侧新增 NEMA 6-20（200V），无 EPO。</li>"
    "<li><strong>额定与逆变器：</strong>规格书 AC 输出 4000W Max，但备注“主机逆变器只有 3.6kW”，两者口径需统一。</li>"
    "<li><strong>AC 充电／旁路：</strong>日规 1500W（品字尾）；美规 1800W 充电、1440W 旁路。并机口旁路 30A／6000W。</li>"
    "<li><strong>型号与商品名：</strong>规格书写 HP3600 Pro Max；日文商品名、铭牌型号、BP3600 日文名待定。</li></ul>"
    "<h2>章节结构待决定</h2><ul>"
    "<li><strong>连接章节：</strong>美规有“CONNECTIONS”章（电池包、级联并机、EPO、ATS、MTS 单机／级联）及 ATS 附章；本稿目前只有电池包小节。"
    "规格书选配含 BP3600、ATS、MTS 连接线、30A 并机通讯线、20A 快充线、30A 并机／快充线、200W 光伏板、储能推车，需决定日规版纳入哪些连接章节。EPO 章不纳入（日规无 EPO）。</li>"
    "<li><strong>MTS 注意事项（规格书备注）：</strong>由于主机逆变器只有 3.6kW，接入 MTS 时需要注意负载功率，大于逆变器功率可能会过载断电。若增加 MTS 章节，须写入此注意事项。</li>"
    "<li><strong>200V 充电：</strong>美规有经 AC 扩展口的 240V 充电小节；日规选配快充线暗示经并机口 200V 快充，规格书未给功率，需确认是否增加小节。</li>"
    "<li><strong>温度、海拔、通风间距、待机／省电时间、保修期限、客服信息：</strong>规格书未列，仍为玫红占位。</li></ul>"
    "<h2>沿用项</h2><ul>"
    "<li><strong>认证：</strong>已从主文移除美规 FCC 章。日本 PSE／无线认证标识、编号和法定文案按认证包补齐。</li>"
    "<li><strong>本机新增 LCD 功能：</strong>31 项图标与日文共享模板的差异需逐项确认；尤其 TOU、自发电、充电计划、智能电表、EV 充电和并联。</li>"
    "<li><strong>参考版面边界：</strong>依据仓库日规共享模板、JE-1000F/JP 已生成 RST、线上日规规格参数表及 JE-5000A/JP 已审日文说明书；"
    "未宣称找到 JHP-3600C 已批准日规原稿。新拟日文（並列ポート、並列通信ポート）均标玫红。</li></ul>"))

# ---------------------------------------------------------------- change log
cl = soup.find(class_="change-log")
cl.find("summary").insert_after(frag(
    "<p><strong>v0.15（2026-10-12）</strong> — 按日规规格书回填规格表、各部名称、同梱品、UPS 旁路、电池包、太阳能与 USB-C 参数；"
    "日文句式复用 JE-5000A/JP 已审说明书与线上日规规格参数表。</p>"))
foot = soup.find(class_="footer-note")
foot.append(frag(" 参数依据：JHP-3600C 日规规格书（2026-10-12）。"))

HTML.write_text(str(soup), encoding="utf-8")
(OUT / "jp-spec-fill-register.json").write_text(
    json.dumps({"revision": "0.15", "spec_basis": SPEC, "wording_sources": [JE5, LIVE, "Translation_Memory"],
                "filled": REGISTER}, ensure_ascii=False, indent=1), encoding="utf-8")
print("filled values:", len(REGISTER))
