from __future__ import annotations

import unittest

from tools.idml.stable_ids import apply_stable_labels


class StableIdTests(unittest.TestCase):
    def test_labels_editable_objects_and_is_idempotent(self) -> None:
        source = (
            '<Spread Self="sp_1"><Page Self="pg_1"/>'
            '<TextFrame Self="tf_1" ParentStory="st_1"/>'
            '<Rectangle Self="rc_1"/><Story Self="st_1"/></Spread>'
        )
        labeled = apply_stable_labels(source)
        for object_id in ("sp_1", "pg_1", "tf_1", "rc_1", "st_1"):
            self.assertIn(f'Label="hb:self={object_id}"', labeled)
        self.assertEqual(labeled, apply_stable_labels(labeled))


if __name__ == "__main__":
    unittest.main()
