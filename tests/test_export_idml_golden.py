#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden-output regression net for the IDML exporter (componentization P0).

Builds the .idml package through the real CLI (``tools/export_idml.py``) from
committed fixtures and compares every zip part byte-for-byte against a
committed golden snapshot. The ``composed`` variant uses the synthetic bundle in
  ``tests/fixtures/idml_bundle``: prose stories, the safety twocol split, the
  safety+symbols merged page, the fcc+inbox merged page, components
  (safetywarning / warninglead / warnbox / notice / fcc / inbox / lcdmode),
  list-tables, and bold runs — i.e. the whole main() composition state machine.
The Japanese and Korean variants localize representative prose, component,
table, and semantic data-page content before export so future CJK run-routing
changes have a real byte-level baseline rather than an English-only alias.

Normalization: absolute ``file://`` image-link URIs are machine-dependent, so
the repo-root URI prefix is replaced with a placeholder before comparing.

Regenerating the golden (ONLY for an intentional output change — never to make
a refactor pass; during the componentization phases a golden diff means the
refactor changed behavior and must be fixed, not re-baselined):

    python tests/test_export_idml_golden.py --regenerate

then review the fixture diff like any other code change.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "fixtures" / "idml_golden"
BUNDLE_FIXTURE = ROOT / "tests" / "fixtures" / "idml_bundle"
DATA_FIXTURE = ROOT / "tests" / "fixtures" / "phase2"
ROOT_URI = ROOT.resolve().as_uri()
URI_PLACEHOLDER = "file://IDML-GOLDEN-ROOT"

VARIANTS: dict[str, dict] = {
    "composed": {"bundle_root": BUNDLE_FIXTURE, "lang": "en"},
    "composed_fr": {"bundle_root": BUNDLE_FIXTURE, "lang": "fr"},
    "composed_ja": {"bundle_root": BUNDLE_FIXTURE, "lang": "ja"},
    "composed_ko": {"bundle_root": BUNDLE_FIXTURE, "lang": "ko"},
}

CJK_SENTINELS = {
    "composed_ja": ("日本語の取扱説明書", "記号の意味", "入力ポート"),
    "composed_ko": ("한국어 사용 설명서", "기호의 의미", "입력 포트"),
}

