"""v0.16: English CONNECTIONS chapter + English port labels (no JP term in RTD-published JP manuals).

Usage: python3 -I make_v016.py <v015_dir> <us_fig_dir> <out_dir>
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SRC, FIG, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(SRC, OUT)
for stale in OUT.glob("JHP-3600C-JP-*.zip"):
    stale.unlink()
HTML = OUT / "manual_jhp3600c_jp_en_draft.html"
soup = BeautifulSoup(HTML.read_text(encoding="utf-8"), "html.parser")

SPEC = "JHP-3600C 日规规格书（用户 2026-10-12 提供截图）"
US = "https://ht-doc.readthedocs.io/JHP-3600C/US/en/md/manual_jhp3600c_us_en.html · CONNECTIONS"
RTD_JP = ("RTD 已发布日文说明书 6 本（JA-AD500A-SIL、JBP-1000B-WH、JBP-5000A、JE-1000E-WH、JE-1000F、JE-5000A）"
          "均无对应日文端口名（仅有故障名“並列ユニット通信エラー”、DC 拡張ポート），按用户 2026-10-12 指示保留美规英文")
REG = {"revision": "0.16", "english_by_request": "用户 2026-10-12：连接章节“加，写成英语的”", "figures": [], "spec_values": []}


def esc(t):
    return t.replace("&", "&amp;").replace('"', "&quot;")


def frag(h):
    return BeautifulSoup(h, "html.parser")


def Z(t):
    return f'<span class="zh-translation" lang="zh-CN">{t}</span>'


def G(t):
    REG["spec_values"].append(t)
    return f'<span class="jp-spec-filled" data-jp-spec-source="{esc(SPEC)}" lang="en">{t}</span>'


def P(t):
    return f'<span class="us-difference jp-parameter" lang="en">{t}</span>'


def R(t, src=None):
    small = f'<small class="jp-review-source">{src}</small>' if src else ""
    return f'<div class="jp-review" data-v016="true" lang="zh-CN"><strong>审阅：</strong>{t}{small}</div>'


def EN(t, zh, tag="p"):
    return f'<{tag} class="us-retained" data-us-source="{esc(US)}" lang="en">{t}{Z(zh)}</{tag}>'


def H(level, t, zh, sold=False):
    extra = ' <span class="us-retained">— SOLD SEPARATELY</span>' if sold else ""
    return f'<h{level} class="us-retained" data-us-source="{esc(US)}" lang="en">{t}{extra}{Z(zh)}</h{level}>'


def callout(label, zh_label, body):
    return (f'<div class="jp-callout"><strong class="us-retained" lang="en">{label}{Z(zh_label)}</strong>'
            f"{body}</div>")


def steps(items):
    lis = "".join(f'<li class="us-retained" data-us-source="{esc(US)}" lang="en">{t}{Z(z)}{extra}</li>'
                  for t, z, extra in items)
    return f"<ol>{lis}</ol>"


def figure(name, alt, caption):
    data = (FIG / f"{name}.png").read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    (OUT / "assets" / f"{sha}.png").write_bytes(data)
    REG["figures"].append({"reference_id": name, "asset": f"assets/{sha}.png", "sha256": sha,
                           "source": US + f" · figure[data-reference-id={name}] (Chromium 渲染截图，含美规 live 标注)"})
    return (f'<figure class="us-review-figure" data-us-image-source="{esc(US)}#{name}">'
            f'<img alt="{alt}" loading="eager" src="assets/{sha}.png"/>'
            f'<figcaption class="jp-review" lang="zh-CN">{caption}</figcaption></figure>')


# ------------------------------------------------------------ 1. English port labels
def replace_text(old, new, expected):
    hits = 0
    for s in list(soup.find_all(string=lambda x: x and old in x)):
        hits += s.count(old)
        s.replace_with(s.replace(old, new))
    assert hits == expected, (old, hits)


# spec table: bypass via parallel port
par = soup.find("span", class_="jp-parameter", string="並列ポート")
par.replace_with(frag(f'<span class="us-difference" data-unmatched-reason="{esc(RTD_JP)}" lang="en">AC Expansion Port</span>'))
replace_text("（並列通信ポート ×1）", "（Parallel Communication ×1）", 1)
replace_text("“並列ポート”为新拟日文（语料库无“并机口”术语，美规称 AC Expansion Port），玫红待日方定词。",
             "并机口用美规英文标签“AC Expansion Port”：RTD 已发布日文说明书无对应日文。", 1)
replace_text("“並列通信ポート”等日文用语语料库无，需日方定词。",
             "并机通讯口用美规英文“Parallel Communication”：RTD 已发布日文说明书无对应日文。", 1)
replace_text("候选日文“並列ポート”（新拟，非语料），待日方确认。", "RTD 已发布日文说明书无对应日文，保留美规英文标签。", 1)
replace_text("候选日文“並列通信ポート”（新拟，非语料），待日方确认。", "RTD 已发布日文说明书无对应日文，保留美规英文标签。", 1)
replace_text("并机口、并机通讯口在语料库中无日文，保留英文标签并给出候选日文。",
             "并机口、并机通讯口在 RTD 已发布日文说明书中无对应日文，按用户指示保留美规英文标签。", 1)
for el in soup.select("[data-unmatched-reason]"):
    if el.get_text(strip=True).startswith(("AC Expansion Port", "Parallel Communication")):
        el["data-unmatched-reason"] = RTD_JP

# ------------------------------------------------------------ 2. CONNECTIONS chapter (English)
PN = P("[PRODUCT NAME]")
chapter = (
    '<section data-english-by-request="2026-10-12" data-jp-layout-source="JHP-3600C US en · CONNECTIONS" id="connections">'
    f'<h1 class="us-difference" lang="en">CONNECTIONS{Z("连接（按用户要求以英文撰写）")}</h1>'
    '<div class="jp-change">'
    + R("v0.16 按用户指示新增本章，以英文撰写（RTD 已发布日文说明书无对应日文原句）。依据美规 CONNECTIONS 章，按日规规格书改写："
        "240V→100V/200V，NEMA 14-50R→NEMA L14-30R，8000W→6000W，美规 40A Charging Cable→日规选配线缆。美规 EPO 小节不纳入（日规无 EPO）；"
        "电池包连接保留在「充電方法」章（日规模板位置），本章不重复。黑色＝美规原句，绿色＝日规规格书数值，玫红＝改写／待确认。"
        "[PRODUCT NAME] 为日文商品名占位。", "版面依据：JHP-3600C US en · CONNECTIONS")
    # ---- cascade parallel
    + H(2, "CASCADE PARALLEL CONNECTION", "级联并机")
    + f'<p class="us-retained" data-us-source="{esc(US)}" lang="en">Cascade connection allows 2 {PN} units to operate as a combined system, '
      f"increasing total output power. Total output: up to {G('6000W')}; total capacity with battery packs: up to {G('43kWh')}."
      + Z("级联连接可使 2 台本产品作为一个系统运行，提高总输出功率。总输出最大 6000W；连接电池包后总容量最大 43kWh。") + "</p>"
    + H(3, "Required Accessories", "所需配件")
    + f'<p class="us-retained" lang="en">{G("Jackery 30A Parallel/Fast Charging Cable")} · {G("Jackery 30A Parallel Communication Cable")} — Sold separately'
      + Z("Jackery 30A 并机／快充线 · Jackery 30A 并机通讯线（需另购）") + "</p>"
    + R("线缆英文名按规格书选配件中文名“30A 并机/快充线”“30A 并机通讯线”译出，正式名称待确认；美规为 Jackery 40A Charging Cable · Jackery Parallel Communication Cable。")
    + H(3, "Connection Steps", "连接步骤")
    + steps([
        ("Ensure both units are powered OFF and completely disconnected from power sources.", "确认两台设备均已关机，并与所有电源完全断开。", ""),
        ("Connect Parallel Communication ports on both units.", "连接两台设备的并机通讯口。", ""),
    ])
    + callout("CAUTION", "注意", EN("Do not skip this step. Without communication, the units cannot synchronize data and may be damaged.",
                                   "请勿跳过此步骤。未建立通讯时，两台设备无法同步数据，可能导致损坏。"))
    + '<ol start="3">'
    + f'<li class="us-retained" lang="en">Connect the first unit\'s {G("100V/200V Output Port (NEMA L14-30R)")} to the second unit\'s AC Expansion Port.'
      + Z("将第一台的 100V/200V 输出口（NEMA L14-30R）连接到第二台的 AC Expansion Port（并机口）。")
      + R("美规为第一台 240V 输出（NEMA 14-50R）接第二台 AC Expansion Port。日规对应端口按规格书推定为 L14-30R → 并机口，使用 30A 并机/快充线，需确认。") + "</li>"
    + f'<li class="us-retained" lang="en">System information will synchronize across both displays.{Z("两台显示屏上的系统信息将同步。")}</li></ol>'
    + figure("cascade", "级联并机连接",
             "审阅：美规原图（RTD 渲染截图）· 级联并机。图中 NEMA 14-50R 插头、40A 充电线为美规；日规为 NEMA L14-30R 与 30A 并机/快充线，需按日规外观重绘。")
    + callout("CAUTION", "注意",
              f'<p class="us-retained" lang="en">After cascading, the total system output power via the {P("[OUTPUT PORT TBC]")} of the second unit is '
              f"{G('6000W')}. The total load MUST NOT exceed total power."
              + Z("级联后，经第二台【输出口待确认】输出的系统总功率为 6000W。总负载不得超过总功率。") + "</p>")
    + R("规格书：级联并机 6kW。美规由第二台 NEMA 14-50R 输出 8000W；日规 L14-30R 规格书为 20A／4000W，6000W 需经哪个端口输出待确认。")
    # ---- backup power
    + H(2, "BACKUP POWER CONNECTION", "备用电源连接")
    + H(3, "CONNECT TO ATS", "连接 ATS（需另购）", sold=True)
    + EN(f"{PN} can supply backup power to home circuits through a Jackery Automatic Transfer Switch (ATS). "
         "For detailed installation and operation, refer to the Jackery ATS User Manual.",
         "本产品可通过 Jackery 自动切换开关（ATS）为家庭回路提供备用电源。详细安装和操作请参阅 Jackery ATS 使用说明书。")
    + figure("ats-lock", "ATS 电源线锁定", "审阅：美规原图 · ATS 电源输入／输出线锁定与解锁。日规 ATS 型号、线缆及是否在日本销售待确认。")
    + callout("NOTE", "提示",
              f'<p class="us-retained" lang="en">When UPS mode is enabled on the ATS, the power station remains active and continuously consumes power. '
              f"During a grid outage, the system switches to battery power within {P('20 milliseconds [TBC]')}."
              + Z("在 ATS 上启用 UPS 模式时，储能电源保持运行并持续耗电。电网停电时，系统在【20 毫秒，待确认】内切换为电池供电。") + "</p>")
    + R("美规 ATS 模式切换为 20 ms；规格书只写本机 UPS 10ms，ATS 场景切换时间待确认。规格书选配 ATS 外观为美式配电箱，日规 ATS 型号待确认。")
    + H(3, "CONNECT TO MTS", "连接 MTS（需另购）", sold=True)
    + EN(f"{PN} can be connected to a Manual Transfer Switch (MTS) to power selected home circuits. "
         "Choose the appropriate method based on your installation mode.",
         "本产品可连接手动切换开关（MTS），为选定的家庭回路供电。请根据安装方式选择合适的连接方法。")
    + callout("NOTE", "提示", EN("All cables used in this section are sold separately or included with the separately sold MTS.",
                                "本节使用的所有线缆均需另购，或随另购的 MTS 附带。"))
    + callout("CAUTION", "注意",
              f'<p class="jp-spec-filled" data-jp-spec-source="{esc(SPEC)}：备注" lang="en">The built-in inverter of this product is rated at 3.6kW. '
              "When connecting to an MTS, pay attention to the total load power. A load exceeding the inverter power may cause an overload shutdown."
              + Z("由于主机逆变器只有 3.6kW，接入 MTS 时需要注意负载功率，大于逆变器功率可能会过载断电。") + "</p>")
    + R("上述注意事项按日规规格书备注新增（英文为译写）。美规另有 MTS 安装提示（AC 输入建议接非 GFCI 回路，GFCI 装在负载侧）；"
        "GFCI 属美规电气体系，日本对应为漏电断路器，未写入正文，适用性待电气确认。")
    + H(3, "SINGLE UNIT CONNECTION WITH MTS", "单机连接 MTS")
    + EN(f"In automatic mode, {PN} receives AC input and provides UPS-like backup power through the MTS.",
         "自动模式下，本产品接收交流输入，并通过 MTS 提供类似 UPS 的备用电源。")
    + steps([
        (f"Power OFF {PN}.", "关闭本产品电源。", ""),
        (f"Connect {PN} to a {P('[100V / 200V TBC]')} AC power supply.", "将本产品连接到【100V／200V 待确认】交流电源。",
         R("美规为经 40A 充电线把 240V 市电接入 AC Expansion Port。日规可经 AC 充电口（100V，1500W）或经并机口用 20A 快充线／30A 并机/快充线接 200V，规格书未说明，需确认输入方式及旁路功率。")),
        (f"Connect the {G('100V/200V Output Port (NEMA L14-30R)')} to the MTS inlet.", "将 100V/200V 输出口（NEMA L14-30R）连接到 MTS 入口。",
         R("规格书选配“MTS 连接线”；L14-30R 用于连接入户箱／切换开关与 JE-5000A 日规说明一致。")),
        ("Turn the load switch of the MTS to backup.", "将 MTS 的负载开关拨到备用（backup）。", ""),
        ("Turn ON the unit and enable AC Output.", "开启本产品并打开交流输出。", ""),
    ])
    + figure("mts-single", "单机连接 MTS",
             "审阅：美规原图 · 单机连接 MTS。图中 240V 输入、NEMA 14-50R、40A 充电线及美式配电箱为美规；日规按 L14-30R＋MTS 连接线重绘，输入方式待确认。")
    + f'<p class="us-retained" lang="en">When grid power is present, AC power passes through to the MTS. During a power outage, the system automatically '
      f"switches to battery power within {G('10 milliseconds')}."
      + Z("有市电时，交流电直通至 MTS；停电时，系统在 10 毫秒内自动切换为电池供电。") + "</p>"
    + callout("NOTE", "提示", EN("Automatic switching requires the AC input to remain connected at all times.", "自动切换要求交流输入始终保持连接。"))
    + H(3, "CASCADE PARALLEL CONNECTION WITH MTS", "级联并机连接 MTS")
    + EN("When two units are connected in cascade parallel mode, the system can deliver higher output power to the MTS.",
         "两台设备以级联并机方式连接时，系统可向 MTS 提供更高的输出功率。")
    + steps([
        ("Complete the Cascade Parallel Connection steps described earlier.", "先完成前述级联并机连接步骤。", ""),
        (f"Connect the second unit's {G('100V/200V Output Port (NEMA L14-30R)')} to the MTS inlet.", "将第二台的 100V/200V 输出口（NEMA L14-30R）连接到 MTS 入口。", ""),
        ("Turn ON both units and enable AC Output.", "开启两台设备并打开交流输出。", ""),
    ])
    + figure("mts-cascade", "级联并机连接 MTS", "审阅：美规原图 · 级联并机连接 MTS。图中 240V 端口与线缆为美规，日规待按 L14-30R 及日规线缆重绘。")
    + callout("CAUTION", "注意",
              f'<p class="us-retained" lang="en">After cascading, the maximum output to the MTS is {G("6000W")}. The total load MUST NOT exceed total power.'
              + Z("级联后，输出至 MTS 的最大功率为 6000W。总负载不得超过总功率。") + "</p>")
    + R("规格书级联 6kW；L14-30R 规格书为 20A／4000W，经 L14-30R 输出 6000W 是否成立需确认。另请结合单机逆变器 3.6kW 备注核对。")
    + "</div></section>"
)
soup.find(id="uninterruptible-power-supply-ups").insert_after(frag(chapter))
ups_link = soup.select_one('aside.toc a[href="#uninterruptible-power-supply-ups"]')
ups_link.insert_after(frag('<a href="#connections">连接（英文）</a>'))

# ------------------------------------------------------------ 3. labels, appendix, change log
soup.find("header").find("small").string = "本地审阅 · v0.16 · 日规规格书回填＋英文连接章节＋中文对照"
soup.title.string = "JHP-3600C · 日规说明书审核稿 v0.16"
soup.find(class_="draft-banner").find("strong").string = "v0.16 · 规格书参数回填 · 新增英文连接章节 · 现成日文复用"
style = soup.new_tag("style")
style.string = ("html body #furo-main-content section#connections ol{padding-left:1.4em}"
                "html body #furo-main-content section#connections li{margin:8px 0}"
                "html body #furo-main-content section#connections h3{margin-top:26px}")
soup.head.append(style)

app = soup.find(id="jp-review-appendix")
for li in app.find_all("li"):
    txt = li.get_text()
    if txt.startswith("连接章节："):
        li.clear()
        li.append(frag("<strong>连接章节：</strong>v0.16 已按用户指示以英文新增 CONNECTIONS 章（级联并机、ATS、MTS 单机／级联），"
                       "EPO 不纳入；电池包连接仍在「充電方法」章。端口映射（L14-30R→并机口）、线缆名称、MTS 输入方式、ATS 切换时间及 6000W 输出端口待确认。"))
    elif txt.startswith("MTS 注意事项"):
        li.clear()
        li.append(frag("<strong>MTS 注意事项（规格书备注）：</strong>已写入 CONNECT TO MTS 的 CAUTION（英文译写）。"))
    elif txt.startswith("参考版面边界"):
        li.clear()
        li.append(frag("<strong>参考版面边界：</strong>依据仓库日规共享模板、JE-1000F/JP 已生成 RST、线上日规规格参数表及 JE-5000A/JP 已审日文说明书；"
                       "未宣称找到 JHP-3600C 已批准日规原稿。并机口、并机通讯口在 RTD 已发布 6 本日文说明书中无对应日文，按用户指示保留英文"
                       "（AC Expansion Port、Parallel Communication）。"))
cl = soup.find(class_="change-log")
cl.find("summary").insert_after(frag(
    "<p><strong>v0.16（2026-10-12）</strong> — 新增英文 CONNECTIONS 章（级联并机、ATS、MTS），按日规规格书改写端口与功率；"
    "并机口／并机通讯口改用美规英文标签（RTD 已发布日文说明书无对应日文）。</p>"))

HTML.write_text(str(soup), encoding="utf-8")
(OUT / "jp-connections-register.json").write_text(json.dumps(REG, ensure_ascii=False, indent=1), encoding="utf-8")
print("figures:", len(REG["figures"]), "spec values:", len(REG["spec_values"]))
