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

test("inferCloudDocBackportSource resolves the only review page candidate", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "repo-control-source-infer-"));
  await fs.mkdir(path.join(root, "docs", "_review", "JE-2000F", "EU", "page"), { recursive: true });
  await fs.writeFile(
    path.join(root, "docs", "_review", "JE-2000F", "EU", "page", "00_preface.rst"),
    "**IMPORTANT**\n\nOriginal copy.\n",
    "utf8"
  );

  const repoControl = createRepoControl({ repoRoot: root, pythonBin: "python3" });
  const result = await repoControl.inferCloudDocBackportSource({
    docUrl: "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc",
    messageText: "根据这个文档回填修订 manual_je2000f_eu_en_0.7 副本",
    targetHint: { model: "JE-2000F", region: "EU", lang: "en", version: "0.7" },
  });

  assert.equal(result.status, "resolved");
  assert.equal(result.reason, "single_review_source_candidate");
  assert.equal(result.sourcePath, "docs/_review/JE-2000F/EU/page/00_preface.rst");
});

test("inferCloudDocBackportSource reports ambiguity with candidates", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "repo-control-source-ambiguous-"));
  const pageDir = path.join(root, "docs", "_review", "JE-2000F", "EU", "page");
  await fs.mkdir(pageDir, { recursive: true });
  await fs.writeFile(path.join(pageDir, "00_preface.rst"), "**IMPORTANT**\n", "utf8");
  await fs.writeFile(path.join(pageDir, "11_warranty.rst"), "Warranty\n========\n", "utf8");

  const repoControl = createRepoControl({ repoRoot: root, pythonBin: "python3" });
  const result = await repoControl.inferCloudDocBackportSource({
    docUrl: "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc",
    messageText: "根据这个文档回填修订 manual_je2000f_eu_en_0.7 副本",
    targetHint: { model: "JE-2000F", region: "EU", lang: "en", version: "0.7" },
  });

  assert.equal(result.status, "needs_input");
  assert.equal(result.reason, "review_source_ambiguous");
  assert.deepEqual(
    result.candidates.map((candidate) => candidate.sourcePath),
    [
      "docs/_review/JE-2000F/EU/page/00_preface.rst",
      "docs/_review/JE-2000F/EU/page/11_warranty.rst",
    ]
  );
});

test("inferCloudDocBackportSource resolves a unique message hint among multiple pages", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "repo-control-source-hint-"));
  const pageDir = path.join(root, "docs", "_review", "JE-2000F", "EU", "page");
  await fs.mkdir(pageDir, { recursive: true });
  await fs.writeFile(path.join(pageDir, "00_preface.rst"), "**IMPORTANT**\n", "utf8");
  await fs.writeFile(path.join(pageDir, "11_warranty.rst"), "Warranty\n========\n", "utf8");

  const repoControl = createRepoControl({ repoRoot: root, pythonBin: "python3" });
  const result = await repoControl.inferCloudDocBackportSource({
    docUrl: "https://test.feishu.cn/wiki/MbI4w8xLyi8NYnkoe4acAs9Hnvc",
    messageText: "根据这个文档回填修订 manual_je2000f_eu_en_0.7 warranty",
    targetHint: { model: "JE-2000F", region: "EU", lang: "en", version: "0.7" },
  });

  assert.equal(result.status, "resolved");
  assert.equal(result.reason, "unique_message_hint_match");
  assert.equal(result.sourcePath, "docs/_review/JE-2000F/EU/page/11_warranty.rst");
});

test("openCloudDocBackportPr calls the Python open-pr helper and parses JSON", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "repo-control-backport-pr-"));
  const fakePython = path.join(root, "fake-python.mjs");
  await fs.writeFile(
    fakePython,
    `#!/usr/bin/env node
const args = process.argv.slice(2);
console.log(JSON.stringify({
  schema_version: "cloud-doc-backport-pr/v1",
  result: "PR_OPENED",
  branch: args[args.indexOf("--branch") + 1],
  manifest_path: args[args.indexOf("--manifest") + 1],
  pr_url: "https://github.com/Bingboom/auto-manual/pull/999"
}));
`,
    { mode: 0o755 }
  );

  const repoControl = createRepoControl({
    repoRoot: root,
    pythonBin: fakePython,
  });

  const result = await repoControl.openCloudDocBackportPr({
    manifestPath: "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json",
    branchName: "review/JE-2000F-EU-cloud-doc",
  });

  assert.equal(result.result, "PR_OPENED");
  assert.equal(result.branch, "review/JE-2000F-EU-cloud-doc");
  assert.equal(result.manifest_path, "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json");
  assert.equal(result.pr_url, "https://github.com/Bingboom/auto-manual/pull/999");
});
