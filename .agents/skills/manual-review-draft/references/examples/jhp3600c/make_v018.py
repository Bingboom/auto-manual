"""v0.18: restyle the review draft in the published JP web-manual style (JE-1000F JP on RTD).

Usage: python3 -I make_v018.py <v017_dir> <jpstyle_dir> <out_dir>
"""
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag

SRC, STY, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(SRC, OUT)
for stale in OUT.glob("JHP-3600C-JP-*.zip"):
    stale.unlink()
HTML = OUT / "manual_jhp3600c_jp_en_draft.html"
soup = BeautifulSoup(HTML.read_text(encoding="utf-8"), "html.parser")
REF = "https://ht-doc.readthedocs.io/JE-1000F/JP/ja/md/manual_je1000f_jp.html"
ALERT = ('<svg aria-hidden="true" class="jp-alert-icon" viewBox="0 0 48 44"><path d="M20 3 Q24 -3 28 3 L47 37 Q50 43 43 43 H5 '
         'Q-2 43 1 37 Z" fill="currentColor"></path><path d="M24 12 V26" stroke="white" stroke-linecap="round" stroke-width="5">'
         '</path><circle cx="24" cy="35" fill="white" r="2.7"></circle></svg>')


def frag(h):
    return BeautifulSoup(h, "html.parser")


def kids(el):
    return [c for c in el.children if isinstance(c, Tag)]


def zh_of(el):
    z = el.find(class_="zh-translation", recursive=False)
    return z.extract() if z is not None else None


# ------------------------------------------------------------ stylesheets
(OUT / "assets" / "jp-style").mkdir(exist_ok=True)
inline = (STY / "je1000f_inline.css").read_text(encoding="utf-8")
inline = "\n".join(b for b in inline.split("/* ---- */") if "--color-code-background" not in b)
(OUT / "assets" / "jp-style" / "jp-manual-components.css").write_text(
    f"/* JP web-manual component styles, copied from the published JE-1000F JP manual: {REF} */\n" + inline, encoding="utf-8")
shutil.copy(STY / "css" / "manual-locales.css", OUT / "assets" / "jp-style" / "manual-locales.css")
for st in soup.head.find_all("style"):
    st.decompose()
link = soup.head.find("link", href="assets/source-manual.css")
link.insert_after(frag('<link href="assets/jp-style/jp-manual-components.css" rel="stylesheet"/>'
                       '<link href="assets/jp-style/manual-locales.css" rel="stylesheet"/>'
                       '<link href="assets/jp-style/review-overlay.css" rel="stylesheet"/>'))

# ------------------------------------------------------------ generic: nest h2 runs into sections
def nest_h2(container):
    cur = None
    for c in list(container.children):
        if isinstance(c, Tag) and c.name == "h2":
            cur = soup.new_tag("section")
            c.insert_before(cur)
            cur.append(c.extract())
        elif isinstance(c, Tag) and c.name == "section":
            cur = None
        elif cur is not None:
            cur.append(c.extract())


main = soup.find(id="furo-main-content")

# ------------------------------------------------------------ safety chapter (JE-1000F layout)
saf = soup.find(id="important-safety-information")
sd = saf.find("div", class_="jp-change", recursive=False)
lead = sd.find("p", recursive=False)
lead["class"] = (lead.get("class") or []) + ["jp-safety-lead"]
h2s = sd.find_all("h2", recursive=False)
about, warn, urgent, caution, usage = h2s[0], h2s[1], h2s[2], h2s[3], h2s[4]
about["class"] = (about.get("class") or []) + ["jp-safety-band"]

# signal-word table -> jp-signal-table
sig_wrap = about.find_next_sibling("div", class_="jp-table-scroll")
rows = []
for tr in sig_wrap.find("tbody").find_all("tr"):
    th, td = tr.find_all(["td", "th"])[:2]
    label_zh = zh_of(th)
    label = th.get_text(strip=True)
    icon = ALERT if label in ("警告", "注意") else ""
    rows.append(f'<tr><th scope="row"><p>{icon}<strong>{label}</strong></p>{label_zh or ""}</th><td>{td.decode_contents()}</td></tr>')
sig_wrap.replace_with(frag(f'<div class="jp-signal-wrap"><table class="jp-signal-table"><tbody>{"".join(rows)}</tbody></table></div>'))

