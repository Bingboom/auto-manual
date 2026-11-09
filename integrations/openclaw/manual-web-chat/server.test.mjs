import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { once } from "node:events";
import test from "node:test";
import { answerQuestion, ChatError, modelCompletion } from "./answer.mjs";
import { corpusFetch, loadConfig } from "./config.mjs";
import { createChatServer } from "./server.mjs";

export function fixture() {
  const context = { model: "JE-TEST", region: "EU", language: "en", version: "1.0", page: "JE-TEST/EU/en/md/manual.html" };
  const doc = { id: "doc", model: context.model, region: "EU", lang: "en", version: "1.0",
    language_scope: "single", url: context.page, sections: [{ id: "solar", title: "Solar charging", anchor: "solar",
      blocks: [{ type: "paragraph", text: "Connect the solar panel. Use only compatible cables." },
        { type: "callout", text: "WARNING: Keep dry." }] }] };
  const snapshot = { origin: "https://manual.example/en/latest", checkedAt: 0, digest: "a".repeat(64),
    corpus: { source_sha256: "b".repeat(64), published_at: "2026-11-08", counts: { models: 1, editions: 1, sections: 1 }, documents: [doc] } };
  const body = { message: "怎么太阳能充电？", context, history: [] };
  const calls = [];
  const complete = async (system, input) => {
    calls.push({ system, input });
    return input.evidence ? { answer: "连接太阳能板，使用兼容线缆并保持干燥。", citations: ["solar"] }
      : { query: "solar charging", clarification: "" };
  };
  return { context, doc, snapshot, body, complete, calls };
}

const password = "test-only-password";
const config = { baseUrl: "https://manual.example/en/latest", origins: ["https://manual.example"],
  passwordHash: createHash("sha256").update(password).digest("hex"), rtdToken: "" };

async function running(t, overrides = {}) {
  const f = fixture();
  let clock = 1000;
  const server = createChatServer(config, { client: { load: async () => f.snapshot }, complete: f.complete, now: () => clock, ...overrides });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(() => { server.closeAllConnections(); server.close(); });
  const base = `http://127.0.0.1:${server.address().port}`;
  const post = (path, body, token, origin = config.origins[0]) => fetch(base + path, {
    method: "POST", headers: { Origin: origin, "Content-Type": "application/json", ...(token ? { Authorization: "Bearer " + token } : {}) },
    body: JSON.stringify(body),
  });
  const login = async () => {
    const res = await post("/api/session", { password });
    assert.equal(res.status, 200);
    assert.equal(res.headers.get("cache-control"), "no-store");
    return (await res.json()).token;
  };
  return { ...f, base, post, login, tick: (ms) => { clock += ms; } };
}

test("current manual evidence is scoped, fully read and cited", async () => {
  const f = fixture();
  f.snapshot.corpus.documents.push({ ...f.doc, id: "other", model: "JE-OTHER", url: "other.html" });
  const result = await answerQuestion(f.snapshot, f.body, f.complete);
  assert.equal(f.calls.length, 2);
  assert.equal(f.calls[1].input.evidence[0].blocks.length, 2);
  assert.match(f.calls[1].input.evidence[0].blocks[1].text, /WARNING/);
  assert.equal(result.sources[0].url, config.baseUrl + "/" + f.context.page + "#solar");
  assert.equal(f.calls[1].input.context.model, "JE-TEST");
});

test("pagination includes later safety warnings", async () => {
  const f = fixture();
  f.doc.sections[0].blocks = Array.from({ length: 35 }, (_, i) => ({ type: "paragraph", text: `Solar charging step ${i}` }));
  await answerQuestion(f.snapshot, f.body, f.complete);
  assert.equal(f.calls[1].input.evidence[0].blocks.length, 35);
});

