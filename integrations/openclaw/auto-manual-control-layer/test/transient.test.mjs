import test from "node:test";
import assert from "node:assert/strict";

import { isTransientError, withRetry } from "../lib/transient.mjs";

function httpError(status) {
  const error = new Error(`GitHub API ${status}: boom`);
  error.httpStatus = status;
  return error;
}

test("isTransientError treats 5xx/429/408 http status as transient", () => {
  for (const status of [408, 429, 500, 502, 503, 504]) {
    assert.equal(isTransientError(httpError(status)), true, `status ${status} should be transient`);
  }
});

test("isTransientError treats 4xx (except 408/425/429) as definitive", () => {
  for (const status of [400, 401, 403, 404, 422]) {
    assert.equal(isTransientError(httpError(status)), false, `status ${status} should be definitive`);
  }
});

test("isTransientError matches node fetch transport failures", () => {
  const fetchFailed = new TypeError("fetch failed");
  fetchFailed.cause = { code: "ECONNRESET" };
  assert.equal(isTransientError(fetchFailed), true);

  const dnsError = new Error("getaddrinfo EAI_AGAIN api.github.com");
  assert.equal(isTransientError(dnsError), true);

  const undici = new Error("connect timeout");
  undici.code = "UND_ERR_CONNECT_TIMEOUT";
  assert.equal(isTransientError(undici), true);
});

test("isTransientError parses a bare GitHub API status message without httpStatus", () => {
  assert.equal(isTransientError(new Error("GitHub API 503: upstream")), true);
  assert.equal(isTransientError(new Error("GitHub API 404: not found")), false);
});

test("isTransientError is false for null and plain logic errors", () => {
  assert.equal(isTransientError(null), false);
  assert.equal(isTransientError(new Error("Cannot read properties of undefined")), false);
});

test("withRetry returns on first success without sleeping", async () => {
  let calls = 0;
  const sleeps = [];
  const result = await withRetry(async () => {
    calls += 1;
    return "ok";
  }, { sleep: async (ms) => sleeps.push(ms) });
  assert.equal(result, "ok");
  assert.equal(calls, 1);
  assert.equal(sleeps.length, 0);
});

test("withRetry retries transient failures then succeeds", async () => {
  let calls = 0;
  const sleeps = [];
  const result = await withRetry(
    async () => {
      calls += 1;
      if (calls < 3) {
        throw httpError(503);
      }
      return "recovered";
    },
    { attempts: 3, baseDelayMs: 10, sleep: async (ms) => sleeps.push(ms) }
  );
  assert.equal(result, "recovered");
  assert.equal(calls, 3);
  assert.deepEqual(sleeps, [10, 20]);
});

test("withRetry does not retry a definitive error", async () => {
  let calls = 0;
  await assert.rejects(
    withRetry(
      async () => {
        calls += 1;
        throw httpError(404);
      },
      { attempts: 3, sleep: async () => {} }
    ),
    /GitHub API 404/
  );
  assert.equal(calls, 1);
});

test("withRetry gives up after the attempt budget on persistent transient errors", async () => {
  let calls = 0;
  await assert.rejects(
    withRetry(
      async () => {
        calls += 1;
        throw httpError(502);
      },
      { attempts: 2, baseDelayMs: 1, sleep: async () => {} }
    ),
    /GitHub API 502/
  );
  assert.equal(calls, 2);
});
