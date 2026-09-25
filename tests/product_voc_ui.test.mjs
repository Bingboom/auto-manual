import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const script = readFileSync(new URL("../tools/rtd_portal_assets/_static/product-voc.js", import.meta.url), "utf8");

function fixture(fetchResponse) {
  const listeners = {};
  const status = { textContent: "" };
  const fields = { disabled: true };
  const button = { disabled: false };
  const dialogEvents = {}, launchEvents = {}, closeEvents = {};
  const launch = { hidden: true, focus() { this.focused = true; }, addEventListener(n, fn) { launchEvents[n] = fn; } };
  const dialog = { open: false, showModal() { this.open = true; }, close() { this.open = false; dialogEvents.close(); }, addEventListener(n, fn) { dialogEvents[n] = fn; }, getBoundingClientRect: () => ({left: 10, right: 100, top: 10, bottom: 100}) };
  const root = { querySelector: (s) => s === "dialog" ? dialog : s === ".product-voc-launch" ? launch : { addEventListener(n, fn) { closeEvents[n] = fn; } } };
  const values = { model: "TEST", suggestion: "TEST product suggestion", use_case: "", context: "TEST page", website: "" };
  const form = {
    closest: () => root,
    dataset: { endpoint: "https://example.test/api/voc" },
    querySelector: (selector) => selector.includes("input[") ? { focus() {} } : selector === "fieldset" ? fields : selector.includes("button") ? button : status,
    addEventListener: (name, fn) => { listeners[name] = fn; },
    reportValidity: () => true,
  };
  const calls = [];
  let serial = 0;
  const fetch = async (...args) => { calls.push(args); return fetchResponse(...args); };
  vm.runInNewContext(script, {
    document: { querySelectorAll: () => [form] },
    window: { fetch, crypto: { randomUUID: () => `test-uuid-${++serial}` } },
    fetch, AbortController, Error, TypeError,
    FormData: class { constructor() { return Object.entries(values); } },
    setTimeout: () => 1, clearTimeout: () => {},
  });
  return { values, status, fields, button, calls, listeners, dialog, launch, launchEvents, closeEvents, dialogEvents,
    submit: () => listeners.submit({ preventDefault() {} }) };
}

test("nothing is transmitted on load; only explicit submission sends the known fields", async () => {
  const f = fixture(async () => ({ ok: true, json: async () => ({ ok: true }) }));
  assert.equal(f.calls.length, 0);
  assert.equal(f.fields.disabled, false);
  await f.submit();
  assert.equal(f.calls.length, 1);
  const [endpoint, request] = f.calls[0];
  assert.equal(endpoint, "https://example.test/api/voc");
  assert.equal(request.credentials, "omit");
  assert.equal(request.referrerPolicy, "no-referrer");
  assert.equal(request.redirect, "error");
  assert.deepEqual(JSON.parse(request.body), { ...f.values, request_id: "test-uuid-1" });
  assert.match(f.status.textContent, /received/);
  assert.equal(f.button.disabled, true);
});

test("failure preserves input, retry reuses reference, changed text gets a new reference", async () => {
  const f = fixture(async () => { throw new TypeError("network"); });
  await f.submit();
  assert.match(f.status.textContent, /not confirmed/);
  assert.equal(f.values.suggestion, "TEST product suggestion");
  assert.equal(f.fields.disabled, false);
  await f.submit();
  assert.equal(JSON.parse(f.calls[0][1].body).request_id, JSON.parse(f.calls[1][1].body).request_id);
  f.values.suggestion = "A changed suggestion";
  f.listeners.input();
  await f.submit();
  assert.notEqual(JSON.parse(f.calls[1][1].body).request_id, JSON.parse(f.calls[2][1].body).request_id);
});

test("double submit while busy makes only one call", async () => {
  let release;
  const f = fixture(() => new Promise((resolve) => { release = resolve; }));
  const pending = f.submit();
  await f.submit();
  assert.equal(f.calls.length, 1);
  assert.equal(f.fields.disabled, true);
  release({ ok: true, json: async () => ({ ok: true }) });
  await pending;
  assert.equal(f.fields.disabled, false);
});

test("error responses do not claim success; preview says nothing was sent and names no platform", async () => {
  for (const status of [400, 403, 409, 429, 503]) {
    const f = fixture(async () => ({ ok: false, status, json: async () => ({ ok: false }) }));
    await f.submit();
    assert.doesNotMatch(f.status.textContent, /Thank you/);
    assert.equal(f.fields.disabled, false);
  }
  const f = fixture(async () => ({ ok: true, json: async () => ({ ok: true, preview: true }) }));
  await f.submit();
  assert.match(f.status.textContent, /Preview only — nothing was sent\. Reference: /);
  assert.doesNotMatch(f.status.textContent, /Feishu|飞书/);
});

test("modal opens without sending and close restores focus while retaining input", () => {
  const f = fixture(async () => ({ok:true}));
  assert.equal(f.launch.hidden, false);
  f.launchEvents.click();
  assert.equal(f.dialog.open, true);
  assert.equal(f.calls.length, 0);
  f.closeEvents.click();
  assert.equal(f.dialog.open, false);
  assert.equal(f.launch.focused, true);
  assert.equal(f.values.suggestion, "TEST product suggestion");
  f.launchEvents.click();
  f.dialogEvents.click({target:f.dialog,clientX:0,clientY:0});
  assert.equal(f.dialog.open, false);
});
