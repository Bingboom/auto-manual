import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import test from "node:test";
import vm from "node:vm";

const script = readFileSync(new URL("../tools/rtd_portal_assets/_static/system-workspace.js", import.meta.url), "utf8");
const old = "a".repeat(40), fresh = "b".repeat(40);
function harness(response, {hidden = false, current = old, builtAt = "2026-09-26T00:00:00Z"} = {}) {
  const listeners = {}, status = {}, button = {hidden:true, addEventListener:(k, fn) => {listeners[k] = fn;}};
  const events = {}, intervals = [], calls = [], navigations = [];
  const document = {
    hidden,
    querySelector: (selector) => selector === ".sw-update" ? {dataset:{revision:current, builtAt, versionUrl:"../../_static/system-workspace-revision.json"}} : null,
    getElementById:(id) => id === "sw-update-status" ? status : button,
    addEventListener:(key, fn) => {events[key] = fn;},
  };
  vm.runInNewContext(script, {
    document, URL, Date, AbortController, setTimeout, clearTimeout,
    setInterval:fn => intervals.push(fn),
    window:{location:{href:"https://example.test/workspace/system/index.html#focus",origin:"https://example.test",assign:url => navigations.push(url)}},
    fetch:async (url, options) => {calls.push({url, options}); if (response instanceof Error) throw response; return {ok:true,json:async () => response};},
  });
  return {document, status, button, events, calls, navigations, refresh:() => listeners.click(), tick:async () => {await new Promise(resolve => setImmediate(resolve));}, poll:() => intervals[0]()};
}
const receipt = (revision, built_at = "2026-09-26T01:00:00Z") => ({schema:"hello-docs-system-revision/v1",revision,built_at});

test("published update offers refresh without interrupting reading and keeps the anchor", async () => {
  const h = harness(receipt(fresh)); await h.tick();
  assert.equal(h.button.hidden, false); assert.equal(h.navigations.length, 0);
  assert.equal(h.calls[0].options.cache, "no-store");
  assert.equal(new URL(h.calls[0].url).pathname, "/_static/system-workspace-revision.json");
  h.refresh();
  const target = new URL(h.navigations[0]);
  assert.equal(target.searchParams.get("_sw_revision"), fresh); assert.equal(target.hash, "#focus");
  await h.poll(); assert.equal(h.calls.length, 1);
});
test("matching deployment stays current; hidden tabs wait until visible", async () => {
  const h = harness(receipt(old), {hidden:true}); await h.tick(); assert.equal(h.calls.length, 0);
  h.document.hidden = false; h.events.visibilitychange(); await h.tick();
  assert.match(h.status.textContent, /最新已发布/); assert.equal(h.button.hidden, true);
});
test("offline, invalid and stale receipts do not offer a downgrade or unsafe redirect", async () => {
  for (const response of [new Error("offline"), receipt("javascript:bad"), receipt(fresh, "2026-09-25T00:00:00Z"), {}]) {
    const h = harness(response); await h.tick(); assert.equal(h.button.hidden, true); h.refresh(); assert.equal(h.navigations.length, 0);
    assert.match(h.status.textContent, /无法检查|同步中/);
  }
});
test("unversioned local preview performs no network request", async () => {
  const h = harness(receipt(fresh), {current:""}); await h.tick(); assert.equal(h.calls.length, 0);
  assert.match(h.status.textContent, /本地预览/);
});
