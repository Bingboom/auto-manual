// Opt-in audit of a real frozen-site build, without a gateway or network calls.
// node test/verify-published-corpus.mjs /absolute/path/to/sphinx/html
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { createKnowledgeClient } from "../lib/manual-query/client.mjs";
import { readSection, searchManuals } from "../lib/manual-query/search.mjs";

assert.ok(process.argv[2], "Pass the real frozen-site HTML output directory.");
const root = resolve(process.argv[2]);
const bytes = await readFile(resolve(root, "manual-knowledge.json"));
const receipt = await readFile(resolve(root, "manual-deployment.json"));
const client = createKnowledgeClient({ baseUrl: "https://manual.example", fetchImpl: async (url) =>
  new Response(new URL(url).pathname.endsWith("manual-deployment.json") ? receipt : bytes) });
const snapshot = await client.load();
const { corpus } = snapshot;
const blockTypes = {};
let pages = 0;
for (const doc of corpus.documents) {
  const html = await readFile(resolve(root, doc.url));
  assert.equal(createHash("sha256").update(html).digest("hex"), doc.html_sha256, doc.url);
  const inventory = searchManuals(snapshot, { model: doc.model, language: doc.lang || "" });
  assert.equal(inventory.status, "manuals");
  assert.ok(inventory.manuals.some((row) => row.document_id === doc.id), doc.url);
  for (const section of doc.sections) {
    if (section.anchor) {
      assert.ok(html.toString().includes(`id="${section.anchor}"`), `${doc.url}#${section.anchor}`);
    }
    const found = [];
    let offset = 0;
    do {
      const result = readSection(snapshot, { document_id: doc.id, section_id: section.id,
        snapshot_id: snapshot.digest, offset, limit: 30 });
      assert.equal(result.status, "evidence", `${doc.url}#${section.anchor}: oversized evidence`);
      found.push(...result.blocks);
      offset = result.next_offset;
      pages++;
    } while (offset !== null);
    assert.deepEqual(found, section.blocks, "Pagination must not lose a table, condition or warning.");
    for (const block of found) blockTypes[block.type] = (blockTypes[block.type] || 0) + 1;
  }
}

const questions = [
  ...["JE-1000F", "JE-1000H", "JE-100C", "JE-2000E", "JE-2000F", "JE-3000C", "JE-300D", "JE-3600A", "JE-500A",
    "JBP-2000B", "JBP-3600A", "JS-100F", "JS-200E", "JS-40C", "JA-AD01A", "JA-AD600A", "JA-CC30A", "JAAC-WHE-100-EUA1"]
    .map((model) => [`${model} 规格`, /SPECIFICATIONS/]),
  ["JS-100I 参数", /TECHNICAL PARAMETERS/],
  ["JA-CA05B connect", /CONNECTION GUIDE/],
  ["JA-CA3SA ports", /FUNCTIONS OF MAIN PORTS/],
  ["JE-2000F USB-C输出功率", /SPECIFICATIONS/],
  ["JE-2000F 节能模式怎么关闭", /OPERATIONS/],
  ["JE-2000F 故障代码 F1", /TROUBLESHOOTING/],
  ["JE-1000F solar charging", /CHARGING/],
];
const queries = questions.map(([query, title]) => {
  const result = searchManuals(snapshot, { query });
  assert.equal(result.status, "matches", query);
  assert.ok(result.results.some((row) => title.test(row.title.toUpperCase())), query);
  return { query, status: result.status, titles: result.results.map((row) => row.title) };
});
for (const [params, expected] of [
  [{ query: "USB-C功率" }, "needs_model"],
  [{ query: "JE-9999 output" }, "model_not_found"],
  [{ query: "JE-1000F JE-2000F output" }, "needs_model"],
  [{ query: "JE-2000F 美规输出" }, "outside_scope"],
  [{ model: "JE-2000F", language: "zz", query: "output" }, "language_not_found"],
  [{ query: "JE-2000F underwater submersion" }, "no_evidence"],
]) {
  assert.equal(searchManuals(snapshot, params).status, expected, JSON.stringify(params));
  queries.push({ ...params, status: expected });
}
console.log(JSON.stringify({ source_sha256: corpus.source_sha256, snapshot_id: snapshot.digest,
  counts: corpus.counts, bytes: bytes.length, pages, blockTypes,
  legacy_editions: corpus.documents.filter((doc) => doc.lang === null).length, queries }, null, 2));
