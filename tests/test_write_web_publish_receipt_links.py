from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import publish_branch_assembly, write_web_publish_receipt_links as receipt_links
from tools.rtd import deployment_receipt as receipt
from tools.rtd import private_build_verify as private_verify
from tools.web.document_link_queue import (
    describe_url_field,
    split_rendered_url,
    url_field_matches,
)


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
    """Fake per-record field values with post-write visibility."""

    def __init__(self, initial: dict[str, str], field_name: str = "HTML_link") -> None:
        self.values = dict(initial)
        self.field_name = field_name
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
        return {self.field_name: self.values.get(record_id, "")}


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
        if "changed_since" in overrides:
            argv += ["--changed-since", overrides.pop("changed_since")]
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

    def _run(
        self, *, args, verify_fn, store: _FieldStore, changed_paths: list[str] | None = None
    ) -> tuple[int, dict, _RecordingSource]:
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
            changed_paths_fn=(lambda _root, _since: list(changed_paths or ())),
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

    # --- push scope: only the targets this push changed -------------------

    SINCE = "e027ead1" + "0" * 32
    QUEUE_PAGE = "web/JE-1000F/US/en/md/manual_je1000f_us_en.md"
    GIT_ONLY_PAGE = "web/JE-500A/EU/en/md/manual_je500a_eu_en.md"

    @staticmethod
    def _recording_verify(seen: list[str]):
        def verify(web_root, *, base_url, targets, project_slug, session, include_dependency):
            seen.extend("/".join((t["model"], t["region"], t["lang"])) for t in targets)
            return ReceiptLaneManifestTests._verify_ok(
                web_root, base_url=base_url, targets=targets, project_slug=project_slug,
                session=session, include_dependency=include_dependency,
            )
        return verify

    def test_push_verifies_a_changed_git_only_target_without_touching_feishu(self) -> None:
        seen: list[str] = []
        forbidden = mock.MagicMock(
            side_effect=AssertionError("a Git-only push must not read or write Feishu")
        )
        exit_code, report = receipt_links.run(
            self._args(changed_since=self.SINCE),
            verify_fn=self._recording_verify(seen),
            sleep_fn=lambda _seconds: None,
            fetch_fields=forbidden,
            lark_source_factory=forbidden,
            changed_paths_fn=lambda _root, _since: [
                self.GIT_ONLY_PAGE,
                "sources/web/JE-500A/EU/en/md/source.json",
                "web/_static/manual-assets/_pool/ab/" + "ab" * 32 + ".png",
                "publish_manifest.json",
            ],
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(["JE-500A/EU/en"], seen)
        self.assertEqual("registered", report["status"])
        self.assertEqual(["JE-500A/EU/en"], report["scope"]["changed_targets"])
        self.assertEqual(0, report["scope"]["shared_path_count"])
        self.assertEqual([], report["targets"][0]["records"])
        forbidden.assert_not_called()

    def test_push_registers_only_the_changed_queue_backed_target(self) -> None:
        seen: list[str] = []
        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        exit_code, report, source = self._run(
            args=self._args(changed_since=self.SINCE),
            verify_fn=self._recording_verify(seen),
            store=store,
            changed_paths=[self.QUEUE_PAGE],
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(["JE-1000F/US/en"], seen)
        self.assertEqual(
            ["rec_web_1", "rec_web_2"], [upsert[2] for upsert in source.upserts]
        )

    def test_shared_change_also_verifies_every_queue_backed_target(self) -> None:
        seen: list[str] = []
        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        exit_code, report, source = self._run(
            args=self._args(changed_since=self.SINCE),
            verify_fn=self._recording_verify(seen),
            store=store,
            changed_paths=[self.GIT_ONLY_PAGE, "web/_static/web_manual.css"],
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(["JE-1000F/US/en", "JE-500A/EU/en"], seen)
        self.assertEqual(["JE-500A/EU/en"], report["scope"]["changed_targets"])
        self.assertEqual(["web/_static/web_manual.css"], report["scope"]["shared_paths"])
        # Only the queue-backed target has rows to register.
        self.assertEqual(2, report["records_written"])

    def test_push_without_a_changed_target_verifies_nothing(self) -> None:
        forbidden = mock.MagicMock(side_effect=AssertionError("nothing changed"))
        exit_code, report = receipt_links.run(
            self._args(changed_since=self.SINCE),
            verify_fn=forbidden,
            fetch_fields=forbidden,
            lark_source_factory=forbidden,
            changed_paths_fn=lambda _root, _since: ["publish_manifest.json", "web/index.md"],
        )
        self.assertEqual(0, exit_code)
        self.assertEqual("no-changed-targets", report["status"])
        forbidden.assert_not_called()

    def test_changed_since_cannot_be_combined_with_record_ids(self) -> None:
        args = self._args(changed_since=self.SINCE, record_ids=["rec_web_1"])
        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            receipt_links.run(args, changed_paths_fn=lambda _root, _since: [])

    # --- url-field rendering (Hello-Docs run 35492573107) -------------------
    # HTML_link is a Bitable ``url``-type field: lark-cli reads a stored URL
    # back as ``[url](url)``. The lane must accept that rendering and still
    # reject a pair whose halves disagree.

    RENDERED_URL = (
        "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us_en.html"
    )

    def _rendering_store(self, initial: dict[str, str]) -> _FieldStore:
        """A store whose writes become visible in the CLI's rendered form."""
        store = _FieldStore(initial)

        def attach(source: _RecordingSource) -> None:
            inner = source.upsert_record

            def rendering_upsert(*, base_token, table_id, record_id, record):
                result = inner(
                    base_token=base_token, table_id=table_id,
                    record_id=record_id, record=record,
                )
                value = str(record[store.field_name])
                store.values[record_id] = f"[{value}]({value})"
                return result

            source.upsert_record = rendering_upsert

        store.attach = attach  # type: ignore[method-assign]
        return store

    def test_rendered_readback_is_accepted_as_registered(self) -> None:
        store = self._rendering_store({"rec_web_1": "", "rec_web_2": ""})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual("registered", report["status"])
        self.assertEqual(2, report["records_written"])
        # The write still carries the bare URL; only the readback is rendered.
        self.assertEqual(
            [{"HTML_link": self.RENDERED_URL}, {"HTML_link": self.RENDERED_URL}],
            [upsert[3] for upsert in source.upserts],
        )

    def test_rerun_over_a_rendered_row_is_idempotent(self) -> None:
        rendered = f"[{self.RENDERED_URL}]({self.RENDERED_URL})"
        store = _FieldStore({"rec_web_1": rendered, "rec_web_2": rendered})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual([], source.upserts)
        self.assertEqual(0, report["records_written"])
        self.assertEqual(2, report["records_already_registered"])

    def test_rendered_pair_pointing_elsewhere_still_fails_the_readback(self) -> None:
        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})

        def attach(source: _RecordingSource) -> None:
            inner = source.upsert_record

            def wrong_upsert(*, base_token, table_id, record_id, record):
                result = inner(
                    base_token=base_token, table_id=table_id,
                    record_id=record_id, record=record,
                )
                # Halves that disagree are a real difference, not the CLI
                # rendering artifact: the lane must stay red.
                store.values[record_id] = (
                    f"[{record[store.field_name]}](https://wrong.example/x.html)"
                )
                return result

            source.upsert_record = wrong_upsert

        store.attach = attach  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "readback mismatch") as caught:
            self._run(args=self._args(), verify_fn=self._verify_ok, store=store)
        self.assertIn("https://wrong.example/x.html", str(caught.exception))

    def test_titled_link_to_the_page_is_rewritten_to_the_canonical_url(self) -> None:
        # Only the CLI rendering shape counts as registered: a hand-titled
        # link to the right page is rewritten to the bare canonical URL.
        titled = f"[Manual]({self.RENDERED_URL})"
        store = self._rendering_store({"rec_web_1": titled, "rec_web_2": titled})
        exit_code, report, source = self._run(
            args=self._args(), verify_fn=self._verify_ok, store=store
        )
        self.assertEqual(0, exit_code)
        self.assertEqual(2, report["records_written"])
        self.assertEqual(
            [{"HTML_link": self.RENDERED_URL}, {"HTML_link": self.RENDERED_URL}],
            [upsert[3] for upsert in source.upserts],
        )


