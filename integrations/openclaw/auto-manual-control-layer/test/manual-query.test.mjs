import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { createKnowledgeClient, siteOrigin, validateCorpus } from "../lib/manual-query/client.mjs";
import { readSection, searchManuals } from "../lib/manual-query/search.mjs";
import { registerManualQuery, renderQueryResult } from "../lib/manual-query/plugin.mjs";
import plugin from "../index.mjs";

const origin = "https://manual.example";
const digest = (value) => createHash("sha256").update(value).digest("hex");
function fixture({ version = "2.0", model = "JE-TEST", scope = "single", lang = "en" } = {}) {
  const doc = { id: "doc-" + model, model, name: "Product", region: "EU", lang: scope === "single" ? lang : null,
    language_scope: scope, version, url: `${model}/EU/en/md/manual.html`, html_sha256: "b".repeat(64),
    coverage: { image_text_coverage: "alt_only_no_ocr" }, sections: [
      { id: "spec-" + model, title: "Specifications", anchor: "specifications", blocks: [
        { type: "table", text: "USB-C output | 100 W\nVoltage | 20 V", grid: [["USB-C output", "100 W"], ["Voltage", "20 V"]] },
        { type: "callout", text: "WARNING: Single port only.", label: "WARNING", body: "Single port only." },
      ] },
      { id: "operate-" + model, title: "Operations", anchor: "operation", blocks: [
        { type: "paragraph", text: "Turn Energy Saving Mode off. Hold for 3 seconds." },
        { type: "callout", text: "WARNING: Do not use for critical continuous loads." },
      ] },
    ] };
  const corpus = { schema: "auto-manual-knowledge/v1", source_sha256: "a".repeat(64), region: "EU",
    published_at: "2026-10-01T00:00:00Z", counts: { models: 1, editions: 1, sections: 2 }, documents: [doc] };
  const bytes = Buffer.from(JSON.stringify(corpus));
  const receipt = { schema: "manual-rtd-deployment/v1", source_sha256: corpus.source_sha256,
    files: { "manual-knowledge.json": digest(bytes), [doc.url]: doc.html_sha256 } };
  return { corpus, receipt, bytes, origin, checkedAt: 1000, digest: digest(bytes) };
}

function fetcher(current) {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    const f = current();
    if (f instanceof Error) throw f;
    const bytes = new URL(url).pathname.endsWith("manual-deployment.json") ? JSON.stringify(f.receipt) : f.bytes;
    return new Response(bytes, { status: 200 });
  };
  return { calls, fetchImpl };
}

test("query client accepts only bounded HTTPS origins", () => {
  assert.equal(siteOrigin(origin + "/"), origin);
  for (const url of ["http://manual.example", "https://x:y@manual.example", origin + "/x", origin + "?secret=1", origin + "#x"]) {
    assert.throws(() => siteOrigin(url));
  }
});

test("receipt/hash verification is atomic and cache refresh observes a replacement release", async () => {
  let current = fixture(); let time = 1000;
  const transport = fetcher(() => current);
  const client = createKnowledgeClient({ baseUrl: origin, fetchImpl: transport.fetchImpl, now: () => time });
  const first = await client.load();
  assert.equal(first.corpus.documents[0].version, "2.0");
  assert.equal(transport.calls.length, 3);
  await client.load(); assert.equal(transport.calls.length, 3);
  time += 60001; current = fixture({ version: "3.0" });
  assert.equal((await client.load()).corpus.documents[0].version, "3.0");
  for (const { url, options } of transport.calls) {
    assert.equal(new URL(url).origin, origin); assert.equal(options.redirect, "manual");
    assert.match(new URL(url).search, /^\?receipt_probe=[a-f0-9]{32}$/);
  }
});

test("RTD version-prefix redirects are bounded and never followed across origins", async () => {
  const transport = fetcher(() => fixture());
  const fetchImpl = async (url, options) => {
    const path = new URL(url).pathname;
    if (!path.startsWith("/en/latest/")) return new Response(null, { status: 302, headers: { location: "/en/latest" + path } });
    return transport.fetchImpl(url, options);
  };
  assert.equal((await createKnowledgeClient({ baseUrl: origin, fetchImpl }).load()).corpus.counts.models, 1);
  let calls = 0;
  await assert.rejects(createKnowledgeClient({ baseUrl: origin, fetchImpl: async () => {
    calls++;
    return new Response(null, { status: 302, headers: { location: "https://other.example/receipt" } });
  } }).load(), /Cross-origin/);
  assert.equal(calls, 1);
  await assert.rejects(createKnowledgeClient({ baseUrl: origin, fetchImpl: async () =>
    new Response(null, { status: 302, headers: { location: "/loop" } }) }).load(), /Too many/);
});

