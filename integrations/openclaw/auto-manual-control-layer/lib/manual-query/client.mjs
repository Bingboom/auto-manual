import { createHash, randomUUID } from "node:crypto";

export const KNOWLEDGE_FILE = "manual-knowledge.json";
const RECEIPT_FILE = "manual-deployment.json";
const MAX_BYTES = 32 * 1024 * 1024;
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const hash = (value) => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);

export function siteOrigin(value) {
  const url = new URL(value);
  if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
    throw new Error("manualQueryBaseUrl must be one HTTPS origin without a path or credentials.");
  }
  return url.origin;
}

async function fetchResponse(fetchImpl, origin, path) {
  let url = new URL(path, origin + "/");
  const signal = AbortSignal.timeout(15000);
  for (let hops = 0; hops <= 5; hops++) {
    if (url.origin !== origin || url.username || url.password) throw new Error("Cross-origin query redirect refused.");
    url.searchParams.set("receipt_probe", randomUUID().replaceAll("-", ""));
    const response = await fetchImpl(url.href, {
      redirect: "manual", signal,
      headers: { "Cache-Control": "no-cache", "Accept-Encoding": "identity" },
    });
    if (![301, 302, 303, 307, 308].includes(response.status)) return response;
    await response.body?.cancel();
    const location = response.headers.get("location");
    if (!location) throw new Error("Manual query redirect has no location.");
    url = new URL(location, url);
  }
  throw new Error("Too many manual query redirects.");
}

async function download(fetchImpl, origin, path) {
  const response = await fetchResponse(fetchImpl, origin, path);
  if (!response.ok) throw new Error(`Manual query publication unavailable (HTTP ${response.status}).`);
  if (response.url && new URL(response.url).origin !== origin) throw new Error("Cross-origin query response refused.");
  if (![null, "identity"].includes(response.headers.get("content-encoding"))) throw new Error("Encoded manual query response refused.");
  const length = response.headers.get("content-length");
  if (length !== null && (!/^\d+$/.test(length) || Number(length) > MAX_BYTES)) {
    throw new Error("Manual query response exceeds size limit.");
  }
  if (!response.body) throw new Error("Empty manual query response.");
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > MAX_BYTES) throw new Error("Manual query response exceeds size limit.");
      chunks.push(Buffer.from(value));
    }
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
  if (length !== null && size !== Number(length)) throw new Error("Incomplete manual query response.");
  return Buffer.concat(chunks);
}

function validateReceipt(receipt) {
  if (receipt.schema !== "manual-rtd-deployment/v1" || !hash(receipt.source_sha256)
      || !hash(receipt.files?.[KNOWLEDGE_FILE])) {
    throw new Error("Deployment does not contain a verified manual query export yet.");
  }
}

export function validateCorpus(corpus, receipt) {
  if (corpus.schema !== "auto-manual-knowledge/v1" || corpus.region !== "EU"
      || corpus.source_sha256 !== receipt.source_sha256 || !Array.isArray(corpus.documents)
      || corpus.documents.length > 2000 || corpus.counts?.editions !== corpus.documents.length) {
    throw new Error("Invalid manual query corpus identity or count.");
  }
  const documentIds = new Set();
  const sectionIds = new Set();
  for (const doc of corpus.documents) {
    if (typeof doc.id !== "string" || documentIds.has(doc.id) || doc.region !== "EU"
        || typeof doc.model !== "string" || !doc.model || !Array.isArray(doc.sections)
        || !doc.sections.length || doc.sections.length > 1000
        || !/^[A-Za-z0-9_-]+\/EU\/(?:[A-Za-z_-]+\/)?md\/[A-Za-z0-9_.-]+\.html$/.test(doc.url)
        || receipt.files[doc.url] !== doc.html_sha256 || !hash(doc.html_sha256)
        || !["single", "legacy_unspecified"].includes(doc.language_scope)
        || (doc.language_scope === "single" ? typeof doc.lang !== "string" || !doc.lang : doc.lang !== null)) {
      throw new Error("Invalid or duplicate EU document in query corpus.");
    }
    documentIds.add(doc.id);
    for (const section of doc.sections) {
      if (typeof section.id !== "string" || sectionIds.has(section.id) || typeof section.title !== "string"
          || typeof section.anchor !== "string" || !Array.isArray(section.blocks) || section.blocks.length > 10000
          || section.blocks.some((block) => typeof block?.text !== "string" || typeof block.type !== "string")) {
        throw new Error("Invalid or duplicate section in query corpus.");
      }
      sectionIds.add(section.id);
    }
  }
  if (corpus.counts.models !== new Set(corpus.documents.map((doc) => doc.model)).size
      || corpus.counts.sections !== sectionIds.size) throw new Error("Manual query corpus counts disagree.");
}

export function createKnowledgeClient({ baseUrl, fetchImpl = globalThis.fetch, now = Date.now, ttlMs = 60000 }) {
  const origin = siteOrigin(baseUrl);
  let cache;
  let pending;
  async function refresh() {
    const receipt = JSON.parse((await download(fetchImpl, origin, RECEIPT_FILE)).toString("utf8"));
    validateReceipt(receipt);
    const digest = receipt.files[KNOWLEDGE_FILE];
    if (cache?.digest === digest && cache.corpus.source_sha256 === receipt.source_sha256) {
      validateCorpus(cache.corpus, receipt);
      cache.checkedAt = now();
      return cache;
    }
    const bytes = await download(fetchImpl, origin, KNOWLEDGE_FILE);
    if (sha256(bytes) !== digest) throw new Error("Manual query data does not match its deployment receipt.");
    const corpus = JSON.parse(bytes.toString("utf8"));
    validateCorpus(corpus, receipt);
    const after = JSON.parse((await download(fetchImpl, origin, RECEIPT_FILE)).toString("utf8"));
    validateReceipt(after);
    if (after.source_sha256 !== receipt.source_sha256 || after.files[KNOWLEDGE_FILE] !== digest) {
      throw new Error("Manual deployment changed during refresh; please retry.");
    }
    cache = { corpus, digest, origin, checkedAt: now() };
    return cache;
  }
  return {
    async load() {
      if (cache && now() - cache.checkedAt < ttlMs) return cache;
      if (!pending) pending = refresh().catch((error) => { cache = undefined; throw error; })
        .finally(() => { pending = undefined; });
      return pending;
    },
  };
}