# meaning of symbols chapter -> h2 band + symbol panels inside safety
ms = soup.find(id="meaning-of-symbols")
ms_h1 = ms.find("h1")
ms_reviews = [r.extract() for r in ms.select(".jp-review")]
sym_rows, recycle_rows = [], []
for tr in ms.find("tbody").find_all("tr"):
    tds = tr.find_all("td")
    img = tds[0].find("img")
    name, meaning = tds[1], tds[2]
    body = ""
    nz, mz = zh_of(name), zh_of(meaning)
    name_txt, mean_txt = name.get_text("", strip=True), meaning.get_text("", strip=True)
    if "jp-li_ion" in img["src"] or "jp-battery_recycle" in img["src"]:
        body = f'<p><strong>{name.decode_contents()}</strong></p>{nz or ""}<p>{meaning.decode_contents()}</p>{mz or ""}'
        recycle_rows.append(f'<tr><td>{img}</td><td>{body}</td></tr>')
        continue
    if name_txt and name_txt not in mean_txt and not name_txt.startswith("警告"):
        body = f'<p>{name.decode_contents()}</p>{nz or ""}'
    body += f'<p>{meaning.decode_contents()}</p>{mz or ""}'
    sym_rows.append(f'<tr><td>{img}</td><td>{body}</td></tr>')
half = (len(sym_rows) + 1) // 2
h1_zh = zh_of(ms_h1)
sym_html = (
    f'<section id="meaning-of-symbols"><h2 class="jp-original jp-safety-band" lang="ja" '
    f'data-jp-original-source="{ms_h1.get("data-jp-original-source", "")}">{ms_h1.get_text(strip=True)}{h1_zh or ""}</h2>'
    f'<div class="jp-symbol-grid"><table class="jp-symbol-panel"><tbody>{"".join(sym_rows[:half])}</tbody></table>'
    f'<table class="jp-symbol-panel"><tbody>{"".join(sym_rows[half:])}</tbody></table></div>'
    + ('<div class="jp-symbol-grid jp-recycling-grid" id="jp-recycling">'
       + "".join(f'<table class="jp-symbol-panel"><tbody>{r}</tbody></table>' for r in recycle_rows) + "</div>" if recycle_rows else "")
    + "".join(str(r) for r in ms_reviews) + "</section>")
ms.decompose()
warn.insert_before(frag(sym_html))

# 警告: heading + two panels of cards
def card_rows(grid):
    out = []
    for card in grid.select(".jp-safety-card"):
        img = card.find("img")
        body = card.find("div")
        parts = []
        for c in kids(body):
            if c.name == "strong":
                c.name = "p"
            parts.append(str(c))
        out.append(f'<tr><td>{img}</td><td class="jp-safety-copy">{"".join(parts)}</td></tr>')
    return out


warn_zh = zh_of(warn)
warn.attrs["class"] = (warn.get("class") or []) + ["jp-warning-heading"]
warn.clear()
warn.append(frag(ALERT + "警告"))
if warn_zh:
    warn.append(warn_zh)
grid1 = warn.find_next_sibling("div", class_="jp-safety-grid")
r1 = card_rows(grid1)
h = (len(r1) + 1) // 2
grid1.replace_with(frag(f'<div class="jp-symbol-grid jp-warning-grid"><table class="jp-symbol-panel"><tbody>{"".join(r1[:h])}</tbody></table>'
                        f'<table class="jp-symbol-panel"><tbody>{"".join(r1[h:])}</tbody></table></div>'))

# 万が一…: second 警告 heading + detail table
urgent_text = urgent.decode_contents()
panel = urgent.find_next_sibling("div", class_="jp-warning-panel")
grid2 = urgent.find_next_sibling("div", class_="jp-safety-grid")
pimg = panel.find("img")
ps = panel.find("div").find_all("p", recursive=False)
first = ps[0]
fz = zh_of(first)
items = [t.strip() for t in first.get_text("", strip=True).split("／") if t.strip()]
emergency = (f'<div class="jp-safety-cell-section"><p class="jp-original" lang="ja">{urgent_text}</p>'
             f'<ul class="jp-emergency-list">' + "".join(f'<li><p class="jp-original" lang="ja">{t}</p></li>' for t in items)
             + f'</ul>{fz or ""}</div>'
             + "".join(f'<div class="jp-safety-cell-section">{p}</div>' for p in ps[1:]))
detail_rows = [f'<tr><td>{pimg}</td><td class="jp-safety-copy jp-safety-split">{emergency}</td></tr>'] + card_rows(grid2)
urgent_new = frag(f'<h2 class="jp-warning-heading">{ALERT}警告</h2>'
                  f'<table class="jp-symbol-panel jp-safety-detail"><tbody>{"".join(detail_rows)}</tbody></table>')
panel.decompose()
grid2.decompose()
urgent.replace_with(urgent_new)

# 注意: list -> detail table with prohibition icon
cz = zh_of(caution)
caution["class"] = (caution.get("class") or []) + ["jp-warning-heading"]
caution.clear()
caution.append(frag(ALERT + "注意"))
if cz:
    caution.append(cz)
