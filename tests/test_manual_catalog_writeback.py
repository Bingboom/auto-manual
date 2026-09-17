from __future__ import annotations

import json
import os
import unittest
from typing import Any
from unittest import mock

from tools import manual_catalog_writeback
from tools.manual_catalog_writeback import (
    CATALOG_UNKNOWN_VERSION_LABEL,
    CATALOG_WEB_DOC_TYPE,
    catalog_writeback_settings_from_env,
    ensure_select_option,
    find_catalog_candidates,
    format_catalog_notes,
    resolve_catalog_lang_label,
    resolve_catalog_region_label,
    verify_record_fields,
    write_catalog_record,
)
from tools.manual_index_query import (
    FIELD_DOC_TYPE,
    FIELD_MANUAL_LINK,
    FIELD_MODELS,
    FIELD_NOTES,
    FIELD_REGION,
    FIELD_SOURCE_LANG,
    FIELD_VERSION,
    ManualIndexSettings,
    manual_index_row_from_record,
)


def _catalog_record(
    record_id: str,
    *,
    models: tuple[str, ...] = (),
    region: tuple[str, ...] = (),
    source_lang: tuple[str, ...] = (),
    doc_type: tuple[str, ...] = (),
    manual_link: str = "",
    version: tuple[str, ...] = (),
    notes: str = "",
) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "fields": {
            FIELD_MODELS: list(models),
            FIELD_REGION: list(region),
            FIELD_SOURCE_LANG: list(source_lang),
            FIELD_DOC_TYPE: list(doc_type),
            FIELD_MANUAL_LINK: manual_link,
            FIELD_VERSION: list(version),
            FIELD_NOTES: notes,
        },
    }


SETTINGS = ManualIndexSettings(base_token="base_catalog", table_id="tbl_catalog", view_id="view_catalog", identity="bot")


class ResolveLabelTests(unittest.TestCase):
    def test_resolve_catalog_region_label_should_use_known_alias(self) -> None:
        self.assertEqual("美加规", resolve_catalog_region_label("US"))
        self.assertEqual("欧规", resolve_catalog_region_label("eu"))

    def test_resolve_catalog_region_label_should_fall_back_to_raw_value(self) -> None:
        self.assertEqual("XX", resolve_catalog_region_label("XX"))

    def test_resolve_catalog_lang_label_should_use_known_alias(self) -> None:
        self.assertEqual("EN", resolve_catalog_lang_label("en"))
        self.assertEqual("KR", resolve_catalog_lang_label("ko"))

    def test_resolve_catalog_lang_label_should_fall_back_to_uppercased_raw_value(self) -> None:
        self.assertEqual("FR", resolve_catalog_lang_label("fr"))


class FormatCatalogNotesTests(unittest.TestCase):
    def test_should_combine_version_and_link(self) -> None:
        self.assertEqual(
            "version=2.0; alias=https://ht-doc.readthedocs.io/x.html",
            format_catalog_notes(version="2.0", link="https://ht-doc.readthedocs.io/x.html"),
        )


class CatalogWritebackSettingsFromEnvTests(unittest.TestCase):
    def _base_settings(self) -> ManualIndexSettings:
        return ManualIndexSettings(
            base_token="base_catalog",
            table_id="tbl_catalog",
            view_id="view_catalog",
            identity="whatever-the-read-path-picked",
        )

    def test_should_default_identity_to_user_when_unset(self) -> None:
        with mock.patch.dict(os.environ, {"FEISHU_MANUAL_INDEX_IDENTITY": ""}), mock.patch.object(
            manual_catalog_writeback, "manual_index_settings_from_env", return_value=self._base_settings()
        ):
            settings = catalog_writeback_settings_from_env({})

        self.assertEqual("user", settings.identity)
        self.assertEqual("base_catalog", settings.base_token)
        self.assertEqual("tbl_catalog", settings.table_id)

    def test_should_respect_an_explicit_identity_override(self) -> None:
        with mock.patch.dict(os.environ, {"FEISHU_MANUAL_INDEX_IDENTITY": "bot"}), mock.patch.object(
            manual_catalog_writeback, "manual_index_settings_from_env", return_value=self._base_settings()
        ):
            settings = catalog_writeback_settings_from_env({})

        self.assertEqual("bot", settings.identity)

    def test_should_reject_an_invalid_identity_value(self) -> None:
        with mock.patch.dict(os.environ, {"FEISHU_MANUAL_INDEX_IDENTITY": "robot"}), mock.patch.object(
            manual_catalog_writeback, "manual_index_settings_from_env", return_value=self._base_settings()
        ):
            with self.assertRaises(RuntimeError):
                catalog_writeback_settings_from_env({})


