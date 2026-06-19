#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the cloud-doc finalize ops (tools/queue_cloud_doc_finalize.py).

These cover the operator edit-access grant + wiki co-location that fix the
"built Feishu cloud-doc is bot-owned, operator can only make a 副本" problem.
All ops are pure (injected callables) — no network.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.queue_cloud_doc_finalize import (  # noqa: E402
    finalize_cloud_doc,
    grant_doc_full_access,
    is_wiki_destination,
)
from tools.queue_lark_ops import move_drive_file_to_wiki  # noqa: E402

WIKI_DEST = SimpleNamespace(space_id="spc123", parent_wiki_token="wiknodeP")
NON_WIKI_DEST = SimpleNamespace(space_id="", parent_wiki_token="")


class GrantDocFullAccessTests(unittest.TestCase):
    def _capture(self):
        calls: list[list[str]] = []

        def fake_run(*, cli_bin: str, args: list[str]) -> dict[str, object]:
            calls.append(args)
            return {"ok": True}

        return calls, fake_run

    def test_builds_permission_member_create_args(self) -> None:
        calls, fake_run = self._capture()
        grant_doc_full_access(
            cli_bin="lark-cli",
            identity="bot",
            doc_token="docTOKEN",
            member_id="on_union_xyz",
            run_lark_cli_json=fake_run,
        )
        self.assertEqual(len(calls), 1)
        args = calls[0]
        self.assertEqual(args[:3], ["drive", "permission.members", "create"])
        self.assertIn("--as", args)
        self.assertEqual(args[args.index("--as") + 1], "bot")
        self.assertIn("--yes", args)  # high-risk confirmation gate
        params = json.loads(args[args.index("--params") + 1])
        self.assertEqual(params, {"token": "docTOKEN", "type": "docx"})
        data = json.loads(args[args.index("--data") + 1])
        self.assertEqual(data, {"member_type": "unionid", "member_id": "on_union_xyz", "perm": "full_access"})

    def test_requires_doc_token_and_member(self) -> None:
        _calls, fake_run = self._capture()
        with self.assertRaises(RuntimeError):
            grant_doc_full_access(cli_bin="c", identity="bot", doc_token="", member_id="m", run_lark_cli_json=fake_run)
        with self.assertRaises(RuntimeError):
            grant_doc_full_access(cli_bin="c", identity="bot", doc_token="d", member_id="", run_lark_cli_json=fake_run)


class IsWikiDestinationTests(unittest.TestCase):
    def test_true_when_space_and_parent_present(self) -> None:
        self.assertTrue(is_wiki_destination(WIKI_DEST))

    def test_false_when_missing(self) -> None:
        self.assertFalse(is_wiki_destination(NON_WIKI_DEST))
        self.assertFalse(is_wiki_destination(SimpleNamespace(space_id="s")))
        self.assertFalse(is_wiki_destination(None))