_CJK_FIXTURE_REPLACEMENTS: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "ja": {
        "00_preface.rst": (
            (r"\section{PREFACE}", r"\section{日本語の取扱説明書}"),
            (
                "Thank you for choosing the Jackery Explorer 1000 v2 portable power station.",
                "Jackery Explorer 1000 v2 ポータブル電源をお選びいただき、ありがとうございます。",
            ),
            (
                "Please read this manual **carefully** before use and keep it for future reference.",
                "ご使用前に本書を**よくお読み**になり、いつでも参照できるよう保管してください。",
            ),
        ),
        "05_operation_guide.rst": (
            (r"\section{OPERATION GUIDE}", r"\section{操作ガイド}"),
            ("BUTTONS & KEY COMBINATIONS", "ボタンとキーの組み合わせ"),
            ("Press the DISPLAY button to wake the screen.", "DISPLAYボタンを押すと画面が点灯します。"),
            ("Button", "ボタン"),
            ("Short Press", "短押し"),
            ("Long Press", "長押し"),
        ),
        "safety_en.rst": (
            (r"\section{IMPORTANT SAFETY INFORMATION}", r"\section{安全上の重要な注意事項}"),
            ("{WARNING}", "{警告}"),
            (
                "Always follow these basic precautions when using this product.",
                "本製品を使用するときは、必ず基本的な注意事項を守ってください。",
            ),
        ),
        "20_01_user_maintenance_instructions.rst": (
            (
                r"\section{USER MAINTENANCE INSTRUCTIONS}",
                r"\section{ユーザーメンテナンス手順}",
            ),
            (
                "During the lifecycle of energy storage products, always keep the unit dry and store it in a cool, ventilated place.",
                "蓄電製品の使用期間中は、本体を乾燥した状態に保ち、涼しく換気のよい場所に保管してください。",
            ),
        ),
        "symbols_en.rst": (
            ("MEANING OF SYMBOLS", "記号の意味"),
            ('"Symbol"', '"記号"'),
            ('"Meaning"', '"意味"'),
            ('"label":"WARNING"', '"label":"警告"'),
            (
                "Hazardous practices that may result in severe injury, death, and/or property damage.",
                "重傷、死亡、または物的損害につながるおそれのある危険な行為。",
            ),
        ),
        "lcd_icons_en.rst": (
            ('"name":"Wi-Fi"', '"name":"Wi-Fi接続"'),
            ("On: Wi-Fi connected.", "オン：Wi-Fiに接続されています。"),
        ),
        "troubleshooting_en.rst": (
            ("Restart the product.", "製品を再起動してください。"),
        ),
        "spec_en.rst": (
            ('"title":"SPECIFICATIONS"', '"title":"仕様"'),
            ('"title":"GENERAL INFO"', '"title":"一般情報"'),
            ('"title":"INPUT PORTS"', '"title":"入力ポート"'),
            ('"Product Name"', '"製品名"'),
        ),
    },
    "ko": {
        "00_preface.rst": (
            (r"\section{PREFACE}", r"\section{한국어 사용 설명서}"),
            (
                "Thank you for choosing the Jackery Explorer 1000 v2 portable power station.",
                "Jackery Explorer 1000 v2 휴대용 파워 스테이션을 선택해 주셔서 감사합니다.",
            ),
            (
                "Please read this manual **carefully** before use and keep it for future reference.",
                "사용하기 전에 이 설명서를 **주의 깊게 읽고** 나중에 참조할 수 있도록 보관하십시오.",
            ),
        ),
        "05_operation_guide.rst": (
            (r"\section{OPERATION GUIDE}", r"\section{작동 안내}"),
            ("BUTTONS & KEY COMBINATIONS", "버튼 및 키 조합"),
            ("Press the DISPLAY button to wake the screen.", "DISPLAY 버튼을 누르면 화면이 켜집니다."),
            ("Button", "버튼"),
            ("Short Press", "짧게 누르기"),
            ("Long Press", "길게 누르기"),
        ),
        "safety_en.rst": (
            (r"\section{IMPORTANT SAFETY INFORMATION}", r"\section{중요 안전 정보}"),
            ("{WARNING}", "{경고}"),
            (
                "Always follow these basic precautions when using this product.",
                "이 제품을 사용할 때는 다음 기본 안전 수칙을 반드시 준수하십시오.",
            ),
        ),
        "20_01_user_maintenance_instructions.rst": (
            (
                r"\section{USER MAINTENANCE INSTRUCTIONS}",
                r"\section{사용자 유지 관리 지침}",
            ),
            (
                "During the lifecycle of energy storage products, always keep the unit dry and store it in a cool, ventilated place.",
                "에너지 저장 제품을 사용하는 동안 본체를 건조하게 유지하고 서늘하고 환기가 잘되는 곳에 보관하십시오.",
            ),
        ),
        "symbols_en.rst": (
            ("MEANING OF SYMBOLS", "기호의 의미"),
            ('"Symbol"', '"기호"'),
            ('"Meaning"', '"의미"'),
            ('"label":"WARNING"', '"label":"경고"'),
            (
                "Hazardous practices that may result in severe injury, death, and/or property damage.",
                "심각한 부상, 사망 또는 재산 피해를 초래할 수 있는 위험한 행동입니다.",
            ),
        ),
        "lcd_icons_en.rst": (
            ('"name":"Wi-Fi"', '"name":"Wi-Fi 연결"'),
            ("On: Wi-Fi connected.", "켜짐: Wi-Fi에 연결되었습니다."),
        ),
        "troubleshooting_en.rst": (
            ("Restart the product.", "제품을 다시 시작하십시오."),
        ),
        "spec_en.rst": (
            ('"title":"SPECIFICATIONS"', '"title":"사양"'),
            ('"title":"GENERAL INFO"', '"title":"일반 정보"'),
            ('"title":"INPUT PORTS"', '"title":"입력 포트"'),
            ('"Product Name"', '"제품명"'),
        ),
    },
}


def _build_package(
    bundle_root: Path, out_path: Path, *, lang: str,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "export_idml.py"),
        "--model", "JE-1000F",
        "--region", "US",
        "--lang", lang,
        "--data-root", str(DATA_FIXTURE),
        "--bundle-root", str(bundle_root),
        "--out", str(out_path),
    ]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def _normalized_parts(idml_path: Path) -> dict[str, bytes]:
    parts: dict[str, bytes] = {}
    with zipfile.ZipFile(idml_path) as zf:
        for name in zf.namelist():
            text = zf.read(name).decode("utf-8")
            parts[name] = text.replace(ROOT_URI, URI_PLACEHOLDER).encode("utf-8")
    return parts