class EnsureSelectOptionTests(unittest.TestCase):
    @staticmethod
    def _field_list_payload(*, field_id: str, field_name: str, options: list[str], multiple: bool = False) -> dict:
        return {
            "code": 0,
            "data": {
                "items": [
                    {
                        "field_id": field_id,
                        "field_name": field_name,
                        "type": "multi_select" if multiple else "single_select",
                        "property": {"options": [{"name": name} for name in options]},
                        "multiple": multiple,
                    }
                ],
                "total": 1,
            },
        }

    def test_should_skip_field_update_when_option_already_exists(self) -> None:
        run_lark_cli_json = mock.Mock(
            return_value=self._field_list_payload(
                field_id="fld_doc_type", field_name="文档类型", options=["User Manual", "Web手册"]
            )
        )

        added = ensure_select_option(
            cli_bin="lark-cli",
            identity="user",
            base_token="base_catalog",
            table_id="tbl_catalog",
            field_name="文档类型",
            option_name="Web手册",
            run_lark_cli_json=run_lark_cli_json,
        )

        self.assertFalse(added)
        run_lark_cli_json.assert_called_once()  # +field-list only; no +field-update needed

    def test_should_append_the_missing_option_via_a_full_put(self) -> None:
        list_payload = self._field_list_payload(
            field_id="fld_doc_type", field_name="文档类型", options=["User Manual", "取扱説明書"]
        )
        run_lark_cli_json = mock.Mock(side_effect=[list_payload, {"code": 0, "data": {}}])

        added = ensure_select_option(
            cli_bin="lark-cli",
            identity="user",
            base_token="base_catalog",
            table_id="tbl_catalog",
            field_name="文档类型",
            option_name="Web手册",
            run_lark_cli_json=run_lark_cli_json,
        )

        self.assertTrue(added)
        self.assertEqual(2, run_lark_cli_json.call_count)
        update_kwargs = run_lark_cli_json.call_args_list[1].kwargs
        update_args = update_kwargs["args"]
        self.assertIn("+field-update", update_args)
        self.assertIn("fld_doc_type", update_args)
        payload = json.loads(update_args[update_args.index("--json") + 1])
        self.assertEqual(
            ["User Manual", "取扱説明書", "Web手册"],
            [option["name"] for option in payload["options"]],
        )
        self.assertNotIn("multiple", payload)

    def test_should_carry_the_multiple_flag_for_multi_select_fields(self) -> None:
        list_payload = self._field_list_payload(
            field_id="fld_multi", field_name="颜色", options=["红"], multiple=True
        )
        run_lark_cli_json = mock.Mock(side_effect=[list_payload, {"code": 0, "data": {}}])

        ensure_select_option(
            cli_bin="lark-cli",
            identity="user",
            base_token="base_catalog",
            table_id="tbl_catalog",
            field_name="颜色",
            option_name="蓝",
            run_lark_cli_json=run_lark_cli_json,
        )

        payload = json.loads(run_lark_cli_json.call_args_list[1].kwargs["args"][-1])
        self.assertTrue(payload["multiple"])

    def test_should_raise_when_the_field_is_not_found(self) -> None:
        run_lark_cli_json = mock.Mock(return_value={"code": 0, "data": {"items": [], "total": 0}})

        with self.assertRaises(RuntimeError):
            ensure_select_option(
                cli_bin="lark-cli",
                identity="user",
                base_token="base_catalog",
                table_id="tbl_catalog",
                field_name="文档类型",
                option_name="Web手册",
                run_lark_cli_json=run_lark_cli_json,
            )


