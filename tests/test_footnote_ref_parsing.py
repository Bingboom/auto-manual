from __future__ import annotations

import json
import unittest

from tools.spec_master_sources import (
    collect_footnote_record_id_refs,
    normalize_footnote_ref_value,
    record_id_from_ref_token,
)

# A Feishu-shaped record id: `rec` + >=10 base62 chars, no underscore.
_REC = "recAbc123Def45"
_REC2 = "recZy9Xw8Vu7Ts"


class RecordIdFromRefTokenTests(unittest.TestCase):
    def test_dict_token_returns_id_regardless_of_shape(self) -> None:
        self.assertEqual(record_id_from_ref_token({"id": _REC}), _REC)
        # multi-key link dict — the id is still recovered
        self.assertEqual(record_id_from_ref_token({"id": _REC, "text": "1"}), _REC)

    def test_feishu_shaped_bare_string_is_a_record_id(self) -> None:
        self.assertEqual(record_id_from_ref_token(_REC), _REC)

    def test_literal_footnote_id_starting_with_rec_is_not_a_record_id(self) -> None:
        # the reported false-match: business ids that merely start with "rec"
        self.assertIsNone(record_id_from_ref_token("recharge_time"))
        self.assertIsNone(record_id_from_ref_token("recycle_note"))
        self.assertIsNone(record_id_from_ref_token("recycle"))

    def test_plain_literal_is_not_a_record_id(self) -> None:
        self.assertIsNone(record_id_from_ref_token("ac_bypass"))

    def test_json_object_string_returns_id(self) -> None:
        self.assertEqual(record_id_from_ref_token(json.dumps({"id": _REC})), _REC)


class CollectFootnoteRecordIdRefsTests(unittest.TestCase):
    def test_multi_key_json_cell_is_not_shredded(self) -> None:
        # `_coerce_scalar` serializes a link cell as json.dumps(item); a multi-key
        # dict must not be split on its internal comma.
        cell = json.dumps({"id": _REC, "text": "footnote 1"})
        refs = collect_footnote_record_id_refs([{"Param_footnote_refs": cell}])
        self.assertEqual(refs, [_REC])

    def test_two_joined_records_both_collected(self) -> None:
        cell = ", ".join([json.dumps({"id": _REC}), json.dumps({"id": _REC2})])
        refs = collect_footnote_record_id_refs([{"Value_footnote_refs": cell}])
        self.assertEqual(refs, [_REC, _REC2])

    def test_literal_ids_collect_nothing(self) -> None:
        # a rec-prefixed literal must NOT be collected as an unresolvable ref
        rows = [{"Row_label_footnote_refs": "ac_bypass, recharge_time"}]
        self.assertEqual(collect_footnote_record_id_refs(rows), [])


class NormalizeFootnoteRefValueTests(unittest.TestCase):
    def test_multi_key_dict_resolves_via_mapping(self) -> None:
        cell = json.dumps({"id": _REC, "text": "x"})
        self.assertEqual(normalize_footnote_ref_value(cell, {_REC: "ac_bypass"}), "ac_bypass")

    def test_two_records_resolve_and_dedupe(self) -> None:
        cell = ", ".join([json.dumps({"id": _REC}), json.dumps({"id": _REC2})])
        out = normalize_footnote_ref_value(cell, {_REC: "ac_bypass", _REC2: "max_charge"})
        self.assertEqual(out, "ac_bypass, max_charge")

    def test_literal_passes_through_unchanged(self) -> None:
        self.assertEqual(normalize_footnote_ref_value("ac_bypass", {_REC: "x"}), "ac_bypass")


if __name__ == "__main__":
    unittest.main()