ul = caution.find_next_sibling("ul")
crow = "".join(f'<tr><td><img alt="Prohibited action symbol." class="jp-symbol" src="assets/jp-prohibited.png"/></td>'
               f'<td class="jp-safety-copy"><p class="jp-original" lang="ja">{li.decode_contents()}</p></td></tr>' for li in ul.find_all("li"))
ul.replace_with(frag(f'<table class="jp-symbol-panel jp-safety-detail"><tbody>{crow}</tbody></table>'))

# 使用上のご注意: dark heading + grey intro
usage["class"] = (usage.get("class") or []) + ["jp-usage-heading"]
intro = usage.find_next_sibling("p")
if intro is not None:
    box = soup.new_tag("div", attrs={"class": "jp-usage-intro"})
    intro.insert_before(box)
    box.append(intro.extract())

# ------------------------------------------------------------ box (同梱品)
box = soup.find(id="what-s-in-the-box")
bd = box.find("div", class_="jp-change", recursive=False)
grid = bd.find("div", class_="jp-box-grid")
cards, moved = [], []
for i, c in enumerate(kids(grid), 1):
    img = c.find("img")
    name = c.find("strong")
    for cap in c.select("figcaption"):
        moved.append(f'<div class="jp-review" lang="zh-CN">{cap.decode_contents()}</div>')
    nz = zh_of(name)
    cards.append(f'<figure class="jp-inbox-card"><span class="jp-inbox-number">{i}</span><div class="jp-inbox-art">{img}</div>'
                 f'<figcaption><span class="jp-original" lang="ja" data-jp-original-source="{name.get("data-jp-original-source", "")}">'
                 f'{name.get_text(strip=True)}</span>{nz or ""}</figcaption></figure>')
grid.replace_with(frag(f'<div class="jp-inbox-grid">{"".join(cards)}</div>' + "".join(moved)))
notes = bd.find("ul", recursive=False)
notes.replace_with(frag('<div class="jp-inbox-notes">' + "".join(f'<p class="jp-original" lang="ja">{li.decode_contents()}</p>' for li in notes.find_all("li")) + "</div>"))
disc = bd.find("p", recursive=False, string=None)
for p in bd.find_all("p", recursive=False):
    if "予告なく変更" in p.get_text():
        z = zh_of(p)
        p["class"] = ["jp-original", "jp-inbox-disclaimer"]
        txt = p.get_text(strip=True)
        p.clear()
        p.append(frag(f"■ <strong>{txt}</strong>"))
        if z:
            p.append(z)

# ------------------------------------------------------------ specifications (grouped cards)
spec = soup.find(id="specifications")
sdiv = spec.find("div", class_="jp-change", recursive=False)
tbl_wrap = sdiv.find("div", class_="jp-table-scroll")
groups = [["基本情報", "基本信息", []], ["入力ポート", "输入接口", []], ["出力ポート", "输出接口", []], ["温度範囲", "温度范围", []]]
cur = 0
cert_value = None
for tr in tbl_wrap.find("tbody").find_all("tr", recursive=False):
    th = tr.find("th")
    if th is not None and th.get("colspan"):
        cur = 1 if "入力" in th.get_text() else 2
        continue
    tds = tr.find_all("td", recursive=False)
    label_txt = tds[0].get_text(" ", strip=True)
    if label_txt.startswith("Certification"):
        cert_value = tds[1]
        continue
    target = cur
    if any(k in label_txt for k in ("バッテリーパック", "Cascade", "騒音")):
        target = 0
    if any(k in label_txt for k in ("温度", "Altitude")):
        target = 3
    lab, val = tds
    lab.name = "th"
    lab["scope"] = "row"
    lab["class"] = (lab.get("class") or []) + ["hb-spec-label", "manual-spec-label"]
    val["class"] = (val.get("class") or []) + ["hb-spec-value", "manual-spec-value"]
    groups[target][2].append(str(tr))
spec_html = ""
for jp, zh, rws in groups:
    spec_html += (f'<section><h2 class="jp-original" lang="ja" data-jp-original-source="{REF}">{jp}'
                  f'<span class="zh-translation" lang="zh-CN">{zh}</span></h2><figure class="hb-spec-table-composition">'
                  f'<table class="hb-spec-table manual-table manual-spec-table"><colgroup><col class="hb-spec-col-label"/>'
                  f'<col class="hb-spec-col-value"/></colgroup><tbody>{"".join(rws)}</tbody></table></figure></section>')
cert = ""
if cert_value is not None:
    cz = cert_value.find(class_="zh-translation")
    cert = (f'<p class="jp-original" lang="ja" data-jp-original-source="{REF}「認証：」">認証：'
            f'<span class="us-difference jp-parameter">【未入力】</span>'
            f'<span class="zh-translation" lang="zh-CN">认证：【待填】（PSE 等标识及编号）</span></p>')
