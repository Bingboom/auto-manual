from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import publish_branch_assembly, write_web_publish_receipt_links as receipt_links


def write_release_target(
    root: Path,
    *,
    model: str,
    region: str,
    lang: str,
    version: str,
    queue_record_ids: list[str] | None,
) -> Path:
    """Minimal real release fixture accepted by the real assembler."""
    lang_root = root / "reports" / "releases" / model / region / lang
    web_root = lang_root / "versions" / version / "web"
    md_root = web_root / "md"
    html_root = web_root / "html"
    metadata_root = lang_root / "latest" / "web"
    for directory in (md_root, html_root, metadata_root):
        directory.mkdir(parents=True, exist_ok=True)
    manual_stem = f"manual_{model.lower().replace('-', '')}_{region.lower()}_{lang}"
    (md_root / f"{manual_stem}.md").write_text("# Manual\n", encoding="utf-8")
    (md_root / "conf.py").write_text('extensions = ["myst_parser"]\n', encoding="utf-8")
    (md_root / "index.md").write_text(
        f"# {model} {region}\n\n```{{toctree}}\n:maxdepth: 2\n\n{manual_stem}\n```\n",
        encoding="utf-8",
    )
    (html_root / "index.html").write_text("<html>verified</html>\n", encoding="utf-8")
    payload = {
        "schema_version": "auto-manual-web-publish/v1",
        "model": model,
        "region": region,
        "lang": lang,
        "version": version,
        "git_ref": f"review/{model}-{region}",
        "workflow_action": "Web Publish",
        "built_at": "2026-09-19T12:00:00+00:00",
        "md_output_path": (md_root / f"{manual_stem}.md").relative_to(root).as_posix(),
        "html_dir": html_root.relative_to(root).as_posix(),
        "html_index": (html_root / "index.html").relative_to(root).as_posix(),
    }
    if queue_record_ids is not None:
        payload["queue_record_ids"] = queue_record_ids
    (metadata_root / "publish_meta.json").write_text(
        json.dumps(payload) + "\n", encoding="utf-8"
    )
    return lang_root


class _RecordingSource:
    """Captures upsert_record calls in place of the real lark transport."""

    def __init__(self) -> None:
        self.upserts: list[tuple[str, str, str, dict[str, object]]] = []

    def upsert_record(self, *, base_token, table_id, record_id, record):
        self.upserts.append((base_token, table_id, record_id, dict(record)))
        return {"code": 0}


class _FieldStore:
    """Fake per-record field values with post-write visibility.

    ``render_as_link`` reads stored URLs back the way ``lark-cli base
    +record-get`` does for a Feishu text cell: as ``[url](url)``.
    """

    def __init__(
        self,
        initial: dict[str, str],
        field_name: str = "HTML_link",
        *,
        render_as_link: bool = False,
    ) -> None:
        self.values = dict(initial)
        self.field_name = field_name
        self.render_as_link = render_as_link
        self.reads: list[str] = []

    def attach(self, source: _RecordingSource) -> None:
        original = source.upsert_record

        def recording_upsert(*, base_token, table_id, record_id, record):
            result = original(
                base_token=base_token, table_id=table_id,
                record_id=record_id, record=record,
            )
            self.values[record_id] = str(record[self.field_name])
            return result

        source.upsert_record = recording_upsert

    def fetch(self, *, cli_bin, identity, base_token, table_id, record_id):
        self.reads.append(record_id)
        value = self.values.get(record_id, "")
        if self.render_as_link and value:
            value = f"[{value}]({value})"
        return {self.field_name: value}


