/* Check only this deployed site's receipt. A main push is not a deployment. */
(() => {
  "use strict";
  const menu = document.querySelector(".mobile-menu");
  if (menu) menu.addEventListener("click", () => document.body.classList.toggle("menu-open"));
  const panel = document.querySelector(".sw-update");
  if (!panel) return;
  const status = document.getElementById("sw-update-status");
  const refresh = document.getElementById("sw-refresh");
  const current = panel.dataset.revision;
  let pending = "";
  let busy = false;
  const valid = (value) => typeof value === "string" && /^[0-9a-f]{40}$/.test(value);
  refresh.addEventListener("click", () => {
    if (!valid(pending)) return;
    const url = new URL(window.location.href);
    url.searchParams.set("_sw_revision", pending);
    window.location.assign(url.href);
  });
  if (!valid(current)) {
    status.textContent = "本地预览，未启用发布版本检查";
    return;
  }
  async function check() {
    if (document.hidden || busy || pending) return;
    busy = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const url = new URL(panel.dataset.versionUrl, window.location.href);
      if (url.origin !== window.location.origin) throw new Error("Unexpected receipt origin");
      url.searchParams.set("_sw_check", Date.now().toString());
      const response = await fetch(url.href, {cache: "no-store", signal: controller.signal});
      if (!response.ok) throw new Error("Receipt unavailable");
      const receipt = await response.json();
      if (receipt.schema !== "hello-docs-system-revision/v1" || !valid(receipt.revision)) {
        throw new Error("Invalid receipt");
      }
      if (receipt.revision !== current &&
          !(Date.parse(receipt.built_at) > Date.parse(panel.dataset.builtAt))) {
        status.textContent = "发布版本同步中，请稍后再试";
      } else if (receipt.revision !== current) {
        pending = receipt.revision;
        status.textContent = "新版本已发布 · " + pending.slice(0, 8);
        refresh.hidden = false;
      } else {
        status.textContent = "当前为最新已发布版本";
      }
    } catch {
      status.textContent = "暂时无法检查更新，当前快照仍可查看";
    } finally {
      clearTimeout(timeout);
      busy = false;
    }
  }
  check();
  setInterval(check, 60000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) check(); });
})();
