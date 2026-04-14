from __future__ import annotations

import unittest

from tools.dingtalk import workspace


class TestDingTalkWorkspace(unittest.TestCase):
    def test_normalize_node_url_should_unwrap_markdown_link_target(self) -> None:
        raw = (
            "[https://alidocs.dingtalk.com/i/nodes/LeBq413JAw6ZqaOQUBxLL332WDOnGvpb?utm_scene=team_space]"
            "(https://alidocs.dingtalk.com/i/nodes/LeBq413JAw6ZqaOQUBxLL332WDOnGvpb?utm_scene=team_space)"
        )

        normalized = workspace.normalize_node_url(raw)

        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/LeBq413JAw6ZqaOQUBxLL332WDOnGvpb?utm_scene=team_space",
            normalized,
        )

    def test_parse_node_id_from_url_should_extract_node(self) -> None:
        node_id = workspace.parse_node_id_from_url(
            "https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space"
        )

        self.assertEqual("NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY", node_id)

    def test_parse_node_id_from_url_should_extract_node_from_markdown_link(self) -> None:
        node_id = workspace.parse_node_id_from_url(
            "[folder](https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space)"
        )

        self.assertEqual("NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY", node_id)

    def test_workspace_target_from_url_should_preserve_source_url(self) -> None:
        url = "https://alidocs.dingtalk.com/i/nodes/gvNG4YZ7JneBaO2OfqPKZ5N6V2LD0oRE?iframeQuery=entrance%3Ddata"

        target = workspace.workspace_target_from_url(url)

        self.assertEqual("gvNG4YZ7JneBaO2OfqPKZ5N6V2LD0oRE", target.node_id)
        self.assertEqual(url, target.source_url)

    def test_parse_node_id_from_url_should_raise_for_non_node_url(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Could not resolve DingTalk workspace node ID"):
            workspace.parse_node_id_from_url("https://alidocs.dingtalk.com/i/spaces/demo")
