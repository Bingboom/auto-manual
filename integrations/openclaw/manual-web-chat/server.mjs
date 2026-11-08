import { createServer } from "node:http";
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";
import { pathToFileURL } from "node:url";
import { createKnowledgeClient } from "../auto-manual-control-layer/lib/manual-query/client.mjs";
import { answerQuestion, ChatError, modelCompletion, validateQuestion } from "./answer.mjs";
import { corpusFetch, loadConfig } from "./config.mjs";

const MAX_BODY = 64000;
const SESSION_MS = 30 * 60 * 1000;
function jsonBody(req) {
  if (!/^application\/json(?:;|$)/i.test(req.headers["content-type"] || "")) throw new ChatError(415, "请使用JSON请求。");
  if (Number(req.headers["content-length"]) > MAX_BODY) { req.resume(); throw new ChatError(413, "请求过长。"); }
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) { reject(new ChatError(413, "请求过长。")); return; }
      chunks.push(chunk);
    });
    req.on("end", () => {
      if (size > MAX_BODY) return;
      try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8"))); }
      catch { reject(new ChatError(400, "请求格式不正确。")); }
    });
    req.on("error", reject);
    req.on("aborted", () => reject(new ChatError(400, "请求已中断。")));
  });
}

export function createChatServer(config, { client, complete, now = Date.now } = {}) {
  client ||= createKnowledgeClient({ baseUrl: config.baseUrl, fetchImpl: corpusFetch(config) });
  complete ||= modelCompletion(config);
  const sessions = new Map();
  const attempts = new Map();
  let active = 0;
  const prune = () => {
    for (const [key, value] of sessions) if (value.expires <= now()) sessions.delete(key);
    for (const [key, value] of attempts) if (value.until <= now()) attempts.delete(key);
  };
  const server = createServer(async (req, res) => {
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("Referrer-Policy", "no-referrer");
    const send = (status, body) => { res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" }); res.end(JSON.stringify(body)); };
    try {
      if (req.method === "GET" && req.url === "/health") return send(200, { status: "ok" });
      const origin = req.headers.origin;
      if (!config.origins.includes(origin)) throw new ChatError(403, "此站点未开放问答访问。");
      res.setHeader("Access-Control-Allow-Origin", origin);
      res.setHeader("Vary", "Origin");
      if (!["/api/session", "/api/chat", "/api/logout"].includes(req.url)) throw new ChatError(404, "未找到接口。");
      if (req.method === "OPTIONS") {
        res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
        res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
        res.writeHead(204); return res.end();
      }
      if (req.method !== "POST") throw new ChatError(405, "此接口仅接受POST请求。");
      prune();
      if (req.url === "/api/session") {
        const ip = req.socket.remoteAddress;
        let bucket = attempts.get(ip);
        if (!bucket) {
          if (attempts.size >= 2000) throw new ChatError(503, "服务繁忙，请稍后再试。");
          attempts.set(ip, bucket = { count: 0, until: now() + 60000 });
        }
        if (++bucket.count > 10) throw new ChatError(429, "尝试次数较多，请稍后再试。");
        const body = await jsonBody(req);
        const password = typeof body?.password === "string" && body.password.length <= 256 ? body.password : "";
        const actual = createHash("sha256").update(password).digest();
        if (!password || !timingSafeEqual(actual, Buffer.from(config.passwordHash, "hex"))) throw new ChatError(401, "访问密码不正确。");
        if (sessions.size >= 1000) throw new ChatError(503, "服务繁忙，请稍后再试。");
        const token = randomBytes(32).toString("hex");
        sessions.set(token, { expires: now() + SESSION_MS, count: 0, window: now(), origin });
        return send(200, { token, expires_in: SESSION_MS / 1000 });
      }
      const token = /^Bearer ([a-f0-9]{64})$/.exec(req.headers.authorization || "")?.[1];
      const session = sessions.get(token);
      if (!session || session.origin !== origin) throw new ChatError(401, "对话访问已过期，请重新输入访问密码。");
      if (req.url === "/api/logout") { sessions.delete(token); req.resume(); return send(200, { status: "ok" }); }
      if (now() - session.window >= 60000) { session.count = 0; session.window = now(); }
      if (++session.count > 12) throw new ChatError(429, "提问较频繁，请稍后再试。");
      const question = validateQuestion(await jsonBody(req));
      if (active >= 4) throw new ChatError(503, "问答服务繁忙，请稍后再试。");
      active++;
      try { return send(200, await answerQuestion(await client.load(), question, complete)); }
      finally { active--; }
    } catch (error) {
      if (res.headersSent) return;
      // Never echo upstream responses, credentials, stack traces or private requests.
      send(error instanceof ChatError ? error.status : 503, { message: error instanceof ChatError ? error.message
        : "目前无法核对已发布资料或生成回答，请稍后重试。" });
    }
  });
  server.requestTimeout = 15000;
  server.headersTimeout = 10000;
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const config = loadConfig();
    createChatServer(config).listen(config.port, config.host, () => {
      console.log(`HT-Docs manual Q&A listening on ${config.host}:${config.port}`);
    });
  } catch { console.error("HT-Docs Q&A configuration is incomplete or invalid; see manual-web-chat/README.md."); process.exitCode = 1; }
}