class FindCatalogCandidatesTests(unittest.TestCase):
    def test_should_match_on_model_region_lang_doc_type(self) -> None:
        rows = [
            manual_index_row_from_record(
                _catalog_record(
                    "rec_match",
                    models=["JE-1000F"],
                    region=["美加规"],
                    source_lang=["EN"],
                    doc_type=[CATALOG_WEB_DOC_TYPE],
                )
            ),
            manual_index_row_from_record(
                _catalog_record(
                    "rec_other_model",
                    models=["JE-2000F"],
                    region=["美加规"],
                    source_lang=["EN"],
                    doc_type=[CATALOG_WEB_DOC_TYPE],
                )
            ),
        ]

        candidates = find_catalog_candidates(
            rows, model="JE-1000F", region_label="美加规", lang_label="EN", doc_type=CATALOG_WEB_DOC_TYPE
        )

        self.assertEqual(("rec_match",), tuple(row.record_id for row in candidates))

    def test_should_split_comma_delimited_model_cells(self) -> None:
        rows = [
            manual_index_row_from_record(
                _catalog_record(
                    "rec_multi_model",
                    models=["JE-1000F, JE-2000F"],
                    region=["美加规"],
                    source_lang=["EN"],
                    doc_type=[CATALOG_WEB_DOC_TYPE],
                )
            )
        ]

        candidates = find_catalog_candidates(
            rows, model="JE-2000F", region_label="美加规", lang_label="EN", doc_type=CATALOG_WEB_DOC_TYPE
        )

        self.assertEqual(1, len(candidates))

    def test_should_return_empty_when_nothing_matches(self) -> None:
        rows = [
            manual_index_row_from_record(
                _catalog_record(
                    "rec_print_only",
                    models=["JE-1000F"],
                    region=["美加规"],
                    source_lang=["EN"],
                    doc_type=["User Manual"],
                )
            )
        ]

        candidates = find_catalog_candidates(
            rows, model="JE-1000F", region_label="美加规", lang_label="EN", doc_type=CATALOG_WEB_DOC_TYPE
        )

        self.assertEqual((), candidates)


class VerifyRecordFieldsTests(unittest.TestCase):
    def test_should_confirm_when_fields_match(self) -> None:
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = [
            _catalog_record("rec_1", manual_link="https://example.com/manual.html", version=["2.0"])
        ]

        result = verify_record_fields(
            source=source,
            base_token="base",
            table_id="tbl",
            view_id=None,
            record_id="rec_1",
            expected_fields={FIELD_MANUAL_LINK: "https://example.com/manual.html", FIELD_VERSION: "2.0"},
        )

        self.assertTrue(result.ok)

    def test_should_fail_when_a_field_mismatches(self) -> None:
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = [
            _catalog_record("rec_1", manual_link="https://stale.example.com", version=["2.0"])
        ]

        result = verify_record_fields(
            source=source,
            base_token="base",
            table_id="tbl",
            view_id=None,
            record_id="rec_1",
            expected_fields={FIELD_MANUAL_LINK: "https://example.com/manual.html"},
        )

        self.assertFalse(result.ok)
        self.assertIn("mismatch", result.detail)

    def test_should_fail_when_record_is_missing_after_write(self) -> None:
        source = mock.Mock()
        source.fetch_records_with_ids.return_value = []

        result = verify_record_fields(
            source=source,
            base_token="base",
            table_id="tbl",
            view_id=None,
            record_id="rec_missing",
            expected_fields={FIELD_MANUAL_LINK: "https://example.com/manual.html"},
        )

        self.assertFalse(result.ok)
        self.assertIn("did not find", result.detail)