test("mismatched edition, language, market and legacy scope never call the model", async () => {
  for (const change of [{ version: "old" }, { language: "de" }, { page: "other.html" }, { model: "JE-OTHER" }]) {
    const f = fixture();
    Object.assign(f.body.context, change);
    await assert.rejects(answerQuestion(f.snapshot, f.body, f.complete), (e) => e instanceof ChatError && e.status === 409);
    assert.equal(f.calls.length, 0);
  }
  const f = fixture();
  f.doc.language_scope = "legacy_unspecified";
  await assert.rejects(answerQuestion(f.snapshot, f.body, f.complete));
  f.context.region = "JP";
  assert.match((await answerQuestion(f.snapshot, f.body, f.complete)).answer, /尚未开放/);
  assert.equal(f.calls.length, 0);
});

test("missing evidence is stated explicitly instead of generating product facts", async () => {
  const f = fixture();
  const result = await answerQuestion(f.snapshot, f.body, async () => ({ query: "unfindable", clarification: "" }));
  assert.match(result.answer, /没有检索到足够/);
  assert.deepEqual(result.sources, []);
});

test("a question naming another model or market is not silently answered from this page", async () => {
  for (const question of ["JE-OTHER 如何充电？", "日规充电参数是什么？"]) {
    const f = fixture();
    f.body.message = question;
    const result = await answerQuestion(f.snapshot, f.body, f.complete);
    assert.match(result.answer, /当前对话绑定/);
    assert.equal(f.calls.length, 0);
  }
});

test("oversized sections link the complete source and do not synthesize partial procedures", async () => {
  const f = fixture();
  f.doc.sections[0].blocks.push({ type: "paragraph", text: "solar ".repeat(11000) });
  const result = await answerQuestion(f.snapshot, f.body, f.complete);
  assert.match(result.answer, /无法完整读取/);
  assert.equal(f.calls.length, 1);
  assert.equal(result.sources.length, 1);
});

test("fabricated citations are rejected", async () => {
  const f = fixture();
  await assert.rejects(answerQuestion(f.snapshot, f.body, async (_system, input) => input.evidence
    ? { answer: "invented", citations: ["unknown"] } : { query: "solar" }), (e) => e.status === 502);
});

test("server enforces exact origin, authentication, expiry and logout", async (t) => {
  const f = await running(t);
  assert.equal((await f.post("/api/chat", f.body)).status, 401);
  assert.equal((await f.post("/api/session", { password }, null, "https://evil.example")).status, 403);
  assert.equal((await f.post("/api/session", { password: "wrong" })).status, 401);
  const token = await f.login();
  const answer = await f.post("/api/chat", f.body, token);
  assert.equal(answer.status, 200);
  assert.equal(answer.headers.get("access-control-allow-origin"), config.origins[0]);
  assert.equal((await answer.json()).sources.length, 1);
  await f.post("/api/logout", {}, token);
  assert.equal((await f.post("/api/chat", f.body, token)).status, 401);
  const second = await f.login();
  f.tick(30 * 60 * 1000 + 1);
  assert.equal((await f.post("/api/chat", f.body, second)).status, 401);
});

test("preflight is restricted to the intended service routes", async (t) => {
  const f = await running(t);
  const res = await fetch(f.base + "/api/chat", { method: "OPTIONS", headers: { Origin: config.origins[0] } });
  assert.equal(res.status, 204);
  assert.equal(res.headers.get("access-control-allow-headers"), "Content-Type, Authorization");
  assert.equal((await f.post("/api/execute", { command: "publish" })).status, 404);
});

test("login rate limit, malformed JSON and bounded requests fail closed", async (t) => {
  const f = await running(t);
  const malformed = await fetch(f.base + "/api/session", { method: "POST", headers: { Origin: config.origins[0], "Content-Type": "application/json" }, body: "{" });
  assert.equal(malformed.status, 400);
  const large = await f.post("/api/session", { password: "x".repeat(65000) });
  assert.equal(large.status, 413);
  for (let i = 0; i < 8; i++) await f.post("/api/session", { password: "wrong" });
  assert.equal((await f.post("/api/session", { password })).status, 429);
});

