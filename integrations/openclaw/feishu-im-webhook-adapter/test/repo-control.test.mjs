import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

import { createRepoControl } from "../lib/repo-control.mjs";

test("runCloudDocBackportReview calls the Python runner and reads the run manifest", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "repo-control-backport-"));
  const fakePython = path.join(root, "fake-python.mjs");
  await fs.writeFile(
    fakePython,
    `#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
const args = process.argv.slice(2);
const outDir = args[args.indexOf("--out") + 1];
const runId = args[args.indexOf("--run-id") + 1];
const write = args.includes("--write");
fs.mkdirSync(path.join(process.cwd(), outDir), { recursive: true });
fs.writeFileSync(
  path.join(process.cwd(), outDir, "cloud_doc_backport_run.json"),
  JSON.stringify({
    schema_version: "cloud-doc-backport-run/v1",
    result: write ? "PR_READY" : "DRY_RUN",
    mode: write ? "write" : "dry-run",
    reports: { run_markdown: path.join(outDir, "cloud_doc_backport_run.md") },
    summary: { pr_ready: write, changed: write, source_table_suggestions: 1 },
    next_actions: ["ok"]
  })
);
console.log(JSON.stringify({ args }));
`,
    { mode: 0o755 }
  );

  const repoControl = createRepoControl({
    repoRoot: root,
    pythonBin: fakePython,
  });

  const result = await repoControl.runCloudDocBackportReview({
    docUrl: "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc",
    sourcePath: "docs/_review/JE-2000F/EU/page/00_preface.rst",
    runId: "run-1",
    write: true,
  });

  assert.equal(result.result, "PR_READY");
  assert.equal(result.run_id, "run-1");
  assert.equal(result.summary.pr_ready, true);
  assert.equal(result.manifest_path, "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json");
  assert.match(result.stdout, /tools\/cloud_doc_backport\.py/);
  assert.match(result.stdout, /--write/);
});