class WriteCatalogRecordTests(unittest.TestCase):
    @staticmethod
    def _source() -> mock.Mock:
        source = mock.Mock()
        source.cli_bin = "lark-cli"
        source.identity = "user"
        return source

    def test_should_create_when_no_existing_row_matches(self) -> None:
        source = self._source()
        expected_notes = format_catalog_notes(
            version="2.0", link="https://ht-doc.readthedocs.io/manual_je1000f_us.html"
        )
        source.fetch_records_with_ids.side_effect = [
            [],  # search
            [
                _catalog_record(
                    "rec_new",
                    manual_link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                    version=[CATALOG_UNKNOWN_VERSION_LABEL],
                    notes=expected_notes,
                )
            ],  # readback
        ]
        source.create_record.return_value = "rec_new"

        with mock.patch.object(manual_catalog_writeback, "ensure_select_option") as ensure_mock:
            result = write_catalog_record(
                source=source,
                settings=SETTINGS,
                model="JE-1000F",
                region="US",
                lang="en",
                link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                version="2.0",
            )

        self.assertEqual("created", result.status)
        self.assertEqual("rec_new", result.record_id)
        create_kwargs = source.create_record.call_args.kwargs
        self.assertEqual(
            {
                FIELD_MODELS: "JE-1000F",
                FIELD_REGION: "美加规",
                FIELD_SOURCE_LANG: "EN",
                FIELD_DOC_TYPE: CATALOG_WEB_DOC_TYPE,
                FIELD_MANUAL_LINK: "https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                FIELD_VERSION: CATALOG_UNKNOWN_VERSION_LABEL,
                FIELD_NOTES: expected_notes,
            },
            create_kwargs["fields"],
        )
        source.upsert_record.assert_not_called()

        # Select-option pre-check ran for both target fields before the create.
        self.assertEqual(2, ensure_mock.call_count)
        checked = {call.kwargs["field_name"]: call.kwargs["option_name"] for call in ensure_mock.call_args_list}
        self.assertEqual(
            {FIELD_DOC_TYPE: CATALOG_WEB_DOC_TYPE, FIELD_VERSION: CATALOG_UNKNOWN_VERSION_LABEL},
            checked,
        )
        for call in ensure_mock.call_args_list:
            self.assertEqual("lark-cli", call.kwargs["cli_bin"])
            self.assertEqual("base_catalog", call.kwargs["base_token"])
            self.assertEqual("tbl_catalog", call.kwargs["table_id"])

    def test_should_update_link_and_notes_but_leave_version_untouched_when_one_row_matches(self) -> None:
        existing = _catalog_record(
            "rec_existing",
            models=["JE-1000F"],
            region=["美加规"],
            source_lang=["EN"],
            doc_type=[CATALOG_WEB_DOC_TYPE],
            manual_link="https://old.example.com",
            version=[CATALOG_UNKNOWN_VERSION_LABEL],
        )
        expected_notes = format_catalog_notes(
            version="2.0", link="https://ht-doc.readthedocs.io/manual_je1000f_us.html"
        )
        source = self._source()
        source.fetch_records_with_ids.side_effect = [
            [existing],  # search
            [
                _catalog_record(
                    "rec_existing",
                    manual_link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                    version=[CATALOG_UNKNOWN_VERSION_LABEL],
                    notes=expected_notes,
                )
            ],  # readback
        ]

        with mock.patch.object(manual_catalog_writeback, "ensure_select_option") as ensure_mock:
            result = write_catalog_record(
                source=source,
                settings=SETTINGS,
                model="JE-1000F",
                region="US",
                lang="en",
                link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                version="2.0",
            )

        self.assertEqual("updated", result.status)
        self.assertEqual("rec_existing", result.record_id)
        source.upsert_record.assert_called_once_with(
            base_token="base_catalog",
            table_id="tbl_catalog",
            record_id="rec_existing",
            record={FIELD_MANUAL_LINK: "https://ht-doc.readthedocs.io/manual_je1000f_us.html", FIELD_NOTES: expected_notes},
        )
        source.create_record.assert_not_called()
        # 版本 is not part of the update patch at all, and no option pre-check is needed
        # on the update path since no Select field value is being written.
        ensure_mock.assert_not_called()

    def test_should_reject_ambiguous_matches_without_writing(self) -> None:
        rows = [
            _catalog_record(
                "rec_a", models=["JE-1000F"], region=["美加规"], source_lang=["EN"], doc_type=[CATALOG_WEB_DOC_TYPE]
            ),
            _catalog_record(
                "rec_b", models=["JE-1000F"], region=["美加规"], source_lang=["EN"], doc_type=[CATALOG_WEB_DOC_TYPE]
            ),
        ]
        source = self._source()
        source.fetch_records_with_ids.return_value = rows

        result = write_catalog_record(
            source=source,
            settings=SETTINGS,
            model="JE-1000F",
            region="US",
            lang="en",
            link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
            version="2.0",
        )

        self.assertEqual("ambiguous", result.status)
        self.assertIn("rec_a", result.detail)
        self.assertIn("rec_b", result.detail)
        source.upsert_record.assert_not_called()
        source.create_record.assert_not_called()

    def test_should_fail_when_readback_does_not_confirm_the_write(self) -> None:
        source = self._source()
        source.fetch_records_with_ids.side_effect = [
            [],  # search
            [_catalog_record("rec_new", manual_link="https://stale.example.com", version=["1.0"])],  # readback
        ]
        source.create_record.return_value = "rec_new"

        with mock.patch.object(manual_catalog_writeback, "ensure_select_option"):
            result = write_catalog_record(
                source=source,
                settings=SETTINGS,
                model="JE-1000F",
                region="US",
                lang="en",
                link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                version="2.0",
            )

        self.assertEqual("failed", result.status)
        self.assertEqual("rec_new", result.record_id)
        self.assertIn("mismatch", result.detail)


if __name__ == "__main__":
    unittest.main()