test("withdrawal replaces the whole corpus; withdrawn sections cannot be read", async () => {
  let current = fixture(); let time = 1000;
  const transport = fetcher(() => current);
  const client = createKnowledgeClient({ baseUrl: origin, fetchImpl: transport.fetchImpl, now: () => time });
  await client.load();
  current = fixture({ model: "JE-OTHER" }); time += 60001;
  const after = await client.load();
  assert.equal(readSection(after, { document_id: "doc-JE-TEST", section_id: "spec-JE-TEST", snapshot_id: after.digest }).status, "not_found");
});

test("expired cached data is refused when fresh receipt fetch fails", async () => {
  let current = fixture(); let time = 1000;
  const transport = fetcher(() => current);
  const client = createKnowledgeClient({ baseUrl: origin, fetchImpl: transport.fetchImpl, now: () => time });
  await client.load(); time += 60001; current = new Error("offline");
  await assert.rejects(client.load(), /offline/);
  await assert.rejects(client.load(), /offline/);
});

test("tampered bytes, missing artifact, deployment race and foreign routes fail closed", async () => {
  const tampered = fixture(); tampered.bytes = Buffer.from("{}");
  await assert.rejects(createKnowledgeClient({ baseUrl: origin, ...fetcher(() => tampered) }).load(), /does not match/);
  const missing = fixture(); delete missing.receipt.files["manual-knowledge.json"];
  await assert.rejects(createKnowledgeClient({ baseUrl: origin, ...fetcher(() => missing) }).load(), /does not contain/);
  let i = 0; const before = fixture(); const after = fixture({ version: "3" });
  await assert.rejects(createKnowledgeClient({ baseUrl: origin,
    ...fetcher(() => ++i < 3 ? before : after) }).load(), /changed during refresh/);
  const foreign = fixture(); foreign.corpus.documents[0].url = "https://evil.test/manual.html";
  assert.throws(() => validateCorpus(foreign.corpus, foreign.receipt), /Invalid/);
});

test("HTTP failures and oversized or incomplete responses never become a corpus", async () => {
  for (const response of [new Response("forbidden", { status: 403 }),
    new Response("{}", { headers: { "content-length": "999999999" } }),
    new Response("{}", { headers: { "content-length": "20" } })]) {
    await assert.rejects(createKnowledgeClient({ baseUrl: origin, fetchImpl: async () => response }).load());
  }
});

test("concurrent queries share one verification download", async () => {
  const transport = fetcher(() => fixture());
  const client = createKnowledgeClient({ baseUrl: origin, fetchImpl: transport.fetchImpl });
  const results = await Promise.all([client.load(), client.load(), client.load()]);
  assert.equal(transport.calls.length, 3); assert.equal(results[0], results[2]);
});

test("Chinese questions retrieve source evidence with explicit version and chapter URL", () => {
  const f = fixture();
  for (const query of ["JE-TEST USB-C输出功率", "JE-TEST USB-C的输出是多少", "JE-TEST specifications", "JE TEST specifications"]) {
    const result = searchManuals(f, { query });
    assert.equal(result.status, "matches");
    assert.equal(result.results[0].section_id, "spec-JE-TEST");
    assert.equal(result.results[0].version, "2.0");
    assert.equal(result.results[0].url, origin + "/JE-TEST/EU/en/md/manual.html#specifications");
  }
  assert.equal(searchManuals(f, { query: "JE-TEST节能模式怎么关闭" }).results[0].section_id, "operate-JE-TEST");
});

test("model, region and language uncertainty is not silently resolved to another manual", () => {
  const f = fixture();
  assert.equal(searchManuals(f, { query: "USB-C功率" }).status, "needs_model");
  assert.equal(searchManuals(f, { query: "JE-TESTMORE output" }).status, "model_not_found");
  assert.equal(searchManuals(f, { query: "JE-NONE output" }).status, "model_not_found");
  assert.equal(searchManuals(f, { query: "JE-TEST 美规输出" }).status, "outside_scope");
  assert.equal(searchManuals(f, { query: "JE-TEST UK output" }).status, "outside_scope");
  assert.equal(searchManuals(f, { query: "JE-TEST 英规输出" }).status, "outside_scope");
  assert.equal(searchManuals(f, { model: "JE-TEST", language: "fr", query: "output" }).status, "language_not_found");
  const other = fixture({ model: "JE-OTHER" }); f.corpus.documents.push(other.corpus.documents[0]);
  assert.equal(searchManuals(f, { query: "compare JE-TEST JE-OTHER" }).status, "needs_model");
  assert.equal(searchManuals(f, { query: "compare JE-TEST JE-UNKNOWN" }).status, "model_not_found");
});

