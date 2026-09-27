import json
import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tools import rtd_workspace_revision as revision


class WorkspaceRevisionTests(unittest.TestCase):
    def test_rtd_checkout_identity_is_preserved_without_git(self):
        with patch.dict(os.environ, {"READTHEDOCS_GIT_COMMIT_HASH": "a" * 40}), \
                patch.object(revision.subprocess, "check_output") as git:
            receipt = revision.workspace_revision(Path("/unused"))
        self.assertEqual(receipt["revision"], "a" * 40)
        git.assert_not_called()

    def test_local_git_failure_does_not_invent_a_deployed_version(self):
        with patch.dict(os.environ, {"READTHEDOCS_GIT_COMMIT_HASH": "invalid"}), \
                patch.object(revision.subprocess, "check_output", side_effect=subprocess.TimeoutExpired("git", 5)):
            self.assertEqual(revision.workspace_revision(Path("/unused"))["revision"], "")

    def test_receipt_is_identical_to_page_and_not_written_on_failure(self):
        with TemporaryDirectory() as tmp:
            app = SimpleNamespace(outdir=tmp)
            with patch.object(revision, "workspace_revision", return_value={"revision": "b" * 40}):
                receipt = revision.page_revision(app)
            output = Path(tmp) / "_static" / revision.RECEIPT_NAME
            revision.write_workspace_revision(app, RuntimeError("build failed"))
            self.assertFalse(output.exists())
            revision.write_workspace_revision(app, None)
            self.assertEqual(json.loads(output.read_text()), receipt)
