from __future__ import annotations

import unittest

from tools import queue_artifact_sink


class TestQueueArtifactSink(unittest.TestCase):
    def test_collect_artifact_sink_preflight_errors_should_require_dingtalk_session_envs_but_not_target_url_env(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            }
        }

        errors = queue_artifact_sink.collect_artifact_sink_preflight_errors(cfg, environ={})

        self.assertEqual(1, len(errors))
        self.assertIn("DINGTALK_DOCS_A_TOKEN", errors[0])
        self.assertIn("DINGTALK_DOCS_XSRF_TOKEN", errors[0])
        self.assertIn("DINGTALK_DOCS_COOKIE", errors[0])

    def test_resolve_dingtalk_artifact_destination_should_parse_target_node_url(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            }
        }
        environ = {
            "DINGTALK_DOCS_TARGET_NODE_URL": "https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space",
            "DINGTALK_DOCS_A_TOKEN": "token",
            "DINGTALK_DOCS_XSRF_TOKEN": "xsrf",
            "DINGTALK_DOCS_COOKIE": "cookie=value",
        }

        destination = queue_artifact_sink.resolve_dingtalk_artifact_destination(cfg, environ=environ)

        self.assertEqual("dingtalk_alidocs_session", destination.provider)
        self.assertEqual("NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY", destination.details["target_node_id"])
        self.assertEqual(environ["DINGTALK_DOCS_TARGET_NODE_URL"], destination.runtime_target)

    def test_resolve_dingtalk_artifact_destination_should_prefer_explicit_target_node_url(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            }
        }
        environ = {
            "DINGTALK_DOCS_TARGET_NODE_URL": "https://alidocs.dingtalk.com/i/nodes/defaultNode?utm_scene=team_space",
            "DINGTALK_DOCS_A_TOKEN": "token",
            "DINGTALK_DOCS_XSRF_TOKEN": "xsrf",
            "DINGTALK_DOCS_COOKIE": "cookie=value",
        }
        explicit_target = "https://alidocs.dingtalk.com/i/nodes/rowNode123?utm_scene=team_space"

        destination = queue_artifact_sink.resolve_dingtalk_artifact_destination(
            cfg,
            environ=environ,
            target_node_url=explicit_target,
        )

        self.assertEqual(explicit_target, destination.runtime_target)
        self.assertEqual("rowNode123", destination.details["target_node_id"])


if __name__ == "__main__":
    unittest.main()
