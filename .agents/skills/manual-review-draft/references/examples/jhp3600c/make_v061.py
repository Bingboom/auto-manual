"""v0.61 (operator 2026-10-20: 按研发的说法 适配修改): 「2台を並列接続してMTSに接続する」 follows R&D's answer.

R&D: no port outputs 6000W on its own; 6000W is the total of all output ports. This section feeds the MTS through the
second unit's one NEMA L14-30R (A0: 100V/200V, 20A, 4000W), so the MTS gets at most 4000W and the system total over
all ports is 6000W. The intro no longer says cascading gives the MTS more output.

  python3 -I make_v061.py <v060_dir> <v061_dir>
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


def PU(text: str, ref: str, prev: str) -> str:
    return (f'<span class="jp-spec-updated" data-previous-value="{prev}" data-spec-ref="{ref}" data-spec-source="研发答复 2026-10-20" '
            f'lang="ja" title="研发答复更新：{ref}（原：{prev}）">{text}</span>')


R_PORT = "A0：NEMA L14-30R 100V/200V，20A，4000W；研发 2026-10-20：没有可单独输出 6000W 的接口"
R_TOTAL = "研发 2026-10-20：所有输出口合计 6000W"

rep("2台を並列接続すると、システムはより大きな出力をMTSに供給できます。"
    '<span class="zh-translation" lang="zh-CN">两台设备以级联并机方式连接时，系统可向 MTS 提供更高的输出功率。</span>',
    "2台を並列接続すると、システム全体の総出力を高めることができます。"
    '<span class="zh-translation" lang="zh-CN">两台设备级联并机时，可提高系统总输出功率。</span>')
rep("並列接続後、MTSへの最大出力は6000Wです。合計負荷が総出力を絶対に超えないようにしてください。"
    '<span class="zh-translation" lang="zh-CN">级联后，输出至 MTS 的最大功率为 6000W。总负载不得超过总功率。</span>',
    f"並列接続後、MTSへの出力は2台目のNEMA L14-30R 1ポート分で、最大{PU('4000W', R_PORT, '6000W')}です。"
    f"システム総出力はすべての出力ポートの合計で{PU('6000W', R_TOTAL, '（无）')}です。"
    "合計負荷が総出力を絶対に超えないようにしてください。"
    '<span class="zh-translation" lang="zh-CN">级联后，输出至 MTS 的只有第二台的一个 NEMA L14-30R，最大 4000W；系统总输出为所有输出口合计 6000W。'
    "总负载不得超过总功率。</span>")
rep("「MTSへの最大出力は6000W」与此矛盾，需再问研发（是否应为 4000W，或接法不同）。文字暂未改。",
    "「MTSへの最大出力は6000W」与此矛盾。v0.61 按用户指示按研发说法适配：开头句改为「システム全体の総出力を高めることができます」"
    "（不再说向 MTS 提供更大输出）；注意框改为 MTS 经第二台一个 NEMA L14-30R，最大 4000W（规格书该口上限），系统总输出为所有输出口合计 6000W（紫色）。"
    "美规此处为 8000W（经第二台 NEMA 14-50R），日规不照搬。")

CHG = ("按研发说法（没有可单独输出 6000W 的接口，所有输出口合计 6000W）适配「2台を並列接続してMTSに接続する」：开头句改为「システム全体の総出力を高めることができます」；"
       "注意框改为「MTSへの出力は2台目のNEMA L14-30R 1ポート分で、最大4000W」＋「システム総出力はすべての出力ポートの合計で6000W」（紫色；4000W 为规格书 L14-30R 上限）。")
for old, new in (
    ("<title>JHP-3600C · 日规说明书审核稿 v0.60</title>", "<title>JHP-3600C · 日规说明书审核稿 v0.61</title>"),
    ("<small>本地审阅 · v0.60 · 级联 6000W 与切换时间（研发答复）</small>", "<small>本地审阅 · v0.61 · 级联接 MTS 按研发说法适配</small>"),
    ("<strong>v0.60 · 级联 6000W 与切换时间（研发答复） · ", "<strong>v0.61 · 级联接 MTS 按研发说法适配 · v0.60 级联 6000W 与切换时间（研发答复） · "),
    ('<span class="manual-locale-current">日本語（审核稿 v0.60）</span>', '<span class="manual-locale-current">日本語（审核稿 v0.61）</span>'),
    ('<p class="print-note">JHP-3600C v0.60；', '<p class="print-note">JHP-3600C v0.61；'),
    ("<summary>本次改写记录与日文版面依据</summary>",
     "<summary>本次改写记录与日文版面依据</summary><p><strong>v0.61（2026-10-20）</strong> — " + CHG + "</p>"),
):
    rep(old, new)
P.write_text(h, encoding="utf-8")

sec_md = "## v0.61 级联接 MTS 按研发说法适配\n\n" + CHG + "\n\n"
for nm in ("README.md", "review.zh.md"):
    path = DST / nm
    t = path.read_text(encoding="utf-8")
    if nm == "README.md":
        assert "# JHP-3600C 日规说明书审核稿 v0.60" in t
        t = t.replace("# JHP-3600C 日规说明书审核稿 v0.60", "# JHP-3600C 日规说明书审核稿 v0.61", 1)
        head, rest = t.split("\n## ", 1)
        t = head + "\n" + sec_md + "## " + rest
    else:
        t = sec_md + t
    path.write_text(t, encoding="utf-8")
print("ok")