class ChangedTargetScopeTests(unittest.TestCase):
    PAYLOAD = {
        "targets": [
            {"model": "JE-1000F", "region": "US", "lang": "en",
             "legacy_default": True, "legacy_route": "JE-1000F/US/md"},
            {"model": "JE-1000F", "region": "US", "lang": "es",
             "legacy_route": "JE-1000F/US/md"},
            {"model": "JE-500A", "region": "EU", "lang": "en"},
        ]
    }

    def test_paths_map_to_their_target_or_stay_shared(self) -> None:
        changed, shared = receipt_links.changed_target_scope(
            self.PAYLOAD,
            [
                "web/JE-1000F/US/es/md/manual_je1000f_us_es.md",
                "sources/web/JE-500A/EU/en/md/source.json",
                # The legacy region route belongs to the default target only.
                "web/JE-1000F/US/md/index.md",
                # Pool, catalog, library index and alias pages widen nothing.
                "web/_static/manual-assets/_pool/0b/" + "0b" * 32 + ".png",
                "publish_manifest.json",
                "web/index.md",
                "web/manual_je500a_eu_en.md",
                # Shared files and routes no target owns widen the scope.
                "web/_static/web_manual.css",
                "web/conf.py",
                "web/JE-9999X/US/en/md/orphan.md",
            ],
        )
        self.assertEqual(
            {("JE-1000F", "US", "es"), ("JE-500A", "EU", "en"), ("JE-1000F", "US", "en")},
            changed,
        )
        self.assertEqual(
            ["web/_static/web_manual.css", "web/conf.py", "web/JE-9999X/US/en/md/orphan.md"],
            shared,
        )

    def test_a_route_prefix_needs_the_path_separator(self) -> None:
        changed, shared = receipt_links.changed_target_scope(
            self.PAYLOAD, ["web/JE-500A/EU/en-GB/md/manual.md"]
        )
        self.assertEqual(set(), changed)
        self.assertEqual(["web/JE-500A/EU/en-GB/md/manual.md"], shared)