class MoveObjTypeTests(unittest.TestCase):
    def test_obj_type_passed_through(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(*, cli_bin: str, args: list[str]) -> dict[str, object]:
            captured["data"] = json.loads(args[args.index("--data") + 1])
            return {"data": {"wiki_token": "wTok"}}

        url = move_drive_file_to_wiki(
            cli_bin="lark-cli",
            identity="bot",
            file_token="objTOK",
            drive_url="https://x.feishu.cn/docx/objTOK",
            destination=WIKI_DEST,
            run_lark_cli_json=fake_run,
            host_root_from_url=lambda u: "https://x.feishu.cn",
            wiki_url_from_host_root=lambda host, tok: f"{host}/wiki/{tok}",
            wait_for_wiki_move_task=lambda **k: "unused",
            obj_type="docx",
        )
        self.assertEqual(captured["data"]["obj_type"], "docx")
        self.assertEqual(captured["data"]["obj_token"], "objTOK")
        self.assertEqual(url, "https://x.feishu.cn/wiki/wTok")


class FinalizeCloudDocTests(unittest.TestCase):
    def _fakes(self, *, move_url: str = "https://x.feishu.cn/wiki/wTok", grant_exc=None, move_exc=None):
        grant_calls: list[tuple[str, str]] = []
        move_calls: list[tuple[str, str]] = []
        warnings: list[str] = []

        def grant(*, doc_token: str, member_id: str) -> None:
            grant_calls.append((doc_token, member_id))
            if grant_exc:
                raise grant_exc

        def move(*, obj_token: str, doc_url: str) -> str:
            move_calls.append((obj_token, doc_url))
            if move_exc:
                raise move_exc
            return move_url

        return grant_calls, move_calls, warnings, grant, move

    def test_grants_then_moves_to_wiki(self) -> None:
        grant_calls, move_calls, warnings, grant, move = self._fakes()
        url = finalize_cloud_doc(
            cloud_doc_token="docTOK",
            cloud_doc_url="https://x.feishu.cn/docx/docTOK",
            member_union_id="on_union_xyz",
            destination=WIKI_DEST,
            grant_full_access=grant,
            move_to_wiki=move,
            on_warning=warnings.append,
        )
        self.assertEqual(grant_calls, [("docTOK", "on_union_xyz")])
        self.assertEqual(move_calls, [("docTOK", "https://x.feishu.cn/docx/docTOK")])
        self.assertEqual(url, "https://x.feishu.cn/wiki/wTok")  # wiki URL after move
        self.assertEqual(warnings, [])

    def test_skips_grant_when_no_member(self) -> None:
        grant_calls, move_calls, _w, grant, move = self._fakes()
        url = finalize_cloud_doc(
            cloud_doc_token="docTOK",
            cloud_doc_url="https://x/docx/docTOK",
            member_union_id="",
            destination=WIKI_DEST,
            grant_full_access=grant,
            move_to_wiki=move,
        )
        self.assertEqual(grant_calls, [])
        self.assertEqual(move_calls, [("docTOK", "https://x/docx/docTOK")])
        self.assertEqual(url, "https://x.feishu.cn/wiki/wTok")

    def test_skips_move_for_non_wiki_destination(self) -> None:
        grant_calls, move_calls, _w, grant, move = self._fakes()
        url = finalize_cloud_doc(
            cloud_doc_token="docTOK",
            cloud_doc_url="https://x/docx/docTOK",
            member_union_id="on_union_xyz",
            destination=NON_WIKI_DEST,
            grant_full_access=grant,
            move_to_wiki=move,
        )
        self.assertEqual(grant_calls, [("docTOK", "on_union_xyz")])
        self.assertEqual(move_calls, [])  # no wiki dest -> no move
        self.assertEqual(url, "https://x/docx/docTOK")  # original import URL

    def test_grant_failure_is_best_effort(self) -> None:
        _gc, move_calls, warnings, grant, move = self._fakes(grant_exc=RuntimeError("perm boom"))
        url = finalize_cloud_doc(
            cloud_doc_token="docTOK",
            cloud_doc_url="https://x/docx/docTOK",
            member_union_id="on_union_xyz",
            destination=WIKI_DEST,
            grant_full_access=grant,
            move_to_wiki=move,
            on_warning=warnings.append,
        )
        # grant blew up but the build continues: move still ran, warning logged
        self.assertEqual(len(warnings), 1)
        self.assertIn("grant failed", warnings[0])
        self.assertEqual(move_calls, [("docTOK", "https://x/docx/docTOK")])
        self.assertEqual(url, "https://x.feishu.cn/wiki/wTok")

    def test_move_failure_falls_back_to_import_url(self) -> None:
        _gc, _mc, warnings, grant, move = self._fakes(move_exc=RuntimeError("wiki boom"))
        url = finalize_cloud_doc(
            cloud_doc_token="docTOK",
            cloud_doc_url="https://x/docx/docTOK",
            member_union_id="on_union_xyz",
            destination=WIKI_DEST,
            grant_full_access=grant,
            move_to_wiki=move,
            on_warning=warnings.append,
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn("co-location failed", warnings[0])
        self.assertEqual(url, "https://x/docx/docTOK")  # fallback: keep import URL


if __name__ == "__main__":
    unittest.main()
