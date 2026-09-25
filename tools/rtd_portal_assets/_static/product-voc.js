"use strict";
document.querySelectorAll("form[data-product-voc]").forEach((form) => {
  const root = form.closest(".product-voc");
  const dialog = root.querySelector("dialog");
  const launch = root.querySelector(".product-voc-launch");
  if (typeof dialog.showModal === "function") {
    launch.hidden = false;
    launch.addEventListener("click", () => {
      dialog.showModal();
      const first = form.querySelector('input[name="model"]');
      first.focus();
    });
    root.querySelector(".product-voc-close").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      const rect = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right ||
          event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
    });
    dialog.addEventListener("close", () => launch.focus());
  }
  const status = form.querySelector(".product-voc-status");
  const fields = form.querySelector("fieldset");
  const button = form.querySelector('button[type="submit"]');
  if (!window.fetch || !window.crypto || !window.crypto.randomUUID) {
    status.textContent = "Please use a current browser to send a suggestion. Nothing has been submitted.";
    return;
  }
  fields.disabled = false;
  let previous = "";
  let requestId = "";
  let busy = false;
  form.addEventListener("input", () => { if (!busy) button.disabled = false; });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !form.reportValidity()) return;
    const values = Object.fromEntries(new FormData(form));
    const fingerprint = JSON.stringify(values);
    if (fingerprint !== previous) {
      requestId = window.crypto.randomUUID();
      previous = fingerprint;
    }
    busy = true;
    fields.disabled = true;
    status.textContent = "Sending your suggestion…";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 45000);
    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST", mode: "cors", credentials: "omit", redirect: "error",
        referrerPolicy: "no-referrer", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...values, request_id: requestId }), signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok || result.ok !== true) {
        const messages = {
          400: "Please check the fields and try again.",
          403: "This page is not enabled to send suggestions yet.",
          409: "This submission needs verification. Please keep your reference and do not send another copy.",
          429: "Too many attempts. Please wait ten minutes before trying again.",
        };
        throw new Error(messages[response.status] || "Delivery is not confirmed. Your text is kept; retry with the same reference.");
      }
      status.textContent = result.preview === true
        ? `Preview only — nothing was sent. Reference: ${requestId}`
        : `Thank you — your suggestion was received. Reference: ${requestId}`;
      button.disabled = true;
    } catch (error) {
      status.textContent = (error.name === "AbortError" || error instanceof TypeError
        ? "Delivery is not confirmed. Your text is kept; you can retry."
        : error.message) + ` Reference: ${requestId}`;
    } finally {
      clearTimeout(timeout);
      busy = false;
      fields.disabled = false;
    }
  });
});
