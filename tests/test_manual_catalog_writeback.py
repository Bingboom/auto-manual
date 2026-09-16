from __future__ import annotations

import unittest
from typing import Any
from unittest import mock

from tools.manual_catalog_writeback import (
    CATALOG_WEB_DOC_TYPE,
    find_catalog_candidates,
    resolve_catalog_lang_label,
    resolve_catalog_region_label,
    verify_record_fields,
    write_catalog_record,
)
from tools.manual_index_query import (
    FIELD_DOC_TYPE,
    FIELD_MANUAL_LINK,
    FIELD_MODELS,
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


class FindCatalogCandidatesTests(unittest.TestCase):
    def test_should_match_on_model_region_lang_doc_type(self) -> None:
        rows = [
            manual_index_row_from_record(
                _catalog_record(
                    "rec_match",
                    models=["JE-1000F"],
                    region=["美加规"],
                    source_lang=["EN"],
                    doc_type=["web"],
                )
            ),
            manual_index_row_from_record(
                _catalog_record(
                    "rec_other_model",
                    models=["JE-2000F"],
                    region=["美加规"],
                    source_lang=["EN"],
                    doc_type=["web"],
                )
            ),
        ]

        candidates = find_catalog_candidates(
            rows, model="JE-1000F", region_label="美加规", lang_label="EN", doc_type="web"
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
                    doc_type=["web"],
                )
            )
        ]

        candidates = find_catalog_candidates(
            rows, model="JE-2000F", region_label="美加规", lang_label="EN", doc_type="web"
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
    def test_should_create_when_no_existing_row_matches(self) -> None:
        source = mock.Mock()
        source.fetch_records_with_ids.side_effect = [
            [],  # search
            [
                _catalog_record(
                    "rec_new",
                    manual_link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                    version=["2.0"],
                )
            ],  # readback
        ]
        source.create_record.return_value = "rec_new"

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
                FIELD_VERSION: "2.0",
            },
            create_kwargs["fields"],
        )
        source.upsert_record.assert_not_called()

    def test_should_update_link_and_version_when_one_row_matches(self) -> None:
        existing = _catalog_record(
            "rec_existing",
            models=["JE-1000F"],
            region=["美加规"],
            source_lang=["EN"],
            doc_type=["web"],
            manual_link="https://old.example.com",
            version=["1.0"],
        )
        source = mock.Mock()
        source.fetch_records_with_ids.side_effect = [
            [existing],  # search
            [
                _catalog_record(
                    "rec_existing",
                    manual_link="https://ht-doc.readthedocs.io/manual_je1000f_us.html",
                    version=["2.0"],
                )
            ],  # readback
        ]

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
            record={FIELD_MANUAL_LINK: "https://ht-doc.readthedocs.io/manual_je1000f_us.html", FIELD_VERSION: "2.0"},
        )
        source.create_record.assert_not_called()

    def test_should_reject_ambiguous_matches_without_writing(self) -> None:
        rows = [
            _catalog_record(
                "rec_a", models=["JE-1000F"], region=["美加规"], source_lang=["EN"], doc_type=["web"]
            ),
            _catalog_record(
                "rec_b", models=["JE-1000F"], region=["美加规"], source_lang=["EN"], doc_type=["web"]
            ),
        ]
        source = mock.Mock()
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
        source = mock.Mock()
        source.fetch_records_with_ids.side_effect = [
            [],  # search
            [_catalog_record("rec_new", manual_link="https://stale.example.com", version=["1.0"])],  # readback
        ]
        source.create_record.return_value = "rec_new"

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
