from __future__ import annotations

import unittest

from tools.build_queue import artifact_sink as queue_artifact_sink


class TestQueueArtifactSink(unittest.TestCase):
    def test_collect_artifact_sink_preflight_errors_should_reject_dingtalk_provider(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            }
        }

        errors = queue_artifact_sink.collect_artifact_sink_preflight_errors(cfg, environ={})

        self.assertEqual(1, len(errors))
        self.assertIn("Unsupported queue artifact sink provider", errors[0])
        self.assertIn("dingtalk", errors[0])

    def test_collect_artifact_sink_preflight_errors_should_reject_dingtalk_mirror_provider(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                    "mirror_provider": "dingtalk_alidocs_session",
                }
            }
        }

        errors = queue_artifact_sink.collect_artifact_sink_preflight_errors(cfg, environ={})

        self.assertEqual(1, len(errors))
        self.assertIn("Unsupported queue artifact sink provider", errors[0])

    def test_collect_artifact_sink_preflight_errors_should_accept_lark_drive(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                }
            }
        }

        errors = queue_artifact_sink.collect_artifact_sink_preflight_errors(cfg, environ={})

        self.assertEqual([], errors)

    def test_artifact_sink_provider_should_default_to_lark_drive(self) -> None:
        self.assertEqual("lark_drive", queue_artifact_sink.artifact_sink_provider({}, environ={}))

    def test_artifact_sink_provider_should_accept_aliases(self) -> None:
        for alias in ("lark", "feishu", "lark_drive", "lark-drive"):
            self.assertEqual(
                "lark_drive",
                queue_artifact_sink.artifact_sink_provider(
                    {"queue": {"artifact_sink": {"provider": alias}}},
                    environ={},
                ),
            )

    def test_artifact_sink_provider_should_reject_unsupported(self) -> None:
        for unsupported in ("dingtalk", "dingtalk_alidocs_session", "unknown"):
            with self.assertRaisesRegex(RuntimeError, "Unsupported queue artifact sink provider"):
                queue_artifact_sink.artifact_sink_provider(
                    {"queue": {"artifact_sink": {"provider": unsupported}}},
                    environ={},
                )

    def test_artifact_mirror_provider_should_resolve_disabled_values(self) -> None:
        for disabled in ("none", "off", "disabled", "false", "no", ""):
            self.assertIsNone(
                queue_artifact_sink.artifact_mirror_provider(
                    {"queue": {"artifact_sink": {"mirror_provider": disabled}}},
                    environ={},
                )
            )

    def test_artifact_mirror_provider_should_reject_unsupported(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Unsupported queue artifact sink provider"):
            queue_artifact_sink.artifact_mirror_provider(
                {"queue": {"artifact_sink": {"mirror_provider": "dingtalk"}}},
                environ={},
            )

    def test_resolve_artifact_destination_should_return_lark_destination(self) -> None:
        dest = queue_artifact_sink.resolve_artifact_destination(
            {"queue": {"artifact_sink": {"provider": "lark_drive"}}},
            environ={},
            space_id="spc123",
        )
        self.assertEqual("lark_drive", dest.provider)
        self.assertEqual("spc123", dest.details.get("space_id"))

    def test_resolve_artifact_destination_should_reject_unsupported(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Unsupported queue artifact sink provider"):
            queue_artifact_sink.resolve_artifact_destination(
                {"queue": {"artifact_sink": {"provider": "dingtalk"}}},
                environ={},
            )


if __name__ == "__main__":
    unittest.main()