class ReceiptLaneManifestTests(unittest.TestCase):
    """Real assembler -> real manifest -> receipt-lane target selection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory()
        root = Path(cls._tempdir.name)
        write_release_target(
            root, model="JE-1000F", region="US", lang="en", version="2.0",
            queue_record_ids=["rec_web_2", "rec_web_1"],
        )
        write_release_target(
            root, model="JE-500A", region="EU", lang="en", version="1.0",
            queue_record_ids=None,
        )
        cls.publish_root = root / "docs" / "publish"
        cls.manifest_path = publish_branch_assembly.assemble_web_publish_branch(
            repo_root=root,
            releases_root=root / "reports" / "releases",
            output_dir=cls.publish_root,
            title="Manual Library",
        )
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def test_registrable_targets_come_from_the_real_manifest_with_sorted_ids(self) -> None:
        targets = receipt_links.registrable_targets(
            self.manifest, manifest_path=self.manifest_path
        )
        self.assertEqual(1, len(targets))
        target = targets[0]
        self.assertEqual(("JE-1000F", "US", "en"), (target["model"], target["region"], target["lang"]))
        self.assertEqual(("rec_web_1", "rec_web_2"), target["queue_record_ids"])
        self.assertEqual(
            "JE-1000F/US/en/md/manual_je1000f_us_en.html", target["page"]
        )

    def test_explicit_record_filter_narrows_and_fails_closed(self) -> None:
        targets = receipt_links.registrable_targets(
            self.manifest, manifest_path=self.manifest_path
        )
        narrowed = receipt_links.filter_targets_by_record_ids(targets, ("rec_web_2",))
        self.assertEqual(("rec_web_2",), narrowed[0]["queue_record_ids"])
        with self.assertRaisesRegex(RuntimeError, "No registrable publish target matched"):
            receipt_links.filter_targets_by_record_ids(targets, ("rec_absent",))

    def _args(self, **overrides) -> object:
        argv = [
            "--config", "configs/config.us.yaml",
            "--publish-root", str(self.publish_root),
            "--base-url", "https://ht-doc.readthedocs.io",
            "--deploy-timeout-seconds", str(overrides.pop("deploy_timeout", 0)),
            "--poll-interval-seconds", "0",
        ]
        for record_id in overrides.pop("record_ids", ()):
            argv += ["--record-id", record_id]
        args = receipt_links.parse_args(argv)
        return args

    def _lark_patches(self):
        binding = SimpleNamespace(base_token="base_tok", table_id="tbl_link")
        return (
            mock.patch.object(receipt_links, "load_config", return_value={}),
            mock.patch.object(receipt_links, "collect_queue_preflight_errors", return_value=[]),
            mock.patch.object(receipt_links, "resolve_document_link_binding", return_value=binding),
            mock.patch.object(receipt_links, "cli_bin", return_value="lark-cli"),
            mock.patch.object(receipt_links, "phase2_identity", return_value="bot"),
            mock.patch.object(receipt_links, "fetch_field_id_map", return_value={"HTML_link": "fld1"}),
        )

    def _run(self, *, args, verify_fn, store: _FieldStore) -> tuple[int, dict, _RecordingSource]:
        source = _RecordingSource()
        store.attach(source)
        patches = self._lark_patches()
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        exit_code, report = receipt_links.run(
            args,
            verify_fn=verify_fn,
            sleep_fn=lambda _seconds: None,
            fetch_fields=store.fetch,
            lark_source_factory=lambda **_kwargs: source,
        )
        return exit_code, report, source

    @staticmethod
    def _verify_ok(web_root, *, base_url, targets, project_slug, session, include_dependency):
        return [
            {"model": t["model"], "region": t["region"], "lang": t["lang"],
             "page": t["page"], "mode": "frozen-source", "status": "ok"}
            for t in targets
        ]

    @staticmethod
    def _verify_with(status: str):
        def verify(web_root, *, base_url, targets, project_slug, session, include_dependency):
            return [
                {"model": t["model"], "region": t["region"], "lang": t["lang"],
                 "page": t["page"], "mode": "frozen-source", "status": status,
                 "error": f"forced {status}"}
                for t in targets
            ]
        return verify

    def test_run_registers_after_verification_with_same_record_readback(self) -> None:
        store = _FieldStore({"rec_web_1": "", "rec_web_2": "https://old.example/entry.html"})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual("registered", report["status"])
        self.assertEqual(2, report["records_written"])
        expected_url = (
            "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us_en.html"
        )
        self.assertEqual(
            [("base_tok", "tbl_link", "rec_web_1", {"HTML_link": expected_url}),
             ("base_tok", "tbl_link", "rec_web_2", {"HTML_link": expected_url})],
            source.upserts,
        )
        # read-before-write plus readback: two reads per written record.
        self.assertEqual(
            ["rec_web_1", "rec_web_1", "rec_web_2", "rec_web_2"], store.reads
        )

    def test_run_skips_records_whose_link_is_already_registered(self) -> None:
        url = "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us_en.html"
        store = _FieldStore({"rec_web_1": url, "rec_web_2": url})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual([], source.upserts)
        self.assertEqual(0, report["records_written"])
        self.assertEqual(2, report["records_already_registered"])

    def test_readback_mismatch_fails_instead_of_claiming_registration(self) -> None:
        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})

        def attach_noop(source: _RecordingSource) -> None:
            # The write "succeeds" but never becomes visible on read-back.
            return None

        store.attach = attach_noop  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
            self._run(args=self._args(), verify_fn=self._verify_ok, store=store)

    def test_link_segment_readback_verifies_the_registration(self) -> None:
        # Feishu keeps the written URL as a link segment; +record-get renders
        # it as [url](url). That is the registered value, not a mismatch.
        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""}, render_as_link=True)
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual("registered", report["status"])
        self.assertEqual(2, report["records_written"])
        expected_url = (
            "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us_en.html"
        )
        self.assertEqual(
            [{"HTML_link": expected_url}, {"HTML_link": expected_url}],
            [record for *_ids, record in source.upserts],
        )

    def test_link_segment_holding_the_url_is_already_registered(self) -> None:
        url = "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us_en.html"
        store = _FieldStore({"rec_web_1": url, "rec_web_2": url}, render_as_link=True)
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual([], source.upserts)
        self.assertEqual(2, report["records_already_registered"])

    def test_link_segment_to_another_url_still_fails_the_readback(self) -> None:
        store = _FieldStore(
            {"rec_web_1": "https://old.example/entry.html", "rec_web_2": ""},
            render_as_link=True,
        )
        store.attach = lambda source: None  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "readback mismatch.*old.example"):
            self._run(args=self._args(), verify_fn=self._verify_ok, store=store)

    def test_failed_verification_registers_nothing(self) -> None:
        store = _FieldStore({})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_with("failed"), store=store
        )
        self.assertEqual(1, exit_code)
        self.assertEqual("failed", report["status"])
        self.assertEqual([], source.upserts)
        self.assertEqual([], store.reads)

    def test_throttled_verification_is_undecided_tempfail(self) -> None:
        store = _FieldStore({})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_with("throttled"), store=store
        )
        self.assertEqual(75, exit_code)
        self.assertEqual("throttled", report["status"])
        self.assertEqual([], source.upserts)

    def test_polling_waits_until_the_deployment_verifies(self) -> None:
        attempts: list[int] = []

        def verify(web_root, *, base_url, targets, project_slug, session, include_dependency):
            attempts.append(1)
            status = "failed" if len(attempts) < 3 else "ok"
            entry = {"model": targets[0]["model"], "region": targets[0]["region"],
                     "lang": targets[0]["lang"], "page": targets[0]["page"],
                     "mode": "frozen-source", "status": status}
            if status != "ok":
                entry["error"] = "Live deployment does not match frozen source"
            return [entry]

        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        exit_code, report, _source = self._run(
            args=self._args(deploy_timeout=600),
            verify_fn=verify,
            store=store,
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(3, report["verify_attempts"])
        self.assertEqual("registered", report["status"])

    def test_no_registrable_targets_is_a_clean_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_release_target(
                root, model="JE-500A", region="EU", lang="en", version="1.0",
                queue_record_ids=None,
            )
            publish_root = root / "docs" / "publish"
            publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=root / "reports" / "releases",
                output_dir=publish_root,
                title="Manual Library",
            )
            args = receipt_links.parse_args(
                [
                    "--config", "configs/config.us.yaml",
                    "--publish-root", str(publish_root),
                    "--base-url", "https://ht-doc.readthedocs.io",
                ]
            )
            forbidden = mock.MagicMock(
                side_effect=AssertionError("no-queue-rows run must not verify or write")
            )
            exit_code, report = receipt_links.run(
                args,
                verify_fn=forbidden,
                fetch_fields=forbidden,
                lark_source_factory=forbidden,
            )
            self.assertEqual(0, exit_code)
            self.assertEqual("no-queue-rows", report["status"])
            forbidden.assert_not_called()


class FetchRecordFieldsTests(unittest.TestCase):
    def test_positional_arrays_map_to_field_names(self) -> None:
        payload = {
            "data": {
                "fields": ["Document_key", "HTML_link"],
                "data": [["JE-1000F_US", {"link": "https://x", "text": "https://x"}]],
            }
        }
        captured: dict[str, object] = {}

        def run_json(*, cli_bin, args):
            captured["args"] = args
            return payload

        fields = receipt_links.fetch_record_fields(
            cli_bin="lark-cli", identity="bot", base_token="base_tok",
            table_id="tbl_link", record_id="rec_1", run_json=run_json,
        )
        self.assertEqual("JE-1000F_US", fields["Document_key"])
        self.assertEqual({"link": "https://x", "text": "https://x"}, fields["HTML_link"])
        self.assertIn("+record-get", captured["args"])
        self.assertIn("rec_1", captured["args"])

    def test_invalid_shape_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "invalid shape"):
            receipt_links.fetch_record_fields(
                cli_bin="lark-cli", identity="bot", base_token="base_tok",
                table_id="tbl_link", record_id="rec_1",
                run_json=lambda **_kwargs: {"data": {"fields": ["A"], "data": []}},
            )


class RegisteredLinkTests(unittest.TestCase):
    URL = "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html"

    def test_reads_plain_and_link_rendered_cells_as_the_url(self) -> None:
        for value in (
            self.URL,
            f"  {self.URL}\n",
            f"[{self.URL}]({self.URL})",
            f"[Manual]({self.URL})",
            {"link": self.URL, "text": self.URL},
            [{"link": self.URL, "text": self.URL}],
        ):
            with self.subTest(value=value):
                self.assertEqual(self.URL, receipt_links.registered_link(value))

    def test_leaves_other_text_unchanged(self) -> None:
        self.assertEqual("", receipt_links.registered_link(None))
        self.assertEqual("", receipt_links.registered_link(""))
        # Only a cell that is exactly one link is unwrapped.
        text = f"see [{self.URL}]({self.URL})"
        self.assertEqual(text, receipt_links.registered_link(text))


if __name__ == "__main__":
    unittest.main()