def _golden_parts(variant: str) -> dict[str, bytes]:
    base = GOLDEN_ROOT / variant
    return {
        p.relative_to(base).as_posix(): p.read_bytes()
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


def _write_golden(variant: str, parts: dict[str, bytes]) -> None:
    base = GOLDEN_ROOT / variant
    if base.exists():
        for p in sorted(base.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
    for name, data in parts.items():
        dest = base / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


def _replace_required(text: str, replacements: tuple[tuple[str, str], ...], *, page: Path) -> str:
    for source, target in replacements:
        if source not in text:
            raise AssertionError(f"localized golden fixture source missing in {page.name}: {source}")
        text = text.replace(source, target)
    return text


def _localize_cjk_bundle(bundle_root: Path, lang: str) -> None:
    replacements_by_page = _CJK_FIXTURE_REPLACEMENTS[lang]
    page_root = bundle_root / "page"
    for page_name, replacements in replacements_by_page.items():
        page = page_root / page_name
        text = page.read_text(encoding="utf-8")
        page.write_text(
            _replace_required(text, replacements, page=page),
            encoding="utf-8",
        )

    index = bundle_root / "index.rst"
    index_text = index.read_text(encoding="utf-8")
    for page in sorted(page_root.glob("*_en.rst")):
        localized = page.with_name(f"{page.stem.removesuffix('_en')}_{lang}.rst")
        index_text = index_text.replace(page.name, localized.name)
        page.rename(localized)
    index.write_text(index_text, encoding="utf-8")


def _bundle_for_variant(variant: str, temp_root: Path) -> tuple[Path, str]:
    config = VARIANTS[variant]
    lang = config["lang"]
    source = Path(config["bundle_root"])
    if lang == "en":
        return source, lang

    localized = temp_root / f"bundle_{lang}"
    shutil.copytree(source, localized)
    for page in localized.rglob("*.rst"):
        text = page.read_text(encoding="utf-8")
        page.write_text(
            text.replace(r"\HBApplyLang{en}", rf"\HBApplyLang{{{lang}}}"),
            encoding="utf-8",
        )
    if lang in _CJK_FIXTURE_REPLACEMENTS:
        _localize_cjk_bundle(localized, lang)
    return localized, lang


def _contains_text(parts: dict[str, bytes], text: str) -> bool:
    encoded = text.encode("utf-8")
    return any(encoded in data for data in parts.values())


class IdmlGoldenTests(unittest.TestCase):
    maxDiff = 2000

    def _build_and_normalize(self, variant: str) -> dict[str, bytes]:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "golden.idml"
            bundle_root, lang = _bundle_for_variant(variant, Path(td))
            proc = _build_package(bundle_root, out, lang=lang)
            self.assertEqual(
                proc.returncode, 0,
                f"exporter failed for {variant}:\n{proc.stdout}\n{proc.stderr}",
            )
            return _normalized_parts(out)

    def _assert_matches_golden(self, variant: str) -> None:
        golden = _golden_parts(variant)
        self.assertTrue(
            golden,
            f"no golden snapshot for {variant}; generate one with "
            "`python tests/test_export_idml_golden.py --regenerate`",
        )
        built = self._build_and_normalize(variant)
        for sentinel in CJK_SENTINELS.get(variant, ()):
            self.assertTrue(
                _contains_text(golden, sentinel),
                f"{variant}: golden snapshot is missing language sentinel {sentinel!r}",
            )
            self.assertTrue(
                _contains_text(built, sentinel),
                f"{variant}: built package is missing language sentinel {sentinel!r}",
            )
        self.assertEqual(
            sorted(built), sorted(golden),
            f"{variant}: package part list diverged from golden",
        )
        for name in sorted(golden):
            if built[name] != golden[name]:
                built_text = built[name].decode("utf-8")
                golden_text = golden[name].decode("utf-8")
                self.assertEqual(
                    golden_text, built_text,
                    f"{variant}/{name}: content diverged from golden",
                )

    def test_composed_packages_match_golden(self) -> None:
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                self._assert_matches_golden(variant)

    def test_build_is_deterministic(self) -> None:
        built: dict[str, dict[str, bytes]] = {}
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                first = self._build_and_normalize(variant)
                second = self._build_and_normalize(variant)
                self.assertEqual(first, second)
                built[variant] = first
        self.assertNotEqual(built["composed_ja"], built["composed_ko"])


def _regenerate() -> int:
    for variant in VARIANTS:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "golden.idml"
            bundle_root, lang = _bundle_for_variant(variant, Path(td))
            proc = _build_package(bundle_root, out, lang=lang)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr, file=sys.stderr)
                print(f"[golden] FAILED building {variant}", file=sys.stderr)
                return 1
            parts = _normalized_parts(out)
            _write_golden(variant, parts)
            print(f"[golden] wrote {len(parts)} parts -> {GOLDEN_ROOT / variant}")
    return 0


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        raise SystemExit(_regenerate())
    unittest.main()