test("legacy editions remain searchable with unknown language, and missing concepts return no evidence", () => {
  const f = fixture({ scope: "legacy_unspecified" });
  const r = searchManuals(f, { model: "JE-TEST", query: "output" });
  assert.equal(r.results[0].language, null); assert.equal(r.results[0].language_scope, "legacy_unspecified");
  assert.equal(searchManuals(f, { model: "JE-TEST", query: "underwater submersion" }).status, "no_evidence");
  assert.match(renderQueryResult(r), /语言范围未验证/);
});

test("section pagination preserves whole tables and adjacent warnings", () => {
  const f = fixture(); const args = { document_id: "doc-JE-TEST", section_id: "spec-JE-TEST", snapshot_id: f.digest, limit: 1 };
  const first = readSection(f, args); assert.deepEqual(first.blocks[0].grid, [["USB-C output", "100 W"], ["Voltage", "20 V"]]);
  assert.equal(first.next_offset, 1);
  const second = readSection(f, { ...args, offset: first.next_offset });
  assert.equal(second.blocks[0].label, "WARNING"); assert.equal(second.next_offset, null);
  assert.match(first.guidance, /继续读取/);
  assert.throws(() => readSection(f, { ...args, offset: -1 }));
});

test("search and every evidence page must belong to the same publication snapshot", () => {
  const before = fixture(); const after = fixture({ version: "3.0" });
  const result = searchManuals(before, { query: "JE-TEST output" });
  const args = { document_id: "doc-JE-TEST", section_id: "spec-JE-TEST", snapshot_id: result.publication.snapshot_id };
  assert.equal(readSection(before, args).status, "evidence");
  assert.equal(readSection(after, args).status, "publication_changed");
  assert.equal(readSection(after, { ...args, snapshot_id: undefined }).status, "publication_changed");
});

test("technical parameters headings are found with Chinese or English specifications keywords", () => {
  const f = fixture(); f.corpus.documents[0].sections[0].title = "TECHNICAL PARAMETERS";
  for (const query of ["JE-TEST 参数", "JE-TEST specifications"]) {
    assert.equal(searchManuals(f, { query }).results[0].section_id, "spec-JE-TEST");
  }
});

test("oversized evidence is not truncated into a misleading partial table", () => {
  const f = fixture(); f.corpus.documents[0].sections[0].blocks[0].text = "a".repeat(70000);
  const result = readSection(f, { document_id: "doc-JE-TEST", section_id: "spec-JE-TEST", snapshot_id: f.digest });
  assert.equal(result.status, "open_source"); assert.equal(result.next_offset, null); assert.deepEqual(result.blocks, []);
});

test("gateway tools use the existing model path and never dispatch builds", async () => {
  const tools = []; const commands = []; let loads = 0;
  const api = { pluginConfig: { manualQueryBaseUrl: origin }, registerTool: (tool) => tools.push(tool),
    registerCommand: (command) => commands.push(command) };
  registerManualQuery(api, { clientFactory: () => ({ load: async () => { loads++; return fixture(); } }) });
  assert.deepEqual(tools.map((tool) => tool.name), ["manual_search", "manual_section"]);
  assert.equal(commands[0].requireAuth, true);
  const search = await tools[0].execute("call-id", { query: "JE-TEST output" });
  assert.equal(search.details.status, "matches");
  const read = await tools[1].execute("call-id", { document_id: search.details.results[0].document_id,
    section_id: search.details.results[0].section_id, snapshot_id: search.details.publication.snapshot_id });
  assert.equal(read.details.status, "evidence");
  const reply = await commands[0].handler({ args: "JE-TEST output" });
  assert.match(reply.text, /检索片段/); assert.match(reply.text, /\[Specifications\]\(https:\/\/manual\.example/);
  assert.equal(loads, 3);
});

test("plugin registers query tools alongside unchanged operation commands", () => {
  const tools = []; const commands = [];
  plugin.register({ registerTool: (t) => tools.push(t.name), registerCommand: (c) => commands.push(c.name) });
  assert.deepEqual(tools, ["manual_search", "manual_section"]);
  assert.ok(commands.includes("manual-query")); assert.ok(commands.includes("publish"));
  assert.ok(commands.includes("manual-status"));
});

test("unconfigured or disconnected gateway reports unavailable, never a guessed answer", async () => {
  const tools = [];
  registerManualQuery({ registerTool: (tool) => tools.push(tool), registerCommand() {} });
  const result = await tools[0].execute("call-id", { query: "JE-TEST output" });
  assert.equal(result.details.status, "unavailable"); assert.equal(result.isError, true);
  assert.match(result.details.guidance, /请勿使用缓存或记忆补答/);
});
