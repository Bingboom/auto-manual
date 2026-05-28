from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.page_copy import load_page_copy_map


class PageCopyTests(unittest.TestCase):
    def test_load_page_copy_map_rejects_legacy_tip_key(self) -> None:
        with TemporaryDirectory() as td:
            page_copy = Path(td) / "page_copy.csv"
            page_copy.write_text(
                "\n".join(
                    [
                        "page_id,lang,copy_key,text,enabled,order",
                        "alert_labels,,tip,TIP,1,10",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "use copy_key='tips'"):
                load_page_copy_map("alert_labels", "", csv_path=str(page_copy))

    def test_load_page_copy_map_accepts_tips_key(self) -> None:
        with TemporaryDirectory() as td:
            page_copy = Path(td) / "page_copy.csv"
            page_copy.write_text(
                "\n".join(
                    [
                        "page_id,lang,copy_key,text,enabled,order",
                        "alert_labels,,tips,TIPS,1,10",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual("TIPS", load_page_copy_map("alert_labels", "", csv_path=str(page_copy))["tips"])


if __name__ == "__main__":
    unittest.main()
