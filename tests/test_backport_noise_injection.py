#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adversarial noise injection for cloud-doc backport (L3 of the test plan).

The reactive failure mode of the backport loop is *noise that survives
normalization and surfaces as a false delta* (the highlight-metadata and
image-re-host classes that PR #466 / #423 fixed after a real doc hit them). This
module attacks that proactively: it takes a clean baseline, applies noise-only
transformations a real Feishu round-trip would introduce, and asserts the diff
stays empty — so the next noise class is caught here, not in production.

It also pins the two transformations that are deliberately **not** treated as
noise (so the boundary is explicit and a regression in either direction is
visible):

- a markdown-link re-wrap of body text surfaces as a review edit (the body
  normalizer intentionally does not unwrap links — only the CLI ``doc_url`` is
  unwrapped). This is a *candidate* noise source flagged for an operator decision.
- an HTML ``<img>`` vs markdown ``![image]`` form maps to distinct sentinels, so
  converting between them is reported as an ``image_asset_delta`` (asset change),
  never a source/review write.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.cloud_doc_backport import build_report


def _report(baseline: str, fetched: str, *, doc_type: str = "review") -> dict:
    return build_report(
        run_id="noise",
        doc_type=doc_type,
        doc_url="https://x.feishu.cn/wiki/noise",
        baseline_path=Path("baseline.md"),
        fetched_text=fetched,
        baseline_text=baseline,
        command=["test"],
        source_path=None,
        section_title=None,
        value_index=None,
    )


# --- noise-only transformations: each MUST leave the normalized text unchanged --- #
def inject_trailing_ws(text: str) -> str:
    return "\n".join(line + "   " for line in text.splitlines())


def inject_internal_ws(text: str) -> str:
    # Double every run of spaces (normalization collapses runs back to one).
    return re.sub(r" ", "  ", text)


def inject_leading_ws(text: str) -> str:
    return "\n".join("   " + line for line in text.splitlines())


def inject_feishu_highlight(text: str) -> str:
    # Feishu review highlights wrap the selected span in <text bgcolor=...> metadata.
    return "\n".join(
        f'<text bgcolor="rgb(255,246,122)">{line}</text>' if line.strip() else line
        for line in text.splitlines()
    )


def inject_image_rehost(text: str) -> str:
    # Feishu re-hosts each image under a fresh token on every import.
    return re.sub(r"(/img/)(\w+)", r"\1\2_REHOSTED", text)


def inject_bold_markup(text: str) -> str:
    # Wrap the first word of each prose line in ** (the normalizer drops ** / __).
    out = []
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("|") and "![" not in line and "<img" not in line:
            head, _, tail = line.partition(" ")
            out.append(f"**{head}** {tail}" if tail else f"**{head}**")
        else:
            out.append(line)
    return "\n".join(out)


def inject_smart_quotes(text: str) -> str:
    return text.replace('"', "“").replace("'", "’")


_NOISE_INJECTORS = [
    inject_trailing_ws,
    inject_internal_ws,
    inject_leading_ws,
    inject_feishu_highlight,
    inject_image_rehost,
    inject_bold_markup,
    inject_smart_quotes,
]

_BASES = [
    "Charge the battery fully before first use.",
    "Charge the battery fully.\n\nKeep the device dry and away from heat.",
    'Press "Power" to start.\n\nThe LED turns green.',
    "Overview\n\n| ![diagram](https://x/img/TOKEN1) |\n\nConnect the cable.",
    "デバイスは自動的に充電を開始します。\n\nケーブルを差し込んでください。",
]


class NoiseInjectionTests(unittest.TestCase):
    def test_each_injector_alone_produces_no_delta(self) -> None:
        for base in _BASES:
            for inject in _NOISE_INJECTORS:
                with self.subTest(base=base[:24], injector=inject.__name__):
                    report = _report(base, inject(base))
                    self.assertEqual(
                        report["summary"]["total_deltas"],
                        0,
                        f"{inject.__name__} on {base[:24]!r} leaked a delta: "
                        f"{report['summary']['route_classes']}",
                    )

    def test_all_injectors_combined_produce_no_delta(self) -> None:
        for base in _BASES:
            with self.subTest(base=base[:24]):
                noised = base
                for inject in _NOISE_INJECTORS:
                    noised = inject(noised)
                report = _report(base, noised)
                self.assertEqual(
                    report["summary"]["total_deltas"],
                    0,
                    f"combined noise leaked a delta on {base[:24]!r}: "
                    f"{report['summary']['route_classes']}",
                )

    def test_real_edit_survives_a_full_noise_bath(self) -> None:
        # A single genuine prose edit must surface as exactly one repo_review_text
        # delta even when every noise transformation is applied on top of it.
        base = "Charge the battery fully.\n\nKeep the device dry."
        edited = base.replace("Keep the device dry.", "Keep the device away from water.")
        for inject in _NOISE_INJECTORS:
            edited = inject(edited)
        report = _report(base, edited)
        self.assertEqual(report["summary"]["total_deltas"], 1)
        self.assertEqual(report["summary"]["route_classes"], {"repo_review_text": 1})
        self.assertIn("water", report["deltas"][0]["new_text"])

    # --- documented non-noise boundaries (regression pins, not bugs) --- #
    def test_markdown_link_rewrap_of_body_is_a_review_edit(self) -> None:
        # CANDIDATE NOISE GAP: the body normalizer does not unwrap markdown links,
        # so a bare-URL <-> [url](url) re-wrap reads as a real edit. Pinned so the
        # behavior is explicit; flagged for an operator decision on whether Feishu
        # round-trips introduce this and it should be normalized away.
        base = "See https://example.com/guide for details."
        rewrapped = "See [https://example.com/guide](https://example.com/guide) for details."
        report = _report(base, rewrapped)
        self.assertEqual(report["summary"]["route_classes"], {"repo_review_text": 1})

    def test_html_vs_markdown_image_is_an_asset_delta(self) -> None:
        # <img> and ![image] are distinct sentinels, so a form swap is an asset
        # change (never a source/review write).
        report = _report("| <img src='https://x/a'> |", "| ![pic](https://x/b) |")
        self.assertEqual(report["summary"]["route_classes"], {"image_asset_delta": 1})


if __name__ == "__main__":
    unittest.main()
