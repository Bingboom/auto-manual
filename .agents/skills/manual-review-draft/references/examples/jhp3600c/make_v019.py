"""v0.19: add 200V-input UPS and 200V charging subsections (adapted from US 240V sections).

Usage: python3 -I make_v019.py <v018_dir> <us_fig_dir> <out_dir>
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

US = "JHP-3600C US en（https://ht-doc.readthedocs.io/JHP-3600C/US/en/md/manual_jhp3600c_us_en.html）"
SPEC = "JHP-3600C 日规规格书（2026-10-12）"
TM = "Translation_Memory"
REG = {"revision": "0.19", "request": "用户 2026-10-12：200V 充电和 UPS 小节加上，附录先不加", "figures": []}


def esc(t):
    return t.replace("&", "&amp;").replace('"', "&quot;")


def frag(h):
    return BeautifulSoup(h, "html.parser")


def Z(t):
    return f'<span class="zh-translation" lang="zh-CN">{t}</span>'


def R(t, src=None):
    small = f'<small class="jp-review-source">{src}</small>' if src else ""
    return f'<div class="jp-review" lang="zh-CN"><strong>审阅：</strong>{t}{small}</div>'


def P(t):
    return f'<span class="us-difference jp-parameter">{t}</span>'


def N(t, kind="sentence", ref=None):
    r = f' data-reference-jp="{esc(ref)}"' if ref else ""
    return f'<span class="en-new" data-needs-translation="{kind}" lang="en"{r}>{t}</span>'


def NB(tag, t, zh, kind="sentence", ref=None, extra=""):
    r = f' data-reference-jp="{esc(ref)}"' if ref else ""
    return f'<{tag} class="en-new" data-needs-translation="{kind}" lang="en"{r}>{t}{Z(zh)}{extra}</{tag}>'


def J(t, src):
    return f'<span class="jp-original" data-jp-original-source="{esc(src)}" lang="ja">{t}</span>'


def callout(label, zh, body):
    return (f'<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label"><p><strong class="jp-original" '
            f'data-jp-original-source="{TM}: {label}" lang="ja">{label}</strong></p>{Z(zh)}</td>'
            f'<td class="manual-callout-body">{body}</td></tr></tbody></table>')


def figure(name, alt, caption):
    data = (FIG / f"{name}.png").read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    (OUT / "assets" / f"{sha}.png").write_bytes(data)
    REG["figures"].append({"reference_id": name, "asset": f"assets/{sha}.png", "sha256": sha,
                           "source": US + f" · figure[data-reference-id={name}]（Chromium 渲染截图，含美规标注）"})
    return (f'<figure class="us-review-figure" data-us-image-source="{esc(US)}#{name}"><img alt="{alt}" loading="eager" src="assets/{sha}.png"/>'
            f'<figcaption class="jp-review" lang="zh-CN">{caption}</figcaption></figure>')


PN = P("[PRODUCT NAME]")
CABLE = P("[Jackery 20A Fast Charging Cable / Jackery 30A Parallel/Fast Charging Cable — TBC]")
SRC_OUTAGE = "日规 Web 手册 JE-1000F／JE-1000E-WH：停電時には家庭用電源からポータブル電源の切り替え時間が10ミリ秒で行われます。"
SRC_LOOSE = "docs/templates/page_jp/charging.rst／JE-1000F：差し込みが不完全な場合、…支障をきたす恐れがあります。"
REF_PLUG = "AC充電ケーブルのプラグが製品のAC入力ポートにしっかりと、かつ完全に差し込まれていることを確認してください。（charging.rst，仅覆盖产品端）"

# ------------------------------------------------------------ UPS: 200V input subsection
ups_html = (
    '<section id="ups-200v-input" data-added="v0.19">'
    + NB("h2", "WITH 200V AC INPUT", "200V 交流输入时", kind="heading")
    + R("v0.19 按用户指示新增。依据美规 UPS「WITH 240V AC INPUT」按日规规格书改写：240V→200V，NEMA 14-50R→NEMA L14-30R，"
        "并补本机 NEMA 6-20（200V）；美规 40A 充电线改为日规选配线缆（20A 快充线或 30A 并机/快充线，待定）。上方日文模板正文对应 100V（AC 充电口）输入。"
        "各输出口的旁路上限规格书未列，保留玫红待填。", "版面依据：JHP-3600C US en · UPS · WITH 240V AC INPUT")
    + NB("p", f"Connect the product to a 200V AC power supply using a {CABLE} (sold separately). Press the AC power button to enable AC power delivery.",
         "使用【Jackery 20A 快充线／30A 并机快充线，待定】（需另购）将本产品连接到 200V 交流电源。按下交流电源按钮开启交流输出。")
    + NB("p", "All AC output ports support UPS operation under 200V input:", "200V 输入时，所有交流输出口均支持 UPS：")
    + "<ul>"
    + NB("li", f"NEMA L14-30R (100V/200V~): Up to {P('[TBC]')} bypass output", "NEMA L14-30R（100V/200V）：旁路输出最大【待填】")
    + NB("li", f"NEMA 6-20 (200V~): Up to {P('[TBC]')} bypass output", "NEMA 6-20（200V）：旁路输出最大【待填】")
    + NB("li", f"NEMA 5-20R ×2 (100V~): Up to {P('[TBC]')} per port, {P('[TBC]')} total bypass output", "NEMA 5-20R ×2（100V）：每口旁路输出最大【待填】，合计【待填】")
    + "</ul>"
    + NB("p", "The total bypass output through the AC Expansion Port is limited to 30A (6000W).", "经并机口（AC Expansion Port）的旁路输出总计最大 30A（6000W）。")
    + NB("p", "The maximum total load allowed is 4000 W for a single unit and 6000 W for dual units (cascade parallel connection).",
         "单机允许的最大总负载为 4000W，双机（级联并机）为 6000W。")
    + '<p lang="ja">' + J("停電時には家庭用電源からポータブル電源の切り替え時間が10ミリ秒で行われます。", SRC_OUTAGE)
    + N("When the battery is depleted, all AC outputs turn off.")
    + Z("停电时，家用电源切换到便携式电源的时间为 10 毫秒。电池电量耗尽时，所有交流输出关闭。") + "</p>"
    + figure("ups240", "200V 输入 UPS 连接",
             "审阅：美规原图（RTD 渲染截图）· 240V 输入 UPS。图中 NEMA 14-50 插座、40A 充电线、美式配电箱为美规；日规按 200V 插座、日规线缆与 L14-30R／6-20 输出重绘。")
    + R("数值依据：旁路 30A／6000W、单机 4000W、级联 6kW、UPS 10ms 均来自规格书；美规为 9600W／4800W 旁路、单机 4000W、双机 8000W、＜10 ms。"
        "规格书另注“主机逆变器只有 3.6kW”，与 4000W 口径待统一。")
    + "</section>")
ups = soup.find(id="uninterruptible-power-supply-ups")
ups.append(frag(ups_html))

# ------------------------------------------------------------ Charging: 200V AC input subsection
chg_html = (
    '<section id="charging-200v-input" data-added="v0.19">'
    + NB("h2", "CHARGING VIA 200V AC INPUT", "200V 交流输入充电", kind="heading")
    + R("v0.19 按用户指示新增。依据美规「CHARGING VIA 240V AC INPUT」按日规规格书改写：240V→200V，40A 充电线→日规选配线缆（待定）。"
        "规格书未给 200V 输入的充电功率；经 ATS 充电部分取决于 ATS 是否在日本销售（规格书选配含 ATS，外观为美式配电箱）。",
        "版面依据：JHP-3600C US en · CHARGING VIA 240V AC INPUT")
    + NB("p", f"{PN} supports charging through its 200V AC Expansion Port. Depending on your installation, the 200V AC input may come from "
              "a 200V AC outlet or from a Jackery Automatic Transfer Switch (ATS).",
         "本产品支持通过 200V 交流扩展口（AC Expansion Port，并机口）充电。视安装情况，200V 交流输入可来自 200V 插座或 Jackery 自动切换开关（ATS）。")
    + NB("h3", "200V AC Outlet", "200V 交流插座", kind="heading")
    + figure("charge240", "200V 插座充电",
             "审阅：美规原图（RTD 渲染截图）· 240V 插座充电。图中 NEMA 14-50 插头插座、40A 充电线及图内英文说明为美规；日规按 200V 插座与日规线缆重绘。")
    + NB("p", f"Connect the product to a 200V AC power supply using a {CABLE} (Sold Separately).",
         "使用【Jackery 20A 快充线／30A 并机快充线，待定】（需另购）将本产品连接到 200V 交流电源。")
    + callout("注意", "注意",
              "<ul>"
              + NB("li", f"Ensure the {CABLE} is fully and securely plugged into both the 200V outlet and the AC Expansion Port.",
                   "确保充电线已牢固、完全地插入 200V 插座和产品的并机口（AC Expansion Port）。", ref=REF_PLUG)
              + f'<li class="jp-original" data-jp-original-source="{esc(SRC_LOOSE)}" lang="ja">差し込みが不完全な場合、電流の不安定、発熱、接触不良などが発生し、'
                f'機器の正常な動作に支障をきたす恐れがあります。{Z("插入不完全可能导致电流不稳定、发热、接触不良等，影响设备正常运行。")}</li>'
              + "</ul>")
    + NB("h3", "TRANSFER SWITCH (ATS)", "切换开关（ATS）", kind="heading")
    + NB("p", "Connect your Jackery ATS to the product to enable charging via the Transfer Switch.", "将 Jackery ATS 连接到本产品，即可经切换开关充电。")
    + callout("説明", "说明",
              NB("p", f"The backup reserve setting applies in all operating modes of the ATS. When the remaining capacity of {PN} exceeds the "
                      "configured backup reserve, charging will stop automatically.",
                 "备用电量设置适用于 ATS 的所有运行模式。本产品剩余电量超过所设备用电量时，充电自动停止。")
              + NB("p", "To charge it immediately, follow the instructions below:", "如需立即充电，请按以下步骤操作：")
              + "<ol>"
              + NB("li", "Tap Power Station in the energy flow of the ATS dashboard.", "在 ATS 仪表盘的能量流中点击 Power Station。")
              + NB("li", "On the Power Station page, tap Charge now.", "在 Power Station 页面点击 Charge now。")
              + "</ol>")
    + callout("説明", "说明",
              NB("p", f"Once the AC Expansion Port is successfully connected to an ATS, the AC Input port will no longer be used for charging. "
                      f"In this configuration, {PN} can be charged through the following ports:",
                 "并机口（AC Expansion Port）成功连接 ATS 后，AC 输入口不再用于充电。此时本产品可通过以下接口充电：")
              + "<ul>" + NB("li", "AC Expansion Port", "并机口（AC Expansion Port）", kind="term")
              + f'<li class="jp-original" data-jp-original-source="{esc(TM)}／JE-1000F 規格「2×DC8020ポート」" lang="ja">DC8020ポート{Z("DC8020 接口")}</li></ul>')
    + R("美规原文“energe flow”为拼写错误，英文稿已改为 energy flow。ATS 仪表盘按钮名（Power Station、Charge now）以日规 App 界面为准。")
    + "</section>")
charging = soup.find(id="charging")
emerg = [h for h in charging.find_all("h2") if h.get_text(strip=True).startswith("緊急充電モード")][0]
anchor = emerg.find_parent("section") if emerg.find_parent("section") is not charging else emerg
anchor.insert_before(frag(chg_html))

# ------------------------------------------------------------ labels
soup.find("header").find("small").string = "本地审阅 · v0.19 · 日规 Web 手册样式 · 新增 200V 输入 UPS／充电"
soup.title.string = "JHP-3600C · 日规说明书审核稿 v0.19"
soup.find(class_="draft-banner").find("strong").string = "v0.19 · 新增 200V 输入 UPS 与 200V 充电小节 · 黑＝日文 · 绿＝待翻译英文 · 蓝＝中文"
soup.find(class_="manual-locale-current").string = "日本語（审核稿 v0.19）"
cl = soup.find(class_="change-log")
cl.find("summary").insert_after(frag(
    "<p><strong>v0.19（2026-10-12）</strong> — 按用户指示新增「UPS：WITH 200V AC INPUT」与「CHARGING VIA 200V AC INPUT」（200V 插座、经 ATS 充电），"
    "依据美规 240V 小节按日规规格书改写；美规附录（AC ESS、BP3600、ATS 规格）暂不加入。</p>"))

HTML.write_text(str(soup), encoding="utf-8")
(OUT / "jp-200v-register.json").write_text(json.dumps(REG, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", len(REG["figures"]))
