from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import write_publish_html_link


class TestWritePublishHtmlLink(unittest.TestCase):
    def test_resolve_field_name_should_match_normalized_html_link(self) -> None:
        resolved = write_publish_html_link.resolve_field_name(
            {
                "Document link": "fld_doc",
                "HTML link": "fld_html",
            },
            write_publish_html_link.HTML_LINK_FIELD,
        )

        self.assertEqual("HTML link", resolved)

    def test_resolve_html_link_field_name_should_support_aliases(self) -> None:
        resolved = write_publish_html_link.resolve_html_link_field_name(
            {
                "网页链接": "fld_html",
            }
        )

        self.assertEqual("网页链接", resolved)

    def test_resolve_rtd_link_field_name_should_support_aliases(self) -> None:
        resolved = write_publish_html_link.resolve_rtd_link_field_name(
            {
                "Read the Docs URL": "fld_rtd",
            }
        )

        self.assertEqual("Read the Docs URL", resolved)

    def test_target_record_ids_from_publish_meta_should_prefer_explicit_ids(self) -> None:
        payload = {"queue_record_ids": ["rec_meta_1", "rec_meta_2"]}

        resolved = write_publish_html_link.target_record_ids_from_publish_meta(
            payload,
            explicit_record_ids=("rec_cli_1", "rec_cli_1", " rec_cli_2 "),
        )

        self.assertEqual(("rec_cli_1", "rec_cli_2"), resolved)

    def test_persist_publish_urls_should_update_latest_and_version_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            latest_meta_path = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            version_meta_path = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "publish_meta.json"
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            version_meta_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": "0.2",
                "queue_record_ids": ["rec_publish"],
            }
            write_publish_html_link.write_json(latest_meta_path, payload)
            write_publish_html_link.write_json(version_meta_path, payload)

            written = write_publish_html_link.persist_publish_urls(
                latest_meta_path=latest_meta_path,
                payload=payload,
                publish_url="https://manual.example.com/latest",
                rtd_url="https://docs.example.com/en/latest/",
            )

            self.assertEqual((latest_meta_path, version_meta_path), written)
            latest_payload = write_publish_html_link.read_json(latest_meta_path)
            version_payload = write_publish_html_link.read_json(version_meta_path)
            self.assertEqual("https://manual.example.com/latest", latest_payload["publish_url"])
            self.assertEqual("https://manual.example.com/latest", version_payload["publish_url"])
            self.assertEqual("https://docs.example.com/en/latest/", latest_payload["rtd_url"])
            self.assertEqual("https://docs.example.com/en/latest/", version_payload["rtd_url"])

    def test_write_publish_html_link_should_update_all_queue_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.us.yaml"
            releases_root = root / "reports" / "releases"
            latest_meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            version_meta_path = releases_root / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "publish_meta.json"
            config_path.write_text("sync:\n  phase2:\n    provider: lark_cli\n", encoding="utf-8")
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            version_meta_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "built_at": "2026-04-24T12:00:00",
                "version": "0.2",
                "queue_record_ids": ["rec_publish_1", "rec_publish_2"],
            }
            write_publish_html_link.write_json(latest_meta_path, payload)
            write_publish_html_link.write_json(version_meta_path, payload)
            binding = mock.Mock(base_token="base_123", table_id="tbl_123")
            source = mock.Mock()

            with mock.patch.object(write_publish_html_link, "load_config", return_value={"sync": {"phase2": {}}}), mock.patch.object(
                write_publish_html_link,
                "collect_queue_preflight_errors",
                return_value=[],
            ), mock.patch.object(
                write_publish_html_link,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(
                write_publish_html_link,
                "cli_bin",
                return_value="lark-cli",
            ), mock.patch.object(
                write_publish_html_link,
                "fetch_field_id_map",
                return_value={write_publish_html_link.HTML_LINK_FIELD: "fld_html"},
            ) as fetch_field_id_map, mock.patch.object(
                write_publish_html_link,
                "LarkCliSource",
                return_value=source,
            ) as lark_cli_source, mock.patch.object(
                write_publish_html_link,
                "phase2_identity",
                return_value="bot",
            ) as phase2_identity:
                written = write_publish_html_link.write_publish_html_link(
                    config_path=config_path,
                    publish_url="https://manual.example.com/latest",
                    releases_root=releases_root,
                )

            self.assertEqual(2, written)
            self.assertEqual(2, source.upsert_record.call_count)
            first_call = source.upsert_record.call_args_list[0].kwargs
            second_call = source.upsert_record.call_args_list[1].kwargs
            self.assertEqual("rec_publish_1", first_call["record_id"])
            self.assertEqual("rec_publish_2", second_call["record_id"])
            self.assertEqual(
                {write_publish_html_link.HTML_LINK_FIELD: "https://manual.example.com/latest"},
                first_call["record"],
            )
            self.assertEqual("bot", phase2_identity.return_value)
            self.assertEqual("bot", fetch_field_id_map.call_args.kwargs["identity"])
            self.assertEqual("bot", lark_cli_source.call_args.kwargs["identity"])
            updated_meta = write_publish_html_link.read_json(latest_meta_path)
            self.assertEqual("https://manual.example.com/latest", updated_meta["publish_url"])

    def test_write_publish_html_link_should_use_resolved_field_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.us.yaml"
            releases_root = root / "reports" / "releases"
            latest_meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            config_path.write_text("sync:\n  phase2:\n    provider: lark_cli\n", encoding="utf-8")
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            write_publish_html_link.write_json(
                latest_meta_path,
                {
                    "built_at": "2026-04-24T12:00:00",
                    "version": "0.2",
                    "queue_record_ids": ["rec_publish_1"],
                },
            )
            binding = mock.Mock(base_token="base_123", table_id="tbl_123")
            source = mock.Mock()

            with mock.patch.object(write_publish_html_link, "load_config", return_value={"sync": {"phase2": {}}}), mock.patch.object(
                write_publish_html_link,
                "collect_queue_preflight_errors",
                return_value=[],
            ), mock.patch.object(
                write_publish_html_link,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(
                write_publish_html_link,
                "cli_bin",
                return_value="lark-cli",
            ), mock.patch.object(
                write_publish_html_link,
                "fetch_field_id_map",
                return_value={"HTML link": "fld_html"},
            ), mock.patch.object(
                write_publish_html_link,
                "LarkCliSource",
                return_value=source,
            ), mock.patch.object(
                write_publish_html_link,
                "phase2_identity",
                return_value="bot",
            ):
                written = write_publish_html_link.write_publish_html_link(
                    config_path=config_path,
                    publish_url="https://manual.example.com/latest",
                    releases_root=releases_root,
                )

            self.assertEqual(1, written)
            self.assertEqual(
                {"HTML link": "https://manual.example.com/latest"},
                source.upsert_record.call_args.kwargs["record"],
            )

    def test_write_publish_html_link_should_update_rtd_link_when_url_is_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.us.yaml"
            releases_root = root / "reports" / "releases"
            latest_meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            config_path.write_text("sync:\n  phase2:\n    provider: lark_cli\n", encoding="utf-8")
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            write_publish_html_link.write_json(
                latest_meta_path,
                {
                    "built_at": "2026-04-24T12:00:00",
                    "version": "0.2",
                    "queue_record_ids": ["rec_publish_1"],
                },
            )
            binding = mock.Mock(base_token="base_123", table_id="tbl_123")
            source = mock.Mock()

            with mock.patch.object(write_publish_html_link, "load_config", return_value={"sync": {"phase2": {}}}), mock.patch.object(
                write_publish_html_link,
                "collect_queue_preflight_errors",
                return_value=[],
            ), mock.patch.object(
                write_publish_html_link,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(
                write_publish_html_link,
                "cli_bin",
                return_value="lark-cli",
            ), mock.patch.object(
                write_publish_html_link,
                "fetch_field_id_map",
                return_value={
                    write_publish_html_link.HTML_LINK_FIELD: "fld_html",
                    write_publish_html_link.RTD_LINK_FIELD: "fld_rtd",
                },
            ), mock.patch.object(
                write_publish_html_link,
                "LarkCliSource",
                return_value=source,
            ), mock.patch.object(
                write_publish_html_link,
                "phase2_identity",
                return_value="bot",
            ):
                written = write_publish_html_link.write_publish_html_link(
                    config_path=config_path,
                    publish_url="https://manual.example.com/latest",
                    rtd_url="https://docs.example.com/en/latest/",
                    releases_root=releases_root,
                )

            self.assertEqual(1, written)
            self.assertEqual(2, source.upsert_record.call_count)
            self.assertEqual(
                {write_publish_html_link.HTML_LINK_FIELD: "https://manual.example.com/latest"},
                source.upsert_record.call_args_list[0].kwargs["record"],
            )
            self.assertEqual(
                {write_publish_html_link.RTD_LINK_FIELD: "https://docs.example.com/en/latest/"},
                source.upsert_record.call_args_list[1].kwargs["record"],
            )
            updated_meta = write_publish_html_link.read_json(latest_meta_path)
            self.assertEqual("https://docs.example.com/en/latest/", updated_meta["rtd_url"])

    def test_write_publish_html_link_should_write_only_rtd_link_when_publish_url_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.us.yaml"
            releases_root = root / "reports" / "releases"
            latest_meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            config_path.write_text("sync:\n  phase2:\n    provider: lark_cli\n", encoding="utf-8")
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            write_publish_html_link.write_json(
                latest_meta_path,
                {
                    "built_at": "2026-04-24T12:00:00",
                    "version": "0.2",
                    "queue_record_ids": ["rec_publish_1"],
                },
            )
            binding = mock.Mock(base_token="base_123", table_id="tbl_123")
            source = mock.Mock()

            with mock.patch.object(write_publish_html_link, "load_config", return_value={"sync": {"phase2": {}}}), mock.patch.object(
                write_publish_html_link,
                "collect_queue_preflight_errors",
                return_value=[],
            ), mock.patch.object(
                write_publish_html_link,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(
                write_publish_html_link,
                "cli_bin",
                return_value="lark-cli",
            ), mock.patch.object(
                write_publish_html_link,
                "fetch_field_id_map",
                return_value={write_publish_html_link.RTD_LINK_FIELD: "fld_rtd"},
            ), mock.patch.object(
                write_publish_html_link,
                "LarkCliSource",
                return_value=source,
            ), mock.patch.object(
                write_publish_html_link,
                "phase2_identity",
                return_value="bot",
            ):
                written = write_publish_html_link.write_publish_html_link(
                    config_path=config_path,
                    publish_url="",
                    rtd_url="https://docs.example.com/en/latest/",
                    releases_root=releases_root,
                )

            self.assertEqual(1, written)
            self.assertEqual(1, source.upsert_record.call_count)
            self.assertEqual(
                {write_publish_html_link.RTD_LINK_FIELD: "https://docs.example.com/en/latest/"},
                source.upsert_record.call_args.kwargs["record"],
            )

    def test_write_publish_html_link_should_skip_when_html_link_field_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.us.yaml"
            releases_root = root / "reports" / "releases"
            latest_meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            config_path.write_text("sync:\n  phase2:\n    provider: lark_cli\n", encoding="utf-8")
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            write_publish_html_link.write_json(
                latest_meta_path,
                {
                    "built_at": "2026-04-24T12:00:00",
                    "version": "0.2",
                    "queue_record_ids": ["rec_publish_1"],
                },
            )
            binding = mock.Mock(base_token="base_123", table_id="tbl_123")
            source = mock.Mock()
            source.upsert_record.side_effect = RuntimeError("unknown field")

            with mock.patch.object(write_publish_html_link, "load_config", return_value={"sync": {"phase2": {}}}), mock.patch.object(
                write_publish_html_link,
                "collect_queue_preflight_errors",
                return_value=[],
            ), mock.patch.object(
                write_publish_html_link,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(
                write_publish_html_link,
                "cli_bin",
                return_value="lark-cli",
            ), mock.patch.object(
                write_publish_html_link,
                "fetch_field_id_map",
                return_value={},
            ), mock.patch.object(
                write_publish_html_link,
                "LarkCliSource",
                return_value=source,
            ):
                written = write_publish_html_link.write_publish_html_link(
                    config_path=config_path,
                    publish_url="https://manual.example.com/latest",
                    releases_root=releases_root,
                )

            self.assertEqual(0, written)
            self.assertGreater(source.upsert_record.call_count, 0)

    def test_write_publish_html_link_should_fallback_to_direct_html_link_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.us.yaml"
            releases_root = root / "reports" / "releases"
            latest_meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            config_path.write_text("sync:\n  phase2:\n    provider: lark_cli\n", encoding="utf-8")
            latest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            write_publish_html_link.write_json(
                latest_meta_path,
                {
                    "built_at": "2026-04-24T12:00:00",
                    "version": "0.2",
                    "queue_record_ids": ["rec_publish_1"],
                },
            )
            binding = mock.Mock(base_token="base_123", table_id="tbl_123")
            source = mock.Mock()

            def fake_upsert_record(**kwargs: object) -> dict[str, object]:
                record = kwargs["record"]
                if record != {write_publish_html_link.HTML_LINK_FIELD: "https://manual.example.com/latest"}:
                    raise RuntimeError("unknown field")
                return {"ok": True}

            source.upsert_record.side_effect = fake_upsert_record

            with mock.patch.object(write_publish_html_link, "load_config", return_value={"sync": {"phase2": {}}}), mock.patch.object(
                write_publish_html_link,
                "collect_queue_preflight_errors",
                return_value=[],
            ), mock.patch.object(
                write_publish_html_link,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(
                write_publish_html_link,
                "cli_bin",
                return_value="lark-cli",
            ), mock.patch.object(
                write_publish_html_link,
                "fetch_field_id_map",
                return_value={"Document link": "fld_doc"},
            ), mock.patch.object(
                write_publish_html_link,
                "LarkCliSource",
                return_value=source,
            ), mock.patch.object(
                write_publish_html_link,
                "phase2_identity",
                return_value="bot",
            ):
                written = write_publish_html_link.write_publish_html_link(
                    config_path=config_path,
                    publish_url="https://manual.example.com/latest",
                    releases_root=releases_root,
                )

            self.assertEqual(1, written)
            self.assertEqual(
                {write_publish_html_link.HTML_LINK_FIELD: "https://manual.example.com/latest"},
                source.upsert_record.call_args.kwargs["record"],
            )
