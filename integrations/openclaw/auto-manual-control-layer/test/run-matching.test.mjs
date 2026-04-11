import test from "node:test";
import assert from "node:assert/strict";

import { findActiveRunForRecord, findRunByDispatch } from "../lib/run-matching.mjs";

test("findRunByDispatch matches the nonce in the run title", () => {
  const runs = [
    {
      id: 1,
      display_title: "Feishu Build Queue / rec123 / abc",
      created_at: "2026-04-10T10:00:00Z",
    },
    {
      id: 2,
      display_title: "Feishu Build Queue / rec123 / nonce-123",
      created_at: "2026-04-10T10:01:00Z",
    },
  ];

  const matched = findRunByDispatch(runs, {
    dispatchNonce: "nonce-123",
    dispatchedAfter: "2026-04-10T10:00:10Z",
  });

  assert.equal(matched.id, 2);
});

test("findActiveRunForRecord skips completed runs", () => {
  const runs = [
    {
      id: 1,
      display_title: "Feishu Build Queue / rec123 / older",
      status: "completed",
    },
    {
      id: 2,
      display_title: "Feishu Build Queue / rec123 / newer",
      status: "in_progress",
    },
  ];

  const matched = findActiveRunForRecord(runs, "rec123");

  assert.equal(matched.id, 2);
});
