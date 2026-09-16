from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from tools import web_receipt
from tools.manual_catalog_writeback import CatalogWritebackResult
from tools.web_receipt import (
    ReceiptTarget,
    ReceiptWriteResult,
    discover_receipt_targets,
    find_document_link_candidates,
    resolve_receipt_record_ids,
    run_web_receipt,
    write_html_receipt,
)


def _write_publish_meta(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _base_payload(*, model: str, region: str, lang: str, version: str = "2.0", queue_record_ids=()) -> dict:
    return {
        "schema_version": "auto-manual-web-publish/v1",
        "model": model,
        "region": region,
        "lang": lang,
        "version": version,
        "md_output_path": f"reports/releases/{model}/{region}/{lang}/versions/{version}/web/md/manual.md",
        "queue_record_ids": list(queue_record_ids),
    }


def _document_link_record(record_id: str, *, document_key: str, lang: str) -> dict:
    return {"record_id": record_id, "fields": {"Document_Key": document_key, "Lang": lang}}


class DiscoverReceiptTargetsTests(unittest.TestCase):
    def test_should_find_every_target_when_unfiltered(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_publish_meta(
                root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-1000F", region="US", lang="en"),
            )
            _write_publish_meta(
                root / "JE-2000F" / "JP" / "ja" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-2000F", region="JP", lang="ja"),
            )

            targets = discover_receipt_targets(root)

        self.assertEqual(2, len(targets))
        self.assertEqual({"JE-1000F/US/en", "JE-2000F/JP/ja"}, {t.label() for t in targets})

    def test_should_narrow_by_model_region_lang(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_publish_meta(
                root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-1000F", region="US", lang="en"),
            )
            _write_publish_meta(
                root / "JE-1000F" / "US" / "fr" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-1000F", region="US", lang="fr"),
            )

            targets = discover_receipt_targets(root, model="JE-1000F", region="US", lang="en")

        self.assertEqual(["JE-1000F/US/en"], [t.label() for t in targets])

    def test_should_raise_when_no_target_matches_the_filters(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_publish_meta(
                root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-1000F", region="US", lang="en"),
            )

            with self.assertRaisesRegex(RuntimeError, "No Web Publish metadata matched"):
                discover_receipt_targets(root, model="JE-9999Z")

    def test_should_raise_when_metadata_is_missing_model_region_or_lang(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta_path = root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json"
            payload = _base_payload(model="JE-1000F", region="US", lang="en")
            del payload["lang"]
            _write_publish_meta(meta_path, payload)

            with self.assertRaisesRegex(RuntimeError, "missing model, region, or lang"):
                discover_receipt_targets(root)


class FindDocumentLinkCandidatesTests(unittest.TestCase):
    def test_should_match_model_region_lang_case_insensitively(self) -> None:
        records = [
            _document_link_record("rec_match", document_key="JE-1000F_US", lang="en"),
            _document_link_record("rec_other_region", document_key="JE-1000F_JP", lang="en"),
            _document_link_record("rec_other_lang", document_key="JE-1000F_US", lang="fr"),
        ]

        found = find_document_link_candidates(records, model="je-1000f", region="us", lang="EN")

        self.assertEqual(("rec_match",), found)

    def test_should_return_empty_tuple_when_nothing_matches(self) -> None:
        records = [_document_link_record("rec_1", document_key="JE-1000F_JP", lang="ja")]

        found = find_document_link_candidates(records, model="JE-1000F", region="US", lang="en")

        self.assertEqual((), found)

    def test_should_skip_rows_with_unresolvable_document_key(self) -> None:
        records = [{"record_id": "rec_bad", "fields": {"Document_Key": "not-a-key", "Lang": "en"}}]

        found = find_document_link_candidates(records, model="JE-1000F", region="US", lang="en")

        self.assertEqual((), found)

    def test_should_return_every_matching_record_when_ambiguous(self) -> None:
        records = [
            _document_link_record("rec_a", document_key="JE-1000F_US", lang="en"),
            _document_link_record("rec_b", document_key="JE-1000F_US", lang="en"),
        ]

        found = find_document_link_candidates(records, model="JE-1000F", region="US", lang="en")

        self.assertEqual(("rec_a", "rec_b"), found)


class ResolveReceiptRecordIdsTests(unittest.TestCase):
    def _target(self, **kwargs) -> ReceiptTarget:
        payload = _base_payload(model="JE-1000F", region="US", lang="en", **kwargs)
        return ReceiptTarget(model="JE-1000F", region="US", lang="en", metadata_path=Path("x"), payload=payload)

    def test_explicit_record_ids_take_priority(self) -> None:
        target = self._target(queue_record_ids=["rec_from_meta"])
        source = mock.Mock()

        found, mode = resolve_receipt_record_ids(
            target=target, explicit_record_ids=("rec_explicit",), source=source, binding=mock.Mock()
        )

        self.assertEqual(("rec_explicit",), found)
        self.assertEqual("explicit --receipt-record-id", mode)
        source.fetch_records_with_ids.assert_not_called()

    def test_queue_record_ids_used_when_no_explicit_override(self) -> None:
        target = self._target(queue_record_ids=["rec_from_meta"])
        source = mock.Mock()

        found, mode = resolve_receipt_record_ids(
            target=target, explicit_record_ids=(), source=source, binding=mock.Mock()
        )

        self.assertEqual(("rec_from_meta",), found)
        self.assertEqual("publish_meta.json queue_record_ids", mode)
        source.fetch_records_with_ids.assert_not_called()

    def test_falls_back_to_live_search_when_meta_has_no_queue_record_ids(self) -> None:
        target = self._target(queue_record_ids=[])
        binding = SimpleNamespace(base_token="base_doc", table_id="tbl_doc", view_id=None)
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = [
            _document_link_record("rec_found", document_key="JE-1000F_US", lang="en")
        ]

        found, mode = resolve_receipt_record_ids(
            target=target, explicit_record_ids=(), source=source, binding=binding
        )

        self.assertEqual(("rec_found",), found)
        self.assertEqual("search Document_link by model/region/lang", mode)
        source.fetch_records_with_ids.assert_called_once_with(
            base_token="base_doc", table_id="tbl_doc", view_id=None
        )


class WriteHtmlReceiptTests(unittest.TestCase):
    def _target(self) -> ReceiptTarget:
        payload = _base_payload(model="JE-1000F", region="US", lang="en")
        return ReceiptTarget(model="JE-1000F", region="US", lang="en", metadata_path=Path("x"), payload=payload)

    def _binding(self) -> SimpleNamespace:
        return SimpleNamespace(base_token="base_doc", table_id="tbl_doc", view_id=None)

    def test_should_skip_when_no_record_is_found(self) -> None:
        target = self._target()
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = []

        result = write_html_receipt(
            target=target,
            explicit_record_ids=(),
            base_url="https://ht-doc.readthedocs.io",
            source=source,
            binding=self._binding(),
            field_name="HTML_link",
        )

        self.assertEqual("skipped", result.status)
        source.upsert_record.assert_not_called()

    def test_should_reject_ambiguous_candidates(self) -> None:
        target = self._target()
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = [
            _document_link_record("rec_a", document_key="JE-1000F_US", lang="en"),
            _document_link_record("rec_b", document_key="JE-1000F_US", lang="en"),
        ]

        result = write_html_receipt(
            target=target,
            explicit_record_ids=(),
            base_url="https://ht-doc.readthedocs.io",
            source=source,
            binding=self._binding(),
            field_name="HTML_link",
        )

        self.assertEqual("ambiguous", result.status)
        source.upsert_record.assert_not_called()

    def test_should_write_and_confirm_readback_for_a_single_match(self) -> None:
        target = self._target()
        source = mock.Mock()
        source.fetch_records_with_ids.side_effect = [
            [_document_link_record("rec_1", document_key="JE-1000F_US", lang="en")],  # search
            [{"record_id": "rec_1", "fields": {"HTML_link": "https://ht-doc.readthedocs.io/manual.html"}}],  # readback
        ]

        result = write_html_receipt(
            target=target,
            explicit_record_ids=(),
            base_url="https://ht-doc.readthedocs.io",
            source=source,
            binding=self._binding(),
            field_name="HTML_link",
        )

        self.assertEqual("written", result.status)
        self.assertEqual(("rec_1",), result.record_ids)
        source.upsert_record.assert_called_once_with(
            base_token="base_doc",
            table_id="tbl_doc",
            record_id="rec_1",
            record={"HTML_link": "https://ht-doc.readthedocs.io/manual.html"},
        )

    def test_should_fail_when_readback_does_not_confirm_the_write(self) -> None:
        target = self._target()
        source = mock.Mock()
        source.fetch_records_with_ids.side_effect = [
            [_document_link_record("rec_1", document_key="JE-1000F_US", lang="en")],  # search
            [{"record_id": "rec_1", "fields": {"HTML_link": "https://stale.example.com"}}],  # readback
        ]

        result = write_html_receipt(
            target=target,
            explicit_record_ids=(),
            base_url="https://ht-doc.readthedocs.io",
            source=source,
            binding=self._binding(),
            field_name="HTML_link",
        )

        self.assertEqual("failed", result.status)
        self.assertIn("mismatch", result.detail)

    def test_explicit_record_id_bypasses_search(self) -> None:
        target = self._target()
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = [
            {"record_id": "rec_explicit", "fields": {"HTML_link": "https://ht-doc.readthedocs.io/manual.html"}}
        ]

        result = write_html_receipt(
            target=target,
            explicit_record_ids=("rec_explicit",),
            base_url="https://ht-doc.readthedocs.io",
            source=source,
            binding=self._binding(),
            field_name="HTML_link",
        )

        self.assertEqual("written", result.status)
        self.assertEqual(1, source.fetch_records_with_ids.call_count)  # readback only, no search


class RunWebReceiptTests(unittest.TestCase):
    def _resolve_path_from_root(self, root: Path):
        return lambda value: (root / value if not Path(value).is_absolute() else Path(value))

    def test_dry_run_should_touch_no_live_table(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            releases_root = root / "reports" / "releases"
            _write_publish_meta(
                releases_root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-1000F", region="US", lang="en"),
            )
            (root / "config.us-en.yaml").write_text("build: {}\n", encoding="utf-8")

            args = SimpleNamespace(
                config="config.us-en.yaml",
                releases_root=str(releases_root),
                base_url=None,
                receipt_record_id=[],
                model=None,
                region=None,
                lang=None,
                write=False,
            )

            def _boom(*_args, **_kwargs):
                raise AssertionError("dry-run must not touch any live table")

            with mock.patch.object(web_receipt, "load_config", side_effect=_boom), mock.patch.object(
                web_receipt, "LarkCliSource", side_effect=_boom
            ), mock.patch.object(web_receipt, "collect_queue_preflight_errors", side_effect=_boom):
                run_web_receipt(args, repo_root=root, resolve_path_from_root=self._resolve_path_from_root(root))

    def test_write_should_process_every_target_and_raise_on_any_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            releases_root = root / "reports" / "releases"
            _write_publish_meta(
                releases_root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-1000F", region="US", lang="en"),
            )
            _write_publish_meta(
                releases_root / "JE-2000F" / "JP" / "ja" / "latest" / "web" / "publish_meta.json",
                _base_payload(model="JE-2000F", region="JP", lang="ja"),
            )
            (root / "config.us.yaml").write_text("build: {}\n", encoding="utf-8")

            args = SimpleNamespace(
                config="config.us.yaml",
                releases_root=str(releases_root),
                base_url=None,
                receipt_record_id=[],
                model=None,
                region=None,
                lang=None,
                write=True,
            )

            binding = SimpleNamespace(base_token="base_doc", table_id="tbl_doc", view_id=None)
            catalog_settings = SimpleNamespace(base_token="base_cat", table_id="tbl_cat", view_id=None, identity="bot")

            def fake_write_html_receipt(*, target, **_kwargs):
                if target.model == "JE-1000F":
                    return ReceiptWriteResult(status="written", record_ids=("rec_1",), detail="ok", url="https://x/1.html")
                return ReceiptWriteResult(status="ambiguous", record_ids=("rec_a", "rec_b"), detail="ambiguous")

            def fake_write_catalog_record(*, model, **_kwargs):
                return CatalogWritebackResult(status="created", record_id=f"rec_catalog_{model}", detail="ok")

            with mock.patch.object(web_receipt, "load_config", return_value={}), mock.patch.object(
                web_receipt, "collect_queue_preflight_errors", return_value=[]
            ), mock.patch.object(
                web_receipt, "resolve_document_link_binding", return_value=binding
            ), mock.patch.object(
                web_receipt, "cli_bin", return_value="lark-cli"
            ), mock.patch.object(
                web_receipt, "phase2_identity", return_value="bot"
            ), mock.patch.object(
                web_receipt,
                "fetch_field_id_map",
                return_value={"HTML_link": "fld_html"},
            ), mock.patch.object(
                web_receipt, "manual_index_settings_from_env", return_value=catalog_settings
            ), mock.patch.object(
                web_receipt, "LarkCliSource", side_effect=[mock.Mock(), mock.Mock()]
            ), mock.patch.object(
                web_receipt, "write_html_receipt", side_effect=fake_write_html_receipt
            ) as html_mock, mock.patch.object(
                web_receipt, "write_catalog_record", side_effect=fake_write_catalog_record
            ) as catalog_mock:
                with self.assertRaisesRegex(RuntimeError, "1/2 target"):
                    run_web_receipt(
                        args, repo_root=root, resolve_path_from_root=self._resolve_path_from_root(root)
                    )

            self.assertEqual(2, html_mock.call_count)
            self.assertEqual(2, catalog_mock.call_count)


if __name__ == "__main__":
    unittest.main()
