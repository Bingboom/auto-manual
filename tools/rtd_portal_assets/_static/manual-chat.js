(() => {
  "use strict";
  const root = document.querySelector(".manual-chat");
  if (!root || root.dataset.ready) return;
  root.dataset.ready = "true";
  const dialog = root.querySelector("dialog");
  if (!dialog.showModal) return;
  const launch = root.querySelector(".manual-chat-launch");
  const login = root.querySelector(".manual-chat-login");
  const form = root.querySelector(".manual-chat-question");
  const log = root.querySelector(".manual-chat-messages");
  const status = root.querySelector(".manual-chat-status");
  const context = Object.fromEntries(["model", "region", "language", "version", "page"].map((key) => [key, root.dataset[key]]));
  const greeting = log.firstElementChild.cloneNode(true);
  let token = "";
  let pending;
  let history = [];
  let epoch = 0;
  const tell = (text, who = "bot") => {
    const p = document.createElement("p");
    p.className = "manual-chat-" + who;
    p.textContent = text;
    log.append(p);
    log.scrollTop = log.scrollHeight;
  };
  const busy = (value) => {
    root.querySelectorAll('button[type="submit"]').forEach((button) => { button.disabled = value; });
    form.querySelector("textarea").disabled = value;
  };
  const lock = () => { token = ""; history = []; login.hidden = false; form.hidden = true; };
  const errorText = (error) => error.name === "AbortError" ? "连接超时，请重试。"
    : ["TypeError", "SyntaxError"].includes(error.name) ? "无法连接问答服务，请稍后重试。" : error.message;
  const post = async (path, data) => {
    const controller = new AbortController();
    pending = controller;
    const timer = setTimeout(() => controller.abort(), 100000);
    try {
      const response = await fetch(root.dataset.endpoint + path, {
        method: "POST", mode: "cors", credentials: "omit", redirect: "error", referrerPolicy: "no-referrer",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: "Bearer " + token } : {}) },
        body: JSON.stringify(data), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 401) lock();
        throw new Error(result.message || "问答服务暂时无法处理，请稍后重试。");
      }
      return result;
    } finally { clearTimeout(timer); if (pending === controller) pending = undefined; }
  };
  const showSources = (sources) => {
    if (!sources?.length) return;
    const list = document.createElement("ul");
    list.className = "manual-chat-sources";
    for (const source of sources) {
      let url;
      try { url = new URL(source.url); } catch { continue; }
      // Only the current publication can be cited. Never turn model text into HTML or links.
      if (url.origin !== location.origin || url.pathname !== location.pathname || url.search) continue;
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = url.href;
      a.textContent = "查看原文 · " + source.title;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      const details = document.createElement("small");
      details.textContent = [context.model, context.region, context.language, context.version].join(" · ");
      li.append(a, details);
      list.append(li);
    }
    log.append(list);
    log.scrollTop = log.scrollHeight;
  };
  launch.hidden = false;
  launch.addEventListener("click", () => {
    dialog.showModal();
    if (context.region !== "EU" || !context.language || !context.version) {
      login.hidden = true;
      form.hidden = true;
      status.textContent = context.region !== "EU" ? "当前问答仅支持已接入的 EU 说明书，此市场尚未开放。"
        : "这份资料的语言或版本尚未确认，暂无法提供问答。";
    } else (token ? form.querySelector("textarea") : login.elements.password).focus();
  });
  root.querySelector(".manual-chat-close").addEventListener("click", () => dialog.close());
  login.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (pending) return;
    busy(true);
    status.textContent = "正在验证…";
    const password = login.elements.password.value;
    login.elements.password.value = "";
    try {
      const result = await post("/api/session", { password });
      if (typeof result.token !== "string" || !result.token) throw new Error("暂时无法开始对话，请稍后重试。");
      token = result.token;
      login.hidden = true;
      form.hidden = false;
      status.textContent = "";
    } catch (error) { status.textContent = errorText(error); }
    finally { busy(false); if (token) form.querySelector("textarea").focus(); }
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = form.elements.question;
    const message = input.value.trim();
    if (!message || pending) return;
    const turn = epoch;
    tell(message, "user");
    input.value = "";
    busy(true);
    status.textContent = "正在查阅这份说明书…";
    try {
      const result = await post("/api/chat", { message, context,
        history: history.map((item) => ({ ...item, content: item.content.slice(0, 2000) })) });
      if (turn !== epoch) return;
      if (typeof result.answer !== "string") throw new Error("暂时无法生成回答，请稍后重试。");
      tell(result.answer);
      showSources(result.sources);
      history = [...history, { role: "user", content: message }, { role: "assistant", content: result.answer }].slice(-6);
      status.textContent = "依据当前发布资料回答，请以原文为准。";
    } catch (error) {
      if (turn === epoch) { status.textContent = errorText(error); input.value = message; }
    } finally { busy(false); if (!form.hidden) input.focus(); }
  });
  root.querySelector(".manual-chat-clear").addEventListener("click", () => {
    epoch++;
    pending?.abort();
    history = [];
    log.replaceChildren(greeting.cloneNode(true));
    status.textContent = "对话已清空。";
    busy(false);
  });
  // Tokens and messages live only in this page's memory, never localStorage, cookies or URLs.
  window.addEventListener("pagehide", () => { epoch++; pending?.abort(); lock(); log.replaceChildren(greeting.cloneNode(true)); });
})();