class ChangedPublishPathsTests(unittest.TestCase):
    """The diff runs against a real repository: renames count on both routes."""

    def _git(self, repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
             *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def test_lists_publish_relative_changes_since_the_base_commit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            publish_root = repo / "docs" / "publish"
            old_page = publish_root / "web" / "A" / "US" / "en" / "md" / "old.md"
            kept = publish_root / "web" / "B" / "US" / "en" / "md" / "kept.md"
            for path in (old_page, kept):
                path.parent.mkdir(parents=True)
                path.write_text("v1\n", encoding="utf-8")
            self._git(repo, "init", "-q")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-q", "-m", "base")
            base = self._git(repo, "rev-parse", "HEAD")
            self._git(repo, "mv", str(old_page), str(old_page.with_name("new.md")))
            (repo / "outside.txt").write_text("not published\n", encoding="utf-8")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-q", "-m", "rename")

            self.assertEqual(
                ["web/A/US/en/md/new.md", "web/A/US/en/md/old.md"],
                receipt_links.changed_publish_paths(publish_root, base),
            )
            with self.assertRaisesRegex(ValueError, "40-character commit SHA"):
                receipt_links.changed_publish_paths(publish_root, "HEAD~1")
            with self.assertRaisesRegex(RuntimeError, "Cannot list publish changes"):
                receipt_links.changed_publish_paths(publish_root, "f" * 40)


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


class UrlFieldReadbackNormalizationTests(unittest.TestCase):
    """``HTML_link`` is a ``url``-type field; lark-cli reads it back rendered.

    The normalization absorbs exactly that rendering artifact. It must not
    absorb a real difference, so a ``[label](target)`` pair whose halves
    disagree never matches — not even when one half is the expected URL.
    """

    URL = "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html"

    def test_plain_string_equal_matches(self) -> None:
        self.assertTrue(url_field_matches(self.URL, self.URL))

    def test_plain_string_different_fails(self) -> None:
        self.assertFalse(url_field_matches("https://other.example/x.html", self.URL))

    def test_cli_rendered_pair_matches(self) -> None:
        """The exact shape that reddened Hello-Docs run 35492573107."""
        self.assertTrue(url_field_matches(f"[{self.URL}]({self.URL})", self.URL))

    def test_rendered_pair_with_disagreeing_halves_fails(self) -> None:
        self.assertFalse(
            url_field_matches("[https://a.example/a.html](https://b.example/b.html)", self.URL)
        )

    def test_rendered_pair_matching_only_one_half_fails(self) -> None:
        # Fail-closed: a label or target that alone equals the expected URL is
        # not the CLI rendering shape, so it stays a real difference.
        self.assertFalse(url_field_matches(f"[a label]({self.URL})", self.URL))
        self.assertFalse(url_field_matches(f"[{self.URL}](https://b.example/b.html)", self.URL))

    def test_empty_and_missing_values_never_match(self) -> None:
        self.assertFalse(url_field_matches("", self.URL))
        self.assertFalse(url_field_matches(None, self.URL))

    def test_split_rendered_url_reports_the_parsed_halves(self) -> None:
        self.assertEqual(
            ("https://a.example/a.html", "https://b.example/b.html"),
            split_rendered_url("[https://a.example/a.html](https://b.example/b.html)"),
        )
        self.assertIsNone(split_rendered_url(self.URL))

    def test_description_exposes_both_halves_of_a_mismatching_pair(self) -> None:
        described = describe_url_field("[https://a.example/a.html](https://b.example/b.html)")
        self.assertIn("https://a.example/a.html", described)
        self.assertIn("https://b.example/b.html", described)
        self.assertIn("link target", described)


class PrivateRtdReceiptLaneTests(unittest.TestCase):
    """End-to-end receipt lane tests against a private /cas/login RTD Business site."""

    BUSINESS_BASE_URL = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"
    CAS_LOGIN = "https://app.readthedocs.com/cas/login"

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_release_target(
            self.root,
            model="JE-1000F",
            region="US",
            lang="en",
            version="2.0",
            queue_record_ids=["rec_web_1", "rec_web_2"],
        )
        self.publish_root = self.root / "docs" / "publish"
        publish_branch_assembly.assemble_web_publish_branch(
            repo_root=self.root,
            releases_root=self.root / "reports" / "releases",
            output_dir=self.publish_root,
            title="Manual Library",
        )
        subprocess.run(["git", "-C", str(self.root), "init"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Test User"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "add", "docs/publish"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-m", "feat(publish): add manual"],
            check=True,
            capture_output=True,
        )
        self.commit_sha = subprocess.check_output(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True
        ).strip()

    def _args(self, *, deploy_timeout: float = 1800) -> object:
        return receipt_links.parse_args(
            [
                "--config",
                "configs/config.us.yaml",
                "--publish-root",
                str(self.publish_root),
                "--base-url",
                self.BUSINESS_BASE_URL,
                "--deploy-timeout-seconds",
                str(deploy_timeout),
                "--poll-interval-seconds",
                "60",
                "--rps",
                "0",
            ]
        )

    def _run_with_lark_mocks(self, *, args, store: _FieldStore, sleep_calls: list[float]):
        source = _RecordingSource()
        store.attach(source)
        binding = SimpleNamespace(base_token="base_tok", table_id="tbl_link")
        patches = (
            mock.patch.object(receipt_links, "load_config", return_value={}),
            mock.patch.object(receipt_links, "collect_queue_preflight_errors", return_value=[]),
            mock.patch.object(receipt_links, "resolve_document_link_binding", return_value=binding),
            mock.patch.object(receipt_links, "cli_bin", return_value="lark-cli"),
            mock.patch.object(receipt_links, "phase2_identity", return_value="bot"),
            mock.patch.object(receipt_links, "fetch_field_id_map", return_value={"HTML_link": "fld1"}),
        )
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        exit_code, report = receipt_links.run(
            args,
            sleep_fn=sleep_calls.append,
            fetch_fields=store.fetch,
            lark_source_factory=lambda **_kwargs: source,
        )
        return exit_code, report, source

    def _cas_redirect(self, _url: str) -> bytes:
        raise receipt.CrossOriginRedirect(self.CAS_LOGIN)

    def test_private_without_token_fails_fast_without_30_min_wait(self) -> None:
        store = _FieldStore({})
        sleep_calls: list[float] = []
        with mock.patch.dict(os.environ, {private_verify.API_TOKEN_ENV: ""}):
            with mock.patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                exit_code, report, source = self._run_with_lark_mocks(
                    args=self._args(deploy_timeout=1800),
                    store=store,
                    sleep_calls=sleep_calls,
                )
        self.assertEqual(receipt_links.EXIT_FAILED, exit_code)
        self.assertEqual("failed", report["status"])
        self.assertEqual(1, report["verify_attempts"])
        self.assertEqual([], sleep_calls)
        self.assertEqual([], source.upserts)

    def test_private_with_token_and_succeeded_build_writes_html_links(self) -> None:
        payload = {
            "results": [
                {
                    "id": 4762840,
                    "commit": self.commit_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T03:37:13Z",
                    "success": True,
                    "version": {"slug": "latest"},
                }
            ]
        }

        def opener(request, timeout=30):
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        sleep_calls: list[float] = []
        with mock.patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "token-123"}):
            with mock.patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with mock.patch.object(private_verify, "urlopen", side_effect=opener):
                    exit_code, report, source = self._run_with_lark_mocks(
                        args=self._args(deploy_timeout=1800),
                        store=store,
                        sleep_calls=sleep_calls,
                    )
        self.assertEqual(receipt_links.EXIT_OK, exit_code)
        self.assertEqual("registered", report["status"])
        self.assertEqual("rtd-private-build", report["verification_mode"])
        self.assertEqual(4762840, report["rtd_build"]["id"])
        self.assertEqual(1, report["verify_attempts"])
        self.assertEqual(2, report["records_written"])
        expected_url = (
            f"{self.BUSINESS_BASE_URL}/JE-1000F/US/en/md/manual_je1000f_us_en.html"
        )
        self.assertEqual(
            [
                ("base_tok", "tbl_link", "rec_web_1", {"HTML_link": expected_url}),
                ("base_tok", "tbl_link", "rec_web_2", {"HTML_link": expected_url}),
            ],
            source.upserts,
        )

    def test_private_with_token_polls_in_progress_build_until_success(self) -> None:
        responses = [
            {
                "results": [
                    {
                        "id": 4762841,
                        "commit": self.commit_sha,
                        "state": {"code": "building"},
                        "finished": None,
                        "success": None,
                        "version": {"slug": "latest"},
                    }
                ]
            },
            {
                "results": [
                    {
                        "id": 4762841,
                        "commit": self.commit_sha,
                        "state": {"code": "finished"},
                        "finished": "2026-11-19T03:40:00Z",
                        "success": True,
                        "version": {"slug": "latest"},
                    }
                ]
            },
        ]
        call_idx = {"n": 0}

        def opener(request, timeout=30):
            idx = min(call_idx["n"], len(responses) - 1)
            call_idx["n"] += 1
            return io.BytesIO(json.dumps(responses[idx]).encode("utf-8"))

        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        sleep_calls: list[float] = []
        with mock.patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "token-123"}):
            with mock.patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with mock.patch.object(private_verify, "urlopen", side_effect=opener):
                    exit_code, report, source = self._run_with_lark_mocks(
                        args=self._args(deploy_timeout=1800),
                        store=store,
                        sleep_calls=sleep_calls,
                    )
        self.assertEqual(receipt_links.EXIT_OK, exit_code)
        self.assertEqual("registered", report["status"])
        self.assertEqual(2, report["verify_attempts"])
        # One 60s poll wait followed by two 2s Bitable readback delays.
        self.assertEqual([60.0, 2.0, 2.0], sleep_calls)
        self.assertEqual(2, len(source.upserts))

    def test_private_with_token_fails_fast_when_build_finished_failed(self) -> None:
        payload = {
            "results": [
                {
                    "id": 4762842,
                    "commit": self.commit_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T03:42:00Z",
                    "success": False,
                    "version": {"slug": "latest"},
                }
            ]
        }

        def opener(request, timeout=30):
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        sleep_calls: list[float] = []
        with mock.patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "token-123"}):
            with mock.patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with mock.patch.object(private_verify, "urlopen", side_effect=opener):
                    exit_code, report, source = self._run_with_lark_mocks(
                        args=self._args(deploy_timeout=1800),
                        store=store,
                        sleep_calls=sleep_calls,
                    )
        self.assertEqual(receipt_links.EXIT_FAILED, exit_code)
        self.assertEqual("failed", report["status"])
        self.assertEqual(1, report["verify_attempts"])
        self.assertEqual([], sleep_calls)
        self.assertEqual([], source.upserts)

    def test_private_with_token_fails_fast_when_local_manual_file_missing(self) -> None:
        (
            self.publish_root
            / "web"
            / "JE-1000F"
            / "US"
            / "en"
            / "md"
            / "manual_je1000f_us_en.md"
        ).unlink()
        payload = {
            "results": [
                {
                    "id": 4762843,
                    "commit": self.commit_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T03:45:00Z",
                    "success": True,
                    "version": {"slug": "latest"},
                }
            ]
        }

        def opener(request, timeout=30):
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        store = _FieldStore({"rec_web_1": "", "rec_web_2": ""})
        sleep_calls: list[float] = []
        with mock.patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "token-123"}):
            with mock.patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with mock.patch.object(private_verify, "urlopen", side_effect=opener):
                    exit_code, report, source = self._run_with_lark_mocks(
                        args=self._args(deploy_timeout=1800),
                        store=store,
                        sleep_calls=sleep_calls,
                    )
        self.assertEqual(receipt_links.EXIT_FAILED, exit_code)
        self.assertEqual("failed", report["status"])
        self.assertEqual(1, report["verify_attempts"])
        self.assertEqual([], sleep_calls)
        self.assertEqual([], source.upserts)


if __name__ == "__main__":
    unittest.main()
