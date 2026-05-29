// Separates "the remote genuinely rejected/failed the request" from "I could
// not observe the result right now" (a network blip, a slow GitHub edge, a
// 5xx, a dropped socket). The control layer must never report the second kind
// as an action failure: a dispatch that GitHub already accepted is still
// running regardless of whether the local poller could read it back.

const TRANSIENT_HTTP_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);

// Node's global fetch surfaces transport failures as a TypeError with the real
// cause nested under error.cause. Match on both the error and its cause.
const TRANSIENT_ERROR_CODES = new Set([
  "ECONNRESET",
  "ECONNREFUSED",
  "ECONNABORTED",
  "ETIMEDOUT",
  "EAI_AGAIN",
  "ENOTFOUND",
  "EPIPE",
  "EHOSTUNREACH",
  "ENETUNREACH",
  "UND_ERR_CONNECT_TIMEOUT",
  "UND_ERR_HEADERS_TIMEOUT",
  "UND_ERR_BODY_TIMEOUT",
  "UND_ERR_SOCKET",
]);

const TRANSIENT_MESSAGE_PATTERN =
  /fetch failed|network|socket hang up|timed? ?out|timeout|temporarily unavailable|ECONN|EAI_AGAIN|terminated/i;

export function isTransientError(error) {
  if (!error) {
    return false;
  }

  // Status tagged onto the error by the GitHub client (preferred signal).
  if (Number.isInteger(error.httpStatus)) {
    return TRANSIENT_HTTP_STATUS.has(error.httpStatus);
  }

  const code = error.code || error.cause?.code;
  if (code && TRANSIENT_ERROR_CODES.has(code)) {
    return true;
  }

  const message = String(error.message || "");

  // "GitHub API <status>: ..." messages from requestUrl when httpStatus is absent.
  const httpMatch = message.match(/GitHub API (\d{3})/);
  if (httpMatch) {
    return TRANSIENT_HTTP_STATUS.has(Number(httpMatch[1]));
  }

  return TRANSIENT_MESSAGE_PATTERN.test(message);
}

// Retry an idempotent operation through transient failures only. A definitive
// error (4xx that is not 408/425/429, parse error, etc.) is rethrown
// immediately so genuine problems still surface fast. Never wrap a
// non-idempotent call (e.g. a workflow_dispatch POST) in this.
export async function withRetry(
  fn,
  { attempts = 3, baseDelayMs = 400, sleep = defaultSleep, shouldRetry = isTransientError } = {}
) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await fn(attempt);
    } catch (error) {
      lastError = error;
      if (attempt >= attempts || !shouldRetry(error)) {
        throw error;
      }
      await sleep(baseDelayMs * attempt);
    }
  }
  throw lastError;
}

function defaultSleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
