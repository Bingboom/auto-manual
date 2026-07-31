from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from tools.queue_orchestration import sync_phase2_snapshot_once


class TestQueueOrchestration(unittest.TestCase):
    def test_phase2_sync_is_memoized_for_same_config_and_data_root(self) -> None:
        sync = mock.Mock()
        memo: set[tuple[str, str]] = set()

        sync_phase2_snapshot_once(
            sync,
            memo=memo,
            config_path=Path("configs/config.us.yaml"),
            data_root="data/phase2",
        )
        sync_phase2_snapshot_once(
            sync,
            memo=memo,
            config_path=Path("configs/config.us.yaml"),
            data_root="data/phase2",
        )

        sync.assert_called_once_with(
            config_path=Path("configs/config.us.yaml"),
            data_root="data/phase2",
        )

    def test_phase2_sync_runs_again_for_a_different_config_or_data_root(self) -> None:
        sync = mock.Mock()
        memo: set[tuple[str, str]] = set()

        for config_path, data_root in (
            (Path("configs/config.us.yaml"), "data/phase2"),
            (Path("configs/config.ja.yaml"), "data/phase2"),
            (Path("configs/config.us.yaml"), "data/phase2-next"),
        ):
            sync_phase2_snapshot_once(
                sync,
                memo=memo,
                config_path=config_path,
                data_root=data_root,
            )

        self.assertEqual(3, sync.call_count)

    def test_failed_phase2_sync_is_not_memoized(self) -> None:
        sync = mock.Mock(side_effect=[RuntimeError("sync failed"), None])
        memo: set[tuple[str, str]] = set()
        kwargs = {
            "memo": memo,
            "config_path": Path("configs/config.us.yaml"),
            "data_root": "data/phase2",
        }

        with self.assertRaisesRegex(RuntimeError, "sync failed"):
            sync_phase2_snapshot_once(sync, **kwargs)
        sync_phase2_snapshot_once(sync, **kwargs)

        self.assertEqual(2, sync.call_count)
        self.assertEqual({("configs/config.us.yaml", "data/phase2")}, memo)


if __name__ == "__main__":
    unittest.main()