tbl_wrap.replace_with(frag(spec_html + cert))

# ------------------------------------------------------------ warranty cards
war = soup.find(id="warranty")
h1 = war.find("h1")
intro_ps = []
for c in list(h1.find_next_siblings()):
    if c.name == "h2":
        break
    if c.name == "p":
        intro_ps.append(c)
if intro_ps:
    fig = soup.new_tag("figure", attrs={"class": "hb-warranty-intro-composition"})
    intro_ps[0].insert_before(fig)
    panel = soup.new_tag("div", attrs={"class": "hb-warranty-intro-panel"})
    fig.append(panel)
    for p in intro_ps[:-1]:
        panel.append(p.extract())
    note = soup.new_tag("div", attrs={"class": "hb-warranty-local-note"})
    fig.append(note)
    note.append(intro_ps[-1].extract())
nest_h2(war)
for sec in war.find_all("section", recursive=False):
    h2 = sec.find("h2", recursive=False)
    rest = [c for c in list(sec.children) if c is not h2]
    fig = soup.new_tag("figure", attrs={"class": "hb-warranty-card"})
    h2.insert_after(fig)
    for c in rest:
        fig.append(c.extract())

# ------------------------------------------------------------ generic sections, tables, callouts
for sec in main.find_all("section", recursive=False):
    if sec.get("id") in ("warranty", "jp-review-appendix"):
        continue
    inner = sec.find("div", class_="jp-change", recursive=False) or sec
    nest_h2(inner)

for call in main.select("div.jp-callout"):
    label = call.find("strong", recursive=False)
    body = [c for c in list(call.children) if c is not label]
    lz = zh_of(label)
    label_attrs = " ".join(f'{k}="{v if isinstance(v, str) else " ".join(v)}"' for k, v in label.attrs.items())
    tbl = frag(f'<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label"><p><strong {label_attrs}>'
               f'{label.get_text(strip=True)}</strong></p>{lz or ""}</td><td class="manual-callout-body"></td></tr></tbody></table>')
    bodycell = tbl.find("td", class_="manual-callout-body")
    for c in body:
        bodycell.append(c.extract())
    call.replace_with(tbl)

for t in main.select("table.jp-table"):
    t["class"] = [c for c in t["class"] if c != "jp-table"] + ["hb-spec-table", "manual-table", "jp-grid-table"]
    wrap = t.find_parent("div", class_="jp-table-scroll")
    if wrap is not None:
        wrap["class"] = ["hb-spec-table-composition", "jp-grid-composition"]
    for th in t.select("thead th"):
        th["class"] = (th.get("class") or []) + ["hb-spec-label"]

# locale card + reference note at the top of the manual body
main.insert(0, frag('<nav aria-label="Manual language" class="manual-locale-nav"><span>JHP-3600C · JP</span>'
                    '<span class="manual-locale-current">日本語（审核稿 v0.18）</span></nav>'))

# ------------------------------------------------------------ toolbar: add 中文对照 toggle
acts = soup.find(class_="toolbar-actions")
acts.find(id="notes").insert_after(frag('<button aria-pressed="true" id="zh">中文对照已显示</button>'))
script = soup.find("script")
script.string = script.string + (";const zh=document.getElementById('zh');zh.addEventListener('click',()=>{const h=document.body.classList.toggle('hide-zh');"
                                 "zh.setAttribute('aria-pressed',String(!h));zh.textContent=h?'显示中文对照':'中文对照已显示'});")
for a in soup.select('aside.toc a[href="#meaning-of-symbols"]'):
    a.string = "符号说明（安全章内）"
soup.find("header").find("small").string = "本地审阅 · v0.18 · 日规 Web 手册样式（参照 JE-1000F JP）"
soup.title.string = "JHP-3600C · 日规说明书审核稿 v0.18"
banner = soup.find(class_="draft-banner")
banner.find("strong").string = "v0.18 · 版式按日规 Web 手册（JE-1000F JP）统一 · 黑＝日文 · 绿＝待翻译英文 · 蓝＝中文"
cl = soup.find(class_="change-log")
cl.find("summary").insert_after(frag(
    f'<p><strong>v0.18（2026-10-12）</strong> — 样式按已发布日规 Web 手册（<a href="{REF}">JE-1000F JP</a>）统一：章节黑色标题条、'
    "安全章信号词表／绘表示面板／警告与注意面板、同梱品编号卡片、规格分组表、保修卡片、警示框；「絵表示の説明」并入安全章；"
    "规格表「認証」改用现成日文标签；新增“隐藏中文对照”开关以查看纯日文版面。</p>"))

HTML.write_text(str(soup), encoding="utf-8")
print("ok")