test("corpus refresh failure is not replaced with model knowledge or private errors", async (t) => {
  let called = false;
  const f = await running(t, { client: { load: async () => { throw new Error("private-token-secret"); } }, complete: () => { called = true; } });
  const response = await f.post("/api/chat", f.body, await f.login());
  assert.equal(response.status, 503);
  assert.doesNotMatch(await response.text(), /private-token-secret/);
  assert.equal(called, false);
});

test("session question rate is bounded independently of login attempts", async (t) => {
  const f = await running(t);
  const token = await f.login();
  for (let i = 0; i < 12; i++) assert.equal((await f.post("/api/chat", f.body, token)).status, 200);
  assert.equal((await f.post("/api/chat", f.body, token)).status, 429);
  f.tick(60001);
  assert.equal((await f.post("/api/chat", f.body, token)).status, 200);
});

test("concurrent model work is bounded and rejected requests do not enter the provider", async (t) => {
  let entered = 0, release, allEntered;
  const gate = new Promise((resolve) => { release = resolve; });
  const started = new Promise((resolve) => { allEntered = resolve; });
  const f = await running(t, { complete: async (_system, input) => {
    if (input.evidence) return { answer: "Use compatible cables.", citations: ["solar"] };
    if (++entered === 4) allEntered();
    await gate;
    return { query: "solar" };
  } });
  const token = await f.login();
  const requests = Array.from({ length: 4 }, () => f.post("/api/chat", f.body, token));
  await started;
  assert.equal((await f.post("/api/chat", f.body, token)).status, 503);
  assert.equal(entered, 4);
  release();
  for (const response of await Promise.all(requests)) assert.equal(response.status, 200);
});

test("RTD token is sent only to the configured publication origin", async () => {
  let auth;
  const fetcher = corpusFetch({ ...config, rtdToken: "private-rtd-token" }, async (_url, options) => { auth = options.headers.get("Authorization"); });
  await fetcher(config.baseUrl + "/manual-knowledge.json");
  assert.equal(auth, "Token private-rtd-token");
  assert.throws(() => fetcher("https://evil.example/collect"));
});

test("model calls disable redirects and tools; upstream secrets are not echoed", async () => {
  let options;
  const completion = modelCompletion({ modelUrl: "https://model.example/v1/chat/completions", model: "test", modelKey: "secret" }, async (_url, input) => {
    options = input;
    return Response.json({ choices: [{ message: { content: '{"query":"solar"}' } }] });
  });
  assert.deepEqual(await completion("rules", { question: "solar" }), { query: "solar" });
  assert.equal(options.redirect, "error");
  assert.equal(JSON.parse(options.body).tools, undefined);
  const failed = modelCompletion({}, async () => new Response("private-error-secret", { status: 401 }));
  await assert.rejects(failed("rules", {}), (e) => e.status === 502 && !e.message.includes("private-error-secret"));
});

test("service requires explicit origins, password hash and upstream connection", () => {
  assert.throws(() => loadConfig({}));
  const env = { HT_DOCS_CHAT_ALLOWED_ORIGINS: config.origins[0], HT_DOCS_CHAT_PASSWORD_SHA256: config.passwordHash,
    HT_DOCS_CHAT_MANUAL_BASE_URL: config.baseUrl, HT_DOCS_CHAT_MODEL_URL: "https://model.example/v1/chat/completions",
    HT_DOCS_CHAT_MODEL: "test", HT_DOCS_CHAT_MODEL_KEY: "secret" };
  assert.equal(loadConfig(env).host, "127.0.0.1");
  assert.throws(() => loadConfig({ ...env, HT_DOCS_CHAT_ALLOWED_ORIGINS: "https://manual.example/path" }));
  assert.throws(() => loadConfig({ ...env, HT_DOCS_CHAT_MODEL_URL: "https://user:password@model.example" }));
});
