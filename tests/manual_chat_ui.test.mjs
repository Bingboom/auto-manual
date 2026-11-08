import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const script = readFileSync(new URL("../tools/rtd_portal_assets/_static/manual-chat.js", import.meta.url), "utf8");

class Element {
  constructor() { this.events = {}; this.children = []; this.hidden = false; this.value = ""; this.textContent = ""; }
  addEventListener(name, fn) { this.events[name] = fn; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  cloneNode() { const copy = new Element(); copy.textContent = this.textContent; return copy; }
  focus() { this.focused = true; }
}

function fixture(reply, dataset = {}) {
  const launch = new Element(), dialog = new Element(), login = new Element(), form = new Element();
  const log = new Element(), status = new Element(), close = new Element(), clear = new Element();
  const password = new Element(), question = new Element(), buttons = [new Element(), new Element()];
  log.firstElementChild = new Element();
  log.firstElementChild.textContent = "hello";
  log.children.push(log.firstElementChild);
  dialog.showModal = () => { dialog.open = true; };
  dialog.close = () => { dialog.open = false; };
  login.elements = { password };
  form.elements = { question };
  form.querySelector = () => question;
  launch.hidden = true; form.hidden = true;
  const elements = { dialog, ".manual-chat-launch": launch, ".manual-chat-login": login, ".manual-chat-question": form,
    ".manual-chat-messages": log, ".manual-chat-status": status, ".manual-chat-close": close, ".manual-chat-clear": clear };
  const root = { dataset: { endpoint: "https://ask.example", model: "JE-TEST", region: "EU", language: "en",
    version: "1.0", page: "JE-TEST/EU/en/md/manual.html", ...dataset }, querySelector: (s) => elements[s], querySelectorAll: () => buttons };
  const calls = [], windowEvents = {};
  vm.runInNewContext(script, {
    document: { querySelector: () => root, createElement: () => new Element() },
    window: { addEventListener: (name, fn) => { windowEvents[name] = fn; } },
    location: { origin: "https://manual.example", pathname: "/en/latest/JE-TEST/EU/en/md/manual.html" },
    fetch: async (url, options) => { calls.push({ url, ...options }); return reply(url, options); },
    AbortController, URL, Error, TypeError, SyntaxError, setTimeout, clearTimeout,
  });
  const submit = (element) => element.events.submit({ preventDefault() {} });
  return { root, launch, dialog, login, form, log, status, close, clear, question, password, buttons, calls, windowEvents,
    loginWith: async () => { password.value = "test-password"; await submit(login); },
    ask: async (text = "怎么充电？") => { question.value = text; await submit(form); } };
}

const ok = (value) => ({ ok: true, json: async () => value });
const router = (answer) => (url) => url.endsWith("/session") ? ok({ token: "a".repeat(64) }) : ok(answer);

test("opening the sidebar sends nothing and unsupported markets cannot start a chat", () => {
  const f = fixture(() => { throw new Error("Unexpected network"); });
  assert.equal(f.launch.hidden, false);
  f.launch.events.click();
  assert.equal(f.dialog.open, true);
  assert.equal(f.calls.length, 0);
  f.close.events.click();
  assert.equal(f.dialog.open, false);
  const unsupported = fixture(() => {}, { region: "JP" });
  unsupported.launch.events.click();
  assert.equal(unsupported.login.hidden, true);
  assert.match(unsupported.status.textContent, /尚未开放/);
});

test("explicit login and question transmit only the intended context and memory-only token", async () => {
  const f = fixture(router({ answer: "Check the manual.", sources: [] }));
  await f.loginWith();
  assert.equal(f.password.value, "");
  assert.equal(f.form.hidden, false);
  await f.ask();
  const request = f.calls[1];
  assert.equal(request.credentials, "omit");
  assert.equal(request.redirect, "error");
  assert.equal(request.referrerPolicy, "no-referrer");
  assert.equal(request.headers.Authorization, "Bearer " + "a".repeat(64));
  assert.deepEqual(JSON.parse(request.body).context, { model: "JE-TEST", region: "EU", language: "en", version: "1.0", page: "JE-TEST/EU/en/md/manual.html" });
  assert.equal(f.log.children.at(-1).textContent, "Check the manual.");
  f.windowEvents.pagehide();
  assert.equal(f.form.hidden, true);
  assert.equal(f.log.children.length, 1);
});

test("model text stays plain text and citations can only open the current canonical page", async () => {
  const f = fixture(router({ answer: '<img src=x onerror="alert(1)">', sources: [
    { title: "Good", url: "https://manual.example/en/latest/JE-TEST/EU/en/md/manual.html#solar" },
    { title: "Foreign", url: "https://evil.example/collect" },
    { title: "Old version", url: "https://manual.example/en/old/JE-TEST/EU/en/md/manual.html#solar" },
    { title: "Script", url: "javascript:alert(1)" },
  ] }));
  await f.loginWith(); await f.ask();
  assert.equal(f.log.children[2].textContent, '<img src=x onerror="alert(1)">');
  const sources = f.log.children.at(-1);
  assert.equal(sources.children.length, 1);
  assert.equal(sources.children[0].children[0].rel, "noopener noreferrer");
});

test("clear removes transcript and history; expired sessions ask for password again", async () => {
  let expired = false;
  const f = fixture((url) => expired && url.endsWith("/chat") ? { ok: false, status: 401, json: async () => ({ message: "请重新输入访问密码" }) }
    : router({ answer: "Answer", sources: [] })(url));
  await f.loginWith(); await f.ask();
  f.clear.events.click();
  assert.equal(f.log.children.length, 1);
  await f.ask();
  assert.deepEqual(JSON.parse(f.calls.at(-1).body).history, []);
  expired = true;
  await f.ask();
  assert.equal(f.form.hidden, true);
  assert.equal(f.login.hidden, false);
  assert.match(f.status.textContent, /重新输入/);
});

test("busy requests cannot double-send and a failed request remains retryable", async () => {
  let finish;
  const f = fixture((url) => url.endsWith("/session") ? ok({ token: "a".repeat(64) })
    : new Promise((resolve) => { finish = resolve; }));
  await f.loginWith();
  const pending = f.ask();
  await f.ask();
  assert.equal(f.calls.length, 2);
  assert.equal(f.buttons[1].disabled, true);
  finish({ ok: false, status: 503, json: async () => ({ message: "服务暂不可用" }) });
  await pending;
  assert.equal(f.buttons[1].disabled, false);
  assert.match(f.status.textContent, /暂不可用/);
  assert.equal(f.question.value, "怎么充电？");
});
